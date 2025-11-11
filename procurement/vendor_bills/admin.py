"""
3-Way Match & Vendor Bills Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    VendorBill, VendorBillLine, ThreeWayMatch, 
    MatchException, MatchTolerance
)


class VendorBillLineInline(admin.TabularInline):
    model = VendorBillLine
    extra = 1
    fields = [
        'line_number', 'catalog_item', 'description', 
        'quantity', 'unit_of_measure', 'unit_price', 'line_total',
        'tax_rate', 'tax_amount',
        'po_number', 'po_line_number', 'grn_number',
        'is_matched', 'has_exception'
    ]
    readonly_fields = ['line_total', 'tax_amount', 'is_matched', 'has_exception']


@admin.register(VendorBill)
class VendorBillAdmin(admin.ModelAdmin):
    list_display = [
        'bill_number', 'supplier', 'supplier_invoice_number', 
        'bill_date', 'get_status_display_colored', 'total_amount',
        'get_match_status', 'get_exception_count', 'get_ap_status'
    ]
    list_filter = [
        'status', 'bill_type', 'has_exceptions', 'is_matched',
        'approval_status', 'bill_date', 'supplier'
    ]
    search_fields = [
        'bill_number', 'supplier_invoice_number', 
        'supplier__name', 'supplier__supplier_code'
    ]
    readonly_fields = [
        'bill_number', 'subtotal', 'tax_amount', 'total_amount',
        'base_currency_total', 'is_matched', 'match_date',
        'has_exceptions', 'exception_count', 'ap_invoice',
        'ap_posted_date', 'ap_posted_by', 'approved_by', 'approved_date',
        'created_by', 'created_at', 'updated_by', 'updated_at',
        'get_line_summary', 'get_match_summary', 'get_exception_summary'
    ]
    
    fieldsets = (
        ('Bill Information', {
            'fields': (
                'bill_number', 'bill_type', 'status',
                'supplier', 'supplier_invoice_number', 'supplier_invoice_date',
                'bill_date', 'due_date'
            )
        }),
        ('Financial Details', {
            'fields': (
                'currency', 'exchange_rate',
                'subtotal', 'tax_amount', 'total_amount', 'base_currency_total'
            )
        }),
        ('Matching Status', {
            'fields': (
                'is_matched', 'match_date', 'has_exceptions', 'exception_count',
                'get_match_summary', 'get_exception_summary'
            )
        }),
        ('AP Integration', {
            'fields': (
                'ap_invoice', 'ap_posted_date', 'ap_posted_by'
            )
        }),
        ('Payment Status', {
            'fields': (
                'is_paid', 'paid_date', 'paid_amount'
            )
        }),
        ('Approval', {
            'fields': (
                'approval_status', 'approved_by', 'approved_date'
            )
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes')
        }),
        ('Line Items', {
            'fields': ('get_line_summary',)
        }),
        ('Audit Trail', {
            'fields': (
                'created_by', 'created_at', 'updated_by', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [VendorBillLineInline]
    
    actions = [
        'action_submit', 'action_match', 'action_approve',
        'action_post_to_ap', 'action_reject', 'action_cancel'
    ]
    
    def get_status_display_colored(self, obj):
        """Color-coded status display"""
        colors = {
            'DRAFT': 'gray',
            'SUBMITTED': 'blue',
            'MATCHED': 'green',
            'EXCEPTION': 'orange',
            'APPROVED': 'darkgreen',
            'POSTED_TO_AP': 'purple',
            'PAID': 'teal',
            'REJECTED': 'red',
            'CANCELLED': 'darkgray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_display_colored.short_description = 'Status'
    
    def get_match_status(self, obj):
        """Match status indicator"""
        if obj.is_matched:
            return format_html(
                '<span style="color: green;">✓ Matched</span>'
            )
        elif obj.has_exceptions:
            return format_html(
                '<span style="color: orange;">⚠ Exceptions ({}/{})</span>',
                obj.exception_count, obj.lines.count()
            )
        else:
            return format_html(
                '<span style="color: gray;">○ Not Matched</span>'
            )
    get_match_status.short_description = 'Match Status'
    
    def get_exception_count(self, obj):
        """Exception count display"""
        if obj.exception_count > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} Exceptions</span>',
                obj.exception_count
            )
        return format_html('<span style="color: green;">No Exceptions</span>')
    get_exception_count.short_description = 'Exceptions'
    
    def get_ap_status(self, obj):
        """AP posting status"""
        if obj.ap_invoice:
            return format_html(
                '<a href="{}" style="color: green;">✓ Posted</a>',
                reverse('admin:ap_apinvoice_change', args=[obj.ap_invoice.id])
            )
        elif obj.status == 'APPROVED':
            return format_html(
                '<span style="color: orange;">Ready to Post</span>'
            )
        else:
            return format_html(
                '<span style="color: gray;">Not Posted</span>'
            )
    get_ap_status.short_description = 'AP Status'
    
    def get_line_summary(self, obj):
        """Summary of bill lines"""
        if not obj.pk:
            return "Save bill to add lines"
        
        lines = obj.lines.all()
        matched_count = lines.filter(is_matched=True).count()
        exception_count = lines.filter(has_exception=True).count()
        total_lines = lines.count()
        
        html = f"""
        <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
            <strong>Line Summary:</strong><br>
            Total Lines: {total_lines}<br>
            Matched: <span style="color: green;">{matched_count}</span><br>
            Exceptions: <span style="color: red;">{exception_count}</span><br>
            Pending: {total_lines - matched_count - exception_count}
        </div>
        """
        return format_html(html)
    get_line_summary.short_description = 'Line Summary'
    
    def get_match_summary(self, obj):
        """Summary of matching results"""
        if not obj.pk or not obj.is_matched:
            return "Not matched yet"
        
        matches = obj.match_records.all()
        matched_count = matches.filter(match_status='MATCHED').count()
        exception_count = matches.filter(has_exception=True).count()
        
        html = f"""
        <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
            <strong>Match Summary:</strong><br>
            Matched: <span style="color: green;">{matched_count}</span><br>
            Exceptions: <span style="color: red;">{exception_count}</span><br>
            Match Date: {obj.match_date.strftime('%Y-%m-%d %H:%M') if obj.match_date else 'N/A'}
        </div>
        """
        return format_html(html)
    get_match_summary.short_description = 'Match Summary'
    
    def get_exception_summary(self, obj):
        """Summary of exceptions"""
        if not obj.pk or not obj.has_exceptions:
            return "No exceptions"
        
        exceptions = MatchException.objects.filter(
            three_way_match__vendor_bill_line__vendor_bill=obj
        )
        
        by_type = {}
        for exc in exceptions:
            exc_type = exc.get_exception_type_display()
            by_type[exc_type] = by_type.get(exc_type, 0) + 1
        
        html = '<div style="padding: 10px; background: #fff3cd; border-radius: 5px;">'
        html += '<strong>Exceptions:</strong><br>'
        for exc_type, count in by_type.items():
            html += f'{exc_type}: <span style="color: red;">{count}</span><br>'
        html += '</div>'
        
        return format_html(html)
    get_exception_summary.short_description = 'Exception Summary'
    
    def action_submit(self, request, queryset):
        """Submit bills for matching"""
        count = 0
        for bill in queryset:
            if bill.status == 'DRAFT':
                try:
                    bill.submit(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error submitting {bill.bill_number}: {e}", level='error')
        
        self.message_user(request, f"Submitted {count} bills for matching")
    action_submit.short_description = "Submit selected bills for matching"
    
    def action_match(self, request, queryset):
        """Perform 3-way matching"""
        count = 0
        for bill in queryset:
            if bill.status == 'SUBMITTED':
                try:
                    bill.perform_three_way_match(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error matching {bill.bill_number}: {e}", level='error')
        
        self.message_user(request, f"Matched {count} bills")
    action_match.short_description = "Perform 3-way match"
    
    def action_approve(self, request, queryset):
        """Approve matched bills"""
        count = 0
        for bill in queryset:
            try:
                bill.approve(request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f"Error approving {bill.bill_number}: {e}", level='error')
        
        self.message_user(request, f"Approved {count} bills")
    action_approve.short_description = "Approve selected bills"
    
    def action_post_to_ap(self, request, queryset):
        """Post to AP"""
        count = 0
        for bill in queryset:
            if bill.status == 'APPROVED':
                try:
                    bill.post_to_ap(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error posting {bill.bill_number}: {e}", level='error')
        
        self.message_user(request, f"Posted {count} bills to AP")
    action_post_to_ap.short_description = "Post to AP (create AP Invoice)"
    
    def action_reject(self, request, queryset):
        """Reject bills"""
        count = 0
        for bill in queryset:
            try:
                bill.reject(request.user, "Rejected via admin action")
                count += 1
            except Exception as e:
                self.message_user(request, f"Error rejecting {bill.bill_number}: {e}", level='error')
        
        self.message_user(request, f"Rejected {count} bills")
    action_reject.short_description = "Reject selected bills"
    
    def action_cancel(self, request, queryset):
        """Cancel bills"""
        count = 0
        for bill in queryset:
            try:
                bill.cancel(request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f"Error cancelling {bill.bill_number}: {e}", level='error')
        
        self.message_user(request, f"Cancelled {count} bills")
    action_cancel.short_description = "Cancel selected bills"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(VendorBillLine)
class VendorBillLineAdmin(admin.ModelAdmin):
    list_display = [
        'vendor_bill', 'line_number', 'catalog_item', 
        'quantity', 'unit_price', 'line_total',
        'get_match_status', 'po_number', 'grn_number'
    ]
    list_filter = ['is_matched', 'has_exception', 'vendor_bill__supplier']
    search_fields = [
        'vendor_bill__bill_number', 'catalog_item__item_code',
        'po_number', 'grn_number'
    ]
    readonly_fields = ['line_total', 'tax_amount', 'is_matched', 'has_exception']
    
    def get_match_status(self, obj):
        """Match status indicator"""
        if obj.is_matched:
            return format_html('<span style="color: green;">✓ Matched</span>')
        elif obj.has_exception:
            return format_html('<span style="color: red;">✗ Exception</span>')
        else:
            return format_html('<span style="color: gray;">○ Pending</span>')
    get_match_status.short_description = 'Match Status'


@admin.register(ThreeWayMatch)
class ThreeWayMatchAdmin(admin.ModelAdmin):
    list_display = [
        'match_number', 'get_status_colored', 'catalog_item',
        'get_quantities', 'get_variance_display',
        'get_exception_indicator', 'matched_date'
    ]
    list_filter = [
        'match_status', 'has_exception',
        'quantity_tolerance_exceeded', 'price_tolerance_exceeded',
        'matched_date'
    ]
    search_fields = [
        'match_number', 'po_number', 'catalog_item__item_code',
        'vendor_bill_line__vendor_bill__bill_number'
    ]
    readonly_fields = [
        'match_number', 'matched_date', 'matched_by',
        'quantity_variance', 'quantity_variance_pct',
        'price_variance', 'price_variance_pct',
        'quantity_tolerance_exceeded', 'price_tolerance_exceeded',
        'match_status', 'has_exception',
        'get_variance_details', 'get_tolerance_check'
    ]
    
    fieldsets = (
        ('Match Information', {
            'fields': (
                'match_number', 'match_status', 'has_exception',
                'matched_date', 'matched_by'
            )
        }),
        ('Documents', {
            'fields': (
                'vendor_bill_line', 'po_number', 'po_line_number',
                'grn_line', 'catalog_item'
            )
        }),
        ('Quantities', {
            'fields': (
                'po_quantity', 'grn_quantity', 'bill_quantity'
            )
        }),
        ('Prices', {
            'fields': (
                'po_unit_price', 'bill_unit_price'
            )
        }),
        ('Variance Analysis', {
            'fields': (
                'get_variance_details', 'get_tolerance_check'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    def get_status_colored(self, obj):
        """Color-coded status"""
        colors = {
            'MATCHED': 'green',
            'EXCEPTION': 'red',
            'PARTIALLY_MATCHED': 'orange',
            'UNMATCHED': 'gray',
        }
        color = colors.get(obj.match_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_match_status_display()
        )
    get_status_colored.short_description = 'Status'
    
    def get_quantities(self, obj):
        """Quantity comparison"""
        return format_html(
            'PO: {} | GRN: {} | Bill: {}',
            obj.po_quantity, obj.grn_quantity, obj.bill_quantity
        )
    get_quantities.short_description = 'Quantities (PO/GRN/Bill)'
    
    def get_variance_display(self, obj):
        """Variance display"""
        qty_color = 'red' if obj.quantity_tolerance_exceeded else 'green'
        price_color = 'red' if obj.price_tolerance_exceeded else 'green'
        
        return format_html(
            'Qty: <span style="color: {};">{:+.2f}%</span> | '
            'Price: <span style="color: {};">{:+.2f}%</span>',
            qty_color, obj.quantity_variance_pct,
            price_color, obj.price_variance_pct
        )
    get_variance_display.short_description = 'Variance'
    
    def get_exception_indicator(self, obj):
        """Exception indicator"""
        if obj.has_exception:
            try:
                exc = obj.exception
                return format_html(
                    '<a href="{}" style="color: red; font-weight: bold;">⚠ {}</a>',
                    reverse('admin:vendor_bill_matchexception_change', args=[exc.id]),
                    exc.get_exception_type_display()
                )
            except:
                return format_html('<span style="color: red;">⚠ Exception</span>')
        return format_html('<span style="color: green;">✓ OK</span>')
    get_exception_indicator.short_description = 'Exception'
    
    def get_variance_details(self, obj):
        """Detailed variance breakdown"""
        html = f"""
        <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
            <strong>Quantity Variance:</strong><br>
            Bill Qty - GRN Qty: {obj.quantity_variance} ({obj.quantity_variance_pct:+.2f}%)<br>
            <span style="color: {'red' if obj.quantity_tolerance_exceeded else 'green'};">
                {'⚠ EXCEEDED' if obj.quantity_tolerance_exceeded else '✓ OK'}
            </span><br><br>
            
            <strong>Price Variance:</strong><br>
            Bill Price - PO Price: {obj.price_variance} ({obj.price_variance_pct:+.2f}%)<br>
            <span style="color: {'red' if obj.price_tolerance_exceeded else 'green'};">
                {'⚠ EXCEEDED' if obj.price_tolerance_exceeded else '✓ OK'}
            </span>
        </div>
        """
        return format_html(html)
    get_variance_details.short_description = 'Variance Details'
    
    def get_tolerance_check(self, obj):
        """Tolerance check results"""
        from .models import MatchTolerance
        
        tolerance = MatchTolerance.get_tolerance(
            supplier=obj.vendor_bill_line.vendor_bill.supplier,
            catalog_item=obj.catalog_item
        )
        
        html = f"""
        <div style="padding: 10px; background: #e3f2fd; border-radius: 5px;">
            <strong>Tolerance Thresholds:</strong><br>
            Quantity: ±{tolerance.quantity_tolerance_pct}%<br>
            Price: ±{tolerance.price_tolerance_pct}%<br><br>
            
            <strong>Check Results:</strong><br>
            Quantity: <span style="color: {'red' if obj.quantity_tolerance_exceeded else 'green'};">
                {abs(obj.quantity_variance_pct):.2f}% {'(EXCEEDED)' if obj.quantity_tolerance_exceeded else '(OK)'}
            </span><br>
            Price: <span style="color: {'red' if obj.price_tolerance_exceeded else 'green'};">
                {abs(obj.price_variance_pct):.2f}% {'(EXCEEDED)' if obj.price_tolerance_exceeded else '(OK)'}
            </span>
        </div>
        """
        return format_html(html)
    get_tolerance_check.short_description = 'Tolerance Check'


@admin.register(MatchException)
class MatchExceptionAdmin(admin.ModelAdmin):
    list_display = [
        'exception_number', 'get_type_colored', 'get_severity_colored',
        'get_resolution_status', 'variance_percentage',
        'financial_impact', 'created_at'
    ]
    list_filter = [
        'exception_type', 'severity', 'resolution_status',
        'requires_approval', 'blocks_posting', 'created_at'
    ]
    search_fields = [
        'exception_number', 'description',
        'three_way_match__match_number',
        'three_way_match__vendor_bill_line__vendor_bill__bill_number'
    ]
    readonly_fields = [
        'exception_number', 'three_way_match', 'description',
        'variance_amount', 'variance_percentage', 'financial_impact',
        'requires_approval', 'blocks_posting', 'created_at', 'updated_at',
        'get_exception_details', 'get_match_details'
    ]
    
    fieldsets = (
        ('Exception Information', {
            'fields': (
                'exception_number', 'exception_type', 'severity',
                'description', 'get_exception_details'
            )
        }),
        ('Match Reference', {
            'fields': (
                'three_way_match', 'get_match_details'
            )
        }),
        ('Variance Details', {
            'fields': (
                'variance_amount', 'variance_percentage', 'financial_impact'
            )
        }),
        ('Resolution', {
            'fields': (
                'resolution_status', 'resolution_action', 'resolution_notes',
                'resolved_by', 'resolved_date'
            )
        }),
        ('Approval', {
            'fields': (
                'requires_approval', 'approved_by', 'approved_date'
            )
        }),
        ('Blocking Status', {
            'fields': (
                'blocks_posting',
            )
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'action_resolve', 'action_waive', 'action_approve_waiver'
    ]
    
    def get_type_colored(self, obj):
        """Color-coded exception type"""
        colors = {
            'QUANTITY_OVER': 'darkorange',
            'QUANTITY_UNDER': 'orange',
            'PRICE_OVER': 'darkred',
            'PRICE_UNDER': 'red',
            'PO_NOT_FOUND': 'gray',
            'GRN_NOT_FOUND': 'gray',
            'ITEM_MISMATCH': 'purple',
            'DUPLICATE_BILL': 'brown',
            'OTHER': 'black',
        }
        color = colors.get(obj.exception_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_exception_type_display()
        )
    get_type_colored.short_description = 'Exception Type'
    
    def get_severity_colored(self, obj):
        """Color-coded severity"""
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'darkred',
        }
        color = colors.get(obj.severity, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_severity_display()
        )
    get_severity_colored.short_description = 'Severity'
    
    def get_resolution_status(self, obj):
        """Resolution status display"""
        colors = {
            'UNRESOLVED': 'red',
            'IN_REVIEW': 'orange',
            'RESOLVED': 'green',
            'WAIVED': 'blue',
        }
        color = colors.get(obj.resolution_status, 'black')
        icon = '✓' if obj.resolution_status == 'RESOLVED' else '○'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_resolution_status_display()
        )
    get_resolution_status.short_description = 'Resolution'
    
    def get_exception_details(self, obj):
        """Detailed exception information"""
        html = f"""
        <div style="padding: 10px; background: #fff3cd; border-radius: 5px;">
            <strong>{obj.get_exception_type_display()}</strong><br><br>
            {obj.description}<br><br>
            
            <strong>Variance:</strong> {obj.variance_amount} ({obj.variance_percentage:.2f}%)<br>
            <strong>Financial Impact:</strong> {obj.financial_impact}<br>
            <strong>Severity:</strong> <span style="color: {'red' if obj.severity == 'CRITICAL' else 'orange'};">
                {obj.get_severity_display()}
            </span><br>
            <strong>Blocks Posting:</strong> {'Yes' if obj.blocks_posting else 'No'}<br>
            <strong>Requires Approval:</strong> {'Yes' if obj.requires_approval else 'No'}
        </div>
        """
        return format_html(html)
    get_exception_details.short_description = 'Exception Details'
    
    def get_match_details(self, obj):
        """Match details"""
        match = obj.three_way_match
        bill = match.vendor_bill_line.vendor_bill
        
        html = f"""
        <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
            <strong>Match:</strong> {match.match_number}<br>
            <strong>Vendor Bill:</strong> <a href="{reverse('admin:vendor_bill_vendorbill_change', args=[bill.id])}">{bill.bill_number}</a><br>
            <strong>Supplier:</strong> {bill.supplier.name}<br>
            <strong>Item:</strong> {match.catalog_item.item_code}<br>
            <strong>PO:</strong> {match.po_number or 'N/A'}<br>
            <strong>GRN:</strong> {match.grn_line.goods_receipt.receipt_number if match.grn_line else 'N/A'}
        </div>
        """
        return format_html(html)
    get_match_details.short_description = 'Match Details'
    
    def action_resolve(self, request, queryset):
        """Resolve exceptions"""
        count = 0
        for exc in queryset:
            if exc.resolution_status == 'UNRESOLVED':
                try:
                    exc.resolve(request.user, 'WAIVE', 'Resolved via admin action')
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error resolving {exc.exception_number}: {e}", level='error')
        
        self.message_user(request, f"Resolved {count} exceptions")
    action_resolve.short_description = "Resolve selected exceptions"
    
    def action_waive(self, request, queryset):
        """Waive exceptions"""
        count = 0
        for exc in queryset:
            try:
                exc.waive(request.user, 'Waived via admin action')
                count += 1
            except Exception as e:
                self.message_user(request, f"Error waiving {exc.exception_number}: {e}", level='error')
        
        self.message_user(request, f"Waived {count} exceptions")
    action_waive.short_description = "Waive selected exceptions"
    
    def action_approve_waiver(self, request, queryset):
        """Approve exception waivers"""
        count = 0
        for exc in queryset:
            if exc.requires_approval and not exc.approved_by:
                try:
                    exc.approve_waiver(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error approving {exc.exception_number}: {e}", level='error')
        
        self.message_user(request, f"Approved {count} exception waivers")
    action_approve_waiver.short_description = "Approve waivers for selected exceptions"


@admin.register(MatchTolerance)
class MatchToleranceAdmin(admin.ModelAdmin):
    list_display = [
        'get_scope_display_detailed', 'quantity_tolerance_pct',
        'price_tolerance_pct', 'auto_approve_threshold', 'is_active'
    ]
    list_filter = ['scope', 'is_active']
    search_fields = ['supplier__name', 'catalog_item__item_code']
    
    fieldsets = (
        ('Scope', {
            'fields': ('scope', 'supplier', 'catalog_item')
        }),
        ('Tolerances', {
            'fields': (
                'quantity_tolerance_pct', 'price_tolerance_pct',
                'auto_approve_threshold'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_scope_display_detailed(self, obj):
        """Detailed scope display"""
        if obj.scope == 'GLOBAL':
            return format_html('<strong style="color: blue;">GLOBAL</strong>')
        elif obj.scope == 'SUPPLIER' and obj.supplier:
            return format_html('SUPPLIER: {}', obj.supplier.name)
        elif obj.scope == 'ITEM' and obj.catalog_item:
            return format_html('ITEM: {}', obj.catalog_item.item_code)
        else:
            return obj.get_scope_display()
    get_scope_display_detailed.short_description = 'Scope'

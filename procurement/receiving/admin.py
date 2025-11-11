"""
Admin interfaces for Receiving and Quality Control.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Sum, Count
from .models import (
    Warehouse, StorageLocation, GoodsReceipt, GRNLine,
    QualityInspection, NonConformance, ReturnToVendor, RTVLine
)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'warehouse_type', 'city',
        'country', 'manager', 'is_active'
    ]
    list_filter = ['is_active', 'warehouse_type', 'country']
    search_fields = ['code', 'name', 'city']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['code', 'name', 'description', 'warehouse_type']
        }),
        ('Address', {
            'fields': [
                'address_line1', 'address_line2',
                'city', 'state', 'postal_code', 'country'
            ]
        }),
        ('Management', {
            'fields': ['manager', 'is_active']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_code', 'warehouse', 'name',
        'aisle', 'rack', 'shelf', 'bin',
        'is_quarantine', 'is_active'
    ]
    list_filter = ['warehouse', 'is_active', 'is_quarantine']
    search_fields = ['code', 'name', 'aisle', 'rack']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Location', {
            'fields': ['warehouse', 'code', 'name']
        }),
        ('Hierarchy', {
            'fields': ['aisle', 'rack', 'shelf', 'bin']
        }),
        ('Capacity', {
            'fields': ['max_weight', 'max_volume']
        }),
        ('Status', {
            'fields': ['is_active', 'is_quarantine']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_full_code(self, obj):
        return str(obj)
    get_full_code.short_description = 'Full Code'


class GRNLineInline(admin.TabularInline):
    model = GRNLine
    extra = 1
    fields = [
        'line_number', 'catalog_item', 'ordered_quantity',
        'received_quantity', 'unit_of_measure',
        'receipt_status', 'condition', 'lot_number'
    ]
    readonly_fields = ['line_number', 'receipt_status']


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = [
        'grn_number', 'get_status_colored', 'supplier',
        'receipt_date', 'warehouse', 'po_reference',
        'get_inspection_status_colored', 'received_by'
    ]
    list_filter = [
        'status', 'inspection_status', 'receipt_date',
        'warehouse', 'requires_inspection'
    ]
    search_fields = [
        'grn_number', 'po_reference', 'delivery_note_number',
        'supplier__name'
    ]
    readonly_fields = [
        'grn_number', 'completed_at', 'created_at',
        'updated_at', 'created_by', 'get_receipt_summary'
    ]
    
    date_hierarchy = 'receipt_date'
    inlines = [GRNLineInline]
    
    fieldsets = [
        ('Document Information', {
            'fields': [
                'grn_number', 'receipt_date', 'expected_date',
                'status'
            ]
        }),
        ('Source', {
            'fields': [
                'po_reference', 'source_document_type',
                'source_document_id'
            ]
        }),
        ('Supplier & Delivery', {
            'fields': [
                'supplier', 'delivery_note_number',
                'vehicle_number', 'driver_name'
            ]
        }),
        ('Receiving', {
            'fields': ['warehouse', 'received_by', 'completed_at']
        }),
        ('Quality Inspection', {
            'fields': [
                'requires_inspection', 'inspection_status'
            ]
        }),
        ('Summary', {
            'fields': ['get_receipt_summary']
        }),
        ('Notes', {
            'fields': ['remarks', 'internal_notes'],
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': ['created_at', 'created_by', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['action_complete', 'action_cancel']
    
    def get_status_colored(self, obj):
        colors = {
            'DRAFT': 'gray',
            'IN_PROGRESS': 'blue',
            'COMPLETED': 'green',
            'QUALITY_HOLD': 'orange',
            'REJECTED': 'red',
            'CANCELLED': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    get_status_colored.admin_order_field = 'status'
    
    def get_inspection_status_colored(self, obj):
        if not obj.requires_inspection:
            return '-'
        
        colors = {
            'PENDING': 'orange',
            'IN_PROGRESS': 'blue',
            'PASSED': 'green',
            'FAILED': 'red',
            'WAIVED': 'gray',
        }
        color = colors.get(obj.inspection_status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.inspection_status
        )
    get_inspection_status_colored.short_description = 'Inspection'
    
    def get_receipt_summary(self, obj):
        if not obj.pk:
            return "Save to see summary"
        
        lines = obj.lines.all()
        total_lines = lines.count()
        
        if total_lines == 0:
            return "No lines yet"
        
        status_counts = {
            'PENDING': lines.filter(receipt_status='PENDING').count(),
            'PARTIAL': lines.filter(receipt_status='PARTIAL').count(),
            'FULL': lines.filter(receipt_status='FULL').count(),
            'OVER': lines.filter(receipt_status='OVER').count(),
            'UNDER': lines.filter(receipt_status='UNDER').count(),
        }
        
        tolerance_exceeded = lines.filter(tolerance_exceeded=True).count()
        
        summary_html = f'<div style="font-family: monospace;">'
        summary_html += f'<strong>Total Lines:</strong> {total_lines}<br>'
        summary_html += f'<strong>Pending:</strong> {status_counts["PENDING"]}<br>'
        summary_html += f'<strong>Partial:</strong> {status_counts["PARTIAL"]}<br>'
        summary_html += f'<strong>Full:</strong> {status_counts["FULL"]}<br>'
        if status_counts["OVER"]:
            summary_html += f'<strong style="color: orange;">Over:</strong> {status_counts["OVER"]}<br>'
        if status_counts["UNDER"]:
            summary_html += f'<strong style="color: orange;">Under:</strong> {status_counts["UNDER"]}<br>'
        if tolerance_exceeded:
            summary_html += f'<strong style="color: red;">Tolerance Exceeded:</strong> {tolerance_exceeded}<br>'
        summary_html += f'</div>'
        
        return format_html(summary_html)
    get_receipt_summary.short_description = 'Receipt Summary'
    
    def action_complete(self, request, queryset):
        completed_count = 0
        errors = []
        
        for grn in queryset.filter(status='IN_PROGRESS'):
            try:
                grn.complete(request.user)
                completed_count += 1
            except ValueError as e:
                errors.append(f"GRN {grn.grn_number}: {str(e)}")
        
        if completed_count:
            self.message_user(request, f"Completed {completed_count} GRN(s)")
        
        if errors:
            self.message_user(request, "Errors: " + "; ".join(errors), level='error')
    
    action_complete.short_description = "Complete selected GRNs"
    
    def action_cancel(self, request, queryset):
        cancelled_count = 0
        
        for grn in queryset.exclude(status='COMPLETED'):
            try:
                grn.cancel(request.user, "Bulk cancellation from admin")
                cancelled_count += 1
            except ValueError:
                pass
        
        self.message_user(request, f"Cancelled {cancelled_count} GRN(s)")
    
    action_cancel.short_description = "Cancel selected GRNs"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GRNLine)
class GRNLineAdmin(admin.ModelAdmin):
    list_display = [
        'get_grn_number', 'line_number', 'catalog_item',
        'ordered_quantity', 'received_quantity', 'accepted_quantity',
        'get_receipt_status_colored', 'get_tolerance_display',
        'condition', 'storage_location'
    ]
    list_filter = [
        'receipt_status', 'condition', 'requires_inspection',
        'inspection_completed', 'put_away_completed', 'tolerance_exceeded'
    ]
    search_fields = [
        'goods_receipt__grn_number', 'catalog_item__name',
        'lot_number'
    ]
    readonly_fields = [
        'line_number', 'receipt_status', 'tolerance_exceeded',
        'tolerance_message', 'put_away_at', 'put_away_by',
        'created_at', 'updated_at', 'get_quantities_summary'
    ]
    
    fieldsets = [
        ('GRN Reference', {
            'fields': ['goods_receipt', 'line_number', 'po_line_reference']
        }),
        ('Item', {
            'fields': ['catalog_item', 'item_description']
        }),
        ('Quantities', {
            'fields': [
                'ordered_quantity', 'received_quantity',
                'accepted_quantity', 'rejected_quantity',
                'unit_of_measure', 'get_quantities_summary'
            ]
        }),
        ('Tolerance', {
            'fields': [
                'over_tolerance_pct', 'under_tolerance_pct',
                'tolerance_exceeded', 'tolerance_message',
                'receipt_status'
            ]
        }),
        ('Lot/Batch', {
            'fields': [
                'lot_number', 'serial_numbers',
                'manufacturing_date', 'expiry_date'
            ]
        }),
        ('Put-Away', {
            'fields': [
                'storage_location', 'put_away_completed',
                'put_away_at', 'put_away_by'
            ]
        }),
        ('Quality', {
            'fields': [
                'requires_inspection', 'inspection_completed',
                'condition'
            ]
        }),
        ('Notes', {
            'fields': ['remarks'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_grn_number(self, obj):
        return obj.goods_receipt.grn_number
    get_grn_number.short_description = 'GRN Number'
    get_grn_number.admin_order_field = 'goods_receipt__grn_number'
    
    def get_receipt_status_colored(self, obj):
        colors = {
            'PENDING': 'gray',
            'PARTIAL': 'orange',
            'FULL': 'green',
            'OVER': 'purple',
            'UNDER': 'red',
        }
        color = colors.get(obj.receipt_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_receipt_status_display()
        )
    get_receipt_status_colored.short_description = 'Receipt Status'
    
    def get_tolerance_display(self, obj):
        if obj.tolerance_exceeded:
            return format_html('<span style="color: red; font-weight: bold;">⚠ EXCEEDED</span>')
        return format_html('<span style="color: green;">✓ OK</span>')
    get_tolerance_display.short_description = 'Tolerance'
    
    def get_quantities_summary(self, obj):
        if not obj.pk:
            return "Save to see summary"
        
        variance = obj.received_quantity - obj.ordered_quantity
        variance_pct = (variance / obj.ordered_quantity * 100) if obj.ordered_quantity else 0
        
        summary_html = f'<div style="font-family: monospace;">'
        summary_html += f'<strong>Ordered:</strong> {obj.ordered_quantity} {obj.unit_of_measure.code}<br>'
        summary_html += f'<strong>Received:</strong> {obj.received_quantity} {obj.unit_of_measure.code}<br>'
        summary_html += f'<strong>Accepted:</strong> {obj.accepted_quantity} {obj.unit_of_measure.code}<br>'
        if obj.rejected_quantity > 0:
            summary_html += f'<strong style="color: red;">Rejected:</strong> {obj.rejected_quantity} {obj.unit_of_measure.code}<br>'
        
        variance_color = 'green' if abs(variance_pct) <= 5 else 'orange' if abs(variance_pct) <= 10 else 'red'
        summary_html += f'<strong>Variance:</strong> <span style="color: {variance_color};">{variance:+.2f} ({variance_pct:+.1f}%)</span><br>'
        summary_html += f'</div>'
        
        return format_html(summary_html)
    get_quantities_summary.short_description = 'Quantities Summary'


@admin.register(QualityInspection)
class QualityInspectionAdmin(admin.ModelAdmin):
    list_display = [
        'inspection_number', 'get_status_colored', 'inspection_type',
        'goods_receipt', 'inspection_date', 'inspector',
        'passed_quantity', 'failed_quantity', 'get_disposition_display'
    ]
    list_filter = [
        'status', 'inspection_type', 'disposition',
        'inspection_date'
    ]
    search_fields = [
        'inspection_number', 'goods_receipt__grn_number',
        'inspector__username'
    ]
    readonly_fields = [
        'inspection_number', 'approved_at', 'approved_by',
        'completed_at', 'created_at', 'updated_at',
        'get_inspection_summary'
    ]
    
    date_hierarchy = 'inspection_date'
    
    fieldsets = [
        ('Inspection Information', {
            'fields': [
                'inspection_number', 'inspection_date',
                'inspection_type', 'status'
            ]
        }),
        ('Reference', {
            'fields': ['goods_receipt', 'grn_line']
        }),
        ('Inspector', {
            'fields': ['inspector']
        }),
        ('Sampling', {
            'fields': ['sample_size', 'lot_size', 'inspection_criteria']
        }),
        ('Results', {
            'fields': [
                'passed_quantity', 'failed_quantity',
                'defects_found', 'get_inspection_summary'
            ]
        }),
        ('Details', {
            'fields': ['inspection_results', 'inspector_notes']
        }),
        ('Disposition', {
            'fields': ['disposition']
        }),
        ('Approval', {
            'fields': ['approved_by', 'approved_at']
        }),
        ('Completion', {
            'fields': ['completed_at']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['action_complete']
    
    def get_status_colored(self, obj):
        colors = {
            'PENDING': 'gray',
            'IN_PROGRESS': 'blue',
            'PASSED': 'green',
            'FAILED': 'red',
            'CONDITIONAL': 'orange',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    get_status_colored.admin_order_field = 'status'
    
    def get_disposition_display(self, obj):
        if not obj.disposition:
            return '-'
        
        colors = {
            'ACCEPT': 'green',
            'REJECT': 'red',
            'REWORK': 'orange',
            'SORT': 'orange',
            'RTV': 'red',
            'SCRAP': 'red',
        }
        color = colors.get(obj.disposition, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_disposition_display()
        )
    get_disposition_display.short_description = 'Disposition'
    
    def get_inspection_summary(self, obj):
        if not obj.pk:
            return "Save to see summary"
        
        total = obj.passed_quantity + obj.failed_quantity
        if total == 0:
            return "No quantities recorded"
        
        pass_rate = (obj.passed_quantity / total * 100)
        fail_rate = (obj.failed_quantity / total * 100)
        
        summary_html = f'<div style="font-family: monospace;">'
        summary_html += f'<strong>Total Inspected:</strong> {total}<br>'
        summary_html += f'<strong style="color: green;">Passed:</strong> {obj.passed_quantity} ({pass_rate:.1f}%)<br>'
        summary_html += f'<strong style="color: red;">Failed:</strong> {obj.failed_quantity} ({fail_rate:.1f}%)<br>'
        
        if obj.defects_found:
            summary_html += f'<strong>Defects:</strong> {len(obj.defects_found)}<br>'
        
        summary_html += f'</div>'
        
        return format_html(summary_html)
    get_inspection_summary.short_description = 'Inspection Summary'
    
    def action_complete(self, request, queryset):
        completed_count = 0
        errors = []
        
        for inspection in queryset.filter(status='IN_PROGRESS'):
            try:
                inspection.complete(request.user)
                completed_count += 1
            except ValueError as e:
                errors.append(f"Inspection {inspection.inspection_number}: {str(e)}")
        
        if completed_count:
            self.message_user(request, f"Completed {completed_count} inspection(s)")
        
        if errors:
            self.message_user(request, "Errors: " + "; ".join(errors), level='error')
    
    action_complete.short_description = "Complete selected inspections"


@admin.register(NonConformance)
class NonConformanceAdmin(admin.ModelAdmin):
    list_display = [
        'ncr_number', 'get_status_colored', 'get_severity_colored',
        'issue_category', 'goods_receipt', 'ncr_date',
        'reported_by', 'supplier_notified'
    ]
    list_filter = [
        'status', 'severity', 'issue_category',
        'supplier_notified', 'ncr_date'
    ]
    search_fields = [
        'ncr_number', 'issue_description',
        'goods_receipt__grn_number'
    ]
    readonly_fields = [
        'ncr_number', 'supplier_notified_at',
        'resolved_at', 'resolved_by',
        'created_at', 'updated_at'
    ]
    
    date_hierarchy = 'ncr_date'
    
    fieldsets = [
        ('NCR Information', {
            'fields': [
                'ncr_number', 'ncr_date', 'reported_by',
                'severity', 'status'
            ]
        }),
        ('Reference', {
            'fields': [
                'goods_receipt', 'grn_line', 'quality_inspection'
            ]
        }),
        ('Issue', {
            'fields': [
                'issue_category', 'issue_description',
                'affected_quantity'
            ]
        }),
        ('Analysis', {
            'fields': ['root_cause']
        }),
        ('Actions', {
            'fields': ['corrective_action', 'preventive_action']
        }),
        ('Supplier Notification', {
            'fields': ['supplier_notified', 'supplier_notified_at']
        }),
        ('Resolution', {
            'fields': [
                'resolved_by', 'resolved_at', 'resolution_notes'
            ]
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['action_close', 'action_notify_supplier']
    
    def get_status_colored(self, obj):
        colors = {
            'OPEN': 'red',
            'INVESTIGATION': 'orange',
            'ACTION_PENDING': 'blue',
            'RESOLVED': 'green',
            'CLOSED': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    get_status_colored.admin_order_field = 'status'
    
    def get_severity_colored(self, obj):
        colors = {
            'MINOR': 'green',
            'MAJOR': 'orange',
            'CRITICAL': 'red',
        }
        color = colors.get(obj.severity, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_severity_display()
        )
    get_severity_colored.short_description = 'Severity'
    get_severity_colored.admin_order_field = 'severity'
    
    def action_close(self, request, queryset):
        closed_count = 0
        
        for ncr in queryset.exclude(status='CLOSED'):
            ncr.close(request.user, "Closed from admin interface")
            closed_count += 1
        
        self.message_user(request, f"Closed {closed_count} NCR(s)")
    
    action_close.short_description = "Close selected NCRs"
    
    def action_notify_supplier(self, request, queryset):
        notified_count = 0
        
        for ncr in queryset.filter(supplier_notified=False):
            ncr.supplier_notified = True
            ncr.supplier_notified_at = timezone.now()
            ncr.save()
            notified_count += 1
        
        self.message_user(request, f"Marked {notified_count} NCR(s) as notified to supplier")
    
    action_notify_supplier.short_description = "Mark as notified to supplier"


class RTVLineInline(admin.TabularInline):
    model = RTVLine
    extra = 1
    fields = [
        'line_number', 'grn_line', 'catalog_item',
        'return_quantity', 'unit_of_measure', 'unit_price',
        'lot_number'
    ]
    readonly_fields = ['line_number']


@admin.register(ReturnToVendor)
class ReturnToVendorAdmin(admin.ModelAdmin):
    list_display = [
        'rtv_number', 'get_status_colored', 'supplier',
        'rtv_date', 'return_reason', 'total_amount',
        'credit_received', 'created_by'
    ]
    list_filter = [
        'status', 'return_reason', 'rtv_date',
        'credit_received'
    ]
    search_fields = [
        'rtv_number', 'supplier__name',
        'debit_memo_number', 'tracking_number'
    ]
    readonly_fields = [
        'rtv_number', 'total_amount',
        'created_at', 'updated_at', 'created_by',
        'get_rtv_summary'
    ]
    
    date_hierarchy = 'rtv_date'
    inlines = [RTVLineInline]
    
    fieldsets = [
        ('RTV Information', {
            'fields': [
                'rtv_number', 'rtv_date', 'status'
            ]
        }),
        ('Reference', {
            'fields': ['goods_receipt', 'supplier', 'non_conformance']
        }),
        ('Return Reason', {
            'fields': ['return_reason', 'return_reason_details']
        }),
        ('Shipping', {
            'fields': [
                'ship_date', 'carrier', 'tracking_number'
            ]
        }),
        ('Financial', {
            'fields': [
                'currency', 'total_amount', 'debit_memo_number',
                'debit_memo_date', 'credit_received',
                'credit_received_date'
            ]
        }),
        ('Summary', {
            'fields': ['get_rtv_summary']
        }),
        ('Notes', {
            'fields': ['remarks'],
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': ['created_at', 'created_by', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['action_submit', 'action_mark_credited']
    
    def get_status_colored(self, obj):
        colors = {
            'DRAFT': 'gray',
            'SUBMITTED': 'blue',
            'APPROVED': 'green',
            'SHIPPED': 'purple',
            'RECEIVED_BY_SUPPLIER': 'orange',
            'CREDITED': 'green',
            'CLOSED': 'gray',
            'REJECTED': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    get_status_colored.admin_order_field = 'status'
    
    def get_rtv_summary(self, obj):
        if not obj.pk:
            return "Save to see summary"
        
        lines = obj.lines.all()
        total_lines = lines.count()
        
        if total_lines == 0:
            return "No lines yet"
        
        total_qty = sum(line.return_quantity for line in lines)
        
        summary_html = f'<div style="font-family: monospace;">'
        summary_html += f'<strong>Total Lines:</strong> {total_lines}<br>'
        summary_html += f'<strong>Total Quantity:</strong> {total_qty}<br>'
        summary_html += f'<strong>Total Value:</strong> {obj.total_amount:,.2f} {obj.currency.code}<br>'
        
        if obj.credit_received:
            summary_html += f'<strong style="color: green;">Credit Received:</strong> {obj.credit_received_date}<br>'
        else:
            summary_html += f'<strong style="color: orange;">Credit Pending</strong><br>'
        
        summary_html += f'</div>'
        
        return format_html(summary_html)
    get_rtv_summary.short_description = 'RTV Summary'
    
    def action_submit(self, request, queryset):
        submitted_count = 0
        errors = []
        
        for rtv in queryset.filter(status='DRAFT'):
            try:
                rtv.submit(request.user)
                submitted_count += 1
            except ValueError as e:
                errors.append(f"RTV {rtv.rtv_number}: {str(e)}")
        
        if submitted_count:
            self.message_user(request, f"Submitted {submitted_count} RTV(s)")
        
        if errors:
            self.message_user(request, "Errors: " + "; ".join(errors), level='error')
    
    action_submit.short_description = "Submit selected RTVs"
    
    def action_mark_credited(self, request, queryset):
        credited_count = 0
        
        for rtv in queryset.filter(credit_received=False):
            rtv.credit_received = True
            rtv.credit_received_date = timezone.now().date()
            rtv.status = 'CREDITED'
            rtv.save()
            credited_count += 1
        
        self.message_user(request, f"Marked {credited_count} RTV(s) as credited")
    
    action_mark_credited.short_description = "Mark as credit received"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RTVLine)
class RTVLineAdmin(admin.ModelAdmin):
    list_display = [
        'get_rtv_number', 'line_number', 'catalog_item',
        'return_quantity', 'unit_of_measure', 'unit_price',
        'get_line_total_display', 'lot_number'
    ]
    list_filter = ['unit_of_measure']
    search_fields = [
        'rtv__rtv_number', 'catalog_item__name',
        'lot_number'
    ]
    readonly_fields = [
        'line_number', 'created_at', 'updated_at',
        'get_line_total'
    ]
    
    fieldsets = [
        ('RTV Reference', {
            'fields': ['rtv', 'line_number']
        }),
        ('Item', {
            'fields': ['grn_line', 'catalog_item']
        }),
        ('Quantity & Pricing', {
            'fields': [
                'return_quantity', 'unit_of_measure',
                'unit_price', 'get_line_total'
            ]
        }),
        ('Lot/Serial', {
            'fields': ['lot_number', 'serial_numbers']
        }),
        ('Notes', {
            'fields': ['remarks'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_rtv_number(self, obj):
        return obj.rtv.rtv_number
    get_rtv_number.short_description = 'RTV Number'
    get_rtv_number.admin_order_field = 'rtv__rtv_number'
    
    def get_line_total_display(self, obj):
        return format_html(
            '<span style="font-weight: bold;">{:,.2f}</span>',
            obj.get_line_total()
        )
    get_line_total_display.short_description = 'Line Total'
    
    def get_line_total(self, obj):
        if not obj.pk:
            return "Save to calculate"
        return format_html('{:,.2f}', obj.get_line_total())
    get_line_total.short_description = 'Line Total'

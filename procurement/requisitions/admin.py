"""
Admin interfaces for Purchase Requisition management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum
from .models import CostCenter, Project, PRHeader, PRLine, PRToPOLineMapping


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'manager', 'annual_budget',
        'get_committed_display', 'get_available_display', 'is_active'
    ]
    list_filter = ['is_active', 'manager']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_budget_summary']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['code', 'name', 'description', 'parent']
        }),
        ('Management', {
            'fields': ['manager', 'is_active']
        }),
        ('Budget', {
            'fields': ['annual_budget', 'get_budget_summary']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_committed_display(self, obj):
        committed = obj.get_total_committed()
        return format_html(
            '<span style="color: orange;">{:,.2f}</span>',
            committed
        )
    get_committed_display.short_description = 'Committed'
    
    def get_available_display(self, obj):
        available = obj.get_available_budget()
        color = 'green' if available > 0 else 'red'
        return format_html(
            '<span style="color: {};">{:,.2f}</span>',
            color, available
        )
    get_available_display.short_description = 'Available'
    
    def get_budget_summary(self, obj):
        if not obj.pk:
            return "Save to see budget summary"
        
        committed = obj.get_total_committed()
        available = obj.get_available_budget()
        utilization = (committed / obj.annual_budget * 100) if obj.annual_budget else 0
        
        return format_html(
            '<div style="font-family: monospace;">'
            '<strong>Annual Budget:</strong> {:,.2f}<br>'
            '<strong>Committed:</strong> {:,.2f} ({:.1f}%)<br>'
            '<strong>Available:</strong> {:,.2f}<br>'
            '</div>',
            obj.annual_budget, committed, utilization, available
        )
    get_budget_summary.short_description = 'Budget Summary'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'project_manager', 'status',
        'start_date', 'end_date', 'budget', 'get_committed_display'
    ]
    list_filter = ['status', 'project_manager', 'start_date']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_budget_summary']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['code', 'name', 'description', 'project_manager']
        }),
        ('Timeline', {
            'fields': ['start_date', 'end_date', 'status']
        }),
        ('Budget', {
            'fields': ['budget', 'get_budget_summary']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_committed_display(self, obj):
        committed = obj.get_total_committed()
        return format_html(
            '<span style="color: orange;">{:,.2f}</span>',
            committed
        )
    get_committed_display.short_description = 'Committed'
    
    def get_budget_summary(self, obj):
        if not obj.pk:
            return "Save to see budget summary"
        
        committed = obj.get_total_committed()
        available = obj.get_available_budget()
        utilization = (committed / obj.budget * 100) if obj.budget else 0
        
        return format_html(
            '<div style="font-family: monospace;">'
            '<strong>Budget:</strong> {:,.2f}<br>'
            '<strong>Committed:</strong> {:,.2f} ({:.1f}%)<br>'
            '<strong>Available:</strong> {:,.2f}<br>'
            '</div>',
            obj.budget, committed, utilization, available
        )
    get_budget_summary.short_description = 'Budget Summary'


class PRLineInline(admin.TabularInline):
    model = PRLine
    extra = 1
    fields = [
        'line_number', 'item_description', 'catalog_item',
        'quantity', 'unit_of_measure', 'estimated_unit_price',
        'need_by_date', 'suggested_supplier', 'tax_rate'
    ]
    readonly_fields = ['line_number']


@admin.register(PRHeader)
class PRHeaderAdmin(admin.ModelAdmin):
    list_display = [
        'pr_number', 'get_status_display_colored', 'title',
        'requestor', 'pr_date', 'required_date',
        'total_amount', 'currency', 'get_budget_check_display',
        'priority'
    ]
    list_filter = [
        'status', 'priority', 'pr_date', 'cost_center',
        'project', 'budget_check_passed'
    ]
    search_fields = [
        'pr_number', 'title', 'description',
        'requestor__username', 'requestor__email'
    ]
    readonly_fields = [
        'pr_number', 'subtotal', 'tax_amount', 'total_amount',
        'budget_check_passed', 'budget_check_message', 'budget_checked_at',
        'catalog_suggestions_generated',
        'submitted_at', 'submitted_by',
        'approved_at', 'approved_by',
        'rejected_at', 'rejected_by',
        'converted_at', 'converted_by',
        'cancelled_at', 'cancelled_by',
        'created_at', 'updated_at', 'created_by',
        'get_workflow_history'
    ]
    
    date_hierarchy = 'pr_date'
    inlines = [PRLineInline]
    
    fieldsets = [
        ('Document Information', {
            'fields': [
                'pr_number', 'pr_date', 'required_date',
                'status', 'priority'
            ]
        }),
        ('Requestor & Organization', {
            'fields': [
                'requestor', 'cost_center', 'project'
            ]
        }),
        ('Details', {
            'fields': [
                'title', 'description', 'business_justification'
            ]
        }),
        ('Financial', {
            'fields': [
                'currency', 'subtotal', 'tax_amount', 'total_amount'
            ]
        }),
        ('Budget Check', {
            'fields': [
                'budget_check_passed', 'budget_check_message',
                'budget_checked_at'
            ],
            'classes': ['collapse']
        }),
        ('Catalog & Vendor', {
            'fields': [
                'catalog_suggestions_generated', 'can_split_by_vendor'
            ]
        }),
        ('Workflow History', {
            'fields': ['get_workflow_history'],
            'classes': ['collapse']
        }),
        ('Rejection/Cancellation', {
            'fields': [
                'rejection_reason', 'cancellation_reason'
            ],
            'classes': ['collapse']
        }),
        ('Notes', {
            'fields': ['internal_notes'],
            'classes': ['collapse']
        }),
        ('Audit Trail', {
            'fields': [
                'created_at', 'created_by', 'updated_at'
            ],
            'classes': ['collapse']
        }),
    ]
    
    actions = [
        'action_submit',
        'action_approve',
        'action_check_budget',
        'action_generate_catalog_suggestions',
        'action_cancel'
    ]
    
    def get_status_display_colored(self, obj):
        colors = {
            'DRAFT': 'gray',
            'SUBMITTED': 'blue',
            'APPROVED': 'green',
            'REJECTED': 'red',
            'CONVERTED': 'purple',
            'CANCELLED': 'orange',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_display_colored.short_description = 'Status'
    get_status_display_colored.admin_order_field = 'status'
    
    def get_budget_check_display(self, obj):
        if not obj.budget_checked_at:
            return format_html('<span style="color: gray;">Not Checked</span>')
        
        if obj.budget_check_passed:
            return format_html('<span style="color: green;">✓ Passed</span>')
        else:
            return format_html('<span style="color: red;">✗ Failed</span>')
    get_budget_check_display.short_description = 'Budget Check'
    
    def get_workflow_history(self, obj):
        if not obj.pk:
            return "Save to see workflow history"
        
        history = []
        
        if obj.submitted_at:
            history.append(f"Submitted: {obj.submitted_at.strftime('%Y-%m-%d %H:%M')} by {obj.submitted_by}")
        
        if obj.approved_at:
            history.append(f"Approved: {obj.approved_at.strftime('%Y-%m-%d %H:%M')} by {obj.approved_by}")
        
        if obj.rejected_at:
            history.append(f"Rejected: {obj.rejected_at.strftime('%Y-%m-%d %H:%M')} by {obj.rejected_by}")
            if obj.rejection_reason:
                history.append(f"Reason: {obj.rejection_reason}")
        
        if obj.converted_at:
            history.append(f"Converted: {obj.converted_at.strftime('%Y-%m-%d %H:%M')} by {obj.converted_by}")
        
        if obj.cancelled_at:
            history.append(f"Cancelled: {obj.cancelled_at.strftime('%Y-%m-%d %H:%M')} by {obj.cancelled_by}")
            if obj.cancellation_reason:
                history.append(f"Reason: {obj.cancellation_reason}")
        
        return format_html('<br>'.join(history)) if history else "No workflow actions yet"
    get_workflow_history.short_description = 'Workflow History'
    
    def action_submit(self, request, queryset):
        submitted_count = 0
        errors = []
        
        for pr in queryset.filter(status='DRAFT'):
            try:
                pr.submit(request.user)
                submitted_count += 1
            except ValueError as e:
                errors.append(f"PR {pr.pr_number}: {str(e)}")
        
        if submitted_count:
            self.message_user(request, f"Successfully submitted {submitted_count} PR(s)")
        
        if errors:
            self.message_user(request, "Errors: " + "; ".join(errors), level='error')
    
    action_submit.short_description = "Submit selected PRs"
    
    def action_approve(self, request, queryset):
        approved_count = 0
        errors = []
        
        for pr in queryset.filter(status='SUBMITTED'):
            try:
                pr.approve(request.user)
                approved_count += 1
            except ValueError as e:
                errors.append(f"PR {pr.pr_number}: {str(e)}")
        
        if approved_count:
            self.message_user(request, f"Successfully approved {approved_count} PR(s)")
        
        if errors:
            self.message_user(request, "Errors: " + "; ".join(errors), level='error')
    
    action_approve.short_description = "Approve selected PRs"
    
    def action_check_budget(self, request, queryset):
        checked_count = 0
        
        for pr in queryset:
            pr.check_budget()
            pr.save()
            checked_count += 1
        
        self.message_user(request, f"Budget check performed on {checked_count} PR(s)")
    
    action_check_budget.short_description = "Check budget for selected PRs"
    
    def action_generate_catalog_suggestions(self, request, queryset):
        total_suggestions = 0
        
        for pr in queryset:
            count = pr.generate_catalog_suggestions()
            total_suggestions += count
        
        self.message_user(
            request,
            f"Generated catalog suggestions for {total_suggestions} line(s)"
        )
    
    action_generate_catalog_suggestions.short_description = "Generate catalog suggestions"
    
    def action_cancel(self, request, queryset):
        cancelled_count = 0
        
        for pr in queryset.exclude(status__in=['CONVERTED', 'CANCELLED']):
            try:
                pr.cancel(request.user, "Bulk cancellation from admin")
                cancelled_count += 1
            except ValueError:
                pass
        
        self.message_user(request, f"Cancelled {cancelled_count} PR(s)")
    
    action_cancel.short_description = "Cancel selected PRs"
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PRLine)
class PRLineAdmin(admin.ModelAdmin):
    list_display = [
        'get_pr_number', 'line_number', 'item_description',
        'quantity', 'unit_of_measure', 'estimated_unit_price',
        'get_line_total_display', 'need_by_date',
        'suggested_supplier', 'get_conversion_status_display'
    ]
    list_filter = [
        'conversion_status', 'unit_of_measure',
        'suggested_supplier', 'need_by_date'
    ]
    search_fields = [
        'pr_header__pr_number', 'item_description',
        'specifications', 'catalog_item__name'
    ]
    readonly_fields = [
        'line_number', 'tax_amount', 'created_at', 'updated_at',
        'get_line_totals', 'conversion_status', 'quantity_converted',
        'get_conversion_info'
    ]
    
    fieldsets = [
        ('PR Reference', {
            'fields': ['pr_header', 'line_number']
        }),
        ('Item Details', {
            'fields': [
                'item_description', 'specifications',
                'catalog_item'
            ]
        }),
        ('Quantity & Pricing', {
            'fields': [
                'quantity', 'unit_of_measure',
                'estimated_unit_price', 'get_line_totals'
            ]
        }),
        ('Tax', {
            'fields': ['tax_code', 'tax_rate', 'tax_amount']
        }),
        ('Dates & Supplier', {
            'fields': [
                'need_by_date', 'suggested_supplier'
            ]
        }),
        ('Account Coding', {
            'fields': ['gl_account']
        }),
        ('Conversion Tracking', {
            'fields': ['conversion_status', 'quantity_converted', 'get_conversion_info']
        }),
        ('Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_pr_number(self, obj):
        return obj.pr_header.pr_number
    get_pr_number.short_description = 'PR Number'
    get_pr_number.admin_order_field = 'pr_header__pr_number'
    
    def get_line_total_display(self, obj):
        return format_html(
            '<span style="font-weight: bold;">{:,.2f}</span>',
            obj.get_line_total()
        )
    get_line_total_display.short_description = 'Line Total'
    
    def get_line_totals(self, obj):
        if not obj.pk:
            return "Save to calculate totals"
        
        subtotal = obj.get_line_total()
        total_with_tax = obj.get_line_total_with_tax()
        
        return format_html(
            '<div style="font-family: monospace;">'
            '<strong>Subtotal:</strong> {:,.2f}<br>'
            '<strong>Tax:</strong> {:,.2f}<br>'
            '<strong>Total:</strong> {:,.2f}<br>'
            '</div>',
            subtotal, obj.tax_amount, total_with_tax
        )
    get_line_totals.short_description = 'Line Totals'
    
    def get_conversion_status_display(self, obj):
        """Display conversion status with color coding."""
        status_colors = {
            'NOT_CONVERTED': 'gray',
            'PARTIALLY_CONVERTED': 'orange',
            'FULLY_CONVERTED': 'green',
        }
        color = status_colors.get(obj.conversion_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_conversion_status_display()
        )
    get_conversion_status_display.short_description = 'Conversion Status'
    get_conversion_status_display.admin_order_field = 'conversion_status'
    
    def get_conversion_info(self, obj):
        """Display detailed conversion information."""
        if not obj.pk:
            return "Save to see conversion info"
        
        # Get related PO mappings
        mappings = obj.po_line_mappings.select_related('po_line__po_header').all()
        
        if not mappings.exists():
            return format_html('<em>Not yet converted to any PO</em>')
        
        info = '<div style="font-family: monospace;">'
        info += f'<strong>Quantity:</strong> {obj.quantity}<br>'
        info += f'<strong>Converted:</strong> {obj.quantity_converted}<br>'
        info += f'<strong>Remaining:</strong> {obj.quantity_remaining}<br>'
        info += '<br><strong>Converted to POs:</strong><br>'
        
        for mapping in mappings:
            po_number = mapping.po_line.po_header.po_number
            po_line_num = mapping.po_line.line_number
            qty = mapping.quantity_converted
            info += f'• {po_number} Line {po_line_num}: {qty} units<br>'
        
        info += '</div>'
        return format_html(info)
    get_conversion_info.short_description = 'Conversion Details'


@admin.register(PRToPOLineMapping)
class PRToPOLineMappingAdmin(admin.ModelAdmin):
    """Admin interface for PR to PO Line Mapping."""
    
    list_display = [
        'get_pr_info', 'get_po_info', 'quantity_converted',
        'created_at', 'created_by'
    ]
    list_filter = ['created_at', 'created_by']
    search_fields = [
        'pr_line__pr_header__pr_number',
        'po_line__po_header__po_number',
        'pr_line__item_description'
    ]
    readonly_fields = ['created_at', 'get_mapping_details']
    
    fieldsets = [
        ('Source PR Line', {
            'fields': ['pr_line', 'get_pr_line_info']
        }),
        ('Target PO Line', {
            'fields': ['po_line', 'get_po_line_info']
        }),
        ('Conversion Details', {
            'fields': ['quantity_converted', 'notes', 'get_mapping_details']
        }),
        ('Tracking', {
            'fields': ['created_at', 'created_by']
        }),
    ]
    
    def get_pr_info(self, obj):
        """Display PR information."""
        return format_html(
            '{} Line {}',
            obj.pr_line.pr_header.pr_number,
            obj.pr_line.line_number
        )
    get_pr_info.short_description = 'PR Line'
    get_pr_info.admin_order_field = 'pr_line__pr_header__pr_number'
    
    def get_po_info(self, obj):
        """Display PO information."""
        return format_html(
            '{} Line {}',
            obj.po_line.po_header.po_number,
            obj.po_line.line_number
        )
    get_po_info.short_description = 'PO Line'
    get_po_info.admin_order_field = 'po_line__po_header__po_number'
    
    def get_pr_line_info(self, obj):
        """Display detailed PR line information."""
        if not obj.pk:
            return "Save to see details"
        
        pr_line = obj.pr_line
        return format_html(
            '<div style="font-family: monospace;">'
            '<strong>PR:</strong> {}<br>'
            '<strong>Line:</strong> {}<br>'
            '<strong>Item:</strong> {}<br>'
            '<strong>Total Qty:</strong> {}<br>'
            '<strong>Converted:</strong> {}<br>'
            '<strong>Remaining:</strong> {}<br>'
            '</div>',
            pr_line.pr_header.pr_number,
            pr_line.line_number,
            pr_line.item_description,
            pr_line.quantity,
            pr_line.quantity_converted,
            pr_line.quantity_remaining
        )
    get_pr_line_info.short_description = 'PR Line Details'
    
    def get_po_line_info(self, obj):
        """Display detailed PO line information."""
        if not obj.pk:
            return "Save to see details"
        
        po_line = obj.po_line
        return format_html(
            '<div style="font-family: monospace;">'
            '<strong>PO:</strong> {}<br>'
            '<strong>Line:</strong> {}<br>'
            '<strong>Item:</strong> {}<br>'
            '<strong>Quantity:</strong> {}<br>'
            '<strong>Unit Price:</strong> {:,.2f}<br>'
            '<strong>Line Total:</strong> {:,.2f}<br>'
            '</div>',
            po_line.po_header.po_number,
            po_line.line_number,
            po_line.item_description,
            po_line.quantity,
            po_line.unit_price,
            po_line.line_total
        )
    get_po_line_info.short_description = 'PO Line Details'
    
    def get_mapping_details(self, obj):
        """Display mapping summary."""
        if not obj.pk:
            return "Save to see mapping details"
        
        percentage = (obj.quantity_converted / obj.pr_line.quantity * 100) if obj.pr_line.quantity else 0
        
        return format_html(
            '<div style="font-family: monospace; background: #f0f0f0; padding: 10px; border-radius: 5px;">'
            '<strong>This mapping converts:</strong><br>'
            '{} units ({:.1f}% of PR line)<br>'
            '<br>'
            '<strong>From:</strong> {} Line {}<br>'
            '<strong>To:</strong> {} Line {}<br>'
            '<br>'
            '<strong>Created:</strong> {} by {}<br>'
            '</div>',
            obj.quantity_converted,
            percentage,
            obj.pr_line.pr_header.pr_number,
            obj.pr_line.line_number,
            obj.po_line.po_header.po_number,
            obj.po_line.line_number,
            obj.created_at.strftime('%Y-%m-%d %H:%M'),
            obj.created_by.username if obj.created_by else 'System'
        )
    get_mapping_details.short_description = 'Mapping Summary'

"""
Payments & Finance Integration Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    TaxJurisdiction, TaxRate, TaxComponent,
    APPaymentBatch, APPaymentLine,
    TaxPeriod, CorporateTaxAccrual,
    PaymentRequest
)


@admin.register(TaxJurisdiction)
class TaxJurisdictionAdmin(admin.ModelAdmin):
    list_display = [
        'country_code', 'country_name', 'get_tax_system_colored',
        'standard_rate', 'tax_period', 'currency', 'is_active'
    ]
    list_filter = ['tax_system', 'tax_period', 'is_active']
    search_fields = ['country_code', 'country_name', 'tax_authority_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Jurisdiction Details', {
            'fields': (
                'country_code', 'country_name', 'tax_system',
                'standard_rate', 'currency'
            )
        }),
        ('Tax Authority', {
            'fields': (
                'tax_authority_name', 'tax_registration_number'
            )
        }),
        ('Periodization', {
            'fields': ('tax_period',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_tax_system_colored(self, obj):
        """Color-coded tax system"""
        colors = {
            'VAT': 'blue',
            'GST': 'green',
            'SALES_TAX': 'orange',
        }
        color = colors.get(obj.tax_system, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_tax_system_display()
        )
    get_tax_system_colored.short_description = 'Tax System'


class TaxComponentInline(admin.TabularInline):
    model = TaxComponent
    extra = 0
    fields = ['component_type', 'component_name', 'component_percentage', 'gl_account', 'is_active']


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = [
        'rate_code', 'jurisdiction', 'get_rate_type_colored',
        'rate_percentage', 'effective_from', 'effective_to',
        'is_active', 'is_default'
    ]
    list_filter = ['jurisdiction', 'rate_type', 'is_active', 'is_default']
    search_fields = ['rate_code', 'rate_name', 'jurisdiction__country_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Rate Details', {
            'fields': (
                'jurisdiction', 'rate_type', 'rate_code',
                'rate_name', 'rate_percentage'
            )
        }),
        ('Description', {
            'fields': ('description', 'applicable_to')
        }),
        ('GL Accounts', {
            'fields': (
                'tax_payable_account', 'tax_receivable_account'
            )
        }),
        ('Effective Dates', {
            'fields': ('effective_from', 'effective_to')
        }),
        ('Status', {
            'fields': ('is_active', 'is_default')
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TaxComponentInline]
    
    def get_rate_type_colored(self, obj):
        """Color-coded rate type"""
        colors = {
            'STANDARD': 'green',
            'ZERO': 'blue',
            'EXEMPT': 'gray',
            'REVERSE_CHARGE': 'orange',
            'REDUCED': 'purple',
        }
        color = colors.get(obj.rate_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_rate_type_display()
        )
    get_rate_type_colored.short_description = 'Rate Type'


class APPaymentLineInline(admin.TabularInline):
    model = APPaymentLine
    extra = 1
    fields = [
        'line_number', 'ap_invoice', 'payment_amount',
        'withholding_tax_rate', 'withholding_tax_amount',
        'discount_taken', 'net_payment_amount', 'is_paid'
    ]
    readonly_fields = ['net_payment_amount', 'is_paid']


@admin.register(APPaymentBatch)
class APPaymentBatchAdmin(admin.ModelAdmin):
    list_display = [
        'batch_number', 'batch_date', 'payment_date',
        'get_status_colored', 'payment_count', 'total_amount',
        'get_finance_status', 'get_reconciliation_status'
    ]
    list_filter = [
        'status', 'payment_method', 'is_reconciled',
        'batch_date', 'payment_date'
    ]
    search_fields = ['batch_number', 'bank_account__account_name']
    readonly_fields = [
        'batch_number', 'total_amount', 'payment_count',
        'journal_entry', 'posted_to_finance_date', 'posted_to_finance_by',
        'is_reconciled', 'reconciled_date', 'reconciled_by',
        'submitted_by', 'submitted_date', 'approved_by', 'approved_date',
        'created_by', 'created_at', 'updated_by', 'updated_at',
        'get_payment_summary', 'get_supplier_breakdown'
    ]
    
    fieldsets = (
        ('Batch Information', {
            'fields': (
                'batch_number', 'batch_date', 'payment_date',
                'status', 'payment_method'
            )
        }),
        ('Bank Details', {
            'fields': ('bank_account', 'currency')
        }),
        ('Totals', {
            'fields': ('total_amount', 'payment_count', 'get_payment_summary')
        }),
        ('Finance Integration', {
            'fields': (
                'journal_entry', 'posted_to_finance_date', 'posted_to_finance_by'
            )
        }),
        ('Reconciliation', {
            'fields': (
                'is_reconciled', 'reconciled_date', 'reconciled_by'
            )
        }),
        ('Approval Workflow', {
            'fields': (
                'submitted_by', 'submitted_date',
                'approved_by', 'approved_date'
            )
        }),
        ('Supplier Breakdown', {
            'fields': ('get_supplier_breakdown',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit Trail', {
            'fields': (
                'created_by', 'created_at', 'updated_by', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [APPaymentLineInline]
    
    actions = [
        'action_submit', 'action_approve', 'action_post_to_finance',
        'action_reconcile', 'action_reject', 'action_cancel'
    ]
    
    def get_status_colored(self, obj):
        """Color-coded status"""
        colors = {
            'DRAFT': 'gray',
            'SUBMITTED': 'blue',
            'APPROVED': 'green',
            'PROCESSING': 'orange',
            'POSTED_TO_FINANCE': 'purple',
            'RECONCILED': 'teal',
            'REJECTED': 'red',
            'CANCELLED': 'darkgray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    
    def get_finance_status(self, obj):
        """Finance integration status"""
        if obj.journal_entry:
            return format_html(
                '<a href="{}" style="color: green;">✓ Posted (JE-{})</a>',
                reverse('admin:finance_journalentry_change', args=[obj.journal_entry.id]),
                obj.journal_entry.id
            )
        elif obj.status == 'APPROVED':
            return format_html('<span style="color: orange;">Ready to Post</span>')
        else:
            return format_html('<span style="color: gray;">Not Posted</span>')
    get_finance_status.short_description = 'Finance Status'
    
    def get_reconciliation_status(self, obj):
        """Reconciliation status"""
        if obj.is_reconciled:
            return format_html(
                '<span style="color: green;">✓ Reconciled on {}</span>',
                obj.reconciled_date.strftime('%Y-%m-%d') if obj.reconciled_date else 'N/A'
            )
        elif obj.status == 'POSTED_TO_FINANCE':
            return format_html('<span style="color: orange;">Pending Reconciliation</span>')
        else:
            return format_html('<span style="color: gray;">Not Reconciled</span>')
    get_reconciliation_status.short_description = 'Reconciliation'
    
    def get_payment_summary(self, obj):
        """Payment summary"""
        if not obj.pk:
            return "Save batch to see summary"
        
        lines = obj.payment_lines.all()
        total_withholding = sum(line.withholding_tax_amount for line in lines)
        total_discount = sum(line.discount_taken for line in lines)
        total_net = sum(line.net_payment_amount for line in lines)
        
        html = f"""
        <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
            <strong>Payment Summary:</strong><br>
            Total Lines: {lines.count()}<br>
            Gross Payment: {obj.total_amount:,.2f} {obj.currency.code}<br>
            Withholding Tax: {total_withholding:,.2f} {obj.currency.code}<br>
            Discounts: {total_discount:,.2f} {obj.currency.code}<br>
            Net Payment: {total_net:,.2f} {obj.currency.code}
        </div>
        """
        return format_html(html)
    get_payment_summary.short_description = 'Payment Summary'
    
    def get_supplier_breakdown(self, obj):
        """Breakdown by supplier"""
        if not obj.pk:
            return "Save batch to see breakdown"
        
        # Group by supplier
        supplier_totals = {}
        for line in obj.payment_lines.all():
            supplier = line.ap_invoice.supplier
            if supplier not in supplier_totals:
                supplier_totals[supplier] = {
                    'count': 0,
                    'amount': 0
                }
            supplier_totals[supplier]['count'] += 1
            supplier_totals[supplier]['amount'] += line.payment_amount
        
        html = '<div style="padding: 10px; background: #e3f2fd; border-radius: 5px;">'
        html += '<strong>Supplier Breakdown:</strong><br>'
        for supplier, data in supplier_totals.items():
            html += f'{supplier.name}: {data["count"]} payments, {data["amount"]:,.2f} {obj.currency.code}<br>'
        html += '</div>'
        
        return format_html(html)
    get_supplier_breakdown.short_description = 'Supplier Breakdown'
    
    def action_submit(self, request, queryset):
        """Submit batches"""
        count = 0
        for batch in queryset:
            if batch.status == 'DRAFT':
                try:
                    batch.submit(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error submitting {batch.batch_number}: {e}", level='error')
        
        self.message_user(request, f"Submitted {count} payment batches")
    action_submit.short_description = "Submit selected batches"
    
    def action_approve(self, request, queryset):
        """Approve batches"""
        count = 0
        for batch in queryset:
            if batch.status == 'SUBMITTED':
                try:
                    batch.approve(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error approving {batch.batch_number}: {e}", level='error')
        
        self.message_user(request, f"Approved {count} payment batches")
    action_approve.short_description = "Approve selected batches"
    
    def action_post_to_finance(self, request, queryset):
        """Post to Finance"""
        count = 0
        for batch in queryset:
            if batch.status == 'APPROVED':
                try:
                    batch.post_to_finance(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error posting {batch.batch_number}: {e}", level='error')
        
        self.message_user(request, f"Posted {count} payment batches to Finance")
    action_post_to_finance.short_description = "Post to Finance (create journal entries)"
    
    def action_reconcile(self, request, queryset):
        """Reconcile batches"""
        count = 0
        for batch in queryset:
            if batch.status == 'POSTED_TO_FINANCE':
                try:
                    batch.reconcile(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error reconciling {batch.batch_number}: {e}", level='error')
        
        self.message_user(request, f"Reconciled {count} payment batches")
    action_reconcile.short_description = "Mark as reconciled"
    
    def action_reject(self, request, queryset):
        """Reject batches"""
        count = 0
        for batch in queryset:
            try:
                batch.reject(request.user, "Rejected via admin action")
                count += 1
            except Exception as e:
                self.message_user(request, f"Error rejecting {batch.batch_number}: {e}", level='error')
        
        self.message_user(request, f"Rejected {count} payment batches")
    action_reject.short_description = "Reject selected batches"
    
    def action_cancel(self, request, queryset):
        """Cancel batches"""
        count = 0
        for batch in queryset:
            try:
                batch.cancel(request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f"Error cancelling {batch.batch_number}: {e}", level='error')
        
        self.message_user(request, f"Cancelled {count} payment batches")
    action_cancel.short_description = "Cancel selected batches"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(APPaymentLine)
class APPaymentLineAdmin(admin.ModelAdmin):
    list_display = [
        'payment_batch', 'line_number', 'ap_invoice',
        'payment_amount', 'withholding_tax_amount',
        'net_payment_amount', 'is_paid'
    ]
    list_filter = ['is_paid', 'payment_batch__status']
    search_fields = [
        'payment_batch__batch_number', 'ap_invoice__invoice_number',
        'ap_invoice__supplier__name'
    ]
    readonly_fields = ['net_payment_amount', 'is_paid', 'paid_date']


@admin.register(TaxPeriod)
class TaxPeriodAdmin(admin.ModelAdmin):
    list_display = [
        'period_name', 'jurisdiction', 'get_status_colored',
        'output_tax', 'input_tax', 'net_tax_payable',
        'filing_due_date', 'get_filing_status'
    ]
    list_filter = ['jurisdiction', 'status']
    search_fields = ['period_name', 'jurisdiction__country_name']
    readonly_fields = [
        'output_tax', 'input_tax', 'net_tax_payable',
        'filed_date', 'filed_by', 'journal_entry',
        'created_at', 'updated_at',
        'get_tax_breakdown'
    ]
    
    fieldsets = (
        ('Period Information', {
            'fields': (
                'jurisdiction', 'period_start', 'period_end',
                'period_name', 'status'
            )
        }),
        ('Tax Amounts', {
            'fields': (
                'output_tax', 'input_tax', 'net_tax_payable',
                'get_tax_breakdown'
            )
        }),
        ('Filing Details', {
            'fields': (
                'filing_due_date', 'filed_date', 'filed_by'
            )
        }),
        ('Payment', {
            'fields': (
                'payment_date', 'payment_reference', 'journal_entry'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'action_calculate_tax', 'action_close_period',
        'action_file_return', 'action_record_payment'
    ]
    
    def get_status_colored(self, obj):
        """Color-coded status"""
        colors = {
            'OPEN': 'gray',
            'CLOSED': 'blue',
            'FILED': 'green',
            'PAID': 'teal',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    
    def get_filing_status(self, obj):
        """Filing status indicator"""
        if obj.status == 'PAID':
            return format_html('<span style="color: green;">✓ Paid</span>')
        elif obj.status == 'FILED':
            return format_html('<span style="color: blue;">Filed, Awaiting Payment</span>')
        elif obj.status == 'CLOSED':
            return format_html('<span style="color: orange;">Ready to File</span>')
        else:
            return format_html('<span style="color: gray;">Open</span>')
    get_filing_status.short_description = 'Filing Status'
    
    def get_tax_breakdown(self, obj):
        """Tax breakdown display"""
        html = f"""
        <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
            <strong>Tax Breakdown:</strong><br>
            Output Tax (Sales): {obj.output_tax:,.2f}<br>
            Input Tax (Purchases): {obj.input_tax:,.2f}<br>
            <hr style="margin: 5px 0;">
            <strong>Net Tax Payable: {obj.net_tax_payable:,.2f}</strong>
        </div>
        """
        return format_html(html)
    get_tax_breakdown.short_description = 'Tax Breakdown'
    
    def action_calculate_tax(self, request, queryset):
        """Calculate tax amounts"""
        count = 0
        for period in queryset:
            try:
                period.calculate_tax_amounts()
                count += 1
            except Exception as e:
                self.message_user(request, f"Error calculating tax for {period.period_name}: {e}", level='error')
        
        self.message_user(request, f"Calculated tax for {count} periods")
    action_calculate_tax.short_description = "Calculate tax amounts"
    
    def action_close_period(self, request, queryset):
        """Close periods"""
        count = 0
        for period in queryset:
            if period.status == 'OPEN':
                try:
                    period.close_period(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error closing {period.period_name}: {e}", level='error')
        
        self.message_user(request, f"Closed {count} tax periods")
    action_close_period.short_description = "Close periods"
    
    def action_file_return(self, request, queryset):
        """File tax returns"""
        count = 0
        for period in queryset:
            if period.status == 'CLOSED':
                try:
                    period.file_return(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error filing {period.period_name}: {e}", level='error')
        
        self.message_user(request, f"Filed {count} tax returns")
    action_file_return.short_description = "File tax returns"
    
    def action_record_payment(self, request, queryset):
        """Record tax payment"""
        count = 0
        for period in queryset:
            if period.status == 'FILED':
                try:
                    period.record_payment(request.user, f"Payment for {period.period_name}")
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error recording payment for {period.period_name}: {e}", level='error')
        
        self.message_user(request, f"Recorded payment for {count} tax periods")
    action_record_payment.short_description = "Record tax payment"


@admin.register(CorporateTaxAccrual)
class CorporateTaxAccrualAdmin(admin.ModelAdmin):
    list_display = [
        'fiscal_year', 'period_month', 'period_quarter',
        'profit_before_tax', 'tax_rate', 'tax_amount',
        'get_posting_status', 'get_journal_entry_link'
    ]
    list_filter = ['fiscal_year', 'period_quarter', 'is_posted']
    search_fields = ['fiscal_year']
    readonly_fields = [
        'profit_before_tax', 'tax_amount',
        'journal_entry', 'is_posted', 'posted_date', 'posted_by',
        'created_at', 'updated_at',
        'get_tax_calculation'
    ]
    
    fieldsets = (
        ('Period', {
            'fields': (
                'fiscal_year', 'period_month', 'period_quarter'
            )
        }),
        ('Financial Data', {
            'fields': (
                'revenue', 'expenses', 'profit_before_tax'
            )
        }),
        ('Tax Calculation', {
            'fields': (
                'tax_rate', 'tax_amount', 'get_tax_calculation'
            )
        }),
        ('Cumulative', {
            'fields': (
                'cumulative_profit_before_tax', 'cumulative_tax_amount'
            )
        }),
        ('GL Accounts', {
            'fields': (
                'tax_expense_account', 'tax_payable_account'
            )
        }),
        ('Posting Status', {
            'fields': (
                'is_posted', 'posted_date', 'posted_by', 'journal_entry'
            )
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['action_post_accrual']
    
    def get_posting_status(self, obj):
        """Posting status"""
        if obj.is_posted:
            return format_html('<span style="color: green;">✓ Posted</span>')
        else:
            return format_html('<span style="color: orange;">Not Posted</span>')
    get_posting_status.short_description = 'Status'
    
    def get_journal_entry_link(self, obj):
        """Journal entry link"""
        if obj.journal_entry:
            return format_html(
                '<a href="{}">JE-{}</a>',
                reverse('admin:finance_journalentry_change', args=[obj.journal_entry.id]),
                obj.journal_entry.id
            )
        return format_html('<span style="color: gray;">N/A</span>')
    get_journal_entry_link.short_description = 'Journal Entry'
    
    def get_tax_calculation(self, obj):
        """Tax calculation breakdown"""
        html = f"""
        <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
            <strong>Tax Calculation:</strong><br>
            Revenue: {obj.revenue:,.2f}<br>
            Expenses: ({obj.expenses:,.2f})<br>
            <hr style="margin: 5px 0;">
            Profit Before Tax: {obj.profit_before_tax:,.2f}<br>
            Tax Rate: {obj.tax_rate}%<br>
            <hr style="margin: 5px 0;">
            <strong>Tax Amount: {obj.tax_amount:,.2f}</strong>
        </div>
        """
        return format_html(html)
    get_tax_calculation.short_description = 'Tax Calculation'
    
    def action_post_accrual(self, request, queryset):
        """Post accruals to Finance"""
        count = 0
        for accrual in queryset:
            if not accrual.is_posted:
                try:
                    accrual.post_accrual(request.user)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error posting accrual for FY{accrual.fiscal_year}-{accrual.period_month:02d}: {e}", level='error')
        
        self.message_user(request, f"Posted {count} corporate tax accruals to Finance")
    action_post_accrual.short_description = "Post to Finance (create journal entries)"


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    """Admin for Payment Requests"""
    
    list_display = [
        'request_number', 'supplier', 'payment_amount', 'currency',
        'requested_payment_date', 'get_status_colored', 'get_priority_colored',
        'approved_by', 'created_at'
    ]
    list_filter = ['status', 'priority', 'payment_method', 'requested_payment_date', 'created_at']
    search_fields = ['request_number', 'supplier__name', 'purpose', 'payment_reference']
    readonly_fields = [
        'request_number', 'base_currency_amount', 'approved_by', 'approved_date',
        'scheduled_date', 'paid_date', 'created_at', 'updated_at', 'created_by', 'updated_by'
    ]
    
    fieldsets = (
        ('Request Details', {
            'fields': (
                'request_number', 'supplier', 'vendor_bill', 'priority'
            )
        }),
        ('Payment Information', {
            'fields': (
                'payment_method', 'requested_payment_date',
                'currency', 'payment_amount', 'exchange_rate', 'base_currency_amount'
            )
        }),
        ('Status & Workflow', {
            'fields': (
                'status', 'approval_required',
                'approved_by', 'approved_date'
            )
        }),
        ('Payment Execution', {
            'fields': (
                'payment_batch', 'scheduled_date', 'paid_date', 'payment_reference'
            )
        }),
        ('Additional Information', {
            'fields': (
                'purpose', 'notes', 'attachment_url'
            )
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'DRAFT': 'gray',
            'SUBMITTED': 'blue',
            'APPROVED': 'green',
            'REJECTED': 'red',
            'SCHEDULED': 'purple',
            'PAID': 'darkgreen',
            'CANCELLED': 'darkred',
            'CLOSED': 'black',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    
    def get_priority_colored(self, obj):
        """Display priority with color coding"""
        colors = {
            'LOW': 'gray',
            'NORMAL': 'blue',
            'HIGH': 'orange',
            'URGENT': 'red',
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    get_priority_colored.short_description = 'Priority'
    
    actions = ['action_submit', 'action_approve', 'action_cancel']
    
    def action_submit(self, request, queryset):
        """Submit payment requests for approval"""
        count = 0
        for pr in queryset.filter(status='DRAFT'):
            try:
                pr.submit(request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f"Error submitting {pr.request_number}: {e}", level='error')
        
        self.message_user(request, f"Submitted {count} payment requests for approval")
    action_submit.short_description = "Submit for approval"
    
    def action_approve(self, request, queryset):
        """Approve payment requests"""
        count = 0
        for pr in queryset.filter(status='SUBMITTED'):
            try:
                pr.approve(request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f"Error approving {pr.request_number}: {e}", level='error')
        
        self.message_user(request, f"Approved {count} payment requests")
    action_approve.short_description = "Approve payment requests"
    
    def action_cancel(self, request, queryset):
        """Cancel payment requests"""
        count = 0
        for pr in queryset.exclude(status__in=['PAID', 'CLOSED']):
            try:
                pr.cancel(request.user, "Cancelled via admin action")
                count += 1
            except Exception as e:
                self.message_user(request, f"Error cancelling {pr.request_number}: {e}", level='error')
        
        self.message_user(request, f"Cancelled {count} payment requests")
    action_cancel.short_description = "Cancel payment requests"


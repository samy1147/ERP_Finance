# ap/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Supplier, VendorContact, VendorDocument, VendorPerformanceRecord, VendorOnboardingChecklist,
    APInvoice, APItem, APPayment, APPaymentAllocation
)


# ==================== VENDOR/SUPPLIER MANAGEMENT ====================

# Vendor Contact Inline
class VendorContactInline(admin.TabularInline):
    model = VendorContact
    extra = 0
    fields = ('first_name', 'last_name', 'title', 'email', 'phone', 'contact_type', 'is_primary', 'is_active')
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_active:
            return []
        return ['is_active']


# Vendor Document Inline
class VendorDocumentInline(admin.TabularInline):
    model = VendorDocument
    extra = 0
    fields = ('document_type', 'document_name', 'issue_date', 'expiry_date', 'is_verified', 'is_expired_display')
    readonly_fields = ('is_expired_display',)
    
    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">⚠ EXPIRED</span>')
        elif obj.days_until_expiry and obj.days_until_expiry < 30:
            return format_html('<span style="color: orange;">⚠ Expiring in {} days</span>', obj.days_until_expiry)
        return format_html('<span style="color: green;">✓ Valid</span>')
    is_expired_display.short_description = 'Status'


# Vendor Onboarding Checklist Inline
class VendorOnboardingChecklistInline(admin.TabularInline):
    model = VendorOnboardingChecklist
    extra = 0
    fields = ('item_name', 'is_required', 'is_completed', 'completed_date', 'priority')
    ordering = ['priority', 'item_name']


# Supplier/Vendor Admin
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "code", "name", "vendor_category", "country", "currency", 
        "is_preferred_display", "status_display", "performance_score_display",
        "onboarding_status", "is_active"
    )
    list_filter = (
        "vendor_category", "country", "is_active", "is_preferred", 
        "is_blacklisted", "is_on_hold", "onboarding_status", "compliance_verified"
    )
    search_fields = ("code", "name", "legal_name", "email", "vat_number", "tax_id", "trade_license_number")
    autocomplete_fields = ("currency",)
    ordering = ("code",)
    
    inlines = [VendorContactInline, VendorDocumentInline, VendorOnboardingChecklistInline]
    
    fieldsets = (
        ("Basic Information", {
            "fields": (
                ("code", "name"),
                "legal_name",
                ("email", "phone"),
                "website",
                "vendor_category",
            )
        }),
        ("Address", {
            "fields": (
                "address_line1",
                "address_line2",
                ("city", "state", "postal_code"),
                "country",
            )
        }),
        ("Tax & Registration", {
            "fields": (
                ("vat_number", "tax_id"),
                ("trade_license_number", "trade_license_expiry"),
            )
        }),
        ("Financial Details", {
            "fields": (
                ("currency", "payment_terms_days"),
                "credit_limit",
            )
        }),
        ("Bank Details", {
            "fields": (
                "bank_name",
                "bank_account_name",
                "bank_account_number",
                ("bank_iban", "bank_swift"),
                "bank_routing_number",
            ),
            "classes": ("collapse",)
        }),
        ("Status & Classification", {
            "fields": (
                ("is_active", "is_preferred"),
                ("is_blacklisted", "is_on_hold"),
                "blacklist_reason",
                "hold_reason",
            )
        }),
        ("Onboarding & Compliance", {
            "fields": (
                ("onboarding_status", "onboarding_completed_date"),
                ("compliance_verified", "compliance_verified_date"),
            )
        }),
        ("Performance Metrics", {
            "fields": (
                "performance_score",
                ("quality_score", "delivery_score", "price_score"),
            ),
            "classes": ("collapse",)
        }),
        ("Additional Information", {
            "fields": (
                "notes",
                ("created_at", "updated_at"),
                "created_by",
            ),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = ("created_at", "updated_at", "performance_score")
    
    def is_preferred_display(self, obj):
        if obj.is_preferred:
            return format_html('<span style="color: gold;">⭐ Preferred</span>')
        return "-"
    is_preferred_display.short_description = 'Preferred'
    
    def status_display(self, obj):
        statuses = []
        if obj.is_blacklisted:
            statuses.append('<span style="color: red;">⛔ BLACKLISTED</span>')
        if obj.is_on_hold:
            statuses.append('<span style="color: orange;">⏸ ON HOLD</span>')
        if not obj.is_active:
            statuses.append('<span style="color: gray;">Inactive</span>')
        if obj.can_transact() and obj.is_active:
            statuses.append('<span style="color: green;">✓ Active</span>')
        return format_html(' '.join(statuses) if statuses else '-')
    status_display.short_description = 'Status'
    
    def performance_score_display(self, obj):
        if obj.performance_score:
            score = float(obj.performance_score)
            if score >= 80:
                color = 'green'
            elif score >= 60:
                color = 'orange'
            else:
                color = 'red'
            return format_html('<span style="color: {};">{:.1f}</span>', color, score)
        return "-"
    performance_score_display.short_description = 'Performance'
    
    actions = ['mark_as_preferred', 'remove_preferred', 'put_on_hold', 'remove_hold', 'blacklist_vendors']
    
    def mark_as_preferred(self, request, queryset):
        updated = queryset.update(is_preferred=True)
        self.message_user(request, f'{updated} vendor(s) marked as preferred.')
    mark_as_preferred.short_description = "Mark selected as preferred vendors"
    
    def remove_preferred(self, request, queryset):
        updated = queryset.update(is_preferred=False)
        self.message_user(request, f'{updated} vendor(s) removed from preferred status.')
    remove_preferred.short_description = "Remove preferred status"
    
    def put_on_hold(self, request, queryset):
        updated = queryset.update(is_on_hold=True)
        self.message_user(request, f'{updated} vendor(s) put on hold.')
    put_on_hold.short_description = "Put selected vendors on hold"
    
    def remove_hold(self, request, queryset):
        updated = queryset.update(is_on_hold=False, hold_reason='')
        self.message_user(request, f'{updated} vendor(s) removed from hold.')
    remove_hold.short_description = "Remove hold status"
    
    def blacklist_vendors(self, request, queryset):
        updated = queryset.update(is_blacklisted=True, is_active=False)
        self.message_user(request, f'{updated} vendor(s) blacklisted.')
    blacklist_vendors.short_description = "Blacklist selected vendors"


# Vendor Contact Admin
@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'vendor', 'contact_type', 'email', 'phone', 'is_primary', 'is_active')
    list_filter = ('contact_type', 'is_primary', 'is_active', 'receives_invoices', 'receives_payments')
    search_fields = ('first_name', 'last_name', 'email', 'vendor__name', 'vendor__code')
    autocomplete_fields = ('vendor',)
    
    fieldsets = (
        ('Contact Information', {
            'fields': (
                'vendor',
                ('first_name', 'last_name'),
                'title',
                ('email', 'phone', 'mobile'),
            )
        }),
        ('Classification', {
            'fields': (
                ('contact_type', 'is_primary'),
                'is_active',
            )
        }),
        ('Communication Preferences', {
            'fields': (
                'receives_invoices',
                'receives_payments',
                'receives_orders',
            )
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


# Vendor Document Admin
@admin.register(VendorDocument)
class VendorDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'vendor', 'document_type', 'document_name', 'issue_date', 
        'expiry_date', 'is_verified', 'expiry_status_display'
    )
    list_filter = (
        'document_type', 'is_verified', 'is_required_for_onboarding', 
        'is_submitted', 'issue_date', 'expiry_date'
    )
    search_fields = ('vendor__name', 'vendor__code', 'document_name', 'document_number')
    autocomplete_fields = ('vendor', 'verified_by', 'uploaded_by')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Document Details', {
            'fields': (
                'vendor',
                ('document_type', 'document_name'),
                'document_number',
            )
        }),
        ('File', {
            'fields': (
                'file',
                'file_url',
            )
        }),
        ('Validity', {
            'fields': (
                ('issue_date', 'expiry_date'),
                ('is_verified', 'verified_by', 'verified_date'),
            )
        }),
        ('Onboarding', {
            'fields': (
                'is_required_for_onboarding',
                'is_submitted',
            )
        }),
        ('Additional Information', {
            'fields': (
                'notes',
                ('created_at', 'updated_at'),
                'uploaded_by',
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def expiry_status_display(self, obj):
        if not obj.expiry_date:
            return '-'
        if obj.is_expired:
            return format_html('<span style="color: red; font-weight: bold;">⚠ EXPIRED</span>')
        elif obj.days_until_expiry and obj.days_until_expiry < 30:
            return format_html('<span style="color: orange;">⚠ Expires in {} days</span>', obj.days_until_expiry)
        return format_html('<span style="color: green;">✓ Valid ({} days)</span>', obj.days_until_expiry)
    expiry_status_display.short_description = 'Expiry Status'


# Vendor Performance Record Admin
@admin.register(VendorPerformanceRecord)
class VendorPerformanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        'vendor', 'period_start', 'period_end', 
        'overall_score_display', 'delivery_score', 'quality_score', 
        'price_score', 'risk_level_display'
    )
    list_filter = ('risk_level', 'period_start', 'period_end')
    search_fields = ('vendor__name', 'vendor__code')
    autocomplete_fields = ('vendor', 'created_by')
    date_hierarchy = 'period_end'
    
    fieldsets = (
        ('Period', {
            'fields': (
                'vendor',
                ('period_start', 'period_end'),
            )
        }),
        ('Delivery Performance', {
            'fields': (
                ('total_orders', 'on_time_deliveries', 'late_deliveries'),
                'avg_delivery_delay_days',
            )
        }),
        ('Quality Performance', {
            'fields': (
                ('total_items_received', 'rejected_items'),
                'defect_rate',
            )
        }),
        ('Price Performance', {
            'fields': (
                ('price_changes', 'price_increase_count'),
                'avg_price_variance',
            )
        }),
        ('Invoice & Payment', {
            'fields': (
                ('total_invoices', 'disputed_invoices'),
                'invoice_accuracy_rate',
            )
        }),
        ('Calculated Scores', {
            'fields': (
                ('delivery_score', 'quality_score', 'price_score'),
                'overall_score',
            )
        }),
        ('Risk Assessment', {
            'fields': (
                'risk_level',
                'risk_notes',
            )
        }),
        ('Additional Information', {
            'fields': (
                'notes',
                ('created_at', 'updated_at'),
                'created_by',
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'defect_rate', 'invoice_accuracy_rate')
    
    actions = ['recalculate_scores']
    
    def overall_score_display(self, obj):
        if obj.overall_score:
            score = float(obj.overall_score)
            if score >= 80:
                color = 'green'
            elif score >= 60:
                color = 'orange'
            else:
                color = 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{:.1f}</span>', color, score)
        return "-"
    overall_score_display.short_description = 'Overall Score'
    
    def risk_level_display(self, obj):
        if obj.risk_level:
            colors = {
                'LOW': 'green',
                'MEDIUM': 'orange',
                'HIGH': 'red',
                'CRITICAL': 'darkred'
            }
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                colors.get(obj.risk_level, 'black'),
                obj.get_risk_level_display()
            )
        return "-"
    risk_level_display.short_description = 'Risk Level'
    
    def recalculate_scores(self, request, queryset):
        for record in queryset:
            record.calculate_scores()
        self.message_user(request, f'{queryset.count()} performance record(s) recalculated.')
    recalculate_scores.short_description = "Recalculate performance scores"


# Vendor Onboarding Checklist Admin
@admin.register(VendorOnboardingChecklist)
class VendorOnboardingChecklistAdmin(admin.ModelAdmin):
    list_display = (
        'checklist_status', 'vendor', 'item_name', 'is_required', 
        'is_completed', 'completed_date', 'priority'
    )
    list_filter = ('is_completed', 'is_required', 'vendor')
    search_fields = ('vendor__name', 'vendor__code', 'item_name')
    autocomplete_fields = ('vendor', 'completed_by', 'related_document')
    
    fieldsets = (
        ('Checklist Item', {
            'fields': (
                'vendor',
                'item_name',
                'description',
                ('is_required', 'priority'),
            )
        }),
        ('Status', {
            'fields': (
                'is_completed',
                ('completed_date', 'completed_by'),
            )
        }),
        ('Related Information', {
            'fields': (
                'related_document',
                'notes',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def checklist_status(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">○</span>')
    checklist_status.short_description = '✓'


# ==================== ACCOUNTS PAYABLE ====================


# AP Item Inline
class APItemInline(admin.TabularInline):
    model = APItem
    extra = 0
    fields = ("description", "quantity", "unit_price", "tax_rate", "tax_country", "tax_category")
    autocomplete_fields = ("tax_rate",)


# AP Invoice Admin
@admin.register(APInvoice)
class APInvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "supplier", "country", "date", "due_date", "currency", "is_posted", "payment_status", "is_cancelled")
    list_filter = ("is_posted", "payment_status", "is_cancelled", "country", "date", "currency")
    search_fields = ("number", "supplier__name", "supplier__code")
    autocomplete_fields = ("supplier", "currency")
    date_hierarchy = "date"
    ordering = ("-date",)
    inlines = [APItemInline]
    
    readonly_fields = ("posted_at", "paid_at", "cancelled_at", "gl_journal")
    
    fieldsets = (
        ("Invoice Information", {
            "fields": ("number", "supplier", "date", "due_date", "country")
        }),
        ("Financial Details", {
            "fields": ("currency",)
        }),
        ("Status", {
            "fields": ("is_posted", "payment_status", "is_cancelled")
        }),
        ("GL Integration", {
            "fields": ("gl_journal", "posted_at", "paid_at", "cancelled_at"),
            "classes": ("collapse",)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_posted:
            # Posted invoices should be mostly readonly
            return self.readonly_fields + ("number", "supplier", "date", "due_date", "currency")
        return self.readonly_fields


# AP Payment Allocation Inline
class APPaymentAllocationInline(admin.TabularInline):
    model = APPaymentAllocation
    extra = 1
    fields = ("invoice", "amount", "memo")
    autocomplete_fields = ("invoice",)


# AP Payment Admin
@admin.register(APPayment)
class APPaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "supplier", "date", "total_amount", "bank_account", "reconciled", "posted_at")
    list_filter = ("reconciled", "date")
    search_fields = ("reference", "supplier__name", "reconciliation_ref")
    autocomplete_fields = ("supplier", "bank_account", "currency")
    date_hierarchy = "date"
    ordering = ("-date",)
    inlines = [APPaymentAllocationInline]
    
    readonly_fields = ("posted_at", "reconciled_at", "gl_journal")
    
    fieldsets = (
        ("Payment Information", {
            "fields": ("invoice", "date", "amount", "bank_account")
        }),
        ("FX Details", {
            "fields": ("payment_fx_rate",),
            "classes": ("collapse",)
        }),
        ("Reconciliation", {
            "fields": ("reconciled", "reconciliation_ref", "reconciled_at"),
            "classes": ("collapse",)
        }),
        ("GL Integration", {
            "fields": ("gl_journal", "posted_at"),
            "classes": ("collapse",)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.posted_at:
            # Posted payments should be readonly
            return self.readonly_fields + ("invoice", "date", "amount", "bank_account", "payment_fx_rate")
        return self.readonly_fields

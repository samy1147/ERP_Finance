# ar/admin.py
from django.contrib import admin
from .models import Customer, ARInvoice, ARItem, ARPayment, ARPaymentAllocation


# Customer Admin
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "country", "currency", "email", "is_active")
    list_filter = ("country", "is_active")
    search_fields = ("code", "name", "email", "vat_number")
    autocomplete_fields = ("currency",)
    ordering = ("code",)
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("code", "name", "email", "is_active")
        }),
        ("Location & Tax", {
            "fields": ("country", "currency", "vat_number")
        }),
    )


# AR Item Inline
class ARItemInline(admin.TabularInline):
    model = ARItem
    extra = 0
    fields = ("description", "quantity", "unit_price", "tax_rate", "tax_country", "tax_category")
    autocomplete_fields = ("tax_rate",)


# AR Invoice Admin
@admin.register(ARInvoice)
class ARInvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "country", "date", "due_date", "currency", "is_posted", "payment_status", "is_cancelled")
    list_filter = ("is_posted", "payment_status", "is_cancelled", "country", "date", "currency")
    search_fields = ("number", "customer__name", "customer__code")
    autocomplete_fields = ("customer", "currency")
    date_hierarchy = "date"
    ordering = ("-date",)
    inlines = [ARItemInline]
    
    readonly_fields = ("posted_at", "paid_at", "cancelled_at", "gl_journal")
    
    fieldsets = (
        ("Invoice Information", {
            "fields": ("number", "customer", "date", "due_date", "country")
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
            return self.readonly_fields + ("number", "customer", "date", "due_date", "currency")
        return self.readonly_fields


# AR Payment Allocation Inline
class ARPaymentAllocationInline(admin.TabularInline):
    model = ARPaymentAllocation
    extra = 1
    fields = ("invoice", "amount", "memo")
    autocomplete_fields = ("invoice",)


# AR Payment Admin
@admin.register(ARPayment)
class ARPaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer", "date", "total_amount", "bank_account", "reconciled", "posted_at")
    list_filter = ("reconciled", "date")
    search_fields = ("reference", "customer__name", "reconciliation_ref")
    autocomplete_fields = ("customer", "bank_account", "currency")
    date_hierarchy = "date"
    ordering = ("-date",)
    inlines = [ARPaymentAllocationInline]
    
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

# ap/admin.py
from django.contrib import admin
from .models import Supplier, APInvoice, APItem, APPayment, APPaymentAllocation


# Supplier Admin
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
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

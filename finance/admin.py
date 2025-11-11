# apps/finance/admin.py
from django.contrib import admin
from .models import (Invoice, InvoiceLine, InvoiceStatus, BankAccount,
                     InvoiceApproval, JournalLineSegment)

class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0

class InvoiceAdmin(admin.ModelAdmin):
    # inlines = [InvoiceLineInline]  # Temporarily disabled due to admin check issue with lazy ForeignKey
    list_display = ("invoice_no", "customer", "status", "currency", "total_gross", "posted_at")
    readonly_fields_when_posted = (
        "invoice_no", "customer", "currency", "total_net", "total_tax", "total_gross", "posted_at"
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == InvoiceStatus.POSTED:
            return self.readonly_fields_when_posted
        return super().get_readonly_fields(request, obj)

    def has_change_permission(self, request, obj=None):
        # Allow viewing but block editing when posted
        if obj and obj.status == InvoiceStatus.POSTED and request.method in ("POST", "PUT", "PATCH"):
            return False
        return super().has_change_permission(request, obj)

admin.site.register(Invoice, InvoiceAdmin)


# Note: Account Admin moved to segment/admin.py
# Note: Customer admin moved to ar/admin.py
# Note: Supplier admin moved to ap/admin.py


# BankAccount Admin

# BankAccount Admin
@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "account_code", "iban", "swift", "currency", "active")
    list_filter = ("currency", "active")
    search_fields = ("name", "account_code", "iban", "swift")
    autocomplete_fields = ("currency",)


# Invoice Approval Admin
@admin.register(InvoiceApproval)
class InvoiceApprovalAdmin(admin.ModelAdmin):
    list_display = ("invoice_type", "invoice_id", "status", "submitted_by", "submitted_at", "approver", "approved_at")
    list_filter = ("status", "invoice_type", "approval_level")
    search_fields = ("submitted_by", "approver", "comments")
    date_hierarchy = "submitted_at"
    ordering = ("-submitted_at",)
    
    readonly_fields = ("submitted_at", "approved_at", "rejected_at")
    
    fieldsets = (
        ("Invoice Information", {
            "fields": ("invoice_type", "invoice_id", "status", "approval_level")
        }),
        ("Submission", {
            "fields": ("submitted_by", "submitted_at")
        }),
        ("Approval/Rejection", {
            "fields": ("approver", "approved_at", "rejected_at", "comments")
        }),
    )


@admin.register(JournalLineSegment)
class JournalLineSegmentAdmin(admin.ModelAdmin):
    list_display = ("id", "journal_line", "segment_type", "segment", "segment_code", "segment_alias")
    list_filter = ("segment_type",)
    search_fields = ("segment__code", "segment__alias")
    readonly_fields = ("journal_line", "segment_type", "segment")
    
    def segment_code(self, obj):
        return obj.segment.code if obj.segment else "-"
    segment_code.short_description = "Segment Code"
    
    def segment_alias(self, obj):
        return obj.segment.alias if obj.segment else "-"
    segment_alias.short_description = "Segment Name"


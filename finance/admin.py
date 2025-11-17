# apps/finance/admin.py
from django.contrib import admin
from .models import (BankAccount, InvoiceApproval, JournalLineSegment, SegmentAssignmentRule)

# Note: Legacy Invoice and InvoiceLine models have been removed
# Use ar.ARInvoice for customer invoices
# Use ap.APInvoice for supplier invoices

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


# Segment Assignment Rule Admin
@admin.register(SegmentAssignmentRule)
class SegmentAssignmentRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "priority", "is_active", "customer", "supplier", "account_segment_code", "department_segment_code")
    list_filter = ("is_active", "priority")
    search_fields = ("name", "customer__name", "supplier__name", "account_segment__code")
    autocomplete_fields = ("customer", "supplier", "account_segment", "department_segment", 
                          "cost_center_segment", "project_segment", "product_segment")
    
    fieldsets = (
        ("Rule Information", {
            "fields": ("name", "priority", "is_active", "notes")
        }),
        ("Conditions", {
            "fields": ("customer", "supplier", "account_segment")
        }),
        ("Segment Assignments", {
            "fields": ("department_segment", "cost_center_segment", "project_segment", "product_segment")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = ("created_at", "updated_at")
    
    def account_segment_code(self, obj):
        return obj.account_segment.code if obj.account_segment else "-"
    account_segment_code.short_description = "Account Code"
    
    def department_segment_code(self, obj):
        return obj.department_segment.code if obj.department_segment else "-"
    department_segment_code.short_description = "Department Code"


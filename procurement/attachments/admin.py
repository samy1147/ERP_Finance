"""
Admin configuration for attachments.
"""

from django.contrib import admin
from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """Admin interface for Attachment model."""
    
    list_display = [
        'id',
        'get_document_reference',
        'document_type',
        'original_filename',
        'file_size_display',
        'uploaded_by',
        'uploaded_at',
    ]
    list_filter = [
        'document_type',
        'uploaded_at',
    ]
    search_fields = [
        'original_filename',
        'description',
        'po_header__po_number',
        'pr_header__pr_number',
    ]
    readonly_fields = [
        'file_size',
        'original_filename',
        'uploaded_by',
        'uploaded_at',
        'file_size_display',
    ]
    
    fieldsets = (
        ('Document Reference', {
            'fields': ('po_header', 'pr_header')
        }),
        ('File Information', {
            'fields': (
                'file',
                'document_type',
                'description',
                'original_filename',
                'file_size',
                'file_size_display',
            )
        }),
        ('Audit Information', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_document_reference(self, obj):
        """Get document reference string."""
        if obj.po_header:
            return f"PO: {obj.po_header.po_number}"
        elif obj.pr_header:
            return f"PR: {obj.pr_header.pr_number}"
        return "-"
    get_document_reference.short_description = "Document"
    
    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        return obj.get_file_size_display()
    file_size_display.short_description = "File Size"

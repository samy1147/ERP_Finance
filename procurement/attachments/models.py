"""
Attachment models for procurement documents (PO, PR, etc.).
"""

import os
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone


def po_attachment_path(instance, filename):
    """Generate file path for PO attachments."""
    return f'procurement/po/{instance.po_header.po_number}/{filename}'


def pr_attachment_path(instance, filename):
    """Generate file path for PR attachments."""
    return f'procurement/pr/{instance.pr_header.pr_number}/{filename}'


class Attachment(models.Model):
    """
    File attachments for procurement documents.
    Supports PO, PR, and can be extended for other document types.
    """
    
    DOCUMENT_TYPE_CHOICES = [
        ('PO', 'Purchase Order'),
        ('PR', 'Purchase Requisition'),
        ('QUOTE', 'Vendor Quote'),
        ('CONTRACT', 'Contract'),
        ('SPEC', 'Specification'),
        ('OTHER', 'Other'),
    ]
    
    # Document references (only one should be filled, or use temp_session)
    po_header = models.ForeignKey(
        'purchase_orders.POHeader',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='attachments',
        help_text="Related Purchase Order"
    )
    pr_header = models.ForeignKey(
        'requisitions.PRHeader',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='attachments',
        help_text="Related Purchase Requisition"
    )
    
    # Temporary session for attachments uploaded before document creation
    temp_session = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="Temporary session ID for files uploaded during document creation"
    )
    is_temporary = models.BooleanField(
        default=False,
        help_text="True if file is temporarily stored and not yet linked to a document"
    )
    
    # File information
    file = models.FileField(
        upload_to='procurement/attachments/%Y/%m/',
        max_length=500,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'pdf', 'doc', 'docx', 'xls', 'xlsx', 
                    'txt', 'csv', 'jpg', 'jpeg', 'png', 
                    'gif', 'zip', 'rar'
                ]
            )
        ],
        help_text="Allowed file types: PDF, Word, Excel, Images, Text, ZIP"
    )
    
    # Metadata
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default='OTHER',
        help_text="Type/category of the document"
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Brief description of the attachment"
    )
    file_size = models.PositiveIntegerField(
        default=0,
        help_text="File size in bytes"
    )
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original filename when uploaded"
    )
    
    # Audit fields
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments'
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'procurement_attachment'
        ordering = ['-uploaded_at']
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'
        indexes = [
            models.Index(fields=['po_header', '-uploaded_at']),
            models.Index(fields=['pr_header', '-uploaded_at']),
            models.Index(fields=['temp_session', 'is_temporary']),
        ]
    
    def __str__(self):
        if self.is_temporary:
            return f"Temp - {self.original_filename or self.file.name}"
        doc_ref = ""
        if self.po_header:
            doc_ref = f"PO {self.po_header.po_number}"
        elif self.pr_header:
            doc_ref = f"PR {self.pr_header.pr_number}"
        return f"{doc_ref} - {self.original_filename or self.file.name}"
    
    def save(self, *args, **kwargs):
        """Override save to store file metadata."""
        if self.file:
            # Store original filename if not already set
            if not self.original_filename:
                self.original_filename = os.path.basename(self.file.name)
            
            # Store file size
            if hasattr(self.file, 'size'):
                self.file_size = self.file.size
        
        super().save(*args, **kwargs)
    
    def get_file_extension(self):
        """Get file extension."""
        if self.original_filename:
            return os.path.splitext(self.original_filename)[1].lower()
        return ''
    
    def get_file_size_display(self):
        """Get human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @property
    def file_url(self):
        """Get file URL if file exists."""
        if self.file:
            return self.file.url
        return None

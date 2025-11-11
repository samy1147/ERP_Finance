"""
App configuration for attachments.
"""

from django.apps import AppConfig


class AttachmentsConfig(AppConfig):
    """Configuration for the attachments app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'procurement.attachments'
    label = 'procurement_attachments'
    verbose_name = 'Procurement Attachments'

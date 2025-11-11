"""
Signals for Period Management
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import FiscalPeriod


# Future signals can be added here for:
# - Sending notifications when periods are closed
# - Preventing deletion of periods with transactions
# - Auto-closing previous period when new period is opened
# - etc.

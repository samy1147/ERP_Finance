# finance/signals.py
"""
Django signals for finance module.
Handles automatic updates for payment allocations and invoice statuses.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender='ar.ARPaymentAllocation')
def update_ar_invoice_payment_status_on_allocation(sender, instance, created, **kwargs):
    """
    Automatically update AR invoice payment status when a payment allocation is created or updated.
    Sets status to: PAID, PARTIALLY_PAID, or UNPAID based on outstanding amount.
    """
    invoice = instance.invoice
    update_ar_invoice_payment_status(invoice)


@receiver(post_delete, sender='ar.ARPaymentAllocation')
def update_ar_invoice_payment_status_on_delete(sender, instance, **kwargs):
    """
    Automatically update AR invoice payment status when a payment allocation is deleted.
    """
    invoice = instance.invoice
    update_ar_invoice_payment_status(invoice)


def update_ar_invoice_payment_status(invoice):
    """
    Update the payment status of an AR invoice based on its outstanding amount.
    
    Logic:
    - outstanding = 0 → PAID
    - outstanding > 0 and paid > 0 → PARTIALLY_PAID
    - outstanding = total (no payments) → UNPAID
    """
    from decimal import Decimal
    from django.utils import timezone
    
    total = invoice.calculate_total()
    paid = invoice.paid_amount()
    outstanding = invoice.outstanding_amount()
    
    # Determine payment status
    if outstanding <= Decimal('0.00'):
        # Fully paid
        invoice.payment_status = 'PAID'
        if not invoice.paid_at:
            invoice.paid_at = timezone.now()
    elif paid > Decimal('0.00'):
        # Partially paid
        invoice.payment_status = 'PARTIALLY_PAID'
        invoice.paid_at = None  # Clear paid_at for partial payments
    else:
        # Unpaid
        invoice.payment_status = 'UNPAID'
        invoice.paid_at = None
    
    invoice.save()


# ============================================================================
# AP PAYMENT ALLOCATION SIGNALS - Auto-update invoice payment status
# ============================================================================

@receiver(post_save, sender='ap.APPaymentAllocation')
def update_ap_invoice_payment_status_on_allocation(sender, instance, created, **kwargs):
    """
    Automatically update AP invoice payment status when a payment allocation is created or updated.
    """
    invoice = instance.invoice
    update_ap_invoice_payment_status(invoice)


@receiver(post_delete, sender='ap.APPaymentAllocation')
def update_ap_invoice_payment_status_on_delete(sender, instance, **kwargs):
    """
    Automatically update AP invoice payment status when a payment allocation is deleted.
    """
    invoice = instance.invoice
    update_ap_invoice_payment_status(invoice)


def update_ap_invoice_payment_status(invoice):
    """
    Update the payment status of an AP invoice based on its outstanding amount.
    """
    from decimal import Decimal
    from django.utils import timezone
    
    total = invoice.calculate_total()
    paid = invoice.paid_amount()
    outstanding = invoice.outstanding_amount()
    
    # Determine payment status
    if outstanding <= Decimal('0.00'):
        # Fully paid
        invoice.payment_status = 'PAID'
        if not invoice.paid_at:
            invoice.paid_at = timezone.now()
    elif paid > Decimal('0.00'):
        # Partially paid
        invoice.payment_status = 'PARTIALLY_PAID'
        invoice.paid_at = None
    else:
        # Unpaid
        invoice.payment_status = 'UNPAID'
        invoice.paid_at = None
    
    invoice.save()

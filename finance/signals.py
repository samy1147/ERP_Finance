# finance/signals.py
"""
Django signals that replicate PostgreSQL trigger behavior for invoice validation.
These work on SQLite, PostgreSQL, and any other database backend.

Implements the same logic as the PostgreSQL triggers:
1. Block posting if invoice has no lines
2. Block posting if any line is missing account or tax
3. Block posting if totals are zero
4. Normalize header totals to match line sums at posting time
5. Make posted invoices read-only (except status, reversal_ref, timestamps)
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from decimal import Decimal


@receiver(pre_save, sender='finance.Invoice')
def validate_invoice_posting(sender, instance, **kwargs):
    """
    Signal handler that validates invoices before posting.
    Replicates: finance_validate_invoice_posting() PostgreSQL trigger
    """
    # Only enforce when transitioning to POSTED status
    if instance.pk:  # Existing invoice (UPDATE operation)
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return  # New invoice, no validation needed yet
        
        # Check if we're transitioning TO posted status FROM non-posted status
        if instance.status == 'POSTED' and old_instance.status != 'POSTED':
            
            # 1. Check for lines
            lines_count = instance.lines.count()
            if lines_count == 0:
                raise ValidationError(
                    f'Cannot post invoice {instance.invoice_no}: it has no lines.',
                    code='check_violation'
                )
            
            # 2. Check for missing account or tax on any line
            missing_acct_tax = instance.lines.filter(
                account__isnull=True
            ).exists() or instance.lines.filter(
                tax_code__isnull=True
            ).exists()
            
            if missing_acct_tax:
                raise ValidationError(
                    f'Cannot post invoice {instance.invoice_no}: one or more lines missing account or tax.',
                    code='check_violation'
                )
            
            # 3. Calculate totals from lines
            from django.db.models import Sum
            line_totals = instance.lines.aggregate(
                total_net=Sum('amount_net'),
                total_tax=Sum('tax_amount'),
                total_gross=Sum('amount_gross')
            )
            
            net = line_totals['total_net'] or Decimal('0')
            tax = line_totals['total_tax'] or Decimal('0')
            gross = line_totals['total_gross'] or Decimal('0')
            
            # 4. Check for zero totals
            if gross == 0:
                raise ValidationError(
                    f'Cannot post invoice {instance.invoice_no}: totals are zero.',
                    code='check_violation'
                )
            
            # 5. Normalize header totals to line sums (prevent drift)
            instance.total_net = net
            instance.total_tax = tax
            instance.total_gross = gross


@receiver(pre_save, sender='finance.Invoice')
def block_edit_posted_invoice(sender, instance, **kwargs):
    """
    Signal handler that blocks editing posted invoices.
    Replicates: finance_block_edit_posted() PostgreSQL trigger
    """
    if instance.pk:  # Only for UPDATE operations
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return  # New invoice, no restriction
        
        # Only enforce if OLD status is POSTED
        if old_instance.status == 'POSTED':
            
            # Whitelisted fields that CAN change even after POSTED:
            # - status (to REVERSED)
            # - reversal_ref_id (when reversing)
            # - updated_at (automatic timestamp)
            # - posted_at (timestamp field)
            
            # Allow status change from POSTED to REVERSED
            if instance.status != old_instance.status:
                # Status change is allowed (POSTED -> REVERSED)
                return
            
            # Check for changes to protected fields
            protected_changes = []
            
            if instance.invoice_no != old_instance.invoice_no:
                protected_changes.append('invoice_no')
            
            if instance.customer_id != old_instance.customer_id:
                protected_changes.append('customer')
            
            if instance.currency != old_instance.currency:
                protected_changes.append('currency')
            
            if instance.total_net != old_instance.total_net:
                protected_changes.append('total_net')
            
            if instance.total_tax != old_instance.total_tax:
                protected_changes.append('total_tax')
            
            if instance.total_gross != old_instance.total_gross:
                protected_changes.append('total_gross')
            
            if protected_changes:
                fields_str = ', '.join(protected_changes)
                raise ValidationError(
                    f'Posted documents are read-only. Cannot modify: {fields_str}. Use reversal API.',
                    code='insufficient_privilege'
                )


@receiver(pre_save, sender='finance.InvoiceLine')
def block_edit_posted_invoice_lines(sender, instance, **kwargs):
    """
    Signal handler that blocks editing lines of posted invoices.
    Extends the read-only protection to invoice lines.
    """
    if instance.invoice_id:
        from finance.models import Invoice
        try:
            invoice = Invoice.objects.get(pk=instance.invoice_id)
            if invoice.status == 'POSTED':
                # Check if this is an UPDATE to an existing line
                if instance.pk:
                    try:
                        old_line = sender.objects.get(pk=instance.pk)
                        # If any field changed, block it
                        if (instance.account_id != old_line.account_id or
                            instance.tax_code_id != old_line.tax_code_id or
                            instance.amount_net != old_line.amount_net or
                            instance.tax_amount != old_line.tax_amount or
                            instance.amount_gross != old_line.amount_gross or
                            instance.description != old_line.description):
                            raise ValidationError(
                                f'Cannot modify lines of posted invoice {invoice.invoice_no}. Use reversal API.',
                                code='insufficient_privilege'
                            )
                    except sender.DoesNotExist:
                        pass  # New line
                else:
                    # New line being added to posted invoice
                    raise ValidationError(
                        f'Cannot add lines to posted invoice {invoice.invoice_no}. Use reversal API.',
                        code='insufficient_privilege'
                    )
        except Invoice.DoesNotExist:
            pass  # Invoice not found, let it proceed


# ============================================================================
# AR PAYMENT ALLOCATION SIGNALS - Auto-update invoice payment status
# ============================================================================

from django.db.models.signals import post_save, post_delete

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

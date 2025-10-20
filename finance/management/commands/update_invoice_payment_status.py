"""
Management command to update payment status for all AR and AP invoices
based on their current payment allocations.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from ar.models import ARInvoice
from ap.models import APInvoice


class Command(BaseCommand):
    help = 'Update payment status for all invoices based on current allocations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ar-only',
            action='store_true',
            help='Update only AR invoices',
        )
        parser.add_argument(
            '--ap-only',
            action='store_true',
            help='Update only AP invoices',
        )

    def handle(self, *args, **options):
        ar_only = options.get('ar_only', False)
        ap_only = options.get('ap_only', False)
        
        # If neither specified, update both
        update_ar = not ap_only
        update_ap = not ar_only
        
        ar_updated = 0
        ap_updated = 0
        
        # Update AR Invoices
        if update_ar:
            self.stdout.write(self.style.NOTICE('\n=== Updating AR Invoices ==='))
            ar_updated = self.update_ar_invoices()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated {ar_updated} AR invoice(s)'))
        
        # Update AP Invoices
        if update_ap:
            self.stdout.write(self.style.NOTICE('\n=== Updating AP Invoices ==='))
            ap_updated = self.update_ap_invoices()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated {ap_updated} AP invoice(s)'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Total invoices updated: {ar_updated + ap_updated}'))

    def update_ar_invoices(self):
        """Update payment status for all AR invoices"""
        updated_count = 0
        
        invoices = ARInvoice.objects.all().prefetch_related('items', 'payment_allocations')
        
        for invoice in invoices:
            old_status = invoice.payment_status
            
            total = invoice.calculate_total()
            paid = invoice.paid_amount()
            outstanding = invoice.outstanding_amount()
            
            # Determine new status
            if outstanding <= Decimal('0.00'):
                new_status = 'PAID'
                if not invoice.paid_at:
                    invoice.paid_at = timezone.now()
            elif paid > Decimal('0.00'):
                new_status = 'PARTIALLY_PAID'
                invoice.paid_at = None
            else:
                new_status = 'UNPAID'
                invoice.paid_at = None
            
            # Only update if status changed
            if old_status != new_status or (new_status == 'PAID' and not invoice.paid_at):
                invoice.payment_status = new_status
                invoice.save()
                updated_count += 1
                
                self.stdout.write(
                    f'  Invoice #{invoice.number}: '
                    f'{old_status} → {new_status} '
                    f'(Total: ${total}, Paid: ${paid}, Outstanding: ${outstanding})'
                )
        
        return updated_count

    def update_ap_invoices(self):
        """Update payment status for all AP invoices"""
        updated_count = 0
        
        invoices = APInvoice.objects.all().prefetch_related('items', 'payment_allocations')
        
        for invoice in invoices:
            old_status = invoice.payment_status
            
            total = invoice.calculate_total()
            paid = invoice.paid_amount()
            outstanding = invoice.outstanding_amount()
            
            # Determine new status
            if outstanding <= Decimal('0.00'):
                new_status = 'PAID'
                if not invoice.paid_at:
                    invoice.paid_at = timezone.now()
            elif paid > Decimal('0.00'):
                new_status = 'PARTIALLY_PAID'
                invoice.paid_at = None
            else:
                new_status = 'UNPAID'
                invoice.paid_at = None
            
            # Only update if status changed
            if old_status != new_status or (new_status == 'PAID' and not invoice.paid_at):
                invoice.payment_status = new_status
                invoice.save()
                updated_count += 1
                
                self.stdout.write(
                    f'  Invoice #{invoice.number}: '
                    f'{old_status} → {new_status} '
                    f'(Total: ${total}, Paid: ${paid}, Outstanding: ${outstanding})'
                )
        
        return updated_count

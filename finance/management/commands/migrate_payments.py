"""
Data migration script for Payment Allocations feature
Run this AFTER applying the model migrations
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from ar.models import ARPayment, ARPaymentAllocation
from ap.models import APPayment, APPaymentAllocation


class Command(BaseCommand):
    help = 'Migrate existing AR/AP payments to new allocation model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
        
        # Migrate AR payments
        self.stdout.write('\n' + '='*80)
        self.stdout.write('MIGRATING AR PAYMENTS')
        self.stdout.write('='*80 + '\n')
        
        ar_payments = ARPayment.objects.filter(
            invoice__isnull=False
        )
        
        self.stdout.write(f'Found {ar_payments.count()} AR payments to migrate')
        
        ar_migrated = 0
        ar_skipped = 0
        ar_errors = 0
        
        for payment in ar_payments:
            try:
                # Check if already migrated
                if payment.customer_id and payment.reference and payment.total_amount:
                    self.stdout.write(f'  ✓ Payment #{payment.id} already migrated')
                    ar_skipped += 1
                    continue
                
                # Migrate
                if not dry_run:
                    with transaction.atomic():
                        payment.customer = payment.invoice.customer
                        payment.reference = payment.reference or f"PMT-AR-{payment.id}"
                        payment.total_amount = payment.amount or 0
                        payment.currency = payment.invoice.currency
                        payment.save()
                        
                        # Create allocation if amount > 0
                        if payment.amount and payment.amount > 0:
                            ARPaymentAllocation.objects.get_or_create(
                                payment=payment,
                                invoice=payment.invoice,
                                defaults={'amount': payment.amount}
                            )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Migrated Payment #{payment.id}: {payment.invoice.customer.name} '
                        f'- ${payment.amount} to Invoice {payment.invoice.number}'
                    )
                )
                ar_migrated += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error migrating Payment #{payment.id}: {str(e)}')
                )
                ar_errors += 1
        
        # Migrate AP payments
        self.stdout.write('\n' + '='*80)
        self.stdout.write('MIGRATING AP PAYMENTS')
        self.stdout.write('='*80 + '\n')
        
        ap_payments = APPayment.objects.filter(
            invoice__isnull=False
        )
        
        self.stdout.write(f'Found {ap_payments.count()} AP payments to migrate')
        
        ap_migrated = 0
        ap_skipped = 0
        ap_errors = 0
        
        for payment in ap_payments:
            try:
                # Check if already migrated
                if payment.supplier_id and payment.reference and payment.total_amount:
                    self.stdout.write(f'  ✓ Payment #{payment.id} already migrated')
                    ap_skipped += 1
                    continue
                
                # Migrate
                if not dry_run:
                    with transaction.atomic():
                        payment.supplier = payment.invoice.supplier
                        payment.reference = payment.reference or f"PMT-AP-{payment.id}"
                        payment.total_amount = payment.amount or 0
                        payment.currency = payment.invoice.currency
                        payment.save()
                        
                        # Create allocation if amount > 0
                        if payment.amount and payment.amount > 0:
                            APPaymentAllocation.objects.get_or_create(
                                payment=payment,
                                invoice=payment.invoice,
                                defaults={'amount': payment.amount}
                            )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Migrated Payment #{payment.id}: {payment.invoice.supplier.name} '
                        f'- ${payment.amount} to Invoice {payment.invoice.number}'
                    )
                )
                ap_migrated += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error migrating Payment #{payment.id}: {str(e)}')
                )
                ap_errors += 1
        
        # Summary
        self.stdout.write('\n' + '='*80)
        self.stdout.write('MIGRATION SUMMARY')
        self.stdout.write('='*80)
        self.stdout.write(f'\nAR Payments:')
        self.stdout.write(f'  Migrated: {ar_migrated}')
        self.stdout.write(f'  Skipped:  {ar_skipped}')
        self.stdout.write(f'  Errors:   {ar_errors}')
        self.stdout.write(f'\nAP Payments:')
        self.stdout.write(f'  Migrated: {ap_migrated}')
        self.stdout.write(f'  Skipped:  {ap_skipped}')
        self.stdout.write(f'  Errors:   {ap_errors}')
        self.stdout.write(f'\nTotal Migrated: {ar_migrated + ap_migrated}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n⚠️  DRY RUN - No changes were saved. Run without --dry-run to apply changes.')
            )
        else:
            if ar_errors == 0 and ap_errors == 0:
                self.stdout.write(
                    self.style.SUCCESS('\n✅ Migration completed successfully!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'\n⚠️  Migration completed with {ar_errors + ap_errors} errors')
                )

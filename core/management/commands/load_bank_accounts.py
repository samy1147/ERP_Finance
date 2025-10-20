"""
Management command to load sample bank accounts
Usage: python manage.py load_bank_accounts
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from finance.models import BankAccount
from core.models import Currency
from decimal import Decimal


class Command(BaseCommand):
    help = 'Load 5 sample bank accounts with different currencies'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n🏦 Loading bank accounts...\n'))

        with transaction.atomic():
            # Get currencies
            try:
                aed = Currency.objects.get(code='AED')
                usd = Currency.objects.get(code='USD')
                eur = Currency.objects.get(code='EUR')
                sar = Currency.objects.get(code='SAR')
                inr = Currency.objects.get(code='INR')
            except Currency.DoesNotExist as e:
                self.stdout.write(
                    self.style.ERROR(
                        'Required currencies not found! Please run load_initial_data first.'
                    )
                )
                return

            # Bank accounts data
            bank_accounts_data = [
                {
                    'name': 'Emirates NBD - AED Current Account',
                    'account_code': 'BANK-AED-001',
                    'iban': 'AE070260001234567890123',
                    'swift': 'EBILAEAD',
                    'currency': aed,
                    'active': True,
                },
                {
                    'name': 'ADCB - USD Business Account',
                    'account_code': 'BANK-USD-001',
                    'iban': 'AE330030000123456789',
                    'swift': 'ADCBAEAA',
                    'currency': usd,
                    'active': True,
                },
                {
                    'name': 'Mashreq Bank - EUR Trade Account',
                    'account_code': 'BANK-EUR-001',
                    'iban': 'AE140330000987654321',
                    'swift': 'BOMLAEAD',
                    'currency': eur,
                    'active': True,
                },
                {
                    'name': 'SABB - SAR Business Account',
                    'account_code': 'BANK-SAR-001',
                    'iban': 'SA0380000000608010167519',
                    'swift': 'SABBSARI',
                    'currency': sar,
                    'active': True,
                },
                {
                    'name': 'ICICI Bank - INR Corporate Account',
                    'account_code': 'BANK-INR-001',
                    'iban': 'IN012345678901234567890',
                    'swift': 'ICICINBB',
                    'currency': inr,
                    'active': True,
                },
            ]

            created_accounts = 0
            for account_data in bank_accounts_data:
                account, created = BankAccount.objects.get_or_create(
                    account_code=account_data['account_code'],
                    defaults=account_data
                )
                
                if created:
                    created_accounts += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created: {account.name} ({account.currency.code})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  - Account already exists: {account.account_code}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully loaded bank accounts!\n'
                f'   Accounts created: {created_accounts}\n'
            )
        )
        
        # Display summary
        self.stdout.write(self.style.WARNING('\n💰 Bank Accounts Summary:\n'))
        
        for account in BankAccount.objects.all().order_by('currency__code'):
            self.stdout.write(
                f'   {account.name} - {account.currency.code} (IBAN: {account.iban})'
            )

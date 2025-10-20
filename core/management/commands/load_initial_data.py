"""
Management command to load initial currencies and tax rates
Usage: python manage.py load_initial_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Currency, TaxRate
from decimal import Decimal


class Command(BaseCommand):
    help = 'Load initial currencies and tax rates for USA, Europe, Egypt, India, UAE, and KSA'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n💰 Loading currencies and tax rates...\n'))

        with transaction.atomic():
            # Create Currencies
            currencies_data = [
                {
                    'code': 'USD',
                    'name': 'US Dollar',
                    'symbol': '$',
                    'is_base': False
                },
                {
                    'code': 'EUR',
                    'name': 'Euro',
                    'symbol': '€',
                    'is_base': False
                },
                {
                    'code': 'EGP',
                    'name': 'Egyptian Pound',
                    'symbol': 'E£',
                    'is_base': False
                },
                {
                    'code': 'INR',
                    'name': 'Indian Rupee',
                    'symbol': '₹',
                    'is_base': False
                },
                {
                    'code': 'AED',
                    'name': 'UAE Dirham',
                    'symbol': 'د.إ',
                    'is_base': True  # Set AED as base currency
                },
                {
                    'code': 'SAR',
                    'name': 'Saudi Riyal',
                    'symbol': '﷼',
                    'is_base': False
                },
            ]

            created_currencies = 0
            for currency_data in currencies_data:
                currency, created = Currency.objects.get_or_create(
                    code=currency_data['code'],
                    defaults=currency_data
                )
                if created:
                    created_currencies += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created currency: {currency.code} - {currency.name} ({currency.symbol})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  - Currency already exists: {currency.code}')
                    )

            # Create Tax Rates
            # Note: Only AE, SA, EG, IN supported in TaxRate model
            tax_rates_data = [
                # Egypt - VAT (14%)
                {
                    'country': 'EG',
                    'category': 'STANDARD',
                    'name': 'Egypt Standard VAT',
                    'code': 'VAT14',
                    'rate': Decimal('14.000'),
                    'is_active': True
                },
                {
                    'country': 'EG',
                    'category': 'ZERO',
                    'name': 'Egypt Zero-Rated VAT',
                    'code': 'VAT0',
                    'rate': Decimal('0.000'),
                    'is_active': True
                },
                {
                    'country': 'EG',
                    'category': 'EXEMPT',
                    'name': 'Egypt Exempt',
                    'code': 'EXEMPT',
                    'rate': Decimal('0.000'),
                    'is_active': True
                },
                
                # India - GST (Multiple rates)
                {
                    'country': 'IN',
                    'category': 'STANDARD',
                    'name': 'India GST 28%',
                    'code': 'GST28',
                    'rate': Decimal('28.000'),
                    'is_active': True
                },
                {
                    'country': 'IN',
                    'category': 'STANDARD',
                    'name': 'India GST 18%',
                    'code': 'GST18',
                    'rate': Decimal('18.000'),
                    'is_active': True
                },
                {
                    'country': 'IN',
                    'category': 'STANDARD',
                    'name': 'India GST 12%',
                    'code': 'GST12',
                    'rate': Decimal('12.000'),
                    'is_active': True
                },
                {
                    'country': 'IN',
                    'category': 'STANDARD',
                    'name': 'India GST 5%',
                    'code': 'GST5',
                    'rate': Decimal('5.000'),
                    'is_active': True
                },
                {
                    'country': 'IN',
                    'category': 'ZERO',
                    'name': 'India GST 0%',
                    'code': 'GST0',
                    'rate': Decimal('0.000'),
                    'is_active': True
                },
                {
                    'country': 'IN',
                    'category': 'EXEMPT',
                    'name': 'India GST Exempt',
                    'code': 'EXEMPT',
                    'rate': Decimal('0.000'),
                    'is_active': True
                },
                
                # UAE - VAT (5%)
                {
                    'country': 'AE',
                    'category': 'STANDARD',
                    'name': 'UAE Standard VAT',
                    'code': 'VAT5',
                    'rate': Decimal('5.000'),
                    'is_active': True
                },
                {
                    'country': 'AE',
                    'category': 'ZERO',
                    'name': 'UAE Zero-Rated',
                    'code': 'VAT0',
                    'rate': Decimal('0.000'),
                    'is_active': True
                },
                {
                    'country': 'AE',
                    'category': 'EXEMPT',
                    'name': 'UAE Exempt',
                    'code': 'EXEMPT',
                    'rate': Decimal('0.000'),
                    'is_active': True
                },
                
                # Saudi Arabia - VAT (15%)
                {
                    'country': 'SA',
                    'category': 'STANDARD',
                    'name': 'KSA Standard VAT',
                    'code': 'VAT15',
                    'rate': Decimal('15.000'),
                    'is_active': True
                },
                {
                    'country': 'SA',
                    'category': 'ZERO',
                    'name': 'KSA Zero-Rated',
                    'code': 'VAT0',
                    'rate': Decimal('0.000'),
                    'is_active': True
                },
                {
                    'country': 'SA',
                    'category': 'EXEMPT',
                    'name': 'KSA Exempt',
                    'code': 'EXEMPT',
                    'rate': Decimal('0.000'),
                    'is_active': True
                },
            ]

            created_tax_rates = 0
            for tax_data in tax_rates_data:
                tax_rate, created = TaxRate.objects.get_or_create(
                    country=tax_data['country'],
                    category=tax_data['category'],
                    code=tax_data['code'],
                    defaults=tax_data
                )
                if created:
                    created_tax_rates += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created tax rate: {tax_rate.country} - {tax_rate.name} ({tax_rate.rate}%)'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  - Tax rate already exists: {tax_rate.country} - {tax_rate.name}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully loaded data!\n'
                f'   Currencies created: {created_currencies}\n'
                f'   Tax rates created: {created_tax_rates}\n'
            )
        )

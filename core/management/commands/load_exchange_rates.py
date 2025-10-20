"""
Management command to load exchange rates
Usage: python manage.py load_exchange_rates
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.models import Currency, ExchangeRate
from decimal import Decimal
from datetime import date


class Command(BaseCommand):
    help = 'Load exchange rates for all currencies (base: AED)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date for exchange rates (YYYY-MM-DD). Default: today',
        )

    def handle(self, *args, **options):
        rate_date = options.get('date')
        if rate_date:
            try:
                rate_date = date.fromisoformat(rate_date)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f'Invalid date format: {rate_date}. Use YYYY-MM-DD')
                )
                return
        else:
            rate_date = date.today()

        self.stdout.write(
            self.style.WARNING(f'\n💱 Loading exchange rates for {rate_date}...\n')
        )

        with transaction.atomic():
            # Get base currency (AED)
            try:
                base_currency = Currency.objects.get(is_base=True)
            except Currency.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('No base currency found! Please set a base currency.')
                )
                return

            self.stdout.write(
                self.style.SUCCESS(f'Base Currency: {base_currency.code} ({base_currency.name})\n')
            )

            # Exchange rates as of October 2025 (approximate market rates)
            # All rates are TO AED (how many AED = 1 foreign currency)
            exchange_rates_data = [
                # AED to AED (always 1.0)
                {
                    'from_currency': 'AED',
                    'to_currency': 'AED',
                    'rate': Decimal('1.000000'),
                    'description': 'AED to AED (base)'
                },
                
                # USD to AED (Fixed peg: 1 USD = 3.6725 AED)
                {
                    'from_currency': 'USD',
                    'to_currency': 'AED',
                    'rate': Decimal('3.672500'),
                    'description': 'US Dollar to UAE Dirham (pegged rate)'
                },
                {
                    'from_currency': 'AED',
                    'to_currency': 'USD',
                    'rate': Decimal('0.272258'),
                    'description': 'UAE Dirham to US Dollar'
                },
                
                # EUR to AED (1 EUR ≈ 4.01 AED)
                {
                    'from_currency': 'EUR',
                    'to_currency': 'AED',
                    'rate': Decimal('4.012500'),
                    'description': 'Euro to UAE Dirham'
                },
                {
                    'from_currency': 'AED',
                    'to_currency': 'EUR',
                    'rate': Decimal('0.249221'),
                    'description': 'UAE Dirham to Euro'
                },
                
                # SAR to AED (1 SAR ≈ 0.98 AED)
                {
                    'from_currency': 'SAR',
                    'to_currency': 'AED',
                    'rate': Decimal('0.979200'),
                    'description': 'Saudi Riyal to UAE Dirham'
                },
                {
                    'from_currency': 'AED',
                    'to_currency': 'SAR',
                    'rate': Decimal('1.021240'),
                    'description': 'UAE Dirham to Saudi Riyal'
                },
                
                # EGP to AED (1 EGP ≈ 0.075 AED)
                {
                    'from_currency': 'EGP',
                    'to_currency': 'AED',
                    'rate': Decimal('0.074800'),
                    'description': 'Egyptian Pound to UAE Dirham'
                },
                {
                    'from_currency': 'AED',
                    'to_currency': 'EGP',
                    'rate': Decimal('13.368984'),
                    'description': 'UAE Dirham to Egyptian Pound'
                },
                
                # INR to AED (1 INR ≈ 0.044 AED)
                {
                    'from_currency': 'INR',
                    'to_currency': 'AED',
                    'rate': Decimal('0.044200'),
                    'description': 'Indian Rupee to UAE Dirham'
                },
                {
                    'from_currency': 'AED',
                    'to_currency': 'INR',
                    'rate': Decimal('22.624434'),
                    'description': 'UAE Dirham to Indian Rupee'
                },
                
                # Cross rates (major pairs for convenience)
                # USD to EUR
                {
                    'from_currency': 'USD',
                    'to_currency': 'EUR',
                    'rate': Decimal('0.915331'),
                    'description': 'US Dollar to Euro'
                },
                {
                    'from_currency': 'EUR',
                    'to_currency': 'USD',
                    'rate': Decimal('1.092506'),
                    'description': 'Euro to US Dollar'
                },
                
                # USD to SAR (1 USD ≈ 3.75 SAR - pegged)
                {
                    'from_currency': 'USD',
                    'to_currency': 'SAR',
                    'rate': Decimal('3.750000'),
                    'description': 'US Dollar to Saudi Riyal (pegged)'
                },
                {
                    'from_currency': 'SAR',
                    'to_currency': 'USD',
                    'rate': Decimal('0.266667'),
                    'description': 'Saudi Riyal to US Dollar'
                },
                
                # USD to EGP (1 USD ≈ 49.10 EGP)
                {
                    'from_currency': 'USD',
                    'to_currency': 'EGP',
                    'rate': Decimal('49.100000'),
                    'description': 'US Dollar to Egyptian Pound'
                },
                {
                    'from_currency': 'EGP',
                    'to_currency': 'USD',
                    'rate': Decimal('0.020367'),
                    'description': 'Egyptian Pound to US Dollar'
                },
                
                # USD to INR (1 USD ≈ 83.10 INR)
                {
                    'from_currency': 'USD',
                    'to_currency': 'INR',
                    'rate': Decimal('83.100000'),
                    'description': 'US Dollar to Indian Rupee'
                },
                {
                    'from_currency': 'INR',
                    'to_currency': 'USD',
                    'rate': Decimal('0.012033'),
                    'description': 'Indian Rupee to US Dollar'
                },
            ]

            created_rates = 0
            updated_rates = 0
            
            for rate_data in exchange_rates_data:
                try:
                    from_curr = Currency.objects.get(code=rate_data['from_currency'])
                    to_curr = Currency.objects.get(code=rate_data['to_currency'])
                    
                    # Check if rate already exists for this date
                    rate, created = ExchangeRate.objects.update_or_create(
                        from_currency=from_curr,
                        to_currency=to_curr,
                        rate_date=rate_date,
                        defaults={
                            'rate': rate_data['rate'],
                            'rate_type': 'SPOT',
                            'source': 'Initial Load',
                            'is_active': True
                        }
                    )
                    
                    if created:
                        created_rates += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Created: {from_curr.code}/{to_curr.code} = {rate.rate}'
                            )
                        )
                    else:
                        updated_rates += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ↻ Updated: {from_curr.code}/{to_curr.code} = {rate.rate}'
                            )
                        )
                        
                except Currency.DoesNotExist as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Currency not found: {rate_data["from_currency"]} or {rate_data["to_currency"]}'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error creating rate: {e}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully loaded exchange rates!\n'
                f'   Date: {rate_date}\n'
                f'   Rates created: {created_rates}\n'
                f'   Rates updated: {updated_rates}\n'
                f'   Total: {created_rates + updated_rates}\n'
            )
        )
        
        # Display summary
        self.stdout.write(self.style.WARNING('\n📊 Exchange Rate Summary:\n'))
        self.stdout.write('   All rates to AED (base currency):')
        for curr in Currency.objects.exclude(code='AED'):
            try:
                rate = ExchangeRate.objects.get(
                    from_currency=curr,
                    to_currency=base_currency,
                    rate_date=rate_date
                )
                self.stdout.write(f'     1 {curr.code} = {rate.rate} AED')
            except ExchangeRate.DoesNotExist:
                pass

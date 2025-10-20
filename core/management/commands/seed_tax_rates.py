"""
Management command to seed tax rates for different countries
"""
from django.core.management.base import BaseCommand
from core.models import TaxRate
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed tax rates for UAE, Saudi Arabia, Egypt, and India'

    def handle(self, *args, **options):
        self.stdout.write('Seeding tax rates...')
        
        tax_rates = [
            # UAE Tax Rates
            {
                'name': 'UAE VAT Standard',
                'rate': Decimal('5.000'),
                'country': 'AE',
                'category': 'STANDARD',
                'code': 'VAT5',
                'is_active': True,
            },
            {
                'name': 'UAE VAT Zero Rated',
                'rate': Decimal('0.000'),
                'country': 'AE',
                'category': 'ZERO',
                'code': 'VAT0',
                'is_active': True,
            },
            {
                'name': 'UAE VAT Exempt',
                'rate': Decimal('0.000'),
                'country': 'AE',
                'category': 'EXEMPT',
                'code': 'EXEMPT',
                'is_active': True,
            },
            
            # Saudi Arabia Tax Rates
            {
                'name': 'KSA VAT Standard',
                'rate': Decimal('15.000'),
                'country': 'SA',
                'category': 'STANDARD',
                'code': 'VAT15',
                'is_active': True,
            },
            {
                'name': 'KSA VAT Zero Rated',
                'rate': Decimal('0.000'),
                'country': 'SA',
                'category': 'ZERO',
                'code': 'VAT0',
                'is_active': True,
            },
            {
                'name': 'KSA VAT Exempt',
                'rate': Decimal('0.000'),
                'country': 'SA',
                'category': 'EXEMPT',
                'code': 'EXEMPT',
                'is_active': True,
            },
            
            # Egypt Tax Rates
            {
                'name': 'Egypt GST Standard',
                'rate': Decimal('14.000'),
                'country': 'EG',
                'category': 'STANDARD',
                'code': 'GST14',
                'is_active': True,
            },
            {
                'name': 'Egypt GST Zero Rated',
                'rate': Decimal('0.000'),
                'country': 'EG',
                'category': 'ZERO',
                'code': 'GST0',
                'is_active': True,
            },
            {
                'name': 'Egypt GST Exempt',
                'rate': Decimal('0.000'),
                'country': 'EG',
                'category': 'EXEMPT',
                'code': 'EXEMPT',
                'is_active': True,
            },
            
            # India Tax Rates
            {
                'name': 'India GST 5%',
                'rate': Decimal('5.000'),
                'country': 'IN',
                'category': 'STANDARD',
                'code': 'GST5',
                'is_active': True,
            },
            {
                'name': 'India GST 12%',
                'rate': Decimal('12.000'),
                'country': 'IN',
                'category': 'STANDARD',
                'code': 'GST12',
                'is_active': True,
            },
            {
                'name': 'India GST 18%',
                'rate': Decimal('18.000'),
                'country': 'IN',
                'category': 'STANDARD',
                'code': 'GST18',
                'is_active': True,
            },
            {
                'name': 'India GST 28%',
                'rate': Decimal('28.000'),
                'country': 'IN',
                'category': 'STANDARD',
                'code': 'GST28',
                'is_active': True,
            },
            {
                'name': 'India GST Zero Rated',
                'rate': Decimal('0.000'),
                'country': 'IN',
                'category': 'ZERO',
                'code': 'GST0',
                'is_active': True,
            },
            {
                'name': 'India GST Exempt',
                'rate': Decimal('0.000'),
                'country': 'IN',
                'category': 'EXEMPT',
                'code': 'EXEMPT',
                'is_active': True,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for rate_data in tax_rates:
            # Check if tax rate already exists
            existing = TaxRate.objects.filter(
                country=rate_data['country'],
                category=rate_data['category'],
                code=rate_data['code']
            ).first()
            
            if existing:
                # Update existing
                for key, value in rate_data.items():
                    setattr(existing, key, value)
                existing.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated: {rate_data["name"]} ({rate_data["country"]})')
                )
            else:
                # Create new
                TaxRate.objects.create(**rate_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {rate_data["name"]} ({rate_data["country"]})')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nTax rates seeding complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
        
        # Display summary
        self.stdout.write('\n=== Tax Rates Summary ===')
        for country_code, country_name in [('AE', 'UAE'), ('SA', 'KSA'), ('EG', 'Egypt'), ('IN', 'India')]:
            count = TaxRate.objects.filter(country=country_code, is_active=True).count()
            self.stdout.write(f'{country_name} ({country_code}): {count} active tax rates')

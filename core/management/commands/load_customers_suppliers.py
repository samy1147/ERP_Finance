"""
Management command to load sample customers and suppliers
Usage: python manage.py load_customers_suppliers
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from ar.models import Customer
from ap.models import Supplier
from core.models import Currency


class Command(BaseCommand):
    help = 'Load sample customers and suppliers with different currencies and countries'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n👥 Loading Customers and Suppliers...\n'))

        with transaction.atomic():
            # Get currencies
            try:
                aed = Currency.objects.get(code='AED')
                usd = Currency.objects.get(code='USD')
                eur = Currency.objects.get(code='EUR')
                sar = Currency.objects.get(code='SAR')
                inr = Currency.objects.get(code='INR')
                egp = Currency.objects.get(code='EGP')
            except Currency.DoesNotExist as e:
                self.stdout.write(
                    self.style.ERROR(
                        'Required currencies not found! Please run load_initial_data first.'
                    )
                )
                return

            # CUSTOMERS DATA
            customers_data = [
                {
                    'code': 'CUST-001',
                    'name': 'Emirates Trading LLC - Dubai',
                    'email': 'info@emiratestrading.ae',
                    'country': 'AE',
                    'currency': aed,
                    'vat_number': 'AE123456789012345',
                    'is_active': True,
                },
                {
                    'code': 'CUST-002',
                    'name': 'Global Tech Solutions Inc - USA',
                    'email': 'sales@globaltechsolutions.com',
                    'country': 'US',
                    'currency': usd,
                    'vat_number': 'US-123456789',
                    'is_active': True,
                },
                {
                    'code': 'CUST-003',
                    'name': 'Deutsche Handel GmbH - Germany',
                    'email': 'kontakt@deutschehandel.de',
                    'country': 'DE',
                    'currency': eur,
                    'vat_number': 'DE123456789',
                    'is_active': True,
                },
                {
                    'code': 'CUST-004',
                    'name': 'Al-Riyadh Commercial Est. - KSA',
                    'email': 'info@alriyadhcommercial.sa',
                    'country': 'SA',
                    'currency': sar,
                    'vat_number': 'SA300000012345678',
                    'is_active': True,
                },
                {
                    'code': 'CUST-005',
                    'name': 'Mumbai Industries Pvt Ltd - India',
                    'email': 'business@mumbaiindustries.in',
                    'country': 'IN',
                    'currency': inr,
                    'vat_number': 'GSTIN-29ABCDE1234F1Z5',
                    'is_active': True,
                },
                {
                    'code': 'CUST-006',
                    'name': 'Cairo Export Group - Egypt',
                    'email': 'export@cairogroup.eg',
                    'country': 'EG',
                    'currency': egp,
                    'vat_number': 'EG-123456789',
                    'is_active': True,
                },
                {
                    'code': 'CUST-007',
                    'name': 'Abu Dhabi Enterprises - UAE',
                    'email': 'contact@abudhabienterprises.ae',
                    'country': 'AE',
                    'currency': aed,
                    'vat_number': 'AE987654321098765',
                    'is_active': True,
                },
                {
                    'code': 'CUST-008',
                    'name': 'European Logistics SA - France',
                    'email': 'info@europeanlogistics.eu',
                    'country': 'FR',
                    'currency': eur,
                    'vat_number': 'FR12345678901',
                    'is_active': True,
                },
            ]

            # SUPPLIERS DATA
            suppliers_data = [
                {
                    'code': 'SUPP-001',
                    'name': 'UAE Manufacturing Co. - Dubai',
                    'email': 'orders@uaemanufacturing.ae',
                    'country': 'AE',
                    'currency': aed,
                    'vat_number': 'AE555666777888999',
                    'is_active': True,
                },
                {
                    'code': 'SUPP-002',
                    'name': 'American Supplies Corp - New York',
                    'email': 'sales@americansupplies.com',
                    'country': 'US',
                    'currency': usd,
                    'vat_number': 'US-987654321',
                    'is_active': True,
                },
                {
                    'code': 'SUPP-003',
                    'name': 'Euro Parts Distribution - Germany',
                    'email': 'info@europarts.de',
                    'country': 'DE',
                    'currency': eur,
                    'vat_number': 'DE987654321',
                    'is_active': True,
                },
                {
                    'code': 'SUPP-004',
                    'name': 'Saudi Equipment Trading - Jeddah',
                    'email': 'procurement@saudiequipment.sa',
                    'country': 'SA',
                    'currency': sar,
                    'vat_number': 'SA300999888777666',
                    'is_active': True,
                },
                {
                    'code': 'SUPP-005',
                    'name': 'Delhi Manufacturing Ltd - India',
                    'email': 'supplier@delhimfg.in',
                    'country': 'IN',
                    'currency': inr,
                    'vat_number': 'GSTIN-07ABCDE9876F1Z5',
                    'is_active': True,
                },
                {
                    'code': 'SUPP-006',
                    'name': 'Egyptian Textiles Co - Cairo',
                    'email': 'sales@egyptiantextiles.eg',
                    'country': 'EG',
                    'currency': egp,
                    'vat_number': 'EG-987654321',
                    'is_active': True,
                },
                {
                    'code': 'SUPP-007',
                    'name': 'Sharjah Industrial Supplies - UAE',
                    'email': 'contact@sharjahindustrial.ae',
                    'country': 'AE',
                    'currency': aed,
                    'vat_number': 'AE111222333444555',
                    'is_active': True,
                },
                {
                    'code': 'SUPP-008',
                    'name': 'International Tech Imports - San Francisco',
                    'email': 'imports@intltech.com',
                    'country': 'US',
                    'currency': usd,
                    'vat_number': 'US-555666777',
                    'is_active': True,
                },
                {
                    'code': 'SUPP-009',
                    'name': 'Italia Machinery SRL - Milan',
                    'email': 'vendite@italiamachinery.it',
                    'country': 'IT',
                    'currency': eur,
                    'vat_number': 'IT12345678901',
                    'is_active': True,
                },
                {
                    'code': 'SUPP-010',
                    'name': 'Bangalore Tech Solutions - India',
                    'email': 'vendor@bangaloretech.in',
                    'country': 'IN',
                    'currency': inr,
                    'vat_number': 'GSTIN-29ZYXWV5432F1Z5',
                    'is_active': True,
                },
            ]

            # Create Customers
            self.stdout.write(self.style.WARNING('Creating Customers...'))
            customers_created = 0
            for customer_data in customers_data:
                customer, created = Customer.objects.get_or_create(
                    code=customer_data['code'],
                    defaults=customer_data
                )
                
                if created:
                    customers_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created: {customer.code} - {customer.name} ({customer.country})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  - Already exists: {customer.code} - {customer.name}'
                        )
                    )

            # Create Suppliers
            self.stdout.write(self.style.WARNING('\nCreating Suppliers...'))
            suppliers_created = 0
            for supplier_data in suppliers_data:
                supplier, created = Supplier.objects.get_or_create(
                    code=supplier_data['code'],
                    defaults=supplier_data
                )
                
                if created:
                    suppliers_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created: {supplier.code} - {supplier.name} ({supplier.country})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  - Already exists: {supplier.code} - {supplier.name}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully loaded customers and suppliers!\n'
                f'   Customers created: {customers_created}\n'
                f'   Suppliers created: {suppliers_created}\n'
            )
        )
        
        # Display summary
        self.stdout.write(self.style.WARNING('\n📊 Summary by Currency:\n'))
        
        self.stdout.write(self.style.WARNING('\nCustomers:'))
        for curr in [aed, usd, eur, sar, inr, egp]:
            count = Customer.objects.filter(currency=curr).count()
            if count > 0:
                self.stdout.write(f'   {curr.code}: {count} customers')
        
        self.stdout.write(self.style.WARNING('\nSuppliers:'))
        for curr in [aed, usd, eur, sar, inr, egp]:
            count = Supplier.objects.filter(currency=curr).count()
            if count > 0:
                self.stdout.write(f'   {curr.code}: {count} suppliers')
        
        total_customers = Customer.objects.count()
        total_suppliers = Supplier.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'\n   Total Customers: {total_customers}\n'
                f'   Total Suppliers: {total_suppliers}\n'
            )
        )

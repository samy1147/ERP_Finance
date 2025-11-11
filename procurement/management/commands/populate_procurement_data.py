"""
Management command to populate procurement tables with sample data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import random

from ap.models import Supplier


class Command(BaseCommand):
    help = 'Populate procurement tables with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample procurement data...')
        
        # Get or create a user
        user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        if not user.has_usable_password():
            user.set_password('admin')
            user.save()
        
        # Create suppliers
        suppliers = []
        supplier_names = [
            'Acme Corp', 'Global Supplies Inc', 'TechVendor Ltd', 
            'Office Solutions', 'Industrial Partners', 'Quality Goods Co'
        ]
        
        for name in supplier_names:
            supplier, created = Supplier.objects.get_or_create(
                name=name,
                defaults={
                    'email': f'{name.lower().replace(" ", "")}@example.com',
                    'phone': f'+1-555-{random.randint(1000, 9999)}',
                    'is_active': True,
                }
            )
            suppliers.append(supplier)
            if created:
                self.stdout.write(f'  Created supplier: {name}')
        
        # Try to create Contracts if the model exists
        try:
            from procurement.contracts.models import Contract
            from core.models import Currency
            from django.contrib.contenttypes.models import ContentType
            
            usd, _ = Currency.objects.get_or_create(code='USD', defaults={'name': 'US Dollar', 'symbol': '$'})
            supplier_ct = ContentType.objects.get(app_label='ap', model='supplier')
            
            contract_types = ['PURCHASE', 'SERVICE', 'MASTER']
            for i in range(6):
                supplier = random.choice(suppliers)
                Contract.objects.get_or_create(
                    contract_number=f'CTR-2025-{i+1:04d}',
                    defaults={
                        'contract_title': f'Contract for {supplier.name}',
                        'contract_type': random.choice(contract_types),
                        'party_content_type': supplier_ct,
                        'party_object_id': supplier.id,
                        'contract_date': timezone.now().date(),
                        'effective_date': timezone.now().date(),
                        'expiry_date': (timezone.now() + timedelta(days=365)).date(),
                        'currency': usd,
                        'total_value': Decimal(random.randint(10000, 100000)),
                        'annual_value': Decimal(random.randint(10000, 100000)),
                        'term_months': 12,
                        'status': random.choice(['DRAFT', 'APPROVED', 'ACTIVE']),
                        'contract_owner': user,
                    }
                )
            self.stdout.write('  Created 6 contracts')
        except Exception as e:
            self.stdout.write(f'  Skipped contracts: {str(e)}')
        
        # Try to create Vendor Bills
        # Note: Vendor bills table has app_label mismatch issue, skipping for now
        self.stdout.write('  Skipped vendor bills (table name mismatch - vendor_bill vs vendor_bills)')
        
        # Try to create Catalog Items
        try:
            from procurement.catalog.models import CatalogItem, CatalogCategory, UnitOfMeasure
            from core.models import Currency
            
            usd, _ = Currency.objects.get_or_create(code='USD', defaults={'name': 'US Dollar', 'symbol': '$'})
            
            # Create UoM
            pcs, _ = UnitOfMeasure.objects.get_or_create(code='PCS', defaults={'name': 'Pieces', 'uom_type': 'QUANTITY'})
            each, _ = UnitOfMeasure.objects.get_or_create(code='EA', defaults={'name': 'Each', 'uom_type': 'QUANTITY'})
            
            # Create Categories
            it_cat, _ = CatalogCategory.objects.get_or_create(code='IT', defaults={'name': 'IT Equipment'})
            office_cat, _ = CatalogCategory.objects.get_or_create(code='OFF', defaults={'name': 'Office Supplies'})
            
            # Create Items
            item_names = [
                ('Laptop Computer', it_cat, 1200, 'GOODS'),
                ('Office Desk', office_cat, 450, 'GOODS'),
                ('Ergonomic Chair', office_cat, 350, 'GOODS'),
                ('Printer/Scanner', it_cat, 280, 'GOODS'),
                ('Monitor 27"', it_cat, 320, 'GOODS'),
                ('Wireless Mouse', it_cat, 25, 'CONSUMABLE'),
                ('Keyboard', it_cat, 65, 'CONSUMABLE'),
                ('USB Hub', it_cat, 35, 'GOODS'),
                ('Webcam', it_cat, 85, 'GOODS'),
                ('Headset', it_cat, 95, 'GOODS'),
            ]
            
            for idx, (name, category, price, item_type) in enumerate(item_names, 1):
                supplier = random.choice(suppliers)
                CatalogItem.objects.get_or_create(
                    sku=f'SKU-{idx:04d}',
                    defaults={
                        'item_code': f'ITEM-{idx:04d}',
                        'name': name,
                        'short_description': f'High quality {name.lower()} for office use',
                        'category': category,
                        'item_type': item_type,
                        'unit_of_measure': each,
                        'list_price': Decimal(price),
                        'currency': usd,
                        'preferred_supplier': supplier,
                        'is_active': True,
                        'is_purchasable': True,
                        'created_by': user,
                    }
                )
            self.stdout.write('  Created 10 catalog items')
        except Exception as e:
            self.stdout.write(f'  Skipped catalog items: {str(e)}')
        
        # Try to create RFx Events
        try:
            from procurement.rfx.models import RFxEvent
            from core.models import Currency
            
            usd, _ = Currency.objects.get_or_create(code='USD', defaults={'name': 'US Dollar', 'symbol': '$'})
            rfx_types = ['RFQ', 'RFP', 'RFI']
            
            for i in range(5):
                submission_start = timezone.now() - timedelta(days=random.randint(1, 5))
                RFxEvent.objects.get_or_create(
                    rfx_number=f'RFX-2025-{i+1:04d}',
                    defaults={
                        'title': f'Request for {random.choice(["Office Supplies", "IT Equipment", "Consulting Services", "Maintenance"])}',
                        'event_type': random.choice(rfx_types),
                        'status': random.choice(['DRAFT', 'PUBLISHED', 'CLOSED']),
                        'description': f'RFx event for procurement needs',
                        'submission_start_date': submission_start,
                        'submission_due_date': submission_start + timedelta(days=random.randint(7, 30)),
                        'evaluation_due_date': submission_start + timedelta(days=random.randint(35, 60)),
                        'category': random.choice(['IT', 'Office Supplies', 'Services', 'Equipment']),
                        'currency': usd,
                        'created_by': user,
                    }
                )
            self.stdout.write('  Created 5 RFx events')
        except Exception as e:
            self.stdout.write(f'  Skipped RFx events: {str(e)}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Successfully populated procurement data!'))
        self.stdout.write(self.style.SUCCESS('  Use username: admin / password: admin to login'))

# Create Sample Data - Django Management Command
from django.core.management.base import BaseCommand
from core.models import Currency, TaxRate
from finance.models import Account
from ar.models import Customer
from ap.models import Supplier
from decimal import Decimal


class Command(BaseCommand):
    help = 'Creates sample data for testing the Finance ERP'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Creating sample data for Finance ERP...\n")

        # 1. Create Currency
        self.stdout.write("📊 Creating Currencies...")
        usd, _ = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'US Dollar',
                'symbol': '$',
                'is_base': True
            }
        )
        eur, _ = Currency.objects.get_or_create(
            code='EUR',
            defaults={
                'name': 'Euro',
                'symbol': '€',
                'is_base': False
            }
        )
        aed, _ = Currency.objects.get_or_create(
            code='AED',
            defaults={
                'name': 'UAE Dirham',
                'symbol': 'د.إ',
                'is_base': False
            }
        )
        self.stdout.write(self.style.SUCCESS(f"✓ Created {Currency.objects.count()} currencies"))

        # 2. Create Chart of Accounts
        self.stdout.write("\n💰 Creating Chart of Accounts...")
        accounts_data = [
            ('1000', 'Cash', 'AS'),
            ('1200', 'Accounts Receivable', 'AS'),
            ('1500', 'Inventory', 'AS'),
            ('1800', 'Equipment', 'AS'),
            ('2000', 'Accounts Payable', 'LI'),
            ('2500', 'Long-term Debt', 'LI'),
            ('3000', 'Common Stock', 'EQ'),
            ('3500', 'Retained Earnings', 'EQ'),
            ('4000', 'Sales Revenue', 'IN'),
            ('4100', 'Service Revenue', 'IN'),
            ('5000', 'Cost of Goods Sold', 'EX'),
            ('6000', 'Salaries Expense', 'EX'),
            ('6100', 'Rent Expense', 'EX'),
            ('6200', 'Utilities Expense', 'EX'),
        ]

        for code, name, account_type in accounts_data:
            acc, created = Account.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'type': account_type,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f"  ✓ Created account: {code} - {name}")
        self.stdout.write(self.style.SUCCESS(f"✓ Total accounts: {Account.objects.count()}"))

        # 3. Create Tax Rates
        self.stdout.write("\n💵 Creating Tax Rates...")
        tax1, created1 = TaxRate.objects.get_or_create(
            code='VAT5',
            country='AE',
            category='STANDARD',
            defaults={
                'name': 'VAT 5%',
                'rate': Decimal('5.000'),
                'is_active': True
            }
        )
        if created1:
            self.stdout.write(f"  ✓ Created tax rate: VAT 5%")
        
        tax2, created2 = TaxRate.objects.get_or_create(
            code='VAT15',
            country='SA',
            category='STANDARD',
            defaults={
                'name': 'VAT 15%',
                'rate': Decimal('15.000'),
                'is_active': True
            }
        )
        if created2:
            self.stdout.write(f"  ✓ Created tax rate: VAT 15%")
            
        self.stdout.write(self.style.SUCCESS(f"✓ Total tax rates: {TaxRate.objects.count()}"))

        # 4. Create Customers
        self.stdout.write("\n👥 Creating Customers...")
        customers_data = [
            ('CUST001', 'ACME Corporation', 'contact@acme.com'),
            ('CUST002', 'Global Tech Industries', 'info@globaltech.com'),
            ('CUST003', 'Smith & Associates', 'john@smithassoc.com'),
            ('CUST004', 'Retail Solutions LLC', 'sales@retailsol.com'),
            ('CUST005', 'Dubai Trading Co', 'trading@dubai.com'),
        ]

        for code, name, email in customers_data:
            cust, created = Customer.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'email': email,
                    'country': 'AE',
                    'currency': usd,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f"  ✓ Created customer: {name}")
        
        self.stdout.write(self.style.SUCCESS(f"✓ Total customers: {Customer.objects.count()}"))

        # 5. Create Suppliers
        self.stdout.write("\n🏭 Creating Suppliers...")
        suppliers_data = [
            ('SUP001', 'Office Supplies Co', 'orders@officesupplies.com'),
            ('SUP002', 'Equipment Rentals Inc', 'rentals@equipmentinc.com'),
            ('SUP003', 'Tech Parts Distributor', 'sales@techparts.com'),
            ('SUP004', 'Utility Services Ltd', 'billing@utilityservices.com'),
            ('SUP005', 'Raw Materials Supplier', 'info@rawmaterials.com'),
        ]

        for code, name, email in suppliers_data:
            supp, created = Supplier.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'email': email,
                    'country': 'AE',
                    'currency': usd,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f"  ✓ Created supplier: {name}")
        
        self.stdout.write(self.style.SUCCESS(f"✓ Total suppliers: {Supplier.objects.count()}"))

        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("✅ SAMPLE DATA CREATION COMPLETE!"))
        self.stdout.write("="*60)
        self.stdout.write(f"""
Summary:
  - Currencies: {Currency.objects.count()}
  - Accounts: {Account.objects.count()}
  - Tax Rates: {TaxRate.objects.count()}
  - Customers: {Customer.objects.count()}
  - Suppliers: {Supplier.objects.count()}

🌐 Refresh your frontend at http://localhost:3001
   You should now see data!

📊 Django Admin: http://127.0.0.1:8000/admin/
   (Create superuser: python manage.py createsuperuser)

💡 Next steps:
   - View Chart of Accounts
   - Create invoices
   - Make payments
   - View reports
""")

from django.core.management.base import BaseCommand
from django.db import transaction

# Import from existing apps - use your actual models!
from core.models import Currency, TaxRate
from finance.models import Account
from ar.models import Customer
from ap.models import Supplier

class Command(BaseCommand):
    help = "Seed base ERP catalogs: accounts, currencies, tax rates, and sample customers/suppliers."

    def add_arguments(self, parser):
        parser.add_argument("--fresh", action="store_true", help="Clear basic catalogs before seeding")

    @transaction.atomic
    def handle(self, *args, **options):
        fresh = options.get("fresh")

        if fresh:
            self.stdout.write(self.style.WARNING("⚠️  Clearing simple catalogs..."))
            # Be careful with Account deletion - it may have FK dependencies
            # Account.objects.all().delete()
            Supplier.objects.all().delete()
            Customer.objects.all().delete()
            TaxRate.objects.all().delete()
            Currency.objects.all().delete()

        # --- Currencies ---
        self.stdout.write("📦 Seeding currencies...")
        currencies = [
            dict(code="AED", name="UAE Dirham", symbol="د.إ", is_base=True),
            dict(code="SAR", name="Saudi Riyal", symbol="﷼", is_base=False),
            dict(code="EGP", name="Egyptian Pound", symbol="E£", is_base=False),
            dict(code="INR", name="Indian Rupee", symbol="₹", is_base=False),
            dict(code="USD", name="US Dollar", symbol="$", is_base=False),
            dict(code="EUR", name="Euro", symbol="€", is_base=False),
        ]
        for c in currencies:
            obj, created = Currency.objects.get_or_create(code=c["code"], defaults=c)
            if created:
                self.stdout.write(f"  ✅ Created currency: {c['code']}")
            else:
                self.stdout.write(f"  ℹ️  Currency already exists: {c['code']}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Currencies: {Currency.objects.count()} total"))

        # --- Tax Rates (country/category/code with historical support) ---
        self.stdout.write("📦 Seeding tax rates (country/category/code)...")
        # (category, name, code, rate, effective_from, effective_to, is_active)
        VAT_PRESETS = {
            "AE": [
                ("STANDARD", "VAT 5%", "VAT5", 5.000, "2018-01-01", None, True),
                ("ZERO",     "VAT 0%", "VAT0", 0.000, "2018-01-01", None, True),
                ("EXEMPT",   "VAT Exempt", "VATX", 0.000, "2018-01-01", None, True),
            ],
            "SA": [
                # Historical rate (2018-2020) - preserved from current file
                ("STANDARD", "VAT 5% (historical)", "VAT5", 5.000, "2018-01-01", "2020-06-30", False),
                # Current rate (2020+)
                ("STANDARD", "VAT 15%", "VAT15", 15.000, "2020-07-01", None, True),
                ("ZERO",     "VAT 0%",  "VAT0",  0.000,  "2018-01-01", None, True),
                ("EXEMPT",   "VAT Exempt", "VATX", 0.000, "2018-01-01", None, True),
            ],
            "EG": [
                ("STANDARD", "VAT 14%", "VAT14", 14.000, "2017-01-01", None, True),
                ("ZERO",     "VAT 0%",  "VAT0",  0.000,  "2017-01-01", None, True),
                ("EXEMPT",   "VAT Exempt", "VATX", 0.000, "2017-01-01", None, True),
            ],
            "IN": [
                ("STANDARD", "GST 18%", "GST18", 18.000, "2017-07-01", None, True),
                ("ZERO",     "GST 0%",  "GST0",  0.000,  "2017-07-01", None, True),
                ("EXEMPT",   "GST Exempt", "GSTX", 0.000, "2017-07-01", None, True),
            ],
        }
        created_cnt = 0
        for cc, items in VAT_PRESETS.items():
            for category, name, code, rate, eff_from, eff_to, is_active in items:
                obj, created = TaxRate.objects.get_or_create(
                    country=cc, category=category, code=code, effective_from=eff_from,
                    defaults={
                        "name": name, 
                        "rate": rate, 
                        "effective_to": eff_to,
                        "is_active": is_active
                    }
                )
                if created:
                    created_cnt += 1
                    status = "(historical)" if eff_to else ""
                    self.stdout.write(f"  ✅ Created tax rate: {cc}-{category}-{code} ({rate}%) {status}")
                else:
                    self.stdout.write(f"  ℹ️  Tax rate exists: {cc}-{category}-{code}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Tax Rates: {TaxRate.objects.count()} total (+{created_cnt} new)"))

        # --- Accounts (minimal CoA) ---
        self.stdout.write("📦 Seeding chart of accounts...")
        accounts = [
            dict(code="1110", name="Cash at Bank", type="AS", is_active=True),
            dict(code="1000", name="Accounts Receivable", type="AS", is_active=True),
            dict(code="2000", name="Accounts Payable", type="LI", is_active=True),
            dict(code="3000", name="Revenue", type="IN", is_active=True),
            dict(code="4000", name="Expense", type="EX", is_active=True),
        ]
        for a in accounts:
            obj, created = Account.objects.get_or_create(code=a["code"], defaults=a)
            if created:
                self.stdout.write(f"  ✅ Created account: {a['code']} - {a['name']}")
            else:
                self.stdout.write(f"  ℹ️  Account already exists: {a['code']}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Accounts: {Account.objects.count()} total"))

        # --- Customers ---
        self.stdout.write("📦 Seeding customers...")
        
        # Get currencies for FK relationships
        try:
            aed = Currency.objects.get(code="AED")
            sar = Currency.objects.get(code="SAR")
            egp = Currency.objects.get(code="EGP")
        except Currency.DoesNotExist as e:
            self.stderr.write(self.style.ERROR(f"❌ Currency not found: {e}"))
            return
        
        customers = [
            dict(code="CUST-001", name="Demo Customer UAE", email="demo.customer@example.com",
                 country="AE", currency=aed, vat_number="AE1234567890001", is_active=True),
            dict(code="CUST-002", name="KSA Retail Co", email="ar@ksa-retail.example",
                 country="SA", currency=sar, vat_number="SA3001234567890003", is_active=True),
            dict(code="CUST-003", name="Tech Solutions", email="tech@example.com",
                 country="AE", currency=aed, vat_number="AE1234567890002", is_active=True),
            dict(code="CUST-004", name="Retail Plus", email="retail@example.com",
                 country="AE", currency=aed, vat_number="AE1234567890003", is_active=True),
        ]
        for c in customers:
            # Use code for lookup if present
            lookup = {"code": c["code"]} if c.get("code") else {"name": c["name"]}
            obj, created = Customer.objects.get_or_create(**lookup, defaults=c)
            if created:
                self.stdout.write(f"  ✅ Created customer: {c.get('code', c['name'])}")
            else:
                self.stdout.write(f"  ℹ️  Customer already exists: {c.get('code', c['name'])}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Customers: {Customer.objects.count()} total"))

        # --- Suppliers ---
        self.stdout.write("📦 Seeding suppliers...")
        suppliers = [
            dict(code="SUPP-001", name="Demo Supplier UAE", email="ap@supplier.example",
                 country="AE", currency=aed, vat_number="AE0987654321001", is_active=True),
            dict(code="SUPP-002", name="Cairo Services Ltd", email="ap@cairo-services.example",
                 country="EG", currency=egp, vat_number="EG0123456789001", is_active=True),
            dict(code="SUPP-003", name="Office Supplies Co", email="supplies@example.com",
                 country="AE", currency=aed, vat_number="AE0987654321002", is_active=True),
            dict(code="SUPP-004", name="Tech Equipment LLC", email="tech@example.com",
                 country="AE", currency=aed, vat_number="AE0987654321003", is_active=True),
        ]
        for s in suppliers:
            # Use code for lookup if present
            lookup = {"code": s["code"]} if s.get("code") else {"name": s["name"]}
            obj, created = Supplier.objects.get_or_create(**lookup, defaults=s)
            if created:
                self.stdout.write(f"  ✅ Created supplier: {s.get('code', s['name'])}")
            else:
                self.stdout.write(f"  ℹ️  Supplier already exists: {s.get('code', s['name'])}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Suppliers: {Supplier.objects.count()} total"))
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Seeding complete!"))
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(self.style.SUCCESS(f"Total records created:"))
        self.stdout.write(self.style.SUCCESS(f"  • Currencies: {Currency.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"  • Tax Rates: {TaxRate.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"  • Accounts: {Account.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"  • Customers: {Customer.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"  • Suppliers: {Supplier.objects.count()}"))
        self.stdout.write(self.style.SUCCESS("="*60))

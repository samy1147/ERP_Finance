"""
Management command to load a complete chart of accounts
Usage: python manage.py load_chart_of_accounts
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from finance.models import Account


class Command(BaseCommand):
    help = 'Load a complete chart of accounts for all account types'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n📊 Loading Chart of Accounts...\n'))

        with transaction.atomic():
            # Chart of Accounts data
            accounts_data = [
                # ASSETS (1000-1999)
                {'code': '1000', 'name': 'Cash and Bank Accounts', 'type': Account.ASSET, 'parent': None},
                {'code': '1010', 'name': 'Petty Cash', 'type': Account.ASSET, 'parent': None},
                {'code': '1020', 'name': 'Emirates NBD - AED Account', 'type': Account.ASSET, 'parent': None},
                {'code': '1030', 'name': 'ADCB - USD Account', 'type': Account.ASSET, 'parent': None},
                {'code': '1040', 'name': 'Mashreq Bank - EUR Account', 'type': Account.ASSET, 'parent': None},
                {'code': '1050', 'name': 'SABB - SAR Account', 'type': Account.ASSET, 'parent': None},
                {'code': '1060', 'name': 'ICICI Bank - INR Account', 'type': Account.ASSET, 'parent': None},
                {'code': '1100', 'name': 'Accounts Receivable', 'type': Account.ASSET, 'parent': None},
                {'code': '1110', 'name': 'Trade Receivables - Local', 'type': Account.ASSET, 'parent': None},
                {'code': '1120', 'name': 'Trade Receivables - Export', 'type': Account.ASSET, 'parent': None},
                {'code': '1130', 'name': 'Allowance for Doubtful Accounts', 'type': Account.ASSET, 'parent': None},
                {'code': '1300', 'name': 'Inventory', 'type': Account.ASSET, 'parent': None},
                {'code': '1310', 'name': 'Raw Materials', 'type': Account.ASSET, 'parent': None},
                {'code': '1320', 'name': 'Work in Progress', 'type': Account.ASSET, 'parent': None},
                {'code': '1330', 'name': 'Finished Goods', 'type': Account.ASSET, 'parent': None},
                {'code': '1400', 'name': 'Prepaid Expenses', 'type': Account.ASSET, 'parent': None},
                {'code': '1410', 'name': 'Prepaid Insurance', 'type': Account.ASSET, 'parent': None},
                {'code': '1420', 'name': 'Prepaid Rent', 'type': Account.ASSET, 'parent': None},
                {'code': '1500', 'name': 'Fixed Assets', 'type': Account.ASSET, 'parent': None},
                {'code': '1510', 'name': 'Land', 'type': Account.ASSET, 'parent': None},
                {'code': '1520', 'name': 'Buildings', 'type': Account.ASSET, 'parent': None},
                {'code': '1530', 'name': 'Machinery & Equipment', 'type': Account.ASSET, 'parent': None},
                {'code': '1540', 'name': 'Vehicles', 'type': Account.ASSET, 'parent': None},
                {'code': '1550', 'name': 'Furniture & Fixtures', 'type': Account.ASSET, 'parent': None},
                {'code': '1560', 'name': 'Computer Equipment', 'type': Account.ASSET, 'parent': None},
                {'code': '1600', 'name': 'Accumulated Depreciation', 'type': Account.ASSET, 'parent': None},
                {'code': '1610', 'name': 'Accumulated Depreciation - Buildings', 'type': Account.ASSET, 'parent': None},
                {'code': '1620', 'name': 'Accumulated Depreciation - Equipment', 'type': Account.ASSET, 'parent': None},
                {'code': '1630', 'name': 'Accumulated Depreciation - Vehicles', 'type': Account.ASSET, 'parent': None},
                {'code': '1700', 'name': 'Intangible Assets', 'type': Account.ASSET, 'parent': None},
                {'code': '1710', 'name': 'Goodwill', 'type': Account.ASSET, 'parent': None},
                {'code': '1720', 'name': 'Patents & Trademarks', 'type': Account.ASSET, 'parent': None},
                {'code': '1730', 'name': 'Software Licenses', 'type': Account.ASSET, 'parent': None},

                # LIABILITIES (2000-2999)
                {'code': '2000', 'name': 'Accounts Payable', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2010', 'name': 'Trade Payables - Local', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2020', 'name': 'Trade Payables - Import', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2100', 'name': 'VAT Payable (Output Tax)', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2110', 'name': 'VAT Recoverable (Input Tax)', 'type': Account.ASSET, 'parent': None},
                {'code': '2200', 'name': 'Short-term Loans', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2210', 'name': 'Bank Overdraft', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2220', 'name': 'Short-term Bank Loans', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2300', 'name': 'Tax Liabilities', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2310', 'name': 'Corporate Tax Payable', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2320', 'name': 'Withholding Tax Payable', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2300', 'name': 'Tax Liabilities', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2310', 'name': 'Corporate Tax Payable', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2320', 'name': 'Withholding Tax Payable', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2400', 'name': 'Accrued Expenses', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2410', 'name': 'Accrued Salaries', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2420', 'name': 'Accrued Utilities', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2430', 'name': 'Accrued Interest', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2500', 'name': 'Employee Benefits Payable', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2510', 'name': 'Salaries Payable', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2520', 'name': 'Employee Provident Fund', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2530', 'name': 'End of Service Benefits', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2530', 'name': 'End of Service Benefits', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2600', 'name': 'Customer Deposits', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2610', 'name': 'Advance from Customers', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2610', 'name': 'Advance from Customers', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2700', 'name': 'Long-term Liabilities', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2710', 'name': 'Long-term Bank Loans', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2720', 'name': 'Bonds Payable', 'type': Account.LIABILITY, 'parent': None},
                {'code': '2730', 'name': 'Mortgage Payable', 'type': Account.LIABILITY, 'parent': None},

                # EQUITY (3000-3999)
                {'code': '3000', 'name': 'Share Capital', 'type': Account.EQUITY, 'parent': None},
                {'code': '3010', 'name': 'Ordinary Share Capital', 'type': Account.EQUITY, 'parent': None},
                {'code': '3020', 'name': 'Preference Share Capital', 'type': Account.EQUITY, 'parent': None},
                {'code': '3100', 'name': 'Reserves', 'type': Account.EQUITY, 'parent': None},
                {'code': '3110', 'name': 'Legal Reserve', 'type': Account.EQUITY, 'parent': None},
                {'code': '3120', 'name': 'General Reserve', 'type': Account.EQUITY, 'parent': None},
                {'code': '3130', 'name': 'Revaluation Reserve', 'type': Account.EQUITY, 'parent': None},
                {'code': '3200', 'name': 'Retained Earnings', 'type': Account.EQUITY, 'parent': None},
                {'code': '3210', 'name': 'Retained Earnings - Prior Years', 'type': Account.EQUITY, 'parent': None},
                {'code': '3220', 'name': 'Retained Earnings - Current Year', 'type': Account.EQUITY, 'parent': None},
                {'code': '3300', 'name': 'Dividends', 'type': Account.EQUITY, 'parent': None},
                {'code': '3310', 'name': 'Dividends Declared', 'type': Account.EQUITY, 'parent': None},
                {'code': '3400', 'name': 'Foreign Currency Translation Reserve', 'type': Account.EQUITY, 'parent': None},
                {'code': '3500', 'name': 'Unrealized Gains/Losses', 'type': Account.EQUITY, 'parent': None},

                # INCOME (4000-4999)
                {'code': '4000', 'name': 'Sales Revenue', 'type': Account.INCOME, 'parent': None},
                {'code': '4010', 'name': 'Product Sales - Local', 'type': Account.INCOME, 'parent': None},
                {'code': '4020', 'name': 'Product Sales - Export', 'type': Account.INCOME, 'parent': None},
                {'code': '4030', 'name': 'Service Revenue', 'type': Account.INCOME, 'parent': None},
                {'code': '4040', 'name': 'Consulting Revenue', 'type': Account.INCOME, 'parent': None},
                {'code': '4100', 'name': 'Sales Returns & Allowances', 'type': Account.INCOME, 'parent': None},
                {'code': '4110', 'name': 'Sales Returns', 'type': Account.INCOME, 'parent': None},
                {'code': '4120', 'name': 'Sales Discounts', 'type': Account.INCOME, 'parent': None},
                {'code': '4200', 'name': 'Other Operating Income', 'type': Account.INCOME, 'parent': None},
                {'code': '4210', 'name': 'Rental Income', 'type': Account.INCOME, 'parent': None},
                {'code': '4220', 'name': 'Commission Income', 'type': Account.INCOME, 'parent': None},
                {'code': '4300', 'name': 'Non-Operating Income', 'type': Account.INCOME, 'parent': None},
                {'code': '4310', 'name': 'Interest Income', 'type': Account.INCOME, 'parent': None},
                {'code': '4320', 'name': 'Dividend Income', 'type': Account.INCOME, 'parent': None},
                {'code': '4330', 'name': 'Foreign Exchange Gain', 'type': Account.INCOME, 'parent': None},
                {'code': '4340', 'name': 'Gain on Sale of Assets', 'type': Account.INCOME, 'parent': None},

                # EXPENSES (5000-5999)
                {'code': '5000', 'name': 'Cost of Goods Sold', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5010', 'name': 'Purchase of Raw Materials', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5020', 'name': 'Direct Labor', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5030', 'name': 'Manufacturing Overhead', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5040', 'name': 'Freight & Shipping Costs', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5100', 'name': 'Operating Expenses', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5110', 'name': 'Salaries & Wages', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5120', 'name': 'Employee Benefits', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5130', 'name': 'Rent Expense', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5140', 'name': 'Utilities Expense', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5150', 'name': 'Telephone & Internet', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5160', 'name': 'Office Supplies', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5170', 'name': 'Insurance Expense', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5180', 'name': 'Maintenance & Repairs', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5190', 'name': 'Cleaning & Janitorial', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5200', 'name': 'Selling Expenses', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5210', 'name': 'Advertising & Marketing', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5220', 'name': 'Sales Commissions', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5230', 'name': 'Shipping & Delivery', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5240', 'name': 'Trade Show Expenses', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5300', 'name': 'Administrative Expenses', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5310', 'name': 'Legal & Professional Fees', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5320', 'name': 'Accounting & Audit Fees', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5330', 'name': 'Bank Charges', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5340', 'name': 'Licenses & Permits', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5350', 'name': 'Subscriptions & Memberships', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5400', 'name': 'Travel & Entertainment', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5410', 'name': 'Travel Expenses', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5420', 'name': 'Meals & Entertainment', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5430', 'name': 'Vehicle Expenses', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5500', 'name': 'Depreciation & Amortization', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5510', 'name': 'Depreciation Expense', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5520', 'name': 'Amortization Expense', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5600', 'name': 'Financial Expenses', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5610', 'name': 'Interest Expense', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5620', 'name': 'Bank Loan Interest', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5630', 'name': 'Foreign Exchange Loss', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5700', 'name': 'Tax Expenses', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5710', 'name': 'Corporate Tax Expense', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5720', 'name': 'VAT Expense (non-recoverable)', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5800', 'name': 'Other Expenses', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5810', 'name': 'Loss on Sale of Assets', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5820', 'name': 'Bad Debt Expense', 'type': Account.EXPENSE, 'parent': None},
                {'code': '5830', 'name': 'Miscellaneous Expenses', 'type': Account.EXPENSE, 'parent': None},
            ]

            created_count = 0
            updated_count = 0
            
            for account_data in accounts_data:
                account, created = Account.objects.get_or_create(
                    code=account_data['code'],
                    defaults=account_data
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Created: {account.code} - {account.name}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  - Already exists: {account.code} - {account.name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully loaded chart of accounts!\n'
                f'   Accounts created: {created_count}\n'
                f'   Accounts already existing: {updated_count}\n'
            )
        )
        
        # Display summary by type
        self.stdout.write(self.style.WARNING('\n📋 Chart of Accounts Summary:\n'))
        
        for type_code, type_name in Account.TYPES:
            count = Account.objects.filter(type=type_code).count()
            self.stdout.write(f'   {type_name}: {count} accounts')
        
        total = Account.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'\n   Total Accounts: {total}\n')
        )

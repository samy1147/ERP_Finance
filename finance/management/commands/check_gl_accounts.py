"""
Management command to check and create required GL accounts for invoice posting
Usage: python manage.py check_gl_accounts [--fix]
"""
from django.core.management.base import BaseCommand
from finance.models import Account


class Command(BaseCommand):
    help = 'Check if required GL accounts exist for AR/AP invoice posting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically create missing accounts',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n🔍 Checking Required GL Accounts...\n'))
        
        # Required accounts for invoice posting
        required_accounts = {
            '1000': {'name': 'Cash and Bank Accounts', 'type': Account.ASSET},
            '1100': {'name': 'Accounts Receivable', 'type': Account.ASSET},
            '2000': {'name': 'Accounts Payable', 'type': Account.LIABILITY},
            '2100': {'name': 'VAT Payable (Output Tax)', 'type': Account.LIABILITY},
            '2110': {'name': 'VAT Recoverable (Input Tax)', 'type': Account.ASSET},
            '2220': {'name': 'Corporate Tax Payable', 'type': Account.LIABILITY},
            '4000': {'name': 'Sales Revenue', 'type': Account.INCOME},
            '5000': {'name': 'Operating Expenses', 'type': Account.EXPENSE},
            '6900': {'name': 'Corporate Tax Expense', 'type': Account.EXPENSE},
            '7150': {'name': 'Foreign Exchange Gains', 'type': Account.INCOME},
            '8150': {'name': 'Foreign Exchange Losses', 'type': Account.EXPENSE},
        }
        
        missing_accounts = []
        existing_accounts = []
        
        # Check each required account
        for code, details in required_accounts.items():
            account = Account.objects.filter(code=code).first()
            if account:
                existing_accounts.append((code, account.name, account.type))
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ {code} - {account.name} ({account.get_type_display()})')
                )
            else:
                missing_accounts.append((code, details['name'], details['type']))
                self.stdout.write(
                    self.style.ERROR(f'  ❌ {code} - {details["name"]} (MISSING)')
                )
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'  • Total Required: {len(required_accounts)}')
        self.stdout.write(f'  • Existing: {len(existing_accounts)}')
        self.stdout.write(f'  • Missing: {len(missing_accounts)}')
        
        if missing_accounts:
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.ERROR('\n⚠️  Missing Accounts Will Cause Posting Errors!\n'))
            
            self.stdout.write('Missing Accounts:')
            for code, name, acc_type in missing_accounts:
                type_display = dict(Account.TYPES).get(acc_type, acc_type)
                self.stdout.write(f'  • {code} - {name} ({type_display})')
            
            if options['fix']:
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write(self.style.WARNING('\n🔧 Creating Missing Accounts...\n'))
                
                created_count = 0
                for code, name, acc_type in missing_accounts:
                    try:
                        Account.objects.create(
                            code=code,
                            name=name,
                            type=acc_type,
                            is_active=True
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✅ Created: {code} - {name}')
                        )
                        created_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ Failed to create {code}: {e}')
                        )
                
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write(
                    self.style.SUCCESS(f'\n✅ Successfully created {created_count} account(s)!')
                )
                
                if created_count == len(missing_accounts):
                    self.stdout.write(
                        self.style.SUCCESS('\n🎉 All required accounts are now in place!')
                    )
                    self.stdout.write('\nYou can now post AR/AP invoices without errors.\n')
            else:
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write(self.style.WARNING('\nTo create missing accounts, run:'))
                self.stdout.write(self.style.WARNING('  python manage.py check_gl_accounts --fix\n'))
        else:
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS('\n✅ All Required Accounts Exist!'))
            self.stdout.write('\nYour system is ready to post AR/AP invoices.\n')
        
        self.stdout.write('=' * 60 + '\n')

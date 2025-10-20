"""
Management command to load minimal chart of accounts (one account per type)
Usage: python manage.py load_minimal_accounts --clear
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from finance.models import Account


class Command(BaseCommand):
    help = 'Load minimal chart of accounts - one account per type'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing accounts before loading',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n📊 Loading Minimal Chart of Accounts...\n'))

        with transaction.atomic():
            # Clear existing accounts if requested
            if options['clear']:
                deleted_count = Account.objects.count()
                Account.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(f'  🗑️  Deleted {deleted_count} existing accounts\n')
                )

            # Minimal accounts - one per type
            minimal_accounts = [
                # ASSET
                {
                    'code': '1000',
                    'name': 'Assets',
                    'type': Account.ASSET,
                    'parent': None,
                    'is_active': True,
                },
                # LIABILITY
                {
                    'code': '2000',
                    'name': 'Liabilities',
                    'type': Account.LIABILITY,
                    'parent': None,
                    'is_active': True,
                },
                # EQUITY
                {
                    'code': '3000',
                    'name': 'Equity',
                    'type': Account.EQUITY,
                    'parent': None,
                    'is_active': True,
                },
                # INCOME
                {
                    'code': '4000',
                    'name': 'Income',
                    'type': Account.INCOME,
                    'parent': None,
                    'is_active': True,
                },
                # EXPENSE
                {
                    'code': '5000',
                    'name': 'Expenses',
                    'type': Account.EXPENSE,
                    'parent': None,
                    'is_active': True,
                },
            ]

            created_count = 0
            
            for account_data in minimal_accounts:
                account, created = Account.objects.get_or_create(
                    code=account_data['code'],
                    defaults=account_data
                )
                
                if created:
                    created_count += 1
                    type_display = dict(Account.TYPES)[account.type]
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created: {account.code} - {account.name} ({type_display})'
                        )
                    )
                else:
                    type_display = dict(Account.TYPES)[account.type]
                    self.stdout.write(
                        self.style.WARNING(
                            f'  - Already exists: {account.code} - {account.name} ({type_display})'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully loaded minimal chart of accounts!\n'
                f'   Accounts created: {created_count}\n'
            )
        )
        
        # Display summary
        self.stdout.write(self.style.WARNING('📋 Chart of Accounts Summary:\n'))
        
        for type_code, type_name in Account.TYPES:
            accounts = Account.objects.filter(type=type_code)
            count = accounts.count()
            if count > 0:
                for acc in accounts:
                    self.stdout.write(f'   {acc.code} - {acc.name} ({type_name})')
        
        total = Account.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'\n   Total Accounts: {total}\n')
        )

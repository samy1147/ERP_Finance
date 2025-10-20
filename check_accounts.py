import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from finance.models import Account

print('Accounts in DB:')
accounts = Account.objects.all().order_by('code')
print(f'Total: {accounts.count()}')
for a in accounts[:30]:
    print(f'  {a.code} - {a.name} ({a.type})')

# Check for corporate tax accounts specifically
print('\n\nChecking for Corporate Tax Accounts:')
try:
    tax_exp = Account.objects.get(code='6900')
    print(f'✓ TAX_CORP_EXP found: {tax_exp.code} - {tax_exp.name}')
except Account.DoesNotExist:
    print('✗ TAX_CORP_EXP (6900) NOT FOUND')

try:
    tax_payable = Account.objects.get(code='2400')
    print(f'✓ TAX_CORP_PAYABLE found: {tax_payable.code} - {tax_payable.name}')
except Account.DoesNotExist:
    print('✗ TAX_CORP_PAYABLE (2400) NOT FOUND')

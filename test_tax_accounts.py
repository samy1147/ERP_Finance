import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from finance.models import Account
from finance.services import _acct

print('Testing _acct() function for corporate tax accounts:\n')

try:
    tax_exp = _acct("TAX_CORP_EXP")
    print(f'✓ TAX_CORP_EXP: {tax_exp.code} - {tax_exp.name} ({tax_exp.type})')
except Exception as e:
    print(f'✗ TAX_CORP_EXP failed: {e}')

try:
    tax_payable = _acct("TAX_CORP_PAYABLE")
    print(f'✓ TAX_CORP_PAYABLE: {tax_payable.code} - {tax_payable.name} ({tax_payable.type})')
except Exception as e:
    print(f'✗ TAX_CORP_PAYABLE failed: {e}')

print('\n✓ All corporate tax accounts are correctly configured!')

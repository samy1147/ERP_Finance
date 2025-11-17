"""Check which GL accounts exist for payment posting"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from finance.services import ACCOUNT_CODES, get_account_by_code
from segment.models import XX_Segment

print('\nRequired GL accounts for payment posting:')
print('='*60)

for key in ['AR', 'AP', 'BANK', 'FX_GAIN', 'FX_LOSS']:
    code = ACCOUNT_CODES.get(key)
    print(f'\n{key}: {code}')
    try:
        acct = get_account_by_code(code)
        print(f'  ✅ Found: {acct.name} (ID: {acct.id})')
    except XX_Segment.DoesNotExist:
        print(f'  ❌ NOT FOUND in database')
    except Exception as e:
        print(f'  ❌ ERROR: {e}')

print('\n' + '='*60)

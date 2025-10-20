# Fix Chart of Accounts - Reload Script

## Problem Fixed
The Chart of Accounts has been updated to match the GL posting service expectations.

## Key Changes Made

### Account Code Changes:
- **1100**: Changed from "Bank Accounts" → **"Accounts Receivable"** (AR control account)
- **2100**: Changed from "Short-term Loans" → **"VAT Payable (Output Tax)"**
- **2110**: Changed from "Bank Overdraft" → **"VAT Recoverable (Input Tax)"**
- **1000**: Now "Cash and Bank Accounts" (Bank control)
- **1020-1060**: Individual bank accounts renumbered

## How to Apply the Fix

### Option 1: Fresh Start (Recommended if no important data)

```powershell
# 1. Clear existing accounts
python manage.py shell -c "from finance.models import Account; Account.objects.all().delete()"

# 2. Reload with corrected chart
python manage.py load_chart_of_accounts

# 3. Verify accounts loaded
python manage.py shell -c "from finance.models import Account; print(f'Total accounts: {Account.objects.count()}'); print('\nKey accounts:'); [print(f'{a.code} - {a.name}') for a in Account.objects.filter(code__in=['1000','1100','2000','2100','2110','4000','5000'])]"
```

### Option 2: Update Existing Accounts (If you have data)

```powershell
python manage.py shell
```

Then run:
```python
from finance.models import Account

# Backup account codes first
accounts_to_update = [
    ('1100', 'Bank Accounts', 'Cash and Bank Accounts', '1000'),
    ('1200', 'Accounts Receivable', 'Accounts Receivable', '1100'),
    ('2100', 'Short-term Loans', 'Short-term Loans', '2200'),
    ('2210', 'VAT Payable', 'VAT Payable (Output Tax)', '2100'),
]

# Apply updates
for old_code, old_name, new_name, new_code in accounts_to_update:
    try:
        account = Account.objects.get(code=old_code, name=old_name)
        account.code = new_code
        account.name = new_name
        account.save()
        print(f'✓ Updated {old_code} → {new_code}: {new_name}')
    except Account.DoesNotExist:
        print(f'✗ Account {old_code} - {old_name} not found')
    except Exception as e:
        print(f'✗ Error updating {old_code}: {e}')

# Create VAT Recoverable if missing
if not Account.objects.filter(code='2110').exists():
    Account.objects.create(
        code='2110',
        name='VAT Recoverable (Input Tax)',
        type='AS',  # Asset
        is_active=True
    )
    print('✓ Created 2110 - VAT Recoverable')

print('\nDone! Verify accounts:')
for code in ['1000', '1100', '2000', '2100', '2110', '4000', '5000']:
    try:
        a = Account.objects.get(code=code)
        print(f'{a.code} - {a.name} ({a.type})')
    except:
        print(f'✗ Account {code} NOT FOUND')
```

Exit shell: `exit()`

### Option 3: SQL Update (Advanced)

```sql
-- Backup first!
-- Then update:
BEGIN;

UPDATE finance_account SET code = '1000', name = 'Cash and Bank Accounts' 
WHERE code = '1100' AND name = 'Bank Accounts';

UPDATE finance_account SET code = '1100' 
WHERE code = '1200' AND name = 'Accounts Receivable';

UPDATE finance_account SET code = '2200' 
WHERE code = '2100' AND name = 'Short-term Loans';

UPDATE finance_account SET code = '2100', name = 'VAT Payable (Output Tax)' 
WHERE code = '2210' AND name = 'VAT Payable';

-- Create VAT Recoverable if missing
INSERT INTO finance_account (code, name, type, is_active) 
VALUES ('2110', 'VAT Recoverable (Input Tax)', 'AS', 1)
ON CONFLICT (code) DO NOTHING;

COMMIT;
```

## Verify the Fix

After applying any option above, verify by posting an AR invoice:

```powershell
# Check accounts exist
python manage.py shell -c "from finance.models import Account; required = ['1000','1100','2000','2100','2110','4000','5000']; missing = [c for c in required if not Account.objects.filter(code=c).exists()]; print('Missing accounts:', missing if missing else 'None - All good!')"
```

Expected output: `Missing accounts: None - All good!`

## Test AR Invoice Posting

1. Go to frontend: http://localhost:3000/ar/invoices
2. Find an APPROVED invoice
3. Click "Post" button
4. Should succeed without "Account '1100' does not exist" error

## Required Accounts Summary

After fix, these accounts MUST exist:

| Code | Name | Type | Used For |
|------|------|------|----------|
| 1000 | Cash and Bank Accounts | ASSET | Cash/Bank |
| 1100 | Accounts Receivable | ASSET | **AR Control** |
| 2000 | Accounts Payable | LIABILITY | **AP Control** |
| 2100 | VAT Payable (Output Tax) | LIABILITY | **AR VAT** |
| 2110 | VAT Recoverable (Input Tax) | ASSET | **AP VAT** |
| 4000 | Sales Revenue | INCOME | AR Revenue |
| 5000 | Operating Expenses | EXPENSE | AP Expenses |
| 6900 | Tax Expense | EXPENSE | Corporate Tax |
| 7150 | FX Gains | INCOME | FX Gains |
| 8150 | FX Losses | EXPENSE | FX Losses |

## Troubleshooting

### "Account still not found after reload"
- Make sure you cleared old accounts first
- Check for typos in account codes
- Verify `load_chart_of_accounts.py` was saved with changes

### "Duplicate key error"
- Old accounts still exist
- Run: `Account.objects.all().delete()` first
- Or use Option 2 to update existing accounts

### "Foreign key constraint error"
- Existing invoices/journals reference old accounts
- Use Option 2 (update) instead of delete/reload
- Or backup data, clear all, reload, restore

## Files Changed

- ✅ `core/management/commands/load_chart_of_accounts.py` - Updated account codes
- ✅ `docs/AR_POSTING_ACCOUNT_CONFLICT.md` - Detailed explanation
- ✅ `docs/ACCOUNT_FIX_GUIDE.md` - This file

## Next Steps

1. Apply one of the options above
2. Verify required accounts exist
3. Test posting an AR invoice
4. Test posting an AP invoice
5. Check journal entries created correctly

## Support

If you still see errors after applying fix:
1. Check which account is missing from error message
2. Verify account exists: `Account.objects.filter(code='XXXX')`
3. Check account mapping in `finance/services.py` DEFAULT_ACCOUNTS
4. Consult `docs/AR_POSTING_ACCOUNT_CONFLICT.md` for detailed analysis

# Corporate Tax Accrual Error Fix - Complete Resolution

## Date: October 17, 2025

## Issue Summary
When attempting to create a corporate tax accrual, users encountered two errors:
1. **First Error**: Missing required fields (country, date_from, date_to)
2. **Second Error**: ValueError - Account lookup failed for TAX_CORP_PAYABLE

## Root Causes

### 1. Frontend-Backend Field Mismatch
**Problem**: Frontend form was missing the `country` field and used different field names than the backend expected.

**Frontend sent**:
- `period_start`
- `period_end`
- `tax_rate`

**Backend expected**:
- `country` ✗ (missing)
- `date_from` ✗ (wrong name)
- `date_to` ✗ (wrong name)

### 2. Incorrect Account Code Mapping
**Problem**: The services.py file was configured to look for account code `2400` for TAX_CORP_PAYABLE, but the actual database had account code `2220`.

**Service configuration** (before fix):
```python
"TAX_CORP_PAYABLE": "2400"  # ✗ Wrong code
```

**Actual database**:
```
2220 - Corporate Tax Payable (LI)  # ✓ Correct code
```

### 3. Missing Corporate Tax Rules
**Problem**: No CorporateTaxRule records existed in the database, which are required to determine the tax rate for each country.

## Complete Fix Applied

### Fix #1: Frontend Form - Added Country Field
**File**: `frontend/src/app/tax/corporate/page.tsx`

1. **Updated state** to include country:
```typescript
const [accrualForm, setAccrualForm] = useState({
  country: 'AE',        // ✅ Added - defaults to UAE
  period_start: '',
  period_end: '',
  tax_rate: '9',
});
```

2. **Added country dropdown** to the form:
```tsx
<select
  value={accrualForm.country}
  onChange={(e) => setAccrualForm({ ...accrualForm, country: e.target.value })}
  required
>
  <option value="AE">UAE</option>
  <option value="SA">KSA</option>
  <option value="EG">Egypt</option>
  <option value="IN">India</option>
</select>
```

3. **Updated form reset** to preserve country:
```typescript
setAccrualForm({ 
  country: accrualForm.country,
  period_start: '', 
  period_end: '', 
  tax_rate: '9' 
});
```

### Fix #2: API Service - Field Name Mapping
**File**: `frontend/src/services/api.ts`

Updated the API call to map frontend field names to backend expectations:
```typescript
accrual: (data: { country: string; period_start: string; period_end: string; tax_rate: string }) => 
  api.post('/tax/corporate-accrual/', {
    country: data.country,           // ✅ Pass through
    date_from: data.period_start,    // ✅ Map period_start → date_from
    date_to: data.period_end         // ✅ Map period_end → date_to
  }),
```

### Fix #3: Backend Account Code Correction
**File**: `finance/services.py`

Corrected the account code to match the database:
```python
# Before:
"TAX_CORP_PAYABLE": "2400",  # ✗ Wrong

# After:
"TAX_CORP_PAYABLE": "2220",  # ✅ Correct - matches database
```

### Fix #4: Created Corporate Tax Rules
**Script**: `setup_tax_rules.py`

Created tax rules for all supported countries:
```
UAE (AE):    9.0%
KSA (SA):    20.0%
Egypt (EG):  22.5%
India (IN):  30.0%
```

## Verification

### 1. Account Verification
```bash
C:/Users/samys/FinanceERP/venv/Scripts/python.exe test_tax_accounts.py
```
**Result**: ✅ Both accounts (TAX_CORP_EXP and TAX_CORP_PAYABLE) found correctly

### 2. Tax Rules Verification
```bash
C:/Users/samys/FinanceERP/venv/Scripts/python.exe setup_tax_rules.py
```
**Result**: ✅ All 4 country tax rules created

### 3. Database State
**Accounts**:
- `6900` - Corporate Tax Expense (EX) ✅
- `2220` - Corporate Tax Payable (LI) ✅

**Tax Rules**:
- AE: 9% ✅
- SA: 20% ✅
- EG: 22.5% ✅
- IN: 30% ✅

## Expected Behavior After Fix

When users now access the Corporate Tax Accrual page:

1. **Form displays** with 4 fields:
   - Country dropdown (AE/SA/EG/IN)
   - Period Start Date
   - Period End Date
   - Tax Rate (informational, not used by backend)

2. **On submission**, the form:
   - Collects all required data
   - Maps field names correctly
   - Sends to backend: `POST /api/tax/corporate-accrual/`

3. **Backend processes**:
   - Validates country, date_from, date_to
   - Looks up tax rule for the country
   - Calculates profit from journal entries in the period
   - Applies tax rate from the rule
   - Creates journal entry: DR Tax Expense (6900), CR Tax Payable (2220)
   - Creates CorporateTaxFiling record with ACCRUED status
   - Returns success with filing details

4. **User receives**:
   - Success alert with taxable income and tax amount
   - Journal entry number created
   - Form resets (preserving country selection)

## Testing Checklist

- [✅] Frontend displays country dropdown
- [✅] All required fields present in form
- [✅] API service maps fields correctly
- [✅] Backend account codes are correct
- [✅] Corporate tax rules exist for all countries
- [✅] No TypeScript/compilation errors
- [ ] Manual test: Create tax accrual for UAE Q1 2025
- [ ] Verify journal entry created with correct accounts
- [ ] Verify CorporateTaxFiling record created with ACCRUED status

## Files Modified

1. `frontend/src/app/tax/corporate/page.tsx` - Added country field and dropdown
2. `frontend/src/services/api.ts` - Added field name mapping
3. `finance/services.py` - Fixed TAX_CORP_PAYABLE account code (2400 → 2220)
4. Database - Added 4 CorporateTaxRule records

## Files Created

1. `docs/TAX_ACCRUAL_FIELD_FIX.md` - Initial fix documentation
2. `docs/TAX_ACCRUAL_COMPLETE_FIX.md` - This comprehensive documentation
3. `check_accounts.py` - Script to verify accounts exist
4. `test_tax_accounts.py` - Script to test _acct() function
5. `setup_tax_rules.py` - Script to create/verify tax rules

## Backend API Reference

**Endpoint**: `POST /api/tax/corporate-accrual/`

**Request**:
```json
{
  "country": "AE",
  "date_from": "2025-01-01",
  "date_to": "2025-03-31"
}
```

**Response** (Success):
```json
{
  "created": true,
  "filing_id": 1,
  "journal": {
    "id": 123,
    "date": "2025-03-31",
    "memo": "Corporate tax accrual AE 2025-01-01..2025-03-31 on profit 100000.00",
    "posted": true
  },
  "meta": {
    "profit": 100000.00,
    "tax_base": 100000.00,
    "tax": 9000.00
  }
}
```

## Notes

- The `tax_rate` field in the frontend form is currently NOT used by the backend
- The backend determines the tax rate from CorporateTaxRule based on country
- Consider removing or making the tax_rate field read-only/informational
- Future enhancement: Auto-populate tax rate based on selected country

## Related Files

- Backend API: `finance/api.py` → `CorporateTaxAccrual` class
- Backend Service: `finance/services.py` → `accrue_corporate_tax_with_filing()`
- Backend Serializer: `finance/serializers.py` → `CorpTaxAccrualRequestSerializer`
- Backend Model: `finance/models.py` → `CorporateTaxFiling`, `CorporateTaxRule`
- Frontend Page: `frontend/src/app/tax/corporate/page.tsx`
- Frontend API: `frontend/src/services/api.ts`

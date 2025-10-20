# Tax Accrual Field Mapping Fix

## Issue
When attempting to create a corporate tax accrual, the following error occurred:
```
Failed to create accrual: {
  "country":["This field is required."],
  "date_from":["This field is required."],
  "date_to":["This field is required."]
}
```

## Root Cause
There was a mismatch between the frontend form fields and the backend API expectations:

### Frontend (Before Fix)
- Sent: `period_start`, `period_end`, `tax_rate`
- Missing: `country` field

### Backend Requirements
- Expected: `country`, `date_from`, `date_to`
- Defined in: `finance/serializers.py` → `CorpTaxAccrualRequestSerializer`

```python
class CorpTaxAccrualRequestSerializer(serializers.Serializer):
    country = serializers.ChoiceField(choices=[("AE","UAE"),("SA","KSA"),("EG","Egypt"),("IN","India")])
    date_from = serializers.DateField()
    date_to = serializers.DateField()
```

## Solution Applied

### 1. Updated Frontend Form State
**File**: `frontend/src/app/tax/corporate/page.tsx`

Added `country` field to the accrual form state:
```typescript
const [accrualForm, setAccrualForm] = useState({
  country: 'AE',           // ✅ Added - defaults to UAE
  period_start: '',
  period_end: '',
  tax_rate: '9',
});
```

### 2. Added Country Dropdown to UI
**File**: `frontend/src/app/tax/corporate/page.tsx`

Added a country selection dropdown in the form (changed grid from 3 columns to 4):
```tsx
<select
  value={accrualForm.country}
  onChange={(e) => setAccrualForm({ ...accrualForm, country: e.target.value })}
  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
  required
>
  <option value="AE">UAE</option>
  <option value="SA">KSA</option>
  <option value="EG">Egypt</option>
  <option value="IN">India</option>
</select>
```

### 3. Updated API Field Mapping
**File**: `frontend/src/services/api.ts`

Modified the API call to map frontend field names to backend expectations:
```typescript
accrual: (data: { country: string; period_start: string; period_end: string; tax_rate: string }) => 
  api.post('/tax/corporate-accrual/', {
    country: data.country,           // ✅ Pass through
    date_from: data.period_start,    // ✅ Map period_start → date_from
    date_to: data.period_end         // ✅ Map period_end → date_to
  }),
```

### 4. Updated Form Reset Logic
**File**: `frontend/src/app/tax/corporate/page.tsx`

Updated the form reset after successful submission to include country:
```typescript
setAccrualForm({ 
  country: accrualForm.country,  // ✅ Preserve country selection
  period_start: '', 
  period_end: '', 
  tax_rate: '9' 
});
```

## Testing
After these changes, the tax accrual form should:
1. ✅ Display a country dropdown (defaults to UAE)
2. ✅ Collect all required fields: country, period dates
3. ✅ Map field names correctly when sending to backend
4. ✅ Successfully create tax accrual without field validation errors

## Files Modified
1. `frontend/src/app/tax/corporate/page.tsx` - Added country field to form and state
2. `frontend/src/services/api.ts` - Added field name mapping

## Backend Reference
- API Endpoint: `POST /api/corporate-tax/accrual/`
- View: `finance/api.py` → `CorporateTaxAccrual.post()`
- Serializer: `finance/serializers.py` → `CorpTaxAccrualRequestSerializer`

## Notes
- The `tax_rate` field from the frontend is not currently used by the backend
- The backend determines tax rate based on the country and period
- Future enhancement could remove unused `tax_rate` from frontend or use it to override backend calculation

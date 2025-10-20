# Payment Pages Field Name Mismatch Fix

## Problem
The AR and AP payment list pages were using incorrect field names that didn't match the API response, causing the display to show undefined or incorrect values.

## Root Cause
The frontend payment list pages were using old/incorrect field names that didn't align with the actual API response structure:

### Frontend was using (WRONG):
- `payment.payment_date` ❌
- `payment.amount` ❌
- `payment.reference_number` ❌
- `payment.status` ❌

### API actually returns (CORRECT):
- `payment.date` ✅
- `payment.total_amount` ✅
- `payment.reference` ✅
- `payment.posted_at` ✅ (used to determine status)

## Solution

### Fixed AP Payments Page
**File**: `frontend/src/app/ap/payments/page.tsx`

**Changes**:
1. `payment.payment_date` → `payment.date`
2. `payment.amount` → `payment.total_amount`
3. `payment.reference_number` → `payment.reference`
4. `payment.status === 'POSTED'` → `payment.posted_at` (check if truthy)
5. `payment.status === 'DRAFT'` → `!payment.posted_at` (check if falsy)
6. Display logic: `{payment.posted_at ? 'POSTED' : 'DRAFT'}`

**Before**:
```tsx
<td className="table-td">
  {payment.payment_date 
    ? format(new Date(payment.payment_date), 'MMM dd, yyyy')
    : '-'
  }
</td>
<td className="table-td">{payment.supplier_name || `Supplier #${payment.supplier}`}</td>
<td className="table-td font-medium">${payment.amount}</td>
<td className="table-td">{payment.reference_number || '-'}</td>
<td className="table-td">
  <span className={`... ${payment.status === 'POSTED' ? '...' : '...'}`}>
    {payment.status}
  </span>
</td>
```

**After**:
```tsx
<td className="table-td">
  {payment.date 
    ? format(new Date(payment.date), 'MMM dd, yyyy')
    : '-'
  }
</td>
<td className="table-td">{payment.supplier_name || `Supplier #${payment.supplier}`}</td>
<td className="table-td font-medium">${payment.total_amount}</td>
<td className="table-td">{payment.reference || '-'}</td>
<td className="table-td">
  <span className={`... ${payment.posted_at ? '...' : '...'}`}>
    {payment.posted_at ? 'POSTED' : 'DRAFT'}
  </span>
</td>
```

### Fixed AR Payments Page
**File**: `frontend/src/app/ar/payments/page.tsx`

**Changes**: Identical to AP payments page fix
1. `payment.payment_date` → `payment.date`
2. `payment.amount` → `payment.total_amount`
3. `payment.reference_number` → `payment.reference`
4. `payment.status === 'POSTED'` → `payment.posted_at`
5. `payment.status === 'DRAFT'` → `!payment.posted_at`

## Type Definitions (Already Correct)
The TypeScript interfaces in `frontend/src/types/index.ts` were already correct:

```typescript
export interface ARPayment {
  id?: number;
  customer: number;
  customer_name?: string;
  reference: string;  // ✅ Correct
  date: string;       // ✅ Correct
  total_amount: string; // ✅ Correct
  currency: number;
  currency_code?: string;
  memo?: string;
  bank_account?: number;
  posted_at?: string;  // ✅ Correct (no 'status' field)
  // ... other fields
}

export interface APPayment {
  id?: number;
  supplier: number;
  supplier_name?: string;
  reference: string;  // ✅ Correct
  date: string;       // ✅ Correct
  total_amount: string; // ✅ Correct
  currency: number;
  currency_code?: string;
  memo?: string;
  bank_account?: number;
  posted_at?: string;  // ✅ Correct (no 'status' field)
  // ... other fields
}
```

## API Response Structure
**Actual API Response** from `/api/ar/payments/` and `/api/ap/payments/`:
```json
{
  "id": 1,
  "supplier": 1,
  "supplier_name": "Stationery LLC",
  "reference": "PMT-AP-1",
  "date": "2025-10-06",
  "total_amount": "33.39",
  "currency": 1,
  "currency_code": "USD",
  "memo": "",
  "bank_account": 1,
  "posted_at": "2025-10-06T07:48:40.047120-05:00",
  "reconciled": true,
  "reconciliation_ref": "STATEMENT-091",
  "reconciled_at": "2025-10-07",
  "gl_journal": 6,
  "payment_fx_rate": null,
  "allocations": "",
  "allocated_amount": 33.39,
  "unallocated_amount": 0.0
}
```

## Why This Caused Issues

### Before Fix:
- **Date Column**: Showed `-` because `payment.payment_date` was undefined
- **Amount Column**: Showed `$undefined` because `payment.amount` was undefined
- **Reference Column**: Showed `-` because `payment.reference_number` was undefined
- **Status Column**: Showed blank because `payment.status` was undefined
- **Actions Column**: Buttons always showed because `payment.status === 'DRAFT'` was always false (undefined !== 'DRAFT')

### After Fix:
- **Date Column**: Shows actual date like "Oct 06, 2025"
- **Amount Column**: Shows actual amount like "$33.39"
- **Reference Column**: Shows actual reference like "PMT-AP-1"
- **Status Column**: Shows "POSTED" or "DRAFT" based on `posted_at`
- **Actions Column**: Post/Delete buttons only show for draft payments (when `posted_at` is null)

## Impact
This fix ensures:
- ✅ Payment dates display correctly
- ✅ Payment amounts display correctly
- ✅ Payment references display correctly
- ✅ Payment status displays correctly (POSTED/DRAFT)
- ✅ Action buttons (Post/Delete) only show for draft payments
- ✅ No more duplicate or phantom records appearing in the frontend
- ✅ Data consistency between API and frontend display

## Testing
Verified with:
- Database: 3 AP payments
- API: Returns 3 AP payments with correct data
- Frontend: Now displays 3 AP payments with all fields showing correctly

---

**Date**: October 15, 2025
**Fixed By**: GitHub Copilot
**Files Modified**: 
- `frontend/src/app/ar/payments/page.tsx`
- `frontend/src/app/ap/payments/page.tsx`
**Related Issue**: Field name mismatch between frontend and API

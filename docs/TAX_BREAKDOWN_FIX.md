# Tax Breakdown API Mismatch Fix

## Date: October 17, 2025

## Issue
When clicking on the "Tax Breakdown" tab and loading breakdown data, the following error occurred:
```
TypeError: Cannot read properties of undefined (reading 'length')
at breakdown.filings.length
```

## Root Cause
The frontend and backend had a **complete API contract mismatch** for the breakdown endpoint:

### Frontend Expected (Before Fix)
```typescript
interface TaxBreakdown {
  period_start: string;
  period_end: string;
  revenue: string;
  expenses: string;
  net_income: string;
  taxable_income: string;
  tax_rate: string;
  tax_amount: string;
  filings: TaxFiling[];  // ❌ Backend doesn't return this
}
```

### Backend Actually Returns
```python
{
  "meta": {
    "country": "AE",
    "date_from": "2025-01-01",
    "date_to": "2025-12-31",
    "org_id": null,
    "income": 100000.00,
    "expense": 50000.00,
    "profit": 50000.00
  },
  "rows": [
    {
      "date": "2025-01-15",
      "journal_id": 123,
      "account_code": "4000",
      "account_name": "Income",
      "type": "INCOME",
      "delta": 10000.00,
      "debit": 0.00,
      "credit": 10000.00
    }
    // ... more rows
  ],
  "download_links": {
    "xlsx": "/api/tax/corporate-breakdown/?file_type=xlsx&date_from=2025-01-01&date_to=2025-12-31",
    "csv": "/api/tax/corporate-breakdown/?file_type=csv&date_from=2025-01-01&date_to=2025-12-31"
  }
}
```

### Parameter Name Mismatch
- **Frontend sent**: `period_start`, `period_end`
- **Backend expected**: `date_from`, `date_to`

## Solution

### Fix #1: Updated TaxBreakdown Interface
**File**: `frontend/src/app/tax/corporate/page.tsx`

Changed the interface to match the actual backend response:
```typescript
interface TaxBreakdown {
  meta: {
    country?: string;
    date_from?: string;
    date_to?: string;
    org_id?: string;
    income: number;
    expense: number;
    profit: number;
  };
  rows: Array<{
    date: string;
    journal_id: number;
    account_code: string;
    account_name: string;
    type: string;
    delta: number;
    debit: number;
    credit: number;
  }>;
  download_links: {
    xlsx: string;
    csv: string;
  };
}
```

### Fix #2: Updated Summary Cards
Changed from 4 cards (Revenue, Expenses, Taxable Income, Tax Amount) to 3 cards matching the backend data:
```tsx
<div className="grid grid-cols-3 gap-4 mb-6">
  <div>Income: {breakdown.meta.income}</div>
  <div>Expenses: {breakdown.meta.expense}</div>
  <div>Net Profit: {breakdown.meta.profit}</div>
</div>
```

### Fix #3: Replaced Filings Table with Transaction Details Table
The backend doesn't return filings in the breakdown response. Instead, it returns detailed transaction rows. Created a new table to display:
- Date
- Journal ID
- Account (code and name)
- Type (INCOME/EXPENSE/OTHER)
- Debit
- Credit
- Delta

Added download buttons for CSV and Excel exports using the provided download links.

### Fix #4: Fixed API Parameter Mapping
**File**: `frontend/src/services/api.ts`

Updated the breakdown API call to map parameter names correctly:
```typescript
breakdown: (params?: { period_start?: string; period_end?: string }) => 
  api.get('/tax/corporate-breakdown/', { 
    params: {
      date_from: params?.period_start,  // ✅ Map to backend param name
      date_to: params?.period_end        // ✅ Map to backend param name
    }
  }),
```

## What the Breakdown Now Shows

### Summary Section (3 Cards)
1. **Income** - Total income from all INCOME account types
2. **Expenses** - Total expenses from all EXPENSE account types  
3. **Net Profit** - Income minus Expenses

### Transaction Details Table
Shows all journal line transactions in the period with:
- Transaction date
- Journal entry ID (clickable)
- Account code and name
- Type badge (INCOME/EXPENSE/OTHER) with color coding
- Debit amount
- Credit amount
- Delta (net effect) with color (green for positive, red for negative)

### Download Options
- **CSV Export** - Excel-friendly CSV with BOM
- **Excel Export** - Native .xlsx format

## Files Modified

1. ✅ `frontend/src/app/tax/corporate/page.tsx`
   - Updated `TaxBreakdown` interface
   - Changed summary cards (4 → 3)
   - Replaced filings table with transaction details table
   - Added download buttons

2. ✅ `frontend/src/services/api.ts`
   - Fixed parameter name mapping (period_start/end → date_from/to)

## Backend API Reference

**Endpoint**: `GET /api/tax/corporate-breakdown/`

**Query Parameters**:
- `date_from` (optional) - Start date (YYYY-MM-DD)
- `date_to` (optional) - End date (YYYY-MM-DD)
- `country` (optional) - Country code
- `org_id` (optional) - Organization ID
- `file_type` (optional) - `csv` or `xlsx` for download

**Response Structure**:
```json
{
  "meta": {
    "country": "AE",
    "date_from": "2025-01-01",
    "date_to": "2025-12-31",
    "org_id": null,
    "income": 100000.00,
    "expense": 50000.00,
    "profit": 50000.00
  },
  "rows": [/* transaction details */],
  "download_links": {
    "xlsx": "url",
    "csv": "url"
  }
}
```

## Testing

The breakdown tab should now:
1. ✅ Load without errors
2. ✅ Display 3 summary cards (Income, Expenses, Net Profit)
3. ✅ Show detailed transaction table
4. ✅ Provide CSV and Excel download buttons
5. ✅ Color-code transaction types and deltas
6. ✅ Handle empty results gracefully

## Notes

- The breakdown is a **reporting tool** that analyzes existing journal entries
- It does NOT create or manage tax filings (use the "Accrual" tab for that)
- The transaction table is scrollable and can handle large datasets
- Download exports include summary totals at the bottom
- The breakdown recalculates dynamically based on the selected date range

## Related Documentation

- Backend Implementation: `finance/api.py` → `CorporateTaxBreakdown` class (lines 1188-1292)
- Original breakdown logic in `finance/services.py` → `accrue_corporate_tax()` function

# AP Payment Form Fix

## Date: October 13, 2025

## Applied Same Fixes as AR Payment

The AP Payment form has been updated with the same fixes that were applied to the AR Payment form.

## Changes Made:

### 1. **Added Supplier Dropdown** ✅
- Changed from manual "Supplier ID" input to dropdown
- Loads all suppliers from `suppliersAPI.list()`
- Shows supplier name instead of just ID

### 2. **Added Invoice Dropdown** ✅
- Automatically loads when supplier is selected
- Shows **only POSTED invoices** for the selected supplier
- Shows **only invoices with balance > 0**
- Displays: Invoice Number - Date - Balance Due
- Example: "INV-001 - 2025-10-13 - Balance: 1050.00"

### 3. **Fixed Field Mapping** ✅
Changed from incorrect fields:
```typescript
// OLD (WRONG)
{
  supplier: parseInt(formData.supplier),
  payment_date: formData.payment_date,  // ❌ Wrong field name
  amount: formData.amount,
  currency: parseInt(formData.currency),  // ❌ Not in model
  reference_number: formData.reference_number,  // ❌ Not in model
  memo: formData.memo,  // ❌ Not in model
  bank_account: formData.bank_account,
  invoice: formData.invoice,
}
```

To correct fields:
```typescript
// NEW (CORRECT)
{
  invoice: parseInt(formData.invoice),    // Required FK
  date: formData.payment_date,            // Changed from payment_date
  amount: formData.amount,                // Keep as string
  bank_account: formData.bank_account,    // Optional
}
```

### 4. **Auto-Fill Amount** ✅
- When invoice is selected, amount auto-fills with invoice balance
- User can still manually adjust if paying partial amount
- Uses `selectedInvoice.balance || ''` to handle optional field

### 5. **Made Invoice Required** ✅
- Added `required` attribute to invoice select
- Added validation before submission
- Shows error if trying to submit without selecting invoice

### 6. **Improved Error Handling** ✅
- Checks for both `detail` and `error` fields in response
- Shows specific error messages from backend
- Added console logging for debugging

### 7. **Removed Unnecessary Fields** ✅
Removed fields that don't exist in APPayment model:
- ❌ Currency (invoice already has currency)
- ❌ Reference Number (not in model)
- ❌ Memo (not in model)

Kept only required/optional fields:
- ✅ Supplier (for filtering invoices)
- ✅ Invoice (required)
- ✅ Date (required)
- ✅ Amount (required)
- ✅ Bank Account (optional)

### 8. **Fixed Type Imports** ✅
- Import `APInvoice` from `types/index.ts`
- Import `Supplier` from `types/index.ts`
- No duplicate type definitions

## APPayment Model (Backend):
```python
class APPayment(models.Model):
    invoice = models.ForeignKey(APInvoice, ...)         # REQUIRED
    date = models.DateField()                            # REQUIRED
    amount = models.DecimalField(...)                    # REQUIRED
    bank_account = models.ForeignKey(BankAccount, ...)  # Optional
    posted_at = models.DateTimeField(...)                # Auto
    reconciled = models.BooleanField(...)                # Auto
    reconciliation_ref = models.CharField(...)           # Auto
    reconciled_at = models.DateField(...)                # Auto
    gl_journal = models.ForeignKey(JournalEntry, ...)   # Auto
    payment_fx_rate = models.DecimalField(...)           # Optional
```

## How to Use the Fixed Form:

1. **Select Supplier** → Dropdown loads all suppliers
2. **Invoice Dropdown Loads** → Shows only that supplier's posted invoices with balance > 0
3. **Select Invoice** → Amount auto-fills with invoice balance
4. **Adjust Amount** (if partial payment)
5. **Select Payment Date** (defaults to today)
6. **Select Bank Account** (optional)
7. **Click "Create Payment"**

## What Happens on Backend:
1. Creates APPayment record
2. Automatically posts to GL (creates journal entry)
3. Updates invoice paid_amount and balance
4. If full payment, marks invoice as closed
5. Returns journal entry details

## Invoice Filtering Logic:
```typescript
const supplierInvoices = response.data.filter(
  (inv) => 
    inv.supplier === supplierId &&      // Only this supplier
    inv.status === 'POSTED' &&          // Only posted invoices
    parseFloat(inv.balance || '0') > 0  // Only with outstanding balance
);
```

## Expected Backend Response:
```json
{
  "journal": {
    "id": 456,
    "date": "2025-10-13",
    "posted": true,
    "lines": [
      {"account_code": "2000", "debit": 0, "credit": 1050},
      {"account_code": "1000", "debit": 1050, "credit": 0}
    ]
  },
  "already_posted": false,
  "invoice_closed": true
}
```

## Files Modified:
- `frontend/src/app/ap/payments/new/page.tsx`
  - Added supplier dropdown
  - Added invoice dropdown with filtering
  - Fixed field mapping to match backend
  - Made invoice required
  - Added auto-fill amount feature
  - Improved error handling
  - Removed unnecessary fields

## Testing:
✅ TypeScript compiles with no errors
✅ Supplier dropdown loads correctly
✅ Invoice dropdown filters by supplier
✅ Amount auto-fills from invoice balance
✅ Payment submission sends correct fields
✅ Backend validation works correctly

## Comparison: AR vs AP Payments

Both forms now work identically:

| Feature | AR Payment | AP Payment |
|---------|-----------|-----------|
| Customer/Supplier Dropdown | ✅ | ✅ |
| Invoice Dropdown (Filtered) | ✅ | ✅ |
| Auto-fill Amount | ✅ | ✅ |
| Required Invoice | ✅ | ✅ |
| Correct Field Names | ✅ | ✅ |
| Error Handling | ✅ | ✅ |
| Type Safety | ✅ | ✅ |

## Notes:
- Both AR and AP payment forms now use the same pattern
- Backend automatically posts to GL (no manual "Post" button needed)
- Payment cannot exceed invoice balance (backend validation)
- Invoice must be POSTED before accepting payment (backend validation)
- Supplier/Customer field only used to filter invoices (not sent to backend)

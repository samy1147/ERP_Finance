# AR Payment Form Fix

## Date: October 13, 2025

## Problems Identified:

### 1. **Wrong Field Names**
The frontend was sending field names that don't match the backend model:
- ❌ Sending `payment_date` → Backend expects `date`
- ❌ Sending `customer` → Not needed (invoice already has customer)
- ❌ Sending `currency` → Not needed (invoice already has currency)
- ❌ Sending `reference_number` → Field doesn't exist in ARPayment model
- ❌ Sending `memo` → Field doesn't exist in ARPayment model

### 2. **Invoice Not Filtered by Customer**
The invoice dropdown was showing ALL posted invoices instead of just the selected customer's invoices.

### 3. **Invoice Field Was Optional**
The backend requires an invoice, but the form allowed submission without selecting one.

### 4. **Type Compatibility Issues**
Local type definitions conflicted with the global types from `types/index.ts`.

## Solutions Implemented:

### 1. **Fixed Field Mapping** ✅
Updated `handleSubmit` to send only the fields that the ARPayment model expects:
```typescript
const paymentData = {
  invoice: parseInt(formData.invoice),      // Required FK
  date: formData.payment_date,              // Changed from payment_date
  amount: formData.amount,                  // Keep as string
  bank_account: formData.bank_account ? parseInt(formData.bank_account) : undefined,
};
```

### 2. **Fixed Invoice Filtering** ✅
Added customer ID check to filter:
```typescript
const customerInvoices = response.data.filter(
  (inv) => 
    inv.customer === customerId &&          // ← ADDED THIS
    inv.status === 'POSTED' && 
    parseFloat(inv.balance || '0') > 0
);
```

### 3. **Made Invoice Required** ✅
- Added `required` attribute to invoice select field
- Added validation to check invoice is selected before submission
- Changed label from "Invoice (Optional)" to "Invoice *"

### 4. **Fixed Type Compatibility** ✅
- Removed duplicate local type definitions for `Customer` and `ARInvoice`
- Import types from `types/index.ts` instead
- Fixed `balance` field handling (optional string with fallback)

### 5. **Improved Error Handling** ✅
- Check for `detail` and `error` fields in backend response
- Show specific error messages from backend
- Added console logging for debugging

### 6. **Removed Unnecessary Fields** ✅
- Removed "Reference Number" field (not in model)
- Removed "Memo" field (not in model)
- Kept only: Customer, Payment Date, Amount, Bank Account, Invoice

## ARPayment Model Fields:
```python
class ARPayment(models.Model):
    invoice = models.ForeignKey(ARInvoice, ...)         # REQUIRED
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

1. **Select Customer** → Dropdown loads all customers
2. **Invoice Dropdown Loads** → Shows only that customer's posted invoices with balance > 0
3. **Select Invoice** → Amount auto-fills with invoice balance
4. **Adjust Amount** (if partial payment)
5. **Select Payment Date** (defaults to today)
6. **Select Bank Account** (optional)
7. **Click "Create Payment"**

## What Happens on Backend:
1. Creates ARPayment record
2. Automatically posts to GL (creates journal entry)
3. Updates invoice paid_amount and balance
4. If full payment, marks invoice as closed
5. Returns journal entry details

## Expected Response:
```json
{
  "journal": {
    "id": 123,
    "date": "2025-10-13",
    "posted": true,
    "lines": [...]
  },
  "already_posted": false,
  "invoice_closed": true
}
```

## Files Modified:
1. `frontend/src/app/ar/payments/new/page.tsx`
   - Fixed field mapping
   - Fixed invoice filtering
   - Made invoice required
   - Fixed type imports
   - Improved error handling

## Testing:
✅ TypeScript compiles with no errors
✅ Customer dropdown loads correctly
✅ Invoice dropdown filters by customer
✅ Amount auto-fills from invoice balance
✅ Payment submission sends correct fields
✅ Backend validation works correctly

## Notes:
- The backend automatically posts the payment to GL (no separate "Post" button needed)
- Payment cannot exceed invoice balance (backend validation)
- Invoice must be POSTED before accepting payment (backend validation)
- Customer field is only used to filter invoices (not sent to backend)

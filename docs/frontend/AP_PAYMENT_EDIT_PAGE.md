# AP Payment Edit Page Implementation

## Overview
Created a complete edit page for AP (Accounts Payable) payments that allows modifying draft payments and their invoice allocations to suppliers.

## File Created
**Path**: `frontend/src/app/ap/payments/[id]/edit/page.tsx`  
**Lines**: 550+ lines  
**Type**: Next.js 14 Dynamic Route Page (Edit Mode)

## Key Features

### 1. Payment Loading and Validation
- Loads existing payment data by ID from URL params
- Validates that payment is not yet posted (prevents editing posted payments)
- Redirects to payment list if payment is posted or not found
- Pre-fills all form fields with existing payment data

### 2. Supplier Locking
- Supplier field is **disabled** in edit mode (cannot change supplier)
- Reference field is **disabled** (auto-generated, cannot change)
- Rationale: Changing supplier would invalidate existing allocations

### 3. Invoice Allocation Management
- Loads outstanding invoices for the payment's supplier
- Pre-selects and pre-fills previously allocated invoices
- Shows:
  - Invoice numbers
  - Invoice totals
  - Outstanding balances
  - Current allocation amounts
- Allows adding new invoice allocations
- Allows removing existing allocations
- Allows modifying allocation amounts

### 4. Real-Time Calculations
```typescript
const calculateTotalAllocated = () => {
  return invoices
    .filter(inv => inv.selected)
    .reduce((sum, inv) => sum + parseFloat(inv.amount || '0'), 0);
};

const calculateUnallocated = () => {
  const total = parseFloat(formData.total_amount) || 0;
  const allocated = calculateTotalAllocated();
  return total - allocated;
};
```

### 5. Validation Rules
- Total payment amount must be positive
- At least one invoice must be allocated
- Individual allocations cannot exceed invoice outstanding balance
- Total allocations cannot exceed payment amount
- All allocation amounts must be positive

### 6. Allocation Summary Display
Three-column summary panel (blue background):
- **Total Payment Amount** (green) - The payment total
- **Total Allocated** (blue) - Sum of all selected allocations
- **Unallocated Amount** (red if > 0, green if = 0) - Remaining balance

### 7. User Actions
- **Select Invoice**: Checkbox to include/exclude invoice
- **Auto-Fill Amount**: When selected, auto-fills with outstanding balance
- **Manual Amount Entry**: Editable input for custom allocation
- **Clear All Allocations**: Button to deselect all invoices
- **Update Payment**: Submits changes via PATCH request
- **Cancel**: Returns to payment list without saving

## UI Structure

```
┌─────────────────────────────────────────────┐
│  Edit AP Payment                            │
│  Modify payment and allocations             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Payment Details Card                       │
│  ├─ Supplier (disabled)                     │
│  ├─ Payment Date                            │
│  ├─ Total Amount                            │
│  ├─ Currency                                │
│  ├─ Reference (disabled)                    │
│  ├─ Bank Account                            │
│  └─ Memo                                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Allocation Summary (Blue Card)             │
│  ├─ Total Payment: $1,000.00 (green)        │
│  ├─ Total Allocated: $800.00 (blue)         │
│  └─ Unallocated: $200.00 (red/green)        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Invoice Allocations Table                  │
│  [Clear All Allocations]                    │
│  ┌─────────────────────────────────────────┐│
│  │ [✓] INV-001 | $500 | $300 | [$300.00] ││
│  │ [ ] INV-002 | $800 | $800 | [$0.00]   ││
│  │ [✓] INV-003 | $600 | $500 | [$500.00] ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘

                    [Cancel] [Update Payment]
```

## Integration with Payment List Page

### Added Edit Button
**File**: `frontend/src/app/ap/payments/page.tsx`

**Changes**:
1. Added `Edit2` icon import
2. Added Edit button in Actions column (before Post button)
3. Only shows for draft (unposted) payments
4. Links to `/ap/payments/${payment.id}/edit`

**Button Display Logic**:
```tsx
{!payment.posted_at && (
  <Link
    href={`/ap/payments/${payment.id}/edit`}
    className="text-blue-600 hover:text-blue-900"
    title="Edit Payment"
  >
    <Edit2 className="h-4 w-4" />
  </Link>
)}
```

## API Integration

### Used Endpoints
1. **GET** `/api/ap/payments/{id}/` - Load payment data
2. **GET** `/api/outstanding-invoices/ap/?supplier={id}` - Load outstanding invoices
3. **PATCH** `/api/ap/payments/{id}/` - Update payment
4. **GET** `/api/suppliers/` - Supplier dropdown
5. **GET** `/api/currencies/` - Currency dropdown
6. **GET** `/api/bank-accounts/` - Bank account dropdown

### Update Payload
```json
{
  "supplier": 1,
  "date": "2025-10-15",
  "total_amount": "1000.00",
  "currency": 1,
  "reference": "PMT-AP-123",
  "memo": "Payment memo",
  "bank_account": 1,
  "allocations": [
    {
      "invoice": 5,
      "amount": "300.00"
    },
    {
      "invoice": 7,
      "amount": "500.00"
    }
  ]
}
```

## State Management

### Form State
```typescript
const [formData, setFormData] = useState({
  supplier: '',
  date: '',
  total_amount: '',
  currency: '1',
  reference: '',
  memo: '',
  bank_account: '',
});
```

### Invoice Allocations State
```typescript
interface InvoiceAllocation {
  invoice: number;
  invoiceNumber: string;
  invoiceTotal: string;
  outstanding: string;
  amount: string;
  selected: boolean;
}

const [invoices, setInvoices] = useState<InvoiceAllocation[]>([]);
```

### Loading States
- `loadingData` - Initial payment load
- `loadingInvoices` - Outstanding invoices load
- `loading` - Form submission

## Differences from AR Payment Edit Page

The AP payment edit page mirrors the AR version with these key differences:

1. **Entity References**:
   - `customer` → `supplier`
   - `customersAPI` → `suppliersAPI`
   - `outstandingInvoicesAPI.getByCustomer()` → `outstandingInvoicesAPI.getBySupplier()`
   - `arPaymentsAPI` → `apPaymentsAPI`

2. **UI Labels**:
   - "Customer" → "Supplier"
   - "Edit AR Payment" → "Edit AP Payment"
   - "customer invoices" → "supplier invoices"

3. **Routes**:
   - `/ar/payments` → `/ap/payments`

4. **Type Imports**:
   - `Customer` → `Supplier`
   - `ARPayment` → `APPayment`

## Security & Validation

### Edit Restrictions
1. **Posted Payments**: Cannot be edited (redirects to list)
2. **Supplier Lock**: Cannot change supplier once payment created
3. **Reference Lock**: Cannot change auto-generated reference

### Business Rules Enforced
- ✅ Allocation amount ≤ Invoice outstanding balance
- ✅ Total allocations ≤ Payment amount
- ✅ Minimum one invoice allocation required
- ✅ All amounts must be positive

## User Experience Features

### Auto-Fill Behavior
When user selects an invoice checkbox:
- If amount is empty or $0.00, auto-fills with outstanding balance
- If amount already exists, preserves the value
- User can always override with custom amount

### Clear All Function
- Quickly deselects all invoices
- Resets all amounts to $0.00
- Useful for starting fresh allocation

### Loading States
- Shows "Loading payment..." during initial load
- Shows "Loading invoices..." while fetching outstanding invoices
- Disables submit button during processing
- Button text changes to "Updating..." during submission

### Error Handling
- Toast notifications for all errors
- Redirects if payment not found or already posted
- Validation messages for business rule violations
- Console logging for debugging

## Workflow Example

### Editing a Payment
1. User clicks Edit icon (blue pencil) on payment list
2. System loads payment data and outstanding invoices
3. Form pre-fills with existing values
4. Existing allocations are pre-selected and pre-filled
5. User can:
   - Change payment date
   - Change total amount
   - Change currency
   - Change bank account
   - Modify memo
   - Add new invoice allocations
   - Remove existing allocations
   - Adjust allocation amounts
6. Real-time summary updates as changes are made
7. User clicks "Update Payment"
8. System validates and saves changes
9. Success toast and redirect to payment list

## Testing Checklist

### Functionality
- [ ] Load existing payment data correctly
- [ ] Pre-select and pre-fill existing allocations
- [ ] Load outstanding invoices for supplier
- [ ] Allow adding new allocations
- [ ] Allow removing existing allocations
- [ ] Allow modifying allocation amounts
- [ ] Real-time calculation updates
- [ ] Validation prevents over-allocation
- [ ] Validation prevents negative amounts
- [ ] Validation requires at least one allocation
- [ ] Update API call with correct payload
- [ ] Success redirect to payment list
- [ ] Posted payment redirect protection

### UI/UX
- [ ] Supplier field disabled (locked)
- [ ] Reference field disabled (locked)
- [ ] Date picker works correctly
- [ ] Currency dropdown loads
- [ ] Bank account dropdown loads
- [ ] Invoice checkboxes toggle selection
- [ ] Amount inputs accept decimal values
- [ ] Clear All button works
- [ ] Loading states display properly
- [ ] Error toasts appear correctly
- [ ] Success toast on update
- [ ] Cancel button returns to list

## Related Files
- **AR Payment Edit**: `frontend/src/app/ar/payments/[id]/edit/page.tsx`
- **New Payment Page**: `frontend/src/app/ap/payments/new/page.tsx`
- **Payment List**: `frontend/src/app/ap/payments/page.tsx`
- **API Services**: `frontend/src/services/api.ts`
- **Type Definitions**: `frontend/src/types/index.ts`

---

**Status**: ✅ Complete and Ready for Testing  
**Date**: October 16, 2025  
**Next Steps**: 
1. Test both AR and AP payment edit functionality
2. Create invoice edit pages for AR and AP
3. Add edit buttons to invoice list pages

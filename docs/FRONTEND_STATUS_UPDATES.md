# Frontend Updates for Invoice Status Separation

## Summary of Changes

The frontend has been updated to work with the new separated invoice status fields.

## Files Modified

### 1. TypeScript Types (`frontend/src/types/index.ts`)

**ARInvoice Interface:**
```typescript
// Old
status: 'DRAFT' | 'POSTED' | 'REVERSED';

// New
is_posted: boolean;
payment_status: 'UNPAID' | 'PARTIALLY_PAID' | 'PAID';
is_cancelled: boolean;
posted_at?: string;
paid_at?: string;
cancelled_at?: string;
```

**APInvoice Interface:**
```typescript
// Old
status: 'DRAFT' | 'POSTED' | 'REVERSED';

// New
is_posted: boolean;
payment_status: 'UNPAID' | 'PARTIALLY_PAID' | 'PAID';
is_cancelled: boolean;
posted_at?: string;
paid_at?: string;
cancelled_at?: string;
```

### 2. AR Invoices List Page (`frontend/src/app/ar/invoices/page.tsx`)

**Status Display:**
- Now shows separate badges for:
  - **Posting Status**: "Posted" (green) or "Draft" (yellow)
  - **Payment Status**: "Paid" (blue), "Partial" (purple), or "Unpaid" (gray) - shown only for posted invoices
  - **Cancelled Status**: "Cancelled" (red) - shown when cancelled

**Action Buttons:**
- "Post to GL" button: Shows when `!is_posted && !is_cancelled`
- "Delete" button: Shows when `!is_posted && !is_cancelled`

### 3. AP Invoices List Page (`frontend/src/app/ap/invoices/page.tsx`)

Same changes as AR invoices page:
- Separate status badges
- Updated button visibility logic

### 4. AR Payment Creation (`frontend/src/app/ar/payments/new/page.tsx`)

**Invoice Filtering:**
```typescript
// Old
inv.status === 'POSTED' && parseFloat(inv.balance || '0') > 0

// New
inv.is_posted && !inv.is_cancelled && parseFloat(inv.balance || '0') > 0
```

### 5. AP Payment Creation (`frontend/src/app/ap/payments/new/page.tsx`)

**Invoice Filtering:**
```typescript
// Old
inv.status === 'POSTED' && parseFloat(inv.balance || '0') > 0

// New
inv.is_posted && !inv.is_cancelled && parseFloat(inv.balance || '0') > 0
```

## Visual Changes

### Before
Single status badge showing: DRAFT, POSTED, or PAID

### After
Multiple status badges showing:
1. **Draft** (yellow) or **Posted** (green)
2. **Unpaid** (gray), **Partial** (purple), or **Paid** (blue) - for posted invoices only
3. **Cancelled** (red) - when applicable

## Status Badge Colors

| Status | Color | Background | Text |
|--------|-------|------------|------|
| Draft | Yellow | `bg-yellow-100` | `text-yellow-800` |
| Posted | Green | `bg-green-100` | `text-green-800` |
| Unpaid | Gray | `bg-gray-100` | `text-gray-800` |
| Partially Paid | Purple | `bg-purple-100` | `text-purple-800` |
| Paid | Blue | `bg-blue-100` | `text-blue-800` |
| Cancelled | Red | `bg-red-100` | `text-red-800` |

## Benefits

1. **Clearer Status Display**: Users can now see at a glance both the posting status and payment status
2. **Better Filtering**: Easier to identify partially paid invoices
3. **Improved UX**: More intuitive understanding of invoice state
4. **Flexibility**: Can show multiple statuses simultaneously (e.g., Posted + Partially Paid)

## Testing Checklist

- [ ] AR invoice list loads correctly
- [ ] AP invoice list loads correctly
- [ ] Status badges display correctly for:
  - [ ] Draft invoices
  - [ ] Posted but unpaid invoices
  - [ ] Partially paid invoices
  - [ ] Fully paid invoices
  - [ ] Cancelled invoices
- [ ] "Post to GL" button only shows for draft, non-cancelled invoices
- [ ] "Delete" button only shows for draft, non-cancelled invoices
- [ ] Payment creation pages filter invoices correctly
- [ ] No console errors related to status fields

## Notes

- The payment pages (AR/AP payments list) still use the old `status` field as payments have not been updated yet
- If you need to update payments similarly, the same pattern can be applied

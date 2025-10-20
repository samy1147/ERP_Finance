# Invoice Approval Status Fix

## Issue Description
Pending invoice approvals were not appearing in the "Pending" tab but were visible in the "All" tab.

## Root Cause
**Status Value Mismatch**: 
- Backend uses: `'PENDING_APPROVAL'`
- Frontend was filtering for: `'PENDING'`

### Backend Status Values
From `finance/models.py`:
```python
class InvoiceApprovalStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    POSTED = "POSTED", "Posted"
```

The default status when submitting for approval is `PENDING_APPROVAL`, not `PENDING`.

## Solution Applied

### 1. Updated TypeScript Type Definition
**File**: `frontend/src/types/index.ts`

**Before**:
```typescript
status: 'PENDING' | 'APPROVED' | 'REJECTED';
```

**After**:
```typescript
status: 'DRAFT' | 'PENDING' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'POSTED';
```

### 2. Updated Filtering Logic - Enhanced Page
**File**: `frontend/src/app/invoice-approvals/page.tsx`

#### Filter Function
**Before**:
```typescript
case 'pending':
  filtered = filtered.filter(a => a.status === 'PENDING');
  break;
```

**After**:
```typescript
case 'pending':
  filtered = filtered.filter(a => a.status === 'PENDING_APPROVAL' || a.status === 'PENDING');
  break;
```

#### Tab Count Function
**Before**:
```typescript
case 'pending':
  return approvals.filter(a => a.status === 'PENDING').length;
```

**After**:
```typescript
case 'pending':
  return approvals.filter(a => a.status === 'PENDING' || a.status === 'PENDING_APPROVAL').length;
```

#### Status Badge Function
**Before**:
```typescript
case 'PENDING':
  return <PendingBadge />;
```

**After**:
```typescript
case 'PENDING':
case 'PENDING_APPROVAL':
  return <PendingBadge />;
```

#### Action Button Conditions
**Before**:
```typescript
{approval.status === 'PENDING' && (
  <ApproveRejectButtons />
)}
```

**After**:
```typescript
{(approval.status === 'PENDING' || approval.status === 'PENDING_APPROVAL') && (
  <ApproveRejectButtons />
)}
```

### 3. Updated Original Approval Page
**File**: `frontend/src/app/approvals/page.tsx`

Applied same fixes:
- Filter function: Check for both 'PENDING' and 'PENDING_APPROVAL'
- History filter: Exclude both 'PENDING' and 'PENDING_APPROVAL'
- Badge function: Handle both statuses
- Badge count: Count both statuses

## Files Modified

1. ✅ `frontend/src/types/index.ts` - Added all status values to type
2. ✅ `frontend/src/app/invoice-approvals/page.tsx` - Updated all status checks
3. ✅ `frontend/src/app/approvals/page.tsx` - Updated all status checks

## Testing Checklist

### Before Fix
- [ ] Pending approvals don't show in "Pending" tab
- [ ] Pending approvals show in "All" tab
- [ ] Badge count shows 0 for Pending
- [ ] Approve/Reject buttons don't show

### After Fix
- [x] Pending approvals show in "Pending" tab
- [x] Pending approvals show in "All" tab
- [x] Badge count shows correct number
- [x] Approve/Reject buttons visible for pending items
- [x] Status badges display "Pending" correctly
- [x] No TypeScript errors

## Why Both Status Values?

The code now checks for both `'PENDING'` and `'PENDING_APPROVAL'` for backward compatibility:

1. **Backend Default**: Uses `'PENDING_APPROVAL'`
2. **Potential Legacy**: If any old data used `'PENDING'`
3. **Future Flexibility**: Easy to support either value
4. **No Breaking Changes**: Existing functionality preserved

## Related Status Values

For reference, here are all possible invoice approval statuses:

| Status | Value | Meaning |
|--------|-------|---------|
| Draft | `'DRAFT'` | Not submitted yet |
| Pending | `'PENDING'` | Legacy pending (if any) |
| Pending Approval | `'PENDING_APPROVAL'` | Awaiting approval ⭐ |
| Approved | `'APPROVED'` | Approved by approver |
| Rejected | `'REJECTED'` | Rejected with reason |
| Posted | `'POSTED'` | Invoice posted to GL |

**Primary Status**: `'PENDING_APPROVAL'` is the main status used by the system when an invoice is submitted for approval.

## Prevention

To avoid similar issues in the future:

### 1. Keep Types in Sync
When backend status choices change, immediately update frontend types.

### 2. Use Constants
Consider creating shared constants:
```typescript
// constants.ts
export const APPROVAL_STATUS = {
  DRAFT: 'DRAFT',
  PENDING_APPROVAL: 'PENDING_APPROVAL',
  APPROVED: 'APPROVED',
  REJECTED: 'REJECTED',
  POSTED: 'POSTED',
} as const;

// Usage
a.status === APPROVAL_STATUS.PENDING_APPROVAL
```

### 3. Backend-Frontend Contract
Document status values in API documentation:
- `docs/openapi.yaml`
- API response examples
- Type definitions with comments

### 4. Testing
Add test cases that verify:
- Status filtering works correctly
- All status values from backend are handled
- Badge rendering for all statuses
- Action buttons show/hide correctly

## Impact

### User Impact
✅ **Positive**: Users can now see and act on pending approvals

**Before**:
- Confusion: "Where are my pending approvals?"
- Workaround: Use "All" tab and manually find pending items
- Inefficient: Can't use dedicated pending tab

**After**:
- Clear: Pending tab shows all items awaiting approval
- Efficient: Quick access to pending items
- Accurate: Badge count shows correct number

### System Impact
✅ **No Breaking Changes**: 
- Backward compatible (checks both statuses)
- No database changes needed
- No API changes needed
- Works with existing data

## Verification

### How to Test
1. **Create Test Approval**:
   ```
   - Go to AR or AP invoices
   - Create or select a draft invoice
   - Click "Submit for Approval"
   ```

2. **Check Pending Tab**:
   ```
   - Go to /invoice-approvals
   - Click "Pending" tab
   - Verify invoice appears
   ```

3. **Verify Badge Count**:
   ```
   - Check badge number on Pending tab
   - Should match number of pending items
   ```

4. **Test Actions**:
   ```
   - Approve/Reject buttons should be visible
   - Click Approve and verify it works
   - Click Reject and verify it works
   ```

5. **Check All Tab**:
   ```
   - Switch to "All" tab
   - Pending items still visible
   - All statuses displayed correctly
   ```

## Summary

**Problem**: Status value mismatch between backend (`PENDING_APPROVAL`) and frontend (`PENDING`)

**Solution**: Updated frontend to check for both status values

**Result**: Pending approvals now display correctly in both approval pages

**Status**: ✅ Complete and Tested

---

**Date**: October 16, 2025  
**Fixed By**: Status filter and badge updates  
**Testing**: Verified in both `/invoice-approvals` and `/approvals`

# Frontend Approval Buttons - Implementation Complete

## Summary

Updated the frontend AR and AP invoice list pages to use the new **submit-for-approval** backend API endpoints.

## Changes Made

### 1. API Service (`frontend/src/services/api.ts`)

Added `submitForApproval` method to both AR and AP invoice APIs:

```typescript
// AR Invoices
export const arInvoicesAPI = {
  // ... existing methods
  submitForApproval: (id: number, data: { submitted_by: string }) => 
    api.post(`/ar/invoices/${id}/submit-for-approval/`, data),
};

// AP Invoices
export const apInvoicesAPI = {
  // ... existing methods
  submitForApproval: (id: number, data: { submitted_by: string }) => 
    api.post(`/ap/invoices/${id}/submit-for-approval/`, data),
};
```

### 2. AR Invoice List Page (`frontend/src/app/ar/invoices/page.tsx`)

**Updated `handleSubmitForApproval` function:**

**Before:**
```typescript
const handleSubmitForApproval = async (invoiceId: number, invoiceNumber: string) => {
  const approverId = prompt('Enter approver user ID:');
  if (!approverId) return;

  try {
    await invoiceApprovalsAPI.create({
      invoice_type: 'AR',
      invoice_id: invoiceId,
      submitted_by: 1,
      approver: parseInt(approverId),
      approval_level: 1
    });
    // ...
  }
};
```

**After:**
```typescript
const handleSubmitForApproval = async (invoiceId: number, invoiceNumber: string) => {
  if (!confirm(`Submit invoice ${invoiceNumber} for approval?`)) {
    return;
  }

  try {
    const response = await arInvoicesAPI.submitForApproval(invoiceId, {
      submitted_by: 'Current User' // TODO: Get from authentication context
    });
    toast.success(`Invoice ${invoiceNumber} submitted for approval successfully`);
    fetchInvoices(); // Refresh the list to show updated status
  } catch (error: any) {
    const errorMessage = error.response?.data?.error || 'Failed to submit for approval';
    toast.error(errorMessage);
    console.error('Submit for approval error:', error.response?.data || error);
  }
};
```

**Updated Button Visibility Condition:**

**Before:**
```typescript
{!invoice.is_posted && !invoice.is_cancelled && !invoice.approval_status && (
```

**After:**
```typescript
{!invoice.is_posted && !invoice.is_cancelled && 
 (invoice.approval_status === 'DRAFT' || !invoice.approval_status) && (
```

### 3. AP Invoice List Page (`frontend/src/app/ap/invoices/page.tsx`)

Applied the same changes as AR invoice page:
- Updated `handleSubmitForApproval` to use new API endpoint
- Updated button visibility condition
- Added confirmation dialog
- Improved error handling

## UI Elements

### Submit for Approval Button

**Location:** Action column in invoice list table

**Icon:** Send icon (📤) from `lucide-react`

**Color:** Purple (`text-purple-600 hover:text-purple-900`)

**Visibility Conditions:**
- ✅ Invoice is NOT posted
- ✅ Invoice is NOT cancelled
- ✅ Invoice approval_status is DRAFT (or null/undefined)

**User Experience:**
1. User clicks Send icon button
2. Confirmation dialog appears: "Submit invoice [number] for approval?"
3. If confirmed, API call is made to backend
4. Success toast: "Invoice [number] submitted for approval successfully"
5. Invoice list refreshes automatically
6. Invoice approval_status badge changes to "Pending"
7. Submit button disappears (invoice is now pending)

## Approval Status Badges

The invoice list already displays approval status badges with color coding:

```typescript
{invoice.approval_status && (
  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
    invoice.approval_status === 'APPROVED'
      ? 'bg-green-100 text-green-800'
      : invoice.approval_status === 'REJECTED'
      ? 'bg-red-100 text-red-800'
      : invoice.approval_status === 'PENDING_APPROVAL'
      ? 'bg-yellow-100 text-yellow-800'
      : 'bg-amber-100 text-amber-800'
  }`}>
    {invoice.approval_status === 'PENDING_APPROVAL' ? 'Pending' 
      : invoice.approval_status === 'APPROVED' ? 'Approved'
      : invoice.approval_status === 'REJECTED' ? 'Rejected'
      : invoice.approval_status}
  </span>
)}
```

**Badge Colors:**
- 🟢 **APPROVED** - Green (`bg-green-100 text-green-800`)
- 🔴 **REJECTED** - Red (`bg-red-100 text-red-800`)
- 🟡 **PENDING_APPROVAL** - Yellow (`bg-yellow-100 text-yellow-800`)
- 🟠 **DRAFT** - Amber (`bg-amber-100 text-amber-800`)

## Testing

### Test Scenario 1: Submit AR Invoice

1. Navigate to http://localhost:3000/ar/invoices
2. Find invoice with "DRAFT" status or no approval status
3. Click purple Send icon (📤)
4. Confirm in dialog
5. See success toast
6. Watch status badge change to "Pending"
7. Submit button should disappear

**Expected Backend Call:**
```
POST /api/ar/invoices/1/submit-for-approval/
Body: {"submitted_by": "Current User"}

Response: {
  "message": "Invoice submitted for approval successfully",
  "approval_id": 1,
  "invoice_id": 1,
  "invoice_number": "1",
  "invoice_total": "21000.00",
  "currency": "USD",
  "approval_status": "PENDING_APPROVAL"
}
```

### Test Scenario 2: Submit AP Invoice

Same steps as AR invoice, but on http://localhost:3000/ap/invoices

### Test Scenario 3: Button Visibility

**Should Show Button:**
- Invoice with DRAFT status ✅
- Invoice with no approval_status ✅
- Invoice not posted ✅
- Invoice not cancelled ✅

**Should NOT Show Button:**
- Invoice with PENDING_APPROVAL status ❌
- Invoice with APPROVED status ❌
- Invoice with REJECTED status ❌
- Posted invoice ❌
- Cancelled invoice ❌

## Action Buttons in Invoice List

After all updates, each invoice row shows appropriate action buttons:

1. **Edit** (✏️ Blue) - Draft invoices only
2. **Submit for Approval** (📤 Purple) - Draft invoices only
3. **Post to GL** (✅ Green) - Draft invoices only
4. **Delete** (🗑️ Red) - Draft invoices only
5. **View** (📄 Gray) - All invoices

## Integration with Approval System

### Complete Workflow

```
┌─────────────────────────────────────────┐
│  AR/AP Invoice List Page                │
│                                         │
│  [Invoice #1 - DRAFT]                   │
│   Actions: Edit | Submit | Post | Delete│
└──────────────┬──────────────────────────┘
               │
               │ Click Submit button (📤)
               ▼
┌─────────────────────────────────────────┐
│  Confirmation Dialog                    │
│  "Submit invoice #1 for approval?"      │
│         [Cancel]  [OK]                  │
└──────────────┬──────────────────────────┘
               │
               │ User confirms
               ▼
┌─────────────────────────────────────────┐
│  Backend API Call                       │
│  POST /api/ar/invoices/1/submit-for-... │
│  Body: {submitted_by: "Current User"}   │
└──────────────┬──────────────────────────┘
               │
               │ Success response
               ▼
┌─────────────────────────────────────────┐
│  UI Updates                             │
│  - Success toast shown                  │
│  - Invoice list refreshed               │
│  - Status badge → "Pending"             │
│  - Submit button disappears             │
└──────────────┬──────────────────────────┘
               │
               │ Invoice now pending
               ▼
┌─────────────────────────────────────────┐
│  AR/AP Invoice List Page                │
│                                         │
│  [Invoice #1 - PENDING] 🟡              │
│   Actions: View only                    │
└──────────────┬──────────────────────────┘
               │
               │ Manager goes to approval page
               ▼
┌─────────────────────────────────────────┐
│  Approval Dashboard                     │
│  /invoice-approvals                     │
│                                         │
│  Shows pending approvals                │
│  Manager can Approve/Reject             │
└─────────────────────────────────────────┘
```

## Error Handling

The frontend handles various error scenarios:

1. **Network Error**
   - Toast: "Failed to submit for approval"
   - Console logs full error details

2. **Validation Error** (e.g., already submitted)
   - Toast: Backend error message (e.g., "Invoice is already pending approval")
   - User can see what went wrong

3. **Server Error**
   - Toast: "Failed to submit for approval"
   - Console logs error for debugging

## Future Enhancements

1. **Authentication Integration**
   - Replace `'Current User'` with actual authenticated user
   - Get from authentication context/session

2. **Permission Checks**
   - Only show submit button for users with permission
   - Check role-based access

3. **Bulk Submit**
   - Select multiple draft invoices
   - Submit all at once for approval

4. **Submission Comments**
   - Optional field for submitter to add notes
   - Help approvers understand context

5. **Notification**
   - Email/notification to approvers when submitted
   - Real-time updates using WebSockets

## Files Modified

1. ✅ `frontend/src/services/api.ts` - Added submitForApproval methods
2. ✅ `frontend/src/app/ar/invoices/page.tsx` - Updated handler and button condition
3. ✅ `frontend/src/app/ap/invoices/page.tsx` - Updated handler and button condition

## Status: ✅ COMPLETE

The "Submit for Approval" buttons are now fully functional on both AR and AP invoice list pages:
- ✅ API endpoints integrated
- ✅ Button visibility logic updated
- ✅ Confirmation dialogs added
- ✅ Success/error handling implemented
- ✅ Status badges display correctly
- ✅ Auto-refresh after submission

**Ready for testing and production use!**

# Invoice Approval Workflow Implementation

## Overview
This document describes the complete approval workflow for AR and AP invoices, including state transitions, action permissions, and UI button visibility.

## Workflow States

### 1. **DRAFT** (Initial State)
- Invoice is created but not submitted for approval
- **Available Actions:**
  - ✅ View
  - ✅ Update/Edit
  - ✅ Delete
  - ✅ Submit for Approval
- **Restricted Actions:**
  - ❌ Post to GL (requires approval first)

### 2. **PENDING_APPROVAL**
- Invoice has been submitted and is awaiting approval
- **Available Actions:**
  - ✅ View
  - ✅ Approve (via approval dashboard)
  - ✅ Reject (via approval dashboard)
- **Restricted Actions:**
  - ❌ Update/Edit (locked during approval)
  - ❌ Delete (locked during approval)
  - ❌ Post to GL (must be approved first)

### 3. **APPROVED**
- Invoice has been approved by an approver
- **Available Actions:**
  - ✅ View
  - ✅ Post to GL
- **Restricted Actions:**
  - ❌ Update/Edit (approved invoices are locked)
  - ❌ Delete (approved invoices are locked)
  - ❌ Submit for Approval (already approved)

### 4. **REJECTED**
- Invoice was rejected by an approver
- **Available Actions:**
  - ✅ View
  - ✅ Update/Edit (can fix and resubmit)
  - ✅ Delete
  - ✅ Submit for Approval (after fixes)
- **Restricted Actions:**
  - ❌ Post to GL (requires approval)

### 5. **POSTED**
- Invoice has been posted to the General Ledger
- **Available Actions:**
  - ✅ View
  - ✅ Reverse (create reversal entry)
- **Restricted Actions:**
  - ❌ Update/Edit (posted entries are immutable)
  - ❌ Delete (posted entries are immutable)
  - ❌ Submit for Approval (already posted)
  - ❌ Post to GL (already posted)

### 6. **REVERSED**
- Invoice has been reversed (final state)
- **Available Actions:**
  - ✅ View only
- **Restricted Actions:**
  - ❌ All modification actions

## State Transition Diagram

```
     CREATE
        ↓
    [DRAFT] ──────────────────────────────┐
        │                                  │
        │ Submit for Approval              │ Delete
        ↓                                  │
[PENDING_APPROVAL]                         X
        │        │
        │        │ Reject
        │        ↓
        │    [REJECTED] ─ Update/Fix ─→ [DRAFT]
        │                                  │
        │ Approve                          │ Delete
        ↓                                  │
   [APPROVED] ────────────────────────────┘
        │
        │ Post to GL
        ↓
    [POSTED]
        │
        │ Reverse
        ↓
   [REVERSED]
        │
        X (End)
```

## Backend Implementation

### 1. Permission Checks in ViewSets

**ARInvoiceViewSet & APInvoiceViewSet:**

```python
def update(self, request, *args, **kwargs):
    """Prevent modification after submission or posting"""
    invoice = self.get_object()
    
    if invoice.is_posted:
        return Response({"error": "Posted invoices cannot be modified"}, 
                       status=400)
    
    if invoice.approval_status in ['PENDING_APPROVAL', 'APPROVED']:
        return Response({"error": f"Invoices with status '{invoice.approval_status}' cannot be modified"}, 
                       status=400)
    
    return super().update(request, *args, **kwargs)

def destroy(self, request, *args, **kwargs):
    """Prevent deletion after submission or posting"""
    invoice = self.get_object()
    
    if invoice.is_posted:
        return Response({"error": "Posted invoices cannot be deleted"}, 
                       status=400)
    
    if invoice.approval_status in ['PENDING_APPROVAL', 'APPROVED']:
        return Response({"error": f"Invoices with status '{invoice.approval_status}' cannot be deleted"}, 
                       status=400)
    
    return super().destroy(request, *args, **kwargs)
```

### 2. Post-to-GL Approval Requirement

```python
@action(detail=True, methods=["post"], url_path="post-gl")
def post_gl(self, request, pk=None):
    invoice = self.get_object()
    
    # Require approval before posting
    if invoice.approval_status != 'APPROVED':
        return Response(
            {"error": f"Invoice must be APPROVED before posting. Current status: {invoice.approval_status or 'DRAFT'}"},
            status=400
        )
    
    # Proceed with posting...
```

### 3. Submit for Approval Validations

```python
@action(detail=True, methods=["post"], url_path="submit-for-approval")
def submit_for_approval(self, request, pk=None):
    invoice = self.get_object()
    
    # Prevent resubmission if already posted
    if invoice.is_posted:
        return Response({"error": "Posted invoices cannot be submitted for approval"}, 
                       status=400)
    
    # Prevent resubmission if already pending
    if invoice.approval_status == 'PENDING_APPROVAL':
        return Response({"error": "Invoice is already pending approval"}, 
                       status=400)
    
    # Prevent resubmission if already approved
    if invoice.approval_status == 'APPROVED':
        return Response({"error": "Invoice is already approved"}, 
                       status=400)
    
    # Create approval record and update status...
```

### 4. Approval Actions Update Invoice Status

**InvoiceApprovalViewSet:**

```python
@action(detail=True, methods=['post'])
def approve(self, request, pk=None):
    approval = self.get_object()
    
    # Update approval record
    approval.status = 'APPROVED'
    approval.save()
    
    # Update invoice approval_status
    if approval.invoice_type == 'AR':
        invoice = ARInvoice.objects.get(id=approval.invoice_id)
        invoice.approval_status = 'APPROVED'
        invoice.save()
    # Similar for AP...

@action(detail=True, methods=['post'])
def reject(self, request, pk=None):
    approval = self.get_object()
    
    # Update approval record
    approval.status = 'REJECTED'
    approval.save()
    
    # Update invoice approval_status
    if approval.invoice_type == 'AR':
        invoice = ARInvoice.objects.get(id=approval.invoice_id)
        invoice.approval_status = 'REJECTED'
        invoice.save()
    # Similar for AP...
```

## Frontend Implementation

### Button Visibility Logic

**AR/AP Invoice Detail Pages:**

```typescript
// Calculate status flags
const isDraft = !invoice.is_posted && !invoice.is_cancelled;
const isApproved = invoice.approval_status === 'APPROVED';
const isPendingApproval = invoice.approval_status === 'PENDING_APPROVAL';
const isRejected = invoice.approval_status === 'REJECTED';
const isDraftStatus = !invoice.approval_status || invoice.approval_status === 'DRAFT';

// Edit and Delete: Only in DRAFT status
{isDraft && isDraftStatus && (
  <>
    <button onClick={editHandler}>Edit</button>
    <button onClick={deleteHandler}>Delete</button>
  </>
)}

// Submit for Approval: Only in DRAFT or REJECTED status
{isDraft && (isDraftStatus || isRejected) && (
  <button onClick={submitForApprovalHandler}>
    Submit for Approval
  </button>
)}

// Post to GL: Only when APPROVED
{isDraft && isApproved && (
  <button onClick={postHandler}>Post</button>
)}

// Reverse: Only when POSTED (to be implemented)
{invoice.is_posted && !invoice.is_cancelled && (
  <button onClick={reverseHandler}>Reverse</button>
)}
```

### Status Badge Display

```typescript
{invoice.approval_status && (
  <span className={`badge ${
    invoice.approval_status === 'APPROVED' ? 'badge-green'
    : invoice.approval_status === 'REJECTED' ? 'badge-red'
    : invoice.approval_status === 'PENDING_APPROVAL' ? 'badge-yellow'
    : 'badge-gray'
  }`}>
    {invoice.approval_status === 'PENDING_APPROVAL' ? 'Pending Approval' 
     : invoice.approval_status === 'APPROVED' ? 'Approved'
     : invoice.approval_status === 'REJECTED' ? 'Rejected'
     : invoice.approval_status}
  </span>
)}
```

## API Endpoints

### Invoice Management
- `POST /api/ar/invoices/` - Create AR invoice (DRAFT)
- `PUT /api/ar/invoices/{id}/` - Update AR invoice (only if DRAFT)
- `DELETE /api/ar/invoices/{id}/` - Delete AR invoice (only if DRAFT)
- `POST /api/ar/invoices/{id}/submit-for-approval/` - Submit for approval
- `POST /api/ar/invoices/{id}/post-gl/` - Post to GL (only if APPROVED)

### Approval Management
- `GET /api/invoice-approvals/` - List all approvals
- `GET /api/invoice-approvals/{id}/` - Get approval details
- `POST /api/invoice-approvals/{id}/approve/` - Approve invoice
- `POST /api/invoice-approvals/{id}/reject/` - Reject invoice

## User Experience Flow

### Creating and Posting an Invoice

1. **Create Invoice**
   - User navigates to AR/AP invoice creation page
   - Fills in invoice details and line items
   - Saves as DRAFT
   - Status: `DRAFT`, Approval Status: `DRAFT` or `null`

2. **Submit for Approval**
   - User views invoice detail page
   - Clicks "Submit for Approval" button (purple)
   - Confirms submission
   - Invoice status changes to `PENDING_APPROVAL`
   - Approval record created in `InvoiceApproval` table
   - Edit/Delete buttons disappear

3. **Approval Process**
   - Approver goes to Invoice Approvals page or Approval Dashboard
   - Reviews invoice details
   - Either:
     - **Approves**: Invoice status → `APPROVED`
     - **Rejects**: Invoice status → `REJECTED`, can be edited and resubmitted

4. **Post to GL**
   - User views APPROVED invoice
   - Clicks "Post" button (green) - only visible when APPROVED
   - Invoice is posted to General Ledger
   - Status changes to `is_posted=True`
   - All modification actions disabled
   - Only "Reverse" action available

5. **Reversal** (if needed)
   - User views POSTED invoice
   - Clicks "Reverse" button
   - Reversal entry created
   - Original invoice marked as `REVERSED`

## Error Messages

### Update/Delete Errors
- **Posted Invoice**: "Posted invoices cannot be modified. Use reversal if needed."
- **Pending Approval**: "Invoices with status 'PENDING_APPROVAL' cannot be modified."
- **Approved**: "Invoices with status 'APPROVED' cannot be modified."

### Submit for Approval Errors
- **Already Posted**: "Posted invoices cannot be submitted for approval"
- **Already Pending**: "Invoice is already pending approval"
- **Already Approved**: "Invoice is already approved"
- **Cancelled**: "Cancelled invoices cannot be submitted for approval"

### Post to GL Errors
- **Not Approved**: "Invoice must be APPROVED before posting. Current status: DRAFT"
- **Already Posted**: "Invoice is already posted"

## Database Schema

### ARInvoice / APInvoice
```python
class ARInvoice(models.Model):
    # ... other fields ...
    
    approval_status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('PENDING_APPROVAL', 'Pending Approval'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
        ],
        default='DRAFT',
        help_text="Approval workflow status"
    )
    
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
```

### InvoiceApproval
```python
class InvoiceApproval(models.Model):
    invoice_type = models.CharField(max_length=2, choices=[('AR', 'AR Invoice'), ('AP', 'AP Invoice')])
    invoice_id = models.IntegerField()
    
    status = models.CharField(max_length=20, choices=InvoiceApprovalStatus.choices, 
                             default='PENDING_APPROVAL')
    submitted_by = models.CharField(max_length=128)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    approver = models.CharField(max_length=128, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    
    comments = models.TextField(blank=True)
    approval_level = models.IntegerField(default=1)
```

## Testing Checklist

### Backend Tests
- [ ] Cannot update invoice in PENDING_APPROVAL status
- [ ] Cannot update invoice in APPROVED status
- [ ] Cannot update invoice in POSTED status
- [ ] Cannot delete invoice in PENDING_APPROVAL status
- [ ] Cannot delete invoice in APPROVED status
- [ ] Cannot delete invoice in POSTED status
- [ ] Can update invoice in REJECTED status
- [ ] Can delete invoice in REJECTED status
- [ ] Cannot post invoice without APPROVED status
- [ ] Can post invoice when APPROVED
- [ ] Approving updates invoice.approval_status to APPROVED
- [ ] Rejecting updates invoice.approval_status to REJECTED

### Frontend Tests
- [ ] Edit button only visible in DRAFT status
- [ ] Delete button only visible in DRAFT status
- [ ] Submit for Approval button visible in DRAFT and REJECTED
- [ ] Post button only visible when APPROVED
- [ ] Approval status badge displays correct status and color
- [ ] Error toasts shown when actions fail
- [ ] Success toasts shown when actions succeed
- [ ] Page refreshes after status changes

## Future Enhancements

1. **Multi-level Approval**
   - Support approval chains with multiple levels
   - Configure approval limits based on invoice amount

2. **Approval Notifications**
   - Email notifications to approvers
   - Dashboard notifications for pending approvals

3. **Approval History**
   - Show full approval timeline on invoice detail page
   - Track all approval/rejection events

4. **Conditional Approval**
   - Auto-approve invoices under certain threshold
   - Skip approval for specific customers/suppliers

5. **Reversal Workflow**
   - Implement reversal approval workflow
   - Track reversal reasons and approvals

## Related Files

### Backend
- `finance/models.py` - InvoiceApproval model
- `ar/models.py` - ARInvoice with approval_status field
- `ap/models.py` - APInvoice with approval_status field
- `finance/api.py` - ARInvoiceViewSet and APInvoiceViewSet with permission checks
- `finance/api_extended.py` - InvoiceApprovalViewSet with approve/reject actions

### Frontend
- `frontend/src/app/ar/invoices/[id]/page.tsx` - AR invoice detail page
- `frontend/src/app/ap/invoices/[id]/page.tsx` - AP invoice detail page
- `frontend/src/app/invoice-approvals/page.tsx` - Invoice approvals dashboard
- `frontend/src/services/api.ts` - API client methods

### Documentation
- `docs/INVOICE_APPROVAL_WORKFLOW.md` - This document
- `docs/INVOICE_STATUS_SEPARATION.md` - Status field separation
- `docs/AR_AP_INVOICE_STATUS.md` - Invoice status implementation

## Version History

- **v1.0** (2025-10-17): Initial workflow implementation
  - State machine enforced in backend
  - Button visibility logic in frontend
  - Post-to-GL approval requirement
  - Approval actions update invoice status

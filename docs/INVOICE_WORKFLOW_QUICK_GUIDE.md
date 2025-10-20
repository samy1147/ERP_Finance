# Invoice Workflow Quick Reference

## 🔄 Invoice Lifecycle

```
CREATE → DRAFT → SUBMIT → PENDING → APPROVE → APPROVED → POST → POSTED → REVERSE → REVERSED
                              ↓
                          REJECT → REJECTED → (can resubmit)
```

## 📋 Available Actions by Status

| Status | Edit | Delete | Submit | Post | Reverse |
|--------|------|--------|--------|------|---------|
| **DRAFT** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **PENDING_APPROVAL** | ❌ | ❌ | ❌ | ❌ | ❌ |
| **APPROVED** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **REJECTED** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **POSTED** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **REVERSED** | ❌ | ❌ | ❌ | ❌ | ❌ |

## 🎯 Button Colors & Meanings

| Button | Color | Status Required | Action |
|--------|-------|-----------------|--------|
| **Edit** | Gray | DRAFT or REJECTED | Modify invoice details |
| **Delete** | Red | DRAFT or REJECTED | Delete invoice |
| **Submit for Approval** | Purple | DRAFT or REJECTED | Send to approver |
| **Post** | Green | APPROVED | Post to GL |
| **Reverse** | Orange | POSTED | Create reversal entry |

## 🚦 Status Badge Colors

| Badge | Color | Meaning |
|-------|-------|---------|
| **Draft** | Gray | Not yet submitted |
| **Pending Approval** | Yellow | Awaiting approval |
| **Approved** | Green | Ready to post |
| **Rejected** | Red | Needs fixes |
| **Posted** | Blue | Posted to GL |
| **Reversed** | Purple | Reversed entry |

## 💡 Common Workflows

### ✅ Normal Approval Flow
1. Create invoice → Status: **DRAFT**
2. Click "Submit for Approval" → Status: **PENDING_APPROVAL**
3. Approver approves → Status: **APPROVED**
4. Click "Post" → Status: **POSTED**

### ❌ Rejection & Resubmission
1. Invoice submitted → Status: **PENDING_APPROVAL**
2. Approver rejects → Status: **REJECTED**
3. Fix invoice (Edit button appears) → Status: **DRAFT**
4. Click "Submit for Approval" again → Status: **PENDING_APPROVAL**
5. Approver approves → Status: **APPROVED**
6. Click "Post" → Status: **POSTED**

### 🔄 Reversal
1. Posted invoice → Status: **POSTED**
2. Click "Reverse" → Status: **REVERSED**
3. Reversal entry created in GL

## 🔒 Lock Rules

### When is an invoice LOCKED (no edit/delete)?
- ✅ When **PENDING_APPROVAL** (awaiting approval)
- ✅ When **APPROVED** (ready to post)
- ✅ When **POSTED** (in GL)
- ✅ When **REVERSED** (final state)

### When can you EDIT/DELETE?
- ✅ When **DRAFT** (initial state)
- ✅ When **REJECTED** (needs fixes)

## ⚠️ Common Error Messages

| Error | Reason | Solution |
|-------|--------|----------|
| "Invoices with status 'PENDING_APPROVAL' cannot be modified" | Invoice is locked for approval | Wait for approval/rejection |
| "Invoice must be APPROVED before posting" | Trying to post without approval | Submit for approval first |
| "Posted invoices cannot be modified" | Invoice already in GL | Use reversal instead |
| "Invoice is already pending approval" | Resubmitting pending invoice | Wait for approval/rejection |

## 📍 Where to Find Actions

### Invoice Detail Page
- **Location**: Click on any invoice from the list
- **Actions Available**: Edit, Delete, Submit for Approval, Post
- **Status Badge**: Top right corner shows current approval status

### Invoice List Page
- **Location**: AR Invoices or AP Invoices page
- **Actions Available**: Quick actions (Send icon for submit)
- **Status Column**: Shows both posting status and approval status

### Approval Dashboard
- **Location**: Invoice Approvals menu
- **Actions Available**: Approve, Reject
- **Filters**: Pending, Approved, Rejected tabs

## 🎓 Best Practices

1. **Always review invoice details** before submitting for approval
2. **Add comments when rejecting** to help submitter understand issues
3. **Post invoices promptly** after approval to keep GL up to date
4. **Use reversal** instead of deleting posted invoices
5. **Check approval status badge** to understand current state

## 🔧 Troubleshooting

### Can't edit invoice?
→ Check status - if PENDING, APPROVED, or POSTED, editing is locked

### Can't post invoice?
→ Must be APPROVED first - submit for approval if still DRAFT

### Submit button disappeared?
→ Invoice is PENDING or APPROVED - wait for approval completion

### Want to fix rejected invoice?
→ Edit button will appear once rejected - fix and resubmit

## 📞 Need Help?

- Review full documentation: `docs/INVOICE_APPROVAL_WORKFLOW.md`
- Check status separation guide: `docs/INVOICE_STATUS_SEPARATION.md`
- Contact system administrator for approval workflow issues

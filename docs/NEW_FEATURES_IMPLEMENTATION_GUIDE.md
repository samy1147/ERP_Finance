# 🚀 NEW FEATURES IMPLEMENTATION GUIDE

## Overview
This document describes the three major features added to the FinanceERP system:

1. **Payment Allocations** - Allow partial/split payments
2. **Invoice Approval Workflow** - Multi-level approval process
3. **Invoice Editing** - Edit draft invoices (backend ready, frontend TBD)

---

## 1. PAYMENT ALLOCATIONS

### What Changed?

#### AR Payment Model (`ar/models.py`)
```python
# OLD (One payment = One invoice)
class ARPayment:
    invoice = FK(ARInvoice)
    amount = Decimal
    
# NEW (One payment = Multiple invoices)
class ARPayment:
    customer = FK(Customer)          # Payment is to customer, not invoice
    reference = CharField(unique)     # Unique payment reference
    total_amount = Decimal            # Total payment amount
    currency = FK(Currency)
    # ... other fields ...

class ARPaymentAllocation:         # NEW MODEL
    payment = FK(ARPayment)
    invoice = FK(ARInvoice)
    amount = Decimal                # Amount allocated to this invoice
```

#### AP Payment Model (`ap/models.py`)
Similar changes for supplier payments.

### Key Features

✅ **Split One Payment Across Multiple Invoices**
```json
POST /api/ar/payments/
{
  "customer": 1,
  "reference": "PMT-001",
  "total_amount": "5000.00",
  "currency": 1,
  "date": "2025-10-15",
  "allocations": [
    {"invoice": 10, "amount": "3000.00"},
    {"invoice": 11, "amount": "2000.00"}
  ]
}
```

✅ **Partial Payment Support**
```json
{
  "customer": 1,
  "total_amount": "1500.00",
  "allocations": [
    {"invoice": 10, "amount": "1500.00"}
  ]
}
// Invoice 10 total: $3000
// Paid: $1500
// Outstanding: $1500
```

✅ **Unallocated Payments**
```json
{
  "customer": 1,
  "total_amount": "10000.00",
  "allocations": [
    {"invoice": 10, "amount": "3000.00"}
  ]
}
// Total: $10,000
// Allocated: $3,000
// Unallocated: $7,000 (can allocate later)
```

### New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ar/payments/` | GET | List AR payments with allocations |
| `/api/ar/payments/` | POST | Create AR payment with allocations |
| `/api/ar/payments/{id}/` | GET | Get payment details |
| `/api/ar/payments/{id}/` | PATCH | Update payment allocations |
| `/api/ar/payments/{id}/post/` | POST | Post payment to GL |
| `/api/ar/payments/{id}/reconcile/` | POST | Mark payment as reconciled |
| `/api/ar/payments/outstanding/` | GET | List payments with unallocated amounts |
| `/api/ap/payments/*` | * | Same for AP payments |
| `/api/outstanding-invoices/?customer=1` | GET | Get outstanding invoices for customer |
| `/api/outstanding-invoices/?supplier=1` | GET | Get outstanding invoices for supplier |

### Invoice Methods

```python
# Calculate invoice outstanding amount
invoice = ARInvoice.objects.get(id=10)
total = invoice.calculate_total()           # Total from items
paid = invoice.paid_amount()                # Sum of allocations
outstanding = invoice.outstanding_amount()  # Total - Paid
```

---

## 2. INVOICE APPROVAL WORKFLOW

### New Fields Added to Invoices

```python
# ar/models.py - ARInvoice
class ARInvoice:
    approval_status = CharField(choices=[
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ], default='DRAFT')

# ap/models.py - APInvoice
class APInvoice:
    approval_status = CharField(...)  # Same choices
```

### New Model (`finance/models.py`)

```python
class InvoiceApproval:
    invoice_type = CharField  # 'AR' or 'AP'
    invoice_id = IntegerField
    status = CharField        # PENDING_APPROVAL, APPROVED, REJECTED
    submitted_by = CharField
    submitted_at = DateTimeField
    approver = CharField
    approved_at = DateTimeField
    rejected_at = DateTimeField
    comments = TextField
    approval_level = IntegerField  # For multi-level approvals
```

### Workflow

#### Status Flow
```
DRAFT
  ↓ [Submit for Approval]
PENDING_APPROVAL
  ↓                    ↓
[Approve]          [Reject]
  ↓                    ↓
APPROVED            REJECTED
  ↓                    ↓
[Post to GL]      [Back to DRAFT]
  ↓
POSTED
```

#### 1. Submit Invoice for Approval
```json
POST /api/invoice-approvals/
{
  "invoice_type": "AR",
  "invoice_id": 10,
  "status": "PENDING_APPROVAL",
  "submitted_by": "john.doe@company.com",
  "approval_level": 1
}
```

#### 2. Approve Invoice
```json
POST /api/invoice-approvals/{id}/approve/
{
  "approver": "manager@company.com",
  "comments": "Approved - looks good"
}
```

#### 3. Reject Invoice
```json
POST /api/invoice-approvals/{id}/reject/
{
  "approver": "manager@company.com",
  "comments": "Rejected - missing line items"
}
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/invoice-approvals/` | GET | List all approvals |
| `/api/invoice-approvals/` | POST | Submit invoice for approval |
| `/api/invoice-approvals/{id}/` | GET | Get approval details |
| `/api/invoice-approvals/{id}/approve/` | POST | Approve invoice |
| `/api/invoice-approvals/{id}/reject/` | POST | Reject invoice |

### Query Parameters

- `?status=PENDING_APPROVAL` - Filter by approval status
- `?invoice_type=AR` - Filter by invoice type

### Business Rules

✅ **Only DRAFT invoices can be submitted for approval**
✅ **Only APPROVED invoices can be posted to GL**
✅ **Rejected invoices go back to DRAFT for editing**
✅ **Comments required when rejecting**
✅ **Approval history is tracked**

---

## 4. INVOICE EDITING

### Current State

✅ **Backend Models Support Editing**
- Draft invoices can be modified
- Posted invoices are locked
- Line items can be added/removed

❌ **Frontend NOT YET IMPLEMENTED**
- Need to create edit pages
- `/ar/invoices/{id}/edit`
- `/ap/invoices/{id}/edit`

### How to Edit (via API)

```json
# Update invoice header
PATCH /api/ar/invoices/{id}/
{
  "due_date": "2025-11-30",
  "country": "SA"
}

# Add/Update line items (recreate all items)
PUT /api/ar/invoices/{id}/
{
  "number": "INV-001",
  "customer": 1,
  "date": "2025-10-15",
  "due_date": "2025-11-15",
  "currency": 1,
  "items": [
    {"description": "Product A", "quantity": 10, "unit_price": "100.00", "tax_rate": 1},
    {"description": "Product B", "quantity": 5, "unit_price": "200.00", "tax_rate": 1}
  ]
}
```

### Editing Rules

✅ **Can Edit:**
- Draft invoices (approval_status = 'DRAFT')
- All fields except `id`, `posted_at`, `gl_journal`

❌ **Cannot Edit:**
- Posted invoices (is_posted = True)
- Approved invoices without rejection
- Cancelled invoices

---

## MIGRATION STEPS

### 1. Generate Migrations

```bash
python manage.py makemigrations ar
python manage.py makemigrations ap
python manage.py makemigrations finance
```

### 2. Review Migrations

Check the generated migration files in:
- `ar/migrations/`
- `ap/migrations/`
- `finance/migrations/`

### 3. Apply Migrations

```bash
python manage.py migrate
```

### 4. Handle Existing Data

**IMPORTANT:** Existing AR/AP payments need migration!

```python
# Run this script to migrate old payments
python manage.py shell

from ar.models import ARPayment, ARPaymentAllocation
from ap.models import APPayment, APPaymentAllocation

# Migrate AR payments
for payment in ARPayment.objects.filter(invoice__isnull=False, customer__isnull=True):
    payment.customer = payment.invoice.customer
    payment.reference = f"PMT-AR-{payment.id}"
    payment.total_amount = payment.amount or 0
    payment.currency = payment.invoice.currency
    payment.save()
    
    # Create allocation if amount > 0
    if payment.amount and payment.amount > 0:
        ARPaymentAllocation.objects.create(
            payment=payment,
            invoice=payment.invoice,
            amount=payment.amount
        )

# Migrate AP payments
for payment in APPayment.objects.filter(invoice__isnull=False, supplier__isnull=True):
    payment.supplier = payment.invoice.supplier
    payment.reference = f"PMT-AP-{payment.id}"
    payment.total_amount = payment.amount or 0
    payment.currency = payment.invoice.currency
    payment.save()
    
    # Create allocation if amount > 0
    if payment.amount and payment.amount > 0:
        APPaymentAllocation.objects.create(
            payment=payment,
            invoice=payment.invoice,
            amount=payment.amount
        )
```

---

## FRONTEND IMPLEMENTATION (TODO)

### Priority 1: Payment Pages

**AR Payment Create/Edit** (`/ar/payments/new`, `/ar/payments/{id}/edit`)
- Customer dropdown
- Payment reference input
- Total amount
- Date picker
- Currency selector
- **Allocation Section:**
  - Show customer's outstanding invoices
  - Checkboxes to select invoices
  - Amount input for each selected invoice
  - Auto-calculate unallocated amount
  - Warning if over-allocated

**AP Payment Create/Edit** (similar structure)

### Priority 2: Approval Dashboard

**Approvals Dashboard** (`/approvals`)
- **Pending Approvals Tab:**
  - List of invoices awaiting approval
  - Invoice details preview
  - Approve/Reject buttons
  - Comments field
- **My Submissions Tab:**
  - Invoices I submitted
  - Current status
- **History Tab:**
  - All approvals
  - Filter by date/status

**Invoice Pages Updates:**
- Add "Submit for Approval" button on draft invoices
- Show approval status badge
- Disable "Post to GL" if not approved

### Priority 3: Invoice Editing

**Invoice Edit Pages** (`/ar/invoices/{id}/edit`, `/ap/invoices/{id}/edit`)
- Same form as create page
- Pre-filled with existing data
- Can modify all fields
- Can add/remove line items
- Save button
- "Only DRAFT invoices can be edited" message for posted ones

---

## TESTING CHECKLIST

### Payment Allocations
- [ ] Create payment with single allocation
- [ ] Create payment with multiple allocations
- [ ] Create payment with partial allocation (unallocated balance)
- [ ] Verify invoice outstanding_amount() updates correctly
- [ ] Post payment to GL

### Invoice Approval
- [ ] Submit draft invoice for approval
- [ ] Approve invoice
- [ ] Reject invoice with comments
- [ ] Verify rejected invoice goes back to DRAFT
- [ ] Verify only approved invoices can be posted
- [ ] List pending approvals

### Invoice Editing (via API)
- [ ] Edit draft invoice header
- [ ] Add/remove line items
- [ ] Verify posted invoice cannot be edited
- [ ] Verify approved invoice requires rejection before edit

---

## API DOCUMENTATION

All new endpoints are automatically documented in:
- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/

Refresh after server restart to see new endpoints.

---

## NEXT STEPS

1. ✅ Run migrations
2. ✅ Test all APIs via Swagger/Postman
3. ⏳ Implement frontend payment pages
4. ⏳ Implement approval dashboard
5. ⏳ Implement invoice edit pages
6. ⏳ Create user documentation
7. ⏳ Add automated tests

---

## SUPPORT

If you encounter issues:
1. Check migration errors first
2. Review API documentation at `/api/docs/`
3. Test endpoints with Postman/curl before building frontend
4. Check Django admin to verify data structure


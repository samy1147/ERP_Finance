# Invoice Status Field Separation

## Overview
The AR and AP invoice models have been refactored to separate the single `status` field into distinct fields for better clarity and flexibility.

## Changes

### Old Structure
Previously, invoices had a single `status` field with values:
- `DRAFT` - Unposted invoice
- `POSTED` - Posted to GL but not paid
- `PAID` - Fully paid
- `CANCELLED` - Cancelled invoice

This combined multiple concerns (posting status, payment status, cancellation) into one field.

### New Structure

#### 1. Posting Status
**Field:** `is_posted` (Boolean)
- `False` - Invoice is in draft/unposted state
- `True` - Invoice has been posted to the General Ledger

**Related Field:** `posted_at` (DateTime) - Timestamp when invoice was posted

#### 2. Payment Status
**Field:** `payment_status` (CharField with choices)
- `UNPAID` - No payments received
- `PARTIALLY_PAID` - Some payments received but not fully paid
- `PAID` - Fully paid

**Related Field:** `paid_at` (DateTime) - Timestamp when invoice was fully paid

#### 3. Cancellation Status
**Field:** `is_cancelled` (Boolean)
- `False` - Invoice is active
- `True` - Invoice has been cancelled

**Related Field:** `cancelled_at` (DateTime) - Timestamp when invoice was cancelled

## Benefits

1. **Clarity**: Each field has a single, clear purpose
2. **Flexibility**: Can now track partially paid invoices separately
3. **Independence**: Posting and payment states are independent
4. **Better Queries**: Easier to filter invoices by specific criteria
   - Get all posted invoices: `filter(is_posted=True)`
   - Get all unpaid posted invoices: `filter(is_posted=True, payment_status='UNPAID')`
   - Get partially paid invoices: `filter(payment_status='PARTIALLY_PAID')`

## Migration Path

The migration is done in three steps:

### Step 1: Add New Fields (Migration 0003)
- Adds `is_posted`, `payment_status`, `is_cancelled`, and related timestamp fields
- Makes old `status` field nullable

### Step 2: Data Migration (Migration 0004)
- Converts existing data from old `status` to new fields:
  - `DRAFT` → `is_posted=False, payment_status=UNPAID`
  - `POSTED` → `is_posted=True, payment_status=UNPAID`
  - `PAID` → `is_posted=True, payment_status=PAID`
  - `CANCELLED` → `is_cancelled=True, is_posted=False, payment_status=UNPAID`

### Step 3: Remove Old Field (Migration 0005)
- Removes the old `status` field

## Code Changes

### Models (ar/models.py, ap/models.py)
- Removed single `status` field
- Added separate `is_posted`, `payment_status`, `is_cancelled` fields
- Added timestamp fields: `posted_at`, `paid_at`, `cancelled_at`

### Admin (ar/admin.py, ap/admin.py)
- Updated `list_display` to show new fields
- Updated `list_filter` to filter by new fields
- Updated fieldsets to group status fields together
- Changed readonly field checks from `posted_at` to `is_posted`

### Services (finance/services.py)
- Updated `gl_post_from_ar_balanced()` to set `is_posted=True`
- Updated `gl_post_from_ap_balanced()` to set `is_posted=True`
- Updated `post_ar_payment()` to set `payment_status` correctly:
  - Sets to `PAID` when fully paid
  - Sets to `PARTIALLY_PAID` when partially paid
- Updated `post_ap_payment()` with same payment status logic

### Tests (tests/test_payments.py)
- Updated assertions to check `payment_status` instead of `status`

## Usage Examples

### Creating a New Invoice
```python
invoice = ARInvoice.objects.create(
    customer=customer,
    number="INV-001",
    date=date.today(),
    due_date=date.today() + timedelta(days=30),
    currency=currency,
    # Default values:
    # is_posted=False
    # payment_status='UNPAID'
    # is_cancelled=False
)
```

### Posting an Invoice
```python
# In posting service
invoice.is_posted = True
invoice.posted_at = timezone.now()
invoice.save(update_fields=['is_posted', 'posted_at'])
```

### Recording a Payment
```python
# After posting a payment
if invoice_fully_paid:
    invoice.payment_status = 'PAID'
    invoice.paid_at = timezone.now()
    invoice.save(update_fields=['payment_status', 'paid_at'])
elif has_partial_payments:
    invoice.payment_status = 'PARTIALLY_PAID'
    invoice.save(update_fields=['payment_status'])
```

### Cancelling an Invoice
```python
invoice.is_cancelled = True
invoice.cancelled_at = timezone.now()
invoice.save(update_fields=['is_cancelled', 'cancelled_at'])
```

### Querying Invoices

```python
# Get all unposted invoices
ARInvoice.objects.filter(is_posted=False)

# Get all posted but unpaid invoices
ARInvoice.objects.filter(is_posted=True, payment_status='UNPAID')

# Get all partially paid invoices
ARInvoice.objects.filter(payment_status='PARTIALLY_PAID')

# Get all posted and fully paid invoices
ARInvoice.objects.filter(is_posted=True, payment_status='PAID')

# Get all active (non-cancelled) invoices
ARInvoice.objects.filter(is_cancelled=False)

# Get overdue unpaid invoices
from django.utils import timezone
ARInvoice.objects.filter(
    is_posted=True,
    payment_status__in=['UNPAID', 'PARTIALLY_PAID'],
    due_date__lt=timezone.now().date(),
    is_cancelled=False
)
```

## Frontend Integration

The frontend will need to be updated to:
1. Display separate status indicators for posting and payment status
2. Update filter dropdowns to use new field names
3. Show "Partially Paid" status in invoice lists
4. Update API calls to use new field names

## Rollback

If needed, the migration can be rolled back:
```bash
python manage.py migrate ar 0002
python manage.py migrate ap 0002
```

This will revert to the old single `status` field structure.

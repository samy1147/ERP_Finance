# Finance Signals Documentation (signals.py)

## Overview
This file implements Django signal handlers that enforce business rules and data integrity for invoices. The signals replicate PostgreSQL trigger behavior but work across all database backends (SQLite, PostgreSQL, MySQL, etc.).

---

## File Location
```
finance/signals.py
```

---

## Purpose

**Why Signals?**
- **Database Agnostic:** Works on SQLite, PostgreSQL, Oracle, etc.
- **Centralized Logic:** Business rules in one place
- **Automatic Enforcement:** No manual validation needed
- **Pre-save Hooks:** Catch violations before database write

**Replaces:** PostgreSQL triggers (which only work on PostgreSQL)

---

## Signal Handlers

### 1. `validate_invoice_posting`

**Signal:** `pre_save` on `Invoice` model

**Purpose:** Validates invoice before allowing status change to POSTED

**Trigger Condition:** When invoice status changes FROM non-POSTED TO POSTED

**Validation Checks:**

#### Check 1: Has Lines
```python
if lines_count == 0:
    raise ValidationError("Cannot post invoice: it has no lines.")
```

**Why:** Empty invoices have no financial impact

#### Check 2: Lines Have Account and Tax
```python
missing_acct_tax = instance.lines.filter(
    Q(account__isnull=True) | Q(tax_code__isnull=True)
).exists()

if missing_acct_tax:
    raise ValidationError("...one or more lines missing account or tax.")
```

**Why:** GL posting requires account codes, tax reporting requires tax codes

#### Check 3: Totals Not Zero
```python
if gross == 0:
    raise ValidationError("Cannot post invoice: totals are zero.")
```

**Why:** Zero-amount invoices serve no accounting purpose

#### Check 4: Normalize Header Totals
```python
instance.total_net = net    # From line aggregation
instance.total_tax = tax    # From line aggregation
instance.total_gross = gross  # From line aggregation
```

**Why:** Prevents drift between header totals and line totals

**Example Workflow:**
```python
# Create invoice with lines
invoice = Invoice.objects.create(...)
InvoiceLine.objects.create(invoice=invoice, amount_gross=100, ...)
InvoiceLine.objects.create(invoice=invoice, amount_gross=200, ...)

# Try to post
invoice.status = InvoiceStatus.POSTED
invoice.save()  # Signal validates:
                # ✓ Has 2 lines
                # ✓ All lines have account/tax
                # ✓ Total > 0
                # ✓ Normalizes totals to 300
```

**Error Handling:**
```python
try:
    invoice.status = InvoiceStatus.POSTED
    invoice.save()
except ValidationError as e:
    print(f"Cannot post: {e.message}")
    # "Cannot post invoice INV-001: it has no lines."
```

---

### 2. `block_edit_posted_invoice`

**Signal:** `pre_save` on `Invoice` model

**Purpose:** Prevents modification of posted invoices (read-only enforcement)

**Trigger Condition:** When invoice OLD status is POSTED

**Protected Fields:**
- `invoice_no`: Invoice number
- `customer`: Customer reference
- `currency`: Currency
- `total_net`: Net total
- `total_tax`: Tax total
- `total_gross`: Gross total

**Allowed Changes (Whitelist):**
- `status`: Can change POSTED → REVERSED
- `reversal_ref`: Can link to reversal invoice
- `posted_at`: Timestamp field
- `updated_at`: Automatic timestamp

**Logic:**
```python
if old_instance.status == 'POSTED':
    # Allow status change (POSTED -> REVERSED)
    if instance.status != old_instance.status:
        return  # Allowed
    
    # Check protected fields
    if any field changed:
        raise ValidationError("Posted documents are read-only. Use reversal API.")
```

**Example:**
```python
invoice = Invoice.objects.get(id=1)  # Status: POSTED

# ✅ ALLOWED: Status change
invoice.status = InvoiceStatus.REVERSED
invoice.save()  # Works!

# ❌ BLOCKED: Change customer
invoice.customer = other_customer
invoice.save()  # ValidationError: "Posted documents are read-only..."

# ❌ BLOCKED: Change amount
invoice.total_gross = Decimal("999.99")
invoice.save()  # ValidationError: "Posted documents are read-only..."
```

**Error Message:**
```
Posted documents are read-only. Cannot modify: customer, total_gross. Use reversal API.
```

**Why Read-only?**
- **Audit Trail:** Posted invoices are financial records
- **GL Impact:** Already posted to General Ledger
- **Compliance:** Accounting standards require immutability
- **Tax Reporting:** Already reported to tax authorities

**Proper Way to Change:**
```python
# Don't edit posted invoice
# Instead: Create reversal

from finance.services import reverse_posted_invoice

# 1. Reverse original
reversal = reverse_posted_invoice(original_id=1)
# Creates negative invoice

# 2. Create new corrected invoice
corrected = Invoice.objects.create(...)
# New invoice with correct data
```

---

### 3. `block_edit_posted_invoice_lines`

**Signal:** `pre_save` on `InvoiceLine` model

**Purpose:** Prevents modification of lines on posted invoices

**Trigger Condition:** When line belongs to invoice with status=POSTED

**Protected Operations:**

#### Block Update
```python
if instance.pk:  # Existing line
    if any field changed:
        raise ValidationError("Cannot modify lines of posted invoice...")
```

**Checked Fields:**
- `account_id`: GL account
- `tax_code_id`: Tax code
- `amount_net`: Net amount
- `tax_amount`: Tax amount
- `amount_gross`: Gross amount
- `description`: Line description

#### Block Insert
```python
else:  # New line
    if invoice.status == 'POSTED':
        raise ValidationError("Cannot add lines to posted invoice...")
```

**Why Block Line Changes?**
- **Consistency:** Header already posted to GL
- **Totals:** Would invalidate posted totals
- **Audit:** Line items are part of immutable record

**Example:**
```python
invoice = Invoice.objects.get(id=1)  # POSTED
line = invoice.lines.first()

# ❌ BLOCKED: Modify existing line
line.amount_gross = Decimal("500.00")
line.save()  # ValidationError

# ❌ BLOCKED: Add new line
InvoiceLine.objects.create(
    invoice=invoice,
    amount_gross=Decimal("100.00")
)  # ValidationError

# ❌ BLOCKED: Delete line
line.delete()  # ValidationError (from Django's delete signal)
```

**Delete Protection:**
Django signals don't catch `delete()` - use the `LockOnPostedMixin` model method:
```python
class InvoiceLine(LockOnPostedMixin, models.Model):
    def delete(self, *args, **kwargs):
        if self.invoice.status == InvoiceStatus.POSTED:
            raise ValidationError("Cannot delete lines of posted invoice")
        super().delete(*args, **kwargs)
```

---

## Signal Registration

Signals are automatically registered when app initializes:

**In `apps.py`:**
```python
class FinanceConfig(AppConfig):
    name = 'finance'
    
    def ready(self):
        import finance.signals  # Import to register
```

**No manual registration needed!**

---

## Technical Details

### Signal Type: `pre_save`

**Timing:** Called BEFORE `.save()` writes to database

**Advantages:**
- Can modify `instance` before save
- Can raise exception to block save
- Access to both old and new values

**Alternative:** `post_save` (AFTER save, can't block)

### Sender Strings
```python
@receiver(pre_save, sender='finance.Invoice')
```

**Why String?** Avoids circular import issues

**Alternative:** Direct import
```python
from finance.models import Invoice
@receiver(pre_save, sender=Invoice)
```

### Checking for UPDATE vs INSERT
```python
if instance.pk:  # Has primary key = existing record (UPDATE)
    old_instance = sender.objects.get(pk=instance.pk)
else:  # No primary key = new record (INSERT)
    pass
```

---

## Testing Signals

### Test Validation
```python
from django.test import TestCase
from django.core.exceptions import ValidationError

class InvoiceSignalTests(TestCase):
    def test_cannot_post_without_lines(self):
        invoice = Invoice.objects.create(...)
        invoice.status = InvoiceStatus.POSTED
        
        with self.assertRaises(ValidationError):
            invoice.save()  # Should fail
```

### Test Read-only
```python
def test_cannot_edit_posted_invoice(self):
    invoice = Invoice.objects.create(...)
    invoice.status = InvoiceStatus.POSTED
    invoice.save()
    
    # Try to change
    invoice.total_gross = Decimal("999.99")
    
    with self.assertRaises(ValidationError):
        invoice.save()
```

---

## Common Patterns

### 1. Safe Status Transition
```python
def post_invoice_safely(invoice_id):
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        invoice.status = InvoiceStatus.POSTED
        invoice.save()  # Signal validates
        return True, "Posted successfully"
    except ValidationError as e:
        return False, str(e)
```

### 2. Reversal Workflow
```python
@transaction.atomic
def reverse_and_correct(original_id, corrected_data):
    # 1. Reverse (status change allowed)
    original = Invoice.objects.get(id=original_id)
    reversal = reverse_posted_invoice(original_id)
    
    # 2. Create corrected (new invoice, no restrictions)
    corrected = Invoice.objects.create(**corrected_data)
    corrected.status = InvoiceStatus.POSTED
    corrected.save()
    
    return reversal, corrected
```

### 3. Bulk Operations Safety
```python
def bulk_update_draft_invoices(invoice_ids, **updates):
    """Only updates DRAFT invoices (skip POSTED)"""
    drafts = Invoice.objects.filter(
        id__in=invoice_ids,
        status=InvoiceStatus.DRAFT  # Exclude POSTED
    )
    drafts.update(**updates)  # Safe - no POSTED invoices
```

---

## Best Practices

### 1. Never Bypass Signals
❌ **DON'T:**
```python
Invoice.objects.filter(id=1).update(status='DRAFT')  # Bypasses signals!
```

✅ **DO:**
```python
invoice = Invoice.objects.get(id=1)
invoice.status = InvoiceStatus.DRAFT
invoice.save()  # Triggers signals
```

**Why:** `.update()` is a SQL UPDATE that skips Django signals

### 2. Use Reversals, Not Edits
❌ **DON'T:** Try to edit posted invoices  
✅ **DO:** Create reversals and new invoices

### 3. Validate Before Posting
✅ **DO:** Check validation in UI before posting
```python
def can_post_invoice(invoice):
    if invoice.lines.count() == 0:
        return False, "No lines"
    if invoice.lines.filter(account__isnull=True).exists():
        return False, "Missing accounts"
    return True, "Can post"
```

### 4. Test Signal Behavior
✅ **DO:** Write tests for all signal paths
```python
# Test posting validation
# Test read-only enforcement
# Test status transitions
```

### 5. Handle ValidationError in API
✅ **DO:** Catch and return user-friendly errors
```python
try:
    invoice.status = InvoiceStatus.POSTED
    invoice.save()
except ValidationError as e:
    return Response(
        {"error": str(e)},
        status=status.HTTP_400_BAD_REQUEST
    )
```

---

## Signal Flow Diagram

```
User Action: invoice.save()
        ↓
Django ORM: pre_save signal
        ↓
┌───────────────────────────────┐
│ validate_invoice_posting       │
│ - Check for lines             │
│ - Check accounts/taxes        │
│ - Check totals > 0            │
│ - Normalize header totals     │
└───────────────────────────────┘
        ↓
┌───────────────────────────────┐
│ block_edit_posted_invoice     │
│ - Check if old status=POSTED  │
│ - Block protected field edits │
│ - Allow status changes        │
└───────────────────────────────┘
        ↓
Database: INSERT/UPDATE
        ↓
Success or ValidationError raised
```

---

## Debugging Signals

### Enable Signal Logging
```python
import logging
logger = logging.getLogger(__name__)

@receiver(pre_save, sender='finance.Invoice')
def validate_invoice_posting(sender, instance, **kwargs):
    logger.info(f"Validating invoice {instance.id}, status: {instance.status}")
    # ... validation logic
```

### Check Signal Registration
```python
from django.db.models.signals import pre_save
from finance.models import Invoice

# See all receivers
receivers = pre_save._live_receivers(Invoice)
print(f"Registered receivers: {len(receivers)}")
```

### Temporarily Disable Signals (Testing Only)
```python
from django.db.models import signals

# Disconnect
signals.pre_save.disconnect(validate_invoice_posting, sender=Invoice)

# Do something without signals
invoice.save()

# Reconnect
signals.pre_save.connect(validate_invoice_posting, sender=Invoice)
```

---

## Comparison with Triggers

| Feature | Django Signals | PostgreSQL Triggers |
|---------|---------------|-------------------|
| Database Support | ✅ All backends | ❌ PostgreSQL only |
| Language | Python | PL/pgSQL |
| Debugging | ✅ Easy | ❌ Difficult |
| Version Control | ✅ In code | ⚠️ Migration files |
| Testing | ✅ Standard tests | ❌ Special setup |
| Bypass Risk | ⚠️ .update() bypasses | ✅ No bypass |

**When to Use Signals:** Most cases (database agnostic)  
**When to Use Triggers:** Critical data integrity on PostgreSQL only

---

## Conclusion

The Finance signals provide:

✅ **Validation:** Pre-posting checks for data completeness  
✅ **Read-only Enforcement:** Prevents modification of posted documents  
✅ **Data Integrity:** Normalizes header totals to match lines  
✅ **Audit Trail:** Immutable financial records  
✅ **Database Agnostic:** Works on SQLite, PostgreSQL, MySQL, etc.  
✅ **Centralized Logic:** Business rules in one place  
✅ **Automatic:** No manual validation needed  
✅ **Testable:** Standard Django test framework  

The signals ensure that posted invoices remain immutable and that only valid data gets posted to the General Ledger, maintaining accounting integrity and compliance requirements.

---

**Last Updated:** October 13, 2025  
**Framework:** Django 4.x+  
**Python Version:** 3.10+  
**Pattern:** Observer Pattern (Django Signals)

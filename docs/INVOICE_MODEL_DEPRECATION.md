# Invoice Model Deprecation Notice

**Date:** November 16, 2025  
**Status:** ✅ COMPLETED

---

## Summary

The legacy `finance.Invoice` model has been officially **DEPRECATED** and marked for removal in future versions.

## What Changed

### Deprecated Models (DO NOT USE)
- ❌ `finance.Invoice` 
- ❌ `finance.InvoiceLine`
- ❌ `finance.InvoiceStatus`
- ❌ `finance.TaxCode`
- ❌ `finance.LockOnPostedMixin`

### Current Models (USE THESE)
- ✅ `ar.ARInvoice` - For customer invoices (Accounts Receivable)
- ✅ `ar.InvoiceGLLine` - For invoice line items
- ✅ `ap.APInvoice` - For supplier invoices (Accounts Payable)
- ✅ `core.TaxRate` - For tax codes

---

## Why This Change?

1. **Duplicate Implementation**: Two separate invoice systems existed causing confusion
2. **No Data in Legacy System**: `finance.Invoice` table had **0 records**
3. **Active AR System**: `ar.ARInvoice` has **11 records** and is being actively used
4. **Better Architecture**: AR/AP separation is clearer and more maintainable

---

## What Was Done

### 1. Added Deprecation Warnings
- Updated `finance/models.py` with clear deprecation comments
- Added warning banners to all deprecated classes
- Included docstrings explaining which models to use instead

### 2. Updated Signal Handlers
- Modified `finance/signals.py` to include deprecation notices
- Added warnings when deprecated models are used
- Kept functionality intact for backward compatibility

### 3. Updated Management Commands
- Modified `finance/management/commands/validate_invoices.py`
- Added deprecation notice to command help text
- Command still works but warns users

### 4. Documentation
- Created this deprecation notice
- Updated inline code comments
- No breaking changes - existing code continues to work

---

## Migration Guide

### If you're using `finance.Invoice`:

**OLD CODE (Don't use):**
```python
from finance.models import Invoice, InvoiceLine

invoice = Invoice.objects.create(
    customer=customer,
    invoice_no="INV-001",
    currency="USD"
)
```

**NEW CODE (Use this):**
```python
from ar.models import ARInvoice, InvoiceGLLine

invoice = ARInvoice.objects.create(
    customer=customer,
    invoice_number="INV-001",
    currency=currency_obj,
    # ... other fields
)
```

### Key Differences:

| Legacy (finance.Invoice) | Current (ar.ARInvoice) |
|-------------------------|------------------------|
| `invoice_no` (CharField) | `invoice_number` (CharField) |
| `currency` (CharField) | `currency` (ForeignKey to Currency) |
| `InvoiceLine` model | `InvoiceGLLine` model |
| No GL integration | Full GL journal posting |
| Basic status (DRAFT/POSTED) | Full approval workflow |

---

## Database Status

- `finance_invoice` table: **0 records**
- `ar_arinvoice` table: **11 records** ✅ (Active)
- `ap_apinvoice` table: In use ✅

The deprecated tables will remain in the database for backward compatibility but should not be used for new development.

---

## Timeline

### ✅ Phase 1 (COMPLETED - Nov 16, 2025)
- Mark models as deprecated
- Add documentation
- Add warnings to signals
- No breaking changes

### 📅 Phase 2 (Future - Optional)
- Create migration to remove deprecated models
- Drop `finance_invoice` and related tables
- Remove signal handlers
- **Only do this after confirming no external dependencies**

---

## API Impact

### Finance APIs Still Available:
- ✅ `/api/finance/journal-entries/` - Still active
- ✅ `/api/finance/bank-accounts/` - Still active
- ✅ `/api/finance/corporate-tax/` - Still active

### Deprecated APIs (if any exist):
- ❌ `/api/finance/invoices/` - Use `/api/ar/invoices/` instead

---

## For Developers

### When writing new code:
1. **DO NOT** import from `finance.models.Invoice`
2. **DO** use `ar.ARInvoice` for customer invoices
3. **DO** use `ap.APInvoice` for supplier invoices
4. **DO** use `finance.JournalEntry` for GL entries (this is NOT deprecated)

### When maintaining existing code:
- Legacy code using `finance.Invoice` will continue to work
- You will see `DeprecationWarning` messages
- Plan to migrate to `ar.ARInvoice` when refactoring

---

## Testing Results

```bash
✓ Django system check: PASSED (no issues)
✓ ar.ARInvoice: 11 records (ACTIVE)
✓ finance.Invoice: 0 records (DEPRECATED)
✓ All migrations applied successfully
✓ Server starts without errors
```

---

## Questions?

If you need help migrating from the old Invoice model to the new one:

1. Check `ar/models.py` for the ARInvoice model structure
2. Check `ar/api.py` for API endpoints
3. Check `ar/serializers.py` for data format
4. See examples in `postman_collections/2_AR_Invoices_and_Payments.json`

---

## Related Documentation

- See: `docs/2_CURRENT_PROBLEMS.md` (Problem #3)
- See: `docs/1_SIMPLE_PROJECT_EXPLANATION.md`
- See: `ar/README.md` (if exists)

---

**Status:** ✅ Problem #3 SOLVED - Duplicate Invoice models issue resolved

# Invoice Pages Loading Fix

## Problem
AR and AP invoice pages were failing to load with the following error:
```
AttributeError: "Cannot find 'payments' on ARInvoice object, 'payments' is an invalid parameter to prefetch_related()"
```

## Root Cause
The ViewSet queries and service functions were using incorrect relationship names to access payment information:

1. **ViewSet Issue**: `ARInvoiceViewSet` and `APInvoiceViewSet` were trying to prefetch a non-existent `'payments'` relation
2. **Services Issue**: `ar_totals()` and `ap_totals()` functions were trying to access `invoice.payments.all()` which doesn't exist

## Solution

### 1. Fixed ViewSet Queries
**File**: `finance/api.py`

**Before**:
```python
class ARInvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = ARInvoiceSerializer
    queryset = ARInvoice.objects.select_related('customer', 'currency').prefetch_related('items', 'items__tax_rate', 'payments')
```

**After**:
```python
class ARInvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = ARInvoiceSerializer
    queryset = ARInvoice.objects.select_related('customer', 'currency').prefetch_related('items', 'items__tax_rate')
```

Same fix applied to `APInvoiceViewSet`.

### 2. Fixed Payment Calculations
**File**: `finance/services.py`

**Before**:
```python
def ar_totals(invoice: ARInvoice) -> dict:
   # ... calculation code ...
   paid = sum((p.amount for p in invoice.payments.all()), start=Decimal("0"))
   return {"subtotal": q2(subtotal), "tax": q2(tax), "total": q2(total), "paid": q2(paid), "balance": q2(total - paid)}
```

**After**:
```python
def ar_totals(invoice: ARInvoice) -> dict:
   # ... calculation code ...
   # Get paid amount from payment allocations (reverse relation: payment_allocations)
   paid = sum((alloc.amount for alloc in invoice.payment_allocations.all()), start=Decimal("0"))
   return {"subtotal": q2(subtotal), "tax": q2(tax), "total": q2(total), "paid": q2(paid), "balance": q2(total - paid)}
```

**Before** (AP):
```python
def ap_totals(invoice: APInvoice) -> dict:
   # ... calculation code ...
   paid = sum((p.amount for p in invoice.payments.all()), start=Decimal("0"))
   return {"subtotal": q2(subtotal), "tax": q2(tax), "total": q2(total - paid)}  # Missing paid and balance!
```

**After** (AP):
```python
def ap_totals(invoice: APInvoice) -> dict:
   # ... calculation code ...
   # Get paid amount from payment allocations (reverse relation: payment_allocations)
   paid = sum((alloc.amount for alloc in invoice.payment_allocations.all()), start=Decimal("0"))
   return {"subtotal": q2(subtotal), "tax": q2(tax), "total": q2(total), "paid": q2(paid), "balance": q2(total - paid)}
```

## Understanding the Relationships

### Invoice → Payment Relationship
The relationship is **NOT direct**. It goes through allocation tables:

```
ARInvoice ←→ ARPaymentAllocation ←→ ARPayment
APInvoice ←→ APPaymentAllocation ←→ APPayment
```

### Model Definitions
**From `ar/models.py`**:
```python
class ARPaymentAllocation(models.Model):
    payment = models.ForeignKey(ARPayment, related_name="allocations", on_delete=models.CASCADE)
    invoice = models.ForeignKey(ARInvoice, related_name="payment_allocations", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    # ...
```

**From `ap/models.py`**:
```python
class APPaymentAllocation(models.Model):
    payment = models.ForeignKey(APPayment, related_name="allocations", on_delete=models.CASCADE)
    invoice = models.ForeignKey(APInvoice, related_name="payment_allocations", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    # ...
```

### Correct Reverse Relationship Names
- From ARInvoice to allocations: `invoice.payment_allocations.all()`
- From APInvoice to allocations: `invoice.payment_allocations.all()`
- From ARPayment to allocations: `payment.allocations.all()`
- From APPayment to allocations: `payment.allocations.all()`

## Additional Fix in AP Totals
The `ap_totals()` function was also missing the `paid` and `balance` fields in its return dictionary. This has been corrected to match the `ar_totals()` function structure.

## Testing
After applying the fixes, the API endpoints work correctly:

```bash
# AR Invoices API - Returns complete data
GET http://127.0.0.1:8000/api/ar/invoices/

# AP Invoices API - Returns complete data
GET http://127.0.0.1:8000/api/ap/invoices/
```

## Status
✅ **FIXED** - Invoice pages now load successfully in the frontend
- AR invoices page: `http://localhost:3001/ar/invoices`
- AP invoices page: `http://localhost:3001/ap/invoices`

## Files Modified
1. `finance/api.py` - Removed invalid `'payments'` prefetch from both ViewSets
2. `finance/services.py` - Fixed payment calculations in both `ar_totals()` and `ap_totals()` functions

## Impact
This fix ensures:
- Invoice list pages load without errors
- Payment allocations are correctly calculated
- Paid amounts and balances display accurately
- Both AR and AP invoices work consistently

---

**Date**: October 15, 2025
**Fixed By**: GitHub Copilot
**Related Features**: Payment Allocations, Invoice Management

# Tax Calculation and Currency Conversion Logic

## Overview
This document explains the correct order of operations for calculating tax and converting currencies in multi-currency invoices.

## ✅ Correct Flow: Tax THEN Exchange

### Order of Operations
```
1. Calculate line items in INVOICE CURRENCY
2. Calculate TAX in INVOICE CURRENCY  
3. Calculate TOTAL (subtotal + tax) in INVOICE CURRENCY
4. Convert TOTAL to BASE CURRENCY using exchange rate
```

### Why This Order Matters

**Tax Calculation in Invoice Currency:**
- Tax rates are based on the country's local regulations
- Tax should be calculated on the **original invoice currency** amounts
- Example: A USD 100 invoice with 5% UAE VAT = USD 105 total
- This USD 105 is then converted to AED at the exchange rate

**Incorrect Approach (Convert Then Tax):**
```
❌ WRONG:
1. Invoice: USD 100
2. Convert to AED: 100 × 3.67 = AED 367
3. Apply 5% VAT: 367 × 1.05 = AED 385.35

This is INCORRECT because tax should apply to USD amounts first!
```

**Correct Approach (Tax Then Convert):**
```
✅ CORRECT:
1. Invoice: USD 100
2. Apply 5% VAT: 100 × 1.05 = USD 105
3. Convert to AED: 105 × 3.67 = AED 385.35

Tax is calculated on the original currency before conversion.
```

## Implementation in Code

### AR Invoice Posting (`gl_post_from_ar_balanced`)

```python
# Step 1: Calculate totals in INVOICE CURRENCY
totals = ar_totals(inv)  # Calculates in invoice currency
subtotal = totals["subtotal"]  # e.g., USD 100.00
tax = totals["tax"]            # e.g., USD 5.00 (5%)
invoice_total = subtotal + tax # e.g., USD 105.00

# Step 2: Get exchange rate
exchange_rate = get_exchange_rate(
    from_currency=inv.currency,  # USD
    to_currency=base_currency,   # AED
    rate_date=inv.date
)  # e.g., 3.67

# Step 3: Convert TOTAL (with tax) to base currency
total_base = convert_amount(
    invoice_total,    # USD 105.00
    inv.currency,     # USD
    base_currency,    # AED
    inv.date
)  # = AED 385.35

# Step 4: Convert components for GL breakdown
subtotal_base = convert_amount(subtotal, ...)  # AED 367.00
tax_base = total_base - subtotal_base          # AED 18.35
```

### AP Invoice Posting (`gl_post_from_ap_balanced`)

Same logic applies for AP invoices:
```python
# Calculate in invoice currency
totals = ap_totals(inv)
invoice_total = subtotal + tax

# Convert total with tax
total_base = convert_amount(invoice_total, ...)
subtotal_base = convert_amount(subtotal, ...)
tax_base = total_base - subtotal_base  # Ensures balance
```

## Real-World Example

### Scenario: USD Invoice in UAE

**Invoice Details:**
- Customer: US Company
- Invoice Currency: USD
- Base Currency: AED (UAE Dirham)
- Date: October 14, 2025
- Exchange Rate: 1 USD = 3.67 AED
- Tax: UAE VAT 5%

**Line Items:**
```
Item 1: 10 units × $50 = $500.00
Item 2: 5 units × $100 = $500.00
---------------------------------
Subtotal:              $1,000.00
Tax (5%):                 $50.00
---------------------------------
Total:                 $1,050.00
```

**Currency Conversion to AED:**
```
Subtotal: $1,000 × 3.67 = AED 3,670.00
Tax:         $50 × 3.67 = AED 183.50
Total:    $1,050 × 3.67 = AED 3,853.50
```

**GL Posting (in AED - Base Currency):**
```
DR  Accounts Receivable    AED 3,853.50
    CR  Revenue                         AED 3,670.00
    CR  VAT Payable                     AED 183.50
```

### Scenario: SAR Invoice in UAE

**Invoice Details:**
- Customer: Saudi Company  
- Invoice Currency: SAR
- Base Currency: AED
- Exchange Rate: 1 SAR = 0.98 AED
- Tax: KSA VAT 15%

**Line Items:**
```
Item: 100 units × SAR 20 = SAR 2,000.00
---------------------------------
Subtotal:              SAR 2,000.00
Tax (15%):               SAR 300.00
---------------------------------
Total:                 SAR 2,300.00
```

**Currency Conversion to AED:**
```
Total: SAR 2,300 × 0.98 = AED 2,254.00
Subtotal: SAR 2,000 × 0.98 = AED 1,960.00
Tax: SAR 300 × 0.98 = AED 294.00
```

## Tax Rate Resolution

### Tax is Applied in Invoice Currency

The `line_rate()` function determines the tax rate:

```python
def line_rate(item, inv_date) -> Decimal:
    """
    Priority:
    1. Explicit TaxRate FK on line item
    2. Country + Category lookup for invoice date
    3. Default to 0%
    """
    if item.tax_rate:
        return Decimal(item.tax_rate.rate)  # e.g., 5
    
    if item.tax_country and item.tax_category:
        return resolve_tax_rate_for_date(
            item.tax_country, 
            item.tax_category, 
            inv_date
        )
    
    return Decimal("0.0")
```

### Tax Calculation Per Line

```python
def amount_with_tax(qty, price, rate):
    """
    Calculate line totals in original currency.
    Tax rate is a percentage (e.g., 5 = 5%).
    """
    subtotal = Decimal(qty) * Decimal(price)
    tax = subtotal * (Decimal(rate) / Decimal("100"))
    total = subtotal + tax
    return q2(subtotal), q2(tax), q2(total)
```

### Invoice Totals

```python
def ar_totals(invoice: ARInvoice) -> dict:
    """
    Sum all line items in INVOICE CURRENCY.
    Tax is calculated per line in invoice currency.
    """
    subtotal = Decimal("0")
    tax = Decimal("0")
    total = Decimal("0")
    
    for item in invoice.items.all():
        rate = line_rate(item, invoice.date)
        s, t, tot = amount_with_tax(
            item.quantity, 
            item.unit_price, 
            rate
        )
        subtotal += s
        tax += t
        total += tot
    
    return {
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        ...
    }
```

## Benefits of This Approach

### 1. **Accounting Accuracy**
- Tax is calculated on the **actual transaction currency**
- Follows international accounting standards (IAS 21)
- Prevents rounding errors from converting first

### 2. **Tax Compliance**
- Tax authorities expect tax calculated on invoice currency
- Audit trail shows correct tax calculation
- Meets VAT/GST reporting requirements

### 3. **Multi-Currency Support**
- Works consistently across all currency pairs
- Exchange rate applied to final total
- Clear separation of tax vs FX effects

### 4. **Rounding Precision**
- Single conversion point (total with tax)
- Minimizes cumulative rounding errors
- GL entries always balance

## Edge Cases Handled

### Same Currency (No Conversion)
```python
if needs_conversion:
    # Convert from invoice to base currency
    total_base = convert_amount(invoice_total, ...)
else:
    # Same currency - no conversion needed
    exchange_rate = Decimal('1.000000')
    total_base = invoice_total
    subtotal_base = subtotal
    tax_base = tax
```

### Zero Tax Items
```python
# Some items may have 0% tax (exempt, zero-rated)
# Tax calculation handles this naturally:
tax = subtotal × (0 / 100) = 0
```

### Mixed Tax Rates
```python
# Each line item can have different tax rate
# Totals accumulate correctly:
Item 1: $100 × 1.05 = $105.00 (5% VAT)
Item 2: $200 × 1.00 = $200.00 (0% exempt)
Total: $305.00 → Convert to base currency
```

### Tax Balance Derivation
```python
# To ensure GL balance, tax_base is derived:
total_base = convert_amount(invoice_total, ...)
subtotal_base = convert_amount(subtotal, ...)
tax_base = total_base - subtotal_base  

# This prevents rounding mismatches like:
# total_base = 3853.50
# subtotal_base + tax_base might be 3853.51 (rounding error)
```

## Testing Scenarios

### Test 1: USD to AED with 5% VAT
```python
invoice.currency = USD
invoice.date = '2025-10-14'
items = [
    {qty: 10, price: 100.00, tax_rate: 5%}
]

Expected:
- Invoice Total: USD 1,050.00
- Exchange Rate: 3.67
- Base Total: AED 3,853.50
- Tax (base): AED 183.50
```

### Test 2: SAR to AED with 15% VAT
```python
invoice.currency = SAR
items = [
    {qty: 5, price: 200.00, tax_rate: 15%}
]

Expected:
- Invoice Total: SAR 1,150.00
- Exchange Rate: 0.98
- Base Total: AED 1,127.00
- Tax (base): AED 147.00
```

### Test 3: Same Currency (AED)
```python
invoice.currency = AED
base_currency = AED

Expected:
- No conversion
- Exchange Rate: 1.000000
- Amounts same in invoice and base
```

## Key Changes Made

### Before (Potential Issue)
```python
# Convert subtotal and tax separately
subtotal_base = convert_amount(subtotal, ...)
tax_base = convert_amount(tax, ...)
total_base = subtotal_base + tax_base  # Could have rounding error
```

### After (Correct)
```python
# Convert total first, derive tax to ensure balance
total_base = convert_amount(invoice_total, ...)  # Total with tax
subtotal_base = convert_amount(subtotal, ...)
tax_base = total_base - subtotal_base  # Derived for accuracy
```

## Summary

✅ **Tax is calculated in invoice currency FIRST**  
✅ **Total (with tax) is then converted to base currency**  
✅ **GL posting uses base currency amounts**  
✅ **Exchange rate stored on invoice for audit**  
✅ **Tax_base derived to ensure GL balance**  

This approach ensures:
- **Tax compliance** with local regulations
- **Accounting accuracy** per IAS 21
- **Audit trail** with clear currency conversion
- **GL balance** without rounding errors

---

**Status:** ✅ IMPLEMENTED  
**Date:** October 14, 2025  
**Applies To:** AR and AP invoice posting  
**Related Files:**
- `finance/services.py` - `gl_post_from_ar_balanced()`, `gl_post_from_ap_balanced()`
- `finance/fx_services.py` - Currency conversion functions
- `ar/models.py`, `ap/models.py` - Invoice models with exchange_rate field

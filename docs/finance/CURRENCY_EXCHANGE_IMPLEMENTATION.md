# Currency Exchange Feature Implementation Plan

**Date:** October 14, 2025  
**Feature:** Automatic currency conversion when posting invoices to GL

---

## 📋 Requirements

When posting an AR/AP invoice:
1. **Invoice Currency** ≠ **Base Currency** → Convert amounts
2. Use exchange rate from `core.ExchangeRate` table
3. Post GL entries in **base currency**
4. Store original currency and rate for audit trail
5. Support FX gain/loss on future payments

---

## 🗄️ Database Schema

### Existing Tables:
```sql
-- core.ExchangeRate
from_currency_id  → Currency FK
to_currency_id    → Currency FK  
rate_date         → Date
rate              → Decimal(18,6)
rate_type         → 'SPOT', 'AVERAGE', 'FIXED', 'CLOSING'
is_active         → Boolean

-- core.Currency
code              → 'USD', 'AED', 'EUR', etc.
is_base           → Boolean (one should be TRUE)

-- ar.ARInvoice / ap.APInvoice
currency_id       → Currency FK (invoice currency)
```

---

## 🔧 Implementation Steps

### Step 1: Add exchange rate tracking to invoices
Add fields to track the rate used at posting time:
- `exchange_rate` - Decimal(18,6) - Rate used for conversion
- `base_currency_total` - Decimal(14,2) - Total in base currency

### Step 2: Modify posting functions
Update `gl_post_from_ar_balanced()` and `gl_post_from_ap_balanced()`:
1. Check if invoice currency = base currency
2. If different, look up exchange rate
3. Convert all amounts to base currency
4. Store conversion rate on invoice
5. Create journal lines in base currency

### Step 3: Add FX gain/loss on payments
When payment is received in different currency:
1. Compare invoice rate vs payment rate
2. Calculate FX gain/loss
3. Post additional GL lines

---

## 💻 Code Implementation

### 1. Add fields to ARInvoice model
```python
# In ar/models.py
class ARInvoice(models.Model):
    # ... existing fields ...
    
    # NEW: FX tracking
    exchange_rate = models.DecimalField(
        max_digits=18, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Exchange rate used when posting (invoice currency to base currency)"
    )
    base_currency_total = models.DecimalField(
        max_digits=14, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Total amount in base currency"
    )
```

### 2. Add fields to APInvoice model
```python
# In ap/models.py
class APInvoice(models.Model):
    # ... existing fields ...
    
    # NEW: FX tracking
    exchange_rate = models.DecimalField(
        max_digits=18, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Exchange rate used when posting (invoice currency to base currency)"
    )
    base_currency_total = models.DecimalField(
        max_digits=14, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Total amount in base currency"
    )
```

### 3. Update gl_post_from_ar_balanced()
```python
# In finance/services.py
from finance.fx_services import get_base_currency, get_exchange_rate, convert_amount

@transaction.atomic
def gl_post_from_ar_balanced(invoice: ARInvoice):
    """
    Post AR invoice to GL with automatic currency conversion.
    If invoice currency differs from base currency, converts amounts using exchange rate.
    """
    inv = ARInvoice.objects.select_for_update().get(pk=invoice.pk)

    if inv.gl_journal_id:
        return inv.gl_journal, False

    # Validate invoice has items
    item_count = inv.items.count()
    if item_count == 0:
        raise ValueError(f"Cannot post invoice {inv.number}: Invoice has no line items")

    # Calculate totals in invoice currency
    totals = ar_totals(inv)
    subtotal = totals["subtotal"]
    tax = totals["tax"]
    invoice_total = q2(subtotal + tax)
    
    if invoice_total == Decimal("0.00"):
        raise ValueError(f"Cannot post invoice {inv.number}: Total amount is zero")

    # Get base currency
    base_currency = get_base_currency()
    
    # Determine if currency conversion is needed
    needs_conversion = inv.currency.id != base_currency.id
    
    if needs_conversion:
        # Get exchange rate for invoice date
        exchange_rate = get_exchange_rate(
            from_currency=inv.currency,
            to_currency=base_currency,
            rate_date=inv.date,
            rate_type="SPOT"
        )
        
        # Convert amounts to base currency
        subtotal_base = convert_amount(subtotal, inv.currency, base_currency, inv.date)
        tax_base = convert_amount(tax, inv.currency, base_currency, inv.date)
        total_base = q2(subtotal_base + tax_base)
        
        # Store exchange rate and base currency total
        inv.exchange_rate = exchange_rate
        inv.base_currency_total = total_base
    else:
        # Same currency - no conversion needed
        exchange_rate = Decimal('1.000000')
        subtotal_base = subtotal
        tax_base = tax
        total_base = invoice_total
        inv.exchange_rate = exchange_rate
        inv.base_currency_total = total_base

    # Create journal entry in BASE CURRENCY
    je = _create_journal_entry(
        organization=getattr(inv, "organization", None),
        date=inv.date,
        currency=base_currency,  # Always post in base currency
        memo=f"AR Post {inv.number} ({inv.currency.code}→{base_currency.code} @ {exchange_rate})" if needs_conversion else f"AR Post {inv.number}",
    )
    
    # Create journal lines in base currency
    JournalLine.objects.create(entry=je, account=_acct("AR"), debit=total_base)
    
    if subtotal_base:
        JournalLine.objects.create(entry=je, account=_acct("REV"), credit=subtotal_base)
    
    if tax_base:
        JournalLine.objects.create(entry=je, account=_acct("VAT_OUT"), credit=tax_base)

    post_entry(je)

    # Update invoice
    inv.gl_journal = je
    if hasattr(inv, "status"):
        inv.status = getattr(inv, "POSTED", getattr(inv, "status", "POSTED"))
    inv.posted_at = timezone.now()
    
    # Save with new fields
    inv.save(update_fields=["gl_journal", "posted_at", "status", "exchange_rate", "base_currency_total"])

    return je, True
```

### 4. Update gl_post_from_ap_balanced()
```python
@transaction.atomic
def gl_post_from_ap_balanced(invoice: APInvoice):
    """
    Post AP invoice to GL with automatic currency conversion.
    If invoice currency differs from base currency, converts amounts using exchange rate.
    """
    inv = APInvoice.objects.select_for_update().get(pk=invoice.pk)

    if inv.gl_journal_id:
        return inv.gl_journal, False

    item_count = inv.items.count()
    if item_count == 0:
        raise ValueError(f"Cannot post invoice {inv.number}: Invoice has no line items")

    # Calculate totals in invoice currency
    totals = ap_totals(inv)
    subtotal = totals["subtotal"]
    tax = totals["tax"]
    invoice_total = q2(subtotal + tax)
    
    if invoice_total == Decimal("0.00"):
        raise ValueError(f"Cannot post invoice {inv.number}: Total amount is zero")

    # Get base currency
    base_currency = get_base_currency()
    
    # Determine if currency conversion is needed
    needs_conversion = inv.currency.id != base_currency.id
    
    if needs_conversion:
        # Get exchange rate
        exchange_rate = get_exchange_rate(
            from_currency=inv.currency,
            to_currency=base_currency,
            rate_date=inv.date,
            rate_type="SPOT"
        )
        
        # Convert amounts
        subtotal_base = convert_amount(subtotal, inv.currency, base_currency, inv.date)
        tax_base = convert_amount(tax, inv.currency, base_currency, inv.date)
        total_base = q2(subtotal_base + tax_base)
        
        inv.exchange_rate = exchange_rate
        inv.base_currency_total = total_base
    else:
        exchange_rate = Decimal('1.000000')
        subtotal_base = subtotal
        tax_base = tax
        total_base = invoice_total
        inv.exchange_rate = exchange_rate
        inv.base_currency_total = total_base

    # Create journal entry in BASE CURRENCY
    je = _create_journal_entry(
        organization=getattr(inv, "organization", None),
        date=inv.date,
        currency=base_currency,
        memo=f"AP Post {inv.number} ({inv.currency.code}→{base_currency.code} @ {exchange_rate})" if needs_conversion else f"AP Post {inv.number}",
    )
    
    # Create journal lines in base currency
    if subtotal_base:
        JournalLine.objects.create(entry=je, account=_acct("EXP"), debit=subtotal_base)
    
    if tax_base:
        JournalLine.objects.create(entry=je, account=_acct("VAT_IN"), debit=tax_base)
    
    JournalLine.objects.create(entry=je, account=_acct("AP"), credit=total_base)

    post_entry(je)

    inv.gl_journal = je
    if hasattr(inv, "status"):
        inv.status = getattr(inv, "POSTED", getattr(inv, "status", "POSTED"))
    inv.posted_at = timezone.now()
    
    inv.save(update_fields=["gl_journal", "posted_at", "status", "exchange_rate", "base_currency_total"])

    return je, True
```

---

## 📊 Example Scenarios

### Scenario 1: USD Invoice with AED Base Currency

**Setup:**
- Base Currency: AED
- Invoice Currency: USD
- Invoice Total: $1,000 USD
- Exchange Rate: 1 USD = 3.67 AED (from ExchangeRate table)

**Invoice Posting:**
```
DR  Accounts Receivable (AED)    3,670.00
    CR  Sales Revenue (AED)              3,670.00

Memo: "AR Post INV-001 (USD→AED @ 3.670000)"
```

**Stored on Invoice:**
- `exchange_rate` = 3.670000
- `base_currency_total` = 3670.00
- `currency` = USD (FK)

### Scenario 2: Same Currency (No Conversion)

**Setup:**
- Base Currency: AED
- Invoice Currency: AED  
- Invoice Total: 1,000 AED

**Invoice Posting:**
```
DR  Accounts Receivable (AED)    1,000.00
    CR  Sales Revenue (AED)              1,000.00

Memo: "AR Post INV-002"
```

**Stored on Invoice:**
- `exchange_rate` = 1.000000
- `base_currency_total` = 1000.00
- `currency` = AED (FK)

---

## 🔄 Migration Required

```bash
python manage.py makemigrations
python manage.py migrate
```

This will add:
- `ar_arinvoice.exchange_rate`
- `ar_arinvoice.base_currency_total`
- `ap_apinvoice.exchange_rate`
- `ap_apinvoice.base_currency_total`

---

## ✅ Testing Steps

1. **Set Base Currency:**
   ```python
   aed = Currency.objects.get(code='AED')
   aed.is_base = True
   aed.save()
   ```

2. **Create Exchange Rates:**
   ```python
   from finance.fx_services import create_exchange_rate
   from decimal import Decimal
   from datetime import date
   
   # USD to AED
   create_exchange_rate('USD', 'AED', Decimal('3.67'), date.today())
   
   # EUR to AED
   create_exchange_rate('EUR', 'AED', Decimal('4.02'), date.today())
   ```

3. **Create Invoice in Foreign Currency:**
   ```python
   usd = Currency.objects.get(code='USD')
   customer = Customer.objects.first()
   
   invoice = ARInvoice.objects.create(
       customer=customer,
       number='INV-TEST-001',
       date=date.today(),
       due_date=date.today(),
       currency=usd  # Foreign currency
   )
   
   ARItem.objects.create(
       invoice=invoice,
       description='Test Item',
       quantity=1,
       unit_price=1000
   )
   ```

4. **Post Invoice:**
   ```python
   from finance.services import gl_post_from_ar_balanced
   
   je, created = gl_post_from_ar_balanced(invoice)
   
   # Check journal entry
   print(f"JE Currency: {je.currency.code}")  # Should be AED (base)
   print(f"JE Lines:")
   for line in je.lines.all():
       print(f"  {line.account.code}: DR {line.debit} CR {line.credit}")
   
   # Check invoice
   print(f"Invoice Currency: {invoice.currency.code}")  # USD
   print(f"Exchange Rate: {invoice.exchange_rate}")  # 3.670000
   print(f"Base Total: {invoice.base_currency_total}")  # 3670.00
   ```

---

## 🚀 Next Steps (Future Enhancements)

1. **Payment FX Gain/Loss:**
   - When payment received at different rate
   - Post FX gain/loss to GL

2. **Revaluation:**
   - Period-end unrealized FX on open balances

3. **Multi-Rate Support:**
   - Support AVERAGE, CLOSING rates
   - Monthly average rates for P&L

4. **Reporting:**
   - Show original currency amounts
   - Show base currency amounts
   - FX gain/loss reports

---

**Status:** Ready to implement  
**Files to modify:**
1. `ar/models.py` - Add exchange_rate, base_currency_total
2. `ap/models.py` - Add exchange_rate, base_currency_total
3. `finance/services.py` - Update posting functions
4. Create migration

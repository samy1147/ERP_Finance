# Currency Exchange Feature - Testing Guide

**Date:** October 14, 2025  
**Feature:** Automatic currency conversion for AR/AP invoices

---

## ✅ Implementation Complete

### Files Modified:
1. **`ar/models.py`** - Added `exchange_rate` and `base_currency_total` to ARInvoice
2. **`ap/models.py`** - Added `exchange_rate` and `base_currency_total` to APInvoice
3. **`finance/services.py`** - Updated `gl_post_from_ar_balanced()` and `gl_post_from_ap_balanced()`

### Migrations Created:
- `ar/migrations/0002_arinvoice_base_currency_total_and_more.py`
- `ap/migrations/0002_apinvoice_base_currency_total_and_more.py`

---

## 🚀 Setup Instructions

### Step 1: Apply Migrations

```bash
python manage.py migrate
```

This will add the new fields to the database.

---

### Step 2: Set Base Currency

```python
from core.models import Currency

# Set AED as base currency (or your preferred currency)
aed = Currency.objects.get(code='AED')
aed.is_base = True
aed.save()

# Ensure no other currencies are marked as base
Currency.objects.exclude(code='AED').update(is_base=False)

# Verify
base = Currency.objects.get(is_base=True)
print(f"Base Currency: {base.code} - {base.name}")
```

---

### Step 3: Create Exchange Rates

```python
from finance.fx_services import create_exchange_rate
from decimal import Decimal
from datetime import date

# USD to AED (1 USD = 3.67 AED)
create_exchange_rate(
    from_currency_code='USD',
    to_currency_code='AED',
    rate=Decimal('3.67'),
    rate_date=date(2025, 1, 1),
    rate_type='SPOT',
    source='Central Bank'
)

# EUR to AED (1 EUR = 4.02 AED)
create_exchange_rate(
    from_currency_code='EUR',
    to_currency_code='AED',
    rate=Decimal('4.02'),
    rate_date=date(2025, 1, 1),
    rate_type='SPOT',
    source='Central Bank'
)

# SAR to AED (1 SAR = 0.98 AED)
create_exchange_rate(
    from_currency_code='SAR',
    to_currency_code='AED',
    rate=Decimal('0.98'),
    rate_date=date(2025, 1, 1),
    rate_type='SPOT',
    source='Central Bank'
)

# Verify
from core.models import ExchangeRate
rates = ExchangeRate.objects.all()
for r in rates:
    print(f"{r.from_currency.code}/{r.to_currency.code} = {r.rate} on {r.rate_date}")
```

---

## 🧪 Test Scenarios

### Test 1: Invoice in Base Currency (No Conversion)

```python
from ar.models import Customer, ARInvoice, ARItem
from core.models import Currency
from datetime import date, timedelta

# Get base currency
aed = Currency.objects.get(code='AED')

# Create customer
customer = Customer.objects.create(
    code='CUST-001',
    name='Test Customer AED',
    currency=aed
)

# Create invoice in AED
invoice = ARInvoice.objects.create(
    customer=customer,
    number='INV-AED-001',
    date=date.today(),
    due_date=date.today() + timedelta(days=30),
    currency=aed
)

# Add items
ARItem.objects.create(
    invoice=invoice,
    description='Service Item',
    quantity=1,
    unit_price=1000
)

# Post to GL
from finance.services import gl_post_from_ar_balanced

je, created = gl_post_from_ar_balanced(invoice)

# Verify results
invoice.refresh_from_db()
print(f"\n=== Test 1: Same Currency (AED) ===")
print(f"Invoice Currency: {invoice.currency.code}")
print(f"Exchange Rate: {invoice.exchange_rate}")
print(f"Base Currency Total: {invoice.base_currency_total}")
print(f"Journal Entry Currency: {je.currency.code}")
print(f"Journal Entry Memo: {je.memo}")
print("\nJournal Lines:")
for line in je.lines.all():
    print(f"  {line.account.code} - DR: {line.debit}, CR: {line.credit}")

# Expected Results:
# - exchange_rate = 1.000000
# - base_currency_total = 1000.00
# - JE currency = AED
# - JE memo = "AR Post INV-AED-001"
```

### Test 2: Invoice in Foreign Currency (USD to AED)

```python
from ar.models import Customer, ARInvoice, ARItem
from core.models import Currency
from datetime import date, timedelta

# Get currencies
usd = Currency.objects.get(code='USD')
aed = Currency.objects.get(code='AED')

# Create customer
customer = Customer.objects.create(
    code='CUST-002',
    name='Test Customer USD',
    currency=usd
)

# Create invoice in USD
invoice = ARInvoice.objects.create(
    customer=customer,
    number='INV-USD-001',
    date=date(2025, 1, 15),
    due_date=date(2025, 2, 15),
    currency=usd
)

# Add items (Total: $1,000 USD)
ARItem.objects.create(
    invoice=invoice,
    description='Consulting Service',
    quantity=10,
    unit_price=100
)

# Post to GL
from finance.services import gl_post_from_ar_balanced

je, created = gl_post_from_ar_balanced(invoice)

# Verify results
invoice.refresh_from_db()
print(f"\n=== Test 2: Foreign Currency (USD → AED) ===")
print(f"Invoice Currency: {invoice.currency.code}")
print(f"Invoice Total (USD): $1,000.00")
print(f"Exchange Rate: {invoice.exchange_rate}")
print(f"Base Currency Total (AED): {invoice.base_currency_total}")
print(f"Calculated: 1000 × {invoice.exchange_rate} = {invoice.base_currency_total}")
print(f"Journal Entry Currency: {je.currency.code}")
print(f"Journal Entry Memo: {je.memo}")
print("\nJournal Lines (in AED):")
total_dr = 0
total_cr = 0
for line in je.lines.all():
    print(f"  {line.account.code} - DR: {line.debit}, CR: {line.credit}")
    total_dr += line.debit
    total_cr += line.credit
print(f"Total DR: {total_dr}, Total CR: {total_cr}, Balanced: {total_dr == total_cr}")

# Expected Results:
# - exchange_rate = 3.670000
# - base_currency_total = 3670.00
# - JE currency = AED
# - JE memo = "AR Post INV-USD-001 (USD→AED @ 3.670000)"
# - AR account DR = 3670.00 AED
# - Revenue account CR = 3670.00 AED
```

### Test 3: Invoice with Tax in Foreign Currency

```python
from ar.models import Customer, ARInvoice, ARItem
from core.models import Currency, TaxRate
from datetime import date, timedelta

# Get currencies
eur = Currency.objects.get(code='EUR')

# Get or create tax rate
tax_rate, _ = TaxRate.objects.get_or_create(
    name='VAT 5%',
    rate=5.0,
    country='AE',
    category='STANDARD'
)

# Create customer
customer = Customer.objects.create(
    code='CUST-003',
    name='Test Customer EUR',
    currency=eur
)

# Create invoice in EUR
invoice = ARInvoice.objects.create(
    customer=customer,
    number='INV-EUR-001',
    date=date(2025, 1, 15),
    due_date=date(2025, 2, 15),
    currency=eur
)

# Add items with tax
ARItem.objects.create(
    invoice=invoice,
    description='Software License',
    quantity=1,
    unit_price=1000,
    tax_rate=tax_rate
)

# Calculate expected amounts
# Subtotal: €1,000
# Tax (5%): €50
# Total: €1,050
# Converted at 4.02: 1,050 × 4.02 = 4,221 AED

# Post to GL
from finance.services import gl_post_from_ar_balanced

je, created = gl_post_from_ar_balanced(invoice)

# Verify results
invoice.refresh_from_db()
print(f"\n=== Test 3: Foreign Currency with Tax (EUR → AED) ===")
print(f"Invoice Currency: {invoice.currency.code}")
print(f"Invoice Subtotal (EUR): €1,000.00")
print(f"Invoice Tax (5%): €50.00")
print(f"Invoice Total (EUR): €1,050.00")
print(f"Exchange Rate: {invoice.exchange_rate}")
print(f"Base Currency Total (AED): {invoice.base_currency_total}")
print(f"Journal Entry Currency: {je.currency.code}")
print(f"Journal Entry Memo: {je.memo}")
print("\nJournal Lines (in AED):")
for line in je.lines.all():
    account_name = line.account.name
    print(f"  {line.account.code} ({account_name}) - DR: {line.debit}, CR: {line.credit}")

# Expected Results:
# - exchange_rate = 4.020000
# - base_currency_total = 4221.00 AED (1050 × 4.02)
# - AR account DR = 4221.00 AED
# - Revenue account CR = 4020.00 AED (1000 × 4.02)
# - VAT Out account CR = 201.00 AED (50 × 4.02)
```

### Test 4: AP Invoice in Foreign Currency

```python
from ap.models import Supplier, APInvoice, APItem
from core.models import Currency
from datetime import date, timedelta

# Get currencies
usd = Currency.objects.get(code='USD')

# Create supplier
supplier = Supplier.objects.create(
    code='SUPP-001',
    name='Test Supplier USD',
    currency=usd
)

# Create AP invoice in USD
invoice = APInvoice.objects.create(
    supplier=supplier,
    number='APINV-USD-001',
    date=date(2025, 1, 15),
    due_date=date(2025, 2, 15),
    currency=usd
)

# Add items
APItem.objects.create(
    invoice=invoice,
    description='Office Supplies',
    quantity=5,
    unit_price=200
)

# Post to GL
from finance.services import gl_post_from_ap_balanced

je, created = gl_post_from_ap_balanced(invoice)

# Verify results
invoice.refresh_from_db()
print(f"\n=== Test 4: AP Invoice (USD → AED) ===")
print(f"Invoice Currency: {invoice.currency.code}")
print(f"Invoice Total (USD): $1,000.00")
print(f"Exchange Rate: {invoice.exchange_rate}")
print(f"Base Currency Total (AED): {invoice.base_currency_total}")
print(f"Journal Entry Currency: {je.currency.code}")
print(f"Journal Entry Memo: {je.memo}")
print("\nJournal Lines (in AED):")
for line in je.lines.all():
    print(f"  {line.account.code} - DR: {line.debit}, CR: {line.credit}")

# Expected Results:
# - exchange_rate = 3.670000
# - base_currency_total = 3670.00 AED
# - Expense account DR = 3670.00 AED
# - AP account CR = 3670.00 AED
```

---

## 🔍 Verification Queries

### Check Base Currency
```python
from core.models import Currency
base = Currency.objects.get(is_base=True)
print(f"Base Currency: {base.code} - {base.name}")
```

### Check Exchange Rates
```python
from core.models import ExchangeRate
rates = ExchangeRate.objects.filter(is_active=True).order_by('-rate_date')
for rate in rates:
    print(f"{rate.from_currency.code}/{rate.to_currency.code} = {rate.rate} ({rate.rate_date})")
```

### Check Posted Invoices
```python
from ar.models import ARInvoice

invoices = ARInvoice.objects.filter(status='POSTED')
for inv in invoices:
    print(f"\n{inv.number}:")
    print(f"  Currency: {inv.currency.code}")
    print(f"  Exchange Rate: {inv.exchange_rate}")
    print(f"  Base Total: {inv.base_currency_total}")
    if inv.gl_journal:
        print(f"  JE Currency: {inv.gl_journal.currency.code}")
        print(f"  JE Memo: {inv.gl_journal.memo}")
```

### Check Journal Entries
```python
from finance.models import JournalEntry

entries = JournalEntry.objects.filter(posted=True).order_by('-date')[:5]
for je in entries:
    print(f"\nJE-{je.id} ({je.date}):")
    print(f"  Currency: {je.currency.code}")
    print(f"  Memo: {je.memo}")
    print("  Lines:")
    for line in je.lines.all():
        print(f"    {line.account.code}: DR {line.debit}, CR {line.credit}")
```

---

## ⚠️ Error Handling

### Error 1: No Base Currency Configured
```python
# Error message:
# "No base currency configured. Please set a currency as is_base=True."

# Solution:
from core.models import Currency
currency = Currency.objects.get(code='AED')
currency.is_base = True
currency.save()
```

### Error 2: No Exchange Rate Found
```python
# Error message:
# "No exchange rate found for USD/AED on or before 2025-01-15 (type: SPOT)"

# Solution:
from finance.fx_services import create_exchange_rate
from decimal import Decimal
from datetime import date

create_exchange_rate('USD', 'AED', Decimal('3.67'), date(2025, 1, 15))
```

### Error 3: Multiple Base Currencies
```python
# Error message:
# "Multiple base currencies found. Only one currency should have is_base=True."

# Solution:
from core.models import Currency
# Keep only one as base
Currency.objects.all().update(is_base=False)
aed = Currency.objects.get(code='AED')
aed.is_base = True
aed.save()
```

---

## 📊 Expected Results Summary

| Test | Invoice Currency | Base Currency | Exchange Rate | Original Total | Base Total |
|------|-----------------|---------------|---------------|----------------|------------|
| 1 | AED | AED | 1.000000 | 1,000.00 AED | 1,000.00 AED |
| 2 | USD | AED | 3.670000 | 1,000.00 USD | 3,670.00 AED |
| 3 | EUR | AED | 4.020000 | 1,050.00 EUR | 4,221.00 AED |
| 4 | USD | AED | 3.670000 | 1,000.00 USD | 3,670.00 AED |

---

## ✅ Success Criteria

1. ✅ Migrations applied successfully
2. ✅ Base currency configured
3. ✅ Exchange rates created
4. ✅ Same-currency invoices post correctly (rate = 1.0)
5. ✅ Foreign-currency invoices convert correctly
6. ✅ Journal entries created in base currency
7. ✅ Exchange rate and base total saved on invoice
8. ✅ Journal entry memo shows conversion details
9. ✅ All journal entries remain balanced

---

## 🎯 Next Steps

After successful testing, you can:

1. **Update Frontend** - Display exchange rate and base currency total
2. **Add Reports** - Show FX exposure and conversion summary
3. **Implement Payment FX** - Handle FX gain/loss on payments
4. **Period-End Revaluation** - Unrealized FX on open balances

---

**Status:** ✅ Ready to Test  
**Last Updated:** October 14, 2025

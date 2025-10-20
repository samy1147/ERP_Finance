# Currency Exchange - Quick Start

## 🚀 3 Steps to Enable

### 1️⃣ Run Migration
```bash
python manage.py migrate
```

### 2️⃣ Set Base Currency
```python
from core.models import Currency
Currency.objects.all().update(is_base=False)
aed = Currency.objects.get(code='AED')
aed.is_base = True
aed.save()
```

### 3️⃣ Add Exchange Rates
```python
from finance.fx_services import create_exchange_rate
from decimal import Decimal
from datetime import date

create_exchange_rate('USD', 'AED', Decimal('3.67'), date.today())
create_exchange_rate('EUR', 'AED', Decimal('4.02'), date.today())
```

---

## ✅ Done! Now It Works Automatically

**When you post an invoice:**
- ✅ System checks invoice currency vs base currency
- ✅ If different → looks up exchange rate
- ✅ Converts all amounts to base currency  
- ✅ Posts GL entry in base currency
- ✅ Saves rate & base total on invoice

---

## 📊 Example

**Invoice:** $1,000 USD  
**Rate:** 3.67  
**Result:** 3,670 AED in GL

---

## 🔍 Quick Check

```python
from ar.models import ARInvoice
inv = ARInvoice.objects.filter(status='POSTED').first()
print(f"Rate: {inv.exchange_rate}, Base Total: {inv.base_currency_total}")
```

---

## 📚 Full Docs

- **Summary:** `docs/finance/CURRENCY_EXCHANGE_SUMMARY.md`
- **Testing:** `docs/finance/CURRENCY_EXCHANGE_TESTING_GUIDE.md`
- **Implementation:** `docs/finance/CURRENCY_EXCHANGE_IMPLEMENTATION.md`

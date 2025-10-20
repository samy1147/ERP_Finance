# Model Analysis - Duplicate Check Report

**Date:** October 14, 2025  
**Purpose:** Verify no duplicate fields across core, ar, and ap models

---

## ✅ Analysis Summary

**Result:** ✅ **NO DUPLICATES FOUND**

All three models are properly structured with:
- Core models defining shared structures (Currency, ExchangeRate, TaxRate)
- AR models referencing core via Foreign Keys
- AP models referencing core via Foreign Keys
- No duplicate table definitions

---

## 📋 Model Structure

### 1. Core Models (`core/models.py`)

**Purpose:** Shared reference data used across all modules

#### Currency Model
```python
class Currency(models.Model):
    code = CharField(3)          # USD, EUR, AED, etc.
    name = CharField(64)          # "US Dollar", etc.
    symbol = CharField(8)         # $, €, etc.
    is_base = BooleanField        # One currency is base
```
- **Used by:** ARInvoice, APInvoice, Customer, Supplier
- **Purpose:** Multi-currency support

#### ExchangeRate Model ✅
```python
class ExchangeRate(models.Model):
    from_currency = FK(Currency)  # Source currency
    to_currency = FK(Currency)    # Target currency
    rate_date = DateField         # Effective date
    rate = Decimal(18, 6)         # Exchange rate
    rate_type = CharField         # SPOT, AVERAGE, FIXED, CLOSING
    source = CharField            # Rate source
    is_active = BooleanField
```
- **Purpose:** Store historical exchange rates
- **Unique constraint:** (from_currency, to_currency, rate_date, rate_type)
- **Used by:** fx_services.py for currency conversion

#### TaxRate Model
```python
class TaxRate(models.Model):
    name = CharField(64)
    rate = Decimal(6, 3)          # e.g., 5.000 for 5%
    country = CharField(2)        # AE, SA, EG, IN
    category = CharField(16)      # STANDARD, ZERO, EXEMPT, RC
    code = CharField(16)          # VAT5, GST18, etc.
    effective_from = DateField
    effective_to = DateField
    is_active = BooleanField
```
- **Used by:** ARItem, APItem for tax calculations

#### FXGainLossAccount Model
```python
class FXGainLossAccount(models.Model):
    account = OneToOneFK(Account)  # GL account
    gain_loss_type = CharField     # REALIZED_GAIN, REALIZED_LOSS, etc.
    is_active = BooleanField
```
- **Purpose:** Configure which GL accounts to use for FX gains/losses

---

### 2. AR Models (`ar/models.py`)

**Purpose:** Accounts Receivable (Customer) transactions

#### Customer Model
```python
class Customer(models.Model):
    code = CharField(50)
    name = CharField(128)
    email = EmailField
    country = CharField(2)
    currency = FK(Currency) ← References core.Currency
    vat_number = CharField(50)
    is_active = BooleanField
```

#### ARInvoice Model
```python
class ARInvoice(models.Model):
    customer = FK(Customer)
    number = CharField(32)
    date = DateField
    due_date = DateField
    currency = FK(Currency) ← References core.Currency
    status = CharField(16)
    gl_journal = OneToOneFK(JournalEntry)
    posted_at = DateTimeField
    paid_at = DateTimeField
    
    # FX tracking fields (NEW) ✅
    exchange_rate = Decimal(18, 6)      ← Invoice-specific rate
    base_currency_total = Decimal(14, 2) ← Converted total
```
**Note:** 
- `exchange_rate` here is the **rate used when invoice was posted**
- Different from `ExchangeRate` table which stores **reference rates**
- This is the **audit trail** of what rate was applied

#### ARItem Model
```python
class ARItem(models.Model):
    invoice = FK(ARInvoice)
    description = CharField(255)
    quantity = Decimal(12, 2)
    unit_price = Decimal(12, 2)
    tax_rate = FK(TaxRate) ← References core.TaxRate
    tax_country = CharField(2)
    tax_category = CharField(16)
```

#### ARPayment Model
```python
class ARPayment(models.Model):
    invoice = FK(ARInvoice)
    date = DateField
    amount = Decimal(14, 2)
    bank_account = FK(BankAccount)
    posted_at = DateTimeField
    reconciled = BooleanField
    reconciliation_ref = CharField(64)
    reconciled_at = DateField
    gl_journal = FK(JournalEntry)
    payment_fx_rate = Decimal(12, 6) ← Payment-specific rate
```
**Note:**
- `payment_fx_rate` is for **payment-time FX rate**
- Used to calculate FX gain/loss if payment rate differs from invoice rate

---

### 3. AP Models (`ap/models.py`)

**Purpose:** Accounts Payable (Supplier) transactions

#### Supplier Model
```python
class Supplier(models.Model):
    code = CharField(50)
    name = CharField(128)
    email = EmailField
    country = CharField(2)
    currency = FK(Currency) ← References core.Currency
    vat_number = CharField(50)
    is_active = BooleanField
```

#### APInvoice Model
```python
class APInvoice(models.Model):
    supplier = FK(Supplier)
    number = CharField(32)
    date = DateField
    due_date = DateField
    currency = FK(Currency) ← References core.Currency
    status = CharField(16)
    gl_journal = OneToOneFK(JournalEntry)
    posted_at = DateTimeField
    paid_at = DateTimeField
    
    # FX tracking fields (NEW) ✅
    exchange_rate = Decimal(18, 6)      ← Invoice-specific rate
    base_currency_total = Decimal(14, 2) ← Converted total
```

#### APItem Model
```python
class APItem(models.Model):
    invoice = FK(APInvoice)
    description = CharField(255)
    quantity = Decimal(12, 2)
    unit_price = Decimal(12, 2)
    tax_rate = FK(TaxRate) ← References core.TaxRate
    tax_country = CharField(2)
    tax_category = CharField(16)
```

#### APPayment Model
```python
class APPayment(models.Model):
    invoice = FK(APInvoice)
    date = DateField
    amount = Decimal(14, 2)
    bank_account = FK(BankAccount)
    posted_at = DateTimeField
    reconciled = BooleanField
    reconciliation_ref = CharField(64)
    reconciled_at = DateField
    gl_journal = FK(JournalEntry)
    payment_fx_rate = Decimal(12, 6) ← Payment-specific rate
```

---

## 🔍 Field Analysis

### Fields That Look Similar But Are NOT Duplicates:

| Field Name | Location | Purpose | Type |
|------------|----------|---------|------|
| **rate** | `core.TaxRate` | Tax percentage (5% VAT) | Decimal(6, 3) |
| **rate** | `core.ExchangeRate` | FX rate (3.67 USD→AED) | Decimal(18, 6) |
| **exchange_rate** | `ar.ARInvoice` | Rate used at invoice posting | Decimal(18, 6) |
| **exchange_rate** | `ap.APInvoice` | Rate used at invoice posting | Decimal(18, 6) |
| **payment_fx_rate** | `ar.ARPayment` | Rate used at payment time | Decimal(12, 6) |
| **payment_fx_rate** | `ap.APPayment` | Rate used at payment time | Decimal(12, 6) |

### Why These Are NOT Duplicates:

1. **TaxRate.rate vs ExchangeRate.rate**
   - Different tables
   - Different purposes (tax % vs currency conversion)
   - Different precision (6,3 vs 18,6)

2. **ExchangeRate.rate vs ARInvoice.exchange_rate**
   - `ExchangeRate` = Reference table with all rates
   - `ARInvoice.exchange_rate` = Snapshot of rate used at posting time
   - Relationship: `ARInvoice.exchange_rate` is **copied from** `ExchangeRate.rate`

3. **ARInvoice.exchange_rate vs ARPayment.payment_fx_rate**
   - Invoice rate = rate when invoice posted
   - Payment rate = rate when payment received
   - Used to calculate FX gain/loss if rates differ

4. **ARInvoice fields vs APInvoice fields**
   - Different tables (AR = receivable, AP = payable)
   - Same structure by design (symmetry)
   - No data duplication

---

## ✅ Verification: ExchangeRate Table

### Table Structure Confirmed:

```sql
CREATE TABLE core_exchangerate (
    id INTEGER PRIMARY KEY,
    from_currency_id INTEGER NOT NULL,  ← FK to core_currency
    to_currency_id INTEGER NOT NULL,    ← FK to core_currency
    rate_date DATE NOT NULL,
    rate DECIMAL(18, 6) NOT NULL,
    rate_type VARCHAR(16) DEFAULT 'SPOT',
    source VARCHAR(128),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    UNIQUE(from_currency_id, to_currency_id, rate_date, rate_type),
    INDEX(from_currency_id, to_currency_id, rate_date),
    INDEX(rate_date, is_active)
);
```

### Key Points:

1. ✅ Has `from_currency_id` and `to_currency_id` columns
2. ✅ Uses Foreign Keys to `core_currency` table
3. ✅ Stores historical rates by date
4. ✅ Supports multiple rate types (SPOT, AVERAGE, FIXED, CLOSING)
5. ✅ Unique constraint prevents duplicate rates for same date/type

---

## 📊 Relationship Diagram

```
core.Currency
    ├─→ ar.Customer.currency
    ├─→ ar.ARInvoice.currency
    ├─→ ap.Supplier.currency
    ├─→ ap.APInvoice.currency
    ├─→ core.ExchangeRate.from_currency
    └─→ core.ExchangeRate.to_currency

core.ExchangeRate
    └─→ (copied to) ar.ARInvoice.exchange_rate
    └─→ (copied to) ap.APInvoice.exchange_rate

core.TaxRate
    ├─→ ar.ARItem.tax_rate
    └─→ ap.APItem.tax_rate
```

---

## 🎯 Data Flow Example

### Scenario: Post USD Invoice with AED Base Currency

```
1. Invoice Created:
   ARInvoice.currency = USD (FK to core.Currency)
   ARInvoice.exchange_rate = NULL (not posted yet)

2. Invoice Posted:
   System looks up: core.ExchangeRate
     WHERE from_currency = USD
       AND to_currency = AED
       AND rate_date <= invoice.date
     ORDER BY rate_date DESC
     LIMIT 1
   
   Found: rate = 3.670000
   
   System copies: ARInvoice.exchange_rate = 3.670000
   System converts: ARInvoice.base_currency_total = 1000 × 3.67 = 3670.00

3. Result:
   core.ExchangeRate.rate = 3.670000  ← Original reference rate
   ARInvoice.exchange_rate = 3.670000 ← Audit trail (snapshot)
   ARInvoice.base_currency_total = 3670.00 ← Converted amount
```

**No duplication** - Just a snapshot for audit purposes!

---

## ✅ Conclusion

### Summary:

1. **✅ NO DUPLICATES** - All fields serve distinct purposes
2. **✅ ExchangeRate table exists** in `core.models.py`
3. **✅ Has from_currency and to_currency** columns as expected
4. **✅ Proper Foreign Key relationships** established
5. **✅ AR and AP models** correctly reference core models
6. **✅ New FX fields** properly added to invoices

### Table Count:

| App | Tables | Purpose |
|-----|--------|---------|
| **core** | 3 | Currency, ExchangeRate, TaxRate (shared) |
| **ar** | 4 | Customer, ARInvoice, ARItem, ARPayment |
| **ap** | 4 | Supplier, APInvoice, APItem, APPayment |
| **Total** | 11 | ✅ All unique, no duplicates |

---

## 🔧 Recommendations

1. **✅ Current Structure is Correct** - No changes needed
2. **✅ ExchangeRate Table Ready** - Can be used for FX conversions
3. **✅ Invoice FX Fields Added** - Audit trail in place
4. **✅ Foreign Keys Proper** - Good relational design

---

**Status:** ✅ **ALL VERIFIED - NO DUPLICATES FOUND**  
**Database Design:** ✅ **PROPER NORMALIZATION**  
**Ready for Use:** ✅ **YES**

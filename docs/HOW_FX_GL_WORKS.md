# How FX (Foreign Exchange) Works in GL (General Ledger)

**Complete Visual Guide with Examples**

---

## 📚 Table of Contents
1. [Overview](#overview)
2. [The FX Workflow](#the-fx-workflow)
3. [Key Components](#key-components)
4. [Real Examples](#real-examples)
5. [Journal Entry Examples](#journal-entry-examples)
6. [Configuration](#configuration)
7. [Technical Implementation](#technical-implementation)

---

## Overview

### What is FX in GL?

When you do business in **multiple currencies**, exchange rates fluctuate. These fluctuations create **gains or losses** that must be recorded in your General Ledger.

**Example:**
- You invoice a customer **$10,000 USD** when 1 USD = 3.67 AED (**36,700 AED**)
- Customer pays **$10,000 USD** when 1 USD = 3.70 AED (**37,000 AED**)
- You gained **300 AED** due to exchange rate movement! 💰

The system **automatically** calculates and posts this FX gain to your GL.

---

## The FX Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-CURRENCY TRANSACTION FLOW               │
└─────────────────────────────────────────────────────────────────┘

STEP 1: INVOICE CREATED (EUR Currency)
┌──────────────────────────────────────┐
│  AR Invoice #INV-001                 │
│  Customer: ABC Corp                  │
│  Amount: EUR 10,000                  │
│  Date: Jan 1, 2025                   │
│  Status: DRAFT                       │
└──────────────────────────────────────┘

                    ↓ POST TO GL

STEP 2: INVOICE POSTED (Exchange Rate Locked)
┌──────────────────────────────────────┐
│  AR Invoice #INV-001                 │
│  Amount: EUR 10,000                  │
│  Exchange Rate: 4.00                 │  ← Rate captured at posting
│  Base Amount: AED 40,000             │  ← Converted to base currency
│  Posted: Yes                         │
└──────────────────────────────────────┘

JOURNAL ENTRY #JE-001 (Jan 1)
┌─────────────────────────────────────────────────┐
│  DR  Accounts Receivable     40,000 AED        │
│      CR  Sales Revenue                40,000   │
└─────────────────────────────────────────────────┘

                    ↓ TIME PASSES ↓
                (Exchange rate changes!)

STEP 3: PAYMENT RECEIVED (Different Exchange Rate)
┌──────────────────────────────────────┐
│  AR Payment #PAY-001                 │
│  Customer: ABC Corp                  │
│  Amount: EUR 10,000                  │
│  Date: Feb 1, 2025                   │
│  Exchange Rate: 4.20                 │  ← NEW RATE!
│  Base Amount: AED 42,000             │  ← More AED received!
└──────────────────────────────────────┘

                    ↓ SYSTEM CALCULATES FX

FX CALCULATION:
┌─────────────────────────────────────────────────┐
│  Invoice booked at:  EUR 10,000 × 4.00 = 40,000 AED │
│  Payment received:   EUR 10,000 × 4.20 = 42,000 AED │
│  ─────────────────────────────────────────────────── │
│  FX GAIN:                              2,000 AED     │
└─────────────────────────────────────────────────┘

                    ↓ POST TO GL

STEP 4: PAYMENT POSTED WITH FX GAIN
JOURNAL ENTRY #JE-002 (Feb 1)
┌─────────────────────────────────────────────────┐
│  DR  Bank Account            42,000 AED        │  ← Cash received
│      CR  Accounts Receivable         40,000   │  ← Clear AR
│      CR  FX Gain Income               2,000   │  ← FX profit!
└─────────────────────────────────────────────────┘

✅ RESULT:
- Customer paid exact invoice amount (EUR 10,000)
- You received more in your base currency (AED 42,000 vs 40,000)
- Profit from exchange rate movement recorded as income
```

---

## Key Components

### 1. **Base Currency** 
Your company's "home" currency (usually AED for UAE companies)

**Purpose:**
- All GL entries ultimately recorded in base currency
- Financial reports produced in base currency
- FX gains/losses calculated relative to base currency

**Configuration:** Set in Core → Currencies (one currency has `is_base=True`)

---

### 2. **Exchange Rates**
Historical records of currency conversion rates

**Model:** `ExchangeRate`
```python
from_currency: Currency    # e.g., EUR
to_currency: Currency      # e.g., AED  
rate: Decimal             # e.g., 4.012500 (1 EUR = 4.0125 AED)
rate_date: Date           # e.g., 2025-01-15
rate_type: String         # SPOT, AVERAGE, CLOSING
```

**Stored in:** `core_exchangerate` table

**Example:**
| From | To  | Rate     | Date       | Type |
|------|-----|----------|------------|------|
| EUR  | AED | 4.012500 | 2025-01-15 | SPOT |
| USD  | AED | 3.673000 | 2025-01-15 | SPOT |
| GBP  | AED | 4.682000 | 2025-01-15 | SPOT |

---

### 3. **FX Gain/Loss Accounts**
GL accounts where FX differences are recorded

**Types:**

| Type              | When Used                    | Nature  | Example Account |
|-------------------|------------------------------|---------|-----------------|
| **REALIZED_GAIN**     | Payment received, rate went up  | Income  | 7150 - FX Gains |
| **REALIZED_LOSS**     | Payment received, rate went down| Expense | 8150 - FX Losses|
| **UNREALIZED_GAIN**   | Period-end revaluation (up)     | Income  | 7210 - Unrealized FX Gains|
| **UNREALIZED_LOSS**   | Period-end revaluation (down)   | Expense | 8210 - Unrealized FX Losses|

**Model:** `FXGainLossAccount`

**Configuration:** Finance → FX Configuration page

---

### 4. **Payment FX Tracking**
Payments store their exchange rates for comparison

**Fields on ARPayment/APPayment:**
```python
invoice_currency: ForeignKey(Currency)     # Currency of invoice
exchange_rate: Decimal                     # Rate at payment time
```

**Purpose:** Compare payment rate vs invoice rate to calculate realized FX

---

## Real Examples

### Example 1: AR Payment with FX GAIN 💰

**Scenario:** European customer invoice in EUR, receives payment later

**Timeline:**
```
Jan 1, 2025 - Invoice Created and Posted
├─ Invoice: EUR 5,000
├─ Exchange Rate: 4.00 (1 EUR = 4.00 AED)
└─ Booked as: AED 20,000

Feb 1, 2025 - Payment Received
├─ Payment: EUR 5,000
├─ Exchange Rate: 4.20 (1 EUR = 4.20 AED)
└─ Received as: AED 21,000

FX Calculation:
  Booked:   EUR 5,000 × 4.00 = AED 20,000
  Received: EUR 5,000 × 4.20 = AED 21,000
  ─────────────────────────────────────────
  GAIN:                        AED  1,000 ✅
```

**Journal Entries:**

**Jan 1 - Invoice Posting**
```
JE-001 (Invoice)
DR  Accounts Receivable (1200)     20,000 AED
    CR  Sales Revenue (4000)               20,000 AED
```

**Feb 1 - Payment Posting**
```
JE-002 (Payment with FX Gain)
DR  Bank Account (1000)             21,000 AED  ← Cash received
    CR  Accounts Receivable (1200)         20,000 AED  ← Clear AR
    CR  FX Gain Income (7150)               1,000 AED  ← Profit!
```

**Result:**
- ✅ Customer paid exactly what they owed (EUR 5,000)
- ✅ You received more AED due to favorable exchange rate
- ✅ FX gain recorded as income (increases profit)

---

### Example 2: AP Payment with FX LOSS 📉

**Scenario:** Supplier invoice in USD, payment made later

**Timeline:**
```
Jan 1, 2025 - Invoice Received and Posted
├─ Invoice: USD 10,000
├─ Exchange Rate: 3.70 (1 USD = 3.70 AED)
└─ Booked as: AED 37,000

Feb 1, 2025 - Payment Made
├─ Payment: USD 10,000
├─ Exchange Rate: 3.67 (1 USD = 3.67 AED)
└─ Paid: AED 36,700

FX Calculation:
  Booked: USD 10,000 × 3.70 = AED 37,000
  Paid:   USD 10,000 × 3.67 = AED 36,700
  ─────────────────────────────────────────
  GAIN:                        AED    300 ✅
```

**Journal Entries:**

**Jan 1 - Invoice Posting**
```
JE-003 (Bill)
DR  Purchases (5000)                37,000 AED
    CR  Accounts Payable (2000)            37,000 AED
```

**Feb 1 - Payment Posting**
```
JE-004 (Payment with FX Gain)
DR  Accounts Payable (2000)         37,000 AED  ← Clear AP
    CR  Bank Account (1000)                36,700 AED  ← Cash paid
    CR  FX Gain Income (7150)                 300 AED  ← Benefit!
```

**Result:**
- ✅ Paid supplier exactly what was owed (USD 10,000)
- ✅ Paid less AED due to favorable exchange rate movement
- ✅ FX gain recorded as income (cost savings)

---

### Example 3: AR Payment with FX LOSS 📉

**Scenario:** Customer invoice in GBP, payment received later, rate decreased

**Timeline:**
```
Jan 1, 2025 - Invoice Posted
├─ Invoice: GBP 2,000
├─ Exchange Rate: 4.80 (1 GBP = 4.80 AED)
└─ Booked as: AED 9,600

Feb 1, 2025 - Payment Received
├─ Payment: GBP 2,000
├─ Exchange Rate: 4.60 (1 GBP = 4.60 AED)
└─ Received: AED 9,200

FX Calculation:
  Booked:   GBP 2,000 × 4.80 = AED 9,600
  Received: GBP 2,000 × 4.60 = AED 9,200
  ─────────────────────────────────────────
  LOSS:                        AED   400 ❌
```

**Journal Entries:**

**Jan 1 - Invoice Posting**
```
JE-005 (Invoice)
DR  Accounts Receivable (1200)      9,600 AED
    CR  Sales Revenue (4000)                9,600 AED
```

**Feb 1 - Payment Posting**
```
JE-006 (Payment with FX Loss)
DR  Bank Account (1000)              9,200 AED  ← Cash received
DR  FX Loss Expense (8150)             400 AED  ← Loss!
    CR  Accounts Receivable (1200)          9,600 AED  ← Clear AR
```

**Result:**
- ✅ Customer paid exactly what they owed (GBP 2,000)
- ❌ You received less AED due to unfavorable exchange rate
- ❌ FX loss recorded as expense (reduces profit)

---

### Example 4: Complex Multi-Currency (EUR Invoice → USD Payment)

**Scenario:** Invoice in EUR, customer pays in USD (both are foreign currencies)

**Timeline:**
```
Jan 1, 2025 - Invoice Posted (EUR)
├─ Invoice: EUR 1,000
├─ Exchange Rate (EUR→AED): 4.00
└─ Booked as: AED 4,000

Feb 1, 2025 - Payment Received (USD)
├─ Payment: USD 1,100 (customer's calculation)
├─ Exchange Rate (USD→AED): 3.67
└─ Received: AED 4,037

FX Calculation:
  Booked:   EUR 1,000 × 4.00 = AED 4,000
  Received: USD 1,100 × 3.67 = AED 4,037
  ─────────────────────────────────────────
  GAIN:                         AED    37 ✅
```

**Journal Entries:**
```
JE-007 (Payment)
DR  Bank Account (1000)              4,037 AED
    CR  Accounts Receivable (1200)          4,000 AED
    CR  FX Gain Income (7150)                  37 AED
```

**Why the Gain?**
- Invoice value in base: 4,000 AED
- Payment value in base: 4,037 AED
- Difference is FX gain regardless of source currencies

---

## Journal Entry Examples

### Template: AR Payment with FX Gain
```
When: Payment received at better rate than invoice rate

DR  Bank Account (1000)             [Higher Amount]
    CR  Accounts Receivable (1200)  [Invoice Amount]
    CR  FX Gain Income (7150)       [Difference]
```

### Template: AR Payment with FX Loss
```
When: Payment received at worse rate than invoice rate

DR  Bank Account (1000)             [Lower Amount]
DR  FX Loss Expense (8150)          [Difference]
    CR  Accounts Receivable (1200)  [Invoice Amount]
```

### Template: AP Payment with FX Gain
```
When: Payment made at better rate than invoice rate (less AED paid)

DR  Accounts Payable (2000)         [Invoice Amount]
    CR  Bank Account (1000)         [Lower Amount]
    CR  FX Gain Income (7150)       [Difference]
```

### Template: AP Payment with FX Loss
```
When: Payment made at worse rate than invoice rate (more AED paid)

DR  Accounts Payable (2000)         [Invoice Amount]
DR  FX Loss Expense (8150)          [Difference]
    CR  Bank Account (1000)         [Higher Amount]
```

---

## Configuration

### Step 1: Set Base Currency
**Location:** Core → Currencies

**Action:** Mark one currency as `is_base=True`

**Example:**
```
Currency: AED (United Arab Emirates Dirham)
☑ Is Base Currency
```

---

### Step 2: Configure FX Accounts
**Location:** Finance → FX Configuration

**Required Accounts:**

| Type              | Account Code | Account Name               | Type    |
|-------------------|--------------|----------------------------|---------|
| REALIZED_GAIN     | 7150         | Foreign Exchange Gains     | INCOME  |
| REALIZED_LOSS     | 8150         | Foreign Exchange Losses    | EXPENSE |
| UNREALIZED_GAIN   | 7210         | Unrealized FX Gains        | INCOME  |
| UNREALIZED_LOSS   | 8210         | Unrealized FX Losses       | EXPENSE |

**Screenshot Reference:**
```
┌───────────────────────────────────────────────────────────┐
│  FX Gain/Loss Account Configuration                       │
├───────────────────────────────────────────────────────────┤
│  Type              │ GL Account                 │ Active  │
├────────────────────┼────────────────────────────┼─────────┤
│  Realized Gain     │ 7150 - FX Gains           │ ☑ Yes   │
│  Realized Loss     │ 8150 - FX Losses          │ ☑ Yes   │
│  Unrealized Gain   │ 7210 - Unrealized FX Gains│ ☑ Yes   │
│  Unrealized Loss   │ 8210 - Unrealized FX Losses│ ☑ Yes  │
└────────────────────┴────────────────────────────┴─────────┘
```

---

### Step 3: Load Exchange Rates
**Location:** Finance → Exchange Rates

**Options:**
1. **Auto-Fetch:** Use API to get daily rates automatically
2. **Manual Entry:** Enter rates manually
3. **Bulk Import:** Upload CSV with rates

**Required Rates:**
- From each foreign currency → To base currency (e.g., EUR→AED, USD→AED)
- System can calculate inverse rates automatically

---

## Technical Implementation

### 1. Core Functions (finance/fx_services.py)

#### `get_exchange_rate(from_currency, to_currency, rate_date)`
**Purpose:** Find exchange rate for a date

**Logic:**
1. Check same currency → return 1.0
2. Look for direct rate (EUR→AED)
3. Look for inverse rate (AED→EUR), calculate reciprocal
4. Look for cross-base path (EUR→AED→USD)
5. Raise error if no rate found

**Code:**
```python
def get_exchange_rate(from_currency, to_currency, rate_date, rate_type="SPOT"):
    # If same currency
    if from_currency.id == to_currency.id:
        return Decimal('1.000000')
    
    # Try direct rate
    try:
        rate = ExchangeRate.objects.get(
            from_currency=from_currency,
            to_currency=to_currency,
            rate_date__lte=rate_date
        ).latest('rate_date')
        return rate.rate
    except ExchangeRate.DoesNotExist:
        pass
    
    # Try inverse rate
    try:
        rate = ExchangeRate.objects.get(
            from_currency=to_currency,
            to_currency=from_currency,
            rate_date__lte=rate_date
        ).latest('rate_date')
        return Decimal('1.0') / rate.rate  # Reciprocal
    except ExchangeRate.DoesNotExist:
        raise ValidationError("No exchange rate found")
```

---

#### `calculate_fx_gain_loss(original_amount, original_currency, original_rate, settlement_amount, settlement_currency, settlement_rate)`
**Purpose:** Calculate FX gain/loss amount

**Logic:**
1. Convert original amount to base currency using original rate
2. Convert settlement amount to base currency using settlement rate
3. Calculate difference
4. Positive = GAIN, Negative = LOSS

**Code:**
```python
def calculate_fx_gain_loss(
    original_amount,      # Invoice amount in invoice currency
    original_currency,    # Invoice currency (e.g., EUR)
    original_rate,        # Rate at invoice time (e.g., 4.00)
    settlement_amount,    # Payment amount in payment currency
    settlement_currency,  # Payment currency (could be same or different)
    settlement_rate       # Rate at payment time (e.g., 4.20)
):
    base_currency = get_base_currency()  # AED
    
    # Convert invoice to base
    if original_currency.id == base_currency.id:
        original_base = original_amount
    else:
        original_base = original_amount * original_rate
    
    # Convert payment to base
    if settlement_currency.id == base_currency.id:
        settlement_base = settlement_amount
    else:
        settlement_base = settlement_amount * settlement_rate
    
    # Calculate difference
    difference = settlement_base - original_base
    
    if difference > 0:
        return (abs(difference), "REALIZED_GAIN")
    elif difference < 0:
        return (abs(difference), "REALIZED_LOSS")
    else:
        return (Decimal('0.00'), "REALIZED_GAIN")
```

**Example:**
```python
# Invoice: EUR 1,000 at rate 4.00
# Payment: EUR 1,000 at rate 4.20

gain, type = calculate_fx_gain_loss(
    original_amount=Decimal('1000.00'),
    original_currency=Currency.objects.get(code='EUR'),
    original_rate=Decimal('4.00'),
    settlement_amount=Decimal('1000.00'),
    settlement_currency=Currency.objects.get(code='EUR'),
    settlement_rate=Decimal('4.20')
)

# Result:
# gain = 200.00
# type = "REALIZED_GAIN"
# 
# Because:
# Original:   1000 × 4.00 = 4,000 AED
# Settlement: 1000 × 4.20 = 4,200 AED
# Difference: 200 AED GAIN
```

---

#### `post_fx_gain_loss(journal_entry, gain_loss_amount, gain_loss_type, contra_account)`
**Purpose:** Add FX lines to journal entry

**Logic:**
1. Get FX account for gain/loss type
2. If GAIN: Credit FX Gain, Debit contra account
3. If LOSS: Debit FX Loss, Credit contra account

**Code:**
```python
@transaction.atomic
def post_fx_gain_loss(journal_entry, gain_loss_amount, gain_loss_type, contra_account, memo=""):
    if gain_loss_amount == 0:
        return  # No FX to post
    
    fx_account = get_fx_account(gain_loss_type)
    
    if "GAIN" in gain_loss_type:
        # Credit FX Gain (income increases)
        JournalLine.objects.create(
            entry=journal_entry,
            account=fx_account,
            debit=Decimal('0.00'),
            credit=gain_loss_amount
        )
        # Debit contra account (AR/AP)
        JournalLine.objects.create(
            entry=journal_entry,
            account=contra_account,
            debit=gain_loss_amount,
            credit=Decimal('0.00')
        )
    else:  # LOSS
        # Debit FX Loss (expense increases)
        JournalLine.objects.create(
            entry=journal_entry,
            account=fx_account,
            debit=gain_loss_amount,
            credit=Decimal('0.00')
        )
        # Credit contra account
        JournalLine.objects.create(
            entry=journal_entry,
            account=contra_account,
            debit=Decimal('0.00'),
            credit=gain_loss_amount
        )
```

---

### 2. Integration with Payment Posting

When a payment is posted, the system:

**Step 1:** Capture exchange rate
```python
# In ARPayment/APPayment
def update_exchange_rate_from_allocations(self):
    """Capture exchange rate from first allocation"""
    first_alloc = self.allocations.first()
    if first_alloc and first_alloc.invoice:
        invoice = first_alloc.invoice
        if invoice.currency_id != self.currency_id:
            # Get rate at payment date
            rate = get_exchange_rate(
                from_currency=invoice.currency,
                to_currency=self.currency,
                rate_date=self.date
            )
            self.invoice_currency = invoice.currency
            self.exchange_rate = rate
            self.save()
```

**Step 2:** Calculate FX on posting
```python
# In finance/services.py - post_ar_payment()
@transaction.atomic
def post_ar_payment(payment):
    # ... create journal entry ...
    
    # Check for FX
    if payment.invoice_currency and payment.exchange_rate:
        for allocation in payment.allocations.all():
            invoice = allocation.invoice
            
            # Calculate FX gain/loss
            gain_loss, fx_type = calculate_fx_gain_loss(
                original_amount=allocation.amount,
                original_currency=invoice.currency,
                original_rate=invoice.exchange_rate,
                settlement_amount=allocation.amount,
                settlement_currency=payment.currency,
                settlement_rate=payment.exchange_rate
            )
            
            if gain_loss > 0:
                # Post FX to journal entry
                post_fx_gain_loss(
                    journal_entry=je,
                    gain_loss_amount=gain_loss,
                    gain_loss_type=fx_type,
                    contra_account=ar_account
                )
    
    # ... post journal entry ...
```

---

## Summary

### ✅ What FX GL Does:
1. **Tracks** exchange rates at transaction time
2. **Calculates** gains/losses from rate changes
3. **Records** FX differences in GL automatically
4. **Reports** FX impact on profit/loss

### 🎯 Key Accounts:
- **7150** - FX Gain Income (increases profit)
- **8150** - FX Loss Expense (decreases profit)

### 📊 When It Happens:
- **Invoice Posting:** Locks exchange rate
- **Payment Posting:** Compares rates, posts FX difference

### 💡 Business Value:
- **Accurate Financials:** True profit/loss including FX
- **Compliance:** Meets accounting standards (IAS 21)
- **Transparency:** See FX impact separately
- **Automated:** No manual FX calculations needed

---

**Last Updated:** October 19, 2025
**Status:** ✅ Fully Implemented and Tested

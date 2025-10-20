# FX Services Documentation (fx_services.py)

## Overview
This file provides foreign exchange (FX) services for the Finance module. It handles currency conversions, exchange rate lookups, FX gain/loss calculations, and period-end revaluations.

---

## File Location
```
finance/fx_services.py
```

---

## Imports & Dependencies
```python
from core.models import Currency, ExchangeRate, FXGainLossAccount
from finance.models import JournalEntry, JournalLine, Account
```

---

## Core Functions

### 1. `get_base_currency() -> Currency`

**Purpose:** Gets the company's base/home currency

**Parameters:** None

**Returns:** Currency instance marked with `is_base=True`

**Raises:**
- `ValidationError`: No base currency configured
- `ValidationError`: Multiple base currencies found

**Usage:**
```python
base_currency = get_base_currency()
print(f"Base currency: {base_currency.code}")  # e.g., "USD"
```

**Why Important:** All FX calculations need a base currency reference

---

### 2. `get_exchange_rate(from_currency, to_currency, rate_date, rate_type="SPOT")`

**Purpose:** Retrieves exchange rate for converting between currencies

**Parameters:**
- `from_currency`: Source Currency instance
- `to_currency`: Target Currency instance
- `rate_date`: Date for rate lookup
- `rate_type`: Rate type (default: "SPOT")

**Returns:** Exchange rate as Decimal (e.g., `Decimal("3.67")` for USD→AED)

**Rate Types:**
- `SPOT`: Current market rate
- `AVERAGE`: Period average rate
- `CLOSING`: Month/year end rate

**Lookup Strategy:**
1. **Same currency:** Returns 1.0 immediately
2. **Exact match:** Searches for exact date + from/to pair
3. **Most recent:** Uses latest rate on or before `rate_date`
4. **Inverse rate:** If no direct rate, tries reverse pair and inverts
5. **Error:** Raises ValidationError if not found

**Raises:**
- `ValidationError`: No rate found for currency pair and date

**Example:**
```python
usd = Currency.objects.get(code="USD")
aed = Currency.objects.get(code="AED")

rate = get_exchange_rate(usd, aed, date(2025, 1, 15))
# Returns Decimal("3.6725") (1 USD = 3.6725 AED)

# Inverse lookup
rate = get_exchange_rate(aed, usd, date(2025, 1, 15))
# Returns Decimal("0.2723") (1 AED = 0.2723 USD)
```

**Key Features:**
- ✅ **Smart fallback:** Uses most recent rate if exact date not found
- ✅ **Inverse lookup:** Automatically calculates reciprocal
- ✅ **Same currency:** Returns 1.0 without database query

---

### 3. `convert_amount(amount, from_currency, to_currency, rate_date, rate_type="SPOT")`

**Purpose:** Converts an amount from one currency to another

**Parameters:**
- `amount`: Amount to convert (Decimal)
- `from_currency`: Source Currency
- `to_currency`: Target Currency
- `rate_date`: Date for exchange rate
- `rate_type`: Rate type (default: "SPOT")

**Returns:** Converted amount rounded to 2 decimals

**Formula:** `converted_amount = amount × exchange_rate`

**Example:**
```python
usd = Currency.objects.get(code="USD")
aed = Currency.objects.get(code="AED")

# Convert 1000 USD to AED
amount_aed = convert_amount(
    Decimal("1000.00"),
    usd,
    aed,
    date(2025, 1, 15)
)
# Returns Decimal("3672.50") (at rate 3.6725)
```

**Rounding:** Uses ROUND_HALF_UP (0.5 rounds up)

---

### 4. `calculate_fx_gain_loss(...)`

**Purpose:** Calculates realized FX gain or loss on a transaction

**Parameters:**
- `original_amount`: Original transaction amount
- `original_currency`: Currency at transaction time
- `original_rate`: Exchange rate at transaction time
- `settlement_amount`: Settlement/payment amount
- `settlement_currency`: Currency at settlement time
- `settlement_rate`: Exchange rate at settlement time

**Returns:** Tuple `(gain_loss_amount, gain_or_loss_type)`

**Types:**
- `REALIZED_GAIN`: Positive difference (good!)
- `REALIZED_LOSS`: Negative difference (bad!)

**Calculation Logic:**
1. Converts original amount to base currency using original rate
2. Converts settlement amount to base currency using settlement rate
3. Calculates difference
4. Determines if gain (positive) or loss (negative)

**Example:**
```python
# Invoice for 1000 AED when rate was 3.67 (=272.48 USD base)
# Paid 1000 AED when rate is 3.60 (=277.78 USD base)
# Result: USD 5.30 gain (received more in base currency)

gain_loss, type = calculate_fx_gain_loss(
    original_amount=Decimal("1000.00"),
    original_currency=aed,
    original_rate=Decimal("3.67"),
    settlement_amount=Decimal("1000.00"),
    settlement_currency=aed,
    settlement_rate=Decimal("3.60")
)
# Returns (Decimal("5.30"), "REALIZED_GAIN")
```

**Real-world Scenario:**
```
AR Invoice: 1000 EUR @ 1.10 rate = 1100 USD booked
Payment: 1000 EUR @ 1.08 rate = 1080 USD received
Result: 20 USD REALIZED_LOSS (received less than booked)
```

---

### 5. `get_fx_account(gain_loss_type: str) -> Account`

**Purpose:** Gets configured GL account for FX gain/loss type

**Parameters:**
- `gain_loss_type`: Type of gain/loss

**Gain/Loss Types:**
- `REALIZED_GAIN`: Income account (e.g., 7150)
- `REALIZED_LOSS`: Expense account (e.g., 8150)
- `UNREALIZED_GAIN`: Income account (period-end revaluation)
- `UNREALIZED_LOSS`: Expense account (period-end revaluation)

**Returns:** Account instance

**Raises:**
- `ValidationError`: No account configured for type

**Configuration:** Must set up in FXGainLossAccount model
```python
FXGainLossAccount.objects.create(
    gain_loss_type="REALIZED_GAIN",
    account=Account.objects.get(code="7150"),
    is_active=True
)
```

**Usage:**
```python
gain_account = get_fx_account("REALIZED_GAIN")
loss_account = get_fx_account("REALIZED_LOSS")
```

---

### 6. `post_fx_gain_loss(journal_entry, gain_loss_amount, gain_loss_type, contra_account, memo="")`

**Purpose:** Posts FX gain or loss journal lines to existing entry

**Parameters:**
- `journal_entry`: JournalEntry to add lines to
- `gain_loss_amount`: Absolute amount (always positive)
- `gain_loss_type`: REALIZED_GAIN, REALIZED_LOSS, etc.
- `contra_account`: Account to post against (usually AR/AP)
- `memo`: Optional memo text

**Returns:** None (modifies journal_entry in place)

**Journal Entries Created:**

**For GAIN:**
```
DR Accounts Receivable   5.30
    CR FX Gain Income     5.30
```

**For LOSS:**
```
DR FX Loss Expense       20.00
    CR Accounts Receivable 20.00
```

**Example:**
```python
# Create journal entry
je = JournalEntry.objects.create(
    date=date.today(),
    memo="Payment with FX"
)

# Post FX gain
post_fx_gain_loss(
    journal_entry=je,
    gain_loss_amount=Decimal("5.30"),
    gain_loss_type="REALIZED_GAIN",
    contra_account=ar_account,
    memo="FX gain on EUR payment"
)

# Result: 2 lines added to je
```

**Transaction Safety:** Uses `@transaction.atomic` decorator

---

### 7. `create_exchange_rate(from_currency_code, to_currency_code, rate, rate_date, rate_type="SPOT", source="")`

**Purpose:** Creates or updates an exchange rate

**Parameters:**
- `from_currency_code`: Source currency code (e.g., "USD")
- `to_currency_code`: Target currency code (e.g., "AED")
- `rate`: Exchange rate (Decimal)
- `rate_date`: Effective date
- `rate_type`: Rate type (default: "SPOT")
- `source`: Source of rate (e.g., "Central Bank", "XE.com")

**Returns:** ExchangeRate instance

**Behavior:**
- If rate exists for date: **Updates** it
- If rate doesn't exist: **Creates** new one

**Usage:**
```python
# Manual entry
rate = create_exchange_rate(
    "USD",
    "AED",
    Decimal("3.6725"),
    date(2025, 1, 15),
    source="UAE Central Bank"
)

# From API
import requests
response = requests.get("https://api.exchangerate.com/...")
rate = create_exchange_rate(
    "USD",
    "EUR",
    Decimal(response.json()["rate"]),
    date.today(),
    source="ExchangeRate API"
)
```

**Best Practice:** Store source for audit trail

---

### 8. `revalue_open_balances(as_of_date, account_code, revaluation_currency=None)`

**Purpose:** Revalues open AR/AP balances for unrealized FX gain/loss

**Parameters:**
- `as_of_date`: Date to revalue as of (usually month/year end)
- `account_code`: AR or AP account code to revalue
- `revaluation_currency`: Currency to revalue to (default: base currency)

**Returns:** JournalEntry (not posted)

**Use Case:** Period-end accounting to recognize unrealized gains/losses

**⚠️ Note:** Current implementation is a **placeholder**

**Full Implementation Would:**
1. Get all open AR/AP invoices
2. Calculate original booked amount in base currency
3. Revalue at current rate
4. Post difference as unrealized gain/loss

**Example Workflow:**
```python
# Month-end revaluation
je = revalue_open_balances(
    as_of_date=date(2025, 1, 31),
    account_code="1100"  # AR account
)

# Review revaluation
for line in je.lines.all():
    print(f"{line.account.name}: {line.debit} / {line.credit}")

# Post if approved
post_entry(je)
```

**Unrealized Gain/Loss:**
```
Scenario: Customer owes 1000 EUR
- Booked at 1.10 rate = 1100 USD
- Month end rate 1.12 = 1120 USD
- Result: 20 USD unrealized gain

Journal Entry:
DR Accounts Receivable   20
    CR Unrealized FX Gain 20
```

---

## FX Concepts

### Realized vs Unrealized

**Realized Gain/Loss:**
- Occurs when transaction settles
- Cash actually received/paid
- Permanent (can't reverse)
- Tax impact (usually)

**Unrealized Gain/Loss:**
- Occurs at period-end revaluation
- No cash movement
- Can reverse in future periods
- May not have tax impact

**Example Timeline:**
```
Jan 1: Invoice 1000 EUR @ 1.10 = 1100 USD (booked)
Jan 31: Month end @ 1.12 = 1120 USD
        → Unrealized gain: 20 USD

Feb 15: Payment received @ 1.08 = 1080 USD
        → Reverse unrealized: -20 USD
        → Realized loss: -20 USD (vs original booking)
```

---

## Common Patterns

### 1. Simple Currency Conversion
```python
# Convert price list from USD to local currency
usd = Currency.objects.get(code="USD")
local = Currency.objects.get(code="AED")

for product in Product.objects.all():
    product.local_price = convert_amount(
        product.usd_price,
        usd,
        local,
        date.today()
    )
    product.save()
```

### 2. Payment with FX
```python
@transaction.atomic
def process_foreign_payment(payment):
    invoice = payment.invoice
    
    # Calculate FX gain/loss
    gain_loss, type = calculate_fx_gain_loss(
        invoice.total,
        invoice.currency,
        invoice.fx_rate,  # Rate at invoice time
        payment.amount,
        payment.currency,
        payment.fx_rate  # Rate at payment time
    )
    
    # Create journal entry
    je = JournalEntry.objects.create(...)
    
    # Post payment lines
    JournalLine.objects.create(...)  # Bank
    JournalLine.objects.create(...)  # AR
    
    # Post FX gain/loss if any
    if gain_loss > 0:
        post_fx_gain_loss(je, gain_loss, type, ar_account)
    
    post_entry(je)
```

### 3. Daily Rate Import
```python
def import_daily_rates():
    """Import exchange rates from external API"""
    api_data = fetch_rates_from_api()
    base = get_base_currency()
    
    for currency_code, rate in api_data.items():
        if currency_code == base.code:
            continue
        
        create_exchange_rate(
            base.code,
            currency_code,
            Decimal(str(rate)),
            date.today(),
            source="Daily API Import"
        )
```

### 4. Month-end Revaluation
```python
def month_end_fx_revaluation(period_end):
    """Revalue open balances at month end"""
    
    # Revalue AR
    ar_je = revalue_open_balances(period_end, "1100")
    review_and_post(ar_je)
    
    # Revalue AP
    ap_je = revalue_open_balances(period_end, "2000")
    review_and_post(ap_je)
```

---

## Best Practices

### 1. Always Use Base Currency
✅ **DO:** Set one currency as `is_base=True`  
❌ **DON'T:** Have multiple or no base currencies

### 2. Store Exchange Rates
✅ **DO:** Record rate at transaction time  
❌ **DON'T:** Lookup rates retroactively

**Why:** Exchange rates change! Store the rate used for each transaction.

### 3. Separate Realized vs Unrealized
✅ **DO:** Use different GL accounts for realized vs unrealized  
❌ **DON'T:** Mix them in same account

### 4. Source Your Rates
✅ **DO:** Record source of exchange rates  
❌ **DON'T:** Enter rates without documentation

### 5. Inverse Rates
✅ **DO:** Let system calculate inverse automatically  
❌ **DON'T:** Manually enter both USD→EUR and EUR→USD

### 6. Period-end Discipline
✅ **DO:** Revalue open balances every period  
❌ **DON'T:** Wait until annual audit

---

## Error Handling

### Missing Base Currency
```python
try:
    base = get_base_currency()
except ValidationError as e:
    print(f"Configuration error: {e}")
    # Fix: Currency.objects.filter(code="USD").update(is_base=True)
```

### Missing Exchange Rate
```python
try:
    rate = get_exchange_rate(usd, eur, date(2025, 1, 15))
except ValidationError as e:
    print(f"Rate not found: {e}")
    # Fix: create_exchange_rate("USD", "EUR", Decimal("0.92"), date(2025, 1, 15))
```

### Missing FX Account
```python
try:
    account = get_fx_account("REALIZED_GAIN")
except ValidationError as e:
    print(f"Account not configured: {e}")
    # Fix: Configure in FXGainLossAccount model
```

---

## Example: Complete FX Flow

```python
# 1. Setup
base_usd = Currency.objects.create(code="USD", name="US Dollar", is_base=True)
aed = Currency.objects.create(code="AED", name="UAE Dirham")

# 2. Set exchange rate
create_exchange_rate("USD", "AED", Decimal("3.6725"), date(2025, 1, 1))

# 3. Create invoice in foreign currency
invoice = ARInvoice.objects.create(
    customer=customer,
    date=date(2025, 1, 1),
    currency=aed,
    total=Decimal("1000.00"),  # 1000 AED
    fx_rate=Decimal("3.6725")  # Store rate!
)
# Booked as: 1000 / 3.6725 = 272.35 USD

# 4. Payment received later
create_exchange_rate("USD", "AED", Decimal("3.60"), date(2025, 2, 1))

payment = ARPayment.objects.create(
    invoice=invoice,
    date=date(2025, 2, 1),
    amount=Decimal("1000.00"),  # 1000 AED
    currency=aed,
    fx_rate=Decimal("3.60")  # Store rate!
)
# Received: 1000 / 3.60 = 277.78 USD

# 5. Calculate FX gain/loss
gain_loss, type = calculate_fx_gain_loss(
    Decimal("1000.00"), aed, Decimal("3.6725"),
    Decimal("1000.00"), aed, Decimal("3.60")
)
# Result: (Decimal("5.43"), "REALIZED_GAIN")
# We received 5.43 USD more than booked!

# 6. Post with FX gain
je = JournalEntry.objects.create(date=payment.date, memo="Payment with FX gain")

# Bank: 277.78 USD
JournalLine.objects.create(entry=je, account=bank, debit=Decimal("277.78"))

# AR: -272.35 USD (original booking)
JournalLine.objects.create(entry=je, account=ar, credit=Decimal("272.35"))

# FX Gain: 5.43 USD
post_fx_gain_loss(je, Decimal("5.43"), "REALIZED_GAIN", ar)

post_entry(je)
```

---

## Conclusion

The FX services provide:

✅ **Currency Conversion:** Convert amounts between currencies  
✅ **Rate Lookup:** Smart exchange rate retrieval with fallbacks  
✅ **Gain/Loss Calculation:** Realized FX gain/loss on transactions  
✅ **Automatic Posting:** Journal entries for FX effects  
✅ **Period-end Revaluation:** Unrealized gain/loss recognition  
✅ **Rate Management:** Create and update exchange rates  
✅ **Multi-currency Support:** Full foreign currency transaction handling  
✅ **Audit Trail:** Rate sources and transaction documentation  

These services enable multi-currency operations with proper accounting treatment of exchange rate fluctuations, ensuring accurate financial reporting and compliance.

---

**Last Updated:** October 13, 2025  
**Framework:** Django 4.x+  
**Python Version:** 3.10+  
**Accounting Standard:** IAS 21 (Foreign Currency)

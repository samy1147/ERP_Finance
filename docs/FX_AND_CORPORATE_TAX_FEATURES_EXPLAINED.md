# FX (Foreign Exchange) and Corporate Tax Features - Backend Implementation Explained

**Date:** October 14, 2025  
**Status:** Backend fully implemented, Frontend NOT implemented

---

## Table of Contents
1. [Foreign Exchange (FX) Features](#foreign-exchange-fx-features)
2. [Corporate Tax Features](#corporate-tax-features)
3. [Use Cases and Workflows](#use-cases-and-workflows)
4. [Integration Points](#integration-points)

---

## Foreign Exchange (FX) Features

### Overview
Your backend has a **complete multi-currency foreign exchange system** that handles:
- Exchange rate management
- Currency conversions
- FX gain/loss calculations (realized and unrealized)
- Base currency configuration

### 1. Database Models (in `core/models.py`)

#### **Currency Model**
```python
class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)  # e.g., "USD", "AED", "EUR"
    name = models.CharField(max_length=64)              # e.g., "US Dollar"
    symbol = models.CharField(max_length=8)             # e.g., "$", "د.إ"
    is_base = models.BooleanField(default=False)        # Mark ONE currency as base/home currency
```

**Purpose:** 
- Define all currencies your business operates in
- Set ONE currency as your base/home currency (the currency you report financials in)
- Currently supported but NOT used in frontend

#### **ExchangeRate Model**
```python
class ExchangeRate(models.Model):
    from_currency = ForeignKey(Currency, related_name="rates_from")
    to_currency = ForeignKey(Currency, related_name="rates_to")
    rate_date = DateField()                              # Date this rate is effective
    rate = DecimalField(max_digits=18, decimal_places=6) # Exchange rate (1 from = rate × to)
    rate_type = CharField(choices=["SPOT", "AVERAGE", "FIXED", "CLOSING"])
    source = CharField()                                 # e.g., "Central Bank", "Manual"
    is_active = BooleanField(default=True)
```

**Purpose:**
- Store historical and current exchange rates between currency pairs
- Support different rate types:
  - **SPOT:** Real-time/current market rate
  - **AVERAGE:** Period average rate (e.g., monthly average)
  - **FIXED:** Fixed rate for contracts
  - **CLOSING:** Period-end closing rate for revaluation

**Example:**
```
USD/AED on 2025-10-14: rate = 3.6725
Means: 1 USD = 3.6725 AED
```

#### **FXGainLossAccount Model**
```python
class FXGainLossAccount(models.Model):
    account = OneToOneField('finance.Account')
    gain_loss_type = CharField(choices=[
        "REALIZED_GAIN",    # Gain when transaction settles
        "REALIZED_LOSS",    # Loss when transaction settles
        "UNREALIZED_GAIN",  # Paper gain on open positions
        "UNREALIZED_LOSS"   # Paper loss on open positions
    ])
    is_active = BooleanField(default=True)
```

**Purpose:**
- Map FX gain/loss types to specific GL accounts
- Required for automatic posting of FX differences

**Example Configuration:**
```
REALIZED_GAIN → Account 7200 (FX Gain - Income)
REALIZED_LOSS → Account 6200 (FX Loss - Expense)
UNREALIZED_GAIN → Account 7210 (Unrealized FX Gain)
UNREALIZED_LOSS → Account 6210 (Unrealized FX Loss)
```

---

### 2. FX Services (in `finance/fx_services.py`)

#### **Core Functions:**

##### `get_base_currency()`
```python
def get_base_currency() -> Currency:
    """Get the company's base/home currency (is_base=True)"""
```
**Use Case:** Determine which currency to report financials in

##### `get_exchange_rate(from_currency, to_currency, rate_date, rate_type="SPOT")`
```python
def get_exchange_rate(...) -> Decimal:
    """
    Get exchange rate for a specific date.
    - Tries exact date first
    - Falls back to most recent rate before date
    - Can use inverse rate (to/from) if direct rate not available
    - Returns 1.0 if same currency
    """
```
**Use Case:** Get rate for converting invoice amounts, payments, etc.

##### `convert_amount(amount, from_currency, to_currency, rate_date, rate_type="SPOT")`
```python
def convert_amount(...) -> Decimal:
    """
    Convert amount between currencies using exchange rate.
    Returns amount rounded to 2 decimal places.
    """
```
**Use Case:** Convert foreign currency invoice to base currency

**Example:**
```python
# Convert 1000 USD to AED on 2025-10-14
converted = convert_amount(
    amount=Decimal('1000'),
    from_currency=usd_currency,
    to_currency=aed_currency,
    rate_date=date(2025, 10, 14),
    rate_type="SPOT"
)
# Result: 3672.50 AED (if rate is 3.6725)
```

##### `calculate_fx_gain_loss(...)`
```python
def calculate_fx_gain_loss(
    original_amount, original_currency, original_rate,
    settlement_amount, settlement_currency, settlement_rate
) -> Tuple[Decimal, str]:
    """
    Calculate realized FX gain/loss on settled transactions.
    Returns: (amount, "REALIZED_GAIN" or "REALIZED_LOSS")
    """
```

**Use Case:** When an invoice is paid, calculate the FX difference

**Example Scenario:**
```
1. Invoice created: $1000 on Jan 1 @ rate 3.60 = AED 3,600
2. Payment received: $1000 on Jan 31 @ rate 3.70 = AED 3,700
3. FX Gain: AED 100 (company received more AED than expected)
```

##### `post_fx_gain_loss(journal_entry, gain_loss_amount, gain_loss_type, contra_account)`
```python
def post_fx_gain_loss(...) -> None:
    """
    Post FX gain/loss journal lines to existing journal entry.
    Automatically creates DR/CR entries based on gain or loss.
    """
```

**Use Case:** Automatically record FX differences in journal entries

##### `create_exchange_rate(from_currency_code, to_currency_code, rate, rate_date, ...)`
```python
def create_exchange_rate(...) -> ExchangeRate:
    """
    Create or update exchange rate using currency codes.
    Uses update_or_create for idempotency.
    """
```

**Use Case:** Manual rate entry or bulk import from external source

##### `revalue_open_balances(as_of_date, account_code, revaluation_currency)`
```python
def revalue_open_balances(...) -> JournalEntry:
    """
    Revalue open AR/AP balances for unrealized FX gain/loss.
    (Currently a placeholder for period-end revaluation)
    """
```

**Use Case:** Month-end/year-end unrealized FX gain/loss on open invoices

---

### 3. FX API Endpoints (in `finance/api.py`)

#### **1. Exchange Rate CRUD - `/api/fx/rates/`**
- **ViewSet:** `ExchangeRateViewSet` (ModelViewSet)
- **Methods:** GET (list/detail), POST (create), PUT/PATCH (update), DELETE
- **Query Filters:**
  - `from_currency` - Filter by source currency code
  - `to_currency` - Filter by target currency code
  - `rate_type` - Filter by rate type (SPOT, AVERAGE, etc.)
  - `date_from` - Filter rates from date
  - `date_to` - Filter rates to date

**Example Requests:**
```bash
# List all USD to AED rates
GET /api/fx/rates/?from_currency=USD&to_currency=AED

# Get SPOT rates for October
GET /api/fx/rates/?rate_type=SPOT&date_from=2025-10-01&date_to=2025-10-31

# Create new rate
POST /api/fx/rates/
{
  "from_currency": 1,  # Currency ID
  "to_currency": 2,
  "rate_date": "2025-10-14",
  "rate": "3.6725",
  "rate_type": "SPOT",
  "source": "Central Bank of UAE"
}
```

#### **2. Currency Conversion - `/api/fx/convert/`**
- **View:** `CurrencyConvertView` (APIView)
- **Method:** POST
- **Purpose:** Convert an amount between currencies

**Request:**
```json
POST /api/fx/convert/
{
  "amount": "1000.00",
  "from_currency_code": "USD",
  "to_currency_code": "AED",
  "rate_date": "2025-10-14",
  "rate_type": "SPOT"  // optional, defaults to SPOT
}
```

**Response:**
```json
{
  "from_currency": "USD",
  "to_currency": "AED",
  "original_amount": 1000.00,
  "exchange_rate": 3.6725,
  "converted_amount": 3672.50,
  "rate_date": "2025-10-14",
  "rate_type": "SPOT"
}
```

#### **3. Create Exchange Rate (Simplified) - `/api/fx/create-rate/`**
- **View:** `CreateExchangeRateView` (APIView)
- **Method:** POST
- **Purpose:** Create rate using currency codes (easier than using IDs)

**Request:**
```json
POST /api/fx/create-rate/
{
  "from_currency_code": "USD",
  "to_currency_code": "AED",
  "rate": "3.6725",
  "rate_date": "2025-10-14",
  "rate_type": "SPOT",
  "source": "Manual Entry"
}
```

#### **4. FX Gain/Loss Accounts - `/api/fx/accounts/`**
- **ViewSet:** `FXGainLossAccountViewSet` (ModelViewSet)
- **Methods:** GET (list/detail), POST (create), PUT/PATCH (update), DELETE
- **Purpose:** Configure which GL accounts to use for FX gains/losses

**Example:**
```json
POST /api/fx/accounts/
{
  "account": 15,  // Account ID for "FX Gain - Income"
  "gain_loss_type": "REALIZED_GAIN",
  "is_active": true,
  "notes": "Realized gains from currency conversions"
}
```

#### **5. Base Currency - `/api/fx/base-currency/`**
- **View:** `BaseCurrencyView` (APIView)
- **Method:** GET
- **Purpose:** Get the company's base/home currency

**Response:**
```json
{
  "code": "AED",
  "name": "UAE Dirham",
  "symbol": "د.إ"
}
```

---

### 4. Business Workflows Supported

#### **Workflow A: Multi-Currency Invoice**
1. Customer wants invoice in USD, company reports in AED
2. Create invoice in USD: $1,000
3. On posting date, system:
   - Looks up USD/AED rate for that date
   - Converts to AED: 1000 × 3.6725 = AED 3,672.50
   - Posts journal entry:
     ```
     DR Accounts Receivable (USD customer) - AED 3,672.50
     CR Revenue                             - AED 3,672.50
     ```

#### **Workflow B: Payment with FX Gain/Loss**
1. Invoice created: $1,000 on Oct 1 @ rate 3.60 = AED 3,600 recorded
2. Payment received: $1,000 on Oct 31 @ rate 3.70 = AED 3,700 received
3. System posts:
   ```
   DR Bank (USD account)      - AED 3,700
   CR Accounts Receivable     - AED 3,600
   CR FX Gain (Income)        - AED 100     <-- Realized gain
   ```

#### **Workflow C: Period-End Revaluation**
1. Month-end: Oct 31
2. Open invoices still unpaid in foreign currencies
3. System revalues at closing rate:
   - Invoice $1,000 booked @ 3.60 = AED 3,600
   - Current rate: 3.70
   - Unrealized gain: AED 100
4. Posts adjustment:
   ```
   DR Accounts Receivable           - AED 100
   CR Unrealized FX Gain (Income)   - AED 100
   ```
5. When paid later, reverse unrealized and book realized

---

## Corporate Tax Features

### Overview
Your backend has a **complete corporate tax management system** that handles:
- Country-specific tax rules
- Profit calculation from journal entries
- Tax accrual journal entries
- Tax filing workflow (Accrued → Filed → Locked/Reversed)
- Multi-period tax tracking

### 1. Database Models (in `finance/models.py`)

#### **CorporateTaxRule Model**
```python
class CorporateTaxRule(models.Model):
    country = CharField(choices=["AE", "SA", "EG", "IN"])  # UAE, KSA, Egypt, India
    rate = DecimalField()           # e.g., 9.0 = 9%
    threshold = DecimalField()      # Optional profit threshold
    active = BooleanField()
    notes = CharField()
```

**Purpose:**
- Define country-specific corporate tax rates
- Support profit thresholds (e.g., "tax only if profit > AED 375,000")

**Example:**
```
UAE: 9% corporate tax, threshold = AED 375,000
KSA: 20% corporate tax, no threshold
```

#### **CorporateTaxFiling Model**
```python
class CorporateTaxFiling(models.Model):
    country = CharField()
    period_start = DateField()
    period_end = DateField()
    organization_id = IntegerField()     # Optional multi-entity support
    accrual_journal = OneToOneField(JournalEntry)   # The tax accrual JE
    reversal_journal = OneToOneField(JournalEntry)  # If reversed
    status = CharField(choices=["ACCRUED", "FILED", "REVERSED"])
    filed_at = DateTimeField()
    notes = CharField()
```

**Purpose:**
- Track each tax period filing
- Link to journal entries that created the accrual
- Enforce workflow: ACCRUED → FILED (locked) → optionally REVERSED

**Status Meanings:**
- **ACCRUED:** Tax calculated and journal posted, but not yet filed with government
- **FILED:** Officially filed, locked from changes
- **REVERSED:** Accrual reversed (mistake or adjustment)

---

### 2. Corporate Tax Services (in `finance/services.py`)

#### **Core Functions:**

##### `accrue_corporate_tax(country, date_from, date_to, org_id=None)`
```python
def accrue_corporate_tax(...) -> Tuple[JournalEntry, dict]:
    """
    1. Calculate profit from posted journal entries in period
       Profit = Income - Expenses (from JournalLines)
    2. Apply country-specific tax rule and threshold
    3. Calculate tax amount
    4. Create and post journal entry:
       DR Corporate Tax Expense
       CR Corporate Tax Payable
    5. Return journal entry and calculation metadata
    """
```

**Calculation Logic:**
```python
# Sum all posted journal lines in period
income = sum(credit - debit) for income accounts
expense = sum(debit - credit) for expense accounts
profit = income - expense

# Apply threshold (if configured)
if rule.threshold and profit > rule.threshold:
    tax_base = profit - threshold
else:
    tax_base = profit

# Calculate tax
tax_amount = tax_base × (rate / 100)

# Post journal
DR Corporate Tax Expense    - tax_amount
CR Corporate Tax Payable    - tax_amount
```

**Example:**
```
Period: Q1 2025 (Jan 1 - Mar 31)
Income: AED 1,000,000
Expenses: AED 600,000
Profit: AED 400,000

UAE Rule: 9% rate, AED 375,000 threshold
Taxable profit: AED 400,000 - AED 375,000 = AED 25,000
Tax: AED 25,000 × 9% = AED 2,250

Journal Entry:
DR Tax Expense (6500)     - AED 2,250
CR Tax Payable (2500)     - AED 2,250
```

##### `accrue_corporate_tax_with_filing(...)`
```python
def accrue_corporate_tax_with_filing(...) -> Tuple[CorporateTaxFiling, JournalEntry, dict]:
    """
    Same as accrue_corporate_tax BUT:
    - Creates CorporateTaxFiling record to track the filing
    - Idempotent: if filing exists with ACCRUED status, returns existing
    - If already FILED and allow_override=False, raises error
    """
```

**Purpose:** Production-ready version with filing tracking

##### `file_corporate_tax(filing_id)`
```python
def file_corporate_tax(filing_id: int) -> CorporateTaxFiling:
    """
    Mark filing as FILED (officially submitted to tax authority).
    - Only works if status = ACCRUED
    - Locks the filing from reversal (unless override)
    - Sets filed_at timestamp
    """
```

**Purpose:** Record that tax return was officially filed

##### `reverse_corporate_tax_filing(filing_id)`
```python
def reverse_corporate_tax_filing(filing_id: int) -> JournalEntry:
    """
    Reverse the tax accrual:
    - Creates reversing journal entry
    - Changes status to REVERSED
    - Only works if status = ACCRUED (not FILED)
    """
```

**Purpose:** Undo tax accrual if mistake or adjustment needed

##### `seed_vat_presets(effective_from=None)`
```python
def seed_vat_presets(...) -> list:
    """
    Pre-populate TaxRate table with common VAT rates for:
    - UAE: 5% standard, 0% zero-rated, 0% exempt
    - Saudi Arabia: 15% standard, etc.
    - Egypt: 14% standard
    - India: 18% GST standard, etc.
    """
```

**Purpose:** Quick setup of common tax rates

---

### 3. Corporate Tax API Endpoints (in `finance/api.py`)

#### **1. Seed VAT Presets - `/api/tax/seed-presets/`**
- **View:** `SeedVATPresets` (APIView)
- **Method:** POST
- **Purpose:** Populate common VAT/GST rates

**Request:**
```json
POST /api/tax/seed-presets/
{
  "effective_from": "2025-01-01"  // optional
}
```

**Response:**
```json
{
  "created_ids": [1, 2, 3, 4, 5, 6, 7, 8]  // IDs of created TaxRate records
}
```

#### **2. List Tax Rates - `/api/tax/rates/`**
- **View:** `ListTaxRates` (APIView)
- **Method:** GET
- **Query Param:** `?country=AE` (optional filter)
- **Purpose:** Get all tax rates, optionally filtered by country

**Response:**
```json
[
  {
    "id": 1,
    "name": "UAE VAT Standard",
    "rate": 5.0,
    "country": "AE",
    "category": "STANDARD",
    "code": "VAT5",
    "effective_from": "2018-01-01",
    "is_active": true
  },
  ...
]
```

#### **3. Corporate Tax Accrual - `/api/tax/corporate-accrual/`**
- **View:** `CorporateTaxAccrual` (APIView)
- **Method:** POST
- **Purpose:** Calculate and accrue corporate tax for a period

**Request:**
```json
POST /api/tax/corporate-accrual/
{
  "country": "AE",
  "date_from": "2025-01-01",
  "date_to": "2025-03-31",
  "org_id": null,         // optional for multi-entity
  "override": false       // allow override of existing filing
}
```

**Response (Success):**
```json
{
  "created": true,
  "filing_id": 5,
  "journal": {
    "id": 128,
    "date": "2025-03-31",
    "currency": {"code": "AED"},
    "memo": "Corporate tax accrual AE 2025-01-01..2025-03-31 on profit 25000",
    "posted": true,
    "lines": [
      {
        "account_code": "6500",
        "account_name": "Corporate Tax Expense",
        "debit": "2250.00",
        "credit": "0.00"
      },
      {
        "account_code": "2500",
        "account_name": "Corporate Tax Payable",
        "debit": "0.00",
        "credit": "2250.00"
      }
    ]
  },
  "meta": {
    "profit": 400000.0,
    "tax_base": 25000.0,
    "tax": 2250.0
  }
}
```

**Response (No Tax Due):**
```json
{
  "created": false,
  "meta": {
    "profit": 300000.0,    // Below threshold
    "tax_base": 0.0,
    "tax": 0.0
  }
}
```

#### **4. Corporate Tax Filing Detail - `/api/tax/corporate-filing/{filing_id}/`**
- **View:** `CorporateTaxFilingDetail` (APIView)
- **Method:** GET
- **Purpose:** Get complete details of a tax filing

**Response:**
```json
{
  "id": 5,
  "country": "AE",
  "period_start": "2025-01-01",
  "period_end": "2025-03-31",
  "organization_id": null,
  "status": "ACCRUED",
  "filed_at": null,
  "notes": "",
  "accrual_journal_id": 128,
  "reversal_journal_id": null,
  "accrual_journal": { /* full journal details */ },
  "reversal_journal": null
}
```

#### **5. File Corporate Tax - `/api/tax/corporate-file/{filing_id}/`**
- **View:** `CorporateTaxFile` (APIView)
- **Methods:** GET (info), POST (file it)

**POST Request:**
```bash
POST /api/tax/corporate-file/5/
```

**Response:**
```json
{
  "filing_id": 5,
  "status": "FILED",
  "filed_at": "2025-10-14T10:30:00Z"
}
```

**Error (already filed):**
```json
{
  "detail": "Only ACCRUED filings can be marked FILED.",
  "current_status": "FILED",
  "required_status": "ACCRUED"
}
```

#### **6. Reverse Corporate Tax - `/api/tax/corporate-reverse/{filing_id}/`**
- **View:** `CorporateTaxReverse` (APIView)
- **Methods:** GET (check if reversible), POST (reverse it)

**POST Request:**
```bash
POST /api/tax/corporate-reverse/5/
```

**Response:**
```json
{
  "reversal_journal": {
    "id": 129,
    "date": "2025-10-14",
    "memo": "Reversal of Corporate tax accrual...",
    "posted": true,
    "lines": [
      {
        "account_code": "2500",
        "account_name": "Corporate Tax Payable",
        "debit": "2250.00",
        "credit": "0.00"
      },
      {
        "account_code": "6500",
        "account_name": "Corporate Tax Expense",
        "debit": "0.00",
        "credit": "2250.00"
      }
    ]
  }
}
```

#### **7. Corporate Tax Breakdown - `/api/tax/corporate-breakdown/`**
- **View:** `CorporateTaxBreakdown` (APIView)
- **Method:** GET
- **Query Params:** `?country=AE&date_from=2025-01-01&date_to=2025-12-31`
- **Purpose:** Get tax calculation breakdown for analysis
- *(Implementation details in services.py)*

---

## Use Cases and Workflows

### Corporate Tax Workflow

#### **Quarterly Tax Accrual (Typical UAE Company)**

**Scenario:** Company needs to accrue Q1 2025 corporate tax

**Step 1: Calculate and Accrue Tax**
```http
POST /api/tax/corporate-accrual/
{
  "country": "AE",
  "date_from": "2025-01-01",
  "date_to": "2025-03-31"
}
```

**System Actions:**
1. Queries all posted journal entries in Q1
2. Sums income accounts (credits - debits)
3. Sums expense accounts (debits - credits)
4. Calculates profit
5. Applies UAE rule (9%, AED 375K threshold)
6. Creates journal entry for tax
7. Creates CorporateTaxFiling record with status "ACCRUED"

**Step 2: Review Accrual**
```http
GET /api/tax/corporate-filing/5/
```

**Step 3: File Tax Return (After Government Submission)**
```http
POST /api/tax/corporate-file/5/
```

**System Actions:**
1. Validates status is "ACCRUED"
2. Changes status to "FILED"
3. Sets filed_at timestamp
4. Locks filing from reversal

**Step 4 (If Mistake): Reverse Before Filing**
```http
POST /api/tax/corporate-reverse/5/
```

**System Actions:**
1. Creates reversing journal entry
2. Changes status to "REVERSED"
3. Allows re-accrual with correct data

---

### FX Workflow

#### **Multi-Currency Invoice and Payment**

**Scenario:** UAE company (base AED) sells to US customer, invoice in USD

**Step 1: Create Exchange Rate (if not exists)**
```http
POST /api/fx/create-rate/
{
  "from_currency_code": "USD",
  "to_currency_code": "AED",
  "rate": "3.6725",
  "rate_date": "2025-10-01",
  "rate_type": "SPOT"
}
```

**Step 2: Create Invoice in USD**
```http
POST /api/ar/invoices/
{
  "customer": 5,
  "invoice_no": "INV-001",
  "invoice_date": "2025-10-01",
  "currency": "USD",  // Stored as USD currency ID
  "items": [
    {
      "description": "Consulting services",
      "quantity": 1,
      "unit_price": 1000,
      "tax_rate": 1
    }
  ]
}
```

**Step 3: Post Invoice**
```http
POST /api/ar/invoices/25/post-gl/
```

**System Actions:**
1. Looks up USD/AED rate for 2025-10-01 (finds 3.6725)
2. Converts $1,000 to AED: 1000 × 3.6725 = AED 3,672.50
3. Posts journal:
   ```
   DR Accounts Receivable (1100) - AED 3,672.50
   CR Revenue (4000)             - AED 3,672.50
   ```

**Step 4: Customer Pays (Rate Changed)**
```http
POST /api/ar/payments/
{
  "invoice": 25,
  "payment_date": "2025-10-31",
  "amount": 1000,
  "currency": "USD",  // Payment in USD
  "bank_account": 3
}
```

**System Actions:**
1. Looks up USD/AED rate for 2025-10-31 (finds 3.70)
2. Converts $1,000 to AED: 1000 × 3.70 = AED 3,700
3. Calculates FX gain: AED 3,700 - AED 3,672.50 = AED 27.50
4. Posts journal:
   ```
   DR Bank Account (1010)       - AED 3,700.00
   CR Accounts Receivable (1100) - AED 3,672.50
   CR FX Gain (7200)            - AED 27.50     <-- Realized gain
   ```

**Step 5: Period-End Revaluation (Unrealized)**
For invoices still unpaid at month-end:
```http
POST /api/fx/revalue/  // (Placeholder - needs implementation)
{
  "as_of_date": "2025-10-31",
  "account_code": "1100"
}
```

**System Actions:**
1. Finds open AR invoices in foreign currencies
2. Revalues at closing rate
3. Posts unrealized gain/loss adjustments

---

## Integration Points

### How FX Integrates with Existing System

1. **Invoice Posting:**
   - `gl_post_from_ar_balanced()` could check invoice currency
   - If ≠ base currency, look up exchange rate
   - Convert amounts before posting

2. **Payment Posting:**
   - `post_ar_payment()` could compare:
     - Invoice booking rate vs payment rate
     - Calculate FX difference
     - Call `post_fx_gain_loss()`

3. **Trial Balance:**
   - All amounts already in base currency (converted on posting)
   - No special handling needed

### How Corporate Tax Integrates

1. **Journal Entries:**
   - Tax accrual uses standard `JournalEntry` and `JournalLine`
   - Integrates with existing GL system

2. **Accounts Required:**
   - Must have accounts configured:
     - Corporate Tax Expense (e.g., 6500 - Expense type)
     - Corporate Tax Payable (e.g., 2500 - Liability type)

3. **Period Close:**
   - Run tax accrual as part of period-end process
   - File tax return after submission to government

---

## ⚠️ What's Currently Implemented in Frontend

### ✅ Basic Currency Selection (Partial)
**Status:** Currency selection exists in invoice forms but NO management UI

**Where It Works:**
- AR/AP Invoice creation forms have currency dropdown
- Customer/Supplier forms have currency field
- Invoice detail pages show currency code

**What It Does:**
```typescript
// In invoice creation form
const [currencies, setCurrencies] = useState<Currency[]>([]);
const [formData, setFormData] = useState({
  currency: '1', // Default currency ID
  // ...other fields
});

// Fetches currencies from API
const fetchCurrencies = async () => {
  const response = await currenciesAPI.list();
  setCurrencies(response.data);
};

// Currency dropdown in form
<select value={formData.currency} onChange={...}>
  {currencies.map(c => (
    <option value={c.id}>{c.code} - {c.name}</option>
  ))}
</select>
```

**What It DOESN'T Do:**
- ❌ No currency management page (list/create/edit/delete)
- ❌ No exchange rate integration (invoice stored in foreign currency but not converted)
- ❌ No base currency display/configuration
- ❌ No currency symbols shown in amounts

### ✅ Tax Rate Selection with Smart Filtering (Partial)
**Status:** Tax rates are used in invoices with country-based filtering

**Where It Works:**
- AR/AP Invoice line items have tax rate dropdown
- Auto-filters by customer/supplier country
- Calculates tax amount automatically

**What It Does:**
```typescript
// In invoice creation form
const [taxRates, setTaxRates] = useState<TaxRate[]>([]);
const [formData, setFormData] = useState({
  country: 'AE', // Default or from customer
  // ...
});

// Fetches tax rates filtered by country
const fetchTaxRates = async (country?: string) => {
  const response = await taxRatesAPI.list(country);
  setTaxRates(response.data);
};

// Auto-reload when country changes
useEffect(() => {
  if (formData.country) {
    fetchTaxRates(formData.country);
  }
}, [formData.country]);

// When customer selected, auto-set country
const handleCustomerChange = (customerId: string) => {
  const customer = customers.find(c => c.id === parseInt(customerId));
  if (customer && customer.country) {
    setFormData(prev => ({ 
      ...prev, 
      customer: customerId, 
      country: customer.country 
    }));
    // This triggers tax rate reload via useEffect
  }
};

// Tax rate dropdown per line item
<select value={item.tax_rate} onChange={...}>
  <option value="">No Tax</option>
  {taxRates.map(rate => (
    <option value={rate.id}>
      {rate.name} ({rate.rate}%)
    </option>
  ))}
</select>
```

**Example User Flow:**
1. User creates AR Invoice
2. Selects Customer: "ABC Company (United Arab Emirates)"
3. System auto-sets `country = "AE"`
4. Tax rates auto-reload: Only UAE rates shown (VAT 5%, Zero-rated, etc.)
5. User adds line item, selects "UAE VAT Standard (5%)"
6. Tax calculated: Subtotal × 5% = Tax amount
7. Total updated automatically

**What It DOESN'T Do:**
- ❌ No tax rate management page (list/create/edit/delete)
- ❌ No "Seed Presets" button to populate default rates
- ❌ No effective date management (effective_from/to)
- ❌ Cannot see all rates across countries in one view

### ❌ Exchange Rates (NOT Implemented)
**Status:** Zero frontend implementation

- ❌ No exchange rate pages
- ❌ No rate entry forms
- ❌ No currency conversion
- ❌ No FX gain/loss tracking
- ❌ Invoices don't convert to base currency

### ❌ Corporate Tax (NOT Implemented)
**Status:** Zero frontend implementation

- ❌ No tax accrual pages
- ❌ No tax filing management
- ❌ No tax dashboard

---

## What's Missing (Frontend Implementation)

### FX Features Needed:

1. **Exchange Rate Management Page**
   - List rates with filters (currency pair, date range, rate type)
   - Add/edit/delete rates
   - Bulk import from CSV/API
   - Rate history chart

2. **Currency Converter Widget**
   - Quick conversion tool
   - Show current/historical rates
   - Could be in sidebar or header

3. **FX Configuration Page**
   - Set base currency
   - Configure FX gain/loss accounts
   - Set default rate types

4. **Multi-Currency in Invoice Forms**
   - Currency selector
   - Show both foreign and base currency amounts
   - Real-time rate lookup

5. **FX Reports**
   - Realized gain/loss report
   - Unrealized gain/loss report
   - Open foreign currency positions

### Corporate Tax Features Needed:

1. **Tax Dashboard**
   - List all tax periods
   - Status indicators (Accrued/Filed/Reversed)
   - Quick actions (File, Reverse)

2. **Tax Accrual Wizard**
   - Select country, date range
   - Preview calculation
   - Confirm and post

3. **Tax Filing Detail Page**
   - Show filing info
   - Display accrual journal
   - Actions: File, Reverse (with confirmation)
   - Show filing status timeline

4. **Tax Configuration**
   - Manage CorporateTaxRule records
   - Set rates and thresholds per country
   - Configure tax accounts

5. **Tax Reports**
   - Tax breakdown by period
   - Year-to-date tax summary
   - Export for tax return preparation

---

## Summary

### What You Have (Backend):

✅ **Complete FX System:**
- Multi-currency support
- Exchange rate management
- Automatic currency conversion
- Realized FX gain/loss calculation
- Unrealized FX gain/loss (foundation)
- 5 REST API endpoints

✅ **Complete Corporate Tax System:**
- Country-specific tax rules
- Automatic profit calculation
- Tax accrual with journal entries
- Filing workflow (Accrued → Filed → Reversed)
- Multi-period tracking
- 6 REST API endpoints

### What You Need (Frontend):

❌ **FX UI:**
- Rate management pages
- Currency converter
- Configuration screens
- Multi-currency invoice views
- FX reports

❌ **Corporate Tax UI:**
- Tax dashboard
- Accrual wizard
- Filing management
- Tax configuration
- Tax reports

### Next Steps:

1. **Decide Priority:** FX or Corporate Tax first?
2. **Design UI:** Wireframes for key screens
3. **Implement Step-by-Step:**
   - Start with read-only views (lists, details)
   - Add create/edit forms
   - Add complex workflows (filing, reversal)
4. **Test with Real Data:** Use actual exchange rates and tax calculations

---

**Your backend is production-ready for multi-currency and corporate tax. You just need to build the frontend UI to access these powerful features!**

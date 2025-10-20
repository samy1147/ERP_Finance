# Finance Services Documentation (services.py)

## Overview
This file contains business logic functions that power the Finance module. It handles accounting operations, calculations, GL posting, payments, tax accrual, and invoice reversals.

---

## File Location
```
finance/services.py
```

---

## Configuration

### `DEFAULT_ACCOUNTS` / `ACCOUNT_CODES`
**Purpose:** Centralized account code mappings

**Default Codes:**
```python
{
    "BANK": "1000",         # Cash/Bank account
    "AR": "1100",           # Accounts Receivable control
    "AP": "2000",           # Accounts Payable control
    "VAT_OUT": "2100",      # Output VAT (payable)
    "VAT_IN": "2110",       # Input VAT (recoverable)
    "REV": "4000",          # Revenue
    "EXP": "5000",          # Expense
    "TAX_CORP_PAYABLE": "2400",  # Corporate tax liability
    "TAX_CORP_EXP": "6900",      # Corporate tax expense
    "FX_GAIN": "7150",      # FX gain (income)
    "FX_LOSS": "8150",      # FX loss (expense)
}
```

**Usage:** Override in `settings.py`:
```python
FINANCE_ACCOUNTS = {
    "BANK": "1010",  # Custom code
    "AR": "1200",
    # ... etc
}
```

---

## Core Functions

### 1. `q2(x: Decimal) -> Decimal`

**Purpose:** Rounds Decimal to 2 decimal places

**Parameters:**
- `x`: Decimal to round

**Returns:** Rounded Decimal

**Logic:** Uses ROUND_HALF_UP rounding mode

**Usage:**
```python
q2(Decimal("10.567"))  # Returns Decimal("10.57")
q2(Decimal("10.564"))  # Returns Decimal("10.56")
```

---

### 2. `amount_with_tax(qty, price, rate)`

**Purpose:** Calculates subtotal, tax, and total for a line item

**Parameters:**
- `qty`: Quantity (Decimal or numeric)
- `price`: Unit price (Decimal or numeric)
- `rate`: Tax rate percentage (Decimal or numeric)

**Returns:** Tuple `(subtotal, tax, total)` - all rounded to 2 decimals

**Formula:**
```
subtotal = qty × price
tax = subtotal × (rate / 100)
total = subtotal + tax
```

**Usage:**
```python
sub, tax, tot = amount_with_tax(10, 100, 5)
# sub = Decimal("1000.00")
# tax = Decimal("50.00")
# tot = Decimal("1050.00")
```

---

## Reporting Functions

### 3. `build_trial_balance(date_from=None, date_to=None)`

**Purpose:** Generates trial balance report

**Parameters:**
- `date_from`: Start date filter (optional)
- `date_to`: End date filter (optional)

**Returns:** List of dicts with final TOTAL row
```python
[
    {"code": "1000", "name": "Cash", "debit": 5000.00, "credit": 0.00},
    {"code": "4000", "name": "Revenue", "debit": 0.00, "credit": 5000.00},
    {"code": "TOTAL", "name": "", "debit": 5000.00, "credit": 5000.00}
]
```

**Logic:**
1. Queries posted journal lines in date range
2. Groups by account code
3. Sums debits and credits per account
4. Adds TOTAL row

**Usage:**
```python
# All posted entries
tb = build_trial_balance()

# For specific period
tb = build_trial_balance(date(2025, 1, 1), date(2025, 3, 31))
```

---

### 4. `ar_totals(invoice: ARInvoice) -> dict`

**Purpose:** Calculates all totals for an AR invoice

**Parameters:**
- `invoice`: ARInvoice instance

**Returns:** Dict with 5 keys
```python
{
    "subtotal": Decimal("1000.00"),   # Sum of line amounts
    "tax": Decimal("50.00"),          # Total tax
    "total": Decimal("1050.00"),      # Gross total
    "paid": Decimal("500.00"),        # Amount paid
    "balance": Decimal("550.00")      # Remaining balance
}
```

**Logic:**
1. Loops through all invoice items
2. Calls `line_rate()` to get tax rate for each item
3. Calls `amount_with_tax()` for each line
4. Sums all amounts
5. Sums all payments
6. Calculates balance = total - paid

**Example:**
```python
invoice = ARInvoice.objects.get(id=1)
totals = ar_totals(invoice)
print(f"Balance: {totals['balance']}")
```

---

### 5. `ap_totals(invoice: APInvoice) -> dict`

**Purpose:** Calculates all totals for an AP invoice

**Parameters:**
- `invoice`: APInvoice instance

**Returns:** Same structure as `ar_totals()`

**Difference:** Uses APInvoice and APItem models instead of AR models

---

### 6. `build_ar_aging(as_of=None, b1=30, b2=30, b3=30)`

**Purpose:** Generates Accounts Receivable aging report

**Parameters:**
- `as_of`: Report date (default: today)
- `b1`, `b2`, `b3`: Bucket sizes in days (default: 30 each)

**Returns:** Dict with structure:
```python
{
    "as_of": "2025-01-15",
    "buckets": ["Current", "1–30", "31–60", "61–90", ">90"],
    "invoices": [
        {
            "invoice_id": 1,
            "number": "INV-001",
            "customer": "Acme Corp",
            "date": "2024-12-01",
            "due_date": "2025-01-01",
            "days_overdue": 14,
            "balance": 1050.00,
            "bucket": "1–30"
        }
    ],
    "summary": {
        "Current": 5000.00,
        "1–30": 3000.00,
        "31–60": 1500.00,
        "61–90": 500.00,
        ">90": 200.00,
        "TOTAL": 10200.00
    }
}
```

**Logic:**
1. Gets all AR invoices with balances > 0
2. Calculates days overdue = as_of - due_date
3. Buckets each invoice by days overdue
4. Sums totals per bucket
5. Returns detailed list + summary

**Usage:**
```python
# Standard 30-day buckets
aging = build_ar_aging()

# Custom buckets (15, 30, 45 days)
aging = build_ar_aging(b1=15, b2=30, b3=45)
```

---

### 7. `build_ap_aging(as_of=None, b1=30, b2=30, b3=30)`

**Purpose:** Generates Accounts Payable aging report

**Parameters:** Same as `build_ar_aging()`

**Returns:** Same structure but with `supplier` instead of `customer`

**Difference:** Uses APInvoice and supplier relationship

---

## Tax Functions

### 8. `resolve_tax_rate_for_date(country:str, category:str, as_of:date) -> Decimal`

**Purpose:** Finds effective tax rate for a specific date

**Parameters:**
- `country`: Country code (e.g., "AE", "SA")
- `category`: Tax category (e.g., "STANDARD", "ZERO")
- `as_of`: Date to check rate for

**Returns:** Tax rate as Decimal (e.g., `Decimal("5.0")`)

**Logic:**
1. Queries TaxRate model for country + category
2. Filters where `effective_from <= as_of <= effective_to`
3. Returns most recent rate (by effective_from)
4. Returns 0% if not found

**Example:**
```python
rate = resolve_tax_rate_for_date("AE", "STANDARD", date(2025, 1, 15))
# Returns Decimal("5.0") for UAE VAT
```

---

### 9. `line_rate(item, inv_date) -> Decimal`

**Purpose:** Determines tax rate for an invoice line item

**Parameters:**
- `item`: ARItem or APItem instance
- `inv_date`: Invoice date

**Returns:** Tax rate as Decimal

**Priority Logic:**
1. **Explicit TaxRate FK:** If `item.tax_rate` exists, use it
2. **Country + Category:** If `item.tax_country` and `item.tax_category` set, resolve by date
3. **Default:** Return 0%

**Example:**
```python
# Item with explicit tax rate
item.tax_rate = TaxRate.objects.get(code="VAT5")
rate = line_rate(item, date(2025, 1, 15))  # Uses item.tax_rate.rate

# Item with country/category
item.tax_country = "AE"
item.tax_category = "STANDARD"
rate = line_rate(item, date(2025, 1, 15))  # Resolves to 5%
```

---

### 10. `seed_vat_presets(effective_from: date | None = None)`

**Purpose:** Seeds standard VAT/GST rates for multiple countries

**Parameters:**
- `effective_from`: Date rates become effective (optional)

**Returns:** List of created TaxRate IDs

**Preset Countries:**
- **AE** (UAE): 5%, 0%, Exempt
- **SA** (Saudi): 15%, 0%, Exempt
- **EG** (Egypt): 14%, 0%, Exempt
- **IN** (India): 18%, 0%, Exempt (GST)

**Usage:**
```python
created_ids = seed_vat_presets(date(2025, 1, 1))
print(f"Created {len(created_ids)} tax rates")
```

---

## GL Posting Functions

### 11. `_acct(key: str) -> Account`

**Purpose:** Helper to get Account by key from ACCOUNT_CODES

**Parameters:**
- `key`: Key from ACCOUNT_CODES dict (e.g., "AR", "BANK")

**Returns:** Account instance

**Raises:**
- ValueError if key not in ACCOUNT_CODES
- ValueError if account with that code doesn't exist

**Example:**
```python
ar_account = _acct("AR")  # Gets account with code "1100"
```

---

### 12. `post_entry(entry: JournalEntry)`

**Purpose:** Validates and posts a journal entry

**Parameters:**
- `entry`: JournalEntry instance with lines

**Returns:** Posted JournalEntry

**Validation:**
1. Calculates total debits and credits
2. Raises ValueError if unbalanced
3. Sets `posted=True`
4. Saves entry

**Example:**
```python
entry = JournalEntry.objects.create(date=date.today(), memo="Test")
JournalLine.objects.create(entry=entry, account=acct1, debit=100)
JournalLine.objects.create(entry=entry, account=acct2, credit=100)
post_entry(entry)  # Validates and posts
```

---

### 13. `gl_post_from_ar_balanced(invoice: ARInvoice)`

**Purpose:** Posts AR invoice to General Ledger (idempotent)

**Parameters:**
- `invoice`: ARInvoice instance

**Returns:** Tuple `(journal_entry, created: bool)`

**Idempotency:** If invoice already posted, returns existing JE

**Validation:**
1. Checks invoice has items
2. Validates totals > 0
3. Locks invoice row (select_for_update)

**Journal Entry:**
```
DR Accounts Receivable    1050.00
    CR Revenue             1000.00
    CR VAT Output            50.00
```

**Logic:**
1. Calculates totals using `ar_totals()`
2. Creates journal entry
3. Creates lines:
   - Debit AR for total amount
   - Credit Revenue for subtotal
   - Credit VAT_OUT for tax
4. Posts entry
5. Marks invoice as POSTED
6. Links journal to invoice

**Usage:**
```python
invoice = ARInvoice.objects.get(id=1)
journal, created = gl_post_from_ar_balanced(invoice)
if created:
    print("Posted to GL")
else:
    print("Already posted")
```

---

### 14. `gl_post_from_ap_balanced(invoice: APInvoice)`

**Purpose:** Posts AP invoice to General Ledger (idempotent)

**Parameters:**
- `invoice`: APInvoice instance

**Returns:** Tuple `(journal_entry, created: bool)`

**Journal Entry:**
```
DR Expense               1000.00
DR VAT Input               50.00
    CR Accounts Payable  1050.00
```

**Difference from AR:**
- Expense is debited (not Revenue credited)
- VAT Input is debited (recoverable tax)
- AP is credited (liability)

---

## Payment Functions

### 15. `post_ar_payment(payment: ARPayment)`

**Purpose:** Posts AR payment to GL with FX support

**Parameters:**
- `payment`: ARPayment instance

**Returns:** Tuple `(entry, already_posted, invoice_closed)`

**Journal Entry (basic):**
```
DR Bank                  1000.00
    CR Accounts Receivable 1000.00
```

**FX Handling:**
If `payment.payment_fx_rate` provided and != 1.0:
```
DR Bank                  1020.00  (received more)
    CR Accounts Receivable 1000.00
    CR FX Gain               20.00  (exchange gain)
```

**Logic:**
1. Gets bank account from payment.bank_account or default
2. Calculates FX difference if rate provided
3. Creates journal entry:
   - Debit bank (cash received)
   - Credit AR (reduce receivable)
   - Credit/Debit FX Gain/Loss if difference
4. Checks if invoice fully paid → marks as PAID

**Usage:**
```python
payment = ARPayment.objects.create(
    invoice=invoice,
    amount=Decimal("1000.00"),
    date=date.today()
)
entry, already_posted, closed = post_ar_payment(payment)
if closed:
    print("Invoice fully paid!")
```

---

### 16. `post_ap_payment(payment: APPayment)`

**Purpose:** Posts AP payment to GL with FX support

**Parameters:**
- `payment`: APPayment instance

**Returns:** Tuple `(entry, already_posted, invoice_closed)`

**Journal Entry (basic):**
```
DR Accounts Payable      1000.00
    CR Bank              1000.00
```

**FX Handling:**
If paying in different currency:
```
DR Accounts Payable      1000.00
DR FX Loss                 20.00  (paid more)
    CR Bank              1020.00
```

**Difference from AR:**
- AP is debited (reduce liability)
- Bank is credited (reduce cash)
- FX Loss if paid more, FX Gain if paid less

---

### 17. `_bank_account_to_gl_account(payment_bank: BankAccount | None) -> Account`

**Purpose:** Maps BankAccount to GL Account

**Parameters:**
- `payment_bank`: BankAccount instance or None

**Returns:** Account instance

**Logic:**
1. If bank has `account_code`, use it
2. Else use default "BANK" code
3. Raises ValueError if account not found

---

## Reversal Functions

### 18. `reverse_journal(entry: JournalEntry) -> JournalEntry`

**Purpose:** Creates reversing journal entry

**Parameters:**
- `entry`: JournalEntry to reverse

**Returns:** New reversed JournalEntry

**Logic:**
1. Creates new entry with current date
2. Memo: "Reversal of Journal #{original_id}"
3. For each line:
   - Swap debit ↔ credit
   - Same account
4. Marks as posted

**Example:**
Original:
```
DR Cash      100
    CR Revenue 100
```

Reversed:
```
DR Revenue   100
    CR Cash    100
```

**Usage:**
```python
original = JournalEntry.objects.get(id=1)
reversed = reverse_journal(original)
```

---

### 19. `reverse_posted_invoice(original_id: int) -> Invoice`

**Purpose:** Creates reversing invoice (idempotent)

**Parameters:**
- `original_id`: ID of invoice to reverse

**Returns:** Reversing Invoice instance

**Idempotency:** Returns existing reversal if already reversed

**Validation:**
- Only POSTED invoices can be reversed

**Logic:**
1. Checks if already reversed → returns existing
2. Creates new invoice with:
   - invoice_no: "{original_no}-REV"
   - Same customer, currency
   - Status: POSTED
   - reversal_ref: original invoice
3. Mirrors all lines with negative quantities
4. Recomputes totals
5. Marks original as REVERSED

**Example:**
```python
original = Invoice.objects.get(id=1)
# Original has: qty=10, price=100 → total=1000

reversal = reverse_posted_invoice(1)
# Reversal has: qty=-10, price=100 → total=-1000
```

---

### 20. `validate_ready_to_post(inv: Invoice)`

**Purpose:** Validates invoice is ready for posting

**Parameters:**
- `inv`: Invoice instance

**Raises ValidationError if:**
- Invoice has no lines
- Any line missing account or tax_code
- Totals are zero
- Total is negative

**Usage:**
```python
try:
    validate_ready_to_post(invoice)
    # Safe to post
except ValidationError as e:
    print(f"Cannot post: {e}")
```

---

### 21. `post_invoice(invoice_id: int) -> Invoice`

**Purpose:** Posts an invoice (marks as POSTED)

**Parameters:**
- `invoice_id`: Invoice ID

**Returns:** Posted Invoice

**Idempotency:** Returns invoice if already posted

**Validation:**
- Only DRAFT invoices can be posted

**Logic:**
1. Locks invoice row
2. Checks status
3. Validates with `validate_ready_to_post()`
4. Sets status = POSTED
5. Sets posted_at timestamp
6. Saves

**Usage:**
```python
invoice = post_invoice(1)
print(f"Posted at {invoice.posted_at}")
```

---

## Corporate Tax Functions

### 22. `accrue_corporate_tax(country: str, date_from: date, date_to: date, org_id: int | None = None)`

**Purpose:** Calculates and accrues corporate tax for a period

**Parameters:**
- `country`: Country code (e.g., "AE")
- `date_from`: Period start
- `date_to`: Period end
- `org_id`: Organization ID (optional, multi-tenant)

**Returns:** Tuple `(journal_entry, meta_dict)`

**Meta Dict:**
```python
{
    "profit": 100000.00,
    "tax_base": 100000.00,
    "tax": 9000.00
}
```

**Logic:**
1. Finds active CorporateTaxRule for country
2. Sums posted journal lines in period:
   - Income accounts (credit - debit)
   - Expense accounts (debit - credit)
3. Calculates profit = income - expense
4. Applies threshold if configured
5. Calculates tax = tax_base × rate
6. Creates journal entry:
   ```
   DR Corporate Tax Expense    9000
       CR Corporate Tax Payable 9000
   ```

**Example:**
```python
# UAE corporate tax: 9% on profit > 375,000
rule = CorporateTaxRule.objects.create(
    country="AE",
    rate=Decimal("9.0"),
    threshold=Decimal("375000.00"),
    active=True
)

je, meta = accrue_corporate_tax(
    "AE",
    date(2025, 1, 1),
    date(2025, 12, 31)
)
print(f"Tax accrued: {meta['tax']}")
```

---

### 23. `accrue_corporate_tax_with_filing(...)`

**Purpose:** Accrues tax and creates/updates CorporateTaxFiling record

**Parameters:** Same as `accrue_corporate_tax()` plus:
- `allow_override`: Boolean (default: False)

**Returns:** Tuple `(filing, journal_entry, meta)`

**Idempotency:**
- If filing exists with status=ACCRUED, returns existing
- If filing exists with status=FILED and allow_override=False, raises error

**Usage:**
```python
filing, je, meta = accrue_corporate_tax_with_filing(
    "AE",
    date(2025, 1, 1),
    date(2025, 12, 31)
)
print(f"Filing status: {filing.status}")
```

---

### 24. `reverse_corporate_tax_filing(filing_id: int)`

**Purpose:** Reverses corporate tax accrual

**Parameters:**
- `filing_id`: CorporateTaxFiling ID

**Returns:** Reversing JournalEntry

**Validation:**
- Cannot reverse FILED filings (unless unlocked)
- Must have accrual_journal

**Logic:**
1. Locks filing row
2. Calls `reverse_journal()` on accrual
3. Saves reversal reference
4. Sets status = REVERSED

---

### 25. `file_corporate_tax(filing_id: int)`

**Purpose:** Marks tax filing as officially FILED

**Parameters:**
- `filing_id`: CorporateTaxFiling ID

**Returns:** Updated CorporateTaxFiling

**Validation:**
- Only ACCRUED filings can be filed

**Logic:**
1. Locks filing row
2. Sets status = FILED
3. Sets filed_at timestamp
4. Saves

**Example Workflow:**
```python
# 1. Accrue
filing, je, meta = accrue_corporate_tax_with_filing("AE", ...)

# 2. Review
print(f"Tax amount: {meta['tax']}")

# 3. File officially
file_corporate_tax(filing.id)

# 4. Cannot reverse now (locked)
```

---

## Helper Functions

### 26. `_has_field(model, name: str) -> bool`

**Purpose:** Checks if model has a field

**Usage:** Multi-tenant compatibility check

---

### 27. `_with_org_filter(lines_qs, org_id)`

**Purpose:** Filters queryset by organization if field exists

**Usage:** Multi-tenant filtering

---

### 28. `_create_journal_entry(**kwargs)`

**Purpose:** Creates journal entry filtering unknown kwargs

**Why:** Handles optional fields like 'organization' gracefully

---

### 29. `_acct_code_or_raise(key: str) -> Account`

**Purpose:** Gets account by key, raises helpful error

**Difference from `_acct()`:** Different error message

---

### 30. `_aging_bucket(days_overdue, b1=30, b2=30, b3=30)`

**Purpose:** Determines aging bucket for days overdue

**Returns:** String like "Current", "1–30", ">90"

---

### 31. `_ar_balance(inv: ARInvoice)`

**Purpose:** Quick balance calculation for AR invoice

**Returns:** Decimal balance (rounded)

---

### 32. `_ap_balance(inv: APInvoice)`

**Purpose:** Quick balance calculation for AP invoice

**Returns:** Decimal balance (rounded)

---

### 33. `_get_or_block_existing_filing(...)`

**Purpose:** Checks for existing tax filing, validates override

**Returns:** Tuple `(filing, can_create)`

---

## Common Patterns

### Idempotent Posting
```python
# Safe to call multiple times
journal, created = gl_post_from_ar_balanced(invoice)
if created:
    print("Posted now")
else:
    print("Already posted")
```

### Transaction Safety
All posting functions use `@transaction.atomic` decorator:
```python
@transaction.atomic
def post_ar_payment(payment):
    # All or nothing
    # Rollback on any error
```

### Error Handling
```python
try:
    post_invoice(invoice_id)
except ValidationError as e:
    print(f"Validation failed: {e}")
except ValueError as e:
    print(f"Business rule error: {e}")
```

---

## Best Practices

### 1. Always Use Helpers
✅ **DO:** Use `_acct("AR")` to get accounts  
❌ **DON'T:** Hard-code `Account.objects.get(code="1100")`

### 2. Check Idempotency
✅ **DO:** Check `created` flag in posting functions  
❌ **DON'T:** Assume function creates new records

### 3. Validate Before Posting
✅ **DO:** Call `validate_ready_to_post()` first  
❌ **DON'T:** Post without validation

### 4. Use Transactions
✅ **DO:** Wrap related operations in `@transaction.atomic`  
❌ **DON'T:** Risk partial updates

### 5. Handle FX Properly
✅ **DO:** Provide `payment_fx_rate` when needed  
❌ **DON'T:** Ignore exchange rate differences

---

## Conclusion

The Finance services provide:

✅ **Reporting:** Trial balance, aging reports  
✅ **Calculations:** Tax, totals, balances  
✅ **GL Posting:** AR/AP invoices, payments  
✅ **FX Support:** Exchange rate handling  
✅ **Tax Accrual:** Corporate tax calculation  
✅ **Reversals:** Invoice and journal reversals  
✅ **Validation:** Pre-post checks  
✅ **Idempotency:** Safe repeat operations  
✅ **Transaction Safety:** All-or-nothing operations  
✅ **Multi-tenant:** Organization filtering support  

These services form the core business logic layer, ensuring accurate accounting, proper GL posting, and compliance with tax regulations.

---

**Last Updated:** October 13, 2025  
**Framework:** Django 4.x+  
**Python Version:** 3.10+

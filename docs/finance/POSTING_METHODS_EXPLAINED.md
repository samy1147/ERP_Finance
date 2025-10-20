# Complete Guide to Posting Methods in Finance Module

## Overview
This document provides an in-depth explanation of all posting methods in the Finance module. Posting is the process of recording financial transactions into the General Ledger (GL), making them permanent and immutable parts of the accounting record.

---

## Table of Contents
1. [What is Posting?](#what-is-posting)
2. [Invoice Posting](#invoice-posting)
3. [Payment Posting](#payment-posting)
4. [Journal Entry Posting](#journal-entry-posting)
5. [Tax Accrual Posting](#tax-accrual-posting)
6. [Posting Flow Diagrams](#posting-flow-diagrams)
7. [Code Deep Dive](#code-deep-dive)
8. [Troubleshooting](#troubleshooting)

---

## What is Posting?

### Definition
**Posting** is the act of transferring transaction data from source documents (invoices, payments) into the General Ledger as journal entries.

### Key Concepts

#### Before Posting (DRAFT)
- Transaction exists but not recorded in GL
- Can be edited or deleted
- No accounting impact
- Not included in financial reports

#### After Posting (POSTED)
- Transaction recorded in GL as journal entry
- **Immutable** (cannot be edited)
- Impacts account balances
- Included in all financial reports
- Only reversible through reversal entries

### Why Post?
1. **Finalize Transactions:** Make them official accounting records
2. **Update GL:** Reflect in account balances
3. **Financial Reporting:** Include in reports (Trial Balance, P&L, Balance Sheet)
4. **Audit Trail:** Create permanent record
5. **Compliance:** Meet accounting standards requirements

---

## Invoice Posting

### AR Invoice Posting

#### Function: `gl_post_from_ar_balanced()`
**Location:** `finance/services.py`

#### Purpose
Converts an Accounts Receivable (customer) invoice into a General Ledger journal entry.

#### Accounting Principle
When you invoice a customer:
- **Asset increases:** Accounts Receivable (customer owes you)
- **Revenue increases:** Sales/Revenue account
- **Liability increases:** VAT Output (tax you owe government)

#### Journal Entry Created
```
Date: Invoice Date
Memo: "AR Post INV-001"

DR Accounts Receivable    1,050.00  (Asset ↑)
    CR Revenue            1,000.00  (Income ↑)
    CR VAT Output            50.00  (Liability ↑)
```

#### Step-by-Step Process

**Step 1: Lock the Invoice**
```python
inv = ARInvoice.objects.select_for_update().get(pk=invoice.pk)
```
- Uses database row lock to prevent concurrent modifications
- Ensures only one process can post the invoice at a time

**Step 2: Check Idempotency**
```python
if inv.gl_journal_id:
    return inv.gl_journal, False  # Already posted
```
- If invoice already has a journal entry, return it
- Safe to call multiple times (idempotent)

**Step 3: Validate Invoice**
```python
item_count = inv.items.count()
if item_count == 0:
    raise ValueError("Cannot post invoice: Invoice has no line items")
```
- Checks invoice has at least one line item
- Validates totals are not zero

**Step 4: Calculate Totals**
```python
totals = ar_totals(inv)
subtotal = totals["subtotal"]  # Net amount before tax
tax = totals["tax"]            # Tax amount
dr_total = q2(subtotal + tax)  # Total to debit AR
```
- Calls `ar_totals()` to sum all line items
- Includes tax calculations
- Rounds to 2 decimal places

**Step 5: Create Journal Entry**
```python
je = _create_journal_entry(
    organization=getattr(inv, "organization", None),
    date=inv.date,
    currency=inv.currency,
    memo=f"AR Post {inv.number}",
)
```
- Creates journal entry header
- Uses invoice date (transaction date)
- Sets memo for audit trail

**Step 6: Create Journal Lines**
```python
# Debit AR (Asset increases)
JournalLine.objects.create(
    entry=je, 
    account=_acct("AR"), 
    debit=dr_total
)

# Credit Revenue (Income increases)
if subtotal:
    JournalLine.objects.create(
        entry=je, 
        account=_acct("REV"), 
        credit=subtotal
    )

# Credit VAT Output (Liability increases)
tax_bal = q2(dr_total - subtotal)
if tax_bal:
    JournalLine.objects.create(
        entry=je, 
        account=_acct("VAT_OUT"), 
        credit=tax_bal
    )
```
- Creates 2-3 lines depending on whether tax exists
- Debits always equal credits (balanced entry)

**Step 7: Post the Journal Entry**
```python
post_entry(je)
```
- Validates debits = credits
- Sets `posted=True`
- Makes journal entry permanent

**Step 8: Mark Invoice as Posted**
```python
inv.gl_journal = je
inv.status = "POSTED"
inv.posted_at = timezone.now()
inv.save(update_fields=["gl_journal", "posted_at", "status"])
```
- Links journal to invoice
- Changes status to POSTED
- Records timestamp

**Step 9: Return Result**
```python
return je, True  # (journal_entry, created)
```
- Returns tuple: journal entry and whether it was newly created

#### Complete Code Example
```python
@transaction.atomic
def gl_post_from_ar_balanced(invoice: ARInvoice):
    """
    Posts AR invoice to GL. Idempotent.
    Returns: (journal_entry, created: bool)
    """
    # 1. Lock invoice
    inv = ARInvoice.objects.select_for_update().get(pk=invoice.pk)
    
    # 2. Check if already posted
    if inv.gl_journal_id:
        return inv.gl_journal, False
    
    # 3. Validate
    if inv.items.count() == 0:
        raise ValueError(f"Cannot post invoice {inv.number}: no line items")
    
    # 4. Calculate totals
    totals = ar_totals(inv)
    subtotal = totals["subtotal"]
    tax = totals["tax"]
    dr_total = q2(subtotal + tax)
    
    if dr_total == Decimal("0.00"):
        raise ValueError(f"Cannot post invoice {inv.number}: total is zero")
    
    # 5. Create journal entry
    je = _create_journal_entry(
        date=inv.date,
        currency=inv.currency,
        memo=f"AR Post {inv.number}",
    )
    
    # 6. Create lines
    JournalLine.objects.create(entry=je, account=_acct("AR"), debit=dr_total)
    if subtotal:
        JournalLine.objects.create(entry=je, account=_acct("REV"), credit=subtotal)
    tax_bal = q2(dr_total - subtotal)
    if tax_bal:
        JournalLine.objects.create(entry=je, account=_acct("VAT_OUT"), credit=tax_bal)
    
    # 7. Post entry
    post_entry(je)
    
    # 8. Mark invoice posted
    inv.gl_journal = je
    inv.status = "POSTED"
    inv.posted_at = timezone.now()
    inv.save(update_fields=["gl_journal", "posted_at", "status"])
    
    # 9. Return
    return je, True
```

#### Real-World Example

**Scenario:** Invoice customer $1,000 + 5% VAT

```python
# Create invoice
invoice = ARInvoice.objects.create(
    customer=customer,
    date=date(2025, 1, 15),
    number="INV-001"
)

# Add line item
ARItem.objects.create(
    invoice=invoice,
    description="Consulting Services",
    quantity=10,
    unit_price=100.00,
    tax_rate=vat_5_percent
)

# Post to GL
journal, created = gl_post_from_ar_balanced(invoice)

# Result in GL:
# DR 1100 Accounts Receivable  1,050.00
#     CR 4000 Revenue           1,000.00
#     CR 2100 VAT Output           50.00
```

---

### AP Invoice Posting

#### Function: `gl_post_from_ap_balanced()`
**Location:** `finance/services.py`

#### Purpose
Converts an Accounts Payable (supplier) invoice into a General Ledger journal entry.

#### Accounting Principle
When you receive a supplier invoice:
- **Expense increases:** Cost of Goods/Services
- **Asset increases:** VAT Input (tax recoverable from government)
- **Liability increases:** Accounts Payable (you owe supplier)

#### Journal Entry Created
```
Date: Invoice Date
Memo: "AP Post BILL-001"

DR Expense               1,000.00  (Expense ↑)
DR VAT Input                50.00  (Asset ↑)
    CR Accounts Payable  1,050.00  (Liability ↑)
```

#### Key Differences from AR Posting

| Aspect | AR (Customer) | AP (Supplier) |
|--------|---------------|---------------|
| Account Debited | AR (Asset) | Expense |
| Account Credited | Revenue | AP (Liability) |
| Tax Account | VAT Output (CR) | VAT Input (DR) |
| Tax Treatment | Tax collected | Tax recoverable |

#### Step-by-Step Process

**Steps 1-5:** Same as AR posting (lock, check, validate, calculate, create JE)

**Step 6: Create Journal Lines** (Different from AR!)
```python
# Debit Expense (Expense increases)
if subtotal:
    JournalLine.objects.create(
        entry=je, 
        account=_acct("EXP"), 
        debit=subtotal
    )

# Debit VAT Input (Asset increases - recoverable tax)
vat_in = q2(cr_total - subtotal)
if vat_in:
    JournalLine.objects.create(
        entry=je, 
        account=_acct("VAT_IN"), 
        debit=vat_in
    )

# Credit AP (Liability increases)
JournalLine.objects.create(
    entry=je, 
    account=_acct("AP"), 
    credit=cr_total
)
```

**Steps 7-9:** Same as AR posting (post, mark, return)

#### Real-World Example

**Scenario:** Receive supplier bill $500 + 5% VAT

```python
# Create invoice
invoice = APInvoice.objects.create(
    supplier=supplier,
    date=date(2025, 1, 15),
    number="BILL-001"
)

# Add line item
APItem.objects.create(
    invoice=invoice,
    description="Office Supplies",
    quantity=50,
    unit_price=10.00,
    tax_rate=vat_5_percent
)

# Post to GL
journal, created = gl_post_from_ap_balanced(invoice)

# Result in GL:
# DR 5000 Expense              500.00
# DR 2110 VAT Input             25.00
#     CR 2000 Accounts Payable 525.00
```

---

## Payment Posting

### AR Payment Posting

#### Function: `post_ar_payment()`
**Location:** `finance/services.py`

#### Purpose
Records customer payment against an invoice, reducing Accounts Receivable and increasing Cash.

#### Accounting Principle
When customer pays:
- **Asset increases:** Bank/Cash (money received)
- **Asset decreases:** Accounts Receivable (customer no longer owes)

#### Basic Journal Entry
```
Date: Payment Date
Memo: "AR Payment #123"

DR Bank                  1,050.00  (Asset ↑)
    CR Accounts Receivable 1,050.00  (Asset ↓)
```

#### With Foreign Exchange
```
Date: Payment Date
Memo: "AR Payment #123"

DR Bank                  1,070.00  (Asset ↑ - received more)
    CR Accounts Receivable 1,050.00  (Asset ↓ - original amount)
    CR FX Gain                20.00  (Income ↑ - exchange gain)
```

#### Step-by-Step Process

**Step 1: Get Accounts**
```python
invoice = payment.invoice
ar_account = Account.objects.get(code=ACCOUNT_CODES['AR'])

# Get bank account (from payment or default)
if payment.bank_account and payment.bank_account.account_code:
    bank_account = Account.objects.get(code=payment.bank_account.account_code)
else:
    bank_account = Account.objects.get(code=ACCOUNT_CODES['BANK'])
```

**Step 2: Setup FX Accounts (Optional)**
```python
try:
    fx_gain_account = Account.objects.get(code=ACCOUNT_CODES.get('FX_GAIN', '9999'))
    fx_loss_account = Account.objects.get(code=ACCOUNT_CODES.get('FX_LOSS', '9998'))
    fx_accounts_available = True
except Account.DoesNotExist:
    fx_accounts_available = False
```

**Step 3: Create Journal Entry**
```python
entry = JournalEntry.objects.create(
    date=payment.date,
    currency=invoice.currency,
    memo=f"AR Payment #{payment.id}",
    posted=True  # Posted immediately
)
```

**Step 4: Calculate FX Difference**
```python
ar_amount = payment.amount  # Amount to reduce AR
bank_amount = payment.amount  # Amount received in bank
fx_difference = Decimal("0")

if payment.payment_fx_rate and payment.payment_fx_rate != Decimal("1.0"):
    # Calculate difference due to exchange rate
    fx_difference = q2((payment.amount * payment.payment_fx_rate) - payment.amount)
    bank_amount = q2(payment.amount + fx_difference)
```

**Example:**
- Invoice: 1000 AED @ rate 3.67 = $272.48 (AR amount)
- Payment: 1000 AED @ rate 3.60 = $277.78 (bank amount)
- FX Gain: $277.78 - $272.48 = $5.30

**Step 5: Post Bank Line**
```python
# Debit bank (cash received)
JournalLine.objects.create(
    entry=entry,
    account=bank_account,
    debit=bank_amount,  # Actual amount received
    credit=Decimal("0")
)
```

**Step 6: Post AR Line**
```python
# Credit AR (reduce receivable)
JournalLine.objects.create(
    entry=entry,
    account=ar_account,
    debit=Decimal("0"),
    credit=ar_amount  # Original invoice amount
)
```

**Step 7: Post FX Gain/Loss (If Any)**
```python
if fx_difference != 0 and fx_accounts_available:
    if fx_difference > 0:
        # FX Gain: received more than booked
        JournalLine.objects.create(
            entry=entry,
            account=fx_gain_account,
            debit=Decimal("0"),
            credit=abs(fx_difference)
        )
    else:
        # FX Loss: received less than booked
        JournalLine.objects.create(
            entry=entry,
            account=fx_loss_account,
            debit=abs(fx_difference),
            credit=Decimal("0")
        )
```

**Step 8: Mark Payment Posted**
```python
payment.gl_journal = entry
payment.posted_at = timezone.now()
payment.save()
```

**Step 9: Check if Invoice Fully Paid**
```python
totals = ar_totals(invoice)
invoice_closed = (totals['balance'] == 0)

if invoice_closed:
    invoice.status = "PAID"
    invoice.paid_at = timezone.now()
    invoice.save(update_fields=['status', 'paid_at'])
```

**Step 10: Return Result**
```python
return entry, False, invoice_closed
# (journal_entry, already_posted, invoice_closed)
```

#### Complete Example with FX

```python
# Invoice: 1000 EUR @ 1.10 rate = $1100 AR
invoice = ARInvoice.objects.create(
    customer=customer,
    total=Decimal("1000.00"),
    currency=eur,
    fx_rate=Decimal("1.10")
)

# Payment received later at different rate
payment = ARPayment.objects.create(
    invoice=invoice,
    amount=Decimal("1000.00"),  # 1000 EUR
    date=date(2025, 2, 15),
    payment_fx_rate=Decimal("1.08")  # EUR weaker now
)

# Post payment
entry, _, closed = post_ar_payment(payment)

# Result in GL:
# DR Bank              1,080.00  (1000 EUR × 1.08)
# DR FX Loss              20.00  (received $20 less)
#     CR AR            1,100.00  (original booking)
```

---

### AP Payment Posting

#### Function: `post_ap_payment()`
**Location:** `finance/services.py`

#### Purpose
Records payment to supplier, reducing Accounts Payable and decreasing Cash.

#### Accounting Principle
When you pay supplier:
- **Asset decreases:** Bank/Cash (money paid out)
- **Liability decreases:** Accounts Payable (no longer owe supplier)

#### Basic Journal Entry
```
Date: Payment Date
Memo: "AP Payment #456"

DR Accounts Payable       525.00  (Liability ↓)
    CR Bank               525.00  (Asset ↓)
```

#### With Foreign Exchange
```
Date: Payment Date
Memo: "AP Payment #456"

DR Accounts Payable       525.00  (Liability ↓ - original amount)
DR FX Loss                 15.00  (Expense ↑ - paid more)
    CR Bank               540.00  (Asset ↓ - actual payment)
```

#### Key Differences from AR Payment

| Aspect | AR (Customer) | AP (Supplier) |
|--------|---------------|---------------|
| Bank Entry | Debit (receive) | Credit (pay) |
| AR/AP Entry | Credit (reduce) | Debit (reduce) |
| FX Gain | If receive more | If pay less |
| FX Loss | If receive less | If pay more |

#### FX Logic for AP

**Scenario 1: FX Gain (Pay Less)**
```
Invoice: 1000 EUR @ 1.10 = $1100 AP booked
Payment: 1000 EUR @ 1.15 = $870 paid
Result: $230 FX GAIN (paid less in home currency)

DR AP               1,100.00
    CR Bank           870.00
    CR FX Gain        230.00
```

**Scenario 2: FX Loss (Pay More)**
```
Invoice: 1000 EUR @ 1.10 = $1100 AP booked
Payment: 1000 EUR @ 1.05 = $1050 paid
Result: $50 FX LOSS (paid more in home currency)

DR AP               1,100.00
DR FX Loss             50.00
    CR Bank         1,150.00
```

---

## Journal Entry Posting

### Function: `post_entry()`
**Location:** `finance/services.py`

#### Purpose
Validates and posts a manual journal entry.

#### Process

**Step 1: Calculate Totals**
```python
td = sum((l.debit for l in entry.lines.all()), start=Decimal("0"))
tc = sum((l.credit for l in entry.lines.all()), start=Decimal("0"))
```

**Step 2: Validate Balance**
```python
if q2(td) != q2(tc):
    raise ValueError("Unbalanced journal")
```
- Ensures debits equal credits
- Fundamental accounting rule

**Step 3: Mark Posted**
```python
entry.posted = True
entry.save(update_fields=["posted"])
```

**Step 4: Return**
```python
return entry
```

#### Example

```python
# Create manual journal entry
entry = JournalEntry.objects.create(
    date=date.today(),
    memo="Prepaid expense adjustment"
)

# Add lines
JournalLine.objects.create(
    entry=entry,
    account=prepaid_expense_account,
    debit=Decimal("1200.00")
)

JournalLine.objects.create(
    entry=entry,
    account=expense_account,
    credit=Decimal("1200.00")
)

# Post
post_entry(entry)  # Validates debits=credits, then posts
```

---

## Tax Accrual Posting

### Function: `accrue_corporate_tax()`
**Location:** `finance/services.py`

#### Purpose
Calculates and posts corporate tax expense and payable for a period.

#### Accounting Principle
At period end:
- **Expense increases:** Tax Expense (P&L impact)
- **Liability increases:** Tax Payable (you owe government)

#### Journal Entry
```
Date: Period End Date
Memo: "Corporate tax accrual AE 2025-01-01..2025-12-31"

DR Corporate Tax Expense   11,250.00  (Expense ↑)
    CR Corporate Tax Payable 11,250.00  (Liability ↑)
```

#### Step-by-Step Process

**Step 1: Get Tax Rule**
```python
rule = CorporateTaxRule.objects.filter(
    country=country, 
    active=True
).order_by("-id").first()

if not rule:
    raise ValueError(f"No active tax rule for {country}")
```

**Step 2: Sum Posted Journals**
```python
lines = JournalLine.objects.select_related("entry","account") \
      .filter(
          entry__posted=True, 
          entry__date__gte=date_from, 
          entry__date__lte=date_to
      )

income = Decimal("0")
expense = Decimal("0")

for ln in lines:
    acc_type = ln.account.type.upper()
    if acc_type in ("INCOME", "IN"):
        income += (Decimal(ln.credit) - Decimal(ln.debit))
    elif acc_type in ("EXPENSE", "EX"):
        expense += (Decimal(ln.debit) - Decimal(ln.credit))
```

**Step 3: Calculate Profit**
```python
profit = q2(income - expense)

if profit <= 0:
    return None, {"profit": float(profit), "tax_base": 0.0, "tax": 0.0}
```

**Step 4: Apply Threshold**
```python
tax_base = profit

if rule.threshold is not None and profit > rule.threshold:
    tax_base = q2(profit - rule.threshold)
elif rule.threshold:
    # Below threshold, no tax
    return None, {"profit": float(profit), "tax_base": 0.0, "tax": 0.0}
```

**Example:** UAE Corporate Tax
- Profit: $500,000
- Threshold: $375,000 (first 375K exempt)
- Tax Base: $125,000
- Rate: 9%
- Tax: $11,250

**Step 5: Calculate Tax**
```python
tax = q2(tax_base * (rule.rate / Decimal("100")))

if tax == 0:
    return None, {"profit": float(profit), "tax_base": float(tax_base), "tax": 0.0}
```

**Step 6: Create Journal Entry**
```python
je = _create_journal_entry(
    date=date_to,
    currency=currency,
    memo=f"Corporate tax accrual {country} {date_from}..{date_to} on profit {profit}",
)

# Debit Tax Expense
JournalLine.objects.create(
    entry=je, 
    account=_acct("TAX_CORP_EXP"), 
    debit=tax, 
    credit=Decimal("0")
)

# Credit Tax Payable
JournalLine.objects.create(
    entry=je, 
    account=_acct("TAX_CORP_PAYABLE"), 
    debit=Decimal("0"), 
    credit=tax
)
```

**Step 7: Post Entry**
```python
post_entry(je)
```

**Step 8: Return Result**
```python
return je, {
    "profit": float(profit), 
    "tax_base": float(tax_base), 
    "tax": float(tax)
}
```

#### Complete Example

```python
# Setup tax rule
CorporateTaxRule.objects.create(
    country="AE",
    rate=Decimal("9.0"),
    threshold=Decimal("375000.00"),
    active=True
)

# Accrue tax for year
je, meta = accrue_corporate_tax(
    country="AE",
    date_from=date(2025, 1, 1),
    date_to=date(2025, 12, 31)
)

print(f"Profit: ${meta['profit']}")
print(f"Tax Base: ${meta['tax_base']}")
print(f"Tax: ${meta['tax']}")

# Output:
# Profit: $500,000
# Tax Base: $125,000
# Tax: $11,250

# GL now has:
# DR 6900 Corporate Tax Expense   11,250.00
#     CR 2400 Corporate Tax Payable 11,250.00
```

---

## Posting Flow Diagrams

### AR Invoice Posting Flow

```
┌─────────────────────────────────────┐
│   User clicks "Post" button        │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   API: ARInvoiceViewSet.post()     │
│   - Receives invoice ID            │
│   - Calls service function         │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Service: gl_post_from_ar_balanced│
│   Step 1: Lock invoice row         │
│   Step 2: Check if already posted  │
│   Step 3: Validate invoice         │
│   Step 4: Calculate totals         │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Create Journal Entry             │
│   - Set date, currency, memo       │
│   - Create JE header in DB         │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Create Journal Lines             │
│   - DR Accounts Receivable         │
│   - CR Revenue                     │
│   - CR VAT Output                  │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Validate & Post Entry            │
│   - Check debits = credits         │
│   - Set posted = True              │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Update Invoice                   │
│   - Link to journal entry          │
│   - Set status = POSTED            │
│   - Set posted_at timestamp        │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Trigger Signals                  │
│   - block_edit_posted_invoice      │
│   - Makes invoice read-only        │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Return Success Response          │
│   - journal_id                     │
│   - created: true/false            │
└─────────────────────────────────────┘
```

### Payment with FX Flow

```
┌─────────────────────────────────────┐
│   Payment received in EUR          │
│   Invoice was in EUR at 1.10       │
│   Payment at rate 1.08             │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Calculate Amounts                │
│   AR amount: 1000 EUR / 1.10       │
│   = $1100 (original booking)       │
│                                    │
│   Bank amount: 1000 EUR / 1.08     │
│   = $1080 (actual received)        │
│                                    │
│   FX difference: $1080 - $1100     │
│   = -$20 (LOSS)                    │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Create Journal Entry             │
│   Date: Payment date               │
│   Memo: "AR Payment #123"          │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Post Bank Line                   │
│   DR Bank    1,080.00              │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Post FX Loss Line                │
│   DR FX Loss    20.00              │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Post AR Line                     │
│   CR AR      1,100.00              │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Check Invoice Balance            │
│   If balance = 0, mark PAID        │
└─────────────────────────────────────┘
```

### Corporate Tax Accrual Flow

```
┌─────────────────────────────────────┐
│   Month/Year End Process           │
│   Trigger tax accrual              │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Get Tax Rule for Country         │
│   - Rate: 9%                       │
│   - Threshold: $375,000            │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Query Posted Journals            │
│   - Date range: period             │
│   - Posted only                    │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Aggregate by Account Type        │
│   - Sum INCOME accounts            │
│   - Sum EXPENSE accounts           │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Calculate Profit                 │
│   Profit = Income - Expense        │
│   Example: $1M - $500K = $500K     │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Apply Threshold                  │
│   Tax Base = $500K - $375K         │
│   = $125,000                       │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Calculate Tax                    │
│   Tax = $125K × 9%                 │
│   = $11,250                        │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Create Journal Entry             │
│   DR Tax Expense    11,250         │
│   CR Tax Payable    11,250         │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Post Entry                       │
│   Mark as posted                   │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Create Filing Record             │
│   - Period                         │
│   - Status: ACCRUED                │
│   - Link to journal                │
└─────────────────────────────────────┘
```

---

## Code Deep Dive

### Transaction Safety

All posting methods use `@transaction.atomic`:

```python
@transaction.atomic
def gl_post_from_ar_balanced(invoice: ARInvoice):
    # If any error occurs, ALL changes rolled back
    # Ensures database consistency
```

**Benefits:**
- **All or Nothing:** Complete success or complete failure
- **No Partial Posts:** Can't have invoice marked posted without journal
- **Race Condition Protection:** Database locks prevent conflicts

### Idempotency Pattern

Most posting functions are idempotent (safe to call multiple times):

```python
# Check if already posted
if inv.gl_journal_id:
    return inv.gl_journal, False  # Return existing, don't create new

# Otherwise create new
je = create_journal_entry(...)
return je, True  # Return new, flag as created
```

**Why Important:**
- Network failures might retry requests
- Users might click "Post" button twice
- Background jobs might retry
- Prevents duplicate journal entries

### Account Code Mapping

Uses centralized account configuration:

```python
DEFAULT_ACCOUNTS = {
    "BANK": "1000",
    "AR": "1100",
    "AP": "2000",
    "VAT_OUT": "2100",
    "VAT_IN": "2110",
    "REV": "4000",
    "EXP": "5000",
    # ...
}

# Override in settings.py
FINANCE_ACCOUNTS = {
    "AR": "1200",  # Use different code
    # ...
}
```

**Benefits:**
- Flexible chart of accounts
- Easy to customize per company
- Centralized configuration
- Clear error messages if account missing

### Decimal Precision

Uses Python `Decimal` type for accuracy:

```python
from decimal import Decimal, ROUND_HALF_UP

def q2(x: Decimal) -> Decimal:
    """Round to 2 decimal places"""
    return Decimal(x).quantize(
        Decimal("0.01"), 
        rounding=ROUND_HALF_UP
    )
```

**Why Not Float:**
```python
# Float precision issues
0.1 + 0.2  # = 0.30000000000000004 ❌

# Decimal precision
Decimal("0.1") + Decimal("0.2")  # = 0.3 ✅
```

### Database Locking

Prevents concurrent posting:

```python
# Lock the row
inv = ARInvoice.objects.select_for_update().get(pk=invoice.pk)

# Only this transaction can modify invoice
# Other transactions wait
```

**Without Locking:**
```
Time    Transaction A          Transaction B
----    ---------------        ---------------
0       Read invoice (posted=False)
1                              Read invoice (posted=False)
2       Create journal A
3                              Create journal B
4       Mark posted
5                              Mark posted (overwrites A!)

Result: TWO journal entries! ❌
```

**With Locking:**
```
Time    Transaction A          Transaction B
----    ---------------        ---------------
0       Lock + Read invoice
1                              Wait for lock...
2       Create journal A
3                              Still waiting...
4       Mark posted
5       Release lock
6                              Get lock
7                              Read (posted=True)
8                              Return existing ✅

Result: ONE journal entry ✅
```

---

## Troubleshooting

### Issue: "Cannot post invoice: it has no lines"

**Cause:** Invoice has zero line items

**Solution:**
```python
# Add at least one line item before posting
ARItem.objects.create(
    invoice=invoice,
    description="Item description",
    quantity=1,
    unit_price=100.00
)

# Then post
gl_post_from_ar_balanced(invoice)
```

---

### Issue: "Cannot post invoice: totals are zero"

**Cause:** All line items have zero amounts

**Solution:**
```python
# Ensure items have non-zero amounts
item.quantity = 10  # Not 0
item.unit_price = 100.00  # Not 0
item.save()
```

---

### Issue: "Unbalanced journal"

**Cause:** Debits don't equal credits

**Solution:**
```python
# Check line totals
debits = sum(line.debit for line in entry.lines.all())
credits = sum(line.credit for line in entry.lines.all())

print(f"Debits: {debits}, Credits: {credits}")

# Fix: adjust lines so they balance
```

---

### Issue: "Account 'AR' with code '1100' not found"

**Cause:** Required GL account doesn't exist

**Solution:**
```python
# Create missing account
Account.objects.create(
    code="1100",
    name="Accounts Receivable",
    type="AS"  # Asset
)
```

---

### Issue: "Posted documents are read-only"

**Cause:** Trying to edit posted invoice

**Solution:**
```python
# Don't edit posted invoices
# Instead: create reversal

from finance.services import reverse_posted_invoice

reversal = reverse_posted_invoice(original_id=1)

# Then create new corrected invoice
corrected = ARInvoice.objects.create(...)
```

---

### Issue: Invoice posted but balance wrong

**Cause:** Totals calculated incorrectly

**Debug:**
```python
from finance.services import ar_totals

invoice = ARInvoice.objects.get(id=1)
totals = ar_totals(invoice)

print(f"Subtotal: {totals['subtotal']}")
print(f"Tax: {totals['tax']}")
print(f"Total: {totals['total']}")
print(f"Paid: {totals['paid']}")
print(f"Balance: {totals['balance']}")
```

---

### Issue: FX gain/loss not posting

**Cause:** FX accounts not configured

**Solution:**
```python
# Create FX accounts
fx_gain = Account.objects.create(
    code="7150",
    name="FX Gain",
    type="IN"  # Income
)

fx_loss = Account.objects.create(
    code="8150",
    name="FX Loss",
    type="EX"  # Expense
)

# Configure in settings
FINANCE_ACCOUNTS = {
    # ...
    "FX_GAIN": "7150",
    "FX_LOSS": "8150",
}
```

---

### Issue: Corporate tax calculation wrong

**Cause:** Incorrect account types or date range

**Debug:**
```python
# Check income accounts
income_accounts = Account.objects.filter(type__in=["INCOME", "IN"])
print(f"Income accounts: {income_accounts}")

# Check expense accounts
expense_accounts = Account.objects.filter(type__in=["EXPENSE", "EX"])
print(f"Expense accounts: {expense_accounts}")

# Check posted journals in period
journals = JournalEntry.objects.filter(
    posted=True,
    date__gte=date_from,
    date__lte=date_to
)
print(f"Posted journals: {journals.count()}")
```

---

## Best Practices

### 1. Always Validate Before Posting
```python
# ✅ DO
try:
    validate_ready_to_post(invoice)
    gl_post_from_ar_balanced(invoice)
except ValidationError as e:
    return f"Cannot post: {e}"
```

### 2. Use Transactions
```python
# ✅ DO
@transaction.atomic
def post_invoice_and_notify(invoice_id):
    invoice = ARInvoice.objects.get(id=invoice_id)
    gl_post_from_ar_balanced(invoice)
    send_notification(invoice.customer.email)
    # If notification fails, posting rolls back ✅
```

### 3. Check Idempotency
```python
# ✅ DO
journal, created = gl_post_from_ar_balanced(invoice)
if created:
    print("Posted now")
else:
    print("Already posted")
```

### 4. Store FX Rates
```python
# ✅ DO - Store rate at transaction time
invoice.fx_rate = get_exchange_rate(eur, usd, invoice.date)
invoice.save()

# ❌ DON'T - Lookup rate later (rates change!)
```

### 5. Handle Errors Gracefully
```python
# ✅ DO
try:
    gl_post_from_ar_balanced(invoice)
except ValueError as e:
    logger.error(f"Posting failed: {e}")
    return Response(
        {"error": str(e)},
        status=status.HTTP_400_BAD_REQUEST
    )
```

---

## Summary

### Posting Methods Overview

| Method | Purpose | GL Impact |
|--------|---------|-----------|
| `gl_post_from_ar_balanced()` | Post AR invoice | DR AR, CR Revenue, CR VAT Out |
| `gl_post_from_ap_balanced()` | Post AP invoice | DR Expense, DR VAT In, CR AP |
| `post_ar_payment()` | Post customer payment | DR Bank, CR AR, +FX |
| `post_ap_payment()` | Post supplier payment | DR AP, CR Bank, +FX |
| `post_entry()` | Post manual journal | Validate & mark posted |
| `accrue_corporate_tax()` | Post tax accrual | DR Tax Exp, CR Tax Payable |

### Key Principles

1. **Idempotency:** Safe to call multiple times
2. **Transaction Safety:** All-or-nothing operations
3. **Validation:** Check before posting
4. **Immutability:** Posted = read-only
5. **Audit Trail:** Link invoices to journals
6. **FX Support:** Automatic gain/loss calculation
7. **Database Locking:** Prevent race conditions

### Accounting Rules Enforced

✅ Debits must equal credits  
✅ Posted entries are immutable  
✅ All entries have audit trail  
✅ FX gains/losses properly recorded  
✅ Tax correctly calculated  
✅ Account balances always accurate  

---

**Last Updated:** October 13, 2025  
**Module:** Finance  
**Framework:** Django 4.x+  
**Author:** Finance Module Documentation Team

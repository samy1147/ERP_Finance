# Finance Models Documentation (models.py)

## Overview
This file contains all database models for the Finance module. It defines the structure for bank accounts, chart of accounts, journal entries, corporate tax, and invoice management with posting locks.

---

## File Location
```
finance/models.py
```

---

## Constants

### `TAX_COUNTRIES`
```python
[("AE","UAE"), ("SA","KSA"), ("EG","Egypt"), ("IN","India")]
```
**Purpose:** Defines supported countries for tax calculations.

### `TAX_CATS`
```python
[("STANDARD","Standard"), ("ZERO","Zero"), ("EXEMPT","Exempt"), ("RC","Reverse Charge")]
```
**Purpose:** Defines tax categories for VAT/GST handling.

---

## Models

### 1. `BankAccount`

**Purpose:** Represents a company bank account used for payments and receipts.

**Fields:**
- `name` (CharField): Bank account name/description
- `account_code` (CharField): Maps to GL chart of accounts (e.g., "1000" for Cash)
- `iban` (CharField): International Bank Account Number
- `swift` (CharField): SWIFT/BIC code for international transfers
- `currency` (ForeignKey → Currency): Account's currency
- `active` (BooleanField): Whether account is currently active
- `history` (HistoricalRecords): Audit trail of all changes

**Methods:**
- `__str__()`: Returns the account name

**Usage:**
```python
bank = BankAccount.objects.create(
    name="Main Operating Account",
    account_code="1000",
    iban="AE070331234567890123456",
    currency=aed_currency,
    active=True
)
```

---

### 2. `Account`

**Purpose:** Chart of Accounts - defines all GL accounts for double-entry bookkeeping.

**Constants:**
```python
ASSET = "AS"
LIABILITY = "LI"
EQUITY = "EQ"
INCOME = "IN"
EXPENSE = "EX"
```

**Fields:**
- `code` (CharField, unique): Account code (e.g., "1100", "4000")
- `name` (CharField): Account name (e.g., "Accounts Receivable", "Revenue")
- `type` (CharField with choices): Account type (ASSET, LIABILITY, etc.)
- `parent` (ForeignKey → self): For hierarchical account structures
- `is_active` (BooleanField): Whether account is active
- `history` (HistoricalRecords): Audit trail

**Meta:**
- `ordering`: Sorted by account code

**Methods:**
- `__str__()`: Returns formatted string "code - name"

**Example:**
```python
# Create parent account
assets = Account.objects.create(
    code="1000",
    name="Assets",
    type=Account.ASSET
)

# Create child account
ar = Account.objects.create(
    code="1100",
    name="Accounts Receivable",
    type=Account.ASSET,
    parent=assets
)
```

---

### 3. `JournalEntry`

**Purpose:** Represents a journal entry (collection of debits and credits).

**Fields:**
- `date` (DateField): Transaction date
- `currency` (ForeignKey → Currency): Entry currency
- `memo` (CharField): Description/reference
- `posted` (BooleanField): Whether entry is posted (locked)
- `history` (HistoricalRecords): Audit trail

**Related:**
- `lines`: Reverse relation to JournalLine (one-to-many)

**Usage:**
```python
je = JournalEntry.objects.create(
    date=date.today(),
    currency=usd,
    memo="Invoice #INV-001",
    posted=True
)
```

---

### 4. `JournalLine`

**Purpose:** Individual debit or credit line in a journal entry.

**Fields:**
- `entry` (ForeignKey → JournalEntry): Parent journal entry
- `account` (ForeignKey → Account): GL account
- `debit` (DecimalField): Debit amount (default 0)
- `credit` (DecimalField): Credit amount (default 0)

**Accounting Rules:**
- Each line must have either debit OR credit (not both)
- Debits and credits in an entry must balance
- Precision: 14 digits, 2 decimal places

**Example:**
```python
# Create balanced journal entry
je = JournalEntry.objects.create(date=date.today(), currency=usd, memo="Sale")

# Debit AR (Asset increases)
JournalLine.objects.create(entry=je, account=ar_account, debit=1050.00, credit=0)

# Credit Revenue (Income increases)
JournalLine.objects.create(entry=je, account=revenue_account, debit=0, credit=1000.00)

# Credit VAT Payable (Liability increases)
JournalLine.objects.create(entry=je, account=vat_account, debit=0, credit=50.00)
```

---

### 5. `CorporateTaxRule`

**Purpose:** Stores corporate tax rates and thresholds by country.

**Fields:**
- `country` (CharField with choices): Country code (AE, SA, EG, IN)
- `rate` (DecimalField): Tax rate as percentage (e.g., 9.000 = 9%)
- `threshold` (DecimalField, optional): Minimum profit for tax applicability
- `active` (BooleanField): Whether rule is currently active
- `notes` (CharField): Additional information
- `history` (HistoricalRecords): Audit trail

**Methods:**
- `__str__()`: Returns "Country CorpTax Rate%"

**Example:**
```python
uae_tax = CorporateTaxRule.objects.create(
    country="AE",
    rate=Decimal("9.000"),
    threshold=Decimal("375000.00"),  # AED 375K threshold
    active=True,
    notes="UAE Corporate Tax 2023"
)
```

---

### 6. `CorporateTaxFiling`

**Purpose:** Tracks corporate tax filing periods and their journal entries.

**Status Choices:**
- `ACCRUED`: Tax calculated and journal entry created
- `FILED`: Tax return filed (locked, cannot modify)
- `REVERSED`: Tax entry reversed

**Fields:**
- `country` (CharField): Country code
- `period_start` (DateField): Tax period start date
- `period_end` (DateField): Tax period end date
- `organization_id` (IntegerField, optional): For multi-org systems
- `accrual_journal` (OneToOneField → JournalEntry): Journal entry for tax accrual
- `reversal_journal` (OneToOneField → JournalEntry): Journal entry for reversal (if needed)
- `status` (CharField with choices): Current status
- `filed_at` (DateTimeField): When tax return was filed
- `notes` (CharField): Additional information
- `history` (HistoricalRecords): Audit trail

**Meta:**
- `unique_together`: (country, period_start, period_end, organization_id)

**Workflow:**
```python
# 1. Create filing (status=ACCRUED)
filing = CorporateTaxFiling.objects.create(
    country="AE",
    period_start=date(2024, 1, 1),
    period_end=date(2024, 12, 31),
    status="ACCRUED"
)

# 2. Create journal entry for tax
je = JournalEntry.objects.create(...)
filing.accrual_journal = je
filing.save()

# 3. File tax return (lock the filing)
filing.status = "FILED"
filing.filed_at = timezone.now()
filing.save()
```

---

### 7. `InvoiceStatus`

**Purpose:** Enum for invoice status values.

**Choices:**
- `DRAFT`: Invoice is editable
- `POSTED`: Invoice is posted to GL (read-only)
- `REVERSED`: Invoice has been reversed

**Usage:**
```python
invoice.status = InvoiceStatus.POSTED
invoice.save()
```

---

### 8. `LockOnPostedMixin` (Abstract)

**Purpose:** Prevents modification of posted documents (invoices, payments).

**Type:** Abstract Model (doesn't create its own table)

**Fields:**
- `status` (CharField): DRAFT, POSTED, or REVERSED

**Protected Fields:** Most fields are locked once status=POSTED

**Editable Fields (even when POSTED):**
- `status`: To allow POSTED → REVERSED
- `reversal_ref_id`: To link to reversal document
- `updated_at`: System timestamp

**Key Methods:**

#### `_is_posted_locked_update()`
**Returns:** Boolean indicating if the update should be blocked

**Logic:**
1. Returns False if creating new record (no pk)
2. Fetches current database state
3. Checks if old status is POSTED
4. Compares all fields except editable ones
5. Returns True if any protected field changed

#### `save()`
**Behavior:**
- Calls `_is_posted_locked_update()`
- Raises `ValidationError` if trying to modify posted document
- Allows save if validation passes

**Example:**
```python
# This will work
invoice = Invoice.objects.create(...)
invoice.status = InvoiceStatus.POSTED
invoice.save()  # OK - posting the invoice

# This will raise ValidationError
invoice.customer_id = 999
invoice.save()  # ERROR - can't change customer on posted invoice

# This will work
invoice.status = InvoiceStatus.REVERSED
invoice.save()  # OK - status is in editable fields
```

---

### 9. `Invoice`

**Purpose:** Main invoice model (uses LockOnPostedMixin for protection).

**Inherits From:** `LockOnPostedMixin`

**Fields:**
- `customer` (ForeignKey → ar.Customer): Customer who owes money
- `invoice_no` (CharField, unique): Invoice number (e.g., "INV-001")
- `currency` (CharField): Currency code
- `total_net` (DecimalField): Subtotal before tax
- `total_tax` (DecimalField): Total tax amount
- `total_gross` (DecimalField): Grand total (net + tax)
- `posted_at` (DateTimeField): When invoice was posted to GL
- `reversal_ref` (ForeignKey → self): Link to reversal invoice
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last modification timestamp
- `status` (inherited from LockOnPostedMixin)

**Meta:**
- Indexes on (status, customer) for faster queries

**Related:**
- `lines`: Reverse relation to InvoiceLine (one-to-many)
- `reversals`: Invoices that reverse this one

**Methods:**

#### `has_lines()`
**Returns:** Boolean - True if invoice has at least one line

#### `any_line_missing_account_or_tax()`
**Returns:** Boolean - True if any line is missing account or tax code

#### `is_zero_totals()`
**Returns:** Boolean - True if all totals are zero

#### `recompute_totals()`
**Purpose:** Recalculates totals from line items
**Usage:** Call before posting to ensure totals are correct

```python
invoice.recompute_totals()
invoice.save()
```

#### `clean()`
**Purpose:** Model-level validation
**Checks:**
- Posted invoice cannot have reversal_ref

**Example Workflow:**
```python
# 1. Create invoice
invoice = Invoice.objects.create(
    customer=customer,
    invoice_no="INV-001",
    currency="USD"
)

# 2. Add lines
InvoiceLine.objects.create(
    invoice=invoice,
    description="Consulting Services",
    quantity=10,
    unit_price=100,
    account=revenue_account,
    tax_code=standard_vat
)

# 3. Recompute and post
invoice.recompute_totals()
invoice.status = InvoiceStatus.POSTED
invoice.posted_at = timezone.now()
invoice.save()

# 4. Try to edit (will fail)
invoice.total_net = 999
invoice.save()  # ValidationError: Posted documents are read-only
```

---

### 10. `TaxCode`

**Purpose:** Defines tax codes with their rates.

**Fields:**
- `code` (CharField, unique): Tax code (e.g., "VAT-5", "ZERO")
- `rate` (DecimalField): Tax rate as decimal (e.g., 0.0500 for 5%)

**Precision:** 6 digits, 4 decimal places (allows 0.0001 = 0.01%)

**Example:**
```python
standard_vat = TaxCode.objects.create(code="VAT-5", rate=Decimal("0.0500"))
zero_rated = TaxCode.objects.create(code="ZERO", rate=Decimal("0.0000"))
```

---

### 11. `InvoiceLine`

**Purpose:** Individual line item on an invoice.

**Fields:**
- `invoice` (ForeignKey → Invoice): Parent invoice
- `description` (CharField): Item description
- `account` (ForeignKey → Account): GL account for revenue/expense
- `tax_code` (ForeignKey → TaxCode): Tax code to apply
- `quantity` (DecimalField): Quantity (precision: 4 decimals)
- `unit_price` (DecimalField): Price per unit (precision: 4 decimals)
- `amount_net` (DecimalField): Net amount (calculated)
- `tax_amount` (DecimalField): Tax amount (calculated)
- `amount_gross` (DecimalField): Gross amount (calculated)

**Methods:**

#### `recompute()`
**Purpose:** Recalculates all amounts based on quantity, price, and tax rate

**Logic:**
```python
net = quantity * unit_price
rate = tax_code.rate (or 0 if no tax code)
tax = net * rate (rounded to 2 decimals)
gross = net + tax
```

#### `save()`
**Behavior:**
- Automatically calls `recompute()` before saving
- Ensures amounts are always correct

**Example:**
```python
line = InvoiceLine(
    invoice=invoice,
    description="Widget",
    quantity=Decimal("5.0000"),
    unit_price=Decimal("20.0000"),
    account=sales_account,
    tax_code=vat_5_code
)
line.save()  # Automatically computes: net=100, tax=5, gross=105
```

---

## Model Relationships

```
BankAccount
    ↓ (used by)
ARPayment / APPayment

Account (Chart of Accounts)
    ↓ (used in)
JournalLine

JournalEntry
    ↓ (contains)
JournalLine (many)

CorporateTaxRule
    ↓ (applied in)
CorporateTaxFiling

CorporateTaxFiling
    ├─ accrual_journal → JournalEntry
    └─ reversal_journal → JournalEntry

Invoice
    ├─ customer → ar.Customer
    ├─ reversal_ref → Invoice (self)
    └─ lines → InvoiceLine (many)

InvoiceLine
    ├─ invoice → Invoice
    ├─ account → Account
    └─ tax_code → TaxCode

TaxCode
    ↓ (used in)
InvoiceLine
```

---

## Historical Records

All major models use **django-simple-history** for audit trails:
- `BankAccount`
- `Account`
- `JournalEntry`
- `CorporateTaxRule`
- `CorporateTaxFiling`

**Benefits:**
- Track all changes to records
- See who changed what and when
- Restore previous versions
- Comply with audit requirements

**Usage:**
```python
# Access history
account = Account.objects.get(code="1100")
for record in account.history.all():
    print(f"{record.history_date}: {record.name} by {record.history_user}")
```

---

## Best Practices

### 1. Posting Protection
✅ **DO:** Use `LockOnPostedMixin` for documents that should be immutable after posting  
❌ **DON'T:** Try to modify posted documents directly - use reversal instead

### 2. Totals Calculation
✅ **DO:** Call `recompute_totals()` before posting invoices  
❌ **DON'T:** Manually set total fields - let the system calculate them

### 3. Tax Codes
✅ **DO:** Store tax rates as decimals (0.0500 for 5%)  
❌ **DON'T:** Store as percentages (5.0000)

### 4. Account Codes
✅ **DO:** Use consistent numbering scheme (1000s for assets, 4000s for income, etc.)  
❌ **DON'T:** Use random codes

### 5. Journal Entries
✅ **DO:** Ensure debits = credits before posting  
❌ **DON'T:** Create unbalanced entries

---

## Common Queries

### Get all posted invoices
```python
invoices = Invoice.objects.filter(status=InvoiceStatus.POSTED)
```

### Get invoice with lines
```python
invoice = Invoice.objects.prefetch_related('lines').get(invoice_no="INV-001")
```

### Get unposted journal entries
```python
entries = JournalEntry.objects.filter(posted=False)
```

### Get active bank accounts
```python
banks = BankAccount.objects.filter(active=True)
```

### Get accounts by type
```python
assets = Account.objects.filter(type=Account.ASSET)
```

---

## Conclusion

The Finance models provide a complete double-entry accounting system with:

✅ **Chart of Accounts:** Flexible hierarchical GL structure  
✅ **Journal Entries:** Double-entry bookkeeping with audit trails  
✅ **Bank Accounts:** Multi-currency bank account management  
✅ **Tax Management:** Support for VAT/GST and corporate tax  
✅ **Invoice Protection:** Immutable posted documents with reversal workflow  
✅ **Automatic Calculations:** Totals and taxes computed automatically  
✅ **Audit Trail:** Complete history of all changes  
✅ **Multi-currency:** Support for international transactions  

The use of `LockOnPostedMixin` ensures data integrity by preventing accidental modifications to posted financial documents, while the automatic total calculation in `InvoiceLine` prevents arithmetic errors. The historical records provide a complete audit trail for compliance purposes.

---

**Last Updated:** October 13, 2025  
**Database:** PostgreSQL/SQLite  
**Django Version:** 4.x+

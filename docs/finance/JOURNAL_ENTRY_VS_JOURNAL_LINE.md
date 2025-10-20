# JournalEntry vs JournalLine: Complete Explanation

## Overview
This document explains the difference between the `JournalEntry` and `JournalLine` tables, their relationship, and how they work together to record accounting transactions in the General Ledger.

---

## Table of Contents
1. [Quick Summary](#quick-summary)
2. [The Header-Detail Pattern](#the-header-detail-pattern)
3. [JournalEntry Table (Header)](#journalentry-table-header)
4. [JournalLine Table (Detail)](#journalline-table-detail)
5. [Relationship Between Tables](#relationship-between-tables)
6. [Real-World Examples](#real-world-examples)
7. [Why Two Tables?](#why-two-tables)
8. [Database Structure](#database-structure)
9. [Code Examples](#code-examples)
10. [Common Queries](#common-queries)

---

## Quick Summary

### TL;DR

| Aspect | JournalEntry | JournalLine |
|--------|--------------|-------------|
| **What it is** | Header/Container | Detail/Line item |
| **Represents** | One transaction | One account affected |
| **Cardinality** | One entry | Many lines per entry |
| **Contains** | Date, memo, currency | Account, debit, credit |
| **Analogy** | Invoice header | Invoice line item |
| **Example** | "Payment on Jan 15" | "Debit Cash $100" |

**Think of it like a document:**
- **JournalEntry** = Document header (invoice number, date, customer)
- **JournalLine** = Line items on that document (products, quantities, prices)

---

## The Header-Detail Pattern

### Concept: Parent-Child Relationship

```
JournalEntry (Parent/Header)
    ↓ has many
JournalLine (Child/Detail)
JournalLine (Child/Detail)
JournalLine (Child/Detail)
```

### Analogy: Restaurant Receipt

Think of a restaurant receipt:

**Receipt Header** (= JournalEntry)
```
Restaurant Name
Date: Jan 15, 2025
Table: 5
Server: John
Check #: 12345
```

**Line Items** (= JournalLine)
```
1. Burger         $15.00
2. Fries          $ 5.00
3. Soda           $ 3.00
   ─────────────  ──────
   Total          $23.00
```

- **One receipt** (JournalEntry)
- **Multiple items** on that receipt (JournalLines)

---

## JournalEntry Table (Header)

### Purpose
Stores the **header information** for a General Ledger transaction. It's the container that holds metadata about the entire transaction.

### What It Contains

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | Integer | Unique identifier | 123 |
| `date` | Date | Transaction date | 2025-01-15 |
| `currency` | ForeignKey | Currency used | USD |
| `memo` | Text | Description | "AR Post INV-001" |
| `posted` | Boolean | Is it finalized? | True |
| `created_at` | DateTime | When created | 2025-01-15 10:30 |
| `organization` | ForeignKey | Company (multi-tenant) | Acme Corp |

### What It Does NOT Contain
- ❌ Account codes
- ❌ Debit amounts
- ❌ Credit amounts
- ❌ Individual transaction details

### Think of It As
- The **envelope** that contains the transaction
- The **header** of a document
- The **container** for line items
- The **summary** of what happened

### Example Record

```python
JournalEntry(
    id=123,
    date=date(2025, 1, 15),
    currency=USD,
    memo="Customer payment received",
    posted=True,
    created_at=datetime(2025, 1, 15, 10, 30, 0)
)
```

This tells us:
- ✅ WHAT happened: "Customer payment received"
- ✅ WHEN it happened: January 15, 2025
- ✅ STATUS: Posted (finalized)
- ❌ But NOT the accounting details (which accounts, amounts)

---

## JournalLine Table (Detail)

### Purpose
Stores the **detailed accounting information** for each account affected by the transaction. Each line represents one account being debited or credited.

### What It Contains

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | Integer | Unique identifier | 456 |
| `entry` | ForeignKey | Link to JournalEntry | 123 |
| `account` | ForeignKey | GL account | Cash (1000) |
| `debit` | Decimal | Debit amount | 100.00 |
| `credit` | Decimal | Credit amount | 0.00 |
| `memo` | Text | Line description | "Cash received" |

### What It Does
- ✅ Links to parent JournalEntry
- ✅ Specifies which account
- ✅ Shows debit or credit amount
- ✅ Creates the actual accounting impact

### Think of It As
- The **contents** of the envelope
- The **line items** on a document
- The **details** of the transaction
- The **actual accounting entries**

### Example Records

```python
# Line 1: Debit Cash
JournalLine(
    id=456,
    entry_id=123,  # Links to JournalEntry above
    account=Account(code="1000", name="Cash"),
    debit=100.00,
    credit=0.00
)

# Line 2: Credit Accounts Receivable
JournalLine(
    id=457,
    entry_id=123,  # Same JournalEntry
    account=Account(code="1100", name="Accounts Receivable"),
    debit=0.00,
    credit=100.00
)
```

These tell us:
- ✅ Cash account increased by $100 (debit)
- ✅ AR account decreased by $100 (credit)
- ✅ Both linked to same transaction (entry_id=123)

---

## Relationship Between Tables

### Database Relationship

```
┌─────────────────────────────┐
│      JournalEntry           │
│  (id: 123)                  │
│  date: 2025-01-15           │
│  memo: "Payment received"   │
│  posted: True               │
└──────────────┬──────────────┘
               │
               │ One-to-Many
               │
       ┌───────┴────────┬────────────┐
       │                │            │
       ▼                ▼            ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ JournalLine  │  │ JournalLine  │  │ JournalLine  │
│ (id: 456)    │  │ (id: 457)    │  │ (id: 458)    │
│ entry_id:123 │  │ entry_id:123 │  │ entry_id:123 │
│ account:Cash │  │ account: AR  │  │ account: FX  │
│ DR: 100      │  │ CR: 100      │  │ CR: 5        │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Key Rules

1. **One JournalEntry has MANY JournalLines**
   - Minimum: 2 lines (double-entry accounting)
   - No maximum
   - Typical: 2-5 lines

2. **Each JournalLine belongs to ONE JournalEntry**
   - Cannot be shared between entries
   - Foreign key enforces relationship

3. **Lines must balance**
   - Total debits = Total credits
   - Enforced before posting

### Django Model Relationship

```python
class JournalEntry(models.Model):
    date = models.DateField()
    memo = models.TextField()
    posted = models.BooleanField(default=False)
    # ... other fields

class JournalLine(models.Model):
    entry = models.ForeignKey(
        JournalEntry,
        related_name='lines',  # Access: entry.lines.all()
        on_delete=models.CASCADE  # Delete lines when entry deleted
    )
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=12, decimal_places=2)
    credit = models.DecimalField(max_digits=12, decimal_places=2)
```

**Accessing Lines from Entry:**
```python
entry = JournalEntry.objects.get(id=123)
lines = entry.lines.all()  # Get all JournalLines for this entry
```

**Accessing Entry from Line:**
```python
line = JournalLine.objects.get(id=456)
entry = line.entry  # Get parent JournalEntry
```

---

## Real-World Examples

### Example 1: Customer Payment

**Scenario:** Customer pays $1,000 cash for outstanding invoice

**JournalEntry (Header):**
```python
{
    "id": 100,
    "date": "2025-01-15",
    "memo": "Payment from Acme Corp for INV-001",
    "posted": True
}
```

**JournalLines (Details):**
```python
[
    {
        "id": 200,
        "entry_id": 100,
        "account": "1000 - Cash",
        "debit": 1000.00,
        "credit": 0.00
    },
    {
        "id": 201,
        "entry_id": 100,
        "account": "1100 - Accounts Receivable",
        "debit": 0.00,
        "credit": 1000.00
    }
]
```

**In T-Account Format:**
```
Cash (1000)              Accounts Receivable (1100)
────────────             ───────────────────────────
DR  1,000 |              |  CR  1,000
```

**Explanation:**
- **JournalEntry** says: "On Jan 15, we received a payment"
- **JournalLines** say: "We debited Cash $1000 and credited AR $1000"

---

### Example 2: Invoice Posting

**Scenario:** Invoice customer $1,000 + $50 VAT

**JournalEntry (Header):**
```python
{
    "id": 101,
    "date": "2025-01-20",
    "memo": "AR Post INV-002",
    "posted": True
}
```

**JournalLines (Details):**
```python
[
    {
        "id": 202,
        "entry_id": 101,
        "account": "1100 - Accounts Receivable",
        "debit": 1050.00,
        "credit": 0.00
    },
    {
        "id": 203,
        "entry_id": 101,
        "account": "4000 - Revenue",
        "debit": 0.00,
        "credit": 1000.00
    },
    {
        "id": 204,
        "entry_id": 101,
        "account": "2100 - VAT Output",
        "debit": 0.00,
        "credit": 50.00
    }
]
```

**In T-Account Format:**
```
AR (1100)              Revenue (4000)         VAT Output (2100)
─────────              ──────────────         ─────────────────
DR 1,050 |             |  CR 1,000            |  CR 50
```

**Explanation:**
- **JournalEntry** says: "On Jan 20, we posted an AR invoice"
- **JournalLines** say: "We debited AR $1,050, credited Revenue $1,000, and credited VAT $50"

---

### Example 3: Complex Transaction

**Scenario:** Payment with foreign exchange gain

**JournalEntry (Header):**
```python
{
    "id": 102,
    "date": "2025-02-01",
    "memo": "Payment EUR 1000 with FX gain",
    "posted": True,
    "currency": "USD"
}
```

**JournalLines (Details):**
```python
[
    {
        "id": 205,
        "entry_id": 102,
        "account": "1000 - Cash",
        "debit": 1120.00,    # Actually received
        "credit": 0.00
    },
    {
        "id": 206,
        "entry_id": 102,
        "account": "1100 - Accounts Receivable",
        "debit": 0.00,
        "credit": 1100.00    # Originally booked
    },
    {
        "id": 207,
        "entry_id": 102,
        "account": "7150 - FX Gain",
        "debit": 0.00,
        "credit": 20.00      # Exchange gain
    }
]
```

**In T-Account Format:**
```
Cash (1000)           AR (1100)              FX Gain (7150)
───────────           ─────────              ──────────────
DR 1,120 |            | CR 1,100             | CR 20
```

**Explanation:**
- **JournalEntry** says: "On Feb 1, we received payment with FX impact"
- **JournalLines** say: "We got $1,120 cash, reduced AR by $1,100, and recognized $20 FX gain"

---

## Why Two Tables?

### Reason 1: Data Normalization

**Bad Design (One Table):**
```
Transaction Table:
─────────────────────────────────────────────────────────
| date       | memo              | account | debit | credit |
─────────────────────────────────────────────────────────
| 2025-01-15 | Payment received  | Cash    | 100   | 0      |
| 2025-01-15 | Payment received  | AR      | 0     | 100    |
─────────────────────────────────────────────────────────
```

**Problems:**
- ❌ Date repeated (redundancy)
- ❌ Memo repeated (redundancy)
- ❌ Hard to query "all entries on Jan 15"
- ❌ Hard to enforce "must have 2+ lines"
- ❌ Update memo requires updating multiple rows

**Good Design (Two Tables):**
```
JournalEntry Table:
────────────────────────────────────
| id  | date       | memo             |
────────────────────────────────────
| 100 | 2025-01-15 | Payment received |
────────────────────────────────────

JournalLine Table:
──────────────────────────────────────────
| id  | entry_id | account | debit | credit |
──────────────────────────────────────────
| 200 | 100      | Cash    | 100   | 0      |
| 201 | 100      | AR      | 0     | 100    |
──────────────────────────────────────────
```

**Benefits:**
- ✅ Date stored once
- ✅ Memo stored once
- ✅ Easy to query entries
- ✅ Easy to enforce business rules
- ✅ Update memo once

---

### Reason 2: Double-Entry Accounting

**Accounting Rule:** Every transaction affects at least 2 accounts

**With Two Tables:**
```python
# Create entry
entry = JournalEntry.objects.create(
    date=date.today(),
    memo="Sale transaction"
)

# Add multiple lines (minimum 2)
JournalLine.objects.create(entry=entry, account=cash, debit=100)
JournalLine.objects.create(entry=entry, account=revenue, credit=100)
# Can add more lines as needed
JournalLine.objects.create(entry=entry, account=tax, credit=5)
```

**With One Table:** Would be messy and repetitive

---

### Reason 3: Flexible Line Count

Different transactions need different numbers of lines:

**Simple (2 lines):**
```
Entry: Cash sale
  Line 1: DR Cash         100
  Line 2: CR Revenue      100
```

**Medium (3 lines):**
```
Entry: Invoice with tax
  Line 1: DR AR           105
  Line 2: CR Revenue      100
  Line 3: CR VAT           5
```

**Complex (5+ lines):**
```
Entry: Multi-currency payment with fees
  Line 1: DR Cash USD     1000
  Line 2: DR Bank Fees      10
  Line 3: DR FX Loss        20
  Line 4: CR AR           1100
  Line 5: CR Cash EUR      100
```

**Two tables handle all these cases elegantly!**

---

### Reason 4: Validation & Business Rules

**Check Balance:**
```python
def validate_entry(entry):
    lines = entry.lines.all()
    total_debit = sum(line.debit for line in lines)
    total_credit = sum(line.credit for line in lines)
    
    if total_debit != total_credit:
        raise ValidationError("Entry is unbalanced!")
```

**With one table:** Would need to group rows and validate - much harder

---

### Reason 5: Querying & Reporting

**Easy Queries with Two Tables:**

```python
# Get all entries on a date
entries = JournalEntry.objects.filter(date=date(2025, 1, 15))

# Get all lines for Cash account
cash_lines = JournalLine.objects.filter(account__code="1000")

# Get entry with its lines
entry = JournalEntry.objects.prefetch_related('lines').get(id=100)
for line in entry.lines.all():
    print(f"{line.account.name}: DR {line.debit}, CR {line.credit}")

# Trial Balance (aggregate lines by account)
trial_balance = JournalLine.objects.filter(
    entry__posted=True
).values(
    'account__code', 'account__name'
).annotate(
    total_debit=Sum('debit'),
    total_credit=Sum('credit')
)
```

**Much harder with one table!**

---

## Database Structure

### Table Definitions

**JournalEntry Table:**
```sql
CREATE TABLE finance_journalentry (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    currency_id     INTEGER REFERENCES core_currency(id),
    memo            TEXT,
    posted          BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    organization_id INTEGER REFERENCES core_organization(id)
);

CREATE INDEX idx_je_date ON finance_journalentry(date);
CREATE INDEX idx_je_posted ON finance_journalentry(posted);
```

**JournalLine Table:**
```sql
CREATE TABLE finance_journalline (
    id         SERIAL PRIMARY KEY,
    entry_id   INTEGER NOT NULL REFERENCES finance_journalentry(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES finance_account(id) ON DELETE PROTECT,
    debit      NUMERIC(12, 2) DEFAULT 0.00,
    credit     NUMERIC(12, 2) DEFAULT 0.00,
    memo       TEXT
);

CREATE INDEX idx_jl_entry ON finance_journalline(entry_id);
CREATE INDEX idx_jl_account ON finance_journalline(account_id);
```

### Foreign Key Behavior

**ON DELETE CASCADE:**
```sql
entry_id INTEGER REFERENCES finance_journalentry(id) ON DELETE CASCADE
```

**What this means:**
- If you delete a JournalEntry
- All its JournalLines are automatically deleted
- Prevents orphaned lines

**Example:**
```python
entry = JournalEntry.objects.get(id=100)
entry.delete()  # Also deletes lines 200, 201, 202, etc.
```

---

## Code Examples

### Creating Entry with Lines

```python
from decimal import Decimal
from django.db import transaction

@transaction.atomic
def create_payment_entry(payment_amount, payment_date):
    """
    Creates journal entry for customer payment
    """
    # Step 1: Create JournalEntry (header)
    entry = JournalEntry.objects.create(
        date=payment_date,
        memo=f"Customer payment ${payment_amount}",
        posted=False  # Not posted yet
    )
    
    # Step 2: Create JournalLines (details)
    cash_account = Account.objects.get(code="1000")
    ar_account = Account.objects.get(code="1100")
    
    # Debit Cash
    JournalLine.objects.create(
        entry=entry,
        account=cash_account,
        debit=payment_amount,
        credit=Decimal("0.00")
    )
    
    # Credit AR
    JournalLine.objects.create(
        entry=entry,
        account=ar_account,
        debit=Decimal("0.00"),
        credit=payment_amount
    )
    
    # Step 3: Validate balance
    total_debit = sum(line.debit for line in entry.lines.all())
    total_credit = sum(line.credit for line in entry.lines.all())
    
    if total_debit != total_credit:
        raise ValueError(f"Unbalanced! DR:{total_debit} CR:{total_credit}")
    
    # Step 4: Post entry
    entry.posted = True
    entry.save()
    
    return entry
```

---

### Reading Entry with Lines

```python
def display_journal_entry(entry_id):
    """
    Displays a journal entry in readable format
    """
    # Get entry with all lines (efficient query)
    entry = JournalEntry.objects.prefetch_related(
        'lines__account'
    ).get(id=entry_id)
    
    print(f"\nJournal Entry #{entry.id}")
    print(f"Date: {entry.date}")
    print(f"Memo: {entry.memo}")
    print(f"Posted: {entry.posted}")
    print("\nLines:")
    print("-" * 60)
    print(f"{'Account':<30} {'Debit':>12} {'Credit':>12}")
    print("-" * 60)
    
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    
    for line in entry.lines.all():
        print(f"{line.account.name:<30} {line.debit:>12.2f} {line.credit:>12.2f}")
        total_debit += line.debit
        total_credit += line.credit
    
    print("-" * 60)
    print(f"{'TOTAL':<30} {total_debit:>12.2f} {total_credit:>12.2f}")
    print(f"Balanced: {total_debit == total_credit}")

# Usage
display_journal_entry(100)

# Output:
# Journal Entry #100
# Date: 2025-01-15
# Memo: Customer payment $1000
# Posted: True
#
# Lines:
# ------------------------------------------------------------
# Account                            Debit       Credit
# ------------------------------------------------------------
# Cash                             1000.00         0.00
# Accounts Receivable                 0.00      1000.00
# ------------------------------------------------------------
# TOTAL                            1000.00      1000.00
# Balanced: True
```

---

### Querying Lines by Account

```python
def get_account_activity(account_code, date_from, date_to):
    """
    Gets all journal lines for an account in a date range
    """
    lines = JournalLine.objects.filter(
        account__code=account_code,
        entry__posted=True,
        entry__date__gte=date_from,
        entry__date__lte=date_to
    ).select_related(
        'entry', 'account'
    ).order_by('entry__date')
    
    print(f"\nActivity for Account {account_code}")
    print(f"Period: {date_from} to {date_to}")
    print("-" * 80)
    print(f"{'Date':<12} {'Memo':<30} {'Debit':>12} {'Credit':>12}")
    print("-" * 80)
    
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    
    for line in lines:
        print(f"{line.entry.date!s:<12} {line.entry.memo[:30]:<30} "
              f"{line.debit:>12.2f} {line.credit:>12.2f}")
        total_debit += line.debit
        total_credit += line.credit
    
    print("-" * 80)
    print(f"{'TOTAL':<42} {total_debit:>12.2f} {total_credit:>12.2f}")
    
    net_change = total_debit - total_credit
    print(f"Net Change: {net_change:>12.2f}")

# Usage
get_account_activity("1000", date(2025, 1, 1), date(2025, 1, 31))
```

---

## Common Queries

### 1. Get Entry and All Lines

```python
# Efficient way (one query for lines)
entry = JournalEntry.objects.prefetch_related('lines').get(id=100)
for line in entry.lines.all():
    print(f"{line.account.name}: {line.debit}/{line.credit}")
```

### 2. Count Lines in Entry

```python
entry = JournalEntry.objects.get(id=100)
line_count = entry.lines.count()
print(f"Entry has {line_count} lines")
```

### 3. Sum Debits and Credits

```python
from django.db.models import Sum

entry = JournalEntry.objects.get(id=100)
totals = entry.lines.aggregate(
    total_debit=Sum('debit'),
    total_credit=Sum('credit')
)
print(f"Debits: {totals['total_debit']}")
print(f"Credits: {totals['total_credit']}")
```

### 4. Find Unbalanced Entries

```python
from django.db.models import Sum, F

unbalanced = JournalEntry.objects.annotate(
    total_debit=Sum('lines__debit'),
    total_credit=Sum('lines__credit')
).exclude(
    total_debit=F('total_credit')
)

for entry in unbalanced:
    print(f"Entry {entry.id} is unbalanced!")
```

### 5. Get All Entries for an Account

```python
cash_account = Account.objects.get(code="1000")

# Get all entries that touch Cash account
entries_with_cash = JournalEntry.objects.filter(
    lines__account=cash_account
).distinct()

print(f"Found {entries_with_cash.count()} entries affecting Cash")
```

### 6. Trial Balance Query

```python
from django.db.models import Sum

trial_balance = JournalLine.objects.filter(
    entry__posted=True
).values(
    'account__code',
    'account__name'
).annotate(
    total_debit=Sum('debit'),
    total_credit=Sum('credit')
).order_by('account__code')

for row in trial_balance:
    print(f"{row['account__code']} {row['account__name']}: "
          f"DR {row['total_debit']} CR {row['total_credit']}")
```

---

## Visual Summary

### Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    JournalEntry (Header)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ id: 100                                              │   │
│  │ date: 2025-01-15                                     │   │
│  │ memo: "Customer payment received"                    │   │
│  │ posted: True                                         │   │
│  │ created_at: 2025-01-15 10:30:00                      │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ entry_id (Foreign Key)
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  JournalLine    │  │  JournalLine    │  │  JournalLine    │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │ id: 200   │  │  │  │ id: 201   │  │  │  │ id: 202   │  │
│  │entry:100  │  │  │  │entry:100  │  │  │  │entry:100  │  │
│  │acct: Cash │  │  │  │acct: AR   │  │  │  │acct: FX   │  │
│  │DR: 1020   │  │  │  │CR: 1000   │  │  │  │CR: 20     │  │
│  │CR: 0      │  │  │  │DR: 0      │  │  │  │DR: 0      │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
     (Detail)             (Detail)             (Detail)
```

---

## Key Takeaways

### 🎯 Essential Points

1. **JournalEntry = Header/Container**
   - Stores metadata (date, memo, status)
   - One entry per transaction
   - No account or amount info

2. **JournalLine = Detail/Line Item**
   - Stores accounting info (account, debit, credit)
   - Multiple lines per entry
   - Each line affects one account

3. **Relationship = One-to-Many**
   - One JournalEntry has many JournalLines
   - Each JournalLine belongs to one JournalEntry
   - Minimum 2 lines per entry (double-entry rule)

4. **Benefits of Two Tables**
   - ✅ Data normalization (no redundancy)
   - ✅ Flexible line count
   - ✅ Easy validation (check balance)
   - ✅ Efficient queries
   - ✅ Follows accounting principles

5. **Always Use Together**
   - Never create JournalEntry without lines
   - Never create JournalLine without entry
   - Always validate totals match

---

## Analogy Summary

Think of them like an **email**:

**JournalEntry** = Email metadata
- From: sender
- To: recipient
- Date: sent date
- Subject: topic
- Status: read/unread

**JournalLine** = Email body content
- Paragraph 1
- Paragraph 2
- Paragraph 3

You can't have an email without metadata, and you can't have meaningful metadata without content. Both are needed, and they serve different purposes!

---

**Last Updated:** October 13, 2025  
**Module:** Finance  
**Related Docs:** 
- [02_MODELS.md](02_MODELS.md) - Full model documentation
- [POSTING_METHODS_EXPLAINED.md](POSTING_METHODS_EXPLAINED.md) - How posting creates these entries

# Finance Module - Quick Reference Guide

**Last Updated:** October 13, 2025

## 📋 Table of Contents
1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [AR Invoice Posting Flow](#ar-invoice-posting-flow)
4. [Key Functions](#key-functions)
5. [Database Tables](#database-tables)
6. [API Endpoints](#api-endpoints)

---

## Overview

**Finance Module:** Double-entry accounting system with multi-currency support (IAS 21 compliant)

**Tech Stack:** Django 4.x + DRF 3.14 + PostgreSQL + Next.js

**Key Features:**
- Double-entry accounting (every debit has a credit)
- Multi-currency with automatic FX gain/loss
- AR/AP invoice management
- Payment processing with allocation
- Tax calculations (VAT, Corporate Tax)
- Audit trails (django-simple-history)

---

## Core Concepts

### 1. JournalEntry vs JournalLine

```
JournalEntry (Header)          JournalLine (Detail)
├─ entry_date                  ├─ account_id
├─ description                 ├─ debit_amount
├─ total_debit                 ├─ credit_amount
├─ total_credit                ├─ description
└─ is_posted ────────┐         └─ journal_entry_id ──┘
                     └─────── One-to-Many Relationship
```

**Rule:** `sum(debits) = sum(credits)` for each JournalEntry

### 2. Chart of Accounts (CoA)

```
Account Types:
├─ Asset (DR normal)
├─ Liability (CR normal)
├─ Equity (CR normal)
├─ Revenue (CR normal)
└─ Expense (DR normal)
```

### 3. Posting States

- **Draft:** Editable, not in GL
- **Posted:** Read-only, affects GL balances
- **Reversed:** Cancelled with reversal entry

---

## AR Invoice Posting Flow

### Step-by-Step Process

```
1. CREATE INVOICE (Draft)
   Frontend → POST /api/ar/invoices/
   ↓
2. SAVE TO DATABASE
   - ARInvoice (header)
   - ARInvoiceItem (lines)
   - Status: "draft"
   ↓
3. POST INVOICE
   Frontend → POST /api/ar/invoices/{id}/post/
   ↓
4. BACKEND PROCESSING
   gl_post_from_ar_balanced() function
   ↓
5. CREATE JOURNAL ENTRY
   - Calculate totals + tax
   - Create JournalEntry (header)
   - Create JournalLines (debits/credits)
   ↓
6. UPDATE INVOICE
   - Set is_posted = True
   - Link gl_entry_id
   - Make read-only
```

### Accounting Impact (Example: $1,000 + $50 tax)

```
DR  Accounts Receivable    $1,050
    CR  Revenue                    $1,000
    CR  Tax Payable                $   50
```

### Database Changes

**Before Posting:**
- ARInvoice: `is_posted=False`, `gl_entry_id=NULL`
- JournalEntry: (none)
- JournalLine: (none)

**After Posting:**
- ARInvoice: `is_posted=True`, `gl_entry_id=15`
- JournalEntry: Created (id=15, is_posted=True)
- JournalLine: 3 rows created (1 debit, 2 credits)

---

## Key Functions

### Posting Functions

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `gl_post_from_ar_balanced()` | Post AR invoice to GL | ARInvoice | JournalEntry |
| `gl_post_from_ap_balanced()` | Post AP invoice to GL | APInvoice | JournalEntry |
| `post_ar_payment()` | Post AR payment | ARPayment | JournalEntry |
| `post_ap_payment()` | Post AP payment | APPayment | JournalEntry |
| `reverse_journal_entry()` | Reverse posted entry | JournalEntry | JournalEntry |

### FX Functions

| Function | Purpose |
|----------|---------|
| `get_exchange_rate()` | Get rate for date/currency pair |
| `convert_currency()` | Convert amount between currencies |
| `calculate_fx_gain_loss()` | Calculate unrealized FX gain/loss |
| `post_fx_revaluation()` | Post FX adjustment to GL |

### Validation Functions

| Function | Purpose |
|----------|---------|
| `validate_balanced_entry()` | Check debits = credits |
| `validate_posted_cannot_edit()` | Block edits to posted entries |
| `validate_accounts_exist()` | Verify accounts in CoA |

---

## Database Tables

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `finance_journalentry` | GL header | entry_date, total_debit, total_credit, is_posted |
| `finance_journalline` | GL detail | account_id, debit_amount, credit_amount |
| `finance_account` | Chart of Accounts | code, name, account_type |
| `finance_arinvoice` | AR invoices | customer_id, total_amount, is_posted |
| `finance_arinvoiceitem` | AR line items | invoice_id, amount, tax_rate_id |
| `finance_arpayment` | AR payments | customer_id, amount, payment_date |
| `finance_apinvoice` | AP invoices | supplier_id, total_amount, is_posted |
| `finance_appayment` | AP payments | supplier_id, amount, payment_date |
| `core_currency` | Currencies | code (USD, EUR), symbol |
| `finance_exchangerate` | FX rates | from_currency, to_currency, rate, date |

### Relationships

```
Customer ──1:N── ARInvoice ──1:N── ARInvoiceItem
             │       │
             │       └─1:1── JournalEntry ──1:N── JournalLine
             │                                          │
             └────────────N:1──────────────────────────┘
                                                   Account
```

---

## API Endpoints

### Invoice Management

```http
# List invoices
GET /api/ar/invoices/

# Create invoice (draft)
POST /api/ar/invoices/
Body: {
  "customer": 1,
  "invoice_date": "2025-01-15",
  "items": [
    {"description": "Service", "amount": "1000.00", "tax_rate": 1}
  ]
}

# Post invoice to GL
POST /api/ar/invoices/{id}/post/

# Reverse posted invoice
POST /api/ar/invoices/{id}/reverse/
```

### Payment Processing

```http
# Create AR payment
POST /api/ar/payments/
Body: {
  "customer": 1,
  "amount": "1050.00",
  "payment_date": "2025-01-20",
  "allocations": [
    {"invoice": 5, "amount": "1050.00"}
  ]
}

# Post payment to GL
POST /api/ar/payments/{id}/post/
```

### Reports

```http
# Trial Balance
GET /api/reports/trial-balance/?as_of=2025-01-31

# AR Aging
GET /api/reports/ar-aging/?as_of=2025-01-31

# AP Aging
GET /api/reports/ap-aging/?as_of=2025-01-31
```

### Foreign Exchange

```http
# Get exchange rate
GET /api/fx/rates/?from_currency=USD&to_currency=EUR&date=2025-01-15

# Convert currency
POST /api/fx/convert/
Body: {
  "amount": "1000",
  "from_currency": "USD",
  "to_currency": "EUR",
  "date": "2025-01-15"
}

# Create exchange rate
POST /api/fx/create-rate/
Body: {
  "from_currency": "USD",
  "to_currency": "EUR",
  "rate": "0.92",
  "date": "2025-01-15"
}
```

---

## Quick Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Unbalanced entry" | Debits ≠ Credits | Check calculations, ensure totals match |
| "Cannot edit posted invoice" | Signal blocks edits | Reverse invoice first, then create new |
| "Account not found" | Invalid account_id | Verify account exists in CoA |
| "Exchange rate not found" | Missing FX rate | Create rate for date/currency pair |

### Best Practices

1. **Always validate before posting** - Check totals, accounts, dates
2. **Use transactions** - Wrap posting in `transaction.atomic()`
3. **Handle FX rates** - Ensure rates exist before multi-currency transactions
4. **Audit everything** - django-simple-history tracks all changes
5. **Never delete posted entries** - Use reverse instead

---

## File Structure

```
finance/
├── models.py           # 11 models (600+ lines)
├── serializers.py      # 21 serializers (446 lines)
├── services.py         # 33+ functions (789 lines)
├── fx_services.py      # 8 FX functions (337 lines)
├── api.py              # 21 ViewSets (1156 lines)
├── signals.py          # 3 validators (165 lines)
└── apps.py             # Config (18 lines)
```

---

## Additional Documentation

For detailed information, see:
- **README.md** - Full module overview
- **POSTING_METHODS_EXPLAINED.md** - All posting methods in detail
- **JOURNAL_ENTRY_VS_JOURNAL_LINE.md** - Table relationship deep dive
- **AR_POSTING_DEEP_DIVE.md** - AR posting with scenarios
- **01-07 Module Files** - Individual file documentation

---

**Need Help?** Check the full documentation in `/docs/finance/` directory.

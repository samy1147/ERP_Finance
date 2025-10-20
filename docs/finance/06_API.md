# Finance API Documentation (api.py)

## Overview
This file defines REST API endpoints for the Finance module using Django REST Framework. It provides ViewSets for CRUD operations and APIViews for specialized operations like reporting, posting, and tax management.

---

## File Location
```
finance/api.py
```

---

## Architecture

**Framework:** Django REST Framework (DRF)  
**Pattern:** ViewSets for resources, APIViews for operations  
**Authentication:** Django session authentication  
**Documentation:** drf-spectacular (OpenAPI/Swagger)

---

## API Categories

### 📊 Reports (3 endpoints)
- Trial Balance Report
- AR Aging Report  
- AP Aging Report

### 💰 Invoices (2 ViewSets)
- AR Invoice CRUD + Post/Reverse actions
- AP Invoice CRUD + Post/Reverse actions

### 💳 Payments (2 ViewSets)
- AR Payment CRUD + Post action
- AP Payment CRUD + Post action

### 📖 General Ledger (2 ViewSets)
- Journal Entry CRUD + Post action
- Account CRUD

### 💱 Multi-currency (2 ViewSets)
- Currency CRUD
- Exchange Rate CRUD + Convert action

### 🏦 Banking (1 ViewSet)
- Bank Account CRUD

### 📋 Tax Management (5 endpoints)
- Seed VAT Presets
- List Tax Rates
- Corporate Tax Accrual
- Corporate Tax Filing
- Corporate Tax Reversal

### 🔒 Utilities (1 endpoint)
- CSRF Token retrieval

---

## Report Endpoints

### 1. `TrialBalanceReport` (GET /finance/trial-balance/)

**Purpose:** Generates trial balance report

**Query Parameters:**
- `date_from`: Start date (YYYY-MM-DD, optional)
- `date_to`: End date (YYYY-MM-DD, optional)
- `format`: Response format (json, csv, xlsx)

**Response (JSON):**
```json
[
  {"code": "1000", "name": "Cash", "debit": 5000.00, "credit": 0.00},
  {"code": "4000", "name": "Revenue", "debit": 0.00, "credit": 5000.00},
  {"code": "TOTAL", "name": "", "debit": 5000.00, "credit": 5000.00}
]
```

**CSV Export:**
```
GET /finance/trial-balance/?format=csv
```

**Excel Export:**
```
GET /finance/trial-balance/?format=xlsx
```

---

### 2. `ARAgingReport` (GET /finance/ar-aging/)

**Purpose:** Generates accounts receivable aging report

**Query Parameters:**
- `as_of`: Report date (YYYY-MM-DD, default: today)
- `format`: Response format (json, csv, xlsx)
- `b1`, `b2`, `b3`: Bucket sizes in days (default: 30 each)

**Response:**
```json
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

---

### 3. `APAgingReport` (GET /finance/ap-aging/)

**Purpose:** Generates accounts payable aging report

**Same structure as ARAgingReport but with `supplier` instead of `customer`**

---

## Invoice ViewSets

### 4. `ARInvoiceViewSet` (ViewSet)

**Base URL:** `/finance/ar-invoices/`

**Standard Actions:**
- `GET /` - List all AR invoices
- `POST /` - Create new AR invoice
- `GET /{id}/` - Retrieve AR invoice
- `PUT /{id}/` - Update AR invoice (DRAFT only)
- `DELETE /{id}/` - Delete AR invoice (DRAFT only)

**Custom Actions:**

#### POST /{id}/post/ - Post Invoice to GL
**Purpose:** Posts invoice to General Ledger

**Request:** Empty body

**Response:**
```json
{
  "message": "Invoice posted successfully",
  "journal_id": 123,
  "created": true
}
```

**Errors:**
- 404: Invoice not found
- 400: Validation failed (no lines, missing data, etc.)
- 400: Already posted (idempotent)

**Example:**
```bash
curl -X POST http://localhost:8000/finance/ar-invoices/1/post/
```

#### POST /{id}/reverse/ - Reverse Posted Invoice
**Purpose:** Creates reversing invoice

**Request:** Empty body

**Response:**
```json
{
  "message": "Invoice reversed successfully",
  "reversal_id": 124,
  "reversal_number": "INV-001-REV"
}
```

**Errors:**
- 404: Invoice not found
- 400: Invoice not posted
- 400: Already reversed (idempotent)

---

### 5. `APInvoiceViewSet` (ViewSet)

**Base URL:** `/finance/ap-invoices/`

**Same structure as ARInvoiceViewSet**

**Custom Actions:**
- `POST /{id}/post/` - Post to GL
- `POST /{id}/reverse/` - Reverse invoice

---

## Payment ViewSets

### 6. `ARPaymentViewSet` (ViewSet)

**Base URL:** `/finance/ar-payments/`

**Standard Actions:**
- `GET /` - List payments
- `POST /` - Create payment
- `GET /{id}/` - Retrieve payment
- `PUT /{id}/` - Update payment
- `DELETE /{id}/` - Delete payment

**Custom Actions:**

#### POST /{id}/post/ - Post Payment to GL
**Purpose:** Posts payment to General Ledger with FX handling

**Request:** Empty body

**Response:**
```json
{
  "message": "Payment posted successfully",
  "journal_id": 125,
  "invoice_closed": true
}
```

**FX Handling:**
If payment in different currency than invoice, FX gain/loss automatically calculated and posted

**Example:**
```bash
curl -X POST http://localhost:8000/finance/ar-payments/1/post/
```

---

### 7. `APPaymentViewSet` (ViewSet)

**Base URL:** `/finance/ap-payments/`

**Same structure as ARPaymentViewSet**

**Custom Actions:**
- `POST /{id}/post/` - Post to GL with FX

---

## General Ledger ViewSets

### 8. `JournalEntryViewSet` (ViewSet)

**Base URL:** `/finance/journal-entries/`

**Standard Actions:**
- `GET /` - List entries
- `POST /` - Create entry
- `GET /{id}/` - Retrieve entry
- `PUT /{id}/` - Update entry (unposted only)
- `DELETE /{id}/` - Delete entry (unposted only)

**Custom Actions:**

#### POST /{id}/post/ - Post Journal Entry
**Purpose:** Validates and posts journal entry

**Validation:**
- Debits must equal credits
- Entry must have at least 2 lines

**Response:**
```json
{
  "message": "Journal entry posted successfully",
  "id": 123
}
```

---

### 9. `AccountViewSet` (ViewSet)

**Base URL:** `/finance/accounts/`

**Purpose:** Chart of Accounts CRUD

**Standard Actions:**
- `GET /` - List accounts
- `POST /` - Create account
- `GET /{id}/` - Retrieve account
- `PUT /{id}/` - Update account
- `DELETE /{id}/` - Delete account

**Response Example:**
```json
{
  "id": 5,
  "code": "1100",
  "name": "Accounts Receivable",
  "type": "AS"
}
```

---

## Multi-currency ViewSets

### 10. `CurrencyViewSet` (ViewSet)

**Base URL:** `/finance/currencies/`

**Standard CRUD for currencies**

**Response Example:**
```json
{
  "id": 1,
  "code": "USD",
  "name": "US Dollar",
  "symbol": "$",
  "is_base": true
}
```

---

### 11. `ExchangeRateViewSet` (ViewSet)

**Base URL:** `/finance/exchange-rates/`

**Standard Actions:** CRUD for exchange rates

**Custom Actions:**

#### POST /convert/ - Convert Amount
**Purpose:** Converts amount between currencies

**Request:**
```json
{
  "amount": "1000.00",
  "from_currency": "USD",
  "to_currency": "AED",
  "as_of_date": "2025-01-15",
  "rate_type": "SPOT"
}
```

**Response:**
```json
{
  "from_amount": "1000.00",
  "from_currency": "USD",
  "to_amount": "3672.50",
  "to_currency": "AED",
  "rate": "3.6725",
  "rate_date": "2025-01-15"
}
```

---

## Banking ViewSets

### 12. `BankAccountViewSet` (ViewSet)

**Base URL:** `/finance/bank-accounts/`

**Standard CRUD for bank accounts**

**Response Example:**
```json
{
  "id": 1,
  "name": "Main Checking",
  "account_number": "123456789",
  "bank_name": "First National Bank",
  "account_code": "1010",
  "currency": 1
}
```

---

## Tax Management Endpoints

### 13. `SeedVATPresets` (POST /finance/seed-vat/)

**Purpose:** Seeds standard VAT/GST rates for countries

**Request:**
```json
{
  "effective_from": "2025-01-01"
}
```

**Response:**
```json
{
  "message": "Seeded 12 tax rates",
  "created_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
}
```

**Countries Seeded:**
- AE (UAE): 5%, 0%, Exempt
- SA (Saudi): 15%, 0%, Exempt
- EG (Egypt): 14%, 0%, Exempt
- IN (India): 18%, 0%, Exempt (GST)

---

### 14. `ListTaxRates` (GET /finance/tax-rates/)

**Purpose:** Lists all tax rates

**Query Parameters:**
- `country`: Filter by country code
- `category`: Filter by category

**Response:**
```json
[
  {
    "id": 1,
    "country": "AE",
    "category": "STANDARD",
    "code": "VAT5",
    "name": "VAT 5%",
    "rate": "5.0",
    "effective_from": "2018-01-01",
    "effective_to": null
  }
]
```

---

### 15. `CorporateTaxAccrual` (POST /finance/corporate-tax/accrue/)

**Purpose:** Calculates and accrues corporate tax for period

**Request:**
```json
{
  "country": "AE",
  "date_from": "2025-01-01",
  "date_to": "2025-12-31",
  "organization_id": null
}
```

**Response:**
```json
{
  "filing_id": 1,
  "journal_id": 456,
  "meta": {
    "profit": 500000.00,
    "tax_base": 125000.00,
    "tax": 11250.00
  }
}
```

**Calculation:**
1. Sums income and expenses from posted journals
2. Calculates profit = income - expense
3. Applies threshold (e.g., UAE: first 375K exempt)
4. Calculates tax = tax_base × rate
5. Posts journal entry: DR Tax Expense, CR Tax Payable

---

### 16. `CorporateTaxFile` (POST /finance/corporate-tax/file/)

**Purpose:** Marks tax filing as officially filed (locks it)

**Request:**
```json
{
  "filing_id": 1
}
```

**Response:**
```json
{
  "message": "Corporate tax filing 1 marked as FILED",
  "status": "FILED",
  "filed_at": "2025-01-15T10:30:00Z"
}
```

**Effect:** Status changes ACCRUED → FILED (locked, cannot reverse)

---

### 17. `CorporateTaxReverse` (POST /finance/corporate-tax/reverse/)

**Purpose:** Reverses corporate tax accrual

**Request:**
```json
{
  "filing_id": 1
}
```

**Response:**
```json
{
  "message": "Corporate tax filing 1 reversed",
  "reversal_journal_id": 457,
  "status": "REVERSED"
}
```

**Validation:** Cannot reverse FILED status without override

---

### 18. `CorporateTaxFilingDetail` (GET /finance/corporate-tax/filings/{id}/)

**Purpose:** Retrieves corporate tax filing details

**Response:**
```json
{
  "id": 1,
  "country": "AE",
  "period_start": "2025-01-01",
  "period_end": "2025-12-31",
  "status": "ACCRUED",
  "accrual_journal_id": 456,
  "reversal_journal_id": null,
  "filed_at": null
}
```

---

### 19. `CorporateTaxBreakdown` (GET /finance/corporate-tax/breakdown/)

**Purpose:** Shows detailed breakdown of corporate tax calculation

**Query Parameters:**
- `country`: Country code
- `date_from`: Period start
- `date_to`: Period end
- `org_id`: Organization ID (optional)

**Response:**
```json
{
  "period": {
    "from": "2025-01-01",
    "to": "2025-12-31"
  },
  "rule": {
    "country": "AE",
    "rate": "9.0",
    "threshold": "375000.00"
  },
  "income_by_account": [
    {"code": "4000", "name": "Revenue", "amount": 1000000.00}
  ],
  "expense_by_account": [
    {"code": "5000", "name": "COGS", "amount": 400000.00},
    {"code": "6000", "name": "Operating Exp", "amount": 100000.00}
  ],
  "totals": {
    "total_income": 1000000.00,
    "total_expense": 500000.00,
    "profit": 500000.00,
    "threshold": 375000.00,
    "taxable_profit": 125000.00,
    "tax_rate": "9.0",
    "tax_amount": 11250.00
  }
}
```

---

## Legacy Invoice ViewSet

### 20. `InvoiceViewSet` (ViewSet)

**Base URL:** `/finance/invoices/`

**Purpose:** Original unified invoice model (before AR/AP split)

**Custom Actions:**
- `POST /{id}/post/` - Post invoice
- `POST /{id}/reverse/` - Reverse invoice

---

## Utility Endpoints

### 21. `GetCSRFToken` (GET /finance/csrf-token/)

**Purpose:** Retrieves CSRF token for frontend

**Response:**
```json
{
  "csrfToken": "xyz123abc..."
}
```

**Usage:** Frontend calls on app load to get token for POST requests

---

## Common Patterns

### 1. Creating Invoice with Items
```javascript
// POST /finance/ar-invoices/
{
  "customer": 1,
  "date": "2025-01-15",
  "due_date": "2025-02-15",
  "currency": 1,
  "items": [
    {
      "description": "Consulting Services",
      "quantity": "10",
      "unit_price": "100.00",
      "tax_rate": 1,
      "account": 5
    }
  ]
}
```

### 2. Posting Invoice Workflow
```javascript
// 1. Create invoice
const invoice = await api.post('/finance/ar-invoices/', invoiceData);

// 2. Review
console.log(invoice.total);  // Auto-calculated

// 3. Post to GL
const result = await api.post(`/finance/ar-invoices/${invoice.id}/post/`);

// 4. Create payment
const payment = await api.post('/finance/ar-payments/', {
  invoice: invoice.id,
  amount: "1050.00",
  date: "2025-01-20"
});

// 5. Post payment
await api.post(`/finance/ar-payments/${payment.id}/post/`);
```

### 3. Month-end Tax Accrual
```javascript
// 1. Accrue tax
const accrual = await api.post('/finance/corporate-tax/accrue/', {
  country: "AE",
  date_from: "2025-01-01",
  date_to: "2025-01-31"
});

// 2. Review breakdown
const breakdown = await api.get('/finance/corporate-tax/breakdown/', {
  params: {
    country: "AE",
    date_from: "2025-01-01",
    date_to: "2025-01-31"
  }
});

// 3. File officially
await api.post('/finance/corporate-tax/file/', {
  filing_id: accrual.filing_id
});
```

---

## Error Handling

**Standard DRF Error Format:**
```json
{
  "detail": "Error message here"
}
```

**Validation Errors:**
```json
{
  "field_name": ["Error message 1", "Error message 2"]
}
```

**Common HTTP Status Codes:**
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Validation error
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Pagination

**Default:** 100 items per page

**Query Parameters:**
- `page`: Page number
- `page_size`: Items per page (max 1000)

**Response:**
```json
{
  "count": 250,
  "next": "http://localhost:8000/finance/ar-invoices/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering & Ordering

**Filter by Field:**
```
GET /finance/ar-invoices/?status=POSTED
GET /finance/ar-invoices/?customer=1
```

**Date Range:**
```
GET /finance/ar-invoices/?date__gte=2025-01-01&date__lte=2025-01-31
```

**Ordering:**
```
GET /finance/ar-invoices/?ordering=-date  # Descending
GET /finance/ar-invoices/?ordering=number  # Ascending
```

---

## Best Practices

### 1. Use Transactions
All POST actions use `@transaction.atomic` - operations are all-or-nothing

### 2. Idempotency
Most POST actions are idempotent:
- Posting already-posted invoice returns existing journal
- Reversing already-reversed invoice returns existing reversal

### 3. Error Handling
```javascript
try {
  await api.post('/finance/ar-invoices/1/post/');
} catch (error) {
  if (error.response?.status === 400) {
    alert(`Validation error: ${error.response.data.detail}`);
  }
}
```

### 4. Computed Fields
Use serializer-provided totals, don't calculate in frontend:
```javascript
// ✅ DO
const total = invoice.total;  // From serializer

// ❌ DON'T
const total = invoice.items.reduce((sum, item) => sum + item.amount, 0);
```

---

## Conclusion

The Finance API provides:

✅ **Complete CRUD:** All finance entities (invoices, payments, accounts)  
✅ **Business Operations:** Post, reverse, accrue tax  
✅ **Reporting:** Trial balance, aging reports  
✅ **Multi-currency:** Exchange rates, conversions  
✅ **Tax Management:** VAT/GST seeding, corporate tax  
✅ **Export Formats:** JSON, CSV, Excel  
✅ **Validation:** Pre-operation checks  
✅ **Idempotency:** Safe repeated calls  
✅ **Transaction Safety:** Atomic operations  
✅ **Documentation:** OpenAPI/Swagger specs  

The API follows REST principles and Django REST Framework conventions, providing a clean interface for frontend applications and external integrations.

---

**Last Updated:** October 13, 2025  
**Framework:** Django REST Framework 3.x+  
**API Version:** 1.0  
**Documentation:** drf-spectacular (OpenAPI 3.0)

# Finance Module Documentation

## Overview
This directory contains comprehensive documentation for the Finance module of the ERP system. Each file is documented in detail with explanations of all classes, functions, and their purposes.

---

## Documentation Files

### [01_APPS.md](01_APPS.md) - Application Configuration
**File:** `finance/apps.py`

**Contents:**
- `FinanceConfig` class configuration
- Signal registration in `ready()` method
- App initialization process

**Key Topics:**
- Django app configuration
- Signal auto-loading
- App lifecycle

---

### [02_MODELS.md](02_MODELS.md) - Database Models
**File:** `finance/models.py`

**Contents:**
- **11 Model Classes:**
  1. `BankAccount` - Bank account information
  2. `Account` - Chart of Accounts (GL accounts)
  3. `JournalEntry` - General ledger entries
  4. `JournalLine` - Journal entry line items
  5. `CorporateTaxRule` - Tax rate rules by country
  6. `CorporateTaxFiling` - Tax filing records
  7. `InvoiceStatus` - Invoice status enum
  8. `LockOnPostedMixin` - Read-only enforcement
  9. `Invoice` - Unified invoice model
  10. `TaxCode` - Tax code definitions
  11. `InvoiceLine` - Invoice line items

**Key Topics:**
- Database schema
- Model relationships
- Historical records (audit trail)
- Field descriptions
- Model methods
- Common queries
- Best practices

---

### [03_SERIALIZERS.md](03_SERIALIZERS.md) - API Serialization
**File:** `finance/serializers.py`

**Contents:**
- **21 Serializer Classes:**
  - Currency, Account, BankAccount serializers
  - Journal entry serializers (read/write)
  - AR invoice/payment serializers
  - AP invoice/payment serializers
  - Invoice/InvoiceLine serializers
  - Exchange rate serializers
  - Tax-related serializers

**Key Topics:**
- Data validation
- Nested object creation
- Computed fields
- Totals caching
- Read-only serializers
- Business rule validation

---

### [04_SERVICES.md](04_SERVICES.md) - Business Logic
**File:** `finance/services.py`

**Contents:**
- **33+ Service Functions:**
  - **Reporting:** Trial balance, AR/AP aging
  - **Calculations:** Totals, tax, balances
  - **GL Posting:** AR/AP invoice posting, payment posting
  - **Tax:** VAT seeding, corporate tax accrual
  - **Reversals:** Journal and invoice reversals
  - **Validation:** Pre-posting checks

**Key Topics:**
- Business logic layer
- GL posting workflows
- Tax calculations
- Payment processing
- FX handling
- Idempotent operations
- Transaction safety

---

### [05_FX_SERVICES.md](05_FX_SERVICES.md) - Foreign Exchange
**File:** `finance/fx_services.py`

**Contents:**
- **8 FX Functions:**
  1. `get_base_currency()` - Base currency lookup
  2. `get_exchange_rate()` - Rate retrieval with fallbacks
  3. `convert_amount()` - Currency conversion
  4. `calculate_fx_gain_loss()` - Realized gain/loss
  5. `get_fx_account()` - FX GL account mapping
  6. `post_fx_gain_loss()` - FX journal posting
  7. `create_exchange_rate()` - Rate management
  8. `revalue_open_balances()` - Unrealized revaluation

**Key Topics:**
- Multi-currency support
- Exchange rate management
- Realized vs unrealized FX
- FX gain/loss accounting
- Period-end revaluation
- Rate lookup strategies

---

### [06_API.md](06_API.md) - REST API Endpoints
**File:** `finance/api.py`

**Contents:**
- **21 API Classes:**
  - **Reports:** Trial balance, AR/AP aging
  - **Invoices:** AR/AP invoice ViewSets
  - **Payments:** AR/AP payment ViewSets
  - **GL:** Journal entries, accounts
  - **Multi-currency:** Exchange rates, conversions
  - **Tax:** VAT seeding, corporate tax operations
  - **Banking:** Bank accounts
  - **Utilities:** CSRF token

**Key Topics:**
- REST API design
- ViewSets vs APIViews
- Custom actions (@action decorator)
- Export formats (JSON, CSV, Excel)
- Error handling
- Pagination & filtering
- OpenAPI documentation

---

### [07_SIGNALS.md](07_SIGNALS.md) - Django Signals
**File:** `finance/signals.py`

**Contents:**
- **3 Signal Handlers:**
  1. `validate_invoice_posting` - Pre-posting validation
  2. `block_edit_posted_invoice` - Read-only enforcement
  3. `block_edit_posted_invoice_lines` - Line protection

**Key Topics:**
- Signal-based validation
- Database-agnostic triggers
- Read-only invoice enforcement
- Pre-save hooks
- Business rule automation
- Status transition validation

---

## Quick Navigation

### By Use Case

**I want to understand...**

| Use Case | Read These Files |
|----------|-----------------|
| Database schema | 02_MODELS.md |
| API endpoints | 06_API.md |
| Business logic | 04_SERVICES.md |
| Data validation | 03_SERIALIZERS.md, 07_SIGNALS.md |
| Multi-currency | 05_FX_SERVICES.md |
| App setup | 01_APPS.md |

**I want to implement...**

| Feature | Read These Files |
|---------|-----------------|
| New invoice type | 02_MODELS.md, 03_SERIALIZERS.md, 06_API.md |
| GL posting | 04_SERVICES.md, 02_MODELS.md |
| Tax calculation | 04_SERVICES.md, 03_SERIALIZERS.md |
| Currency conversion | 05_FX_SERVICES.md, 03_SERIALIZERS.md |
| Report endpoint | 06_API.md, 04_SERVICES.md |
| Validation rule | 07_SIGNALS.md, 03_SERIALIZERS.md |

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│           Frontend (Next.js/React)          │
└────────────────┬────────────────────────────┘
                 │ HTTP Requests
┌────────────────▼────────────────────────────┐
│          06_API.md (api.py)                 │
│  REST Endpoints: ViewSets, APIViews         │
└────────────────┬────────────────────────────┘
                 │ Calls
┌────────────────▼────────────────────────────┐
│     03_SERIALIZERS.md (serializers.py)      │
│  Data Validation & Transformation           │
└────┬───────────────────────────────────┬────┘
     │ Validates                   Saves │
┌────▼────────────────┐    ┌─────────────▼────┐
│ 07_SIGNALS.md       │    │ 02_MODELS.md     │
│ (signals.py)        │◄───┤ (models.py)      │
│ Business Rules      │    │ Database Schema  │
└─────────────────────┘    └──────────────────┘
                                     │
                                     │ Persists
                                     ▼
                            ┌─────────────────┐
                            │    Database     │
                            │ (PostgreSQL)    │
                            └─────────────────┘
                 ▲
                 │ Calls
┌────────────────┴────────────────────────────┐
│        04_SERVICES.md (services.py)         │
│    Business Logic: Posting, Tax, Reports    │
└────────────────┬────────────────────────────┘
                 │ Uses
┌────────────────▼────────────────────────────┐
│     05_FX_SERVICES.md (fx_services.py)      │
│    Foreign Exchange Operations              │
└─────────────────────────────────────────────┘
```

---

## Module Initialization Flow

```
Django Startup
      │
      ▼
01_APPS.md: FinanceConfig.ready()
      │
      ├─ Import 07_SIGNALS.md (Register signal handlers)
      │
      ▼
Ready to serve requests
```

---

## Data Flow Examples

### Creating and Posting an Invoice

```
1. Frontend sends POST to API
      ↓
2. 06_API.md: ARInvoiceViewSet.create()
      ↓
3. 03_SERIALIZERS.md: ARInvoiceSerializer.validate()
      ↓
4. 03_SERIALIZERS.md: ARInvoiceSerializer.create()
      ↓
5. 02_MODELS.md: ARInvoice.save()
      ↓
6. Database: INSERT invoice + items
      
      
User clicks "Post" button
      ↓
7. Frontend sends POST to /ar-invoices/{id}/post/
      ↓
8. 06_API.md: ARInvoiceViewSet.post()
      ↓
9. 04_SERVICES.md: gl_post_from_ar_balanced()
      ↓
10. 07_SIGNALS.md: validate_invoice_posting() [pre_save]
      ↓
11. 02_MODELS.md: Create JournalEntry + JournalLines
      ↓
12. Database: INSERT journal entry
      ↓
13. Response: {"message": "Posted successfully"}
```

### Payment with FX

```
1. Create ARPayment in foreign currency
      ↓
2. 06_API.md: ARPaymentViewSet.post()
      ↓
3. 04_SERVICES.md: post_ar_payment()
      ↓
4. 05_FX_SERVICES.md: calculate_fx_gain_loss()
      ↓
5. 05_FX_SERVICES.md: post_fx_gain_loss()
      ↓
6. 02_MODELS.md: JournalEntry with FX lines
      ↓
7. Database: Journal with Bank, AR, and FX Gain/Loss lines
```

---

## Testing Guide

### Unit Tests
```python
# Test services (04_SERVICES.md)
from finance.services import ar_totals, gl_post_from_ar_balanced

# Test FX (05_FX_SERVICES.md)
from finance.fx_services import convert_amount, calculate_fx_gain_loss

# Test serializers (03_SERIALIZERS.md)
from finance.serializers import ARInvoiceSerializer
```

### Integration Tests
```python
# Test API endpoints (06_API.md)
from rest_framework.test import APIClient

client = APIClient()
response = client.post('/finance/ar-invoices/', data)
```

### Signal Tests
```python
# Test signals (07_SIGNALS.md)
from django.core.exceptions import ValidationError

invoice.status = InvoiceStatus.POSTED
with self.assertRaises(ValidationError):
    invoice.save()  # Should validate
```

---

## Dependencies

### Python Packages
```
django>=4.0
djangorestframework>=3.14
django-simple-history>=3.0
drf-spectacular>=0.26
openpyxl>=3.0  (optional, for Excel export)
```

### Django Apps
```
core  # Currency, TaxRate, ExchangeRate models
ar    # ARInvoice, ARPayment models
ap    # APInvoice, APPayment models
crm   # Customer, Supplier models
```

---

## Configuration

### Required Settings
```python
# settings.py

INSTALLED_APPS = [
    'finance',
    'core',
    'ar',
    'ap',
    # ...
]

# Optional: Override account codes
FINANCE_ACCOUNTS = {
    "BANK": "1010",
    "AR": "1200",
    "AP": "2100",
    # ... see 04_SERVICES.md for full list
}
```

---

## Common Tasks

### Add New Invoice Type
1. Create model in 02_MODELS.md pattern
2. Create serializers in 03_SERIALIZERS.md pattern
3. Add posting service in 04_SERVICES.md pattern
4. Create ViewSet in 06_API.md pattern
5. Add validation signal in 07_SIGNALS.md pattern

### Add New Report
1. Create service function in 04_SERVICES.md
2. Create APIView in 06_API.md
3. Add export formats (CSV, Excel)
4. Document query parameters

### Add FX Feature
1. Add function in 05_FX_SERVICES.md
2. Update payment posting in 04_SERVICES.md
3. Update serializers in 03_SERIALIZERS.md
4. Add API endpoint in 06_API.md

---

## Troubleshooting

### Issue: Posted invoice can be edited
**Check:** 07_SIGNALS.md - Are signals registered?  
**Fix:** Ensure `finance.apps.ready()` imports signals.py

### Issue: Totals don't match
**Check:** 03_SERIALIZERS.md - Is caching working?  
**Check:** 04_SERVICES.md - Are services calculating correctly?

### Issue: FX not working
**Check:** 05_FX_SERVICES.md - Is base currency set?  
**Check:** Exchange rates exist in database

### Issue: API errors
**Check:** 06_API.md - Correct HTTP method?  
**Check:** 03_SERIALIZERS.md - Validation rules

---

## Contributing

When updating this module:

1. ✅ Update relevant documentation file
2. ✅ Add docstrings to new functions/classes
3. ✅ Include code examples
4. ✅ Update this README if adding new files
5. ✅ Test all changes
6. ✅ Update "Last Updated" date in docs

---

## Support

For questions about:
- **Models:** See 02_MODELS.md
- **API usage:** See 06_API.md
- **Business logic:** See 04_SERVICES.md
- **Multi-currency:** See 05_FX_SERVICES.md
- **Validation:** See 03_SERIALIZERS.md, 07_SIGNALS.md

---

## Version History

| Date | Changes |
|------|---------|
| 2025-01-13 | Initial comprehensive documentation created |
| | All 7 module files documented in detail |
| | Added this README with navigation guide |

---

**Last Updated:** January 13, 2025  
**Django Version:** 4.x+  
**DRF Version:** 3.14+  
**Python Version:** 3.10+

---

## File Summary

| File | Lines | Classes/Functions | Purpose |
|------|-------|-------------------|---------|
| apps.py | 18 | 1 class | App configuration |
| models.py | 600+ | 11 models | Database schema |
| serializers.py | 446 | 21 serializers | API data layer |
| services.py | 789 | 33+ functions | Business logic |
| fx_services.py | 337 | 8 functions | Currency operations |
| api.py | 1156 | 21 ViewSets/Views | REST endpoints |
| signals.py | 165 | 3 handlers | Validation rules |

**Total:** ~3,500 lines of production code fully documented

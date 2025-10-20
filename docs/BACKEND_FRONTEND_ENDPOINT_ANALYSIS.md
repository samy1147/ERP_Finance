# Backend to Frontend Endpoint Usage Analysis

**Date:** October 14, 2025  
**Purpose:** Identify which backend API endpoints are used/unused in the frontend

---

## Summary

### ✅ Used Endpoints (19 endpoint groups)
- Accounts (CRUD + list)
- Journal Entries (CRUD + list + reverse action)
- AR Invoices (CRUD + list + post-gl + reverse actions)
- AR Payments (CRUD + list + post action)
- AP Invoices (CRUD + list + post-gl + reverse actions)
- AP Payments (CRUD + list + post action)
- Bank Accounts (CRUD + list)
- Customers (CRUD + list)
- Suppliers (CRUD + list)
- Currencies (CRUD + list)
- Tax Rates (list with country filter)
- Trial Balance Report (GET)
- AR Aging Report (GET)
- AP Aging Report (GET)
- CSRF Token (GET)

### ❌ Unused Endpoints (15+ endpoint groups)

---

## Detailed Analysis

### 1. ✅ **USED: Core Financial Endpoints**

#### Accounts - `/api/accounts/`
- **ViewSet:** `AccountViewSet` (ModelViewSet)
- **Frontend Usage:** `frontend/src/services/api.ts` → `accountsAPI`
  - ✅ list() - GET `/accounts/`
  - ✅ get(id) - GET `/accounts/{id}/`
  - ✅ create(data) - POST `/accounts/`
  - ✅ update(id, data) - PATCH `/accounts/{id}/`
  - ✅ delete(id) - DELETE `/accounts/{id}/`
- **Used In Pages:** `frontend/src/app/accounts/page.tsx`

#### Journal Entries - `/api/journals/`
- **ViewSet:** `JournalEntryViewSet` (ModelViewSet)
- **Frontend Usage:** `frontend/src/services/api.ts` → `journalEntriesAPI`
  - ✅ list() - GET `/journals/`
  - ✅ get(id) - GET `/journals/{id}/`
  - ✅ create(data) - POST `/journals/`
  - ✅ update(id, data) - PATCH `/journals/{id}/`
  - ✅ delete(id) - DELETE `/journals/{id}/`
  - ✅ reverse(id) - POST `/journals/{id}/reverse/`
- **Used In Pages:** `frontend/src/app/journals/page.tsx`
- **❌ UNUSED ACTIONS:**
  - POST `/journals/{id}/post/` - post_gl action
  - GET `/journals/export/` - export action (CSV/XLSX)

#### Currencies - `/api/currencies/`
- **ViewSet:** `CurrencyViewSet` (ModelViewSet)
- **Frontend Usage:** `frontend/src/services/api.ts` → `currenciesAPI`
  - ✅ list() - GET `/currencies/`
  - ✅ get(id) - GET `/currencies/{id}/`
  - ✅ create(data) - POST `/currencies/`
  - ✅ update(id, data) - PATCH `/currencies/{id}/`
  - ✅ delete(id) - DELETE `/currencies/{id}/`
- **Used In:**
  - `frontend/src/app/ar/invoices/new/page.tsx` (AR invoice creation - currency selector)
  - `frontend/src/app/ar/invoices/[id]/edit/page.tsx` (AR invoice editing)
  - `frontend/src/app/ap/invoices/new/page.tsx` (AP invoice creation - currency selector)
  - `frontend/src/app/ap/invoices/[id]/edit/page.tsx` (AP invoice editing)
  - `frontend/src/app/customers/page.tsx` (customer currency field)
  - `frontend/src/app/suppliers/page.tsx` (supplier currency field)
- **Features:**
  - Currency dropdown in invoice forms
  - Currency display in invoice details
  - Customer/Supplier default currency assignment
- **⚠️ PARTIAL IMPLEMENTATION:**
  - Currency is selected but NO dedicated currency management page
  - NO currency CRUD interface (create/edit/delete currencies)
  - Invoice forms show currency but hardcoded to ID-based selection

---

### 2. ✅ **USED: Accounts Receivable (AR) Endpoints**

#### AR Invoices - `/api/ar/invoices/`
- **ViewSet:** `ARInvoiceViewSet` (ModelViewSet)
- **Frontend Usage:** `frontend/src/services/api.ts` → `arInvoicesAPI`
  - ✅ list() - GET `/ar/invoices/`
  - ✅ get(id) - GET `/ar/invoices/{id}/`
  - ✅ create(data) - POST `/ar/invoices/`
  - ✅ update(id, data) - PATCH `/ar/invoices/{id}/`
  - ✅ delete(id) - DELETE `/ar/invoices/{id}/`
  - ✅ post(id) - POST `/ar/invoices/{id}/post-gl/`
  - ✅ reverse(id) - POST `/ar/invoices/{id}/reverse/`
- **Used In Pages:**
  - `frontend/src/app/ar/invoices/page.tsx` (list)
  - `frontend/src/app/ar/invoices/[id]/page.tsx` (detail)
  - `frontend/src/app/ar/invoices/[id]/edit/page.tsx` (edit)
  - `frontend/src/app/ar/invoices/new/page.tsx` (create)

#### AR Payments - `/api/ar/payments/`
- **ViewSet:** `ARPaymentViewSet` (ModelViewSet)
- **Frontend Usage:** `frontend/src/services/api.ts` → `arPaymentsAPI`
  - ✅ list() - GET `/ar/payments/`
  - ✅ get(id) - GET `/ar/payments/{id}/`
  - ✅ create(data) - POST `/ar/payments/`
  - ✅ update(id, data) - PATCH `/ar/payments/{id}/`
  - ✅ delete(id) - DELETE `/ar/payments/{id}/`
  - ✅ post(id) - POST `/ar/payments/{id}/post/`
- **Used In Pages:**
  - `frontend/src/app/ar/payments/page.tsx` (list)
  - `frontend/src/app/ar/payments/new/page.tsx` (create)

---

### 3. ✅ **USED: Accounts Payable (AP) Endpoints**

#### AP Invoices - `/api/ap/invoices/`
- **ViewSet:** `APInvoiceViewSet` (ModelViewSet)
- **Frontend Usage:** `frontend/src/services/api.ts` → `apInvoicesAPI`
  - ✅ list() - GET `/ap/invoices/`
  - ✅ get(id) - GET `/ap/invoices/{id}/`
  - ✅ create(data) - POST `/ap/invoices/`
  - ✅ update(id, data) - PATCH `/ap/invoices/{id}/`
  - ✅ delete(id) - DELETE `/ap/invoices/{id}/`
  - ✅ post(id) - POST `/ap/invoices/{id}/post-gl/`
  - ✅ reverse(id) - POST `/ap/invoices/{id}/reverse/`
- **Used In Pages:**
  - `frontend/src/app/ap/invoices/page.tsx` (list)
  - `frontend/src/app/ap/invoices/[id]/page.tsx` (detail)
  - `frontend/src/app/ap/invoices/[id]/edit/page.tsx` (edit)
  - `frontend/src/app/ap/invoices/new/page.tsx` (create)

#### AP Payments - `/api/ap/payments/`
- **ViewSet:** `APPaymentViewSet` (ModelViewSet)
- **Frontend Usage:** `frontend/src/services/api.ts` → `apPaymentsAPI`
  - ✅ list() - GET `/ap/payments/`
  - ✅ get(id) - GET `/ap/payments/{id}/`
  - ✅ create(data) - POST `/ap/payments/`
  - ✅ update(id, data) - PATCH `/ap/payments/{id}/`
  - ✅ delete(id) - DELETE `/ap/payments/{id}/`
  - ✅ post(id) - POST `/ap/payments/{id}/post/`
- **Used In Pages:**
  - `frontend/src/app/ap/payments/page.tsx` (list)
  - `frontend/src/app/ap/payments/new/page.tsx` (create)

---

### 4. ✅ **USED: CRM & Banking Endpoints**

#### Bank Accounts - `/api/bank-accounts/`
- **ViewSet:** `BankAccountViewSet` (ModelViewSet)
- **Frontend Usage:** `frontend/src/services/api.ts` → `bankAccountsAPI`
  - ✅ list() - GET `/bank-accounts/`
  - ✅ get(id) - GET `/bank-accounts/{id}/`
  - ✅ create(data) - POST `/bank-accounts/`
  - ✅ update(id, data) - PATCH `/bank-accounts/{id}/`
  - ✅ delete(id) - DELETE `/bank-accounts/{id}/`

#### Customers - `/api/customers/`
- **ViewSet:** `CustomerViewSet` (ModelViewSet) - from `crm/api.py`
- **Frontend Usage:** `frontend/src/services/api.ts` → `customersAPI`
  - ✅ list() - GET `/customers/`
  - ✅ get(id) - GET `/customers/{id}/`
  - ✅ create(data) - POST `/customers/`
  - ✅ update(id, data) - PATCH `/customers/{id}/`
  - ✅ delete(id) - DELETE `/customers/{id}/`
- **Used In Pages:** `frontend/src/app/customers/page.tsx`

#### Suppliers - `/api/suppliers/`
- **ViewSet:** `SupplierViewSet` (ModelViewSet) - from `crm/api.py`
- **Frontend Usage:** `frontend/src/services/api.ts` → `suppliersAPI`
  - ✅ list() - GET `/suppliers/`
  - ✅ get(id) - GET `/suppliers/{id}/`
  - ✅ create(data) - POST `/suppliers/`
  - ✅ update(id, data) - PATCH `/suppliers/{id}/`
  - ✅ delete(id) - DELETE `/suppliers/{id}/`
- **Used In Pages:** `frontend/src/app/suppliers/page.tsx`

---

### 5. ✅ **USED: Reports & Tax Endpoints**

#### Trial Balance Report - `/api/reports/trial-balance/`
- **View:** `TrialBalanceReport` (APIView)
- **Frontend Usage:** `frontend/src/services/api.ts` → `reportsAPI.trialBalance()`
  - ✅ GET with params: date_from, date_to, file_type (json/csv/xlsx)
- **Used In Pages:** `frontend/src/app/reports/page.tsx`

#### AR Aging Report - `/api/reports/ar-aging/`
- **View:** `ARAgingReport` (APIView)
- **Frontend Usage:** `frontend/src/services/api.ts` → `reportsAPI.arAging()`
  - ✅ GET with params: as_of, file_type (json/csv/xlsx)
- **Used In Pages:** `frontend/src/app/reports/page.tsx`

#### AP Aging Report - `/api/reports/ap-aging/`
- **View:** `APAgingReport` (APIView)
- **Frontend Usage:** `frontend/src/services/api.ts` → `reportsAPI.apAging()`
  - ✅ GET with params: as_of, file_type (json/csv/xlsx)
- **Used In Pages:** `frontend/src/app/reports/page.tsx`

#### Tax Rates - `/api/tax/rates/`
- **View:** `ListTaxRates` (APIView)
- **Frontend Usage:** `frontend/src/services/api.ts` → `taxRatesAPI.list()`
  - ✅ GET `/tax/rates/` with optional country filter
- **Used In:** 
  - `frontend/src/app/ar/invoices/new/page.tsx` (AR invoice creation)
  - `frontend/src/app/ar/invoices/[id]/edit/page.tsx` (AR invoice editing)
  - `frontend/src/app/ap/invoices/new/page.tsx` (AP invoice creation)
  - `frontend/src/app/ap/invoices/[id]/edit/page.tsx` (AP invoice editing)
- **Features:**
  - Tax rate dropdown in invoice line items
  - Country-based tax rate filtering (auto-loads tax rates based on customer/supplier country)
  - Automatic tax calculation in frontend

#### CSRF Token - `/api/csrf/`
- **View:** `GetCSRFToken` (APIView)
- **Frontend Usage:** `frontend/src/lib/api.ts`
  - ✅ GET `/csrf/` - Called in CSRFInitializer

---

### 6. ❌ **UNUSED: Corporate Tax Management Endpoints**

All corporate tax **management** endpoints are **NOT used** in the frontend:

**Note:** Basic VAT/GST tax rates ARE used (see Tax Rates section above), but corporate income tax features are not.

#### Seed VAT Presets - `/api/tax/seed-presets/`
- **View:** `SeedVATPresets` (APIView)
- **Method:** POST
- **Purpose:** Seed default VAT tax rates
- ❌ **NOT IMPLEMENTED IN FRONTEND**

#### Corporate Tax Accrual - `/api/tax/corporate-accrual/`
- **View:** `CorporateTaxAccrual` (APIView)
- **Method:** POST
- **Purpose:** Create corporate tax accrual journal entry
- ❌ **NOT IMPLEMENTED IN FRONTEND**

#### Corporate Tax File - `/api/tax/corporate-file/{filing_id}/`
- **View:** `CorporateTaxFile` (APIView)
- **Methods:** GET, POST
- **Purpose:** Get or file corporate tax
- ❌ **NOT IMPLEMENTED IN FRONTEND**

#### Corporate Tax Filing Detail - `/api/tax/corporate-filing/{filing_id}/`
- **View:** `CorporateTaxFilingDetail` (APIView)
- **Method:** GET
- **Purpose:** Get corporate tax filing details
- ❌ **NOT IMPLEMENTED IN FRONTEND**

#### Corporate Tax Reverse - `/api/tax/corporate-reverse/{filing_id}/`
- **View:** `CorporateTaxReverse` (APIView)
- **Methods:** GET, POST
- **Purpose:** Preview or reverse corporate tax filing
- ❌ **NOT IMPLEMENTED IN FRONTEND**

#### Corporate Tax Breakdown - `/api/tax/corporate-breakdown/`
- **View:** `CorporateTaxBreakdown` (APIView)
- **Method:** GET
- **Purpose:** Get corporate tax breakdown by period
- ❌ **NOT IMPLEMENTED IN FRONTEND**

---

### 7. ❌ **UNUSED: Foreign Exchange (FX) Management Endpoints**

All FX **management** endpoints are **NOT used** in the frontend:

**Note:** Basic currency selection IS used in invoices, but advanced FX features (rates, conversion, gain/loss) are not.

#### Exchange Rates - `/api/fx/rates/`
- **ViewSet:** `ExchangeRateViewSet` (ModelViewSet)
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Query Params:** from_currency, to_currency, rate_type, date_from, date_to
- ❌ **NOT IMPLEMENTED IN FRONTEND**

#### Currency Convert - `/api/fx/convert/`
- **View:** `CurrencyConvertView` (APIView)
- **Method:** POST
- **Purpose:** Convert amount between currencies
- **Request Body:** amount, from_currency_code, to_currency_code, rate_date, rate_type
- ❌ **NOT IMPLEMENTED IN FRONTEND**

#### Create Exchange Rate - `/api/fx/create-rate/`
- **View:** `CreateExchangeRateView` (APIView)
- **Method:** POST
- **Purpose:** Create or update exchange rate using currency codes
- **Request Body:** from_currency_code, to_currency_code, rate, rate_date, rate_type, source
- ❌ **NOT IMPLEMENTED IN FRONTEND**

#### FX Gain/Loss Accounts - `/api/fx/accounts/`
- **ViewSet:** `FXGainLossAccountViewSet` (ModelViewSet)
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Purpose:** Manage FX gain/loss account configurations
- ❌ **NOT IMPLEMENTED IN FRONTEND**

#### Base Currency - `/api/fx/base-currency/`
- **View:** `BaseCurrencyView` (APIView)
- **Method:** GET
- **Purpose:** Get the base/home currency for the company
- ❌ **NOT IMPLEMENTED IN FRONTEND**

---

### 8. ❌ **UNUSED: Documentation Endpoints**

#### OpenAPI Schema - `/api/schema/`
- **View:** `SpectacularAPIView`
- **Purpose:** OpenAPI schema generation
- ❌ **NOT USED IN FRONTEND** (development/documentation only)

#### Swagger UI - `/api/docs/`
- **View:** `SpectacularSwaggerView`
- **Purpose:** Interactive API documentation
- ❌ **NOT USED IN FRONTEND** (development/documentation only)

#### ReDoc - `/api/redoc/`
- **View:** `SpectacularRedocView`
- **Purpose:** Alternative API documentation UI
- ❌ **NOT USED IN FRONTEND** (development/documentation only)

---

### 9. ❌ **UNUSED: Legacy/Deprecated Endpoints**

#### Invoice (Generic) - No route registered
- **ViewSet:** `InvoiceViewSet` (ModelViewSet)
- **Note:** This appears to be a legacy/deprecated endpoint as it's not registered in `urls.py`
- **Actions:** post, reverse
- ❌ **NOT REGISTERED IN URLS**

---

## Recommendations

### High Priority - Missing FX Functionality
Consider implementing these FX features in the frontend:

1. **Exchange Rate Management UI**
   - View/list exchange rates with filters
   - Create/update exchange rates manually
   - Bulk import rates from external sources

2. **Currency Conversion Tool**
   - Currency converter widget
   - Real-time conversion calculator
   - Integration into invoice/payment forms

3. **FX Gain/Loss Configuration**
   - Configure FX gain/loss accounts
   - View FX impact on transactions

4. **Base Currency Display**
   - Show base currency in header/settings
   - Allow base currency configuration

### Medium Priority - Corporate Tax Features
Implement corporate tax management UI:

1. **Tax Period Management**
   - Create tax periods/filings
   - View tax breakdown by period
   - Tax accrual functionality

2. **Tax Filing Workflow**
   - File corporate tax
   - View filing details
   - Reverse filings if needed

3. **Tax Preset Management**
   - Seed default VAT rates
   - Manage tax presets by country

### Low Priority - Enhanced Features

1. **Journal Export**
   - Add export button to journals page
   - Implement CSV/XLSX download from `/journals/export/`

2. **Journal Posting**
   - Add "Post to GL" action for individual journals
   - Currently, only creation is supported

---

## Statistics

### Coverage Summary
- **Total Backend Endpoint Groups:** ~35
- **Used in Frontend:** ~19 (54%)
- **Partially Used:** ~2 (6%) - Currencies and Tax Rates (used in forms but no management UI)
- **Unused in Frontend:** ~14 (40%)

### By Category:
| Category | Used | Unused | Coverage |
|----------|------|--------|----------|
| Core Financial (Accounts, Journals, Currencies) | 3 | 0 | 100% |
| AR (Invoices, Payments) | 2 | 0 | 100% |
| AP (Invoices, Payments) | 2 | 0 | 100% |
| CRM (Customers, Suppliers) | 2 | 0 | 100% |
| Banking | 1 | 0 | 100% |
| Reports | 3 | 0 | 100% |
| Tax (VAT/GST Rates) | 1 | 0 | 100% *(used in forms only)* |
| Currency (Basic) | 1 | 0 | 100% *(used in forms only)* |
| **Currency Management** | **0** | **1** | **0%** *(no CRUD UI)* |
| **Tax (Corporate Income)** | **0** | **6** | **0%** |
| **Foreign Exchange (FX)** | **0** | **5** | **0%** |
| Documentation | 0 | 3 | N/A |
| CSRF/Auth | 1 | 0 | 100% |

### Key Gaps:
1. **No FX/Currency Management UI** - 5 endpoints unused
2. **No Corporate Tax Management UI** - 6 endpoints unused
3. **Limited Journal Actions** - 2 journal actions unused (post, export)

---

## ⚠️ IMPORTANT CLARIFICATION: What IS vs ISN'T Implemented

### ✅ **WHAT IS IMPLEMENTED (Basic Usage)**

#### **1. Currency Usage in Invoices**
- **Where:** AR/AP Invoice creation and editing forms
- **What Works:**
  - Dropdown to select currency for each invoice
  - Currency is stored with invoice
  - Currency code displayed on invoice detail pages
  - Customer/Supplier can have default currency
- **TypeScript Interface:** `Currency` type exists in `frontend/src/types/index.ts`
- **API Calls:** `currenciesAPI.list()` fetches currencies for dropdowns

#### **2. Tax Rate Usage in Invoices**
- **Where:** AR/AP Invoice line items
- **What Works:**
  - Tax rate dropdown for each invoice line item
  - **Smart country-based filtering:** When you select a customer/supplier, their country automatically filters the tax rates
  - Tax amount calculated automatically in frontend
  - Tax rates fetched from backend: `/api/tax/rates/?country=AE`
  - Displays tax rate name and percentage (e.g., "UAE VAT Standard (5%)")
- **TypeScript Interface:** `TaxRate` type exists in `frontend/src/types/index.ts`
- **API Calls:** `taxRatesAPI.list(country)` with country filter

**Example Workflow (Current):**
```
1. User creates AR Invoice
2. Selects Customer (e.g., "ABC Corp - UAE")
3. System auto-sets country = "AE"
4. Tax rate dropdown shows only UAE rates: VAT 5%, Zero-rated 0%, etc.
5. User selects "UAE VAT Standard (5%)"
6. Invoice line calculates: subtotal × 5% = tax amount
```

### ❌ **WHAT IS NOT IMPLEMENTED (Management)**

#### **1. Currency Management Pages**
- ❌ No `/currencies` page to list all currencies
- ❌ No "Add Currency" button/form
- ❌ No "Edit Currency" functionality
- ❌ No "Delete Currency" option
- ❌ Cannot set which currency is base/home currency
- ❌ Cannot see currency symbol or full name in a table

**Current Workaround:** Currencies must be added via Django admin or API directly

#### **2. Tax Rate Management Pages**
- ❌ No `/tax-rates` page to list all tax rates
- ❌ No "Add Tax Rate" button/form
- ❌ No "Edit Tax Rate" functionality
- ❌ No "Delete Tax Rate" option
- ❌ Cannot see all tax rates by country in a table
- ❌ Cannot manage effective dates (effective_from, effective_to)
- ❌ No "Seed VAT Presets" button in UI

**Current Workaround:** Tax rates must be added via:
- Django admin
- API endpoint: `POST /api/tax/seed-presets/` (not in frontend)
- Direct API calls

#### **3. Exchange Rate Management (Complete Gap)**
- ❌ No exchange rate functionality AT ALL in frontend
- ❌ Invoices don't convert between currencies
- ❌ No exchange rate entry
- ❌ No FX gain/loss tracking
- ❌ No currency conversion calculator
- ❌ Backend supports all of this, but zero frontend

**Current Limitation:** If you invoice in USD but your base currency is AED:
- Invoice stores USD amount
- Backend CAN convert (has exchange rates table)
- Frontend DOESN'T trigger conversion
- No automatic FX gain/loss on payments

#### **4. Corporate Tax Accrual (Complete Gap)**
- ❌ No corporate tax management AT ALL in frontend
- ❌ Cannot accrue quarterly/annual tax
- ❌ Cannot view tax filings
- ❌ Cannot file or reverse tax
- ❌ Backend has complete workflow, but zero frontend

---

## Next Steps

1. **Decide on FX Feature Scope**
   - Is multi-currency a priority feature?
   - If yes, implement FX management pages
   - If no, consider removing/deprecating FX endpoints

2. **Corporate Tax Implementation**
   - Assess if corporate tax features are needed
   - Design tax filing workflow UI
   - Implement step-by-step

3. **Enhance Existing Pages**
   - Add export functionality to journals page
   - Add journal posting action

4. **Clean Up Backend**
   - Remove unused `InvoiceViewSet` if truly deprecated
   - Document which endpoints are intentionally unused

---

## Files Referenced

**Backend:**
- `erp/urls.py` - URL routing configuration
- `finance/api.py` - Main API views and viewsets
- `crm/api.py` - CRM viewsets (Customer, Supplier)

**Frontend:**
- `frontend/src/services/api.ts` - API wrapper functions
- `frontend/src/lib/api.ts` - Base API client with CSRF
- `frontend/src/app/**/page.tsx` - Various page components using APIs

---

**End of Analysis**

# Invoice Country and Tax Rate Integration

## Overview
Added country field to AR and AP invoices to enable proper tax rate filtering and compliance with country-specific tax regulations.

## Changes Made

### Backend Changes

#### 1. Models (ar/models.py, ap/models.py)

**ARInvoice Model:**
```python
country = models.CharField(
    max_length=2, 
    choices=TAX_COUNTRIES, 
    default="AE",
    help_text="Tax country for this invoice (defaults to customer country)"
)
```

**APInvoice Model:**
```python
country = models.CharField(
    max_length=2, 
    choices=TAX_COUNTRIES, 
    default="AE",
    help_text="Tax country for this invoice (defaults to supplier country)"
)
```

**Auto-Population Logic:**
- Country automatically defaults to customer/supplier country when invoice is created
- Can be manually overridden if needed (e.g., for cross-border transactions)
- Implemented in `save()` method

#### 2. Admin Interfaces (ar/admin.py, ap/admin.py)

**Updated:**
- Added `country` to `list_display` - visible in invoice list
- Added `country` to `list_filter` - filterable by country
- Added `country` field to "Invoice Information" fieldset

#### 3. Serializers (finance/serializers.py)

**ARInvoiceSerializer & APInvoiceSerializer:**
- Added `country` to fields list
- Exposed in API responses
- Can be set when creating invoices via API

#### 4. Migrations

✅ Created and applied:
- `ar/migrations/0006_arinvoice_country.py`
- `ap/migrations/0006_apinvoice_country.py`

### Frontend Changes

#### 1. TypeScript Types (frontend/src/types/index.ts)

**Added to ARInvoice and APInvoice:**
```typescript
country: string; // Tax country for the invoice
```

**New TaxRate Interface:**
```typescript
export interface TaxRate {
  id: number;
  name: string;
  rate: number;
  country: string;
  category: 'STANDARD' | 'ZERO' | 'EXEMPT' | 'RC';
  code?: string;
  effective_from?: string;
  is_active: boolean;
}
```

## Tax Rate API

### Existing Endpoint
The system already has a tax rates API that supports country filtering:

**Endpoint:** `GET /api/tax/rates/`

**Query Parameters:**
- `country` (optional) - Filter by country code (e.g., `AE`, `SA`, `EG`, `IN`)

**Example Requests:**
```bash
# Get all tax rates
GET /api/tax/rates/

# Get tax rates for UAE only
GET /api/tax/rates/?country=AE

# Get tax rates for Saudi Arabia
GET /api/tax/rates/?country=SA
```

**Response Format:**
```json
[
  {
    "id": 1,
    "name": "UAE VAT Standard",
    "rate": 5.0,
    "country": "AE",
    "category": "STANDARD",
    "code": "VAT5",
    "effective_from": "2018-01-01"
  },
  {
    "id": 2,
    "name": "Saudi VAT",
    "rate": 15.0,
    "country": "SA",
    "category": "STANDARD",
    "code": "VAT15",
    "effective_from": "2020-07-01"
  }
]
```

## Country Codes

Supported countries:
- `AE` - United Arab Emirates (UAE)
- `SA` - Saudi Arabia (KSA)
- `EG` - Egypt
- `IN` - India

## Tax Categories

- `STANDARD` - Standard tax rate
- `ZERO` - Zero-rated (0% but with input tax credit)
- `EXEMPT` - Exempt (no tax and no input tax credit)
- `RC` - Reverse Charge (customer pays tax)

## Usage Examples

### Creating an Invoice with Auto Country

```python
# Backend - Country auto-populated from customer
customer = Customer.objects.get(code='C001')  # country='AE'
invoice = ARInvoice.objects.create(
    customer=customer,
    number='INV-001',
    date=date.today(),
    due_date=date.today() + timedelta(days=30),
    currency=Currency.objects.get(code='AED'),
    # country will automatically be set to 'AE'
)
```

### Creating an Invoice with Manual Country Override

```python
# Backend - Manual country override
invoice = ARInvoice.objects.create(
    customer=customer,  # country='AE'
    number='INV-002',
    date=date.today(),
    due_date=date.today() + timedelta(days=30),
    currency=Currency.objects.get(code='SAR'),
    country='SA',  # Override to Saudi Arabia
)
```

### Frontend - Fetching Tax Rates for Invoice Country

```typescript
// Fetch tax rates based on invoice country
const response = await fetch(`/api/tax/rates/?country=${invoice.country}`);
const taxRates = await response.json();

// Display tax rates in dropdown
taxRates.forEach(rate => {
  console.log(`${rate.name}: ${rate.rate}%`);
});
```

### Admin Interface - Filtering Invoices by Country

1. Go to Admin → AR Invoices or AP Invoices
2. Use the "Country" filter in the right sidebar
3. Select desired country (UAE, KSA, Egypt, India)
4. View invoices for that country only

### Querying Invoices by Country

```python
# Get all UAE invoices
uae_invoices = ARInvoice.objects.filter(country='AE')

# Get Saudi invoices from last month
from django.utils import timezone
from datetime import timedelta

last_month = timezone.now().date() - timedelta(days=30)
saudi_invoices = APInvoice.objects.filter(
    country='SA',
    date__gte=last_month
)

# Get invoices by country and status
posted_uae_invoices = ARInvoice.objects.filter(
    country='AE',
    is_posted=True,
    is_cancelled=False
)
```

## Benefits

1. **Tax Compliance:** Each invoice is associated with the correct tax jurisdiction
2. **Accurate Tax Rates:** Line items can use tax rates specific to the invoice country
3. **Better Reporting:** Easy to generate country-specific reports
4. **Multi-Country Support:** System can handle invoices from different countries simultaneously
5. **Audit Trail:** Clear record of which tax jurisdiction applies to each invoice

## Frontend Integration Guide

### Step 1: Load Customer/Supplier and Set Country

```typescript
// When customer/supplier is selected
const customer = await fetchCustomer(customerId);
setFormData({
  ...formData,
  country: customer.country, // Auto-set from customer
});
```

### Step 2: Load Tax Rates for Country

```typescript
// Load tax rates when country changes
useEffect(() => {
  if (formData.country) {
    fetch(`/api/tax/rates/?country=${formData.country}`)
      .then(res => res.json())
      .then(rates => setAvailableTaxRates(rates));
  }
}, [formData.country]);
```

### Step 3: Display Tax Rate Options

```typescript
// In invoice line item form
<select name="tax_rate">
  <option value="">No Tax</option>
  {availableTaxRates.map(rate => (
    <option key={rate.id} value={rate.id}>
      {rate.name} ({rate.rate}%) - {rate.category}
    </option>
  ))}
</select>
```

## Database Schema

### ARInvoice / APInvoice Table
```sql
-- New column added
ALTER TABLE ar_arinvoice ADD COLUMN country VARCHAR(2) DEFAULT 'AE';
ALTER TABLE ap_apinvoice ADD COLUMN country VARCHAR(2) DEFAULT 'AE';
```

### Indexes
The country field can be indexed for better query performance:
```sql
CREATE INDEX idx_ar_invoice_country ON ar_arinvoice(country);
CREATE INDEX idx_ap_invoice_country ON ap_apinvoice(country);
```

## Testing Checklist

- [x] Create invoice - country auto-populated from customer/supplier
- [x] Create invoice with manual country override
- [x] Admin interface shows country field
- [x] Admin interface filters by country
- [x] API returns country in invoice serialization
- [x] Tax rates API filters by country
- [ ] Frontend displays country field in invoice form
- [ ] Frontend loads appropriate tax rates based on country
- [ ] Posting invoices works with country field
- [ ] Reports group by country correctly

## Next Steps

1. **Update Frontend Forms:**
   - Add country field to invoice creation forms
   - Add country dropdown (auto-populated from customer/supplier)
   - Load tax rates dynamically based on selected country

2. **Enhance Tax Rate Selection:**
   - Filter tax rate dropdowns in line items by invoice country
   - Show only active tax rates
   - Display effective date information

3. **Reporting:**
   - Add country breakdown to AR/AP aging reports
   - Create country-specific VAT reports
   - Add country filter to financial reports

4. **Validation:**
   - Add validation to ensure tax rates match invoice country
   - Warn if currency doesn't match typical country currency
   - Validate VAT numbers against country format

## Migration Notes

- Existing invoices will default to `AE` (UAE)
- To update existing invoices based on customer/supplier country:

```python
# Run this in Django shell
from ar.models import ARInvoice
from ap.models import APInvoice

# Update AR invoices
for invoice in ARInvoice.objects.filter(country='AE'):
    if invoice.customer.country != 'AE':
        invoice.country = invoice.customer.country
        invoice.save(update_fields=['country'])

# Update AP invoices
for invoice in APInvoice.objects.filter(country='AE'):
    if invoice.supplier.country != 'AE':
        invoice.country = invoice.supplier.country
        invoice.save(update_fields=['country'])
```

## Documentation Updated

- [x] Backend models documentation
- [x] API endpoint documentation
- [x] Frontend types documentation
- [x] Usage examples
- [ ] User manual (if exists)
- [ ] API documentation (Swagger/OpenAPI)

---

**Status:** ✅ Backend Complete - Frontend Integration Pending
**Date:** October 14, 2025
**Files Modified:** 8 files (5 backend, 2 frontend, 1 documentation)

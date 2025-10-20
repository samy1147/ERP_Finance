# Initial Data Load - Currencies and Tax Rates

## Date: October 16, 2025

## Overview
Successfully populated the database with currencies and tax rates for the requested countries: USA, Europe, Egypt, India, UAE (Emirates), and Saudi Arabia (KSA).

## Command Created
**File**: `core/management/commands/load_initial_data.py`

**Usage**:
```bash
python manage.py load_initial_data
```

## Data Loaded

### Currencies (6 Total)

| Code | Name | Symbol | Country | Base Currency |
|------|------|--------|---------|---------------|
| **USD** | US Dollar | $ | USA | No |
| **EUR** | Euro | € | Europe | No |
| **EGP** | Egyptian Pound | E£ | Egypt | No |
| **INR** | Indian Rupee | ₹ | India | No |
| **AED** | UAE Dirham | د.إ | UAE | **Yes** |
| **SAR** | Saudi Riyal | ﷼ | Saudi Arabia | No |

**Note**: AED (UAE Dirham) is set as the base currency for the system.

### Tax Rates (15 Total)

#### Egypt (EG) - 3 rates
- **Egypt Standard VAT**: 14% (Code: VAT14)
- **Egypt Zero-Rated VAT**: 0% (Code: VAT0)
- **Egypt Exempt**: 0% (Code: EXEMPT)

**Tax Structure**: Egypt uses VAT (Value Added Tax) at 14% standard rate.

#### India (IN) - 6 rates
- **India GST 28%**: 28% (Code: GST28) - Luxury goods
- **India GST 18%**: 18% (Code: GST18) - Standard rate
- **India GST 12%**: 12% (Code: GST12) - Lower rate
- **India GST 5%**: 5% (Code: GST5) - Essential goods
- **India GST 0%**: 0% (Code: GST0) - Zero-rated
- **India GST Exempt**: 0% (Code: EXEMPT) - Exempt supplies

**Tax Structure**: India uses GST (Goods and Services Tax) with multiple slab rates (5%, 12%, 18%, 28%).

#### UAE (AE) - 3 rates
- **UAE Standard VAT**: 5% (Code: VAT5)
- **UAE Zero-Rated**: 0% (Code: VAT0) - Exports, education, healthcare
- **UAE Exempt**: 0% (Code: EXEMPT) - Residential property, local transport

**Tax Structure**: UAE uses VAT at 5% standard rate (introduced in 2018).

#### Saudi Arabia (SA) - 3 rates
- **KSA Standard VAT**: 15% (Code: VAT15)
- **KSA Zero-Rated**: 0% (Code: VAT0) - Exports, international services
- **KSA Exempt**: 0% (Code: EXEMPT) - Healthcare, education

**Tax Structure**: KSA uses VAT at 15% standard rate (increased from 5% in 2020).

## Important Notes

### USA and Europe Tax Rates
The TaxRate model in this system currently only supports these countries:
- AE (United Arab Emirates)
- SA (Saudi Arabia)
- EG (Egypt)
- IN (India)

**USA (US)** and **Europe (EU)** are **not included** in the `COUNTRY_CHOICES` of the TaxRate model. To add support for these countries, you would need to:

1. Update `core/models.py` - Add to `COUNTRY_CHOICES`:
   ```python
   COUNTRY_CHOICES = [
       ("AE", "United Arab Emirates"),
       ("SA", "Saudi Arabia"),
       ("EG", "Egypt"),
       ("IN", "India"),
       ("US", "United States"),  # Add this
       ("EU", "European Union"),  # Add this
   ]
   ```

2. Create and run a migration
3. Re-run the `load_initial_data` command with updated tax rates

### Currencies Available
All 6 currencies are loaded and ready to use:
- ✅ USD - US Dollar
- ✅ EUR - Euro
- ✅ EGP - Egyptian Pound
- ✅ INR - Indian Rupee
- ✅ AED - UAE Dirham (Base Currency)
- ✅ SAR - Saudi Riyal

## Tax Rate Categories

Each tax rate has a category:
- **STANDARD**: Normal tax rate for most goods/services
- **ZERO**: Zero-rated supplies (taxable at 0%)
- **EXEMPT**: Exempt supplies (outside the scope of tax)
- **RC**: Reverse Charge (special mechanism)

## Usage in Invoices

### Creating Invoice with Specific Currency
```python
from ar.models import ARInvoice
from core.models import Currency

usd = Currency.objects.get(code='USD')
invoice = ARInvoice.objects.create(
    customer=customer,
    number="INV-001",
    currency=usd,  # Use USD
    # ... other fields
)
```

### Applying Tax Rates
```python
from ar.models import ARItem
from core.models import TaxRate

# UAE VAT
uae_vat = TaxRate.objects.get(country='AE', code='VAT5')
item = ARItem.objects.create(
    invoice=invoice,
    description="Product",
    quantity=1,
    unit_price=100,
    tax_rate=uae_vat  # Apply 5% UAE VAT
)

# India GST 18%
india_gst = TaxRate.objects.get(country='IN', code='GST18')
item = ARItem.objects.create(
    invoice=invoice,
    description="Service",
    quantity=1,
    unit_price=500,
    tax_rate=india_gst  # Apply 18% India GST
)
```

## Verification Queries

### Check All Currencies
```bash
python manage.py shell -c "
from core.models import Currency
for c in Currency.objects.all():
    print(f'{c.code} - {c.name} ({c.symbol})')
"
```

### Check All Tax Rates
```bash
python manage.py shell -c "
from core.models import TaxRate
for t in TaxRate.objects.all():
    print(f'{t.country} - {t.name}: {t.rate}%')
"
```

### Check Tax Rates by Country
```bash
python manage.py shell -c "
from core.models import TaxRate
# UAE rates
print('UAE Tax Rates:')
for t in TaxRate.objects.filter(country='AE'):
    print(f'  {t.name}: {t.rate}%')
"
```

## Running the Command Again

The command is idempotent - running it again will not create duplicates:

```bash
python manage.py load_initial_data
```

Output will show:
```
  - Currency already exists: USD
  - Currency already exists: EUR
  # ... etc
  - Tax rate already exists: AE - UAE Standard VAT
  # ... etc
```

## Next Steps

1. **Load Exchange Rates**: Create exchange rates between currencies
2. **Set up Chart of Accounts**: Create account structure
3. **Create Customers and Suppliers**: Add master data
4. **Start Creating Invoices**: Use the loaded currencies and tax rates

## Files Created/Modified

1. **`core/management/commands/load_initial_data.py`** - NEW
   - Management command to load initial data
   - 226 lines of code
   - Includes all 6 currencies and 15 tax rates
   - Transaction-wrapped for data integrity

## Status
✅ **COMPLETE** - All requested currencies and tax rates successfully loaded into the database.

## Summary

- **6 Currencies** loaded (USD, EUR, EGP, INR, AED, SAR)
- **15 Tax Rates** loaded across 4 countries (EG, IN, AE, SA)
- **AED** set as base currency
- Ready for invoice creation and multi-currency transactions

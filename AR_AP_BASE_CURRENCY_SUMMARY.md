# AR/AP Base Currency Display - Quick Summary

## What Was Done

Added exchange rate and base currency total columns to AR and AP invoice lists for better multi-currency visibility.

## Changes Made

### ✅ Backend (Serializers)
**File**: `finance/serializers.py`

Added to both ARInvoiceSerializer and APInvoiceSerializer:
- `currency_code` - Shows currency code (USD, AED, etc.)
- `exchange_rate` - Exchange rate used when posting
- `base_currency_total` - Amount in base currency

### ✅ Frontend (Invoice Lists)
**Files**:
- `frontend/src/app/ar/invoices/page.tsx`
- `frontend/src/app/ap/invoices/page.tsx`

Added new columns to tables:
1. **Currency** - Currency code (e.g., USD, AED)
2. **Total** - Amount in invoice currency
3. **Rate** - Exchange rate (4 decimals)
4. **Base Total** - Converted amount in base currency (formatted with commas)

## New Table Layout

| Invoice # | Customer | Date | Currency | Total | Rate | **Base Total** | Balance | Status |
|-----------|----------|------|----------|-------|------|---------------|---------|--------|
| INV-001 | ACME | Jan 1 | USD | USD 1,000 | 3.6725 | **3,672.50** | 0.00 | Posted |
| INV-002 | XYZ | Jan 2 | AED | AED 5,000 | 1.0000 | **5,000.00** | 2,500 | Posted |

## How to Test

1. **Refresh browser** (if servers are running)
2. Go to **AR Invoices** or **AP Invoices**
3. You should see new columns:
   - Currency code
   - Exchange rate (only for posted invoices)
   - Base Total (only for posted invoices)

## Notes

- ✅ Exchange rate only shown for **posted** invoices
- ✅ Base total only shown for **posted** invoices  
- ✅ Unposted invoices show "—" for rate and base total
- ✅ Numbers are formatted with commas (e.g., 1,234.56)
- ✅ Models already had the fields (no migration needed)

## Benefits

✅ **Multi-currency visibility** - See both original and base amounts  
✅ **Exchange rate transparency** - Know the rate used for conversion  
✅ **Better reporting** - Easy to sum totals in base currency  
✅ **Audit trail** - Historical rates are preserved  

## Files Modified

- `finance/serializers.py` (ARInvoiceSerializer, APInvoiceSerializer)
- `frontend/src/app/ar/invoices/page.tsx`
- `frontend/src/app/ap/invoices/page.tsx`

## Documentation

Full details: `docs/AR_AP_BASE_CURRENCY_DISPLAY.md`

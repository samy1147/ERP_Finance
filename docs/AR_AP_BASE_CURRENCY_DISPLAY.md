# AR/AP Base Currency Total - Implementation Summary

## Date: October 17, 2025

## Overview
Added base currency total display to AR and AP invoice lists, showing the exchange rate and converted amount for multi-currency invoices.

## What Was Added

### Backend Changes

#### 1. AR/AP Models (Already Existed)
Both `ARInvoice` and `APInvoice` models already have these fields:
```python
exchange_rate = models.DecimalField(
    max_digits=18, 
    decimal_places=6, 
    null=True, 
    blank=True,
    help_text="Exchange rate used when posting (invoice currency to base currency)"
)
base_currency_total = models.DecimalField(
    max_digits=14, 
    decimal_places=2, 
    null=True, 
    blank=True,
    help_text="Total amount in base currency"
)
```

#### 2. Updated Serializers
**Files Modified**:
- `finance/serializers.py` - ARInvoiceSerializer
- `finance/serializers.py` - APInvoiceSerializer

**Changes**:
- ✅ Added `currency_code` field (from currency.code relation)
- ✅ Added `exchange_rate` field (read-only)
- ✅ Added `base_currency_total` field (read-only)

```python
# ARInvoiceSerializer
class Meta: 
    model = ARInvoice
    fields = [..., "currency_code", "exchange_rate", "base_currency_total", ...]
    read_only_fields = [..., "exchange_rate", "base_currency_total", "currency_code"]
```

### Frontend Changes

#### 1. Types (Already Existed)
**File**: `frontend/src/types/index.ts`

Both `ARInvoice` and `APInvoice` interfaces already include:
```typescript
export interface ARInvoice {
  // ...existing fields...
  currency_code?: string;
  exchange_rate?: string;
  base_currency_total?: string;
}

export interface APInvoice {
  // ...existing fields...
  currency_code?: string;
  exchange_rate?: string;
  base_currency_total?: string;
}
```

#### 2. Updated AR Invoice List
**File**: `frontend/src/app/ar/invoices/page.tsx`

**Added Columns**:
1. **Currency** - Shows currency code (e.g., USD, AED)
2. **Total** - Shows amount in invoice currency with code
3. **Rate** - Shows exchange rate (4 decimal places)
4. **Base Total** - Shows converted amount in base currency (formatted)

**Table Header**:
```tsx
<th>Currency</th>
<th>Total</th>
<th>Rate</th>
<th>Base Total</th>
```

**Table Data**:
```tsx
<td>{invoice.currency_code || 'N/A'}</td>
<td>{invoice.currency_code} {invoice.total}</td>
<td>{invoice.exchange_rate ? parseFloat(invoice.exchange_rate).toFixed(4) : '—'}</td>
<td>{invoice.base_currency_total ? 
  parseFloat(invoice.base_currency_total).toLocaleString('en-US', { 
    minimumFractionDigits: 2, 
    maximumFractionDigits: 2 
  }) : '—'}</td>
```

#### 3. Updated AP Invoice List
**File**: `frontend/src/app/ap/invoices/page.tsx`

Same changes as AR invoice list:
- Added Currency column
- Added Rate column
- Added Base Total column
- Updated Total column to show currency code

## How It Works

### When an Invoice is Posted

1. **Exchange Rate Calculation**:
   - System looks up the exchange rate for the invoice date
   - Stores the rate in `invoice.exchange_rate`

2. **Base Currency Conversion**:
   - Calculates: `base_currency_total = invoice_total * exchange_rate`
   - Stores the result in `invoice.base_currency_total`

3. **Display in Frontend**:
   - Shows original currency amount
   - Shows exchange rate used
   - Shows converted base currency amount

### Example Display

| Invoice # | Currency | Total | Rate | Base Total | Balance |
|-----------|----------|-------|------|------------|---------|
| INV-001 | USD | USD 1,000.00 | 3.6725 | 3,672.50 | USD 0.00 |
| INV-002 | AED | AED 5,000.00 | 1.0000 | 5,000.00 | AED 2,500.00 |
| INV-003 | EUR | EUR 800.00 | 4.0150 | 3,212.00 | EUR 800.00 |

## Benefits

### 1. Multi-Currency Visibility
- Users can see both original and base currency amounts
- Easy to track total exposure in different currencies
- Exchange rates are visible for audit purposes

### 2. Accurate Reporting
- Base currency totals enable accurate P&L reporting
- FX gains/losses can be properly tracked
- Consolidated reports show true financial position

### 3. Better Decision Making
- Management can see total AR/AP in base currency
- Easy to identify large foreign currency exposures
- Historical exchange rates are preserved

## Files Modified

### Backend
1. ✅ `finance/serializers.py` - Added fields to ARInvoiceSerializer
2. ✅ `finance/serializers.py` - Added fields to APInvoiceSerializer

### Frontend
3. ✅ `frontend/src/app/ar/invoices/page.tsx` - Updated table columns
4. ✅ `frontend/src/app/ap/invoices/page.tsx` - Updated table columns

## Database Schema

The fields already exist in the database (no migration needed):

```sql
-- ar_arinvoice table
ALTER TABLE ar_arinvoice ADD COLUMN exchange_rate DECIMAL(18,6);
ALTER TABLE ar_arinvoice ADD COLUMN base_currency_total DECIMAL(14,2);

-- ap_apinvoice table  
ALTER TABLE ap_apinvoice ADD COLUMN exchange_rate DECIMAL(18,6);
ALTER TABLE ap_apinvoice ADD COLUMN base_currency_total DECIMAL(14,2);
```

## API Response Example

### Before
```json
{
  "id": 1,
  "invoice_number": "INV-001",
  "total": "1000.00",
  "currency": 2
}
```

### After
```json
{
  "id": 1,
  "invoice_number": "INV-001",
  "currency": 2,
  "currency_code": "USD",
  "total": "1000.00",
  "exchange_rate": "3.6725",
  "base_currency_total": "3672.50"
}
```

## Testing

### Manual Testing Steps

1. **Create Invoice in Foreign Currency**:
   - Go to AR/AP Invoices
   - Create new invoice
   - Select currency (e.g., USD)
   - Add line items
   - Save

2. **Post Invoice**:
   - Click "Post to GL"
   - System should calculate exchange rate
   - `base_currency_total` should be populated

3. **Verify Display**:
   - Refresh invoice list
   - Should see Currency code
   - Should see Exchange Rate
   - Should see Base Total
   - Base Total should match: Total × Rate

4. **Check API Response**:
   ```bash
   curl http://localhost:8000/api/ar-invoices/
   ```
   - Should include `currency_code`, `exchange_rate`, `base_currency_total`

## Notes

- Exchange rate is only set when invoice is posted to GL
- Unposted invoices will show "—" for rate and base total
- Base currency is typically AED (United Arab Emirates Dirham)
- Exchange rates are historical (date-specific)
- Rates are preserved even if current rates change

## Future Enhancements

- [ ] Add base currency totals to payment screens
- [ ] Add FX gain/loss indicators
- [ ] Add currency filter to invoice list
- [ ] Add base currency summary totals at bottom of lists
- [ ] Add exchange rate history view
- [ ] Add ability to manually override exchange rates
- [ ] Add base currency amounts in invoice detail views

## Related Documentation

- Exchange Rate setup: See `docs/EXCHANGE_RATE_*.md`
- Currency configuration: See `core/models.py` - Currency model
- Posting logic: See `finance/services.py` - post_ar_invoice/post_ap_invoice

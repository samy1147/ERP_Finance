# Multi-Currency Payment UI Guide

## Overview
This guide explains the enhanced AR/AP payment creation pages that handle complex multi-currency scenarios, including payments where both the invoice and payment currencies are different from the base currency.

## Multi-Currency Scenarios Supported

### Scenario 1: Same Currency (Simple)
```
Invoice: AED 1,000
Payment: AED 1,000
Result: No FX conversion needed
```

### Scenario 2: Cross-Currency (One Conversion)
```
Invoice: EUR 1,000
Payment: AED
Exchange: EUR → AED
Result: Single conversion, FX badge shown
```

### Scenario 3: Multi-Currency (Two Conversions) ⚠️
```
Invoice: EUR 1,000
Payment: USD
Base: AED
Exchange: EUR → AED, then USD → AED
Result: Complex FX with orange FX* badge
```

## UI Components

### 1. Invoice Currency Column
**Location:** Payment allocation table

**Visual Indicators:**
- **Blue FX Badge:** Cross-currency (Invoice ≠ Payment)
- **Orange FX* Badge:** Complex multi-currency (Both ≠ Base)

**Example:**
```
| Invoice # | Currency | Total      | Outstanding | Amount |
|-----------|----------|------------|-------------|--------|
| INV-001   | EUR [FX] | $5,000.00  | $5,000.00  | 5000   |
| INV-002   | AED      | $2,000.00  | $2,000.00  | 2000   |
| INV-003   | USD [FX*]| $3,000.00  | $3,000.00  | 3000   |
```

**Legend:**
- `EUR [FX]` = Simple cross-currency (EUR → AED payment)
- `USD [FX*]` = Complex multi-currency (USD → AED → EUR payment)

### 2. Multi-Currency Info Box
**Location:** Above invoice allocation table
**Trigger:** Displays when cross-currency invoices detected

**Blue Info Box (Simple Cross-Currency):**
```
ℹ️ Cross-Currency Payment
Payment Currency: AED
Base Currency: AED
Exchange rate will be applied automatically between invoice and payment currencies.
```

**Orange Warning Box (Complex Multi-Currency):**
```
⚠️ Multi-Currency Payment Detected
Payment Currency: USD
Base Currency: AED

Automatic Processing:
• Invoice amounts converted: Invoice Currency → AED
• Payment amount converted: USD → AED
• FX gain/loss calculated automatically
• All GL entries posted in AED
```

### 3. Confirmation Dialog
**Trigger:** User clicks "Create Payment" with cross-currency allocations

**Simple Cross-Currency:**
```
Cross-currency payment detected:
Payment: AED
Invoices: INV-001 (EUR)

Exchange rates will be applied automatically. Continue?
[Cancel] [OK]
```

**Complex Multi-Currency:**
```
⚠️ MULTI-CURRENCY PAYMENT:

Payment Currency: USD
Invoices with different currencies: INV-001 (EUR), INV-002 (GBP)

The system will automatically:
1. Convert all amounts to base currency (AED)
2. Calculate FX gains/losses
3. Post correct journal entries

Continue with payment creation?
[Cancel] [OK]
```

## Technical Implementation

### Frontend Changes

#### 1. TypeScript Interface Update
```typescript
interface InvoiceAllocation {
  invoice: number;
  invoiceNumber: string;
  invoiceTotal: string;
  outstanding: string;
  amount: string;
  selected: boolean;
  currency?: string; // NEW: Invoice currency code
}
```

#### 2. Backend Integration
**API Response Enhanced:**
```json
{
  "id": 123,
  "number": "INV-001",
  "total": "5000.00",
  "outstanding": "5000.00",
  "currency": "EUR"  // NEW: Currency code included
}
```

#### 3. Currency Detection Logic
```typescript
const isCrossCurrency = invoice.currency && 
                        invoice.currency !== paymentCurrencyCode;

const isComplexFX = invoice.currency && 
                    invoice.currency !== baseCurrency && 
                    paymentCurrencyCode !== baseCurrency &&
                    invoice.currency !== paymentCurrencyCode;
```

**Explanation:**
- `isCrossCurrency`: Invoice and payment currencies differ
- `isComplexFX`: Neither currency is the base currency

### Backend Processing

#### Multi-Currency Payment Flow
```
1. User Creates Payment
   ↓
2. Payment Allocations Created
   - invoice_currency and current_exchange_rate auto-populated
   ↓
3. update_exchange_rate_from_allocations() Called
   - Sets payment.invoice_currency (from allocations)
   - Sets payment.exchange_rate (from ExchangeRate table)
   ↓
4. post_ar_payment() / post_ap_payment() Called
   - Converts invoice amounts: Invoice Currency → Base Currency
   - Converts payment amount: Payment Currency → Base Currency
   - Calculates FX gain/loss
   - Posts journal entries in base currency
```

#### Exchange Rate Lookup
```python
# Example: EUR invoice, USD payment, AED base

# Step 1: Get invoice rate (EUR → AED)
invoice_rate = get_exchange_rate(
    from_currency=EUR,
    to_currency=AED,
    date=invoice.date
)
# Result: 1 EUR = 4.0125 AED

# Step 2: Get payment rate (USD → AED)
payment_rate = get_exchange_rate(
    from_currency=USD,
    to_currency=AED,
    date=payment.date
)
# Result: 1 USD = 3.6725 AED

# Step 3: Calculate effective rate (EUR → USD)
# Invoice: EUR 1,000 * 4.0125 = AED 4,012.50
# Payment: USD 1,093 * 3.6725 = AED 4,013.62
# FX Gain: AED 1.12
```

## User Workflow

### Creating Multi-Currency Payment (AR)

1. **Select Customer**
   - Page loads outstanding invoices
   - Invoices may be in different currencies

2. **Review Currency Information**
   - Check Currency column in allocation table
   - Note FX badges (blue = simple, orange = complex)
   - Read multi-currency info box if displayed

3. **Set Payment Details**
   - Enter payment amount
   - Select payment currency
   - Currency column updates to show cross-currency indicators

4. **Allocate to Invoices**
   - Select invoices (can be multiple currencies)
   - Enter allocation amounts
   - System tracks currency for each allocation

5. **Submit Payment**
   - Confirmation dialog shows currency details
   - Click OK to proceed
   - Backend automatically handles all conversions

6. **Post Payment**
   - Exchange rates fetched automatically
   - FX gain/loss calculated
   - Journal entries posted in base currency

### Creating Multi-Currency Payment (AP)
Same workflow as AR, but with suppliers instead of customers.

## Real-World Examples

### Example 1: EUR Customer, AED Payment
```
Scenario:
- Invoice: EUR 1,000 @ 4.0125 = AED 4,012.50
- Payment: AED 4,012.50
- Base: AED

UI Display:
| Invoice #  | Currency | Outstanding | Amount    |
|------------|----------|-------------|-----------|
| INV-001    | EUR [FX] | €1,000.00   | 1000.00   |

Info Box: Blue (simple cross-currency)

Backend Processing:
1. Convert invoice: EUR 1,000 × 4.0125 = AED 4,012.50
2. Payment already in AED: AED 4,012.50
3. No FX gain/loss (amounts match)
```

### Example 2: EUR Supplier, USD Payment, AED Base
```
Scenario:
- Invoice: EUR 1,000 @ 4.0125 = AED 4,012.50
- Payment: USD 1,093 @ 3.6725 = AED 4,013.62
- Base: AED
- FX Gain: AED 1.12

UI Display:
| Invoice #  | Currency  | Outstanding | Amount    |
|------------|-----------|-------------|-----------|
| INV-001    | EUR [FX*] | €1,000.00   | 1000.00   |

Info Box: Orange (complex multi-currency)

Confirmation Dialog:
⚠️ MULTI-CURRENCY PAYMENT:
Payment Currency: USD
Invoices: INV-001 (EUR)
System will convert EUR → AED and USD → AED

Backend Processing:
1. Convert invoice: EUR 1,000 × 4.0125 = AED 4,012.50
2. Convert payment: USD 1,093 × 3.6725 = AED 4,013.62
3. Calculate FX gain: AED 4,013.62 - AED 4,012.50 = AED 1.12
4. Post journal entries:
   Dr. Accounts Receivable  AED 4,012.50
   Cr. Bank Account        AED 4,013.62
   Cr. FX Gain (7600)      AED 1.12
```

### Example 3: Multiple Invoices, Mixed Currencies
```
Scenario:
- Invoice 1: EUR 1,000
- Invoice 2: USD 500
- Invoice 3: AED 2,000
- Payment: AED 10,500
- Base: AED

UI Display:
| Invoice #  | Currency  | Outstanding | Amount    |
|------------|-----------|-------------|-----------|
| INV-001    | EUR [FX]  | €1,000.00   | 1000.00   |
| INV-002    | USD [FX]  | $500.00     | 500.00    |
| INV-003    | AED       | AED 2,000.00| 2000.00   |

Info Box: Blue (cross-currency, but payment is base)

Backend Processing:
1. Convert EUR invoice: EUR 1,000 × 4.0125 = AED 4,012.50
2. Convert USD invoice: USD 500 × 3.6725 = AED 1,836.25
3. AED invoice: Already AED 2,000.00
4. Total: AED 7,848.75
5. Payment: AED 10,500.00
6. Result: AED 2,651.25 unallocated (allowed)
```

## Badge Color Reference

| Badge Type | Color   | Meaning                              | Example              |
|------------|---------|--------------------------------------|----------------------|
| No Badge   | -       | Same currency as payment             | AED → AED            |
| Blue FX    | Blue    | Cross-currency, one conversion       | EUR → AED            |
| Orange FX* | Orange  | Multi-currency, two conversions      | EUR → AED → USD      |

## Error Prevention

### Validation Rules
1. ✅ **Currency Mismatch Alert:** User warned before submitting
2. ✅ **Exchange Rate Check:** Backend validates rate exists for date
3. ✅ **Amount Validation:** Allocation cannot exceed outstanding
4. ✅ **Total Validation:** Allocations cannot exceed payment amount

### Error Messages
```typescript
// Missing exchange rate
"Exchange rate not found for EUR to AED on 2024-01-15. 
Please add the rate in Settings > Exchange Rates."

// Invalid allocation
"Allocation amount for INV-001 exceeds outstanding balance."

// Over-allocation
"Total allocated (5,500.00) exceeds payment amount (5,000.00)"
```

## Best Practices

### For Users
1. **Review Currency Column:** Always check invoice currencies before allocating
2. **Read Info Boxes:** Pay attention to orange warning boxes for complex FX
3. **Confirm Rates:** Ensure exchange rates are up-to-date in system
4. **Check Totals:** Verify allocation summary before submitting

### For Administrators
1. **Maintain Exchange Rates:** Keep daily rates updated
2. **Set Base Currency:** Configure correct base currency in settings
3. **Monitor FX Accounts:** Review account 7600 (Gain) and 6600 (Loss)
4. **Train Users:** Educate on multi-currency payment flows

## Troubleshooting

### Issue: "Exchange rate not found" error
**Solution:** Add missing exchange rate in Settings > Exchange Rates for the payment date

### Issue: FX badge not showing
**Solution:** Check that invoice currency code is returned by backend API

### Issue: Wrong FX calculation
**Solution:** Verify exchange rates are correct for both invoice and payment dates

### Issue: Complex FX not detected
**Solution:** Ensure base currency is properly configured in Currency table (is_base=true)

## Files Modified

### Frontend (AR)
- `frontend/src/app/ar/payments/new/page.tsx`
  - Added currency column to table
  - Added FX detection logic
  - Added multi-currency info box
  - Added confirmation dialog

### Frontend (AP)
- `frontend/src/app/ap/payments/new/page.tsx`
  - Same changes as AR payment page

### Backend (Already Complete)
- `ar/models.py` - FX fields in ARPayment, ARPaymentAllocation
- `ap/models.py` - FX fields in APPayment, APPaymentAllocation
- `finance/services.py` - Multi-currency post_ar_payment(), post_ap_payment()
- `finance/api_extended.py` - Outstanding invoices API includes currency

## Testing Checklist

### AR Payments
- [ ] Same currency payment (AED → AED)
- [ ] Cross-currency payment (EUR → AED)
- [ ] Complex multi-currency (EUR → AED, payment in USD)
- [ ] Multiple invoices, mixed currencies
- [ ] Info box displays correctly (blue vs orange)
- [ ] FX badges show correctly (FX vs FX*)
- [ ] Confirmation dialog shows currency details
- [ ] Backend processes correctly (check GL entries)

### AP Payments
- [ ] Same tests as AR payments
- [ ] Supplier-specific currency matching

## Summary

**What Was Added:**
1. ✅ Currency column in invoice allocation table
2. ✅ FX badges (blue for simple, orange for complex)
3. ✅ Multi-currency info box with automatic processing details
4. ✅ Confirmation dialog explaining currency conversions
5. ✅ Cross-currency detection and visual indicators
6. ✅ Tooltips explaining FX conversion paths

**User Benefits:**
- Clear visibility of currency mismatches
- Automatic FX handling (no manual rate entry)
- Warnings for complex scenarios
- Confidence in multi-currency transactions

**Technical Benefits:**
- Accurate FX gain/loss calculation
- All GL entries in base currency
- Proper exchange rate tracking
- Full audit trail of currency conversions

---

*Last Updated: January 2024*
*Related Docs: MULTI_CURRENCY_PAYMENT_FUNCTIONS.md, FRONTEND_FX_TRACKING_UPDATES.md*

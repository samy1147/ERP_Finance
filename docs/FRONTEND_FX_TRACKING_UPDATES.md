# Frontend FX Tracking Updates

## Overview
This document outlines all frontend updates made to support the multi-currency payment system with FX tracking capabilities.

## Updated Files

### 1. TypeScript Type Definitions (`frontend/src/types/index.ts`)

#### ARPaymentAllocation Interface
**Added Fields:**
```typescript
invoice_currency?: number;           // Invoice currency ID
invoice_currency_code?: string;      // Invoice currency code (e.g., "EUR")
current_exchange_rate?: string;      // Exchange rate at time of allocation
```

**Purpose:** Track the currency and exchange rate for each payment allocation to an invoice.

#### ARPayment Interface
**Added Fields:**
```typescript
invoice_currency?: number;           // Invoice currency ID (from allocated invoices)
invoice_currency_code?: string;      // Invoice currency code
exchange_rate?: string;              // Exchange rate (Invoice Currency → Payment Currency)
payment_currency_code?: string;      // Payment currency code (e.g., "AED")
```

**Purpose:** Track multi-currency payment information including exchange rates for FX gain/loss calculations.

#### APPaymentAllocation Interface
**Added Fields:**
```typescript
invoice_currency?: number;           // Invoice currency ID
invoice_currency_code?: string;      // Invoice currency code (e.g., "USD")
current_exchange_rate?: string;      // Exchange rate at time of allocation
```

**Purpose:** Track the currency and exchange rate for each payment allocation to a supplier invoice.

#### APPayment Interface
**Added Fields:**
```typescript
invoice_currency?: number;           // Invoice currency ID (from allocated invoices)
invoice_currency_code?: string;      // Invoice currency code
exchange_rate?: string;              // Exchange rate (Invoice Currency → Payment Currency)
payment_currency_code?: string;      // Payment currency code (e.g., "AED")
```

**Purpose:** Track multi-currency payment information including exchange rates for FX gain/loss calculations.

---

### 2. AR Payments List Page (`frontend/src/app/ar/payments/page.tsx`)

#### Table Structure Updates

**Added Columns:**
1. **Currency Column** - Displays payment currency with FX indicator badge
2. **FX Rate Column** - Shows exchange rate for cross-currency payments

**Before:**
```
| Payment Date | Customer | Amount | Reference | Status | Actions |
```

**After:**
```
| Payment Date | Customer | Amount | Currency | FX Rate | Reference | Status | Actions |
```

#### Features Implemented

##### 1. Cross-Currency Detection
```typescript
const isCrossCurrency = payment.invoice_currency_code && 
                         payment.payment_currency_code && 
                         payment.invoice_currency_code !== payment.payment_currency_code;
```

##### 2. Currency Display with FX Badge
```typescript
<td className="table-td">
  <div className="flex items-center gap-1">
    <span className="font-medium">{payment.payment_currency_code || payment.currency_code || '-'}</span>
    {isCrossCurrency && (
      <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded" title="Cross-currency payment">
        FX
      </span>
    )}
  </div>
</td>
```

**Visual:**
- Regular payment: `AED`
- Cross-currency: `AED` with blue `FX` badge

##### 3. Exchange Rate Display
```typescript
<td className="table-td">
  {isCrossCurrency && payment.exchange_rate ? (
    <div className="text-sm">
      <span className="text-gray-600">
        1 {payment.invoice_currency_code} = {parseFloat(payment.exchange_rate).toFixed(6)} {payment.payment_currency_code}
      </span>
    </div>
  ) : (
    <span className="text-gray-400">-</span>
  )}
</td>
```

**Example Displays:**
- Same currency: `-`
- EUR → AED: `1 EUR = 4.012500 AED`
- EGP → AED: `1 EGP = 0.074800 AED`

---

### 3. AP Payments List Page (`frontend/src/app/ap/payments/page.tsx`)

#### Table Structure Updates

**Added Columns:**
1. **Currency Column** - Displays payment currency with FX indicator badge
2. **FX Rate Column** - Shows exchange rate for cross-currency payments

**Before:**
```
| Payment Date | Supplier | Amount | Reference | Status | Actions |
```

**After:**
```
| Payment Date | Supplier | Amount | Currency | FX Rate | Reference | Status | Actions |
```

#### Features Implemented
(Same as AR Payments - see above)

##### Example Displays:
- Same currency: `-`
- EUR → USD: `1 EUR = 1.092506 USD`
- USD → AED: `1 USD = 3.672500 AED`

---

## Backend-Frontend Integration

### Data Flow

```
Backend Serializer → API Response → Frontend TypeScript Interface → UI Display
```

#### 1. Backend Sends (from serializers)
```python
ARPaymentSerializer.fields = [
    "invoice_currency",
    "invoice_currency_code", 
    "exchange_rate",
    "currency",
    "payment_currency_code"
]
```

#### 2. API Response Example
```json
{
  "id": 1,
  "customer": 1,
  "customer_name": "ACME Corp",
  "total_amount": "1000.00",
  "currency": 2,
  "payment_currency_code": "AED",
  "invoice_currency": 3,
  "invoice_currency_code": "EUR",
  "exchange_rate": "4.012500",
  "date": "2024-01-15",
  "posted_at": "2024-01-15T10:30:00Z"
}
```

#### 3. Frontend Receives (TypeScript)
```typescript
interface ARPayment {
  invoice_currency?: number;
  invoice_currency_code?: string;
  exchange_rate?: string;
  payment_currency_code?: string;
  // ... other fields
}
```

#### 4. UI Displays
```
| Jan 15, 2024 | ACME Corp | $1,000.00 | AED [FX] | 1 EUR = 4.012500 AED | ... |
```

---

## Visual Design Elements

### FX Badge Styling
```css
background-color: #dbeafe (blue-100)
color: #1d4ed8 (blue-700)
padding: 2px 6px
border-radius: 4px
font-size: 0.75rem
```

### Status Badge (Existing)
- **POSTED**: Green background (`bg-green-100 text-green-800`)
- **DRAFT**: Yellow background (`bg-yellow-100 text-yellow-800`)

### Exchange Rate Display
- Font size: `text-sm` (14px)
- Color: `text-gray-600`
- Format: `1 [FROM] = [RATE] [TO]`
- Decimals: 6 digits

---

## User Experience Features

### 1. Clear Currency Visibility
- Payment currency always displayed
- FX badge highlights cross-currency transactions
- Easy to scan large payment lists

### 2. Exchange Rate Transparency
- Rate displayed directly in list
- No need to drill down into details
- Format matches accounting standards

### 3. Consistent Design
- Same pattern for AR and AP
- Familiar table layout
- Minimal visual clutter

### 4. Responsive Design
- Table scrolls horizontally if needed
- Badges remain inline with currency
- Rate display adapts to space

---

## Testing Checklist

### AR Payments Page
- [ ] Page loads without errors
- [ ] All payments display correctly
- [ ] Same-currency payments show currency without FX badge
- [ ] Cross-currency payments show FX badge
- [ ] Exchange rates display correctly (6 decimals)
- [ ] Exchange rate format: `1 EUR = 4.012500 AED`
- [ ] Status badges (POSTED/DRAFT) display correctly
- [ ] Actions (Edit/Post/Delete) work as expected

### AP Payments Page
- [ ] Page loads without errors
- [ ] All payments display correctly
- [ ] Same-currency payments show currency without FX badge
- [ ] Cross-currency payments show FX badge
- [ ] Exchange rates display correctly (6 decimals)
- [ ] Exchange rate format: `1 USD = 3.672500 AED`
- [ ] Status badges (POSTED/DRAFT) display correctly
- [ ] Actions (Edit/Post/Delete) work as expected

### Data Integrity
- [ ] TypeScript types match backend serializers
- [ ] No runtime type errors in console
- [ ] All optional fields handled gracefully
- [ ] Missing exchange rates show `-` instead of error

---

## Example Use Cases

### Case 1: Same Currency Payment
```
Customer pays in AED for AED invoice
Display: AED (no FX badge, rate shows "-")
```

### Case 2: EUR Customer, AED Payment
```
Customer has EUR invoice, pays in AED
Display: AED [FX] | 1 EUR = 4.012500 AED
Backend automatically calculates gain/loss
```

### Case 3: Multi-Invoice Payment
```
Payment allocated to 3 invoices in different currencies
Display: Shows average exchange rate
FX badge indicates complexity
```

### Case 4: Draft vs Posted
```
Draft: Yellow DRAFT badge, Edit/Post/Delete actions
Posted: Green POSTED badge, no actions (immutable)
```

---

## Integration with Backend

### Automatic FX Rate Population
- Backend `save()` method auto-populates exchange rates
- Frontend receives rates in API response
- No manual rate entry needed in UI
- Rates pulled from `finance.ExchangeRate` model

### Multi-Currency Payment Flow
1. User creates payment (selects currency)
2. User allocates to invoices (can be different currencies)
3. Backend calls `update_exchange_rate_from_allocations()`
4. Payment `exchange_rate` field updated
5. Frontend displays rate in list

### FX Gain/Loss Calculation
- Backend compares `invoice.exchange_rate` vs `payment.exchange_rate`
- Difference creates FX gain/loss journal entry
- Posted to account 7600 (FX Gain) or 6600 (FX Loss)
- Frontend shows FX badge to indicate cross-currency

---

## Future Enhancements

### Potential Additions
1. **FX Gain/Loss Indicator**
   - Show gain/loss amount next to exchange rate
   - Color code: green for gain, red for loss
   - Example: `+$15.50` or `-$8.25`

2. **Currency Conversion Calculator**
   - Hover over FX badge
   - Show breakdown: Invoice Amount → Payment Amount
   - Example: `EUR 1,000 → AED 4,012.50`

3. **Exchange Rate History**
   - Click on rate to see rate changes over time
   - Compare current rate vs original invoice rate
   - Show rate trend chart

4. **Filter by Currency**
   - Dropdown to filter payments by currency
   - Show only cross-currency payments
   - Group by currency pair

5. **Export to Excel**
   - Include FX rates in export
   - Add calculated columns for gain/loss
   - Format for accounting review

---

## Technical Notes

### Performance Considerations
- Exchange rates loaded with payment data (no extra queries)
- Currency codes use `source` in serializer (efficient)
- FX badge only rendered when needed (conditional)

### Browser Compatibility
- Uses standard React/TypeScript
- CSS classes from Tailwind (widely supported)
- Number formatting with `parseFloat().toFixed(6)`

### Error Handling
- Graceful fallback for missing fields (`|| '-'`)
- Optional chaining for nested properties
- Type-safe with TypeScript interfaces

---

## Summary

**What Changed:**
1. ✅ TypeScript interfaces updated with FX fields
2. ✅ AR payments list shows currency and FX rate
3. ✅ AP payments list shows currency and FX rate
4. ✅ FX badge highlights cross-currency payments
5. ✅ Exchange rates displayed in readable format

**Impact:**
- Users can see currency information at a glance
- Cross-currency payments clearly identified
- Exchange rates transparent and visible
- Professional accounting interface

**Status:** ✅ COMPLETE
All frontend updates aligned with backend multi-currency system.

---

*Last Updated: January 2024*
*Related Docs: MULTI_CURRENCY_PAYMENT_FUNCTIONS.md*

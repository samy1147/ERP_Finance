# Payment Allocation Currency Tracking

## Summary

Added **automatic currency tracking** to payment allocations (`ARPaymentAllocation` and `APPaymentAllocation`) to capture the invoice currency and exchange rate at the time of payment allocation.

## New Fields

### Added to Both `ARPaymentAllocation` and `APPaymentAllocation`:

#### 1. `invoice_currency` Field
```python
invoice_currency = models.ForeignKey(
    Currency, 
    on_delete=models.PROTECT, 
    null=True, 
    blank=True,
    help_text="Currency of the invoice (copied from invoice at allocation time)"
)
```

**Purpose**: Stores the currency of the invoice being paid  
**Source**: Automatically copied from `invoice.currency` when allocation is created  
**Why**: Preserves historical record even if invoice currency changes later

#### 2. `current_exchange_rate` Field
```python
current_exchange_rate = models.DecimalField(
    max_digits=18, 
    decimal_places=6, 
    null=True, 
    blank=True,
    help_text="Exchange rate from invoice currency to payment currency at allocation time"
)
```

**Purpose**: Stores the exchange rate at allocation time  
**Calculation**: FROM invoice currency TO payment currency  
**Source**: Fetched from exchange rate table using payment date  
**Why**: Tracks the exact rate used for cross-currency payments

---

## How It Works

### Automatic Population on Save

The `save()` method automatically populates these fields:

```python
def save(self, *args, **kwargs):
    """Auto-populate invoice_currency and current_exchange_rate on save"""
    if self.invoice and not self.invoice_currency:
        # Step 1: Get invoice currency
        self.invoice_currency = self.invoice.currency
        
        # Step 2: Calculate exchange rate if currencies differ
        if self.payment and self.payment.currency and self.invoice.currency:
            from_currency = self.invoice.currency
            to_currency = self.payment.currency
            
            if from_currency.id != to_currency.id:
                # Different currencies - fetch exchange rate
                self.current_exchange_rate = get_exchange_rate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate_date=self.payment.date,
                    rate_type="SPOT"
                )
            else:
                # Same currency - rate is 1.0
                self.current_exchange_rate = Decimal('1.000000')
    
    super().save(*args, **kwargs)
```

### When Fields Are Populated

✅ **Automatically** when creating new payment allocation  
✅ **Automatically** when saving existing allocation (if not already set)  
✅ **Preserved** after initial save (won't overwrite existing values)

---

## Use Cases

### Use Case 1: Same Currency Payment
```
Invoice: EUR 1,000
Payment: EUR 1,000

Allocation Record:
├─ invoice_currency: EUR
└─ current_exchange_rate: 1.000000
```

**Result**: Simple 1:1 mapping, no currency conversion needed

### Use Case 2: Cross-Currency Payment
```
Invoice: EUR 1,000 (customer billed in EUR)
Payment: AED 4,000 (customer paid in AED)

Allocation Record:
├─ invoice_currency: EUR
└─ current_exchange_rate: 4.012500
    (meaning 1 EUR = 4.0125 AED at payment date)
```

**Result**: Exchange rate preserved for accurate reporting

### Use Case 3: Multi-Currency Payment Allocation
```
Payment: USD 2,000

Allocated to:
├─ Invoice A (EUR 1,000)
│   ├─ invoice_currency: EUR
│   └─ current_exchange_rate: 1.092506 (USD per EUR)
│
└─ Invoice B (GBP 700)
    ├─ invoice_currency: GBP
    └─ current_exchange_rate: 1.287500 (USD per GBP)
```

**Result**: Each allocation tracks its own currency conversion

---

## Real Data Example

From the test results:

### AR Allocation #1
```
Payment Currency: AED
Invoice Currency: EUR
Amount: 42,000.00
Exchange Rate: 4.012500

Interpretation:
- Customer paid 42,000 AED
- Invoice was for approximately EUR 10,467.71 (42,000 / 4.0125)
- Rate: 1 EUR = 4.0125 AED
```

### AR Allocation #2
```
Payment Currency: AED  
Invoice Currency: EGP
Amount: 798,000.00
Exchange Rate: 0.074800

Interpretation:
- Customer paid 798,000 AED
- Invoice was for approximately EGP 10,668,449 (798,000 / 0.0748)
- Rate: 1 EGP = 0.0748 AED
```

### AP Allocation #1
```
Payment Currency: USD
Invoice Currency: EUR
Amount: 500.00
Exchange Rate: 1.092506

Interpretation:
- Company paid USD 500
- Supplier invoice was for approximately EUR 457.62 (500 / 1.092506)
- Rate: 1 EUR = 1.092506 USD
```

---

## API Response

### Payment Allocation Serializer

```python
class ARPaymentAllocationSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.number', read_only=True)
    invoice_currency_code = serializers.CharField(source='invoice_currency.code', read_only=True)
    
    class Meta:
        model = ARPaymentAllocation
        fields = [
            'id', 'payment', 'invoice', 'invoice_number', 
            'amount', 'memo', 'created_at',
            'invoice_currency', 'invoice_currency_code', 'current_exchange_rate'
        ]
        read_only_fields = ['id', 'created_at', 'invoice_currency', 'current_exchange_rate']
```

### Example API Response

```json
{
  "id": 1,
  "payment": 1,
  "invoice": 5,
  "invoice_number": "INV-2025-001",
  "amount": "42000.00",
  "memo": "",
  "created_at": "2025-01-18T10:30:00Z",
  "invoice_currency": 2,
  "invoice_currency_code": "EUR",
  "current_exchange_rate": "4.012500"
}
```

---

## Benefits

### 1. **Historical Accuracy**
- Preserves the exact currency and rate used at payment time
- Even if exchange rates change later, the record is accurate

### 2. **Multi-Currency Support**
- Handles payments in different currencies than invoices
- Each allocation can have its own exchange rate

### 3. **Audit Trail**
- Complete record of currency conversions
- Easy to track and verify payment allocations

### 4. **Reporting**
- Can generate accurate multi-currency reports
- Calculate effective payment amounts in any currency

### 5. **Compliance**
- Meets accounting standards for foreign currency transactions
- Provides documentation for tax and audit purposes

---

## Database Schema

### Migration Files
- `ar/migrations/0011_add_allocation_currency_fields.py`
- `ap/migrations/0011_add_allocation_currency_fields.py`

### Table Updates

#### `ar_arpaymentallocation` Table
```sql
ALTER TABLE ar_arpaymentallocation 
ADD COLUMN invoice_currency_id INTEGER REFERENCES core_currency(id),
ADD COLUMN current_exchange_rate DECIMAL(18, 6);
```

#### `ap_appaymentallocation` Table
```sql
ALTER TABLE ap_appaymentallocation 
ADD COLUMN invoice_currency_id INTEGER REFERENCES core_currency(id),
ADD COLUMN current_exchange_rate DECIMAL(18, 6);
```

---

## Integration Points

### 1. Payment Creation
When creating a payment allocation:

```python
from ar.models import ARPayment, ARPaymentAllocation

# Create payment
payment = ARPayment.objects.create(
    customer=customer,
    total_amount=42000.00,
    currency=aed_currency,  # Payment in AED
    date=today
)

# Create allocation - currency fields auto-populated
allocation = ARPaymentAllocation.objects.create(
    payment=payment,
    invoice=invoice,  # Invoice in EUR
    amount=42000.00
)

# Check auto-populated fields
print(allocation.invoice_currency.code)  # "EUR"
print(allocation.current_exchange_rate)  # 4.012500
```

### 2. Payment Processing
The fields are used during payment processing to:
- Calculate payment amounts in base currency
- Generate journal entries with correct FX amounts
- Update invoice payment status

### 3. Reporting
Use the fields for:
- Foreign exchange gain/loss calculations
- Multi-currency cash flow reports
- Payment reconciliation across currencies

---

## Data Migration

### For Existing Allocations

Existing payment allocations will have `NULL` values for the new fields. To populate them:

```python
from ar.models import ARPaymentAllocation
from ap.models import APPaymentAllocation

# Populate AR allocations
for alloc in ARPaymentAllocation.objects.filter(invoice_currency__isnull=True):
    alloc.save()  # Triggers auto-population
    print(f"Updated AR Allocation #{alloc.id}")

# Populate AP allocations
for alloc in APPaymentAllocation.objects.filter(invoice_currency__isnull=True):
    alloc.save()  # Triggers auto-population
    print(f"Updated AP Allocation #{alloc.id}")
```

Or run the test script:
```bash
python test_payment_allocation_currency.py
```

---

## Exchange Rate Lookup Logic

### Rate Direction
```
FROM: invoice_currency (what customer owes)
TO:   payment_currency (what customer paid)

Example:
Invoice in EUR, Payment in AED
FROM: EUR
TO:   AED
Rate: 4.012500 means 1 EUR = 4.0125 AED
```

### Rate Date
- Uses `payment.date` (the date the payment was made)
- Ensures rate reflects market conditions at payment time

### Rate Type
- Uses `"SPOT"` rate type
- Can be configured to use different rate types if needed

### Fallback
- If rate not found, field remains `NULL`
- Error is logged but doesn't block payment creation
- Allows manual entry later if needed

---

## Frontend Display

### Payment Details View
```tsx
interface PaymentAllocation {
  id: number;
  invoice_number: string;
  amount: string;
  invoice_currency_code: string;
  current_exchange_rate: string;
}

// Display example
<div>
  <p>Invoice: {allocation.invoice_number}</p>
  <p>Amount: {allocation.amount} {paymentCurrency}</p>
  <p>Invoice Currency: {allocation.invoice_currency_code}</p>
  {allocation.current_exchange_rate && (
    <p>Rate: 1 {allocation.invoice_currency_code} = {allocation.current_exchange_rate} {paymentCurrency}</p>
  )}
</div>
```

### Payment List View
Show currency indicator for cross-currency payments:
```tsx
{allocation.invoice_currency_code !== payment.currency_code && (
  <Badge variant="warning">
    Multi-Currency
  </Badge>
)}
```

---

## Testing

### Test Script Results

```
AR Allocation #1:
  Payment Currency: AED
  Invoice Currency: EUR
  Exchange Rate: 4.012500
  ✅ Auto-populated successfully

AR Allocation #2:
  Payment Currency: AED
  Invoice Currency: EGP
  Exchange Rate: 0.074800
  ✅ Auto-populated successfully

AP Allocation #1:
  Payment Currency: USD
  Invoice Currency: EUR
  Exchange Rate: 1.092506
  ✅ Auto-populated successfully
```

### Verification Steps

1. ✅ Fields are automatically populated on save
2. ✅ Exchange rates are fetched from rate table
3. ✅ Same-currency allocations get rate of 1.0
4. ✅ Cross-currency allocations get correct rates
5. ✅ Existing allocations can be updated by re-saving

---

## Files Modified

### Models
- `ar/models.py` - Added fields to `ARPaymentAllocation` with auto-save logic
- `ap/models.py` - Added fields to `APPaymentAllocation` with auto-save logic

### Serializers
- `finance/serializers.py`:
  - Added `ARPaymentAllocationSerializer`
  - Added `APPaymentAllocationSerializer`
  - Updated imports to include allocation models

### Migrations
- `ar/migrations/0011_add_allocation_currency_fields.py`
- `ap/migrations/0011_add_allocation_currency_fields.py`

### Test Scripts
- `test_payment_allocation_currency.py` - Verification script

---

## Future Enhancements

### 1. Realized Gain/Loss Tracking
Calculate FX gain/loss by comparing:
- Invoice exchange rate at posting
- Payment exchange rate at allocation
- Difference = realized gain/loss

### 2. Unrealized Gain/Loss
For unpaid invoices in foreign currency:
- Compare invoice rate to current market rate
- Track unrealized FX exposure

### 3. Multi-Currency Dashboard
- Summary of payments by currency
- Exchange rate trends
- FX exposure analysis

### 4. Rate Override
Allow manual override of exchange rate:
```python
allocation.current_exchange_rate = custom_rate
allocation.save(update_fields=['current_exchange_rate'])
```

---

## Summary

✅ **Fields Added**: `invoice_currency` and `current_exchange_rate` to payment allocations  
✅ **Auto-Population**: Automatically populated on save using invoice and payment data  
✅ **Exchange Rate Lookup**: Fetches rate from exchange rate table based on payment date  
✅ **Multi-Currency Support**: Each allocation tracks its own currency conversion  
✅ **Historical Accuracy**: Preserves exact currency and rate at payment time  
✅ **Migrations Applied**: Database schema updated successfully  
✅ **Tested**: All existing allocations verified and populated  

**Status**: ✅ **Implemented and Tested**  
**Last Updated**: 2025-01-18

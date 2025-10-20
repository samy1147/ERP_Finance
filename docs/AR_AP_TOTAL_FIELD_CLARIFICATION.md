# AR/AP Invoice Total Field - Technical Clarification

## Database vs Serializer Fields

### ❌ Common Misconception
"The database has a `total` column that stores the invoice total"

### ✅ Actual Implementation
The `total` is **calculated dynamically** and exposed through the serializer as a computed field.

---

## Database Schema (Actual Columns)

### ARInvoice / APInvoice Tables

```sql
CREATE TABLE ar_arinvoice (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    number VARCHAR(32) UNIQUE NOT NULL,
    date DATE NOT NULL,
    due_date DATE NOT NULL,
    currency_id INTEGER NOT NULL,
    country VARCHAR(2) NOT NULL,
    
    -- Status fields
    is_posted BOOLEAN DEFAULT FALSE,
    payment_status VARCHAR(20) DEFAULT 'UNPAID',
    approval_status VARCHAR(20) DEFAULT 'DRAFT',
    is_cancelled BOOLEAN DEFAULT FALSE,
    posted_at DATETIME NULL,
    paid_at DATETIME NULL,
    cancelled_at DATETIME NULL,
    
    -- FX fields
    exchange_rate DECIMAL(18,6) NULL,
    base_currency_total DECIMAL(14,2) NULL,
    
    -- NOTE: NO 'total', 'subtotal', 'tax_amount', or 'balance' columns!
    -- These are calculated on-the-fly from invoice items
    
    FOREIGN KEY (customer_id) REFERENCES ar_customer(id),
    FOREIGN KEY (currency_id) REFERENCES core_currency(id)
);
```

---

## How Totals Are Calculated

### 1. Invoice Items Store Line Details

```sql
CREATE TABLE ar_aritem (
    id INTEGER PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    description VARCHAR(255),
    quantity DECIMAL(12,2),
    unit_price DECIMAL(12,2),
    tax_rate_id INTEGER NULL,
    
    FOREIGN KEY (invoice_id) REFERENCES ar_arinvoice(id)
);
```

### 2. Calculation Logic (finance/services.py)

```python
def ar_totals(invoice: ARInvoice) -> dict:
    """Calculate invoice totals from line items"""
    subtotal = Decimal("0")
    tax = Decimal("0")
    total = Decimal("0")
    
    # Sum up all line items
    for item in invoice.items.all():
        rate = line_rate(item, invoice.date)
        line_subtotal, line_tax, line_total = amount_with_tax(
            item.quantity, 
            item.unit_price, 
            rate
        )
        subtotal += line_subtotal
        tax += line_tax
        total += line_total
    
    # Get paid amount from payment allocations
    paid = sum(
        alloc.amount 
        for alloc in invoice.payment_allocations.all()
    )
    
    return {
        "subtotal": subtotal,
        "tax": tax,
        "total": total,        # ← Calculated, not stored!
        "paid": paid,
        "balance": total - paid
    }
```

### 3. Serializer Exposes Calculated Fields

```python
class ARInvoiceSerializer(serializers.ModelSerializer):
    # These are SerializerMethodFields (computed dynamically)
    total = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    
    # These are actual database fields
    exchange_rate = models.DecimalField()  # ← Stored in DB
    base_currency_total = models.DecimalField()  # ← Stored in DB
    
    def get_total(self, obj):
        """Calculate and return total"""
        return str(ar_totals(obj)["total"])
```

---

## Why This Design?

### ✅ Advantages

1. **Data Integrity**
   - Total is always accurate based on current line items
   - No risk of stale/inconsistent totals
   - If line items change, total automatically reflects the change

2. **Flexibility**
   - Can recalculate with different tax rates retroactively
   - Easy to add new calculation logic
   - No database migrations needed for calculation changes

3. **Storage Efficiency**
   - Don't store redundant/derived data
   - Follows database normalization principles

### ⚠️ Trade-offs

1. **Performance**
   - Need to query items and calculate each time
   - Mitigated by caching in serializer (`_cached_totals`)
   - Could add database aggregation for large lists

2. **Complexity**
   - New developers might expect a `total` column
   - Need to understand the calculation flow

---

## API Response Structure

### GET /api/ar-invoices/1/

```json
{
  "id": 1,
  "customer": 5,
  "customer_name": "ACME Corp",
  "number": "INV-001",
  "date": "2025-01-15",
  "due_date": "2025-02-15",
  "currency": 2,
  "currency_code": "USD",
  
  // ← These are CALCULATED fields (not in DB)
  "subtotal": "1000.00",
  "tax_amount": "50.00",
  "total": "1050.00",
  "paid_amount": "500.00",
  "balance": "550.00",
  
  // ← These ARE in the database
  "exchange_rate": "3.6725",
  "base_currency_total": "3856.13",
  
  "is_posted": true,
  "payment_status": "PARTIALLY_PAID",
  "items": [
    {
      "id": 1,
      "description": "Product A",
      "quantity": "10.00",
      "unit_price": "100.00",
      "tax_rate": 1
    }
  ]
}
```

---

## What Gets Stored in Database

### When Invoice is Posted

```python
# During posting (finance/services.py)
def post_ar_invoice(invoice_id):
    invoice = ARInvoice.objects.get(pk=invoice_id)
    
    # Calculate current total
    totals = ar_totals(invoice)
    total_in_invoice_currency = totals["total"]
    
    # Get exchange rate
    exchange_rate = get_exchange_rate(
        invoice.currency, 
        invoice.date
    )
    
    # Calculate and STORE base currency total
    invoice.exchange_rate = exchange_rate
    invoice.base_currency_total = total_in_invoice_currency * exchange_rate
    invoice.is_posted = True
    invoice.save()
```

**Stored**: `exchange_rate`, `base_currency_total`, `is_posted`  
**Not Stored**: `total`, `subtotal`, `tax_amount` (recalculated each time)

---

## Why Store `base_currency_total` But Not `total`?

### `base_currency_total` (Stored)
- ✅ Historical value that should never change
- ✅ Reflects the exchange rate at posting time
- ✅ Used for financial reporting in base currency
- ✅ Audit requirement (locked after posting)

### `total` (Calculated)
- ✅ Can be recalculated from items anytime
- ✅ Items are the source of truth
- ✅ Tax rates might change, need to recalculate
- ✅ Follows normalization (don't store derived data)

---

## Summary

| Field | Stored in DB? | Why? |
|-------|---------------|------|
| `subtotal` | ❌ No | Calculated from items |
| `tax_amount` | ❌ No | Calculated from items + tax rates |
| `total` | ❌ No | Calculated from items |
| `paid_amount` | ❌ No | Calculated from payment allocations |
| `balance` | ❌ No | Calculated as total - paid |
| `exchange_rate` | ✅ Yes | Historical rate at posting time |
| `base_currency_total` | ✅ Yes | Historical converted amount |

---

## Conclusion

✅ **The implementation is correct!**

The `total` field doesn't exist in the database because it's a **derived/calculated value**. It's computed on-the-fly from the invoice items and exposed through the serializer. This is a standard Django REST Framework pattern for computed fields.

The `base_currency_total` and `exchange_rate` ARE stored because they represent **historical values** that should be locked at the time of posting and never change, even if exchange rates change later.

**The current implementation properly exposes all these fields in the API response, and the frontend can use them without knowing whether they're stored or calculated.**

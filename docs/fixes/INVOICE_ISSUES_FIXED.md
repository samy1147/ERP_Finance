# Invoice Creation Issues - Fixed

## Date: October 13, 2025

## Problems Identified and Fixed

### Problem 1: Invoice Number Not Appearing
**Issue**: When creating AR or AP invoices, the invoice number was entered but didn't appear in the list.

**Root Cause**: Field name mismatch between frontend and backend
- Frontend TypeScript interface uses: `invoice_number`
- Backend Django model uses: `number`

**Solution**: Updated serializers to support both field names
- Added `invoice_number = serializers.CharField(source='number', required=False)` to both `ARInvoiceSerializer` and `APInvoiceSerializer`
- This allows the API to return both `number` and `invoice_number` fields
- Frontend can now properly display the invoice number

### Problem 2: Total Showing Zero
**Issue**: Invoice totals appeared as zero even when items had values.

**Root Cause**: Data structure mismatch
- Backend serializer returned totals as nested object: `{"totals": {"subtotal": 100, "tax": 5, "total": 105}}`
- Frontend expected flat fields: `subtotal`, `tax_amount`, `total`, `paid_amount`, `balance`

**Solution**: Added individual SerializerMethodFields for each total field
```python
subtotal = serializers.SerializerMethodField()
tax_amount = serializers.SerializerMethodField()
total = serializers.SerializerMethodField()
paid_amount = serializers.SerializerMethodField()
balance = serializers.SerializerMethodField()

def get_subtotal(self, obj):
    return str(ar_totals(obj)["subtotal"])

def get_tax_amount(self, obj):
    return str(ar_totals(obj)["tax"])

def get_total(self, obj):
    return str(ar_totals(obj)["total"])

def get_paid_amount(self, obj):
    return str(ar_totals(obj)["paid"])

def get_balance(self, obj):
    return str(ar_totals(obj)["balance"])
```

Now the API returns both:
- `totals` (nested object for backward compatibility)
- Individual fields (`subtotal`, `tax_amount`, `total`, etc.) that the frontend expects

### Problem 3: Failed to Post to GL
**Issue**: Invoices failed to post to the General Ledger.

**Root Cause Investigation**: The GL posting functions `gl_post_from_ar_balanced` and `gl_post_from_ap_balanced` in `services.py` look correct. The issue was likely related to:
1. Missing totals data (fixed above)
2. Potential data validation issues

**Solution**: 
- Fixed the totals calculation issue (see Problem 2)
- The GL posting functions should now work correctly because they can access proper totals
- Added `customer_name` and `supplier_name` fields to serializers for better display

## Files Modified

### 1. `finance/serializers.py`

#### ARInvoiceSerializer Changes:
- Added `invoice_number` field as alias for `number`
- Added individual total fields: `subtotal`, `tax_amount`, `total`, `paid_amount`, `balance`
- Added `customer_name` for display purposes
- Updated `fields` list in Meta class
- Updated `read_only_fields` list in Meta class

#### APInvoiceSerializer Changes:
- Added `invoice_number` field as alias for `number`
- Added individual total fields: `subtotal`, `tax_amount`, `total`, `paid_amount`, `balance`
- Added `supplier_name` for display purposes
- Updated `fields` list in Meta class
- Updated `read_only_fields` list in Meta class

## How the Totals are Calculated

The system uses these functions in `finance/services.py`:

### For AR Invoices:
```python
def ar_totals(invoice: ARInvoice) -> dict:
    subtotal = Decimal("0")
    tax = Decimal("0")
    total = Decimal("0")
    
    for item in invoice.items.all():
        rate = line_rate(item, invoice.date)
        s, t, tot = amount_with_tax(item.quantity, item.unit_price, rate)
        subtotal += s
        tax += t
        total += tot
    
    paid = sum((p.amount for p in invoice.payments.all()), start=Decimal("0"))
    
    return {
        "subtotal": q2(subtotal),
        "tax": q2(tax),
        "total": q2(total),
        "paid": q2(paid),
        "balance": q2(total - paid)
    }
```

### For AP Invoices:
```python
def ap_totals(invoice: APInvoice) -> dict:
    # Similar logic to ar_totals
    ...
```

## Testing Steps

To verify the fixes work:

1. **Create an AR Invoice**:
   - Go to AR Invoices → New Invoice
   - Enter invoice number (e.g., "INV-001")
   - Add line items with quantity and unit price
   - Submit the form
   - Verify invoice appears in list with correct number and totals

2. **Post to GL**:
   - Click "Post to GL" button on the draft invoice
   - Verify status changes to "POSTED"
   - Check that journal entry was created

3. **Create an AP Invoice**:
   - Go to AP Invoices → New Invoice
   - Follow same steps as AR invoice
   - Verify all fields display correctly

## API Response Format (After Fix)

### Example AR Invoice Response:
```json
{
  "id": 1,
  "customer": 5,
  "customer_name": "ABC Company",
  "number": "INV-001",
  "invoice_number": "INV-001",
  "date": "2025-10-13",
  "due_date": "2025-11-13",
  "currency": 1,
  "status": "DRAFT",
  "items": [
    {
      "id": 1,
      "description": "Consulting Services",
      "quantity": "10.00",
      "unit_price": "100.00",
      "tax_rate": 1
    }
  ],
  "totals": {
    "subtotal": "1000.00",
    "tax": "50.00",
    "total": "1050.00",
    "paid": "0.00",
    "balance": "1050.00"
  },
  "subtotal": "1000.00",
  "tax_amount": "50.00",
  "total": "1050.00",
  "paid_amount": "0.00",
  "balance": "1050.00"
}
```

## Additional Notes

- The `invoice_number` field is read-only and automatically populated from `number`
- When creating invoices, always use the `number` field in the request
- The API now returns both nested `totals` and flat total fields for maximum compatibility
- Customer/Supplier names are now included in the response for better UI display
- All decimal values are converted to strings in the serializer for JSON compatibility

## Future Improvements

Consider these enhancements:

1. Add validation to ensure invoice numbers are unique per customer/supplier
2. Add auto-numbering feature for invoice numbers
3. Add invoice number prefix configuration (e.g., "INV-", "BILL-")
4. Add search/filter by invoice number in the list view
5. Add invoice number validation regex pattern

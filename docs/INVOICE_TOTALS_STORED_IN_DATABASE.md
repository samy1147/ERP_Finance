# Invoice Totals Stored in Database

## Summary
Invoice totals (subtotal, tax_amount, and total) are now **stored in the database** instead of being calculated dynamically on every request. This improves performance and ensures data consistency.

## Implementation Details

### Database Schema Changes

Added three new fields to both `ARInvoice` and `APInvoice` models:

```python
subtotal = models.DecimalField(
    max_digits=14, decimal_places=2, null=True, blank=True,
    help_text="Sum of all line items before tax"
)
tax_amount = models.DecimalField(
    max_digits=14, decimal_places=2, null=True, blank=True,
    help_text="Total tax amount calculated from all line items"
)
total = models.DecimalField(
    max_digits=14, decimal_places=2, null=True, blank=True,
    help_text="Total invoice amount (subtotal + tax)"
)
```

**Migration Files:**
- `ar/migrations/0010_arinvoice_subtotal_arinvoice_tax_amount_and_more.py`
- `ap/migrations/0010_apinvoice_subtotal_apinvoice_tax_amount_and_more.py`

### Model Methods

Added `calculate_and_save_totals()` method to both `ARInvoice` and `APInvoice`:

```python
def calculate_and_save_totals(self):
    """Calculate and save totals from line items to database"""
    subtotal = Decimal('0.00')
    tax_amount = Decimal('0.00')
    
    for item in self.items.all():
        subtotal += item.amount or Decimal('0.00')
        tax_amount += item.tax or Decimal('0.00')
    
    self.subtotal = subtotal
    self.tax_amount = tax_amount
    self.total = subtotal + tax_amount
    self.save(update_fields=['subtotal', 'tax_amount', 'total'])
```

This method:
1. Loops through all invoice items
2. Sums up amounts and tax
3. Saves totals to database
4. Uses `update_fields` for efficiency

### Serializer Updates

Updated `finance/serializers.py` to use stored values when available, with fallback to dynamic calculation:

#### AR Invoice Serializer

```python
def get_subtotal(self, obj):
    # Use stored value if available, otherwise calculate
    if obj.subtotal is not None:
        return obj.subtotal
    return ar_totals(obj)["subtotal"]

def get_tax_amount(self, obj):
    if obj.tax_amount is not None:
        return obj.tax_amount
    return ar_totals(obj)["tax"]

def get_total(self, obj):
    if obj.total is not None:
        return obj.total
    totals = ar_totals(obj)
    return totals["subtotal"] + totals["tax"]
```

#### AP Invoice Serializer

Same pattern as AR, using `ap_totals()` for fallback calculation.

### Automatic Total Calculation

Totals are automatically calculated and saved in these scenarios:

#### 1. Invoice Creation (`create()` method)
```python
def create(self, validated_data):
    # ... create invoice and items ...
    
    # Calculate and save totals to database
    inv.calculate_and_save_totals()
    
    return inv
```

#### 2. Invoice Update (`update()` method)
```python
def update(self, instance, validated_data):
    # ... update invoice and items ...
    
    # Calculate and save totals to database
    instance.calculate_and_save_totals()
    
    return instance
```

#### 3. Invoice Posting
In `finance/services.py`, both `gl_post_from_ar_balanced()` and `gl_post_from_ap_balanced()`:

```python
# Calculate and save totals to database before posting
inv.calculate_and_save_totals()
```

The `save()` call during posting includes the total fields:
```python
inv.save(update_fields=[
    "gl_journal", "posted_at", "is_posted", 
    "exchange_rate", "base_currency_total",
    "subtotal", "tax_amount", "total"
])
```

## Benefits

### Performance
- **Before**: Totals calculated on every API request by querying all items
- **After**: Totals read directly from database columns (single query)
- **Impact**: Faster API responses, especially for invoices with many items

### Data Consistency
- **Before**: Totals could theoretically differ if items changed between reads
- **After**: Totals are snapshots, consistent with the invoice state
- **Benefit**: Better for reporting, auditing, and historical analysis

### Backward Compatibility
- Fields are nullable (`null=True`)
- Serializers fall back to calculation if stored value is `None`
- Existing invoices will have `None` values until updated or posted
- No breaking changes to API contract

## Related Fields

The following fields are also stored for similar reasons:

### Exchange Rate Information
```python
exchange_rate = models.DecimalField(
    max_digits=12, decimal_places=6, null=True, blank=True,
    help_text="Exchange rate used for currency conversion"
)
base_currency_total = models.DecimalField(
    max_digits=14, decimal_places=2, null=True, blank=True,
    help_text="Total amount converted to base currency"
)
```

These are stored to preserve the **historical exchange rate** at the time of posting, ensuring accurate financial records even if exchange rates change later.

## Migration Path

### For Existing Invoices

Existing invoices will have `NULL` values for the new fields. They will be populated:

1. **Automatically** when the invoice is next updated
2. **Automatically** when the invoice is posted
3. **On-demand** via the serializer fallback (calculates if null)

### Manual Population (Optional)

If you want to populate totals for all existing invoices:

```python
from ar.models import ARInvoice
from ap.models import APInvoice

# Populate AR invoices
for inv in ARInvoice.objects.filter(total__isnull=True):
    inv.calculate_and_save_totals()
    print(f"Updated AR Invoice {inv.number}")

# Populate AP invoices
for inv in APInvoice.objects.filter(total__isnull=True):
    inv.calculate_and_save_totals()
    print(f"Updated AP Invoice {inv.number}")
```

## Testing

### Verify Database Storage

Check that totals are saved:

```python
from ar.models import ARInvoice

inv = ARInvoice.objects.get(number="INV-001")
print(f"Subtotal: {inv.subtotal}")
print(f"Tax: {inv.tax_amount}")
print(f"Total: {inv.total}")
```

### Verify API Response

Check that API returns correct values:

```bash
curl http://localhost:8000/api/ar/invoices/1/
```

Response should include:
```json
{
  "id": 1,
  "subtotal": "1000.00",
  "tax_amount": "150.00",
  "total": "1150.00",
  ...
}
```

### Verify Update Triggers Recalculation

1. Create an invoice with items
2. Check totals are saved
3. Update an item amount
4. Verify totals are recalculated

## Files Modified

### Models
- `ar/models.py` - Added fields and `calculate_and_save_totals()` method
- `ap/models.py` - Added fields and `calculate_and_save_totals()` method

### Serializers
- `finance/serializers.py` - Updated AR/AP serializers:
  - Modified `get_subtotal()`, `get_tax_amount()`, `get_total()` methods
  - Updated `create()` method to save totals
  - Updated `update()` method to save totals

### Services
- `finance/services.py` - Updated posting functions:
  - `gl_post_from_ar_balanced()` - Calculate totals before posting
  - `gl_post_from_ap_balanced()` - Calculate totals before posting
  - Both functions include new fields in `save(update_fields=...)`

### Migrations
- `ar/migrations/0010_arinvoice_subtotal_arinvoice_tax_amount_and_more.py`
- `ap/migrations/0010_apinvoice_subtotal_apinvoice_tax_amount_and_more.py`

## Design Philosophy

### Why Store Calculated Values?

1. **Performance**: Database queries are expensive, especially when calculating aggregates
2. **Historical Accuracy**: Invoice totals should reflect the state at creation/posting time
3. **Reporting**: Fast queries for financial reports without complex joins
4. **Consistency**: Single source of truth stored in database

### When to Recalculate?

Totals are recalculated whenever:
- Invoice items are created/updated/deleted
- Invoice is posted to GL
- Explicitly called via `calculate_and_save_totals()`

### Trade-offs

**Pros:**
- ✅ Faster API responses
- ✅ Simpler queries
- ✅ Historical data integrity
- ✅ Better for reporting

**Cons:**
- ❌ Additional database columns
- ❌ Need to maintain consistency (handled automatically)
- ❌ Slightly more complex update logic

## Future Considerations

### Data Migration
If needed, create a management command to populate totals for all existing invoices:

```python
# finance/management/commands/populate_invoice_totals.py
from django.core.management.base import BaseCommand
from ar.models import ARInvoice
from ap.models import APInvoice

class Command(BaseCommand):
    help = 'Populate total fields for all invoices'

    def handle(self, *args, **options):
        # Update AR invoices
        ar_count = 0
        for inv in ARInvoice.objects.filter(total__isnull=True):
            inv.calculate_and_save_totals()
            ar_count += 1
        
        # Update AP invoices
        ap_count = 0
        for inv in APInvoice.objects.filter(total__isnull=True):
            inv.calculate_and_save_totals()
            ap_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {ar_count} AR invoices and {ap_count} AP invoices'
            )
        )
```

### Validation
Consider adding validation to ensure stored totals match calculated totals:

```python
def validate_totals(self):
    """Validate that stored totals match calculated totals"""
    calculated = Decimal('0.00')
    calculated_tax = Decimal('0.00')
    
    for item in self.items.all():
        calculated += item.amount or Decimal('0.00')
        calculated_tax += item.tax or Decimal('0.00')
    
    if self.subtotal != calculated:
        raise ValidationError(f"Subtotal mismatch: stored={self.subtotal}, calculated={calculated}")
    
    if self.tax_amount != calculated_tax:
        raise ValidationError(f"Tax mismatch: stored={self.tax_amount}, calculated={calculated_tax}")
    
    if self.total != (calculated + calculated_tax):
        raise ValidationError(f"Total mismatch: stored={self.total}, calculated={calculated + calculated_tax}")
```

## Conclusion

Invoice totals are now stored in the database for better performance and data integrity. The implementation maintains backward compatibility and automatically updates totals whenever invoice items change.

**Status**: ✅ Implemented and Migrated

**Last Updated**: 2025-01-17

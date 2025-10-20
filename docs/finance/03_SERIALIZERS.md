# Finance Serializers Documentation (serializers.py)

## Overview
This file contains Django REST Framework serializers that convert between model instances and JSON data. It handles data validation, nested relationships, and computed fields for the Finance API.

---

## File Location
```
finance/serializers.py
```

---

## Imports & Dependencies
```python
from rest_framework import serializers
from decimal import Decimal
from finance.models import Account, JournalEntry, JournalLine, BankAccount, Invoice, InvoiceLine, TaxCode
from finance.services import ar_totals, ap_totals
from ar.models import ARInvoice, ARPayment
from ap.models import APInvoice, APPayment
```

---

## Serializers

### 1. `CurrencySerializer`

**Purpose:** Serializes Currency model from core app.

**Fields:** All fields from Currency model

**Usage:**
```python
{
  "id": 1,
  "code": "USD",
  "name": "US Dollar",
  "symbol": "$",
  "is_base": true
}
```

---

### 2. `AccountSerializer`

**Purpose:** Serializes GL Account information.

**Fields:**
- `id`: Account ID
- `code`: Account code (e.g., "1100")
- `name`: Account name (e.g., "Accounts Receivable")
- `type`: Account type (AS, LI, EQ, IN, EX)

**Usage:**
```python
{
  "id": 5,
  "code": "1100",
  "name": "Accounts Receivable",
  "type": "AS"
}
```

---

### 3. `JournalLineSerializer`

**Purpose:** Serializes individual journal entry lines.

**Fields:**
- `id`: Line ID
- `account`: Account ID (foreign key)
- `debit`: Debit amount
- `credit`: Credit amount

**Usage:**
```python
{
  "id": 1,
  "account": 5,
  "debit": "1050.00",
  "credit": "0.00"
}
```

---

### 4. `JournalEntrySerializer`

**Purpose:** Serializes journal entries with nested lines.

**Fields:**
- `id`: Entry ID
- `date`: Transaction date
- `currency`: Currency ID
- `memo`: Description
- `posted`: Boolean (read-only)
- `lines`: Array of JournalLineSerializer (nested)

**Read-only Fields:** `posted`

**Methods:**

#### `create(validated_data)`
**Purpose:** Creates journal entry with nested lines

**Logic:**
1. Extracts lines data from validated_data
2. Creates JournalEntry without lines
3. Creates each JournalLine linked to entry
4. Returns created entry

**Usage:**
```python
data = {
    "date": "2025-01-15",
    "currency": 1,
    "memo": "Invoice payment",
    "lines": [
        {"account": 1, "debit": "100.00", "credit": "0.00"},
        {"account": 2, "debit": "0.00", "credit": "100.00"}
    ]
}
serializer = JournalEntrySerializer(data=data)
if serializer.is_valid():
    entry = serializer.save()
```

---

### 5. `ARItemSerializer`

**Purpose:** Serializes Accounts Receivable invoice line items.

**Fields:**
- `id`: Item ID (read-only)
- `description`: Item description
- `quantity`: Quantity (as string for precision)
- `unit_price`: Price per unit
- `amount`: Calculated total (read-only)
- `tax_rate`: Tax rate ID (optional, nullable)
- `tax_amount`: Calculated tax (read-only)
- `account`: GL account ID (optional)

**Key Feature:** `tax_rate` is optional (`allow_null=True`) - items can have no tax

**Model:** ARItem

---

### 6. `ARInvoiceSerializer`

**Purpose:** Main serializer for Accounts Receivable invoices with advanced features.

**Fields:**
- `id`: Invoice ID (read-only)
- `customer`: Customer ID
- `customer_name`: Customer name (read-only)
- `invoice_number`: Invoice number (read-only, alias for 'number')
- `date`: Invoice date
- `due_date`: Payment due date
- `currency`: Currency ID
- `status`: DRAFT/POSTED/REVERSED
- `items`: Array of ARItemSerializer (nested)
- **Computed Totals** (all read-only):
  - `subtotal`: Sum of line amounts before tax
  - `tax_amount`: Total tax
  - `total`: Grand total
  - `paid_amount`: Amount paid
  - `balance`: Remaining balance

**Meta:**
- Model: ARInvoice
- Read-only fields: id, invoice_number, customer_name, subtotal, tax_amount, total, paid_amount, balance

**Key Methods:**

#### `validate(attrs)`
**Purpose:** Validates incoming data before creation

**Current Implementation:** Logs validation data for debugging

#### `_get_cached_totals(obj)`
**Purpose:** Caches totals calculation to avoid repeated service calls

**Logic:**
1. Checks if `_cached_totals` attribute exists on object
2. If not, calls `ar_totals(obj)` and caches result
3. Returns cached totals

**Why Important:** Without caching, each total field would call `ar_totals()` separately, resulting in 6x redundant calculations

#### `get_subtotal(obj)`, `get_tax_amount(obj)`, `get_total(obj)`, `get_paid_amount(obj)`, `get_balance(obj)`
**Purpose:** SerializerMethodField getters for computed totals

**Usage:** All call `_get_cached_totals()` to retrieve values efficiently

#### `create(validated_data)`
**Purpose:** Creates AR invoice with nested items

**Logic:**
1. Extracts items from validated_data
2. Filters out items with empty descriptions
3. Creates ARInvoice instance
4. Creates each ARItem linked to invoice
5. Counts created items
6. If no items created, deletes invoice and raises error
7. Returns created invoice

**Validation:**
- Rejects items with empty/whitespace descriptions
- Requires at least one valid item
- Deletes invoice if all items invalid

**Example:**
```python
data = {
    "customer": 1,
    "date": "2025-01-15",
    "due_date": "2025-02-15",
    "currency": 1,
    "items": [
        {
            "description": "Consulting Services",
            "quantity": "10",
            "unit_price": "100.00",
            "tax_rate": 1,
            "account": 5
        }
    ]
}
serializer = ARInvoiceSerializer(data=data)
if serializer.is_valid():
    invoice = serializer.save()
```

---

### 7. `ARPaymentSerializer`

**Purpose:** Serializes AR payments with validation.

**Fields:** All fields from ARPayment model

**Methods:**

#### `validate(data)`
**Purpose:** Validates payment before creation

**Checks:**
1. **Amount > 0:** Payment must be positive
2. **Invoice Posted:** Cannot pay draft invoice
3. **Payment <= Balance:** Cannot overpay

**Logic:**
```python
# Check amount
if amt <= 0:
    raise ValidationError("Payment amount must be positive.")

# Check invoice is posted
if invoice and not invoice.gl_journal:
    raise ValidationError("Cannot apply payment: invoice is not posted yet.")

# Check balance
totals = ar_totals(invoice)
existing = self.instance.amount if updating else 0
remaining = balance + existing
if amt > remaining:
    raise ValidationError(f"Payment exceeds invoice balance ({remaining:.2f}).")
```

**Example Error:**
```python
# This will fail
payment_data = {
    "invoice": 1,  # Balance is 100
    "amount": "150.00",  # Too much!
    "date": "2025-01-15"
}
# ValidationError: "Payment exceeds invoice balance (100.00)."
```

---

### 8. `APItemSerializer`

**Purpose:** Serializes Accounts Payable invoice line items.

**Fields:** Same as ARItemSerializer but for AP

**Model:** APItem

---

### 9. `APInvoiceSerializer`

**Purpose:** Main serializer for Accounts Payable invoices.

**Fields:** Similar to ARInvoiceSerializer but with:
- `supplier`: Supplier ID (instead of customer)
- `supplier_name`: Supplier name (read-only)

**Methods:** Same structure as ARInvoiceSerializer:
- `validate(attrs)`
- `_get_cached_totals(obj)`
- `get_subtotal()`, etc.
- `create(validated_data)`

**Key Difference:** Uses `ap_totals()` instead of `ar_totals()`

---

### 10. `APPaymentSerializer`

**Purpose:** Serializes AP payments with validation.

**Fields:** All fields from APPayment model

**Methods:**

#### `validate(data)`
**Purpose:** Validates payment before creation

**Same checks as ARPaymentSerializer:**
1. Amount > 0
2. Invoice posted
3. Payment <= balance

**Uses:** `ap_totals()` instead of `ar_totals()`

---

### 11. `JournalLineReadSerializer`

**Purpose:** Read-only serializer for journal lines with account details.

**Fields:**
- `id`: Line ID
- `account_code`: Account code (from related Account)
- `account_name`: Account name (from related Account)
- `debit`: Debit amount
- `credit`: Credit amount

**Usage:** Used in API responses to show human-readable account info

---

### 12. `JournalEntryReadSerializer`

**Purpose:** Read-only serializer for journal entries with nested lines.

**Fields:**
- `id`: Entry ID
- `date`: Transaction date
- `currency`: Nested currency object
- `memo`: Description
- `posted`: Boolean
- `lines`: Array of JournalLineReadSerializer (nested)

**Usage:** Returns detailed journal entry with all account information

---

### 13. `BankAccountSerializer`

**Purpose:** Serializes bank account information.

**Fields:** All fields from BankAccount model

---

### 14. `SeedVATRequestSerializer`

**Purpose:** Validates request to seed VAT tax rates.

**Fields:**
- `effective_from`: Date (optional)

**Usage:** Used in API endpoint to create standard VAT rates

---

### 15. `CorpTaxAccrualRequestSerializer`

**Purpose:** Validates corporate tax accrual requests.

**Fields:**
- `country`: Country code (required)
- `date_from`: Period start date (required)
- `date_to`: Period end date (required)
- `organization_id`: Organization ID (optional)

**Usage:** Used in API endpoint to calculate and accrue corporate tax

---

### 16. `InvoiceLineSerializer`

**Purpose:** Serializes invoice line items.

**Fields:** All fields from InvoiceLine model

---

### 17. `InvoiceSerializer`

**Purpose:** Serializes main Invoice model with nested lines.

**Fields:**
- Basic invoice fields
- `lines`: Array of InvoiceLineSerializer (nested)

**Methods:**

#### `validate(attrs)`
**Purpose:** Validates invoice data

**Checks:**
- At least one line item
- All lines have account and tax_code

#### `create(validated)`
**Purpose:** Creates invoice with nested lines

**Logic:**
1. Extracts lines data
2. Creates Invoice
3. Creates each InvoiceLine
4. Calls `invoice.recompute_totals()`
5. Saves and returns invoice

#### `update(instance, validated)`
**Purpose:** Updates invoice and its lines

**Logic:**
1. Updates invoice fields
2. Deletes all existing lines
3. Recreates lines from validated data
4. Recomputes totals
5. Saves and returns invoice

---

### 18. `ExchangeRateSerializer`

**Purpose:** Serializes foreign exchange rates.

**Fields:**
- `id`: Rate ID
- `from_currency`: Source currency object (nested, read-only)
- `to_currency`: Target currency object (nested, read-only)
- `rate`: Exchange rate
- `rate_date`: Date rate is effective
- `rate_type`: Type (SPOT, AVERAGE, etc.)

**Usage:**
```python
{
  "id": 1,
  "from_currency": {"code": "USD", "name": "US Dollar"},
  "to_currency": {"code": "EUR", "name": "Euro"},
  "rate": "0.85",
  "rate_date": "2025-01-15",
  "rate_type": "SPOT"
}
```

---

### 19. `ExchangeRateCreateSerializer`

**Purpose:** Validates exchange rate creation.

**Fields:**
- `from_currency`: Currency code (required)
- `to_currency`: Currency code (required)
- `rate`: Exchange rate (required)
- `rate_date`: Date (required)
- `rate_type`: Type (default: 'SPOT')

**Methods:**

#### `validate(data)`
**Purpose:** Validates exchange rate data

**Checks:**
1. Rate > 0
2. from_currency != to_currency
3. Prevents duplicate rates

---

### 20. `FXGainLossAccountSerializer`

**Purpose:** Serializes FX gain/loss account mappings.

**Fields:** All fields from FXGainLossAccount model

---

### 21. `CurrencyConversionRequestSerializer`

**Purpose:** Validates currency conversion requests.

**Fields:**
- `amount`: Amount to convert (required)
- `from_currency`: Source currency code (required)
- `to_currency`: Target currency code (required)
- `as_of_date`: Date for rate (optional)
- `rate_type`: Type (default: 'SPOT')

**Usage:** Used in API endpoint to convert amounts between currencies

---

## Key Features

### 1. Totals Caching
**Problem:** Without caching, serializing an invoice calls `ar_totals()` 6 times  
**Solution:** `_get_cached_totals()` caches the result on first call

**Performance Impact:**
- Without caching: 6 database queries per invoice
- With caching: 1 database query per invoice

### 2. Empty Description Filtering
**Problem:** Frontend sends empty strings for unused item rows  
**Solution:** `create()` method filters: `if item.get('description', '').strip()`

### 3. Nested Serializers
**Pattern:** Invoice → Items relationship handled automatically

**Benefits:**
- Create invoice and items in single API call
- Atomic transactions (all or nothing)
- Cleaner API interface

### 4. Read-only Computed Fields
**Examples:**
- `invoice_number`: Alias for `number` field
- `customer_name`: From related Customer
- `subtotal`, `tax_amount`, `total`: Calculated from items

**Why:** Frontend needs these but shouldn't send them

### 5. Validation at Multiple Levels
- **Field level:** Data types, formats
- **Object level:** Business rules (positive amounts, posted invoices, etc.)
- **Cross-field:** Payment <= balance, etc.

---

## Common Patterns

### Creating Nested Objects
```python
# Single API call creates invoice + items
data = {
    "customer": 1,
    "date": "2025-01-15",
    "items": [
        {"description": "Item 1", "quantity": "1", "unit_price": "100"},
        {"description": "Item 2", "quantity": "2", "unit_price": "50"}
    ]
}
serializer = ARInvoiceSerializer(data=data)
if serializer.is_valid():
    invoice = serializer.save()  # Creates invoice + 2 items
```

### Validation Errors
```python
serializer = ARPaymentSerializer(data=invalid_data)
if not serializer.is_valid():
    print(serializer.errors)
    # {'amount': ['Payment exceeds invoice balance (100.00).']}
```

### Using Computed Fields
```python
invoice = ARInvoice.objects.get(id=1)
serializer = ARInvoiceSerializer(invoice)
print(serializer.data)
# {
#     "id": 1,
#     "invoice_number": "INV-001",
#     "customer_name": "Acme Corp",
#     "subtotal": "1000.00",
#     "tax_amount": "50.00",
#     "total": "1050.00",
#     ...
# }
```

---

## Best Practices

### 1. Use Caching for Expensive Calculations
✅ **DO:** Cache repeated service calls like `ar_totals()`  
❌ **DON'T:** Call service functions multiple times

### 2. Filter Invalid Data Early
✅ **DO:** Remove empty descriptions in `create()`  
❌ **DON'T:** Let invalid data reach the database

### 3. Validate Business Rules
✅ **DO:** Check payment <= balance in `validate()`  
❌ **DON'T:** Rely only on database constraints

### 4. Use Read-only Serializers for Responses
✅ **DO:** Use `JournalEntryReadSerializer` with nested account details  
❌ **DON'T:** Return raw IDs that require additional API calls

### 5. Atomic Transactions
✅ **DO:** Create parent and children in single transaction  
❌ **DON'T:** Create parent, then create children separately

---

## Conclusion

The Finance serializers provide:

✅ **Data Validation:** Comprehensive checks before saving  
✅ **Nested Creation:** Create complex objects in single API call  
✅ **Computed Fields:** Automatic totals calculation  
✅ **Performance:** Caching prevents redundant calculations  
✅ **Error Handling:** Clear validation messages  
✅ **Read-only Views:** Detailed responses with related data  
✅ **Business Logic:** Payment validation, balance checks  

The serializers act as the bridge between HTTP requests and database models, ensuring data integrity and providing a clean API interface for the frontend.

---

**Last Updated:** October 13, 2025  
**Framework:** Django REST Framework 3.x+  
**Python Version:** 3.10+

# Invoice Creation Fix - Summary

## Problem
AR and AP invoice creation wasn't working due to:
1. **Field name mismatch**: Frontend sent `invoice_number` but backend expected `number`
2. **No dropdown for customers/suppliers**: Users had to manually enter IDs
3. **No currency selector**: Hard-coded currency ID

## Changes Made

### Backend Changes

#### 1. Created Currency API (`finance/serializers.py`)
```python
class CurrencySerializer(serializers.ModelSerializer):
    class Meta: 
        model = Currency
        fields = ["id", "code", "name", "symbol", "is_base"]
```

#### 2. Created CurrencyViewSet (`finance/api.py`)
```python
class CurrencyViewSet(viewsets.ModelViewSet):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()
    filterset_fields = ["code", "is_base"]
```

#### 3. Registered Currency Endpoint (`erp/urls.py`)
```python
router.register(r"currencies", CurrencyViewSet)
```

### Frontend Changes

#### 1. Added currenciesAPI (`frontend/src/services/api.ts`)
```typescript
export const currenciesAPI = {
  list: () => api.get<Currency[]>('/currencies/'),
  get: (id: number) => api.get<Currency>(`/currencies/${id}/`),
  create: (data: Partial<Currency>) => api.post<Currency>('/currencies/', data),
  update: (id: number, data: Partial<Currency>) => api.patch<Currency>(`/currencies/${id}/`, data),
  delete: (id: number) => api.delete(`/currencies/${id}/`),
};
```

#### 2. Fixed AR Invoice Creation Form (`frontend/src/app/ar/invoices/new/page.tsx`)

**Before:**
```typescript
const [formData, setFormData] = useState({
  customer: '',
  invoice_number: '',  // ❌ Wrong field name
  // ...
});
```

**After:**
```typescript
const [formData, setFormData] = useState({
  customer: '',
  number: '',  // ✅ Correct field name
  // ...
});

// Added state for dropdowns
const [customers, setCustomers] = useState<Customer[]>([]);
const [currencies, setCurrencies] = useState<Currency[]>([]);

// Added fetch functions
useEffect(() => {
  fetchCustomers();
  fetchCurrencies();
}, []);
```

**Form Fields Changed:**
- Customer: Number input → Dropdown with customer names
- Currency: Hidden field → Dropdown with currency codes
- Invoice Number: Changed from `invoice_number` to `number`

#### 3. Fixed AP Invoice Creation Form (`frontend/src/app/ap/invoices/new/page.tsx`)

Same changes as AR Invoice:
- Supplier: Number input → Dropdown with supplier names
- Currency: Hidden field → Dropdown with currency codes
- Invoice Number: Changed from `invoice_number` to `number`

## How It Works Now

### AR Invoice Creation (`/ar/invoices/new`)
1. Page loads and fetches:
   - List of customers from `/api/customers/`
   - List of currencies from `/api/currencies/`
2. User selects from dropdowns:
   - Customer (shows customer name)
   - Currency (shows "USD - US Dollar", etc.)
3. User fills invoice number, dates, and line items
4. On submit, sends to API:
   ```json
   {
     "customer": 1,
     "number": "INV-001",
     "date": "2025-10-12",
     "due_date": "2025-11-12",
     "currency": 1,
     "items": [...]
   }
   ```

### AP Invoice Creation (`/ap/invoices/new`)
Same flow but with suppliers instead of customers.

## API Endpoints

### New Endpoint
- `GET /api/currencies/` - List all currencies
- `GET /api/currencies/{id}/` - Get currency details

### Updated Endpoints
- `POST /api/ar/invoices/` - Now accepts `number` field (not `invoice_number`)
- `POST /api/ap/invoices/` - Now accepts `number` field (not `invoice_number`)

## Testing Steps

### 1. Check Currencies Exist
```bash
# Go to Django admin
http://127.0.0.1:8000/admin/core/currency/

# Or test API
curl http://127.0.0.1:8000/api/currencies/
```

If no currencies exist, create one:
- Code: USD
- Name: US Dollar
- Symbol: $
- Is Base: ✓

### 2. Check Customers/Suppliers Exist
```bash
# Customers
curl http://127.0.0.1:8000/api/customers/

# Suppliers
curl http://127.0.0.1:8000/api/suppliers/
```

If none exist, create test data:
- Go to `/customers` page and create a customer
- Go to `/suppliers` page and create a supplier

### 3. Test AR Invoice Creation
1. Go to http://localhost:3000/ar/invoices
2. Click "New Invoice"
3. Should see:
   - Customer dropdown (not a number input)
   - Invoice Number text field
   - Date pickers
   - Currency dropdown (not hidden)
4. Select a customer, enter invoice details
5. Add line items
6. Click "Create Invoice"
7. Should redirect to invoice list with success message

### 4. Test AP Invoice Creation
Same steps but at http://localhost:3000/ap/invoices

## Common Issues & Solutions

### Issue: "Failed to load customers"
**Cause:** No customers in database
**Solution:** Create a customer at http://localhost:3000/customers

### Issue: "Failed to load suppliers"
**Cause:** No suppliers in database
**Solution:** Create a supplier at http://localhost:3000/suppliers

### Issue: "Failed to load currencies"
**Cause:** Currency API not responding
**Solution:** 
1. Check Django is running: http://127.0.0.1:8000/api/currencies/
2. Check currency exists in admin: http://127.0.0.1:8000/admin/core/currency/

### Issue: "Failed to create invoice"
**Possible Causes:**
1. Selected customer/supplier doesn't exist
2. Invalid date format
3. No line items added
4. Currency doesn't exist

**Debug:**
Open browser console (F12) → Network tab → Look at the failed POST request to see the exact error message

## Files Modified

### Backend
1. `finance/serializers.py` - Added CurrencySerializer
2. `finance/api.py` - Added CurrencyViewSet
3. `erp/urls.py` - Registered currencies endpoint

### Frontend
1. `frontend/src/services/api.ts` - Added currenciesAPI
2. `frontend/src/app/ar/invoices/new/page.tsx` - Fixed field names, added dropdowns
3. `frontend/src/app/ap/invoices/new/page.tsx` - Fixed field names, added dropdowns

## Next Steps

### Recommended Improvements
1. **Auto-generate invoice numbers** - Add a "Generate" button next to invoice number field
2. **Show customer balance** - Display outstanding balance when customer is selected
3. **Tax rate selection** - Add dropdown for tax rates on line items
4. **Invoice templates** - Save and reuse common invoice structures
5. **Duplicate invoice** - Add "Copy" button on invoice list to duplicate an existing invoice

### Future Features
- Bulk invoice creation
- Import from CSV
- Invoice templates
- Recurring invoices
- Email invoices to customers/suppliers

## Summary

✅ **Fixed:** Field name mismatch (`invoice_number` → `number`)
✅ **Added:** Customer/Supplier dropdowns
✅ **Added:** Currency dropdown
✅ **Added:** Currency API endpoint
✅ **Improved:** User experience with proper selectors

**The invoice creation forms now work correctly!** 🎉

# Quick Test Guide - Invoice Creation

## ✅ Fixed Issues

The AR and AP invoice creation forms have been fixed! Here's what changed:

### Problems That Were Fixed:
1. ❌ **Field name error**: Backend expected `number` but frontend sent `invoice_number`
2. ❌ **No customer dropdown**: Had to manually type customer ID
3. ❌ **No supplier dropdown**: Had to manually type supplier ID
4. ❌ **No currency selector**: Currency was hidden

### What Works Now:
1. ✅ **Customer dropdown** in AR invoices - Select from list of customers
2. ✅ **Supplier dropdown** in AP invoices - Select from list of suppliers
3. ✅ **Currency dropdown** - Select currency (USD, EUR, etc.)
4. ✅ **Correct field name** - Uses `number` field correctly

## 🧪 How to Test

### Step 1: Start the System
```powershell
cd C:\Users\samys\FinanceERP
.\start_system.bat
```

Wait for both servers to start:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

### Step 2: Create Test Data (if needed)

#### Create a Customer:
1. Go to http://localhost:3000/customers
2. Click "New Customer"
3. Fill in:
   - Name: Test Customer Inc.
   - Email: customer@test.com
4. Click "Create"

#### Create a Supplier:
1. Go to http://localhost:3000/suppliers
2. Click "New Supplier"
3. Fill in:
   - Name: Test Supplier Co.
   - Email: supplier@test.com
4. Click "Create"

#### Check Currency Exists:
1. Go to http://127.0.0.1:8000/admin/core/currency/
2. If no currencies exist, create one:
   - Code: USD
   - Name: US Dollar  
   - Symbol: $
   - Is base: ✓ (checked)

### Step 3: Test AR Invoice Creation

1. **Navigate to AR Invoices:**
   - Go to http://localhost:3000/ar/invoices
   - Click "New Invoice" button

2. **Fill the form:**
   - **Customer**: Select from dropdown (e.g., "Test Customer Inc.")
   - **Invoice Number**: Enter "INV-001"
   - **Invoice Date**: Select today's date
   - **Due Date**: Select future date
   - **Currency**: Select "USD - US Dollar"

3. **Add Line Items:**
   - Description: "Consulting Services"
   - Quantity: 10
   - Unit Price: 150
   - Click "Add Item" if you want more lines

4. **Submit:**
   - Click "Create Invoice"
   - Should redirect to invoice list
   - You should see a green success message

### Step 4: Test AP Invoice Creation

Same steps but at http://localhost:3000/ap/invoices:
1. Click "New Invoice"
2. Select **Supplier** from dropdown
3. Fill invoice details
4. Add line items
5. Create invoice

## 🔍 Troubleshooting

### "Failed to load customers"
**Problem:** No customers in database  
**Fix:** Go to http://localhost:3000/customers and create one

### "Failed to load suppliers"
**Problem:** No suppliers in database  
**Fix:** Go to http://localhost:3000/suppliers and create one

### "Failed to load currencies"
**Problem:** Currency API not working or no currencies exist  
**Fix:** 
1. Check Django admin: http://127.0.0.1:8000/admin/core/currency/
2. Create a currency (USD recommended)

### Dropdown is empty
**Problem:** No data exists yet  
**Fix:** Create customers/suppliers/currencies first

### "Failed to create invoice"
**Debug steps:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for error messages
4. Go to Network tab
5. Find the failed POST request
6. Check the Response tab for error details

Common causes:
- No items added to invoice
- Invalid customer/supplier ID
- Invalid currency ID
- Required fields missing

## 🎯 Expected Behavior

### AR Invoice Form Should Show:
```
┌─────────────────────────────────────┐
│ Customer: [Select...           ▼]  │
│ Invoice Number: [INV-001]          │
│ Invoice Date: [2025-10-12]         │
│ Due Date: [2025-11-12]             │
│ Currency: [USD - US Dollar    ▼]   │
├─────────────────────────────────────┤
│ Line Items:                         │
│ Description | Qty | Price | Total   │
│ [Service   ] [10] [150 ] $1500.00  │
│                    [+ Add Item]     │
├─────────────────────────────────────┤
│ Total: $1,500.00                    │
│ [Create Invoice] [Cancel]           │
└─────────────────────────────────────┘
```

### AP Invoice Form Should Show:
Same layout but with "Supplier" instead of "Customer"

## ✨ New Features

1. **Smart Dropdowns**
   - Type to search in dropdowns
   - Shows customer/supplier names (not just IDs)
   - Shows currency code and name

2. **Real-time Total**
   - Total calculates as you add items
   - Updates when you change quantity or price

3. **Validation**
   - Can't submit without customer/supplier
   - Can't submit without line items
   - Must have valid dates

## 📝 API Endpoints Being Used

### New Endpoint:
- `GET /api/currencies/` - Returns list of currencies

### Existing Endpoints:
- `GET /api/customers/` - Returns list of customers
- `GET /api/suppliers/` - Returns list of suppliers
- `POST /api/ar/invoices/` - Creates AR invoice
- `POST /api/ap/invoices/` - Creates AP invoice

## ✅ Success Checklist

Test AR Invoice:
- [ ] Navigate to /ar/invoices/new
- [ ] See customer dropdown (not number input)
- [ ] See currency dropdown
- [ ] Select a customer
- [ ] Enter invoice number
- [ ] Add at least one line item
- [ ] Click "Create Invoice"
- [ ] See success message
- [ ] Redirected to invoice list
- [ ] New invoice appears in list with status "DRAFT"

Test AP Invoice:
- [ ] Navigate to /ap/invoices/new
- [ ] See supplier dropdown (not number input)
- [ ] See currency dropdown
- [ ] Select a supplier
- [ ] Enter invoice number
- [ ] Add at least one line item
- [ ] Click "Create Invoice"
- [ ] See success message
- [ ] Redirected to invoice list
- [ ] New invoice appears in list with status "DRAFT"

## 🚀 You're All Set!

Invoice creation now works properly with:
- ✅ Customer/Supplier dropdowns
- ✅ Currency selector
- ✅ Correct field names
- ✅ Proper validation
- ✅ Success notifications

Happy invoicing! 💰

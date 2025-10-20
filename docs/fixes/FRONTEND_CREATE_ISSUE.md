# Frontend Create Issue - Diagnosis & Fix

## Problem

The create functionality is not working in the frontend for AR/AP invoices and payments.

## Likely Causes

### 1. Backend Not Running
- **Symptom:** "Network Error" or "Failed to fetch"
- **Solution:** Ensure Django is running on http://localhost:8000
- **Check:** Run `Get-Process | Where-Object {$_.ProcessName -eq "python"}`
- **Start:** Run `.\venv\Scripts\python.exe manage.py runserver`

### 2. Missing Required Data
The forms require:
- **Customer ID** for AR invoices/payments
- **Supplier ID** for AP invoices/payments
- **Currency ID** (defaults to 1)
- **Account IDs** for line items

### 3. Customer/Supplier IDs Unknown
- **Problem:** Forms ask for "Customer ID" but users don't know the IDs
- **Solution:** You need to create customers/suppliers first in Django Admin

## Quick Fix Steps

### Step 1: Start Django Backend
```powershell
cd C:\Users\samys\FinanceERP
.\venv\Scripts\python.exe manage.py runserver
```

Keep this terminal open!

### Step 2: Create Test Data via Django Admin

1. Open http://localhost:8000/admin/
2. Login with Django admin credentials
3. Create at least one Customer:
   - Go to "CRM" → "Customers" → "Add Customer"
   - Fill in name, email, etc.
   - **Note the ID** (it will be shown after saving)
   
4. Create at least one Supplier:
   - Go to "CRM" → "Suppliers" → "Add Supplier"
   - Fill in name, contact info
   - **Note the ID**

5. Verify you have Accounts:
   - Go to "Core" → "Accounts"
   - Should have accounts like "Accounts Receivable", "Sales Revenue", etc.

### Step 3: Use the Frontend

Now you can create invoices:
1. Go to http://localhost:3000/ar/invoices/new
2. Enter the **Customer ID** you noted from step 2
3. Fill in invoice details
4. Add line items
5. Click "Create Invoice"

## Testing Checklist

Before creating invoices/payments, verify:

✅ Django backend is running (check terminal)
✅ Frontend is running on port 3000
✅ At least one Customer exists (for AR)
✅ At least one Supplier exists (for AP)
✅ Chart of Accounts has been set up
✅ Currency exists (ID 1 = default currency)
✅ Bank accounts created (for payments)

## Common Errors & Solutions

### Error: "Customer with ID X does not exist"
**Solution:** Create a customer in Django Admin first

### Error: "Invalid currency"
**Solution:** Create a currency or use ID 1

### Error: "Network Error"
**Solution:** Start Django backend

### Error: "CORS error"
**Solution:** Already configured, but if you see this:
1. Check `erp/settings.py` has `corsheaders` in INSTALLED_APPS
2. Check `CORS_ALLOWED_ORIGINS` includes `http://localhost:3000`

### Error: "Account with ID X does not exist"
**Solution:** Create a proper Chart of Accounts first

## Better Solution (Future Enhancement)

The forms should:
1. Fetch and display customers/suppliers in a dropdown
2. Fetch and display accounts in dropdowns
3. Show friendly names instead of IDs
4. Validate data exists before submission

Would you like me to implement these improvements?

## Quick Test Commands

### Check if Django is running:
```powershell
curl http://localhost:8000/api/accounts/
```

### Check if customers exist:
```powershell
curl http://localhost:8000/admin/crm/customer/
```

## Need Help?

Tell me:
1. What error message you see (exact text)
2. Where you see it (browser console, toast notification, etc.)
3. What you were trying to create (AR invoice, AP payment, etc.)

I'll provide a specific fix!

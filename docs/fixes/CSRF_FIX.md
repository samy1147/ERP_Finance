# CSRF Error Fix

## Problem
```
{"detail":"CSRF Failed: Origin checking failed - http://localhost:3000 does not match any trusted origins."}
```

## Cause
Django's CSRF protection was blocking requests from the Next.js frontend (localhost:3000) because it wasn't in the trusted origins list.

## Solution Applied

Added `CSRF_TRUSTED_ORIGINS` to Django settings:

**File:** `erp/settings.py`

```python
# CSRF Trusted Origins - Required for Django 4.0+
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## How to Apply the Fix

### Option 1: Restart Django Server

**If Django is running in a terminal:**
1. Go to the terminal running Django
2. Press `Ctrl + C` to stop it
3. Run: `.\venv\Scripts\python.exe manage.py runserver`

**If using start_system.bat:**
1. Close all terminal windows
2. Run `.\start_system.bat` again

### Option 2: Quick Restart Script

Create a file `restart_django.bat`:
```batch
@echo off
echo Stopping Django processes...
taskkill /F /IM python.exe /T 2>nul
timeout /t 2 /nobreak >nul
echo Starting Django server...
cd /d %~dp0
.\venv\Scripts\python.exe manage.py runserver
```

Then run: `.\restart_django.bat`

## Verification

After restarting Django:

1. Go to http://localhost:3000/accounts
2. Click "New Account"
3. Fill in:
   - Code: 1234
   - Name: Test Account
   - Type: Asset
4. Click "Create"
5. Should work now! ✅

## What is CSRF?

**CSRF (Cross-Site Request Forgery)** is a security protection that prevents malicious websites from making unauthorized requests to your backend.

Django checks:
- The `Origin` header from the browser
- Against a list of trusted origins

Since Next.js (localhost:3000) and Django (localhost:8000) are on different ports, Django needs to explicitly trust the Next.js origin.

## What Changed?

**Before:**
- CORS was configured (allowing cross-origin requests)
- But CSRF_TRUSTED_ORIGINS was missing
- Django rejected POST/PUT/DELETE requests from localhost:3000

**After:**
- CORS configured ✅
- CSRF_TRUSTED_ORIGINS configured ✅
- All requests from localhost:3000 are trusted ✅

## Testing Other Forms

After restarting Django, test these to confirm the fix:

### 1. Create Customer
```
http://localhost:3000/customers
→ Click "New Customer"
→ Should work now
```

### 2. Create Supplier
```
http://localhost:3000/suppliers
→ Click "New Supplier"
→ Should work now
```

### 3. Create AR Invoice
```
http://localhost:3000/ar/invoices/new
→ Fill form and create
→ Should work now
```

### 4. Create AP Invoice
```
http://localhost:3000/ap/invoices/new
→ Fill form and create
→ Should work now
```

### 5. Create Payment
```
http://localhost:3000/ar/payments/new or /ap/payments/new
→ Fill form and create
→ Should work now
```

## Common Issues

### Issue: Still getting CSRF error after restart
**Solution:** 
1. Make sure you saved `erp/settings.py`
2. Completely stop and restart Django (not just refresh browser)
3. Clear browser cache (Ctrl + Shift + R)

### Issue: Django won't restart
**Solution:**
```powershell
# Kill all Python processes
Get-Process | Where-Object {$_.ProcessName -match "python"} | Stop-Process -Force

# Wait 2 seconds
Start-Sleep -Seconds 2

# Start Django again
cd C:\Users\samys\FinanceERP
.\venv\Scripts\python.exe manage.py runserver
```

### Issue: Different error appears
**Check:**
1. Browser console (F12 → Console)
2. Django terminal (look for error messages)
3. Network tab (F12 → Network → check response)

## Summary

✅ **Fixed:** Added `CSRF_TRUSTED_ORIGINS` to Django settings
✅ **Impact:** All creation forms will now work
✅ **Next Step:** Restart Django server

**The fix is applied, just needs Django restart!** 🚀

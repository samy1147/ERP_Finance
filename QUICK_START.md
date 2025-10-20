# Finance ERP - Quick Start Guide

## 🚀 Fastest Way to Start

### Option 1: Start Everything at Once (Recommended)
```cmd
start_system.bat
```
This will:
1. Start Django backend on port 8000
2. Start Next.js frontend on port 3000
3. Open your browser to http://localhost:3000

### Option 2: Start Individually
```cmd
start_django.bat    # Backend
start_frontend.bat  # Frontend
```

## 📍 Important URLs

- **Frontend (Main UI):** http://localhost:3000
- **Backend API:** http://localhost:8000/api
- **API Documentation:** http://localhost:8000/api/docs/
- **Django Admin:** http://localhost:8000/admin/

## 🗺️ Navigation Map

```
Frontend (http://localhost:3000)
│
├── 📊 Dashboard (/)
│   └── Quick links to all modules
│
├── 📖 Chart of Accounts (/accounts)
│   └── View all GL accounts
│
├── 📄 AR Invoices (/ar/invoices)
│   ├── List all invoices
│   ├── Create new (/ar/invoices/new)
│   └── Post to GL
│
├── 💵 AR Payments (/ar/payments)
│   ├── List all payments
│   ├── Receive payment (/ar/payments/new)
│   └── Post payment
│
├── 📋 AP Invoices (/ap/invoices)
│   ├── List all invoices
│   ├── Create new (/ap/invoices/new)
│   └── Post to GL
│
├── 💳 AP Payments (/ap/payments)
│   ├── List all payments
│   ├── Make payment (/ap/payments/new)
│   └── Post payment
│
└── 📈 Reports (/reports)
    ├── Trial Balance
    ├── AR Aging
    └── AP Aging
    (All with CSV/Excel export)
```

## 🎯 Common Tasks

### Create and Post an AR Invoice
1. Go to `/ar/invoices/new`
2. Fill in customer ID, invoice number, dates
3. Add line items (description, quantity, price)
4. Click "Create Invoice"
5. Go back to `/ar/invoices`
6. Click "Post to GL" on your invoice
7. Status changes from DRAFT → POSTED

### Receive a Customer Payment
1. Go to `/ar/payments/new`
2. Enter customer ID
3. Enter payment amount and date
4. Optional: Enter reference number, bank account
5. Click "Create Payment"
6. Go to `/ar/payments`
7. Click "Post" to finalize

### Run a Trial Balance Report
1. Go to `/reports`
2. Click "Trial Balance" tab
3. Set date range (optional)
4. Click "View Report"
5. Click "Export CSV" or "Export Excel" to download

### View Aging Reports
1. Go to `/reports`
2. Click "AR Aging" or "AP Aging" tab
3. Set "As Of Date"
4. Click "View Report"
5. See aging buckets (Current, 30, 60, 90, 90+ days)
6. Export if needed

## 💡 Tips & Tricks

### Keyboard Shortcuts
- `Ctrl + C` in terminal = Stop server
- `F5` in browser = Refresh page
- `Ctrl + Shift + I` = Open browser console (for debugging)

### Development
- Code changes auto-reload (both Django and Next.js)
- Check browser console for JavaScript errors
- Check terminal for backend errors
- TypeScript errors show in VS Code

### Data Entry
- Customer/Supplier IDs must exist in database
- Currency ID defaults to 1 (create currencies in Django admin if needed)
- Invoice numbers should be unique
- Dates are in YYYY-MM-DD format

### Status Flow
```
DRAFT → (Post) → POSTED → (Reverse) → REVERSED
```
- DRAFT: Editable, not in GL
- POSTED: In GL, cannot edit
- REVERSED: Cancelled entry in GL

## 🐛 Troubleshooting

### Frontend won't start
```cmd
cd frontend
npm install
npm run dev
```

### Backend won't start
```cmd
python manage.py migrate
python manage.py runserver
```

### API Connection Error
- Check backend is running on port 8000
- Check `frontend/.env.local` has correct URL
- Check CORS settings in Django settings.py

### Port Already in Use
```cmd
# Find process on port 8000 or 3000
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill process
taskkill /PID <process_id> /F
```

### Data Not Showing
- Check browser console for errors
- Verify backend API returns data: http://localhost:8000/api/accounts/
- Check Django admin for data in database

## 📊 Test Data Setup

### Option 1: Django Admin
1. Go to http://localhost:8000/admin/
2. Create superuser if needed: `python manage.py createsuperuser`
3. Add Accounts, Customers, Suppliers manually

### Option 2: Django Shell
```python
python manage.py shell

from core.models import Currency
from ar.models import Customer
from ap.models import Supplier
from finance.models import Account

# Create currency
Currency.objects.create(code="USD", name="US Dollar", symbol="$")

# Create customer
Customer.objects.create(name="ACME Corp", email="acme@example.com")

# Create supplier
Supplier.objects.create(name="Office Supplies Inc", email="supplies@example.com")

# Create accounts
Account.objects.create(code="1000", name="Cash", type="AS")
Account.objects.create(code="1200", name="Accounts Receivable", type="AS")
Account.objects.create(code="2000", name="Accounts Payable", type="LI")
Account.objects.create(code="4000", name="Sales Revenue", type="IN")
Account.objects.create(code="5000", name="Cost of Goods Sold", type="EX")
```

## 📚 File Structure Quick Reference

```
FinanceERP/
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/          # Pages
│   │   ├── components/   # Reusable components
│   │   ├── services/     # API calls
│   │   └── types/        # TypeScript types
│   ├── package.json
│   └── README.md
├── finance/              # Django finance app
├── ar/                   # Accounts Receivable app
├── ap/                   # Accounts Payable app
├── core/                 # Core models (Currency, etc)
├── erp/                  # Django project settings
├── manage.py
├── requirements.txt
├── db.sqlite3           # SQLite database
├── start_system.bat     # Start everything
├── start_django.bat     # Backend only
├── start_frontend.bat   # Frontend only
├── SETUP_GUIDE.md       # Full setup instructions
├── PROJECT_SUMMARY.md   # Complete documentation
└── QUICK_START.md       # This file
```

## 🔧 Configuration Files

### Backend
- `erp/settings.py` - Django settings (CORS, DB, etc)
- `erp/urls.py` - API routes
- `requirements.txt` - Python packages

### Frontend
- `frontend/package.json` - Node.js packages
- `frontend/.env.local` - API URL
- `frontend/tsconfig.json` - TypeScript config
- `frontend/tailwind.config.js` - Styling config

## ✅ Health Check

To verify system is working:

1. **Backend Health:**
   ```
   http://localhost:8000/api/
   Should return: {"accounts": "...", "ar": "...", ...}
   ```

2. **Frontend Health:**
   ```
   http://localhost:3000/
   Should show: Finance ERP Dashboard
   ```

3. **Database Health:**
   ```cmd
   python manage.py check
   Should return: System check identified no issues
   ```

## 🎓 Learn More

- **Django REST Framework:** https://www.django-rest-framework.org/
- **Next.js Documentation:** https://nextjs.org/docs
- **Tailwind CSS:** https://tailwindcss.com/docs
- **TypeScript:** https://www.typescriptlang.org/docs/

## 📞 Need Help?

1. Check `SETUP_GUIDE.md` for detailed instructions
2. Check `PROJECT_SUMMARY.md` for complete documentation
3. Review browser console and terminal logs
4. Verify all prerequisites are installed
5. Ensure both servers are running

## 🎉 You're Ready!

Your Finance ERP system is complete and ready to use. Start with:

1. Run `start_system.bat`
2. Open http://localhost:3000
3. Explore the dashboard
4. Create your first invoice!

**Happy accounting! 📊💰**

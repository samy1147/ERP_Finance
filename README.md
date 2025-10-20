# Finance ERP System

A complete Enterprise Resource Planning system for financial management, featuring General Ledger (GL), Accounts Receivable (AR), and Accounts Payable (AP) modules with a modern web interface.

## 🚀 Quick Start

### Fastest Way to Start (Windows)

```cmd
start_system.bat
```

This single command will:
1. ✅ Start Django backend (http://localhost:8000)
2. ✅ Start Next.js frontend (http://localhost:3000)
3. ✅ Open your browser automatically

### First Time Setup

```cmd
# 1. Check prerequisites
check_system.bat

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Setup database
python manage.py migrate

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Start the system
start_system.bat
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[QUICK_START.md](QUICK_START.md)** | 5-minute quick reference guide |
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Complete installation instructions |
| **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** | Full technical documentation |
| **[frontend/README.md](frontend/README.md)** | Frontend-specific documentation |

## 🎯 Features

### ✅ Core Modules
- **Chart of Accounts** - Manage GL accounts with filtering and search
- **AR Invoices** - Create and manage customer invoices
- **AR Payments** - Record customer payments
- **AP Invoices** - Create and manage supplier invoices
- **AP Payments** - Record supplier payments
- **Financial Reports** - Trial Balance, AR Aging, AP Aging

### ✅ Key Capabilities
- Post transactions to General Ledger
- Multi-currency support (backend ready)
- Automated journal entries
- Tax calculation and tracking
- CSV/Excel report exports
- Real-time data synchronization
- Responsive mobile-friendly design

## 🏗️ Architecture

```
┌─────────────────────────────┐
│   Next.js Frontend          │
│   http://localhost:3000     │
│   - React Components        │
│   - TypeScript              │
│   - Tailwind CSS            │
└──────────┬──────────────────┘
           │ REST API
           ↓
┌─────────────────────────────┐
│   Django Backend            │
│   http://localhost:8000     │
│   - REST Framework          │
│   - Business Logic          │
│   - Django ORM              │
└──────────┬──────────────────┘
           │ ORM
           ↓
┌─────────────────────────────┐
│   SQLite/PostgreSQL         │
│   - Accounts                │
│   - Invoices                │
│   - Payments                │
│   - Journal Entries         │
└─────────────────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **Django 5.1.1** - Web framework
- **Django REST Framework** - API framework
- **SQLite/PostgreSQL** - Database
- **django-cors-headers** - CORS support
- **drf-spectacular** - API documentation

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **React Hook Form** - Form handling
- **date-fns** - Date utilities

## 📁 Project Structure

```
FinanceERP/
├── 📂 frontend/              # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Pages (Dashboard, Accounts, AR, AP, Reports)
│   │   ├── components/      # Reusable React components
│   │   ├── services/        # API integration layer
│   │   └── types/           # TypeScript type definitions
│   └── package.json
│
├── 📂 finance/               # Main finance application
│   ├── models.py           # Core financial models
│   ├── api.py              # REST API endpoints
│   ├── services.py         # Business logic
│   └── serializers.py      # Data serialization
│
├── 📂 ar/                    # Accounts Receivable
│   ├── models.py           # AR models (Invoice, Payment)
│   └── admin.py            # Django admin config
│
├── 📂 ap/                    # Accounts Payable
│   ├── models.py           # AP models (Invoice, Payment)
│   └── admin.py            # Django admin config
│
├── 📂 core/                  # Core shared models
│   ├── models.py           # Currency, Tax rates, etc.
│   └── management/         # Management commands
│
├── 📂 erp/                   # Django project configuration
│   ├── settings.py         # Settings (Database, CORS, etc.)
│   └── urls.py             # URL routing
│
├── 📄 manage.py              # Django management script
├── 📄 requirements.txt       # Python dependencies
├── 📄 db.sqlite3            # SQLite database
│
├── 🚀 start_system.bat       # Start everything
├── 🚀 start_django.bat       # Start backend only
├── 🚀 start_frontend.bat     # Start frontend only
├── 🔍 check_system.bat       # Verify prerequisites
│
└── 📖 Documentation files
```

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend UI** | http://localhost:3000 | Main application interface |
| **Backend API** | http://localhost:8000/api | REST API endpoints |
| **API Docs** | http://localhost:8000/api/docs | Interactive API documentation |
| **Admin Panel** | http://localhost:8000/admin | Django administration |

## 📋 API Endpoints

### Accounts
- `GET /api/accounts/` - List all accounts
- `GET /api/accounts/{id}/` - Get account details

### AR (Accounts Receivable)
- `GET /api/ar/invoices/` - List AR invoices
- `POST /api/ar/invoices/` - Create AR invoice
- `POST /api/ar/invoices/{id}/post/` - Post to GL
- `GET /api/ar/payments/` - List AR payments
- `POST /api/ar/payments/` - Create AR payment

### AP (Accounts Payable)
- `GET /api/ap/invoices/` - List AP invoices
- `POST /api/ap/invoices/` - Create AP invoice
- `POST /api/ap/invoices/{id}/post/` - Post to GL
- `GET /api/ap/payments/` - List AP payments
- `POST /api/ap/payments/` - Create AP payment

### Reports
- `GET /api/reports/trial-balance/` - Trial Balance
- `GET /api/reports/ar-aging/` - AR Aging Report
- `GET /api/reports/ap-aging/` - AP Aging Report

## 💻 Development

### Backend Development

```bash
# Activate virtual environment
venv\Scripts\activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
pytest
```

### Frontend Development

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

## 🧪 Testing

### Manual Testing Checklist

1. ✅ Create AR Invoice → Post to GL
2. ✅ Record AR Payment → Post
3. ✅ Create AP Invoice → Post to GL
4. ✅ Record AP Payment → Post
5. ✅ View Trial Balance Report
6. ✅ View AR Aging Report
7. ✅ Export reports to CSV/Excel

### Automated Tests

```bash
# Backend tests
pytest

# Frontend tests
cd frontend
npm test
```

## 🔧 Configuration

### Environment Variables

**Backend** (`.env` file):
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Database Configuration

**SQLite (Default):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**PostgreSQL:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'finance_erp',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🐛 Troubleshooting

### Common Issues

**Port already in use:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

**Module not found:**
```cmd
pip install -r requirements.txt
cd frontend && npm install
```

**Database errors:**
```cmd
python manage.py migrate
python manage.py migrate --run-syncdb
```

**CORS errors:**
- Verify `django-cors-headers` is installed
- Check `CORS_ALLOWED_ORIGINS` in settings.py

For more troubleshooting, see [SETUP_GUIDE.md](SETUP_GUIDE.md#troubleshooting)

## 📊 Sample Data

Create test data via Django shell:

```python
python manage.py shell

from core.models import Currency
from ar.models import Customer
from ap.models import Supplier

# Create currency
Currency.objects.create(code="USD", name="US Dollar", symbol="$")

# Create customer
Customer.objects.create(
    name="ACME Corporation",
    email="billing@acme.com",
    phone="555-1234"
)

# Create supplier
Supplier.objects.create(
    name="Office Supplies Inc",
    email="sales@officesupplies.com"
)
```

## 🚀 Deployment

### Production Checklist

Backend:
- [ ] Set `DEBUG=False`
- [ ] Configure secure `SECRET_KEY`
- [ ] Setup PostgreSQL database
- [ ] Run `collectstatic`
- [ ] Configure HTTPS
- [ ] Setup proper logging
- [ ] Configure email backend

Frontend:
- [ ] Build optimized bundle: `npm run build`
- [ ] Configure production API URL
- [ ] Setup CDN for static assets
- [ ] Enable caching
- [ ] Configure monitoring

## 📞 Support

- **Documentation:** See [SETUP_GUIDE.md](SETUP_GUIDE.md) and [QUICK_START.md](QUICK_START.md)
- **System Check:** Run `check_system.bat`
- **Backend Logs:** Check terminal running Django
- **Frontend Logs:** Check browser console (F12)

## 📝 License

This project is part of a private Finance ERP system.

## 🎯 Next Steps

1. **Run System Check:** `check_system.bat`
2. **Start the System:** `start_system.bat`
3. **Read Quick Start:** [QUICK_START.md](QUICK_START.md)
4. **Create Test Data:** Use Django admin or shell
5. **Explore Features:** Try creating invoices, payments, and reports

---

## 📖 Quick Reference

### Batch Files

| File | Purpose |
|------|---------|
| `start_system.bat` | Start both backend and frontend |
| `start_django.bat` | Start Django backend only |
| `start_frontend.bat` | Start Next.js frontend only |
| `check_system.bat` | Verify system requirements |

### Key Directories

| Directory | Contains |
|-----------|----------|
| `frontend/` | Next.js frontend application |
| `finance/` | Main Django finance app |
| `ar/` | Accounts Receivable module |
| `ap/` | Accounts Payable module |
| `core/` | Shared models and utilities |

### Documentation Files

| File | Content |
|------|---------|
| `README.md` | This file - overview |
| `QUICK_START.md` | 5-minute quick start guide |
| `SETUP_GUIDE.md` | Complete setup instructions |
| `PROJECT_SUMMARY.md` | Full technical documentation |
| `frontend/README.md` | Frontend-specific docs |

---

**Ready to start? Run `start_system.bat` and open http://localhost:3000**

**Finance ERP System - Complete & Ready for Use! 🚀**

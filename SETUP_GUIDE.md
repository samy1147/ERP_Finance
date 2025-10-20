# Finance ERP - Complete Setup Guide

This guide will help you set up and run the complete Finance ERP system with both backend and frontend.

## System Overview

**Backend**: Django REST Framework  
**Frontend**: Next.js + React + TypeScript  
**Database**: SQLite (default) or PostgreSQL  

## Prerequisites

1. **Python 3.8+** and pip installed
2. **Node.js 18+** and npm installed
3. **Git** (optional, for version control)

## Complete Setup Instructions

### Step 1: Backend Setup

1. **Open a command prompt and navigate to the project root:**
   ```cmd
   cd C:\Users\samys\FinanceERP
   ```

2. **Create and activate a virtual environment (recommended):**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run database migrations:**
   ```cmd
   python manage.py migrate
   ```

5. **Create a superuser (optional, for admin access):**
   ```cmd
   python manage.py createsuperuser
   ```

6. **Start the Django backend:**
   ```cmd
   python manage.py runserver
   ```
   
   Or use the provided batch file:
   ```cmd
   start_django.bat
   ```

   ✅ Backend should now be running at: **http://localhost:8000**

### Step 2: Frontend Setup

1. **Open a NEW command prompt and navigate to the frontend folder:**
   ```cmd
   cd C:\Users\samys\FinanceERP\frontend
   ```

2. **Install Node.js dependencies:**
   ```cmd
   npm install
   ```

3. **Start the Next.js frontend:**
   ```cmd
   npm run dev
   ```
   
   Or use the provided batch file (from project root):
   ```cmd
   start_frontend.bat
   ```

   ✅ Frontend should now be running at: **http://localhost:3000**

### Step 3: Access the Application

1. **Open your web browser and go to:** http://localhost:3000

2. **You should see the Finance ERP Dashboard with navigation to:**
   - Chart of Accounts
   - AR Invoices & Payments
   - AP Invoices & Payments
   - Financial Reports

## Quick Start (Windows)

### Option 1: Using Batch Files

1. **Double-click `start_django.bat`** to start the backend
2. **Double-click `start_frontend.bat`** to start the frontend
3. **Open browser to http://localhost:3000**

### Option 2: Manual Start

**Terminal 1 (Backend):**
```cmd
cd C:\Users\samys\FinanceERP
python manage.py runserver
```

**Terminal 2 (Frontend):**
```cmd
cd C:\Users\samys\FinanceERP\frontend
npm run dev
```

## Verifying the Setup

### Backend Verification

1. **Check Django API:** http://localhost:8000/api/
2. **Check Admin Panel:** http://localhost:8000/admin/
3. **Check API Documentation:** http://localhost:8000/api/docs/

### Frontend Verification

1. **Dashboard loads:** http://localhost:3000
2. **Navigation works:** Click through sidebar menu items
3. **API connection:** Try viewing accounts or creating a test invoice

### Database Verification

1. **Check SQLite database exists:** `db.sqlite3` file in project root
2. **Verify tables created:** Open with SQLite browser or Django admin

## Available Endpoints

### Backend API Endpoints

- `http://localhost:8000/api/accounts/` - Chart of Accounts
- `http://localhost:8000/api/ar/invoices/` - AR Invoices
- `http://localhost:8000/api/ar/payments/` - AR Payments
- `http://localhost:8000/api/ap/invoices/` - AP Invoices
- `http://localhost:8000/api/ap/payments/` - AP Payments
- `http://localhost:8000/api/reports/trial-balance/` - Trial Balance
- `http://localhost:8000/api/reports/ar-aging/` - AR Aging
- `http://localhost:8000/api/reports/ap-aging/` - AP Aging

### Frontend Pages

- `http://localhost:3000/` - Dashboard
- `http://localhost:3000/accounts` - Chart of Accounts
- `http://localhost:3000/ar/invoices` - AR Invoices List
- `http://localhost:3000/ar/invoices/new` - Create AR Invoice
- `http://localhost:3000/ar/payments` - AR Payments List
- `http://localhost:3000/ar/payments/new` - Receive Payment
- `http://localhost:3000/ap/invoices` - AP Invoices List
- `http://localhost:3000/ap/invoices/new` - Create AP Invoice
- `http://localhost:3000/ap/payments` - AP Payments List
- `http://localhost:3000/ap/payments/new` - Make Payment
- `http://localhost:3000/reports` - Financial Reports

## Testing the Integration

### Test 1: View Accounts
1. Go to http://localhost:3000/accounts
2. You should see the chart of accounts from your database

### Test 2: Create an AR Invoice
1. Go to http://localhost:3000/ar/invoices/new
2. Fill in the invoice details
3. Add line items
4. Click "Create Invoice"
5. Verify it appears in the invoice list

### Test 3: Post to GL
1. Go to http://localhost:3000/ar/invoices
2. Find a DRAFT invoice
3. Click "Post to GL"
4. Verify status changes to POSTED

### Test 4: Run Reports
1. Go to http://localhost:3000/reports
2. Select "Trial Balance"
3. Click "View Report"
4. Try exporting to CSV or Excel

## Database Connection

The frontend connects to the database through the Django REST API:

```
Frontend (Next.js) 
    ↓ HTTP Requests
Django REST API
    ↓ ORM Queries
SQLite Database (db.sqlite3)
```

All database operations are handled server-side by Django for:
- ✅ Security
- ✅ Data validation
- ✅ Business logic
- ✅ Transaction management

## Architecture

```
┌─────────────────────────────────────────────┐
│         Frontend (Next.js)                  │
│         http://localhost:3000               │
│  ┌─────────────────────────────────────┐   │
│  │ Pages (React Components)             │   │
│  │ - Dashboard                          │   │
│  │ - Accounts                           │   │
│  │ - AR/AP Invoices & Payments         │   │
│  │ - Reports                            │   │
│  └─────────────────────────────────────┘   │
│              ↓ Axios HTTP Requests          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Backend (Django)                    │
│         http://localhost:8000               │
│  ┌─────────────────────────────────────┐   │
│  │ REST API (DRF)                       │   │
│  │ - ViewSets                           │   │
│  │ - Serializers                        │   │
│  │ - Services                           │   │
│  └─────────────────────────────────────┘   │
│              ↓ Django ORM                   │
│  ┌─────────────────────────────────────┐   │
│  │ Database (SQLite/PostgreSQL)         │   │
│  │ - Accounts                           │   │
│  │ - Invoices                           │   │
│  │ - Payments                           │   │
│  │ - Journal Entries                    │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## Troubleshooting

### Backend Issues

**Error: Port 8000 already in use**
```cmd
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

**Error: No module named 'xyz'**
```cmd
pip install -r requirements.txt
```

**Error: Database not found**
```cmd
python manage.py migrate
```

### Frontend Issues

**Error: Port 3000 already in use**
```cmd
# Find and kill the process
netstat -ano | findstr :3000
taskkill /PID <process_id> /F
```

**Error: Cannot find module**
```cmd
cd frontend
npm install
```

**Error: API connection refused**
- Verify Django backend is running on port 8000
- Check CORS settings in Django settings.py

### Database Issues

**Error: Unable to open database file**
- Check file permissions on db.sqlite3
- Ensure migrations have been run

**Error: Table doesn't exist**
```cmd
python manage.py migrate
```

## Development Workflow

1. **Start both servers** (backend and frontend)
2. **Make changes** to code
3. **Hot reload** automatically updates (both Django and Next.js)
4. **Test changes** in browser
5. **Check console** for errors

## Production Deployment

For production deployment:

### Backend
```cmd
python manage.py collectstatic
python manage.py check --deploy
# Use Gunicorn or uWSGI
```

### Frontend
```cmd
cd frontend
npm run build
npm start
```

### Environment Variables
Create `.env` files for production settings:
- `DEBUG=False`
- `SECRET_KEY=<secure-key>`
- `ALLOWED_HOSTS=<your-domain>`
- `DATABASE_URL=<database-url>`

## Additional Resources

- **Django Docs**: https://docs.djangoproject.com/
- **Next.js Docs**: https://nextjs.org/docs
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Tailwind CSS**: https://tailwindcss.com/docs

## Support

If you encounter issues:
1. Check this README for troubleshooting steps
2. Review console logs (both browser and terminal)
3. Verify all dependencies are installed
4. Ensure both backend and frontend are running
5. Check database migrations are up to date

## Features Checklist

✅ Backend Django REST API running  
✅ Frontend Next.js app running  
✅ Database connected and migrated  
✅ CORS configured for frontend-backend communication  
✅ Chart of Accounts display  
✅ AR Invoice creation and posting  
✅ AR Payment recording  
✅ AP Invoice creation and posting  
✅ AP Payment recording  
✅ Financial reports (Trial Balance, AR/AP Aging)  
✅ CSV/Excel export functionality  
✅ Responsive design for mobile/desktop  

**Your Finance ERP system is now fully operational! 🚀**

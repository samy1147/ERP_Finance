# Finance ERP Frontend

Modern Next.js frontend for the Finance ERP system with full support for GL, AR, and AP operations.

## Features

✅ **Chart of Accounts** - View and manage GL accounts with filtering  
✅ **AR Invoices** - Create customer invoices with line items and post to GL  
✅ **AR Payments** - Receive payments from customers  
✅ **AP Invoices** - Create supplier invoices with line items and post to GL  
✅ **AP Payments** - Make payments to suppliers  
✅ **Financial Reports** - Trial Balance, AR Aging, AP Aging with CSV/Excel export  
✅ **Responsive Design** - Works on desktop, tablet, and mobile  
✅ **Real-time Updates** - Connected to Django REST API backend  

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client for API calls
- **React Hook Form** - Form management
- **React Hot Toast** - Toast notifications
- **Lucide React** - Beautiful icons
- **date-fns** - Date formatting

## Installation

### Prerequisites

- Node.js 18+ and npm
- Django backend running on `http://localhost:8000`

### Setup Steps

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

### Quick Start (Windows)

Double-click `start_frontend.bat` in the root directory to automatically install and start the frontend.

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── accounts/          # Chart of Accounts
│   │   ├── ar/                # Accounts Receivable
│   │   │   ├── invoices/      # AR Invoice list & create
│   │   │   └── payments/      # AR Payment list & create
│   │   ├── ap/                # Accounts Payable
│   │   │   ├── invoices/      # AP Invoice list & create
│   │   │   └── payments/      # AP Payment list & create
│   │   ├── reports/           # Financial reports
│   │   ├── layout.tsx         # Root layout
│   │   ├── template.tsx       # Client-side layout wrapper
│   │   └── page.tsx           # Dashboard
│   ├── components/            # Reusable components
│   │   └── Layout.tsx         # Main navigation layout
│   ├── lib/                   # Utilities
│   │   └── api.ts            # Axios instance
│   ├── services/              # API services
│   │   └── api.ts            # API endpoint functions
│   ├── types/                 # TypeScript types
│   │   └── index.ts          # Type definitions
│   └── styles/               # Global styles
│       └── globals.css       # Tailwind CSS
├── public/                    # Static assets
├── package.json              # Dependencies
├── tsconfig.json            # TypeScript config
├── tailwind.config.js       # Tailwind config
└── next.config.js           # Next.js config
```

## API Configuration

The frontend connects to the Django backend API. The default URL is `http://localhost:8000/api`.

To change the API URL, set the environment variable:

```env
NEXT_PUBLIC_API_URL=http://your-backend-url/api
```

## Available Scripts

- `npm run dev` - Start development server (port 3000)
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Main Features

### Dashboard
Central hub with quick links to all modules and recent activities.

### Chart of Accounts
- View all GL accounts
- Filter by account type (Asset, Liability, Equity, Income, Expense)
- Search by code or name
- View account status (Active/Inactive)

### AR Invoices
- Create customer invoices with multiple line items
- Calculate totals automatically
- Post invoices to General Ledger
- View invoice status (DRAFT, POSTED, REVERSED)
- Track due dates and balances

### AR Payments
- Record customer payments
- Link payments to specific invoices
- Specify bank accounts
- Post payments to GL automatically

### AP Invoices
- Create supplier invoices with multiple line items
- Calculate totals automatically
- Post invoices to General Ledger
- View invoice status (DRAFT, POSTED, REVERSED)
- Track due dates and balances

### AP Payments
- Record supplier payments
- Link payments to specific invoices
- Specify bank accounts
- Post payments to GL automatically

### Financial Reports
- **Trial Balance** - Account balances with debit/credit totals
- **AR Aging** - Customer receivables aged by days outstanding
- **AP Aging** - Supplier payables aged by days outstanding
- Export reports to CSV or Excel
- Date range filtering
- As-of-date reporting for aging

## Backend Integration

The frontend is fully integrated with your Django backend:

### API Endpoints Used

- `GET /api/accounts/` - List accounts
- `GET /api/ar/invoices/` - List AR invoices
- `POST /api/ar/invoices/` - Create AR invoice
- `POST /api/ar/invoices/{id}/post/` - Post AR invoice to GL
- `GET /api/ar/payments/` - List AR payments
- `POST /api/ar/payments/` - Create AR payment
- `POST /api/ar/payments/{id}/post/` - Post AR payment
- `GET /api/ap/invoices/` - List AP invoices
- `POST /api/ap/invoices/` - Create AP invoice
- `POST /api/ap/invoices/{id}/post/` - Post AP invoice to GL
- `GET /api/ap/payments/` - List AP payments
- `POST /api/ap/payments/` - Create AP payment
- `POST /api/ap/payments/{id}/post/` - Post AP payment
- `GET /api/reports/trial-balance/` - Trial balance report
- `GET /api/reports/ar-aging/` - AR aging report
- `GET /api/reports/ap-aging/` - AP aging report

### CORS Configuration

The Django backend is already configured to accept requests from `http://localhost:3000`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## Database Connection

The frontend connects to the same database as your Django backend through the REST API. All data operations are handled server-side:

- SQLite database: `db.sqlite3` (default)
- PostgreSQL: Configured via Django settings
- All CRUD operations go through Django ORM
- Data validation on both frontend and backend

## Navigation

The sidebar provides quick access to:
- 📊 Dashboard
- 📖 Accounts (Chart of Accounts)
- 📄 AR Invoices
- 💵 AR Payments  
- 📋 AP Invoices
- 💳 AP Payments
- 📈 Reports

## Responsive Design

The frontend is fully responsive and works on:
- Desktop (1024px+)
- Tablet (768px - 1023px)
- Mobile (320px - 767px)

The sidebar collapses on mobile with a hamburger menu.

## Development Tips

1. **Hot Reload**: Changes to code automatically reload the browser
2. **Type Safety**: TypeScript provides autocompletion and type checking
3. **API Errors**: Check browser console and Network tab for debugging
4. **Backend Required**: Ensure Django backend is running before starting frontend

## Production Build

To build for production:

```bash
npm run build
npm start
```

This creates an optimized build in `.next/` directory.

## Troubleshooting

### Port Already in Use
If port 3000 is busy, the dev server will suggest an alternative port.

### API Connection Failed
- Verify Django backend is running on `http://localhost:8000`
- Check CORS settings in Django
- Verify API endpoints match your backend URLs

### Module Not Found
Run `npm install` to ensure all dependencies are installed.

## License

This frontend is part of the Finance ERP project.

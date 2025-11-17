# 🏢 ERP Finance System - SIMPLE EXPLANATION FOR DEVELOPERS

**Created:** November 15, 2025  
**For:** Development Team who need to understand this project FAST!

---

## 🎯 WHAT IS THIS PROJECT?

This is a **Financial Management System** (ERP) for companies that:
- Need to track money coming IN (from customers)
- Need to track money going OUT (to suppliers/vendors)
- Need to record all financial transactions
- Operate in multiple countries (UAE, Saudi Arabia, Egypt, India)
- Handle different currencies (AED, SAR, USD, etc.)
- Need tax calculations (VAT, Corporate Tax)

---

## 🏗️ SYSTEM ARCHITECTURE (SIMPLE VIEW)

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR PROJECT                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BACKEND (Django)              FRONTEND (Next.js)          │
│  Port: 8007                    Port: 3000                  │
│  ├─ REST APIs                  ├─ User Interface           │
│  ├─ Database (SQLite)          ├─ Forms & Tables           │
│  └─ Business Logic             └─ Connects to Backend API  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Technology Stack:**
- **Backend:** Python + Django REST Framework
- **Frontend:** Next.js + React + Tailwind CSS
- **Database:** SQLite (currently) / PostgreSQL (production ready)
- **API Docs:** Swagger UI (auto-generated)

---

## 📦 WHAT ARE THE MAIN MODULES?

Think of modules as different departments in a company:

### 1. **CORE** - Foundation (Basic Settings)
```
📁 core/
   ├─ Currency (AED, SAR, USD, etc.)
   └─ Tax Rates (VAT 5%, VAT 15%, etc.)
```
**Purpose:** Stores basic reference data that everyone uses

---

### 2. **SEGMENT** - Chart of Accounts (Where Money Goes)
```
📁 segment/
   ├─ Segment Types (Account, Department, Project, etc.)
   └─ Segments (Actual account codes like "1000-Cash", "DEPT-SALES")
```
**Purpose:** Defines ALL the "buckets" where money can be tracked

**Example:**
```
Account Type:
  1000 - Assets
    1100 - Current Assets
      1110 - Cash in Bank (Child - Can Use) ✅
      1120 - Accounts Receivable (Child - Can Use) ✅
    1200 - Fixed Assets (Parent - Cannot Use) ❌

Department Type:
  DEPT-SALES - Sales Department ✅
  DEPT-IT - IT Department ✅
```

---

### 3. **PERIODS** - Fiscal Periods (Time Periods)
```
📁 periods/
   ├─ Fiscal Years (2025, 2026)
   └─ Fiscal Periods (Jan 2025, Feb 2025, etc.)
```
**Purpose:** Controls WHEN you can post transactions
- **OPEN** period = You can post transactions ✅
- **CLOSED** period = No more transactions allowed ❌

---

### 4. **FINANCE** - General Ledger (The Main Accounting Book)
```
📁 finance/
   ├─ Journal Entries (All transactions)
   ├─ Journal Lines (Debit & Credit entries)
   └─ Bank Accounts
```
**Purpose:** This is the HEART of the system - where ALL money movements are recorded

**How it works:**
```
Journal Entry #1 - Sale to Customer
  Date: Jan 15, 2025
  Lines:
    DR Cash          $1,000  (Money coming in)
    CR Sales Revenue $1,000  (We made a sale)
```

---

### 5. **AR (Accounts Receivable)** - Money Coming IN
```
📁 ar/
   ├─ Customers (Who owes us money)
   ├─ AR Invoices (Bills we send to customers)
   └─ AR Payments (Money received from customers)
```
**Purpose:** Track money CUSTOMERS owe us

**Workflow:**
```
1. Create Invoice → Customer owes us $1,000
2. Send Invoice to Customer
3. Customer Pays → We receive $1,000
4. Mark Invoice as PAID
```

---

### 6. **AP (Accounts Payable)** - Money Going OUT
```
📁 ap/
   ├─ Suppliers/Vendors (Who we owe money to)
   ├─ AP Invoices (Bills from suppliers)
   └─ AP Payments (Money we pay to suppliers)
```
**Purpose:** Track money WE owe to SUPPLIERS

**Workflow:**
```
1. Receive Bill from Supplier → We owe $500
2. Approve Bill
3. Pay Supplier → We pay $500
4. Mark Bill as PAID
```

---

### 7. **FIXED ASSETS** - Company Assets
```
📁 fixed_assets/
   ├─ Assets (Computers, Cars, Buildings)
   ├─ Depreciation (Asset value decreases over time)
   └─ Asset Transfers (Moving assets between locations)
```
**Purpose:** Track valuable things the company owns

**Example:**
```
Buy a Car for $20,000
- Every year, it loses value (Depreciation)
- After 5 years: Car is worth $0
```

---

### 8. **PROCUREMENT** - Buying Process
```
📁 procurement/
   ├─ requisitions/ (Internal requests to buy)
   ├─ rfx/ (Request quotes from suppliers)
   ├─ purchase_orders/ (Official orders to suppliers)
   ├─ receiving/ (Receiving goods at warehouse)
   └─ vendor_bills/ (Bills from suppliers)
```
**Purpose:** Complete process from "I need to buy" to "I received and paid"

**Workflow:**
```
1. Employee: "I need 10 laptops" (Requisition)
2. Purchasing: "Send quote requests" (RFQ)
3. Select best vendor → Create Purchase Order
4. Receive laptops at warehouse (GRN)
5. Receive bill from vendor
6. System checks: Order vs Receipt vs Bill (3-Way Match)
7. If OK → Pay the vendor
```

---

### 9. **INVENTORY** - Stock Management
```
📁 inventory/
   └─ Stock tracking (UNDER DEVELOPMENT)
```
**Purpose:** Track products in warehouses (NOT COMPLETE YET)

---

### 10. **CRM** - Customer Relationship Management
```
📁 crm/
   └─ Minimal implementation
```
**Purpose:** Customer information (MINIMAL - mostly in AR module)

---

## 🔄 HOW DO THESE MODULES WORK TOGETHER?

### Example: Selling to a Customer

```
┌─────────────────────────────────────────────────────────────┐
│              SELLING PROCESS (AR Module)                    │
└─────────────────────────────────────────────────────────────┘

Step 1: CREATE INVOICE
  Module: AR
  You create an invoice for Customer "ABC Corp"
  Amount: $1,000
  Status: DRAFT

Step 2: APPROVE INVOICE
  Approver reviews and approves
  Status: APPROVED

Step 3: POST TO GENERAL LEDGER
  Module: FINANCE (GL)
  System creates Journal Entry:
    DR Accounts Receivable  $1,000  [Account: 1120]
    CR Sales Revenue        $1,000  [Account: 4000]
  Status: POSTED

Step 4: CUSTOMER PAYS
  Module: AR
  Record payment received: $1,000
  
Step 5: ALLOCATE PAYMENT TO INVOICE
  Link payment to invoice
  Update Journal Entry:
    DR Cash                 $1,000  [Account: 1110]
    CR Accounts Receivable  $1,000  [Account: 1120]
  Status: PAID ✅
```

### Example: Buying from Supplier

```
┌─────────────────────────────────────────────────────────────┐
│          BUYING PROCESS (Procurement + AP Modules)          │
└─────────────────────────────────────────────────────────────┘

Step 1: CREATE PURCHASE REQUISITION (PR)
  Module: PROCUREMENT - Requisitions
  Employee: "I need office supplies"
  Amount: $500

Step 2: CREATE PURCHASE ORDER (PO)
  Module: PROCUREMENT - Purchase Orders
  Send official order to Supplier "XYZ Supplies"

Step 3: RECEIVE GOODS
  Module: PROCUREMENT - Receiving
  Warehouse receives goods and creates GRN (Goods Receipt Note)

Step 4: RECEIVE VENDOR BILL
  Module: PROCUREMENT - Vendor Bills
  Supplier sends bill for $500

Step 5: 3-WAY MATCH
  System checks:
  ✅ PO says $500
  ✅ GRN shows goods received
  ✅ Bill says $500
  → All match! OK to proceed

Step 6: CREATE AP INVOICE
  Module: AP
  Create bill in AP system
  Status: APPROVED

Step 7: POST TO GL
  Module: FINANCE
  Journal Entry:
    DR Expense Account      $500  [Account: 6000]
    CR Accounts Payable     $500  [Account: 2100]

Step 8: PAY SUPPLIER
  Module: AP
  Make payment: $500
  Journal Entry:
    DR Accounts Payable     $500
    CR Cash                 $500
  Status: PAID ✅
```

---

## 📊 DATABASE RELATIONSHIPS (SIMPLE)

```
                    ┌──────────┐
                    │ Currency │ (Foundation)
                    └────┬─────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐     ┌────▼────┐    ┌────▼────┐
    │Customer │     │Supplier │    │ Period  │
    └────┬────┘     └────┬────┘    └─────────┘
         │               │
    ┌────▼────────┐ ┌────▼─────────┐
    │ AR Invoice  │ │  AP Invoice  │
    └────┬────────┘ └────┬─────────┘
         │               │
         └───────┬───────┘
                 │
         ┌───────▼──────────┐
         │  Journal Entry   │ (General Ledger)
         │                  │
         │  ALL transactions│
         │  end up here!    │
         └──────────────────┘
```

**Key Point:** Everything eventually creates a Journal Entry in the Finance module!

---

## 🎯 WHAT DOES EACH FILE DO?

In each module folder (e.g., `ar/`, `ap/`), you'll find:

```
📁 ar/
   ├─ models.py          → Database tables (Customer, Invoice, Payment)
   ├─ serializers.py     → Convert data to/from JSON for API
   ├─ api.py or views.py → API endpoints (GET, POST, PUT, DELETE)
   ├─ services.py        → Business logic (calculations, workflows)
   ├─ urls.py            → URL routing
   ├─ admin.py           → Django admin interface
   └─ migrations/        → Database changes history
```

**What each file does:**
- **models.py** = "What data do we store?" (Database structure)
- **serializers.py** = "How do we send/receive data via API?" (JSON conversion)
- **api.py/views.py** = "What can users do?" (API endpoints)
- **services.py** = "How do we calculate things?" (Business rules)
- **urls.py** = "What's the API address?" (URL routing)

---

## 🚀 HOW TO START THE SYSTEM?

### Quick Start (Windows PowerShell):

```powershell
# 1. Start Backend (Django)
cd C:\Users\samys\OneDrive\Documents\GitHub\ERP_Finance
python manage.py runserver 8007

# 2. In another terminal, start Frontend (Next.js)
cd frontend
npm run dev
```

### Access Points:
- **Backend API:** http://localhost:8007/api/
- **API Documentation:** http://localhost:8007/api/schema/swagger-ui/
- **Frontend:** http://localhost:3000/
- **Admin Panel:** http://localhost:8007/admin/

---

## 📝 SUMMARY FOR DEVELOPERS

**What you need to know:**

1. **Backend = Django** (Python)
   - Handles all business logic
   - Stores data in database
   - Provides REST APIs

2. **Frontend = Next.js** (React)
   - User interface
   - Forms and tables
   - Calls backend APIs

3. **Main Flow:**
   ```
   User → Frontend → API Call → Backend → Database
                                         ↓
                                    Process & Return
                                         ↓
   User ← Frontend ← JSON Response ← Backend
   ```

4. **All Financial Transactions** eventually create **Journal Entries** in the Finance module

5. **Multi-dimensional Accounting** = Each transaction can be tagged with multiple dimensions (Account, Department, Project, Product)

---

## 🆘 NEED HELP?

**Next Steps:**
1. Read `2_CURRENT_PROBLEMS.md` to understand issues
2. Read `3_MISSING_FEATURES.md` to see what's incomplete
3. Read `4_DETAILED_WORKFLOWS.md` for detailed process flows
4. Check `PROJECT_OVERVIEW.md` for complete technical details

**Quick Reference:**
- **Postman Collections:** Test APIs in `postman_collections/` folder
- **API Docs:** http://localhost:8007/api/schema/swagger-ui/
- **Settings:** Check `erp/settings.py` for configuration

---

**Remember:** This is a LARGE system! Take it one module at a time. Start with understanding AR (customer invoices) and AP (vendor bills) first, then move to other modules.

**Questions?** Refer to the detailed documentation or check the code comments in each module's `models.py` file.

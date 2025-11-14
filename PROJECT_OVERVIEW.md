# 🏢 ERP Finance System - Complete Project Overview

## 📋 Table of Contents
1. [What is This Project?](#what-is-this-project)
2. [System Architecture](#system-architecture)
3. [Core Modules & Relationships](#core-modules--relationships)
4. [Current Problems](#current-problems)
5. [Missing Features](#missing-features)
6. [Data Flow & Workflows](#data-flow--workflows)
7. [Technical Stack](#technical-stack)

---

## 🎯 What is This Project?

This is a **Multi-Module Enterprise Resource Planning (ERP) System** focused on **Financial Management** for businesses operating across multiple countries (UAE, Saudi Arabia, Egypt, India).

### Purpose
- **Manage financial transactions** (invoices, payments, journal entries)
- **Track assets** (fixed assets with depreciation)
- **Handle procurement** (purchase orders, requisitions, vendor management)
- **Manage multi-segment accounting** (Chart of Accounts with dimensions)
- **Support multi-currency** operations with foreign exchange
- **Comply with tax regulations** (VAT, Corporate Tax) across different countries

---

## 🏗️ System Architecture

### Backend: Django REST API (Port 8007)
- **Framework**: Django 5.2.7 + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **API Documentation**: DRF Spectacular (Swagger/OpenAPI)

### Frontend: Next.js (Port 3000)
- **Framework**: Next.js (React-based)
- **Styling**: Tailwind CSS
- **Location**: `frontend/` directory

### Key Technologies
- **django-simple-history**: Audit trail for data changes
- **django-filter**: Advanced filtering for APIs
- **CORS**: Enabled for frontend-backend communication
- **Postman Collections**: Pre-built API testing collections

---

## 🧩 Core Modules & Relationships

### **1. CORE Module** (`core/`)
**Foundation module - provides shared data**

**Models:**
- `Currency`: Multi-currency support (AED, SAR, USD, etc.)
- `TaxRate`: Tax rates by country and category (Standard, Zero, Exempt)

**Purpose:** Central reference data used by all other modules

---

### **2. SEGMENT Module** (`segment/`)
**Chart of Accounts with Multi-Dimensional Accounting**

**Models:**
- `XX_SegmentType`: Defines segment dimensions (Account, Department, Cost Center, Project, Product)
- `XX_Segment`: Actual segment values (hierarchical tree structure)

**Key Features:**
- Hierarchical parent-child relationships (roll-up for reporting)
- Node types: `parent` (folders) vs `child` (actual accounts)
- Only `child` segments can be used in transactions
- Flexible multi-dimensional reporting

**Example Structure:**
```
Account Segment Type:
  1000 (Assets - Parent)
    ├─ 1100 (Current Assets - Parent)
    │   ├─ 1110 (Cash - Child) ← Can use in transactions
    │   └─ 1120 (AR - Child) ← Can use in transactions
    └─ 1200 (Fixed Assets - Parent)

Department Segment Type:
  DEPT-SALES (Sales Department - Child)
  DEPT-IT (IT Department - Child)
```

**Why Important:** Enables multi-dimensional financial analysis (by account + department + project + product)

---

### **3. PERIODS Module** (`periods/`)
**Fiscal Year & Period Management**

**Models:**
- `FiscalYear`: Annual accounting periods (e.g., 2025)
- `FiscalPeriod`: Monthly/quarterly periods within a year
- `PeriodStatus`: Historical tracking of period state changes

**Statuses:**
- `OPEN`: Transactions can be posted
- `CLOSED`: Locked, no changes allowed
- `PERMANENTLY_CLOSED`: Year-end locked

**Purpose:** Controls when transactions can be posted (period cut-off enforcement)

---

### **4. FINANCE Module** (`finance/`)
**Core Financial Transactions & General Ledger**

**Models:**

#### **Banking:**
- `BankAccount`: Company bank accounts with GL mapping

#### **General Ledger:**
- `JournalEntry`: Header for journal transactions
- `JournalLine`: Debit/Credit lines (linked to accounts)
- `JournalLineSegment`: Multi-dimensional segment assignments for each journal line

#### **Tax Management:**
- `TaxCode`: Tax codes with rates
- `CorporateTaxRule`: Corporate tax rules by country
- `CorporateTaxFiling`: Corporate tax accrual tracking

#### **Invoice Templates (Legacy/Incomplete):**
- `Invoice`: AR invoice template (BEING REPLACED by ar.ARInvoice)
- `InvoiceLine`: Invoice line items
- `InvoiceApproval`: Multi-level approval workflow

#### **Segment Assignment:**
- `SegmentAssignmentRule`: Auto-assign segments based on customer/supplier/account

**Key Features:**
- Posted documents are read-only (use reversal for corrections)
- Period validation (can't post to closed periods)
- Multi-segment dimension tracking

---

### **5. AR Module** (`ar/` - Accounts Receivable)
**Customer Invoicing & Collections**

**Models:**

#### **Master Data:**
- `Customer`: Customer master data (name, country, currency, VAT number)

#### **Invoicing:**
- `ARInvoice`: Customer invoices
- `ARItem`: Invoice line items (products/services)
- `InvoiceGLLine`: GL distribution lines (how invoice hits GL accounts)
- `ARInvoiceDistributionSegment`: Segment assignments for each GL distribution

#### **Payments:**
- `ARPayment`: Customer payments received
- `ARPaymentAllocation`: Links payments to invoices

**Statuses:**
- **Approval**: DRAFT → PENDING_APPROVAL → APPROVED/REJECTED
- **Posting**: Not Posted → POSTED (creates GL journal)
- **Payment**: UNPAID → PARTIALLY_PAID → PAID

**Workflow:**
```
1. Create invoice (DRAFT)
2. Submit for approval (PENDING_APPROVAL)
3. Approve (APPROVED)
4. Post to GL (is_posted=True, creates JournalEntry)
5. Receive payment (ARPayment)
6. Allocate payment to invoice (ARPaymentAllocation)
7. Invoice status updates to PAID
```

---

### **6. AP Module** (`ap/` - Accounts Payable)
**Vendor Management & Bill Payment**

**Models:**

#### **Vendor Master:**
- `Supplier`: Vendor/supplier master data (comprehensive)
- `VendorContact`: Contact persons at vendor
- `VendorDocument`: Document storage (certificates, licenses)
- `VendorPerformanceRecord`: Performance tracking
- `VendorOnboardingChecklist`: Vendor onboarding workflow

#### **Invoicing:**
- `APInvoice`: Vendor bills/invoices
- `APItem`: Invoice line items
- `APInvoiceGLLine`: GL distribution lines
- `APInvoiceDistributionSegment`: Segment assignments

#### **Payments:**
- `APPayment`: Vendor payments made
- `APPaymentAllocation`: Links payments to invoices

**Key Features:**
- Comprehensive vendor onboarding (documents, compliance verification)
- Performance scoring (quality, delivery, price)
- Vendor status management (active, on hold, blacklisted)
- Multi-level approval workflows
- 3-way matching (links to procurement module)

**Workflow:** Similar to AR but for payables

---

### **7. FIXED ASSETS Module** (`fixed_assets/`)
**Asset Lifecycle Management**

**Models:**
- `AssetCategory`: Asset classification with depreciation defaults
- `AssetLocation`: Physical locations where assets are kept
- `Asset`: Individual asset records
- `AssetDepreciation`: Depreciation schedules
- `AssetTransfer`: Asset movement between locations
- `AssetDisposal`: Asset retirement/sale

**Features:**
- Multiple depreciation methods (Straight Line, Declining Balance, etc.)
- Depreciation calculation and GL posting
- Asset transfers between locations
- Full asset lifecycle tracking

---

### **8. PROCUREMENT Module** (`procurement/`)
**Complex Procurement-to-Pay Process**

#### **Sub-modules:**

**8.1. Requisitions** (`procurement/requisitions/`)
- `PRHeader`: Purchase Requisition (PR) - internal request to buy
- `PRLine`: PR line items
- `CostCenter`: Cost center master
- `Project`: Project master

**8.2. RFx (Sourcing)** (`procurement/rfx/`)
- `RFxEvent`: RFQ/RFP/RFI events (Request for Quote/Proposal/Information)
- `RFxItem`: Items to quote
- `SupplierInvitation`: Invite vendors to quote
- `SupplierQuote`: Vendor responses
- `SupplierQuoteLine`: Quote line items
- `RFxAward`: Award to winning vendor(s)
- `AuctionBid`: Real-time auction bids

**8.3. Purchase Orders** (`procurement/purchase_orders/`)
- Purchase orders (PO) created from awarded RFx or approved PRs

**8.4. Receiving** (`procurement/receiving/`)
- `Warehouse`: Warehouse locations
- Goods Receipt Notes (GRN) - receiving against POs

**8.5. Vendor Bills** (`procurement/vendor_bills/`)
- `VendorBill`: Vendor invoices (integrated with AP)
- `VendorBillLine`: Bill line items
- `ThreeWayMatch`: Automated 3-way matching (PO ↔ GRN ↔ Invoice)
- `MatchException`: Tolerance violations
- `MatchTolerance`: Configurable matching rules

**8.6. Approvals** (`procurement/approvals/`)
- Multi-level approval workflows for PRs, POs, etc.

**8.7. Contracts** (`procurement/contracts/`)
- Contract management and compliance

**8.8. Payments** (`procurement/payments/`)
- Payment processing (links to AP)

**8.9. Catalog** (`procurement/catalog/`)
- Product/service catalog

---

### **9. INVENTORY Module** (`inventory/`)
**Stock Management** (UNDER DEVELOPMENT)

Expected features:
- Product master
- Stock movements
- Warehouse management
- Inventory valuation

---

### **10. CRM Module** (`crm/`)
**Customer Relationship Management** (MINIMAL)

Currently appears to have minimal implementation. Customer master is in `ar.Customer`.

---

## 🔴 Current Problems

### **Problem 1: Foreign Key Reference Errors**
**Issue:** Migration conflicts and circular dependencies between modules

**Example:** `fixed_assets` trying to reference `ap.Supplier` before it exists

**Evidence:** Terminal shows:
```
Remove-Item "fixed_assets/migrations/0010_asset_supplier.py"
```

**Impact:** Database migrations fail, can't update schema

**Root Cause:**
- `fixed_assets.Asset` wants to link to `ap.Supplier`
- Migration order conflicts
- Apps not properly ordered in `INSTALLED_APPS`

**Solution Needed:**
1. Ensure proper app ordering in `settings.py` (foundational apps first)
2. Use string references for ForeignKeys: `models.ForeignKey('ap.Supplier', ...)`
3. Create proper migration dependencies
4. Consider if the relationship is actually needed

---

### **Problem 2: Duplicate/Inconsistent Invoice Models**
**Issue:** Two invoice implementations competing

**Evidence:**
- `finance.Invoice` (legacy template)
- `ar.ARInvoice` (current implementation)
- Both exist but `ar.ARInvoice` is the active one

**Impact:**
- Developer confusion
- Code duplication
- API inconsistency

**Solution:** Remove or archive `finance.Invoice` and related models

---

### **Problem 3: Incomplete GL Posting Logic**
**Issue:** Not all modules properly create `JournalEntry` records

**What Should Happen:**
1. Create AR Invoice → Post → Creates `JournalEntry` with `JournalLine` + `JournalLineSegment`
2. Create AP Invoice → Post → Creates `JournalEntry`
3. Fixed Asset Depreciation → Creates `JournalEntry`
4. Payments → Create `JournalEntry`

**Current State:** Some modules have posting logic, others don't

**Impact:** GL is incomplete, can't generate accurate financial reports

---

### **Problem 4: Segment Assignment Complexity**
**Issue:** Multi-dimensional accounting is powerful but complex

**Challenge:**
- Every `JournalLine` needs segment assignments for ALL required segment types
- Rules exist (`SegmentAssignmentRule`) but may not be fully implemented
- Manual entry is error-prone

**Example:** A journal line needs:
- Account segment (1110 - Cash)
- Department segment (DEPT-SALES)
- Cost Center segment (CC-HQ)
- Project segment (PROJ-2025-001)
- Product segment (PROD-A)

**Impact:** Users can't post transactions easily, complexity barrier

---

### **Problem 5: Approval Workflow Implementation**
**Issue:** Approval models exist but workflow engine missing

**What Exists:**
- `InvoiceApproval` model
- Status fields on invoices

**What's Missing:**
- Who are the approvers?
- Approval routing rules
- Notification system
- UI for approval actions

---

### **Problem 6: Missing Frontend Integration**
**Issue:** Frontend exists but unclear what's implemented

**Evidence:**
- Next.js frontend in `frontend/`
- Backend API ready
- Unknown integration status

**Impact:** Can't test end-to-end workflows

---

### **Problem 7: Test Coverage**
**Issue:** Terminal shows test failure: `test_invoice_list_quick.py` exit code 1

**Impact:** Unknown code stability, regression risk

---

### **Problem 8: Documentation Gap**
**Issue:** No comprehensive developer documentation until now

**Impact:** New developers can't onboard, team confusion

---

## ⚠️ Missing Features

### **1. Reporting & Analytics**
**Missing:**
- Financial statements (P&L, Balance Sheet, Cash Flow)
- Trial Balance
- Aged Receivables/Payables
- Budget vs Actual
- Multi-dimensional reports (by department, project, etc.)

**What Exists:**
- Raw data is available
- Need report generation layer

---

### **2. Period Close Process**
**Missing:**
- Automated period close workflow
- Validation checks before closing
- Period close checklist
- Year-end adjustments
- Opening balance carry-forward

**What Exists:**
- `FiscalPeriod` model with status
- Basic open/close flag

---

### **3. Budget Management**
**Missing:**
- Budget creation & approval
- Budget allocation by segment
- Budget consumption tracking
- Budget vs Actual variance alerts

---

### **4. Foreign Exchange (FX) Management**
**Partial Implementation:**
- `exchange_rate` and `base_currency_total` fields exist on invoices
- `fx_services.py` exists but unclear if complete

**Missing:**
- Currency revaluation (mark-to-market)
- Realized vs unrealized gains/losses
- Exchange rate history
- Automatic FX gain/loss journal entries

---

### **5. Intercompany Transactions**
**Missing:**
- Intercompany invoicing
- Automatic elimination entries
- Consolidated reporting

---

### **6. User & Role Management**
**Missing:**
- Proper user authentication (seems to use basic Django auth)
- Role-based access control (RBAC)
- Approval matrix configuration
- Segregation of duties controls

---

### **7. Audit Trail & Compliance**
**Partial:**
- `django-simple-history` tracks changes
- Posted documents are locked

**Missing:**
- Audit log reporting
- Change approval for master data
- Compliance reporting (SOX, IFRS, etc.)

---

### **8. Integration Framework**
**Missing:**
- API for external systems
- Import/Export utilities
- Bank statement import
- Excel upload for bulk transactions

---

### **9. Notification System**
**Missing:**
- Email notifications
- Approval request notifications
- Due date reminders
- Exception alerts

---

### **10. Inventory Costing**
**Missing:**
- FIFO/LIFO/Average costing
- Stock valuation
- Cost of goods sold (COGS) calculation
- Inventory adjustments → GL posting

---

### **11. Procurement Completion**
**Partial:**
- Models exist for full P2P cycle
- Not clear if all workflows are implemented
- 3-way match logic may be incomplete

**Need to Verify:**
- PR → PO conversion
- PO → GRN receiving
- GRN → AP Invoice matching
- Approval routing

---

### **12. Advanced Tax Features**
**Missing:**
- Withholding tax (WHT) calculation
- Reverse charge VAT handling
- Tax reporting (VAT return generation)
- E-invoicing integration (ZATCA for KSA, etc.)

---

## 🔄 Data Flow & Workflows

### **Workflow 1: AR Invoice to Payment (Complete Cycle)**

```
┌─────────────────────────────────────────────────────────────────┐
│                    AR INVOICE WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

1. CREATE INVOICE (Draft)
   ↓
   User: Creates ARInvoice with ARItems
   System: Calculates totals (net, tax, gross)
   Status: approval_status=DRAFT, is_posted=False, payment_status=UNPAID

2. SUBMIT FOR APPROVAL
   ↓
   User: Submits invoice
   System: approval_status=PENDING_APPROVAL
   [MISSING: Notification to approver]

3. APPROVE
   ↓
   User: Approver reviews and approves
   System: approval_status=APPROVED
   [MISSING: Approval routing logic]

4. POST TO GL
   ↓
   User: Posts invoice
   System:
   - Creates JournalEntry (header)
   - Creates JournalLine for each GL distribution (InvoiceGLLine)
   - Creates JournalLineSegment for multi-dimensional accounting
   - Links: ARInvoice.gl_journal → JournalEntry
   - Updates: is_posted=True, posted_at=now()
   
   Example GL Entry:
   DR  Accounts Receivable (1120)    1,050  [DEPT-SALES, CC-HQ]
       CR  Sales Revenue (4010)       1,000  [DEPT-SALES, PROD-A]
       CR  VAT Payable (2300)            50  [DEPT-SALES]

5. RECEIVE PAYMENT
   ↓
   User: Records ARPayment
   System: Creates payment record with bank account reference

6. ALLOCATE PAYMENT
   ↓
   User: Allocates payment to invoice(s)
   System:
   - Creates ARPaymentAllocation
   - Updates ARInvoice.payment_status
   - If fully paid: payment_status=PAID, paid_at=now()

7. PAYMENT POST TO GL
   ↓
   System: Creates JournalEntry for payment
   DR  Bank Account (1110)          1,050  [DEPT-SALES]
       CR  Accounts Receivable (1120) 1,050  [DEPT-SALES]

┌─────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                │
└─────────────────────────────────────────────────────────────────┘

Customer (Master) ──► ARInvoice (Transaction)
                         │
                         ├──► ARItem (Line Items)
                         │
                         ├──► InvoiceGLLine (GL Distributions)
                         │      └──► ARInvoiceDistributionSegment
                         │
                         └──► JournalEntry (GL)
                                └──► JournalLine
                                       └──► JournalLineSegment

ARPayment ──► ARPaymentAllocation ──► ARInvoice
```

---

### **Workflow 2: AP Invoice & Payment (Vendor Bills)**

```
┌─────────────────────────────────────────────────────────────────┐
│                    AP INVOICE WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

SCENARIO A: Simple AP Invoice (No Procurement)
──────────────────────────────────────────────

1. Receive vendor invoice
2. Enter APInvoice with APItems
3. Approve
4. Post to GL (similar to AR, but reversed)
   DR  Expense/Asset Account       1,000
   DR  VAT Recoverable               50
       CR  Accounts Payable        1,050

5. Make APPayment
6. Allocate payment
7. Post payment to GL
   DR  Accounts Payable           1,050
       CR  Bank Account            1,050


SCENARIO B: Procurement Cycle (3-Way Match)
────────────────────────────────────────────

1. PR (Purchase Requisition)
   ↓
   Department requests to buy items
   PRHeader + PRLine created

2. RFx (Optional - Sourcing)
   ↓
   Create RFxEvent (RFQ/RFP)
   Invite suppliers
   Receive SupplierQuotes
   Award to best vendor (RFxAward)

3. PO (Purchase Order)
   ↓
   Convert PR or Award to PO
   POHeader + POLine created
   Send to vendor

4. GRN (Goods Receipt)
   ↓
   Warehouse receives goods
   Create GRN against PO
   Update inventory (if inventory module active)

5. Vendor Bill
   ↓
   Receive vendor invoice (VendorBill)
   System performs ThreeWayMatch:
   - Match VendorBill to PO to GRN
   - Check quantity tolerances
   - Check price tolerances
   - Flag MatchExceptions if violations

6. Approve Bill (if match passes)
   ↓
   Create APInvoice (or link VendorBill to APInvoice)

7. Post & Pay
   ↓
   Same as Scenario A

┌─────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                │
└─────────────────────────────────────────────────────────────────┘

Supplier (Master) ──► APInvoice (Transaction)
                         │
                         ├──► APItem (Line Items)
                         │
                         ├──► APInvoiceGLLine (GL Distributions)
                         │      └──► APInvoiceDistributionSegment
                         │
                         └──► JournalEntry (GL)
                                └──► JournalLine
                                       └──► JournalLineSegment

APPayment ──► APPaymentAllocation ──► APInvoice

PROCUREMENT FLOW:
PRHeader ──► RFxEvent ──► PO ──► GRN ──► VendorBill
   │            │          │       │         │
PRLine      RFxItem    POLine  GRNLine  VendorBillLine
                                    │         │
                                    └──3-Way──┘
                                    ThreeWayMatch
```

---

### **Workflow 3: Fixed Asset Lifecycle**

```
┌─────────────────────────────────────────────────────────────────┐
│                  FIXED ASSET WORKFLOW                           │
└─────────────────────────────────────────────────────────────────┘

1. ACQUISITION
   ↓
   Purchase asset (via AP Invoice or direct entry)
   Create Asset record:
   - Asset category
   - Cost
   - Useful life
   - Depreciation method
   - Location
   
   GL Entry (if from invoice):
   DR  Fixed Asset (1500)          10,000
       CR  AP or Cash              10,000

2. CAPITALIZATION
   ↓
   Asset.status = ACTIVE
   Asset.capitalization_date = date
   Start depreciation schedule

3. DEPRECIATION
   ↓
   Monthly/Periodic:
   Calculate depreciation (AssetDepreciation)
   
   System creates JournalEntry:
   DR  Depreciation Expense (6100)    100
       CR  Accumulated Dep (1510)      100

4. TRANSFER
   ↓
   Move asset to different location
   Create AssetTransfer record
   Update Asset.location
   [Optional: Update segment assignments]

5. DISPOSAL
   ↓
   Retire or sell asset
   Create AssetDisposal record
   
   Calculate:
   - Original cost
   - Accumulated depreciation
   - Book value
   - Sale proceeds (if any)
   - Gain/loss on disposal
   
   GL Entry (example - sale):
   DR  Cash                        5,000
   DR  Accumulated Dep            4,000
   DR  Loss on Disposal             500
       CR  Fixed Asset            10,000

   Note: MISSING if disposal logic incomplete

┌─────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                │
└─────────────────────────────────────────────────────────────────┘

AssetCategory (Master)
AssetLocation (Master)
         ↓
      Asset (Transaction)
         │
         ├──► AssetDepreciation (Schedule)
         ├──► AssetTransfer (Movements)
         └──► AssetDisposal (Retirement)
                 │
                 └──► JournalEntry (GL postings)
```

---

### **Workflow 4: Multi-Segment Accounting**

```
┌─────────────────────────────────────────────────────────────────┐
│              MULTI-DIMENSIONAL ACCOUNTING                       │
└─────────────────────────────────────────────────────────────────┘

SETUP PHASE:
────────────

1. Define Segment Types (XX_SegmentType)
   - Account (COA)
   - Department
   - Cost Center
   - Project
   - Product

2. Create Segment Values (XX_Segment)
   - Build hierarchies
   - Mark leaf nodes as type='child'
   
   Example:
   Account Segment:
     1000 (Assets - parent)
       1100 (Current - parent)
         1110 (Cash - child) ← Can use in transactions
         1120 (AR - child)

3. Configure Segment Assignment Rules
   - Create SegmentAssignmentRule
   - Define: For Customer X + Account Y → Auto-assign Dept Z

TRANSACTION PHASE:
──────────────────

When posting a transaction (Invoice, Payment, JE):

1. Create JournalEntry (header)

2. For each distribution line:
   - Create JournalLine (debit/credit amount)
   - User selects account segment (1110 - Cash)
   
3. System requires segment assignment for ALL segment types:
   
   For JournalLine #1:
   ├─ JournalLineSegment (segment_type=Account, segment=1110)
   ├─ JournalLineSegment (segment_type=Department, segment=DEPT-SALES)
   ├─ JournalLineSegment (segment_type=CostCenter, segment=CC-HQ)
   ├─ JournalLineSegment (segment_type=Project, segment=PROJ-001)
   └─ JournalLineSegment (segment_type=Product, segment=PROD-A)

4. Validation:
   - All required segment types must have assignments
   - Only 'child' segments can be assigned
   - Segment must belong to correct segment_type

REPORTING BENEFIT:
──────────────────

Query: "Show me all expenses for Department=SALES, Project=PROJ-001"

SELECT SUM(jl.debit - jl.credit)
FROM journal_line jl
JOIN journal_line_segment jls_dept ON jl.id = jls_dept.journal_line_id
JOIN journal_line_segment jls_proj ON jl.id = jls_proj.journal_line_id
WHERE jls_dept.segment_id = 'DEPT-SALES'
  AND jls_proj.segment_id = 'PROJ-001'
  AND jl.account_id IN (SELECT id FROM xx_segment 
                        WHERE code LIKE '6%')  -- Expense accounts

Result: Multi-dimensional P&L by any combination of dimensions
```

---

### **Workflow 5: Period Management**

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERIOD MANAGEMENT                            │
└─────────────────────────────────────────────────────────────────┘

SETUP:
──────

1. Create FiscalYear (2025)
   - start_date: 2025-01-01
   - end_date: 2025-12-31

2. System auto-creates FiscalPeriods:
   - 2025-01 (Jan): OPEN
   - 2025-02 (Feb): OPEN
   - ...
   - 2025-12 (Dec): OPEN
   - 2025-ADJ (Adjustment): OPEN

OPERATIONS:
───────────

3. Post transactions:
   - System validates: transaction date must be in OPEN period
   - If period is CLOSED → REJECT

4. Month-end close (2025-01):
   User: Closes period
   System:
   - Validates all transactions are posted
   - Runs period-end processes (depreciation, accruals)
   - Updates: FiscalPeriod.status = CLOSED
   - Creates PeriodStatus history record
   
   MISSING:
   - Automated validation checks
   - Close checklist
   - Reversing entries for accruals

5. Reopen (if needed):
   User: Reopens period (emergency)
   System: FiscalPeriod.status = OPEN
   Logs who and when

6. Year-end close:
   User: Closes year
   System:
   - Closes all periods
   - Closes FiscalYear
   - MISSING: Create opening JE for next year
   - MISSING: Close P&L to retained earnings

┌─────────────────────────────────────────────────────────────────┐
│                        VALIDATION                               │
└─────────────────────────────────────────────────────────────────┘

BEFORE POSTING ANY TRANSACTION:

if transaction.date NOT IN (SELECT start-end FROM FiscalPeriod 
                            WHERE status = 'OPEN'):
    REJECT: "Cannot post to closed period"
```

---

## 📊 Entity Relationship Diagram (Simplified)

```
┌──────────────────────────────────────────────────────────────────┐
│                         CORE FOUNDATION                          │
└──────────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
                    │   Currency  │
                    └──────┬──────┘
                           │
                           │ (used by)
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
         │Customer │  │Supplier│  │ARInvoice│
         └─────────┘  └────────┘  └─────────┘


┌──────────────────────────────────────────────────────────────────┐
│                    CHART OF ACCOUNTS (SEGMENTS)                  │
└──────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │ XX_SegmentType   │  (Account, Dept, CC, Project, Product)
    └────────┬─────────┘
             │ 1:N
    ┌────────▼─────────┐
    │   XX_Segment     │  (Hierarchical tree of values)
    └────────┬─────────┘
             │
             │ (referenced by)
             │
    ┌────────▼─────────────┐
    │  JournalLineSegment  │  (Assigns segments to GL lines)
    └──────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                      GENERAL LEDGER FLOW                         │
└──────────────────────────────────────────────────────────────────┘

┌────────────────┐
│ JournalEntry   │  (Header: date, currency, posted flag)
└───────┬────────┘
        │ 1:N
┌───────▼────────┐
│  JournalLine   │  (Debit/Credit, Account)
└───────┬────────┘
        │ 1:N
┌───────▼────────────────┐
│ JournalLineSegment     │  (Multi-dimensional tags)
└────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                   AR (ACCOUNTS RECEIVABLE)                       │
└──────────────────────────────────────────────────────────────────┘

┌──────────┐
│ Customer │
└────┬─────┘
     │ 1:N
┌────▼──────────┐          ┌──────────────┐
│   ARInvoice   │──────────│ JournalEntry │ (GL posting)
└────┬──────────┘   1:1    └──────────────┘
     │ 1:N
     │
     ├──► ARItem (line items)
     │
     ├──► InvoiceGLLine ──► ARInvoiceDistributionSegment
     │
     └──► ARPaymentAllocation ◄──┐
                                  │
                        ┌─────────┴─────┐
                        │   ARPayment   │
                        └───────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                   AP (ACCOUNTS PAYABLE)                          │
└──────────────────────────────────────────────────────────────────┘

┌──────────┐
│ Supplier │──┐
└────┬─────┘  │
     │ 1:N    │ 1:N (contacts)
     │        │
     │    ┌───▼──────────────┐
     │    │ VendorContact    │
     │    └──────────────────┘
     │
┌────▼──────────┐          ┌──────────────┐
│   APInvoice   │──────────│ JournalEntry │
└────┬──────────┘   1:1    └──────────────┘
     │ 1:N
     │
     ├──► APItem
     │
     ├──► APInvoiceGLLine ──► APInvoiceDistributionSegment
     │
     └──► APPaymentAllocation ◄──┐
                                  │
                        ┌─────────┴─────┐
                        │   APPayment   │
                        └───────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                    PROCUREMENT (P2P)                             │
└──────────────────────────────────────────────────────────────────┘

                    ┌──────────┐
                    │ Supplier │
                    └────┬─────┘
                         │
    ┌────────────────────┼─────────────────┐
    │                    │                 │
┌───▼──────┐      ┌──────▼──────┐   ┌─────▼───────┐
│ PRHeader │      │  RFxEvent   │   │  POHeader   │
└───┬──────┘      └──────┬──────┘   └─────┬───────┘
    │ 1:N                │ 1:N            │ 1:N
┌───▼───────┐      ┌─────▼────────┐   ┌───▼────────┐
│  PRLine   │      │  RFxItem     │   │  POLine    │
└───────────┘      └──────────────┘   └─────┬──────┘
                                             │
                   ┌─────────────────────────┤
                   │                         │
            ┌──────▼─────┐          ┌────────▼────────┐
            │    GRN     │          │  VendorBill     │
            └──────┬─────┘          └────────┬────────┘
                   │                         │
                   └───────────┬─────────────┘
                               │
                     ┌─────────▼──────────┐
                     │  ThreeWayMatch     │  (PO ↔ GRN ↔ Bill)
                     └────────────────────┘
                               │
                               ▼
                       ┌───────────────┐
                       │   APInvoice   │  (If match OK)
                       └───────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                      FIXED ASSETS                                │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│ AssetCategory   │
└────────┬────────┘
         │ 1:N
┌────────▼────────┐          ┌──────────────────┐
│     Asset       │──────────│ AssetDepreciation│ (Schedule)
└────────┬────────┘   1:N    └─────────┬────────┘
         │                              │
         │ 1:N                          │ (posts to)
         │                              ▼
         │                    ┌──────────────────┐
         ├──► AssetTransfer   │  JournalEntry    │
         │                    └──────────────────┘
         └──► AssetDisposal


┌──────────────────────────────────────────────────────────────────┐
│                      PERIODS                                     │
└──────────────────────────────────────────────────────────────────┘

┌─────────────┐
│ FiscalYear  │
└──────┬──────┘
       │ 1:N
┌──────▼───────┐
│ FiscalPeriod │  (Controls when transactions can post)
└──────────────┘
```

---

## 🛠️ Technical Stack Summary

### **Backend**
- **Language**: Python 3.11
- **Framework**: Django 5.2.7
- **API**: Django REST Framework 3.16
- **Database**: SQLite (dev) / PostgreSQL ready
- **ORM**: Django ORM
- **API Docs**: drf-spectacular (Swagger/OpenAPI)

### **Frontend**
- **Framework**: Next.js (React)
- **Styling**: Tailwind CSS
- **Language**: TypeScript

### **Key Libraries**
- `django-simple-history`: Audit trail
- `django-filter`: API filtering
- `django-cors-headers`: CORS support
- `psycopg2-binary`: PostgreSQL driver
- `openpyxl`: Excel support
- `pytest` + `pytest-django`: Testing

### **Development Tools**
- Postman collections for API testing
- VS Code workspace
- Git version control

---

## 🚀 Getting Started (For Developers)

### **1. Environment Setup**

```powershell
# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (if fixtures exist)
python manage.py loaddata initial_data
```

### **2. Start Backend**

```powershell
# Option 1: Direct
python manage.py runserver 8007

# Option 2: Using batch file
.\start_django.bat

# Option 3: Using PowerShell script
.\start_system.ps1
```

Backend runs at: `http://localhost:8007`
API docs: `http://localhost:8007/api/schema/swagger-ui/`

### **3. Start Frontend**

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:3000`

### **4. Test API with Postman**

Import collections from `postman_collections/`:
1. `1_Core_Finance_APIs.json`
2. `2_AR_Invoices_and_Payments.json`
3. `3_AP_Invoices_Payments_Vendors.json`
4. ... (others)

---

## 📝 Recommended Next Steps

### **Priority 1: Fix Critical Issues**
1. ✅ Resolve foreign key migration conflicts
2. ✅ Remove duplicate invoice models (clean up `finance.Invoice`)
3. ✅ Complete GL posting logic for all transaction types
4. ✅ Add comprehensive tests

### **Priority 2: Complete Core Features**
1. ✅ Implement approval workflow engine
2. ✅ Complete segment assignment automation
3. ✅ Build financial reports (P&L, Balance Sheet)
4. ✅ Implement period close process

### **Priority 3: Enhance**
1. ✅ Add user/role management
2. ✅ Build notification system
3. ✅ Complete procurement workflows
4. ✅ Add import/export utilities

### **Priority 4: Frontend**
1. ✅ Audit frontend implementation status
2. ✅ Build missing UI screens
3. ✅ Test end-to-end workflows

---

## 🎓 Learning Resources

### **Understanding the System**
1. Read this document first
2. Review `postman_collections/` for API examples
3. Check `POSTMAN_COLLECTION_UPDATES.md` for recent changes
4. Explore models in each app's `models.py`

### **Key Concepts to Study**
- Double-entry accounting
- Multi-dimensional (segment) accounting
- Procure-to-Pay (P2P) process
- Order-to-Cash (O2C) process
- Fixed asset accounting & depreciation
- Tax accounting (VAT/GST)
- Period close procedures

---

## 📞 Questions?

If you have questions about:
- **Models**: Check the app's `models.py` file
- **APIs**: Check `api.py`, `views.py`, or Postman collections
- **Business Logic**: Check `services.py` in each app
- **Database**: Check `migrations/` folder
- **Configuration**: Check `erp/settings.py`

---

## 🎯 Summary

**What you have:**
- A comprehensive, multi-module ERP system
- Strong foundation with proper models
- Multi-dimensional accounting capability
- Full AR, AP, Fixed Assets, and Procurement modules
- API-first architecture with documentation

**What needs work:**
- Fix migration conflicts
- Complete GL posting integration
- Build approval workflows
- Implement reporting layer
- Complete frontend integration
- Add comprehensive testing

**This is a LARGE, ENTERPRISE-GRADE system. Take time to understand each module before making changes.**

Good luck! 🚀

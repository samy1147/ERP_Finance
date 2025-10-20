# Invoice Tables Comparison - AR vs AP vs Finance

## Overview
Your FinanceERP system has THREE different invoice-related table structures in different folders. Here's a detailed explanation of each and their purposes.

---

## 1. AR INVOICES (ar/models.py)
**Table Name:** `ar_customer`, `ar_arinvoice`, `ar_aritem`

### ARInvoice Model - **Accounts Receivable (Sales Invoices)**
**Purpose:** Track money OWED TO YOU by customers

### Key Features:
```python
class ARInvoice(models.Model):
    # WHO owes money
    customer = ForeignKey(Customer)  # Link to customer
    
    # INVOICE DETAILS
    number = CharField(max_length=32, unique=True)
    date = DateField()
    due_date = DateField()
    currency = ForeignKey(Currency)
    country = CharField()  # Tax country (AE, SA, EG, IN)
    
    # THREE STATUS FIELDS (as per your recent changes)
    # 1. APPROVAL STATUS
    approval_status = CharField(choices=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED'])
    
    # 2. POSTING STATUS
    is_posted = BooleanField(default=False)  # Posted to General Ledger?
    posted_at = DateTimeField()
    
    # 3. PAYMENT STATUS
    payment_status = CharField(choices=['UNPAID', 'PARTIALLY_PAID', 'PAID'])
    paid_at = DateTimeField()
    
    # CANCELLATION
    is_cancelled = BooleanField(default=False)
    cancelled_at = DateTimeField()
    
    # FX TRACKING
    exchange_rate = DecimalField()  # Rate when posted
    base_currency_total = DecimalField()  # Amount in AED
    
    # GL LINK
    gl_journal = OneToOneField("finance.JournalEntry")
```

### Related Models:
- **Customer** - Who is buying from you
- **ARItem** - Individual line items on the invoice (products/services sold)
- **ARPayment** - Customer payments received against this invoice

### Use Case:
- Customer "Emirates Trading LLC" buys goods worth $10,000
- Create AR Invoice in USD
- System converts to AED using exchange rate
- Track approval → posting → payment stages

---

## 2. AP INVOICES (ap/models.py)
**Table Name:** `ap_supplier`, `ap_apinvoice`, `ap_apitem`

### APInvoice Model - **Accounts Payable (Purchase Invoices)**
**Purpose:** Track money YOU OWE to suppliers

### Key Features:
```python
class APInvoice(models.Model):
    # WHO you owe money to
    supplier = ForeignKey(Supplier)  # Link to supplier
    
    # INVOICE DETAILS
    number = CharField(max_length=32, unique=True)
    date = DateField()
    due_date = DateField()
    currency = ForeignKey(Currency)
    country = CharField()  # Tax country (AE, SA, EG, IN)
    
    # THREE STATUS FIELDS (same structure as AR)
    # 1. APPROVAL STATUS
    approval_status = CharField(choices=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED'])
    
    # 2. POSTING STATUS
    is_posted = BooleanField(default=False)
    posted_at = DateTimeField()
    
    # 3. PAYMENT STATUS
    payment_status = CharField(choices=['UNPAID', 'PARTIALLY_PAID', 'PAID'])
    paid_at = DateTimeField()
    
    # CANCELLATION
    is_cancelled = BooleanField(default=False)
    cancelled_at = DateTimeField()
    
    # FX TRACKING
    exchange_rate = DecimalField()
    base_currency_total = DecimalField()
    
    # GL LINK
    gl_journal = OneToOneField("finance.JournalEntry")
```

### Related Models:
- **Supplier** - Who you are buying from
- **APItem** - Individual line items on the invoice (goods/services purchased)
- **APPayment** - Payments you make to the supplier

### Use Case:
- Supplier "American Supplies Corp" sends you invoice for $5,000
- Create AP Invoice in USD
- System converts to AED using exchange rate
- Track approval → posting → payment stages

---

## 3. FINANCE INVOICES (finance/models.py)
**Table Name:** `finance_invoice`, `finance_invoiceline`

### Invoice Model - **Generic/Legacy Invoice Structure**
**Purpose:** Original invoice model (appears to be older/alternative implementation)

### Key Features:
```python
class Invoice(LockOnPostedMixin):
    # WHO
    customer = ForeignKey("ar.Customer")  # Only customers, no suppliers
    
    # INVOICE DETAILS
    invoice_no = CharField(max_length=64, unique=True)
    currency = CharField(max_length=8)  # Just a text field!
    
    # TOTALS
    total_net = DecimalField()
    total_tax = DecimalField()
    total_gross = DecimalField()
    
    # STATUS (simplified - only one status field)
    status = CharField(choices=['DRAFT', 'POSTED', 'REVERSED'])
    posted_at = DateTimeField()
    
    # REVERSAL SUPPORT
    reversal_ref = ForeignKey("self")  # Link to reversed invoice
```

### Key Differences:
1. **Only ONE status field** (not three separate ones like AR/AP)
2. **No approval workflow** built-in
3. **No payment tracking** (no payment_status field)
4. **No FX tracking** (no exchange_rate or base_currency_total)
5. **Has reversal support** (can link to reversed invoices)
6. **Read-only after posting** (LockOnPostedMixin prevents edits)
7. **Generic InvoiceLine** structure (different from ARItem/APItem)

### Use Case:
- Appears to be an older or alternative invoice implementation
- May be used for special purposes or legacy data
- NOT currently used by main AR/AP workflows

---

## 4. INVOICE APPROVAL WORKFLOW (finance/models.py)

### InvoiceApproval Model
**Purpose:** Track approval history for BOTH AR and AP invoices

```python
class InvoiceApproval(models.Model):
    # POLYMORPHIC REFERENCE (can point to either AR or AP invoice)
    invoice_type = CharField(choices=[('AR', 'AR Invoice'), ('AP', 'AP Invoice')])
    invoice_id = IntegerField()
    
    # APPROVAL DETAILS
    status = CharField(choices=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'POSTED'])
    
    # WHO submitted
    submitted_by = CharField()
    submitted_at = DateTimeField()
    
    # WHO approved/rejected
    approver = CharField()
    approved_at = DateTimeField()
    rejected_at = DateTimeField()
    
    # DETAILS
    comments = TextField()
    approval_level = IntegerField()  # For multi-level approvals
```

### Use Case:
- When AR invoice is submitted for approval → create InvoiceApproval record
- When AP invoice needs approval → create InvoiceApproval record
- Track who submitted, who approved, when, and comments

---

## COMPARISON TABLE

| Feature | AR Invoice | AP Invoice | Finance Invoice | Invoice Approval |
|---------|------------|------------|-----------------|------------------|
| **Purpose** | Sales (money IN) | Purchases (money OUT) | Generic/Legacy | Approval workflow |
| **Party** | Customer | Supplier | Customer only | N/A (tracks both) |
| **Table** | `ar_arinvoice` | `ap_apinvoice` | `finance_invoice` | `finance_invoiceapproval` |
| **Status Fields** | 3 (approval, posting, payment) | 3 (approval, posting, payment) | 1 (status only) | 1 (approval status) |
| **Approval Workflow** | ✅ Yes | ✅ Yes | ❌ No | ✅ Core purpose |
| **Payment Tracking** | ✅ Yes | ✅ Yes | ❌ No | N/A |
| **FX Tracking** | ✅ Yes | ✅ Yes | ❌ No | N/A |
| **Multi-Currency** | ✅ Currency FK | ✅ Currency FK | ⚠️ Text field only | N/A |
| **Tax Country** | ✅ Yes (AE/SA/EG/IN) | ✅ Yes (AE/SA/EG/IN) | ❌ No | N/A |
| **GL Posting** | ✅ Links to JournalEntry | ✅ Links to JournalEntry | ⚠️ Status only | N/A |
| **Cancellation** | ✅ is_cancelled flag | ✅ is_cancelled flag | ❌ No | N/A |
| **Reversal** | ❓ Not shown | ❓ Not shown | ✅ Yes | N/A |
| **Line Items** | ARItem model | APItem model | InvoiceLine model | N/A |
| **Payments** | ARPayment model | APPayment model | ❌ No model | N/A |
| **Currently Used** | ✅ Active | ✅ Active | ⚠️ May be legacy | ✅ Active |

---

## WORKFLOW EXAMPLE

### AR Invoice (Sales) Workflow:
1. **Create Draft** → `ARInvoice` with `approval_status='DRAFT'`, `is_posted=False`, `payment_status='UNPAID'`
2. **Submit for Approval** → Create `InvoiceApproval` record with `invoice_type='AR'`
3. **Approve** → Update `ARInvoice.approval_status='APPROVED'`
4. **Post to GL** → Create `JournalEntry`, link to `ARInvoice.gl_journal`, set `is_posted=True`
5. **Receive Payment** → Create `ARPayment`, update `payment_status='PAID'`

### AP Invoice (Purchase) Workflow:
1. **Create Draft** → `APInvoice` with `approval_status='DRAFT'`, `is_posted=False`, `payment_status='UNPAID'`
2. **Submit for Approval** → Create `InvoiceApproval` record with `invoice_type='AP'`
3. **Approve** → Update `APInvoice.approval_status='APPROVED'`
4. **Post to GL** → Create `JournalEntry`, link to `APInvoice.gl_journal`, set `is_posted=True`
5. **Make Payment** → Create `APPayment`, update `payment_status='PAID'`

---

## DATABASE TABLE NAMES

### AR Tables:
- `ar_customer` - Customer master data
- `ar_arinvoice` - AR invoice headers
- `ar_aritem` - AR invoice line items
- `ar_arpayment` - Customer payments

### AP Tables:
- `ap_supplier` - Supplier master data
- `ap_apinvoice` - AP invoice headers
- `ap_apitem` - AP invoice line items
- `ap_appayment` - Supplier payments

### Finance Tables:
- `finance_invoice` - Generic invoice (legacy?)
- `finance_invoiceline` - Generic invoice lines
- `finance_invoiceapproval` - Approval workflow for AR/AP invoices

---

## RECOMMENDATIONS

### Current System (ACTIVE):
✅ **Use AR models** for all sales invoices (customers owing you money)
✅ **Use AP models** for all purchase invoices (you owing suppliers money)
✅ **Use InvoiceApproval** for tracking approval workflow of both AR and AP

### Legacy System (CONSIDER REMOVING):
⚠️ **Finance.Invoice** appears to be an older implementation
- Lacks modern features (approval, payment tracking, FX)
- May cause confusion
- Consider migrating data or removing if not used

### Your Recent Changes:
You correctly updated the AR and AP invoice lists to show THREE separate status columns:
1. **Posting Status** (Unposted/Posted/Cancelled)
2. **Payment Status** (Unpaid/Partially Paid/Paid)
3. **Approval Status** (Pending/Approved/Rejected)

This matches the AR/AP models perfectly and gives users clear visibility into each stage of the invoice lifecycle.

---

## SUMMARY

- **AR Invoices** = Sales invoices (customers owe YOU)
- **AP Invoices** = Purchase invoices (YOU owe suppliers)
- **Finance Invoices** = Legacy/generic invoices (may not be actively used)
- **Invoice Approvals** = Workflow tracking for both AR and AP

The AR and AP models are nearly identical in structure but serve opposite purposes (receivables vs payables). The Finance.Invoice model appears to be an older implementation that lacks the modern features like multi-currency support, approval workflow, and payment tracking that your AR/AP models have.

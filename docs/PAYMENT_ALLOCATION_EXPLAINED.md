# Payment Allocation & Invoice Lines Explained

## Overview
This document explains three key concepts in your FinanceERP system:
1. **ARPaymentAllocation** - How customer payments are allocated to invoices
2. **APPaymentAllocation** - How supplier payments are allocated to invoices
3. **ARItem/APItem vs InvoiceLine** - Invoice line item structures

---

## 1. ARPaymentAllocation - Customer Payment Allocation

### **What Problem Does It Solve?**
In real business, when a customer sends you money, they might:
- Pay for **one invoice completely** (e.g., pay $1,000 for Invoice #001)
- Pay for **multiple invoices** (e.g., pay $5,000 to cover Invoices #001, #002, #003)
- Make a **partial payment** (e.g., pay $500 on a $1,000 invoice)
- Make a **payment on account** (e.g., send $10,000 without specifying which invoices)

**ARPaymentAllocation** allows you to track exactly which invoices each payment covers.

### **The Model Structure:**

```python
class ARPayment(models.Model):
    """The payment record itself"""
    customer = ForeignKey(Customer)          # WHO paid
    reference = CharField(unique=True)       # Payment ref number (e.g., "PAY-2025-001")
    date = DateField()                       # When payment received
    total_amount = DecimalField()            # Total payment amount (e.g., $5,000)
    currency = ForeignKey(Currency)          # Payment currency
    bank_account = ForeignKey(BankAccount)   # Which bank account received it
    
    # Methods to track allocation
    def allocated_amount(self):
        """Sum of all allocations"""
        return sum(allocation.amount for allocation in self.allocations.all())
    
    def unallocated_amount(self):
        """Remaining amount not allocated to invoices"""
        return self.total_amount - self.allocated_amount()


class ARPaymentAllocation(models.Model):
    """Links payment to specific invoices"""
    payment = ForeignKey(ARPayment)          # WHICH payment
    invoice = ForeignKey(ARInvoice)          # WHICH invoice
    amount = DecimalField()                  # HOW MUCH allocated
    memo = CharField()                       # Optional notes
    
    class Meta:
        unique_together = [['payment', 'invoice']]  # Can't allocate same payment to same invoice twice
```

### **Real-World Example:**

**Scenario:** Customer "Emirates Trading LLC" sends you $5,000

```
Payment Record:
├── Customer: Emirates Trading LLC
├── Reference: PAY-2025-001
├── Date: 2025-10-16
├── Total Amount: $5,000
└── Bank Account: ADCB - USD Account

Allocations:
├── Allocation 1:
│   ├── Invoice: INV-001 (Amount due: $2,000)
│   └── Amount: $2,000  ✓ Fully paid
│
├── Allocation 2:
│   ├── Invoice: INV-002 (Amount due: $1,500)
│   └── Amount: $1,500  ✓ Fully paid
│
└── Allocation 3:
    ├── Invoice: INV-003 (Amount due: $3,000)
    └── Amount: $1,500  ⚠️ Partial payment

Summary:
- Total Payment: $5,000
- Allocated: $5,000 ($2,000 + $1,500 + $1,500)
- Unallocated: $0
```

### **Database Records:**

**ar_arpayment table:**
| id | customer_id | reference | date | total_amount | currency_id |
|----|-------------|-----------|------|--------------|-------------|
| 1  | 1 (Emirates Trading) | PAY-2025-001 | 2025-10-16 | 5000.00 | 2 (USD) |

**ar_arpaymentallocation table:**
| id | payment_id | invoice_id | amount | memo |
|----|------------|------------|--------|------|
| 1  | 1 | 10 (INV-001) | 2000.00 | Full payment |
| 2  | 1 | 11 (INV-002) | 1500.00 | Full payment |
| 3  | 1 | 12 (INV-003) | 1500.00 | Partial payment |

### **Invoice Payment Status Updates:**
After allocations are created:
- **INV-001**: payment_status = 'PAID' (fully paid)
- **INV-002**: payment_status = 'PAID' (fully paid)
- **INV-003**: payment_status = 'PARTIALLY_PAID' (only $1,500 of $3,000 paid)

---

## 2. APPaymentAllocation - Supplier Payment Allocation

### **What Problem Does It Solve?**
Same concept as AR, but in reverse - when YOU pay suppliers:
- Pay for **one supplier invoice** (e.g., pay $2,000 for Bill #B001)
- Pay for **multiple invoices** (e.g., pay $8,000 to cover Bills #B001, #B002, #B003)
- Make a **partial payment** (e.g., pay $1,000 on a $2,500 bill)
- Make an **advance payment** (e.g., send $5,000 before receiving invoices)

### **The Model Structure:**

```python
class APPayment(models.Model):
    """The payment record itself"""
    supplier = ForeignKey(Supplier)          # WHO you paid
    reference = CharField(unique=True)       # Payment ref number (e.g., "SUPP-PAY-001")
    date = DateField()                       # When you made payment
    total_amount = DecimalField()            # Total payment amount (e.g., $8,000)
    currency = ForeignKey(Currency)          # Payment currency
    bank_account = ForeignKey(BankAccount)   # Which bank account you paid from
    
    # Same allocation tracking methods
    def allocated_amount(self):
        return sum(allocation.amount for allocation in self.allocations.all())
    
    def unallocated_amount(self):
        return self.total_amount - self.allocated_amount()


class APPaymentAllocation(models.Model):
    """Links payment to specific supplier invoices"""
    payment = ForeignKey(APPayment)          # WHICH payment
    invoice = ForeignKey(APInvoice)          # WHICH invoice
    amount = DecimalField()                  # HOW MUCH allocated
    memo = CharField()                       # Optional notes
    
    class Meta:
        unique_together = [['payment', 'invoice']]
```

### **Real-World Example:**

**Scenario:** You pay "American Supplies Corp" $8,000

```
Payment Record:
├── Supplier: American Supplies Corp
├── Reference: SUPP-PAY-001
├── Date: 2025-10-16
├── Total Amount: $8,000
└── Bank Account: ADCB - USD Account

Allocations:
├── Allocation 1:
│   ├── Invoice: BILL-001 (Amount due: $3,000)
│   └── Amount: $3,000  ✓ Fully paid
│
├── Allocation 2:
│   ├── Invoice: BILL-002 (Amount due: $5,000)
│   └── Amount: $5,000  ✓ Fully paid
│
Summary:
- Total Payment: $8,000
- Allocated: $8,000 ($3,000 + $5,000)
- Unallocated: $0
```

---

## 3. Invoice Line Items - ARItem vs APItem vs InvoiceLine

### **What Are They?**
Invoice line items are the **individual products or services** listed on an invoice. Each line represents one item being sold or purchased.

### **Structure Comparison:**

#### **ARItem (Sales Invoice Lines)**
```python
class ARItem(models.Model):
    invoice = ForeignKey(ARInvoice)          # Which sales invoice
    description = CharField()                # Product/service description
    quantity = DecimalField()                # How many (e.g., 10 units)
    unit_price = DecimalField()              # Price per unit (e.g., $100)
    tax_rate = ForeignKey(TaxRate)           # Which tax rate applies
    tax_country = CharField()                # Tax country (AE/SA/EG/IN)
    tax_category = CharField()               # STANDARD/ZERO/EXEMPT/RC
    
    # Calculation done by frontend/API:
    # Line Total = quantity × unit_price
    # Tax Amount = Line Total × tax_rate.rate
    # Line Total with Tax = Line Total + Tax Amount
```

#### **APItem (Purchase Invoice Lines)**
```python
class APItem(models.Model):
    invoice = ForeignKey(APInvoice)          # Which purchase invoice
    description = CharField()                # Product/service description
    quantity = DecimalField()                # How many
    unit_price = DecimalField()              # Price per unit
    tax_rate = ForeignKey(TaxRate)           # Which tax rate
    tax_country = CharField()                # Tax country
    tax_category = CharField()               # Tax category
    
    # Same calculation logic as ARItem
```

#### **InvoiceLine (Finance/Legacy)**
```python
class InvoiceLine(models.Model):
    invoice = ForeignKey(Invoice)            # Which generic invoice
    description = CharField()
    account = ForeignKey(Account)            # GL account (more accounting-focused)
    tax_code = ForeignKey(TaxCode)           # Different tax structure
    
    quantity = DecimalField()
    unit_price = DecimalField()
    amount_net = DecimalField()              # Calculated net amount
    tax_amount = DecimalField()              # Calculated tax
    amount_gross = DecimalField()            # Calculated total
    
    def recompute(self):
        """Auto-calculates totals"""
        self.amount_net = self.quantity * self.unit_price
        self.tax_amount = self.amount_net * self.tax_code.rate
        self.amount_gross = self.amount_net + self.tax_amount
    
    def save(self):
        self.recompute()  # Auto-recalculates before saving
        super().save()
```

### **Key Differences:**

| Feature | ARItem / APItem | InvoiceLine |
|---------|-----------------|-------------|
| **Purpose** | Modern AR/AP invoices | Legacy/generic invoices |
| **Tax System** | TaxRate (country + category) | TaxCode (simple rate) |
| **Calculation** | Done by frontend/API | Auto-calculated in model |
| **Stored Totals** | No (calculated on-the-fly) | Yes (stored in DB) |
| **GL Account** | No (determined at posting) | Yes (stored on line) |
| **Flexibility** | Multi-country tax | Simple tax |
| **Currently Used** | ✅ Active | ⚠️ May be legacy |

### **Real-World Example - Sales Invoice:**

**Invoice:** INV-001 from "Emirates Trading LLC"

```
ARInvoice (Header):
├── Customer: Emirates Trading LLC
├── Number: INV-001
├── Date: 2025-10-16
├── Currency: AED
└── Country: AE (UAE - 5% VAT)

ARItem (Line Items):
├── Line 1:
│   ├── Description: "Laptop Computer"
│   ├── Quantity: 5
│   ├── Unit Price: AED 2,000
│   ├── Line Total: AED 10,000
│   ├── Tax Rate: 5% (UAE Standard VAT)
│   ├── Tax Amount: AED 500
│   └── Total: AED 10,500
│
├── Line 2:
│   ├── Description: "Computer Mouse"
│   ├── Quantity: 10
│   ├── Unit Price: AED 50
│   ├── Line Total: AED 500
│   ├── Tax Rate: 5% (UAE Standard VAT)
│   ├── Tax Amount: AED 25
│   └── Total: AED 525
│
└── Line 3:
    ├── Description: "Software License (Zero-rated)"
    ├── Quantity: 1
    ├── Unit Price: AED 5,000
    ├── Line Total: AED 5,000
    ├── Tax Rate: 0% (UAE Zero-rated)
    ├── Tax Amount: AED 0
    └── Total: AED 5,000

Invoice Summary:
├── Subtotal: AED 15,500
├── Tax: AED 525
└── Total: AED 16,025
```

### **Database Records:**

**ar_arinvoice table:**
| id | customer_id | number | date | currency_id | country |
|----|-------------|--------|------|-------------|---------|
| 1 | 1 (Emirates Trading) | INV-001 | 2025-10-16 | 1 (AED) | AE |

**ar_aritem table:**
| id | invoice_id | description | quantity | unit_price | tax_rate_id |
|----|------------|-------------|----------|------------|-------------|
| 1 | 1 | Laptop Computer | 5.00 | 2000.00 | 1 (5% VAT) |
| 2 | 1 | Computer Mouse | 10.00 | 50.00 | 1 (5% VAT) |
| 3 | 1 | Software License | 1.00 | 5000.00 | 2 (0% Zero) |

---

## Complete Workflow Example

### **Scenario:** Complete sales cycle with payment allocation

**Step 1: Create Sales Invoice**
```
Invoice: INV-001
Customer: Emirates Trading LLC
Items:
  - 5 Laptops @ AED 2,000 = AED 10,000 + AED 500 tax
  - 10 Mice @ AED 50 = AED 500 + AED 25 tax
Total: AED 10,525

Database:
  ar_arinvoice: 1 record
  ar_aritem: 2 records
  payment_status: 'UNPAID'
```

**Step 2: Customer Makes Payment**
```
Payment: PAY-001
Customer: Emirates Trading LLC
Amount: AED 10,525
Date: 2025-10-20

Database:
  ar_arpayment: 1 record
  total_amount: 10,525.00
```

**Step 3: Allocate Payment to Invoice**
```
Allocation:
  Payment: PAY-001 (AED 10,525)
  Invoice: INV-001 (AED 10,525)
  Amount: AED 10,525

Database:
  ar_arpaymentallocation: 1 record
  payment_id: 1
  invoice_id: 1
  amount: 10,525.00

Invoice Update:
  payment_status: 'UNPAID' → 'PAID' ✓
  paid_at: 2025-10-20
```

**Step 4: Check Allocation Status**
```python
payment = ARPayment.objects.get(reference='PAY-001')
print(payment.total_amount)        # 10,525.00
print(payment.allocated_amount())  # 10,525.00
print(payment.unallocated_amount()) # 0.00  ✓ Fully allocated
```

---

## Why Separate Payment and Allocation?

### **Old System (Direct Link):**
```python
# PROBLEM: One payment = One invoice only
class ARPayment:
    invoice = ForeignKey(ARInvoice)  # Can only link to ONE invoice
    amount = DecimalField()
```
❌ Can't handle partial payments
❌ Can't handle payment for multiple invoices
❌ Can't handle advance payments

### **New System (Allocation):**
```python
# SOLUTION: One payment = Many allocations
class ARPayment:
    total_amount = DecimalField()

class ARPaymentAllocation:
    payment = ForeignKey(ARPayment)   # One payment
    invoice = ForeignKey(ARInvoice)   # Can link to many invoices
    amount = DecimalField()            # Each with different amount
```
✅ Handle partial payments
✅ Handle payment for multiple invoices
✅ Handle advance payments (unallocated amount)
✅ Track exact payment history per invoice

---

## Summary

### **ARPaymentAllocation / APPaymentAllocation:**
- **Purpose:** Track which invoices each payment covers
- **Why:** Real payments often cover multiple invoices or partial amounts
- **How:** Creates a "bridge" record linking payment to invoice with specific amount
- **Benefit:** Complete flexibility in payment allocation

### **ARItem / APItem:**
- **Purpose:** Store individual line items on invoices
- **Why:** Invoices list multiple products/services with different prices and tax rates
- **How:** Each line has quantity, price, description, and tax information
- **Benefit:** Detailed invoice breakdown with proper tax calculation per item

### **InvoiceLine:**
- **Purpose:** Legacy invoice line structure
- **Difference:** Auto-calculates totals, stores GL accounts, simpler tax system
- **Status:** May not be actively used in current AR/AP workflows

---

## Database Table Summary

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `ar_arpayment` | Customer payment record | total_amount, customer, bank_account |
| `ar_arpaymentallocation` | Link payment → invoice | payment_id, invoice_id, amount |
| `ar_aritem` | Sales invoice line items | description, quantity, unit_price, tax_rate |
| `ap_appayment` | Supplier payment record | total_amount, supplier, bank_account |
| `ap_appaymentallocation` | Link payment → invoice | payment_id, invoice_id, amount |
| `ap_apitem` | Purchase invoice line items | description, quantity, unit_price, tax_rate |
| `finance_invoiceline` | Legacy invoice lines | amount_net, tax_amount, account |

The allocation system provides complete flexibility in managing complex payment scenarios that occur in real business operations!

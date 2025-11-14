# Updated Postman Collection - AR & AP Invoice/Payment Bodies

## ⚠️ IMPORTANT: Field Name Change

**ERROR:** `"GL distribution lines are required. Please add at least one GL line."`

**SOLUTION:** Use `distributions` field instead of `gl_lines` in your JSON request body.

```json
// ❌ OLD (Deprecated):
{
  "gl_lines": [...]
}

// ✅ NEW (Correct):
{
  "distributions": [...]
}
```

---

## Summary of Changes

This document summarizes the updated JSON request bodies for AR and AP Invoice and Payment endpoints in the ERP Finance System Postman Collection.

---

## 1. AR Invoice - Create (POST /api/ar/invoices/)

### ✅ UPDATED FORMAT

**Important:** Use `distributions` field (not `gl_lines`). The old `gl_lines` field is deprecated.

```json
{
  "customer": 1,
  "number": "ARINV-2025-001",
  "date": "2025-11-12",
  "due_date": "2025-12-12",
  "currency": 1,
  "country": "AE",
  "items": [
    {
      "description": "Product A - Premium",
      "quantity": "10.00",
      "unit_price": "500.00",
      "tax_rate": 1,
      "tax_country": "AE",
      "tax_category": "STANDARD"
    },
    {
      "description": "Product B - Standard",
      "quantity": "5.00",
      "unit_price": "300.00",
      "tax_rate": 1,
      "tax_country": "AE",
      "tax_category": "STANDARD"
    }
  ],
  "distributions": [
    {
      "amount": "6825.00",
      "description": "Revenue - Product Sales",
      "line_type": "CREDIT",
      "segments": [
        {"segment_type": 1, "segment": 2},
        {"segment_type": 2, "segment": 14},
        {"segment_type": 17, "segment": 24},
        {"segment_type": 999, "segment": 16}
      ]
    },
    {
      "amount": "6500.00",
      "description": "AR Account Debit - Customer Receivable",
      "line_type": "DEBIT",
      "segments": [
        {"segment_type": 1, "segment": 3},
        {"segment_type": 2, "segment": 14},
        {"segment_type": 17, "segment": 24},
        {"segment_type": 999, "segment": 16}
      ]
    },
    {
      "amount": "325.00",
      "description": "VAT Collected - UAE 5%",
      "line_type": "CREDIT",
      "segments": [
        {"segment_type": 1, "segment": 7},
        {"segment_type": 2, "segment": 14},
        {"segment_type": 17, "segment": 24},
        {"segment_type": 999, "segment": 16}
      ]
    }
  ]
}
```

**Calculation:**
- Item 1: 10 × $500 = $5,000
- Item 2: 5 × $300 = $1,500
- **Subtotal: $6,500**
- **Tax (5%): $325**
- **Total: $6,825**

**GL Entries:**
- DR Accounts Receivable: $6,825
- CR Revenue: $6,500
- CR VAT Payable: $325

---

## 2. AR Payment - Create (POST /api/ar/payments/)

### ✅ UPDATED FORMAT

```json
{
  "customer": 1,
  "reference": "ARPAY-2025-001",
  "date": "2025-11-12",
  "total_amount": "515.00",
  "currency": 1,
  "memo": "Payment for multiple invoices",
  "bank_account": 1,
  "allocations": [
    {
      "invoice": 6,
      "amount": "100.00",
      "memo": "Full payment for invoice #6"
    },
    {
      "invoice": 7,
      "amount": "100.00",
      "memo": "Full payment for invoice #7"
    },
    {
      "invoice": 5,
      "amount": "315.00",
      "memo": "Partial payment for invoice #5"
    }
  ],
  "distributions": [
    {
      "amount": "515.00",
      "description": "Bank Account Debit - Payment received",
      "line_type": "DEBIT",
      "segments": [
        {"segment_type": 1, "segment": 11},
        {"segment_type": 2, "segment": 14},
        {"segment_type": 17, "segment": 24},
        {"segment_type": 999, "segment": 16}
      ]
    },
    {
      "amount": "515.00",
      "description": "AR Account Credit - Reduce receivable",
      "line_type": "CREDIT",
      "segments": [
        {"segment_type": 1, "segment": 3},
        {"segment_type": 2, "segment": 14},
        {"segment_type": 17, "segment": 24},
        {"segment_type": 999, "segment": 16}
      ]
    }
  ]
}
```

**Allocations:**
- Invoice #6: $100.00 (full)
- Invoice #7: $100.00 (full)
- Invoice #5: $315.00 (partial)
- **Total: $515.00**

**GL Entries:**
- DR Bank Account: $515.00
- CR Accounts Receivable: $515.00

---

## 3. AP Invoice - Create (POST /api/ap/invoices/)

### ✅ UPDATED FORMAT

**Important:** Use `distributions` field (not `gl_lines`). The old `gl_lines` field is deprecated.

```json
{
  "supplier": 2,
  "number": "APINV-2025-001",
  "date": "2025-11-12",
  "due_date": "2025-12-12",
  "currency": 1,
  "country": "AE",
  "items": [
    {
      "description": "Office Supplies - Paper & Stationery",
      "quantity": "50.00",
      "unit_price": "25.00",
      "tax_rate": 1,
      "tax_country": "AE",
      "tax_category": "STANDARD"
    },
    {
      "description": "Computer Equipment - Keyboards",
      "quantity": "10.00",
      "unit_price": "75.00",
      "tax_rate": 1,
      "tax_country": "AE",
      "tax_category": "STANDARD"
    }
  ],
  "distributions": [
    {
      "amount": "1968.75",
      "description": "Expense - Office Supplies & Equipment",
      "line_type": "DEBIT",
      "segments": [
        {"segment_type": 1, "segment": 10},
        {"segment_type": 2, "segment": 14},
        {"segment_type": 17, "segment": 26},
        {"segment_type": 999, "segment": 16}
      ]
    },
    {
      "amount": "1875.00",
      "description": "AP Account Credit - Vendor Payable",
      "line_type": "CREDIT",
      "segments": [
        {"segment_type": 1, "segment": 4},
        {"segment_type": 2, "segment": 14},
        {"segment_type": 17, "segment": 26},
        {"segment_type": 999, "segment": 16}
      ]
    },
    {
      "amount": "93.75",
      "description": "VAT Recoverable - UAE 5%",
      "line_type": "DEBIT",
      "segments": [
        {"segment_type": 1, "segment": 8},
        {"segment_type": 2, "segment": 14},
        {"segment_type": 17, "segment": 26},
        {"segment_type": 999, "segment": 16}
      ]
    }
  ]
}
```

**Calculation:**
- Item 1: 50 × $25 = $1,250
- Item 2: 10 × $75 = $750
- **Subtotal: $1,875**
- **Tax (5%): $93.75**
- **Total: $1,968.75**

**GL Entries:**
- DR Operating Expenses: $1,875
- DR VAT Recoverable: $93.75
- CR Accounts Payable: $1,968.75

---

## 4. AP Payment - Create (POST /api/ap/payments/)

### ✅ NEEDS UPDATE

**Current Format (OLD):**
```json
{
  "vendor": 1,
  "payment_date": "2025-11-12",
  "amount": "2300.00",
  "currency": 1,
  "payment_method": "bank_transfer",
  "reference": "VPAY-2025-001"
}
```

**Recommended New Format:**
```json
{
  "supplier": 2,
  "reference": "VPAY-2025-001",
  "date": "2025-11-12",
  "total_amount": "7040.00",
  "currency": 1,
  "memo": "Payment for multiple invoices",
  "bank_account": 1,
  "allocations": [
    {
      "invoice": 24,
      "amount": "2280.00",
      "memo": "Payment for VINV-2025-111"
    },
    {
      "invoice": 25,
      "amount": "2280.00",
      "memo": "Payment for VINV-2025-116"
    },
    {
      "invoice": 26,
      "amount": "2480.00",
      "memo": "Payment for VINV-2025-123"
    }
  ],
  "distributions": [
    {
      "amount": "7040.00",
      "description": "Bank Account Debit - Payment to supplier",
      "line_type": "DEBIT",
      "segments": [
        {"segment_type": 1, "segment": 11},
        {"segment_type": 2, "segment": 14},
        {"segment_type": 17, "segment": 24},
        {"segment_type": 999, "segment": 16}
      ]
    },
    {
      "amount": "7040.00",
      "description": "AP Account Credit - Reduce liability",
      "line_type": "CREDIT",
      "segments": [
        {"segment_type": 1, "segment": 4},
        {"segment_type": 2, "segment": 14},
        {"segment_type": 17, "segment": 24},
        {"segment_type": 999, "segment": 16}
      ]
    }
  ]
}
```

**Allocations:**
- Invoice #24: $2,280.00
- Invoice #25: $2,280.00
- Invoice #26: $2,480.00
- **Total: $7,040.00**

**GL Entries:**
- DR Bank Account: $7,040.00
- CR Accounts Payable: $7,040.00

---

## Key Changes Summary

### ✅ What Changed:

1. **Field Names Updated:**
   - `invoice_number` → `number`
   - `invoice_date` → `date`
   - `payment_date` → `date`
   - `vendor` → `supplier` (AP)
   - `amount` → `total_amount`
   - **`gl_lines` → `distributions`** (Critical: Use `distributions` not `gl_lines`)

2. **New Required Fields:**
   - `country`: Tax country code (e.g., "AE")
   - `items`: Array of line items with description, quantity, unit_price, tax_rate
   - `distributions`: Array of GL distribution lines

3. **Distribution Structure:**
   - `amount`: Always positive
   - `description`: GL line description
   - `line_type`: "DEBIT" or "CREDIT" (required)
   - `segments`: Array of segment assignments (must include all required segment types)

4. **Payment Allocations:**
   - `allocations`: Array linking payment to specific invoices
   - Each allocation has: `invoice` (ID), `amount`, `memo`
   - Sum of allocations must equal `total_amount`

5. **Removed Fields:**
   - `subtotal`, `tax_amount`, `total_amount` from invoice header (calculated from items)
   - `status` (managed by system)
   - `payment_method` (payment method tracked elsewhere)

### ✅ Segment Types Required:

All distributions must include these segment types:

1. **Account (Type 1)** - Required
2. **company (Type 2)** - Required
3. **Department (Type 17)** - Required
4. **Test Segment (Type 999)** - Required
5. **ref (Type 40)** - Optional

### ✅ Common Segment IDs:

**Accounts (Type 1):**
- 2: Revenue Account
- 3: Accounts Receivable
- 4: Accounts Payable
- 7: VAT Payable
- 8: VAT Recoverable
- 10: Operating Expenses
- 11: Bank Account - Main

**Company (Type 2):**
- 14: Main Company

**Department (Type 17):**
- 24: Sales
- 25: Operations
- 26: Finance

**Test Segment (Type 999):**
- 16: Test Value 1
- 17: Test Value 2

---

## Validation Rules

### Invoice Distributions:
✅ Total DEBIT amounts must equal total CREDIT amounts  
✅ Distributions must balance to invoice total (subtotal + tax)  
✅ Each distribution line must have all required segment types  
✅ Segment IDs must be valid child segments  
✅ Amount must be positive (use line_type for direction)  

### Payment Allocations:
✅ Sum of allocations must equal total_amount  
✅ Invoice IDs must exist and belong to customer/supplier  
✅ Each allocation must reference a valid invoice  
✅ Payment currency should match invoice currency (or handle FX)  

---

## Migration Path

### For Existing API Clients:

1. **Update field names** in request bodies
2. **Add items array** with line item details
3. **Add distributions array** with multi-segment GL coding
4. **Add allocations array** for payments (link to invoices)
5. **Remove calculated fields** (subtotal, tax_amount, total_amount from header)
6. **Test with valid segment IDs** from your database

---

## Testing Checklist

- [ ] AR Invoice creation with items and distributions
- [ ] AR Payment creation with allocations and distributions
- [ ] AP Invoice creation with items and distributions
- [ ] AP Payment creation with allocations and distributions (NEEDS UPDATE IN COLLECTION)
- [ ] Validate segment IDs exist in database
- [ ] Verify debits equal credits in distributions
- [ ] Confirm allocations sum to payment total
- [ ] Test with multiple segment types

---

## Status

| Endpoint | Status | Notes |
|----------|--------|-------|
| AR Invoice | ✅ Updated | Complete with items & distributions |
| AR Payment | ✅ Updated | Complete with allocations & distributions |
| AP Invoice | ✅ Updated | Complete with items & distributions |
| AP Payment | ⚠️ Needs Update | Still using old format, update recommended |

---

## Next Steps

1. ✅ AR Invoice and AR Payment endpoints are fully updated
2. ✅ AP Invoice endpoint is fully updated
3. ⚠️ **Update AP Payment endpoint** in Postman collection to match new format
4. 🔄 Test all endpoints with valid invoice IDs from database
5. 📝 Update any API documentation or client SDKs

---

*Last Updated: November 12, 2025*

# Quick Setup Guide - AP Invoice Edit Page

## Create AP Edit Page

The AP invoice edit page should be created at:
`frontend/src/app/ap/invoices/[id]/edit/page.tsx`

## Changes from AR Edit Page

Replace the following in the AR edit page code:

1. **Imports:**
   - `arInvoicesAPI` → `apInvoicesAPI`
   - `customersAPI` → `suppliersAPI`
   - `ARInvoiceItem` → `APInvoiceItem`
   - `Customer` → `Supplier`

2. **Component Name:**
   - `EditARInvoicePage` → `EditAPInvoicePage`

3. **State Variables:**
   - `customers` → `suppliers`
   - `setCustomers` → `setSuppliers`

4. **Functions:**
   - `handleCustomerChange` → `handleSupplierChange`
   - Update parameter: `customerId` → `supplierId`
   - Find logic: `customers.find` → `suppliers.find`

5. **Form Fields:**
   - Label "Customer *" → "Supplier *"
   - Field name `customer` everywhere → `supplier`

6. **API Calls:**
   - `customersAPI.list()` → `suppliersAPI.list()`
   - `arInvoicesAPI.get()` → `apInvoicesAPI.get()`
   - `arInvoicesAPI.update()` → `apInvoicesAPI.update()`

7. **Routes:**
   - `/ar/invoices` → `/ap/invoices`

8. **Title:**
   - "Edit AR Invoice" → "Edit AP Invoice"

9. **Data Structure:**
   - `formData.customer` → `formData.supplier`
   - `invoice.customer` → `invoice.supplier`
   - `invoiceData.customer` → `invoiceData.supplier`

## Manual Creation Steps

If creating manually:

1. Copy `frontend/src/app/ar/invoices/[id]/edit/page.tsx`
2. Save as `frontend/src/app/ap/invoices/[id]/edit/page.tsx`
3. Use Find & Replace:
   - Find: `arInvoicesAPI` → Replace: `apInvoicesAPI`
   - Find: `customersAPI` → Replace: `suppliersAPI`
   - Find: `ARInvoiceItem` → Replace: `APInvoiceItem`
   - Find: `Customer` → Replace: `Supplier` (careful with label text)
   - Find: `customers` → Replace: `suppliers` (variable names)
   - Find: `customer` → Replace: `supplier` (field names)
   - Find: `/ar/invoices` → Replace: `/ap/invoices`
   - Find: `EditARInvoicePage` → Replace: `EditAPInvoicePage`
   - Find: `Edit AR Invoice` → Replace: `Edit AP Invoice`
   - Find: `handleCustomerChange` → Replace: `handleSupplierChange`
   - Find: `customerId` → Replace: `supplierId`

## Result

The AP edit page will function identically to the AR edit page but work with suppliers instead of customers.

---

**Status:** Instructions provided  
**Next:** Create the AP edit page following these instructions

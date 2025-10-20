# 🎯 Corporate Tax Management - Quick Reference

## 📍 Access
**URL**: `/tax/corporate`
**Dashboard Icon**: Building2 (Purple)

---

## 🔄 Quick Workflows

### Create Quarterly Tax Accrual
1. Go to `/tax/corporate`
2. Stay on "Tax Accrual" tab
3. Enter period dates (e.g., 2025-01-01 to 2025-03-31)
4. Enter tax rate (e.g., 9 for UAE)
5. Click "Create Tax Accrual"
6. ✅ System creates journal entry and filing record

### View Tax Analysis
1. Go to `/tax/corporate`
2. Click "Tax Breakdown" tab
3. Select period (e.g., full year 2024)
4. Click "Load Breakdown"
5. 📊 View summary cards and all filings

### File a Tax Return
1. In breakdown view, find ACCRUED filing
2. Click "View" to see details
3. Click "File Tax Return"
4. ✅ Status changes to FILED, date recorded

### Reverse a Filing
1. Find FILED return in breakdown
2. Click "View" button
3. Click "Reverse Filing"
4. ✅ Creates reversing journal entry

---

## 📊 Status Meanings

| Status | Icon | Color | Meaning |
|--------|------|-------|---------|
| DRAFT | ⚠️ | Gray | Not calculated yet |
| ACCRUED | ✅ | Blue | Tax calculated, JE created |
| FILED | 📄 | Green | Submitted to authorities |
| PAID | ✅ | Purple | Payment completed |
| REVERSED | ❌ | Red | Corrected/reversed |

---

## 💡 Common Tasks

### Monthly Accrual
```
Period: 2025-01-01 to 2025-01-31
Rate: 9%
Result: Monthly tax provision
```

### Quarterly Filing
```
Period: 2025-01-01 to 2025-03-31
Rate: 9%
Result: Quarterly tax return
```

### Annual Reconciliation
```
Breakdown Period: 2024-01-01 to 2024-12-31
View: All 12 monthly or 4 quarterly filings
Total: Annual tax obligation
```

### Correction Process
```
1. Find incorrect filing
2. Click "Reverse" (creates reversing JE)
3. Create new accrual with correct data
4. File corrected return
```

---

## 🧮 How Tax is Calculated

```
Revenue (all income accounts)
- Expenses (all expense accounts)
= Net Income
× Tax Rate
= Tax Amount

Journal Entry:
Dr. Corporate Tax Expense    [Tax Amount]
   Cr. Corporate Tax Payable [Tax Amount]
```

---

## 📋 Summary Dashboard

**Revenue Card (Green)**: Total income for period
**Expenses Card (Red)**: Total costs for period
**Taxable Income Card (Blue)**: Net profit/loss
**Tax Amount Card (Purple)**: Tax owed @ rate

---

## ⚙️ Backend Endpoints

- `POST /api/corporate-tax/accrual/` - Create accrual
- `GET /api/corporate-tax/breakdown/` - Get analysis
- `GET /api/corporate-tax/filing/{id}/` - Get filing details
- `POST /api/corporate-tax/filing/{id}/file/` - File return
- `POST /api/corporate-tax/filing/{id}/reverse/` - Reverse filing

---

## ✅ Best Practices

1. **Regular Accruals**: Create monthly or quarterly
2. **Review First**: Always view details before filing
3. **Documentation**: Note journal entry numbers
4. **Corrections**: Use reverse function, don't delete
5. **Year-End**: Run full-year breakdown for reconciliation
6. **Audit Trail**: All actions timestamped and tracked

---

## 🚨 Important Notes

- ⚠️ Accrual creates immediate journal entry
- ⚠️ Filing cannot be undone (use reverse instead)
- ⚠️ Tax rate must match local regulations
- ⚠️ Period dates must not overlap existing filings
- ⚠️ Reversal creates new journal entry (doesn't delete original)

---

## 📞 Related Features

- **Journal Entries** (`/journals`): View created JE entries
- **Reports** (`/reports`): Tax reports and summaries
- **Tax Rates** (`/tax-rates`): VAT/Sales tax (different feature)
- **Accounts** (`/accounts`): Configure tax expense/payable accounts

---

## 🎓 Example: UAE Corporate Tax (9%)

### Q1 2025 Accrual
```
Period: Jan 1 - Mar 31, 2025
Rate: 9%

Assuming:
Revenue: 500,000 AED
Expenses: 350,000 AED

Result:
Taxable Income: 150,000 AED
Tax @ 9%: 13,500 AED

Journal:
Dr. Corporate Tax Expense    13,500
   Cr. Corporate Tax Payable 13,500
```

---

**Last Updated**: January 2025
**Version**: 1.0
**Status**: Production Ready

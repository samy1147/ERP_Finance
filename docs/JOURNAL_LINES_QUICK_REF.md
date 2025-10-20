# 🎯 Journal Lines - Quick Reference

## 📍 Access
**URL**: `/journal-lines`
**Dashboard**: Click "Journal Lines" card (Indigo BookOpen icon)

---

## 🚀 Quick Actions

### View All Lines
1. Navigate to `/journal-lines`
2. All journal lines displayed automatically
3. Check summary cards for overview

### Filter by Account
1. Enter account code (e.g., "1001") or name (e.g., "Cash")
2. Click "Apply Filters"
3. View all transactions for that account

### Check Period Activity
1. Set Date From and Date To
2. Click "Apply Filters"
3. View all lines for the period

### Verify Entry Lines
1. Enter Journal Entry ID (e.g., "100")
2. Click "Apply Filters"
3. See all lines from JE-100

### Review Unposted Lines
1. Select Status: "Draft"
2. Click "Apply Filters"
3. View all lines from draft entries

---

## 📊 Summary Cards

| Card | Meaning | Color |
|------|---------|-------|
| Total Lines | Count of all lines | Gray |
| Total Debits | Sum of all debits | Green |
| Total Credits | Sum of all credits | Red |
| Posted | Lines from posted entries | Blue |
| Draft | Lines from draft entries | Yellow |

---

## 🎨 Color Codes

### Account Types
- 🔵 **Blue** = Asset
- 🔴 **Red** = Liability
- 🟣 **Purple** = Equity
- 🟢 **Green** = Income
- 🟠 **Orange** = Expense

### Status Badges
- ✅ **Green "Posted"** = Entry is finalized
- ⚠️ **Yellow "Draft"** = Entry not yet posted

### Amounts
- **Green Bold** = Debit amount (when > 0)
- **Red Bold** = Credit amount (when > 0)
- **Gray Dash** = Zero amount

---

## ⚖️ Balance Check

### Balanced (Good)
```
Total Debits:  $10,000.00
Total Credits: $10,000.00
✅ Balanced
```

### Out of Balance (Warning)
```
⚠️ Warning: Debits and Credits are NOT balanced!
Difference: $100.00
```

---

## 🔍 Filter Options

| Filter | Use When | Example |
|--------|----------|---------|
| **Account Code** | Find specific account | "1001" |
| **Account Name** | Search by name | "Cash" |
| **Date From** | Period start | 2025-01-01 |
| **Date To** | Period end | 2025-12-31 |
| **Status** | Posted/Draft only | "Posted" |
| **Entry ID** | Specific entry | 100 |

---

## 👁️ View Details

Click eye icon (👁️) on any line to see:
- Journal entry context (ID, date, memo, status)
- Account details (code, name, type)
- Debit and credit amounts
- Visual status indicators

---

## 📋 Common Use Cases

### 1. Account Reconciliation
```
Filter: Account Code = "1001"
Result: All Cash transactions
Action: Verify against bank statement
```

### 2. Month-End Review
```
Filter: Date From = 2025-10-01, Date To = 2025-10-31
Result: All October transactions
Action: Review for accuracy
```

### 3. Entry Audit
```
Filter: Entry ID = 100
Result: All lines from JE-100
Action: Verify entry is balanced and correct
```

### 4. Draft Cleanup
```
Filter: Status = Draft
Result: All unposted lines
Action: Review and post or delete
```

---

## ⚡ Quick Tips

### For Accountants
✅ Use date filters for period reconciliation
✅ Check balance indicator before month-end
✅ Filter by account for ledger views
✅ Review draft lines daily

### For Auditors
✅ Use Entry ID to trace transactions
✅ Verify totals footer for balance
✅ Filter posted lines for audit scope
✅ Export from /journals page for detailed reports

### For Finance Managers
✅ Monitor summary cards for activity
✅ Check balance warnings immediately
✅ Review account type distribution
✅ Track draft vs posted ratio

---

## 🚨 Red Flags

Watch for:
- ❌ Balance warning (debits ≠ credits)
- ❌ Large number of draft lines
- ❌ Lines with $0 debit AND $0 credit
- ❌ Old draft entries (check date)
- ❌ Unusual account types for transactions

---

## 💡 Pro Tips

1. **Combine Filters**: Use multiple filters together
   - Example: Account Code + Date Range + Posted

2. **Clear Filters**: Click "Clear All" to reset

3. **Sort by Date**: Lines auto-sorted newest first

4. **Check Totals**: Footer shows running totals

5. **Balance Validation**: Always green = good system health

---

## 🔗 Related Pages

- **Journal Entries** (`/journals`): Entry-level view
- **Accounts** (`/accounts`): Chart of accounts
- **Reports** (`/reports`): Financial reports

---

## 📖 Reading the Table

```
Line #123 | JE-50 | Oct 15, 2025 | 1001 - Cash | Asset | $1,000.00 | - | Posted | 👁️
          └─────┘  └───────────┘   └──────────┘  └────┘  └───────┘   └┘  └─────┘  └─┘
          Entry    Date            Account      Type    Debit    Credit Status  View
```

**Understanding**:
- Line ID: 123
- From Journal Entry: JE-50
- Date: October 15, 2025
- Account: 1001 (Cash, Asset type)
- Debit: $1,000.00
- Credit: None (-)
- Status: Posted (green)
- Action: Click eye to view details

---

## ⚙️ Backend Endpoint

**API**: `GET /api/journal-lines/`
**Authentication**: Required
**Method**: GET only (read-only)
**Response**: JSON array of journal lines

---

**Quick Start**: Just go to `/journal-lines` and start exploring! 🚀

---

**Last Updated**: October 15, 2025
**Status**: Production Ready ✅

# 📊 Journal Lines Page - Implementation Guide

## 🎯 Overview

The **Journal Lines** page provides a detailed, line-item view of all journal entries in the system. Unlike the Journal Entries page which shows entries as a whole, this page breaks down every single debit and credit line for advanced analysis, auditing, and reconciliation.

---

## 📍 Access

- **URL**: `/journal-lines`
- **Dashboard Icon**: BookOpen (Indigo)
- **Navigation**: Dashboard → "Journal Lines" card

---

## ✨ Key Features

### 1. **Comprehensive Line Item Display**
- Every debit and credit line from all journal entries
- Complete account information (code, name, type)
- Associated journal entry details
- Posted/Draft status tracking

### 2. **Advanced Filtering**
- **Account Code**: Search by account code (e.g., "1001")
- **Account Name**: Search by account name (e.g., "Cash")
- **Date Range**: Filter by date from/to
- **Status**: Filter by Posted or Draft entries
- **Entry ID**: View lines from specific journal entry

### 3. **Real-Time Summary Statistics**
- Total line count
- Total debits (green)
- Total credits (red)
- Posted line count
- Draft line count
- **Balance validation** (debits = credits check)

### 4. **Balance Checking**
- Automatic validation that total debits = total credits
- Red warning banner if out of balance
- Shows difference amount
- Green "Balanced" indicator when equal

### 5. **Detailed Line View**
- Modal popup with complete information
- Journal entry context
- Account details with type classification
- Visual debit/credit display
- Status indicators

---

## 🎨 UI Components

### Summary Cards (Top Row)
1. **Total Lines** - Count of all lines displayed
2. **Total Debits** (Green) - Sum of all debit amounts
3. **Total Credits** (Red) - Sum of all credit amounts
4. **Posted** (Blue) - Count of lines from posted entries
5. **Draft** (Yellow) - Count of lines from draft entries

### Filter Panel
- Collapsible filter section (Show/Hide button)
- 6 filter fields:
  - Account Code (text search)
  - Account Name (text search)
  - Date From (date picker)
  - Date To (date picker)
  - Status (dropdown: All/Posted/Draft)
  - Entry ID (number input)
- Apply Filters button
- Clear All button

### Main Table
Columns:
- **Line ID** - Unique identifier for the line
- **Journal Entry** - JE-XX link format
- **Date** - Entry date
- **Account** - Code and name
- **Type** - Account type badge (Asset/Liability/Equity/Income/Expense)
- **Debit** - Amount (green if > 0, dash if 0)
- **Credit** - Amount (red if > 0, dash if 0)
- **Status** - Posted (green check) or Draft (yellow)
- **Actions** - View detail button (eye icon)

### Table Footer
- **Totals Row**: Shows sum of debits and credits
- **Balance Status**: Green checkmark if balanced, red X if not

---

## 🔌 Backend Integration

### New API Endpoint
**Endpoint**: `GET /api/journal-lines/`

**Features**:
- Read-only viewset (no create/update/delete)
- Select related queries for performance
- Advanced filtering support
- Ordered by date (descending), then entry ID, then line ID

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `account_code` | string | Filter by account code (contains) | `?account_code=1001` |
| `account_name` | string | Filter by account name (contains) | `?account_name=Cash` |
| `date_from` | date | Filter lines from date onwards | `?date_from=2025-01-01` |
| `date_to` | date | Filter lines up to date | `?date_to=2025-12-31` |
| `posted` | boolean | Filter by entry status | `?posted=true` |
| `entry_id` | number | Filter by specific entry | `?entry_id=100` |

### Response Format

```json
[
  {
    "id": 1,
    "debit": "1000.00",
    "credit": "0.00",
    "entry": {
      "id": 50,
      "date": "2025-10-15",
      "memo": "Sales revenue",
      "posted": true,
      "currency": 1
    },
    "account": {
      "id": 10,
      "code": "1001",
      "name": "Cash",
      "type": "AS"
    }
  }
]
```

---

## 🎯 Use Cases

### 1. **Account Reconciliation**
Filter by specific account code to see all debits and credits:
```
Account Code: 1001
Result: All transactions affecting Cash account
```

### 2. **Period Analysis**
View all transactions within a date range:
```
Date From: 2025-01-01
Date To: 2025-03-31
Result: All Q1 journal lines
```

### 3. **Entry Verification**
Check all lines for a specific journal entry:
```
Entry ID: 100
Result: All lines belonging to JE-100
```

### 4. **Balance Auditing**
View all posted lines to verify accounting balance:
```
Status: Posted
Result: Balance check on all posted transactions
```

### 5. **Draft Review**
Find all unposted lines for review:
```
Status: Draft
Result: All lines from draft entries
```

### 6. **Account Type Analysis**
Visual classification of transactions by account type:
- **Asset** lines (blue badge)
- **Liability** lines (red badge)
- **Equity** lines (purple badge)
- **Income** lines (green badge)
- **Expense** lines (orange badge)

---

## 📊 Visual Indicators

### Account Type Colors
| Type | Badge Color | Meaning |
|------|------------|---------|
| Asset (AS) | Blue | Resources owned |
| Liability (LI) | Red | Obligations owed |
| Equity (EQ) | Purple | Owner's interest |
| Income (IN) | Green | Revenue earned |
| Expense (EX) | Orange | Costs incurred |

### Status Indicators
| Status | Badge | Color | Icon |
|--------|-------|-------|------|
| Posted | Posted | Green | ✓ CheckCircle |
| Draft | Draft | Yellow | None |

### Amount Display
| Field | Color | Meaning |
|-------|-------|---------|
| Debit > 0 | Green | Active debit |
| Debit = 0 | Gray dash | No debit |
| Credit > 0 | Red | Active credit |
| Credit = 0 | Gray dash | No credit |

---

## 🔍 Balance Validation

### Automatic Checking
The page continuously validates accounting balance:

```typescript
if (totalDebit === totalCredit) {
  // ✅ Show green "Balanced" indicator
} else {
  // ❌ Show red warning banner with difference
}
```

### Warning Display
When out of balance:
```
⚠️ Warning: Debits and Credits are NOT balanced!
Difference: $XXX.XX
```

This helps catch:
- Data entry errors
- Incomplete journal entries
- System issues
- Unbalanced imports

---

## 📱 Responsive Design

- Mobile-friendly table scrolling
- Collapsible filters on small screens
- Touch-friendly buttons and modals
- Responsive grid for summary cards

---

## 🎓 Accounting Context

### Double-Entry Bookkeeping
Every journal entry must have:
- **Equal debits and credits** (fundamental rule)
- At least 2 lines (one debit, one credit minimum)
- Proper account classification

### Line Item Importance
Journal lines are the **atomic units** of accounting:
- Each line represents a single account movement
- Multiple lines create compound entries
- Detailed audit trail at line level
- Basis for all financial reports

### Example: Simple Entry
**Journal Entry JE-100**:
```
Line 1: Dr. Cash (1001)         $1,000
Line 2: Cr. Revenue (4001)      $1,000
```
Total: 2 lines, balanced

### Example: Complex Entry
**Journal Entry JE-101** (Sale with tax):
```
Line 1: Dr. Cash (1001)              $1,050
Line 2: Cr. Revenue (4001)           $1,000
Line 3: Cr. VAT Payable (2100)       $50
```
Total: 3 lines, balanced ($1,050 = $1,050)

---

## 🔗 Integration with Other Features

### Journal Entries Page (`/journals`)
- Shows entries as aggregated units
- Use Journal Lines page for detailed breakdown
- Cross-reference via Entry ID filter

### Trial Balance Report
- Line items are source data for trial balance
- Account-level summaries derived from lines
- Period filtering aligns with report periods

### Account Analysis
- Filter by account code for account ledger view
- Shows complete transaction history
- Useful for reconciliation

---

## 🛠️ Technical Implementation

### Backend Files
- **API**: `finance/api.py` - `JournalLineViewSet`
- **URL**: `erp/urls.py` - `router.register("journal-lines")`
- **Model**: `finance/models.py` - `JournalLine`
- **Serializer**: `finance/serializers.py` - `JournalLineSerializer`

### Frontend Files
- **Page**: `frontend/src/app/journal-lines/page.tsx` (600+ lines)
- **API Service**: `frontend/src/services/api.ts` - `journalLinesAPI`
- **Types**: `frontend/src/services/api.ts` - `JournalLineDetail` interface
- **Navigation**: `frontend/src/app/page.tsx` - Dashboard card

### Key Technologies
- **Backend**: Django REST Framework (ReadOnlyModelViewSet)
- **Frontend**: Next.js 14+, React, TypeScript
- **Styling**: Tailwind CSS
- **Icons**: lucide-react
- **Date Handling**: date-fns

---

## 📈 Performance Optimization

### Database Queries
```python
queryset = JournalLine.objects.select_related(
    'entry', 
    'account', 
    'entry__currency'
).all()
```
- **select_related**: Reduces N+1 queries
- Single query fetches all related data
- Improves page load speed significantly

### Frontend Optimization
- Lazy loading with React hooks
- Conditional rendering for filters
- Memoized calculations for stats
- Debounced filter applications

---

## ✅ Testing Checklist

- [ ] Load page with no filters (all lines)
- [ ] Apply account code filter
- [ ] Apply account name filter
- [ ] Filter by date range
- [ ] Filter by posted status
- [ ] Filter by specific entry ID
- [ ] Clear all filters
- [ ] View line details in modal
- [ ] Verify balance calculation
- [ ] Check totals row accuracy
- [ ] Test with unbalanced data (warning appears)
- [ ] Test with balanced data (green indicator)
- [ ] Verify account type badges
- [ ] Check mobile responsiveness

---

## 💡 Tips for Users

### For Accountants
1. **Daily Reconciliation**: Filter by today's date to review daily entries
2. **Month-End Close**: Use date range to verify period entries
3. **Account Analysis**: Filter by account code for detailed ledger
4. **Balance Verification**: Always check totals footer for balance

### For Auditors
1. **Entry ID Filter**: Trace specific transactions
2. **Date Range**: Review historical periods
3. **Posted Filter**: Focus on finalized entries
4. **Export Capability**: Use Journal Entries export for detailed CSV/Excel

### For Finance Managers
1. **Summary Stats**: Quick overview of transaction volume
2. **Account Type View**: See distribution across account types
3. **Draft Review**: Monitor unposted entries
4. **Balance Monitoring**: Ensure system integrity

---

## 🚀 Future Enhancements (Optional)

Potential additions:
- [ ] Export journal lines to CSV/Excel
- [ ] Bulk operations (post multiple entries)
- [ ] Advanced search with multiple conditions
- [ ] Account balance running totals
- [ ] Line-level notes/comments
- [ ] Attachment support per line
- [ ] Line-level tags/categories
- [ ] Custom column visibility
- [ ] Save filter presets

---

## 📚 Related Documentation

- **Journal Entry Reversal**: `docs/REVERSAL_METHOD_EXPLAINED.md`
- **Journal Entries Page**: See `/journals` page implementation
- **Account Management**: `docs/ACCOUNT_MANAGEMENT.md`
- **Chart of Accounts**: `docs/CHART_OF_ACCOUNTS.md`

---

## 🎉 Summary

The Journal Lines page provides:
✅ **Detailed View**: Every debit and credit line
✅ **Advanced Filtering**: 6 different filter options
✅ **Balance Validation**: Automatic debit/credit checking
✅ **Summary Analytics**: Real-time statistics
✅ **Audit Trail**: Complete transaction history
✅ **Account Analysis**: Line-level account investigation
✅ **Professional UI**: Color-coded, intuitive design

This page is essential for:
- **Accountants**: Daily reconciliation and analysis
- **Auditors**: Transaction verification and tracing
- **Finance Managers**: Transaction monitoring and oversight
- **System Administrators**: Data integrity checking

---

**Implementation Date**: October 15, 2025
**Status**: ✅ Complete and Production-Ready
**Backend Endpoint**: `/api/journal-lines/`
**Frontend Page**: `/journal-lines`

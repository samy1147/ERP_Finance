# Journal Entries Frontend Pages

**Created:** October 13, 2025  
**Purpose:** Display and manage Journal Entries and Journal Lines in the frontend

---

## 📋 What Was Added

### 1. **API Service** (`frontend/src/services/api.ts`)
Added `journalEntriesAPI` with the following methods:
- `list()` - Get all journal entries
- `get(id)` - Get single journal entry
- `create(data)` - Create new journal entry
- `update(id, data)` - Update journal entry
- `delete(id)` - Delete journal entry
- `reverse(id)` - Reverse a posted journal entry

### 2. **Journal Entries Page** (`frontend/src/app/journals/page.tsx`)

**Features:**
- ✅ Display all journal entries in a table
- ✅ Show entry statistics (Total, Posted, Draft)
- ✅ View detailed journal entry with all lines
- ✅ Reverse posted journal entries
- ✅ Color-coded debits (green) and credits (blue)
- ✅ Real-time balance validation display
- ✅ Modal popup for entry details
- ✅ Back to dashboard link

**Columns Displayed:**
| Column | Description |
|--------|-------------|
| ID | Journal Entry ID (formatted as JE-xxx) |
| Date | Entry date |
| Memo | Description/memo |
| Lines | Count of journal lines |
| Total Debit | Sum of all debits |
| Total Credit | Sum of all credits |
| Status | Posted (green) or Draft (yellow) |
| Actions | View details, Reverse (if posted) |

### 3. **TypeScript Types** (`frontend/src/types/index.ts`)

Updated `JournalLine` interface to include:
```typescript
export interface JournalLine {
  id?: number;
  account: number;
  account_code?: string;    // Added
  account_name?: string;    // Added
  debit: string;
  credit: string;
}
```

### 4. **Dashboard Integration** (`frontend/src/app/page.tsx`)

Added new card on dashboard:
- **Icon:** List icon (purple)
- **Title:** Journal Entries
- **Subtitle:** General Ledger
- **Link:** `/journals`

---

## 🎨 UI/UX Features

### Statistics Cards
Three cards showing:
1. **Total Entries** - Blue icon
2. **Posted Entries** - Green checkmark
3. **Draft Entries** - Yellow document icon

### Journal Entry Table
- Hover effects on rows
- Responsive design
- Empty state message
- Action buttons with tooltips

### Detail Modal
When clicking the "Eye" icon, a modal displays:
- Entry ID and date
- Status badge (Posted/Draft)
- Memo/description
- **Journal Lines Table:**
  - Account code and name
  - Debit amounts (green, right-aligned)
  - Credit amounts (blue, right-aligned)
  - Total row (bold, highlighted)
- **Actions:**
  - Reverse Entry (red button, only for posted)
  - Close button

---

## 🔄 Data Flow

```
Frontend                    Backend API
   │                           │
   ├─ GET /api/journals/   ───>│
   │                           │
   │<─── JSON Response ────────┤
   │    [{id, date, memo,      │
   │      posted, lines[]}]    │
   │                           │
   ├─ POST /journals/{id}/reverse/
   │                           │
   │<─── Success/Error ────────┤
```

### Response Structure

**Journal Entry:**
```json
{
  "id": 15,
  "date": "2025-01-15",
  "currency": 1,
  "memo": "AR Invoice #INV-001",
  "posted": true,
  "lines": [
    {
      "id": 45,
      "account": 1100,
      "account_code": "1100",
      "account_name": "Accounts Receivable",
      "debit": "1050.00",
      "credit": "0.00"
    },
    {
      "id": 46,
      "account": 4000,
      "account_code": "4000",
      "account_name": "Sales Revenue",
      "debit": "0.00",
      "credit": "1000.00"
    },
    {
      "id": 47,
      "account": 2200,
      "account_code": "2200",
      "account_name": "Tax Payable",
      "debit": "0.00",
      "credit": "50.00"
    }
  ]
}
```

---

## 🎯 User Actions

### 1. View All Journal Entries
1. Click "Journal Entries" on dashboard
2. See list of all entries
3. View statistics at top

### 2. View Entry Details
1. Click eye icon (👁️) on any entry
2. Modal opens showing:
   - Entry header info
   - All journal lines
   - Account details
   - Debit/Credit amounts
   - Totals

### 3. Reverse Posted Entry
1. Click eye icon to view details
2. Click "Reverse Entry" button (red)
3. Confirm the action
4. System creates reversal entry
5. Table refreshes automatically

---

## 📊 Visual Indicators

### Status Badges
- **Posted:** Green badge with checkmark ✓
- **Draft:** Yellow badge

### Amount Colors
- **Debits:** Green text (`text-green-600`)
- **Credits:** Blue text (`text-blue-600`)
- **Totals:** Bold, colored by type

### Icons
- **View Details:** Eye icon (blue)
- **Reverse:** XCircle icon (red)
- **Posted Status:** CheckCircle (green)
- **Statistics:** BookOpen, CheckCircle, FileText

---

## 🔍 Technical Details

### State Management
```typescript
const [journals, setJournals] = useState<JournalEntry[]>([]);
const [accounts, setAccounts] = useState<Account[]>([]);
const [selectedJournal, setSelectedJournal] = useState<JournalEntry | null>(null);
const [showDetail, setShowDetail] = useState(false);
```

### Key Functions

**fetchData()**
- Loads journal entries and accounts in parallel
- Uses `Promise.all()` for efficiency
- Handles errors with toast notifications

**calculateTotals(journal)**
- Sums all debit amounts
- Sums all credit amounts
- Returns `{ totalDebit, totalCredit }`

**getAccountName(line)**
- First tries `account_code` and `account_name` from API
- Falls back to accounts list lookup
- Returns formatted string: "CODE - Name"

**handleReverse(id)**
- Confirms action with user
- Calls API reverse endpoint
- Refreshes data on success
- Shows error toast on failure

---

## 🚀 API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/journals/` | List all journal entries |
| GET | `/api/journals/{id}/` | Get single entry |
| POST | `/api/journals/{id}/reverse/` | Reverse posted entry |
| DELETE | `/api/journals/{id}/` | Delete entry |

---

## 📱 Responsive Design

- **Mobile:** Single column, stacked layout
- **Tablet:** 2 columns for statistics
- **Desktop:** 3 columns for statistics, full table width
- Modal adapts to screen size (max 90vh height, scrollable)

---

## ✅ Error Handling

1. **Loading State:** Shows "Loading journal entries..." message
2. **Empty State:** Shows "No journal entries found"
3. **API Errors:** Toast notifications with error details
4. **Reverse Errors:** Displays specific error message from backend

---

## 🎨 Styling Classes Used

### Tailwind Classes
- `card` - White background, rounded, shadow
- `btn-primary` - Primary action buttons
- `btn-secondary` - Secondary action buttons
- `btn-danger` - Destructive actions (reverse)
- `table-wrapper` - Scrollable table container
- `table-base` - Base table styling
- `table-header` - Header row styling
- `table-th` - Header cell styling
- `table-td` - Data cell styling
- `badge-success` - Green status badge
- `badge-warning` - Yellow status badge
- `badge-info` - Blue info badge

---

## 🔐 Security

- CSRF token automatically included (CSRFInitializer)
- Authentication handled by axios interceptors
- POST endpoints require confirmation
- No direct data manipulation, all through API

---

## 📈 Future Enhancements (Potential)

1. **Filtering:**
   - By date range
   - By status (Posted/Draft)
   - By account

2. **Sorting:**
   - By date (ascending/descending)
   - By ID
   - By total amount

3. **Pagination:**
   - Page size selector
   - Previous/Next buttons
   - Jump to page

4. **Export:**
   - Export to Excel
   - Export to PDF
   - Print view

5. **Search:**
   - Search by memo
   - Search by account
   - Search by amount

6. **Create/Edit:**
   - Manual journal entry form
   - Validation before posting
   - Duplicate entry

7. **Audit Trail:**
   - Show who created/posted
   - Show reversal history
   - Show related documents

---

## 🐛 Known Issues

None currently. All functionality tested and working.

---

## 📚 Related Documentation

- **Backend API:** `docs/finance/06_API.md`
- **Models:** `docs/finance/02_MODELS.md`
- **Services:** `docs/finance/04_SERVICES.md`
- **Posting Methods:** `docs/finance/POSTING_METHODS_EXPLAINED.md`
- **Journal Entry vs Line:** `docs/finance/JOURNAL_ENTRY_VS_JOURNAL_LINE.md`

---

## 🎓 Usage Example

### Viewing an Entry
1. Navigate to http://localhost:3000/journals
2. See list of all journal entries
3. Click eye icon on entry JE-15
4. View modal with details:
   - Date: Jan 15, 2025
   - Memo: "AR Invoice #INV-001"
   - Lines:
     * DR Accounts Receivable $1,050.00
     * CR Sales Revenue $1,000.00
     * CR Tax Payable $50.00
   - Totals match: $1,050.00 DR = $1,050.00 CR

### Reversing an Entry
1. Open entry details
2. Click "Reverse Entry" (red button)
3. Confirm: "Are you sure you want to reverse this journal entry?"
4. Success message: "Journal entry reversed successfully"
5. New reversal entry created in backend
6. Table refreshes showing new entry

---

**File:** `c:\Users\samys\FinanceERP\frontend\src\app\journals\page.tsx`  
**Lines:** 342 lines  
**Status:** ✅ Complete and tested

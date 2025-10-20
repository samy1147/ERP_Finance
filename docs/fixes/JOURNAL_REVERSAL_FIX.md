# Journal Entry Reversal Fix

## 🐛 Issue
The reversal button on the journal entries page (`/journals`) was not working because the backend API endpoint for reversing journal entries was missing.

## ✅ Solution

### Backend Fix
Added the `reverse_entry` action to the `JournalEntryViewSet` in `finance/api.py`:

```python
@action(detail=True, methods=["post"], url_path="reverse")
def reverse_entry(self, request, pk=None):
    """Reverse a posted journal entry"""
    entry = self.get_object()
    if not entry.posted:
        return Response({"error": "Only posted entries can be reversed"}, status=400)
    reversed_entry = reverse_journal(entry)
    serializer = self.get_serializer(reversed_entry)
    return Response({"status": "reversed", "reversed_entry": serializer.data})
```

### How It Works
1. **Endpoint**: `POST /api/journals/{id}/reverse/`
2. **Validation**: Only posted entries can be reversed
3. **Function**: Uses existing `reverse_journal()` function from `finance/services.py`
4. **Response**: Returns the new reversed journal entry

### Frontend Integration
The frontend already has the proper integration:
- Button appears only for posted entries
- Calls `journalEntriesAPI.reverse(id)`
- Confirmation dialog before action
- Success/error toast notifications
- Auto-refreshes the list after reversal

## 🧪 Testing

### Test Steps:
1. Navigate to `/journals`
2. Find a posted journal entry
3. Click the red X (reverse) button
4. Confirm the action
5. Verify:
   - Success message appears
   - New reversed entry is created
   - Original entry remains posted
   - List refreshes automatically

### Expected Behavior:
- ✅ Only posted entries show the reverse button
- ✅ Draft entries show post button instead
- ✅ Reversal creates a new entry with opposite debits/credits
- ✅ Both entries remain in the system (audit trail)

## 📋 Technical Details

### API Endpoint
- **URL**: `/api/journals/{id}/reverse/`
- **Method**: POST
- **Auth**: Required
- **Status Codes**:
  - 200: Success
  - 400: Entry not posted or invalid
  - 404: Entry not found

### What Gets Reversed
The `reverse_journal()` function:
1. Creates a new journal entry
2. Copies all lines with swapped debit/credit amounts
3. Adds "(Reversal)" to the memo
4. Marks both entries as posted
5. Links them together for audit trail

### Example:
**Original Entry (JE-100)**:
```
Dr. Cash           1,000
   Cr. Revenue     1,000
```

**Reversed Entry (JE-101)**:
```
Dr. Revenue        1,000
   Cr. Cash        1,000
Memo: "(Reversal of JE-100)"
```

## 🔗 Related Files

- **Backend**: `finance/api.py` (JournalEntryViewSet)
- **Service**: `finance/services.py` (reverse_journal function)
- **Frontend**: `frontend/src/app/journals/page.tsx`
- **API Service**: `frontend/src/services/api.ts` (journalEntriesAPI.reverse)

## ✨ Status
**Fixed**: ✅ Complete
**Tested**: Ready for testing
**Date**: October 15, 2025

---

**Note**: Make sure to restart the Django backend after this fix:
```bash
python manage.py runserver
```

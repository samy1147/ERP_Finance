# Report Export Fix - October 14, 2025

## Issue
When clicking "Export CSV" or "Export Excel" buttons in the Reports page, the requests failed with **404 status code**.

## Root Cause Analysis

### Problem 1: Query Parameter Conflict with DRF
The frontend was sending the query parameter `format=csv` or `format=xlsx`, but Django REST Framework (DRF) reserves the `format` query parameter for content negotiation. When DRF sees `?format=csv`, it tries to find a renderer for that format and returns a 404 if it can't find one.

The backend code was checking for both `format` and `file_type` parameters:
```python
fmt = (request.GET.get("format") or "json").lower()
file_type = request.GET.get("file_type", "").lower()

if fmt == "csv" or file_type == "csv":
    # Export CSV
```

However, due to DRF's format handling, the request never reached the view when using `?format=csv`.

### Problem 2: AP Aging Report KeyError
The AP Aging Report's Excel export had a bug where it tried to access `r["id"]` instead of `r["invoice_id"]`, causing a KeyError when generating Excel files.

## Solution

### Fix 1: Update Frontend to Use `file_type` Parameter
**File:** `frontend/src/services/api.ts`

Changed from using `format` parameter to `file_type` parameter in all report API calls:

```typescript
// Before
params: { date_from: dateFrom, date_to: dateTo, format }

// After  
params: { date_from: dateFrom, date_to: dateTo, file_type: format }
```

This change was applied to:
- `trialBalance()` - Trial Balance report
- `arAging()` - AR Aging report  
- `apAging()` - AP Aging report

### Fix 2: Fix AP Aging Report Excel Export
**File:** `finance/api.py` (line 255)

Fixed the KeyError by changing:
```python
# Before
ws.append([r["id"], r["number"], r["supplier"], ...])

# After
ws.append([r["invoice_id"], r["number"], r["supplier"], ...])
```

## Testing

All export endpoints now work correctly:

### Trial Balance
- ✅ CSV: `http://localhost:8000/api/reports/trial-balance/?file_type=csv` → 200 OK
- ✅ Excel: `http://localhost:8000/api/reports/trial-balance/?file_type=xlsx` → 200 OK

### AR Aging  
- ✅ CSV: `http://localhost:8000/api/reports/ar-aging/?file_type=csv` → 200 OK
- ✅ Excel: `http://localhost:8000/api/reports/ar-aging/?file_type=xlsx` → 200 OK

### AP Aging
- ✅ CSV: `http://localhost:8000/api/reports/ap-aging/?file_type=csv` → 200 OK
- ✅ Excel: `http://localhost:8000/api/reports/ap-aging/?file_type=xlsx` → 200 OK

## Files Modified

1. **frontend/src/services/api.ts**
   - Lines 119-133: Changed `format` parameter to `file_type` in report API calls

2. **finance/api.py**
   - Line 255: Fixed AP Aging Excel export to use `r["invoice_id"]` instead of `r["id"]`

## User Impact

Users can now successfully:
- View reports in the browser
- Export reports to CSV format
- Export reports to Excel format
- Files download with proper naming: `{report-type}-{date}.{extension}`

## Next Steps

No further action required. The frontend will need to be restarted to pick up the changes in `api.ts`.

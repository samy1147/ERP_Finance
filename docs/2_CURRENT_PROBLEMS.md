# 🔴 CURRENT PROBLEMS IN THE PROJECT

**Created:** November 15, 2025  
**Status:** Issues that MUST be fixed

---

## ⚠️ CRITICAL ISSUES

### **Problem #1: Python Dependencies Not Installed**

**Error:**
```
ModuleNotFoundError: No module named 'django'
```

**What happened:**
The Python packages are not installed on your system.

**Solution:**
```powershell
# Open PowerShell in project folder
cd C:\Users\samys\OneDrive\Documents\GitHub\ERP_Finance

# Install all required packages
pip install -r requirements.txt

# Verify Django is installed
python -c "import django; print(django.VERSION)"
```

**Expected Output:**
```
(5, 2, 7, 'final', 0)
```

---

### **Problem #2: Foreign Key Reference Errors (Migration Issues)**

**What happened:**
Some database migrations try to reference models that don't exist yet, causing circular dependency issues.

**Example:**
- `fixed_assets` module tries to link to `ap.Supplier`
- But `ap` module might not be migrated yet
- This causes migration failures

**Evidence in code:**
- File: `fixed_assets/migrations/0005_asset_ap_invoice_asset_ap_invoice_line_asset_grn_and_more.py`
- Tries to reference `ap.APInvoice` and `ap.Supplier`

**Impact:**
- Cannot run `python manage.py migrate` successfully
- Database schema doesn't match code
- New features can't be added

**Solution:**

1. **Check current migration status:**
```powershell
python manage.py showmigrations
```

2. **If migrations are broken, reset specific app:**
```powershell
# DANGER: This deletes data! Only do in development
python manage.py migrate fixed_assets zero
python manage.py migrate fixed_assets
```

3. **Better approach - Use string references in models:**

Instead of:
```python
# ❌ WRONG - Hard reference
supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
```

Use:
```python
# ✅ CORRECT - String reference
supplier = models.ForeignKey('ap.Supplier', on_delete=models.PROTECT)
```

**Files to check:**
- `fixed_assets/models.py` - Lines referencing Supplier or APInvoice
- Any model that references another app's model

---

### **Problem #3: Duplicate Invoice Models**

**What happened:**
There are TWO invoice implementations:
1. `finance.Invoice` (OLD - Legacy)
2. `ar.ARInvoice` (NEW - Current)

Both exist in the database and code, causing confusion.

**Evidence:**
```python
# In finance/models.py - OLD implementation
class Invoice(models.Model):
    # ... legacy fields
    pass

# In ar/models.py - NEW implementation
class ARInvoice(models.Model):
    # ... current fields
    pass
```

**Impact:**
- Developers don't know which one to use
- API endpoints might be inconsistent
- Database has duplicate tables
- Code duplication

**Solution:**

**Option 1: Remove Legacy (Recommended)**
```powershell
# 1. Check if finance.Invoice is used anywhere
python manage.py shell
>>> from finance.models import Invoice
>>> Invoice.objects.count()
# If 0, safe to remove

# 2. Comment out the model in finance/models.py
# 3. Create migration to drop table
python manage.py makemigrations finance
python manage.py migrate finance
```

**Option 2: Archive Legacy**
- Rename `finance.Invoice` to `finance.InvoiceLegacy`
- Add comment: "# DEPRECATED - Use ar.ARInvoice instead"
- Update all references

**Files to update:**
- `finance/models.py` (lines ~100-200)
- `finance/serializers.py`
- `finance/api.py`
- Any views/URLs using old Invoice

---

### **Problem #4: GL Posting Logic Not Complete**

**What happened:**
Not all transaction types properly create General Ledger (Journal Entry) records.

**What SHOULD happen:**
```
Every financial transaction → Creates JournalEntry → Creates JournalLines
```

**What's MISSING:**

✅ **Working:**
- AR Invoices → Creates Journal Entry (implemented)
- AP Invoices → Creates Journal Entry (implemented)

❌ **Not Working/Incomplete:**
- AR Payments → May not create GL entry
- AP Payments → May not create GL entry
- Fixed Asset Depreciation → May not post to GL automatically
- Inventory Adjustments → No GL posting

**Evidence:**
Look for `gl_journal` field usage in each model's save/post methods.

**Example - What's needed:**

```python
# In ar/models.py - ARPayment model
def post_to_gl(self):
    """Post payment to General Ledger"""
    journal = JournalEntry.objects.create(
        date=self.payment_date,
        currency=self.currency,
        memo=f"Payment {self.reference_number}"
    )
    
    # DR Bank
    JournalLine.objects.create(
        entry=journal,
        account=self.bank_account.gl_account,
        debit=self.amount,
        credit=0
    )
    
    # CR Accounts Receivable
    JournalLine.objects.create(
        entry=journal,
        account=get_ar_account(),
        debit=0,
        credit=self.amount
    )
    
    self.gl_journal = journal
    self.save()
```

**Impact:**
- General Ledger is incomplete
- Financial reports will be wrong
- Can't generate Balance Sheet or P&L accurately

**Solution:**
- Add `post_to_gl()` method to each transaction model
- Call it when transaction is approved/posted
- Test by checking `finance_journalentry` table after posting

**Files to fix:**
- `ar/models.py` - ARPayment model
- `ap/models.py` - APPayment model
- `fixed_assets/services.py` - Depreciation calculation
- `inventory/models.py` - Stock adjustments

---

### **Problem #5: Segment Assignment Complexity**

**What happened:**
Multi-dimensional accounting is powerful but VERY complex to use.

**The Challenge:**
Every journal line needs segment assignments for ALL segment types:
- Account (required)
- Department (required)
- Cost Center (optional?)
- Project (optional?)
- Product (optional?)

**Example - What user must provide:**
```json
{
  "segments": [
    {"segment_type": 1, "segment": 1110},  // Account: Cash
    {"segment_type": 2, "segment": 14},    // Department: Sales
    {"segment_type": 3, "segment": 24},    // Cost Center: HQ
    {"segment_type": 4, "segment": 101},   // Project: Proj-2025-01
    {"segment_type": 5, "segment": 55}     // Product: Product-A
  ]
}
```

**Problems:**
1. Users don't know which segment types are required
2. No clear error messages if missing
3. Rules exist (`SegmentAssignmentRule`) but not fully implemented
4. API responses don't guide users

**Impact:**
- Users can't create invoices easily
- API calls fail with cryptic errors
- High learning curve

**Solution:**

1. **Add validation with clear errors:**
```python
def validate_segments(segments, required_types):
    provided = {s['segment_type'] for s in segments}
    required = set(required_types)
    missing = required - provided
    
    if missing:
        raise ValidationError(
            f"Missing required segment types: {missing}. "
            f"Please provide segments for: {[TYPE_NAMES[t] for t in missing]}"
        )
```

2. **Auto-assign default segments:**
```python
def auto_assign_segments(invoice, gl_line):
    # Check if rules exist
    rules = SegmentAssignmentRule.objects.filter(
        customer=invoice.customer,
        account=gl_line.account
    )
    
    if rules.exists():
        # Apply rules
        for rule in rules:
            gl_line.segments.create(
                segment_type=rule.segment_type,
                segment=rule.segment
            )
```

3. **API endpoint to get required segment types:**
```python
# GET /api/segments/required-types/
{
  "required": [1, 2],  // Account, Department
  "optional": [3, 4, 5]  // Cost Center, Project, Product
}
```

**Files to update:**
- `finance/models.py` - Add validation
- `finance/services.py` - Auto-assignment logic
- `segment/api.py` - New endpoint for requirements
- All serializers that handle segments

---

### **Problem #6: Approval Workflow Not Implemented**

**What happened:**
Models have approval status fields, but NO workflow engine.

**What EXISTS:**
```python
# In ar/models.py
approval_status = models.CharField(
    choices=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED']
)
```

**What's MISSING:**
1. **Who are the approvers?** (No user/role management)
2. **Routing rules** (Who approves what amount?)
3. **Notifications** (Email/alert to approvers)
4. **Approval history** (Who approved when?)
5. **Multi-level approval** (Manager → Director → CFO)

**Impact:**
- Approval status is manually changed
- No accountability
- No automated routing
- No email notifications

**Solution:**

**Phase 1: Basic Implementation**
```python
# Create new model
class ApprovalWorkflow(models.Model):
    invoice = models.ForeignKey(ARInvoice, on_delete=models.CASCADE)
    approver = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(choices=['PENDING', 'APPROVED', 'REJECTED'])
    approved_at = models.DateTimeField(null=True)
    comments = models.TextField(blank=True)
```

**Phase 2: Rules Engine**
```python
class ApprovalRule(models.Model):
    document_type = models.CharField()  # 'AR_INVOICE', 'AP_INVOICE'
    amount_from = models.DecimalField()
    amount_to = models.DecimalField()
    approver_role = models.CharField()  # 'MANAGER', 'DIRECTOR', 'CFO'
    sequence = models.IntegerField()  # Order of approval
```

**Phase 3: Notifications**
- Integration with email system
- Real-time notifications
- Approval dashboard

**Files to create:**
- `core/approvals/` (new app)
- `core/approvals/models.py`
- `core/approvals/services.py`
- `core/approvals/notifications.py`

---

### **Problem #7: Missing Frontend Integration Status**

**What happened:**
Frontend exists in `frontend/` folder, but unclear what's implemented.

**Unknown:**
- Which screens are built?
- Which APIs are connected?
- What's working end-to-end?
- What's just placeholder?

**Impact:**
- Can't test full workflows
- Don't know what's usable
- Development priorities unclear

**Solution:**

1. **Audit frontend:**
```powershell
cd frontend
# Check what pages exist
ls src/app
ls src/components
```

2. **Test each page:**
- Start frontend: `npm run dev`
- Visit: http://localhost:3000
- Document what works vs. what's broken

3. **Create frontend status document**

**Files to check:**
- `frontend/src/app/` - Pages
- `frontend/src/components/` - Reusable components
- `frontend/src/services/` - API calls

---

### **Problem #8: Test Failures**

**What happened:**
Tests exist but some are failing.

**Evidence:**
```
test_invoice_list_quick.py - Exit code 1
```

**Impact:**
- Unknown code stability
- Can't trust changes won't break things
- Regression risk

**Solution:**

1. **Run all tests:**
```powershell
# Run Django tests
python manage.py test

# Or using pytest
pytest
```

2. **Check test output:**
```powershell
# Run specific test
pytest ar/tests.py -v
```

3. **Fix failing tests one by one**

4. **Add more tests for critical flows**

**Files to check:**
- `*/tests.py` in each module
- `pytest.ini` (test configuration)

---

### **Problem #9: Security Issues**

**What happened:**
Many API endpoints have security disabled for development.

**Evidence:**
```python
# In procurement/rfx/api.py (line 35)
permission_classes = [AllowAny]  # TODO: Change to IsAuthenticated
```

**Found in 30+ files!**

**Impact:**
- Anyone can access APIs without authentication
- No user tracking
- Not production-ready

**Solution:**

1. **Enable authentication:**
```python
# Change from:
permission_classes = [AllowAny]

# To:
permission_classes = [IsAuthenticated]
```

2. **Add user management:**
- Django's built-in User model
- Token authentication (JWT)
- Role-based permissions

3. **Update frontend to handle login**

**Files to update:**
- All `**/api.py` files
- `erp/settings.py` (REST_FRAMEWORK settings)
- Frontend: Add login page

---

### **Problem #10: No Notification System**

**What happened:**
No email or notification system implemented.

**What's MISSING:**
- Approval request emails
- Payment reminders
- Due date alerts
- System notifications

**Impact:**
- Manual follow-up required
- Users miss important events
- Poor user experience

**Solution:**

1. **Email backend setup:**
```python
# In settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

2. **Create notification service:**
```python
# core/notifications/service.py
def send_approval_notification(invoice, approver):
    send_mail(
        subject=f'Invoice {invoice.number} Needs Approval',
        message=f'Please review invoice {invoice.number} for {invoice.customer.name}',
        from_email='noreply@erp.com',
        recipient_list=[approver.email],
    )
```

3. **Trigger notifications on events**

**Files to create:**
- `core/notifications/` (new app)
- `core/notifications/services.py`
- `core/notifications/templates/` (email templates)

---

## 📋 PRIORITY ORDER FOR FIXES

**High Priority (Fix First):**
1. ✅ Install Python dependencies
2. ✅ Fix migration issues
3. ✅ Remove duplicate Invoice models
4. ✅ Complete GL posting logic

**Medium Priority:**
5. ✅ Simplify segment assignment
6. ✅ Implement basic approval workflow
7. ✅ Fix test failures

**Low Priority (Can wait):**
8. ✅ Audit frontend status
9. ✅ Add authentication
10. ✅ Build notification system

---

## 🆘 HOW TO REPORT/TRACK ISSUES

**Use this format when discussing problems:**

```
Issue: [Short title]
Module: [Which app/module]
Severity: [Critical/High/Medium/Low]
Impact: [What breaks?]
Files: [Which files are affected]
Solution: [Proposed fix]
Status: [Not Started/In Progress/Done]
```

**Example:**
```
Issue: Foreign Key Migration Error in Fixed Assets
Module: fixed_assets
Severity: Critical
Impact: Cannot run migrations, database is out of sync
Files: fixed_assets/models.py, fixed_assets/migrations/0005_*.py
Solution: Use string references 'ap.Supplier' instead of hard import
Status: Not Started
```

---

## 📝 SUMMARY

**Critical Issues Count:** 10

**Blockers (Can't proceed without fixing):**
- Python dependencies not installed
- Migration errors
- Duplicate models

**Important (Affects functionality):**
- Incomplete GL posting
- No approval workflow
- Missing tests

**Nice to Have (Can work without):**
- Notifications
- Authentication
- Frontend completion

**Next Step:** Start with fixing Python dependencies, then tackle migration issues!

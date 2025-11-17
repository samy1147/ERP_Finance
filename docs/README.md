# 📚 DEVELOPER QUICK START GUIDE

**Created:** November 15, 2025  
**Purpose:** Everything you need to get started FAST!

---

## 🚀 GETTING STARTED IN 5 MINUTES

### Step 1: Install Dependencies (1 minute)
```powershell
# Open PowerShell in project folder
cd C:\Users\samys\OneDrive\Documents\GitHub\ERP_Finance

# Install Python packages
pip install -r requirements.txt
```

### Step 2: Setup Database (1 minute)
```powershell
# Run migrations (create database tables)
python manage.py migrate

# Create admin user
python manage.py createsuperuser
# Enter username, email, password when prompted
```

### Step 3: Start Backend (30 seconds)
```powershell
# Start Django server
python manage.py runserver 8007
```

**Backend is now running at:** http://localhost:8007

### Step 4: Start Frontend (1 minute)
```powershell
# Open NEW PowerShell window
cd C:\Users\samys\OneDrive\Documents\GitHub\ERP_Finance\frontend

# Install Node packages (first time only)
npm install

# Start Next.js
npm run dev
```

**Frontend is now running at:** http://localhost:3000

### Step 5: Test It! (1 minute)
1. Visit http://localhost:8007/admin/
2. Login with your superuser credentials
3. Visit http://localhost:8007/api/schema/swagger-ui/
4. See all available APIs!

---

## 📖 DOCUMENTATION STRUCTURE

We've created **4 documentation files** for you:

### 1. **1_SIMPLE_PROJECT_EXPLANATION.md**
   - 🎯 **Read This First!**
   - What is this project?
   - Simple explanation of each module
   - Basic workflows
   - Technology stack

### 2. **2_CURRENT_PROBLEMS.md**
   - 🔴 **Critical Issues**
   - 10 problems that need fixing
   - Priority order
   - Step-by-step solutions

### 3. **3_MISSING_FEATURES.md**
   - 🚧 **What's Not Built Yet**
   - 12 missing feature areas
   - Completion status per module
   - Estimated development time

### 4. **4_DETAILED_WORKFLOWS.md**
   - 🔄 **How Things Work**
   - Detailed process flows
   - AR/AP/Fixed Assets workflows
   - Module relationships
   - Data flow diagrams

---

## 🎯 YOUR FIRST TASKS

### For New Developers:

**Day 1-2: Understanding**
1. ✅ Read `1_SIMPLE_PROJECT_EXPLANATION.md`
2. ✅ Start the system (follow steps above)
3. ✅ Explore Django Admin: http://localhost:8007/admin/
4. ✅ Test some APIs using Swagger
5. ✅ Read `4_DETAILED_WORKFLOWS.md` (AR workflow section)

**Day 3-5: Fix Critical Issues**
1. ✅ Read `2_CURRENT_PROBLEMS.md`
2. ✅ Fix Problem #1: Install dependencies
3. ✅ Fix Problem #2: Migration issues
4. ✅ Fix Problem #3: Remove duplicate Invoice models
5. ✅ Run tests: `python manage.py test`

**Week 2: Complete a Feature**
1. ✅ Read `3_MISSING_FEATURES.md`
2. ✅ Pick one missing feature (start small)
3. ✅ Implement it
4. ✅ Write tests
5. ✅ Document your changes

---

## 📂 PROJECT STRUCTURE QUICK REFERENCE

```
ERP_Finance/
│
├── docs/                          ← YOU ARE HERE! Read these first!
│   ├── 1_SIMPLE_PROJECT_EXPLANATION.md
│   ├── 2_CURRENT_PROBLEMS.md
│   ├── 3_MISSING_FEATURES.md
│   └── 4_DETAILED_WORKFLOWS.md
│
├── core/                          ← Currency, Tax Rates (Foundation)
├── segment/                       ← Chart of Accounts
├── periods/                       ← Fiscal Periods
├── finance/                       ← General Ledger (GL)
├── ar/                           ← Customer Invoices & Payments
├── ap/                           ← Vendor Bills & Payments
├── fixed_assets/                 ← Asset Management
├── procurement/                  ← Purchase Process (PR, PO, GRN)
│   ├── requisitions/
│   ├── rfx/
│   ├── purchase_orders/
│   ├── receiving/
│   └── vendor_bills/
├── inventory/                    ← Stock Management (Under Development)
├── crm/                         ← Customer Management (Minimal)
│
├── frontend/                     ← Next.js UI
│   ├── src/
│   │   ├── app/                 ← Pages
│   │   ├── components/          ← Reusable components
│   │   └── services/            ← API calls
│   └── package.json
│
├── postman_collections/          ← API test collections
├── requirements.txt              ← Python dependencies
├── manage.py                     ← Django management
├── db.sqlite3                    ← Database file
└── erp/                         ← Django settings
    └── settings.py
```

---

## 🔧 COMMON COMMANDS

### Django Backend:

```powershell
# Run server
python manage.py runserver 8007

# Create migrations (after model changes)
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Open Django shell (Python REPL with models loaded)
python manage.py shell

# Run tests
python manage.py test

# Check for issues
python manage.py check
```

### Frontend:

```powershell
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

---

## 🔍 HOW TO FIND THINGS

### "Where is the Customer model?"
```powershell
# Search for class definition
grep -r "class Customer" --include="*.py"
# Result: ar/models.py
```

### "Where are the AR APIs?"
```
ar/
  ├── models.py       ← Customer, ARInvoice, ARPayment
  ├── serializers.py  ← JSON conversion
  ├── api.py          ← API endpoints (ViewSets)
  └── urls.py         ← URL routing
```

### "How do I test the AR Invoice API?"
1. Start backend
2. Go to: http://localhost:8007/api/schema/swagger-ui/
3. Find: `/api/ar/invoices/`
4. Click "Try it out"
5. See example JSON
6. Click "Execute"

Or use Postman:
1. Import `postman_collections/2_AR_Invoices_and_Payments.json`
2. Run requests

---

## 📊 MODULE QUICK REFERENCE

| Module | Purpose | Key Models | API Endpoint |
|--------|---------|------------|--------------|
| core | Foundation | Currency, TaxRate | `/api/core/` |
| segment | Chart of Accounts | XX_Segment | `/api/segments/` |
| periods | Fiscal Periods | FiscalPeriod | `/api/periods/` |
| finance | General Ledger | JournalEntry | `/api/finance/` |
| ar | Customer Invoices | ARInvoice, ARPayment | `/api/ar/` |
| ap | Vendor Bills | APInvoice, APPayment | `/api/ap/` |
| fixed_assets | Asset Management | Asset | `/api/fixed-assets/` |
| procurement | Purchasing | PR, PO, GRN | `/api/procurement/` |

---

## 🆘 TROUBLESHOOTING

### Problem: "ModuleNotFoundError: No module named 'django'"
**Solution:**
```powershell
pip install -r requirements.txt
```

### Problem: "Database is locked"
**Solution:**
```powershell
# Close all terminals running Django
# Delete db.sqlite3 (WARNING: Deletes all data!)
# Run migrations again
python manage.py migrate
```

### Problem: "Migration conflicts"
**Solution:**
```powershell
# See migration status
python manage.py showmigrations

# If broken, reset specific app (DANGER: Deletes data!)
python manage.py migrate app_name zero
python manage.py migrate app_name
```

### Problem: "Port 8007 already in use"
**Solution:**
```powershell
# Find and kill process
Get-Process -Name python | Stop-Process -Force

# Or use different port
python manage.py runserver 8008
```

### Problem: "Frontend can't connect to backend"
**Solution:**
1. Check backend is running: http://localhost:8007/api/
2. Check CORS settings in `erp/settings.py`
3. Check frontend API URL in `frontend/.env` or config

---

## 🎓 LEARNING PATH

### Week 1: Basics
- [ ] Read all 4 documentation files
- [ ] Understand AR workflow (customer invoices)
- [ ] Understand AP workflow (vendor bills)
- [ ] Test APIs using Swagger or Postman

### Week 2: Database
- [ ] Understand Django ORM
- [ ] Learn model relationships
- [ ] Study segment (Chart of Accounts) structure
- [ ] Understand Journal Entry structure

### Week 3: Business Logic
- [ ] Study `services.py` files
- [ ] Understand GL posting logic
- [ ] Learn approval workflows
- [ ] Study 3-way matching

### Week 4: Frontend
- [ ] Explore Next.js pages
- [ ] Understand component structure
- [ ] Learn API integration
- [ ] Test end-to-end workflows

### Month 2+: Advanced
- [ ] Build new features
- [ ] Fix complex bugs
- [ ] Optimize performance
- [ ] Add comprehensive tests

---

## 📝 CODING CONVENTIONS

### Models (models.py):
```python
class ARInvoice(models.Model):
    """Accounts Receivable Invoice"""
    
    # Foreign keys use related_name
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.PROTECT,
        related_name='ar_invoices'  # customer.ar_invoices.all()
    )
    
    # Use choices for status fields
    STATUSES = [('DRAFT', 'Draft'), ('POSTED', 'Posted')]
    status = models.CharField(max_length=20, choices=STATUSES)
    
    # Use descriptive help_text
    amount = models.DecimalField(
        max_digits=14, 
        decimal_places=2,
        help_text="Invoice total amount"
    )
    
    def __str__(self):
        return f"{self.number} - {self.customer.name}"
```

### Serializers (serializers.py):
```python
class ARInvoiceSerializer(serializers.ModelSerializer):
    # Nested serializers for related objects
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    items = ARItemSerializer(many=True)
    
    class Meta:
        model = ARInvoice
        fields = '__all__'  # Or list specific fields
```

### Views/APIs (api.py):
```python
class ARInvoiceViewSet(viewsets.ModelViewSet):
    queryset = ARInvoice.objects.all()
    serializer_class = ARInvoiceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['customer', 'status', 'date']
    ordering_fields = ['date', 'number']
    
    @action(detail=True, methods=['post'])
    def post_to_gl(self, request, pk=None):
        """Post invoice to General Ledger"""
        invoice = self.get_object()
        # ... business logic
        return Response({'status': 'posted'})
```

---

## 🔐 SECURITY NOTES

**Current Status: DEVELOPMENT MODE**

⚠️ **Security is DISABLED for development!**

These need fixing before production:
```python
# In many api.py files:
permission_classes = [AllowAny]  # ❌ CHANGE TO IsAuthenticated
```

**Before going to production:**
1. Enable authentication on all APIs
2. Add user management
3. Implement role-based access control
4. Enable HTTPS
5. Secure secret keys
6. Enable database encryption

---

## 📞 GETTING HELP

### Documentation:
1. **This folder** (`docs/`) - Start here!
2. **PROJECT_OVERVIEW.md** - Detailed technical overview
3. **POSTMAN_COLLECTION_UPDATES.md** - API usage examples

### Code Comments:
- Most models have docstrings
- Check `models.py` for field descriptions
- Check `services.py` for business logic

### External Resources:
- Django Docs: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Next.js: https://nextjs.org/docs

### Testing:
- Swagger UI: http://localhost:8007/api/schema/swagger-ui/
- Admin Panel: http://localhost:8007/admin/
- Postman Collections: `postman_collections/` folder

---

## ✅ CHECKLIST FOR NEW DEVELOPERS

**Setup:**
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Git installed
- [ ] VS Code or PyCharm installed
- [ ] Postman installed (optional)

**First Day:**
- [ ] Clone repository
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Run migrations (`python manage.py migrate`)
- [ ] Create superuser
- [ ] Start backend successfully
- [ ] Access admin panel
- [ ] View Swagger API docs

**First Week:**
- [ ] Read all documentation files in `docs/`
- [ ] Understand module structure
- [ ] Test 5+ APIs using Swagger
- [ ] Create a customer via API
- [ ] Create an invoice via API
- [ ] Post invoice to GL
- [ ] View journal entry in admin

**First Month:**
- [ ] Fix one bug from `2_CURRENT_PROBLEMS.md`
- [ ] Add one missing feature from `3_MISSING_FEATURES.md`
- [ ] Write tests for your changes
- [ ] Contribute to documentation
- [ ] Review code with team

---

## 🎯 SUCCESS METRICS

**You're doing well when:**
- ✅ You can explain the AR workflow to someone
- ✅ You can create an invoice via API
- ✅ You understand how GL posting works
- ✅ You can add a new field to a model
- ✅ You can fix a bug independently
- ✅ You can explain module relationships

**You're an expert when:**
- ✅ You can design new features
- ✅ You understand all modules deeply
- ✅ You can optimize performance
- ✅ You can mentor new developers
- ✅ You can architect system improvements

---

## 📌 IMPORTANT REMINDERS

1. **Always test after changes:**
   ```powershell
   python manage.py test
   ```

2. **Create migrations after model changes:**
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Use Git properly:**
   ```powershell
   git checkout -b feature/your-feature-name
   git add .
   git commit -m "Clear description of changes"
   git push origin feature/your-feature-name
   ```

4. **Document your changes:**
   - Add comments to complex code
   - Update documentation if you change workflows
   - Add docstrings to new functions

5. **Ask questions:**
   - No question is stupid
   - Better to ask than to break things
   - Document answers for next person

---

## 🚀 READY TO START?

**Recommended Order:**
1. ✅ Complete the 5-minute setup (top of this document)
2. ✅ Read `1_SIMPLE_PROJECT_EXPLANATION.md`
3. ✅ Explore the system using Swagger UI
4. ✅ Read `4_DETAILED_WORKFLOWS.md` (AR section)
5. ✅ Create a test invoice using API
6. ✅ Read `2_CURRENT_PROBLEMS.md`
7. ✅ Pick one problem and fix it!

**You've got this! Welcome to the team! 🎉**

---

**Questions? Check the other documentation files or ask your team lead!**

# 🚀 HOW TO START YOUR FINANCE ERP

## ⚠️ PROBLEM: Servers Keep Stopping

The servers stop when run from VS Code terminal because they need to stay in the foreground.

## ✅ SOLUTION: Use Separate Terminal Windows

### Method 1: Using Batch Files (EASIEST)

I've created two batch files for you:

#### **Step 1: Start Backend**
1. Open File Explorer
2. Navigate to: `C:\Users\samys\FinanceERP\`
3. Double-click: **`start_django.bat`**
4. A terminal window opens → Django starts on port 8000
5. **Keep this window open!**

#### **Step 2: Start Frontend** 
1. In File Explorer (same folder)
2. Double-click: **`start_nextjs.bat`**
3. A terminal window opens → Next.js starts on port 3001
4. **Keep this window open!**

#### **Step 3: Open Browser**
- Go to: **http://localhost:3001**
- Your Finance ERP will be running with all the data!

---

### Method 2: Using PowerShell Manually

#### **Terminal 1 - Backend:**
```powershell
cd C:\Users\samys\FinanceERP
venv\Scripts\python.exe manage.py runserver
```
**Keep this terminal open!**

#### **Terminal 2 - Frontend:**
```powershell
cd C:\Users\samys\FinanceERP\frontend
npm run dev
```
**Keep this terminal open!**

#### **Browser:**
```
http://localhost:3001
```

---

### Method 3: From VS Code (Alternative)

#### **Terminal 1:**
```powershell
C:\Users\samys\FinanceERP\venv\Scripts\python.exe C:\Users\samys\FinanceERP\manage.py runserver
```

#### **Terminal 2:** (Create new terminal: Ctrl + Shift + `)
```powershell
cd C:\Users\samys\FinanceERP\frontend
npm run dev
```

---

## 📊 What You'll See:

### Backend Terminal:
```
Django version 5.2.7, using settings 'erp.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Frontend Terminal:
```
▲ Next.js 14.2.33
- Local:        http://localhost:3001
✓ Ready in 3s
```

---

## 🎯 Your Data Is Ready!

Once both servers are running, you'll see:

- **25 Accounts** in Chart of Accounts
- **13 Customers** ready for invoicing
- **13 Suppliers** for AP invoices
- **6 Currencies** (USD, EUR, AED, etc.)
- **24 Tax Rates** (VAT 5%, VAT 15%, etc.)

---

## 🛑 To Stop the Servers:

- In each terminal window: Press **`Ctrl + C`**
- Or close the terminal windows

---

## ⚙️ CSS Warnings (The 20 "Problems"):

Those are **harmless VS Code warnings** about Tailwind CSS syntax. They don't affect your app at all!

To hide them:
1. Close the "Problems" panel in VS Code
2. Or completely restart VS Code (File → Exit, then reopen)

---

## 🆘 Troubleshooting:

### "Port already in use"
- Another process is using port 8000 or 3001
- Close other Django/Next.js instances
- Or restart your computer

### "Cannot connect to backend"
- Make sure Django terminal is still running
- Check: http://127.0.0.1:8000/admin/
- Should show Django admin login page

### "No data showing"
- Backend must be running
- Data was already created (25 accounts, 13 customers, etc.)
- Refresh the browser page

---

## 📝 Quick Reference:

| What | URL |
|------|-----|
| Frontend | http://localhost:3001 |
| Backend API | http://127.0.0.1:8000/api/ |
| Django Admin | http://127.0.0.1:8000/admin/ |

---

## 🎉 Next Steps:

1. **Double-click `start_django.bat`**
2. **Double-click `start_nextjs.bat`** 
3. **Open browser to http://localhost:3001**
4. **Enjoy your Finance ERP!**

All your data is there and ready to use! 🚀

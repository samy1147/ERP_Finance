# Testing FX Functionality - Step-by-Step Guide

**Now that you've created FX accounts, here's how to see FX gains/losses in action**

---

## 🎯 Current Status
✅ FX GL Accounts created (7150, 8150, 7210, 8210)  
✅ Ready to configure and test!

---

## 📋 Complete Workflow to See FX Results

### Step 1: Configure FX Accounts (5 minutes)
**Location:** `/fx/config`

#### 1.1 Set Base Currency
1. Navigate to **FX Configuration** page
2. If no base currency set, click **AED** (or your preferred currency)
3. Confirm the change
4. ✅ Verify: Blue box shows "Your company's base currency is: AED"

#### 1.2 Configure All 4 FX Account Types
**For each type below, repeat:**

| Order | Type | GL Account | Description |
|-------|------|------------|-------------|
| 1 | Realized FX Gain | 7150 - Foreign Exchange Gains | Gains on settled payments |
| 2 | Realized FX Loss | 8150 - Foreign Exchange Losses | Losses on settled payments |
| 3 | Unrealized FX Gain | 7210 - Unrealized FX Gains | Month-end revaluation gains |
| 4 | Unrealized FX Loss | 8210 - Unrealized FX Losses | Month-end revaluation losses |

**Steps for each:**
1. Click **"+ Configure Account"**
2. Select Type from dropdown
3. Select GL Account (7150, 8150, 7210, or 8210)
4. Add optional description
5. Click **"Create"**
6. ✅ Verify: Card turns green with checkmark

**Expected Result:**
```
✅ All 4 cards are GREEN
✅ Yellow warning disappeared
✅ Ready for multi-currency transactions!
```

---

### Step 2: Load Exchange Rates (3 minutes)
**Location:** `/finance/exchange-rates`

You need exchange rates for the system to convert currencies.

#### Option A: Auto-Fetch Rates (Recommended)
1. Go to **Exchange Rates** page
2. Click **"Fetch Latest Rates"** button
3. System fetches current rates from API
4. ✅ Verify: Rates appear in table (EUR→AED, USD→AED, etc.)

#### Option B: Manual Entry
1. Go to **Exchange Rates** page
2. Click **"+ New Rate"**
3. Fill form:
   - **From Currency:** EUR
   - **To Currency:** AED
   - **Rate:** 4.00
   - **Date:** Today's date
   - **Type:** SPOT
4. Click **"Create"**
5. Repeat for other currencies (USD, GBP, etc.)

**Minimum Required Rates:**
```
EUR → AED = 4.00
USD → AED = 3.67
GBP → AED = 4.68
```

✅ **Checkpoint:** You should see at least 3-5 exchange rates in the table

---

### Step 3: Create Multi-Currency Invoice (5 minutes)
**Location:** `/ar/invoices/new`

Now create an invoice in a foreign currency to lock in an exchange rate.

#### 3.1 Create EUR Invoice
1. Go to **AR Invoices** → **New Invoice**
2. Fill form:
   ```
   Customer: Select any customer (or create one)
   Number: INV-FX-001
   Date: Today's date
   Currency: EUR ← Important!
   
   Line Items:
   - Description: Test Product
   - Quantity: 10
   - Unit Price: 100 EUR
   - Total: 1,000 EUR
   ```
3. Click **"Create Invoice"** (saves as DRAFT)

#### 3.2 Post Invoice to GL
1. Find your invoice in the list
2. Click **"Post to GL"** button
3. Confirm the action
4. ✅ Verify: Status changes to "POSTED"

**What Happened Behind the Scenes:**
```
Invoice Amount: EUR 1,000
Exchange Rate: 4.00 (captured at posting)
Base Amount: AED 4,000 (EUR 1,000 × 4.00)

Journal Entry Created:
DR  Accounts Receivable (1200)    4,000 AED
    CR  Sales Revenue (4000)          4,000 AED
```

✅ **Checkpoint:** Invoice shows "POSTED" status with exchange rate 4.00

---

### Step 4: Change Exchange Rate (Simulate Rate Movement)
**Location:** `/finance/exchange-rates`

To see FX gain/loss, we need the rate to be different at payment time.

1. Go to **Exchange Rates** page
2. Create NEW rate for tomorrow:
   - **From Currency:** EUR
   - **To Currency:** AED
   - **Rate:** 4.20 ← Higher rate (you'll gain!)
   - **Date:** Tomorrow's date (or later today)
   - **Type:** SPOT
3. Click **"Create"**

**Scenario Setup:**
```
Invoice posted:  EUR 1,000 @ 4.00 = AED 4,000
Payment will use: EUR 1,000 @ 4.20 = AED 4,200
Expected FX Gain: AED 200 🎉
```

---

### Step 5: Create Payment with FX Impact (5 minutes)
**Location:** `/ar/payments/new`

Now receive payment and watch the magic happen!

#### 5.1 Create Payment
1. Go to **AR Payments** → **New Payment**
2. Fill form:
   ```
   Customer: Same as invoice
   Date: Tomorrow (or use date with new rate)
   Payment Currency: EUR ← Same as invoice
   Amount: 1,000 EUR
   Reference: PAY-FX-001
   Bank Account: Select any
   ```
3. **Select Invoice:**
   - Check the box next to INV-FX-001
   - Outstanding shows: EUR 1,000.00
   - **Converted column shows:** AED 4,200.00 @ 4.20 ← New rate!
4. **Allocation Amount:** Enter 1,000 EUR

**FX Preview Should Show:**
```
┌─────────────────────────────────────────────────┐
│ 💰 FX Impact Preview                            │
├─────────────────────────────────────────────────┤
│ Invoice Amount: EUR 1,000 @ 4.00 = AED 4,000   │
│ Payment Amount: EUR 1,000 @ 4.20 = AED 4,200   │
│ Current Rate:   4.20 (+5.0% ⬆️)                 │
│                                                 │
│ 🎯 Expected FX GAIN: AED 200.00                 │
│                                                 │
│ Journal Entry Preview:                          │
│ DR  Bank Account            4,200.00            │
│     CR  Accounts Receivable         4,000.00   │
│     CR  FX Gain Income (7150)         200.00   │
└─────────────────────────────────────────────────┘
```

5. Click **"Create Payment"**

✅ **Checkpoint:** Payment created successfully

#### 5.2 Post Payment to GL
1. Go back to **AR Payments** list
2. Find PAY-FX-001
3. Click **"Post to GL"** button
4. Confirm the action

**🎊 MAGIC HAPPENS HERE!**

System automatically:
1. Calculates FX difference (4,200 - 4,000 = 200)
2. Determines it's a GAIN (positive)
3. Gets FX account from configuration (7150)
4. Creates journal entry with 3 lines:

```
Journal Entry #JE-XXX
Date: [Payment Date]
Reference: Payment PAY-FX-001

DR  Bank Account (1000)           4,200.00 AED
    CR  Accounts Receivable (1200)        4,000.00 AED
    CR  FX Gain Income (7150)               200.00 AED ← AUTO!
```

✅ **Checkpoint:** Payment shows "POSTED" status

---

### Step 6: View Results! 🎉
**Where to see the FX impact:**

#### 6.1 Check Journal Entry
1. Go to **Finance** → **Journal Entries**
2. Find the payment entry (JE-XXX)
3. Click to view details
4. **You should see 3 lines:**
   ```
   DR  Bank Account              4,200.00
   CR  Accounts Receivable       4,000.00
   CR  FX Gain Income (7150)       200.00 ← HERE!
   ```

#### 6.2 Check Trial Balance
1. Go to **Reports** → **Trial Balance**
2. Find account **7150 - Foreign Exchange Gains**
3. **You should see:** Credit balance of 200.00 AED

```
Account                          Debit      Credit
─────────────────────────────────────────────────
7150 - Foreign Exchange Gains    0.00      200.00 ← FX PROFIT!
```

#### 6.3 Check Profit & Loss Report
1. Go to **Reports** → **Profit & Loss**
2. **Income section shows:**
   ```
   INCOME:
     Sales Revenue               4,000.00
     Foreign Exchange Gains        200.00 ← FX PROFIT!
     ─────────────────────────────────────
     Total Income                4,200.00
   ```

#### 6.4 Check Payment Detail
1. Go to **AR Payments** → Click PAY-FX-001
2. **FX Breakdown shows:**
   ```
   Invoice Rate:     4.00
   Payment Rate:     4.20
   Rate Change:      +5.0% ⬆️
   FX Gain:          AED 200.00
   ```

---

## 🎯 Quick Test Summary

### What You Just Did:
1. ✅ Configured FX accounts (7150, 8150, 7210, 8210)
2. ✅ Set base currency (AED)
3. ✅ Loaded exchange rates (EUR→AED @ 4.00, then 4.20)
4. ✅ Created invoice in EUR @ 4.00
5. ✅ Posted invoice (locked rate at 4.00)
6. ✅ Created payment in EUR @ 4.20
7. ✅ Posted payment (system auto-calculated 200 AED gain)

### What You Saw:
- ✅ FX gain of **200 AED** posted automatically
- ✅ Account 7150 has credit balance of 200 AED
- ✅ Profit & Loss shows FX Gains separately
- ✅ Journal entry has 3 lines (not just 2)

---

## 🔄 Testing FX Loss (Opposite Scenario)

Want to see an FX LOSS instead? Follow same steps but:

### Scenario: Rate Decreased
1. Create invoice: USD 1,000 @ 3.67 = AED 3,670
2. Change rate to: USD→AED @ 3.65 (lower!)
3. Create payment: USD 1,000 @ 3.65 = AED 3,650
4. **Result:** FX LOSS of 20 AED

**Journal Entry:**
```
DR  Bank Account                3,650.00
DR  FX Loss Expense (8150)         20.00 ← LOSS!
    CR  Accounts Receivable            3,670.00
```

**Profit & Loss:**
```
EXPENSES:
  FX Losses (8150)               20.00 ← Reduces profit
```

---

## 📊 Testing Different Scenarios

### Test Case 1: Large Gain
```
Invoice:  EUR 10,000 @ 4.00 = AED 40,000
Payment:  EUR 10,000 @ 4.50 = AED 45,000
FX Gain:  AED 5,000 🎉
```

### Test Case 2: Multiple Currencies
```
Invoice 1: EUR 5,000 @ 4.00 = AED 20,000
Payment:   EUR 5,000 @ 4.10 = AED 20,500
FX Gain:   AED 500

Invoice 2: USD 10,000 @ 3.67 = AED 36,700
Payment:   USD 10,000 @ 3.60 = AED 36,000
FX Loss:   AED 700

Net FX Impact: 500 - 700 = -200 AED (net loss)
```

### Test Case 3: Same Rate (No FX)
```
Invoice:  GBP 2,000 @ 4.68 = AED 9,360
Payment:  GBP 2,000 @ 4.68 = AED 9,360
FX Impact: 0 (no extra journal lines)
```

---

## 🔍 Verification Checklist

After each test, verify:

### ✅ Invoice Level
- [ ] Invoice shows exchange_rate field filled
- [ ] Invoice shows base_currency_total
- [ ] Invoice status = POSTED

### ✅ Payment Level
- [ ] Payment shows exchange_rate
- [ ] Payment shows invoice_currency
- [ ] Payment status = POSTED
- [ ] FX preview showed correct gain/loss

### ✅ Journal Entry Level
- [ ] Entry has 3 lines (if FX impact)
- [ ] FX line uses correct account (7150 or 8150)
- [ ] FX line amount = rate difference × invoice amount
- [ ] Entry balances (debits = credits)

### ✅ Reports Level
- [ ] Trial Balance: Account 7150 shows FX gains
- [ ] Trial Balance: Account 8150 shows FX losses
- [ ] P&L: FX appears in income/expense sections
- [ ] Balance Sheet: AR cleared correctly

---

## 🎓 Understanding the Results

### What the Numbers Mean:

**Invoice Rate = 4.00**
- You "expected" to receive: 1,000 × 4.00 = 4,000 AED
- This amount was booked in AR

**Payment Rate = 4.20**
- You "actually" received: 1,000 × 4.20 = 4,200 AED
- Customer paid same EUR amount, but you got more AED!

**FX Gain = 200 AED**
- The difference is pure profit from currency movement
- Not from sales, but from favorable exchange rate
- Recorded separately in account 7150

### Why This Matters:

**For Management:**
- See currency impact on profitability
- Make informed hedging decisions
- Understand real vs. book values

**For Accounting:**
- Comply with IAS 21 standards
- Accurate financial statements
- Proper audit trail

**For Tax:**
- FX gains may be taxable
- FX losses may be deductible
- Separate tracking required

---

## 🚀 Next Steps

### 1. Test AP (Accounts Payable) with FX
Same process but reversed:
- Create AP invoice in USD
- Post to GL
- Create AP payment with different rate
- See FX gain/loss in journal entry

### 2. Create FX Report Dashboard
- Navigate to custom reports (if exists)
- Filter by accounts 7150, 8150
- See all FX transactions
- Export to Excel

### 3. Period-End Revaluation (Advanced)
Test unrealized gains/losses:
- Leave some foreign currency invoices unpaid
- Run revaluation at month-end
- See accounts 7210, 8210 in action

### 4. Real Production Use
Once comfortable:
- Process actual customer invoices
- Handle real supplier bills
- Monitor FX exposure regularly

---

## 🆘 Troubleshooting

### Problem: No FX line in journal entry
**Cause:** Rate was same at invoice and payment time  
**Solution:** Normal! No FX if rate unchanged

### Problem: Error "FX account not configured"
**Cause:** Missing FX account mapping  
**Solution:** Go to FX Config, configure all 4 types

### Problem: Wrong FX amount calculated
**Cause:** Incorrect exchange rate used  
**Solution:** Check exchange rate table, verify dates match

### Problem: Can't see FX in reports
**Cause:** Payment not posted to GL  
**Solution:** Post payment, refresh reports

---

## 📚 Summary

### You've Successfully:
✅ Configured FX system  
✅ Created multi-currency transactions  
✅ Seen automatic FX calculation  
✅ Verified results in multiple places  
✅ Understood the accounting impact  

### FX Workflow is Now:
```
1. Invoice in EUR → Rate locked @ 4.00
2. Time passes → Rate changes to 4.20
3. Payment in EUR → System detects difference
4. Auto-calculate → 200 AED gain
5. Auto-post → Account 7150 credited
6. Reports updated → Profit increased
```

### Key Achievement:
🎉 **You now have a fully functional multi-currency accounting system with automatic FX gain/loss tracking!**

---

**Last Updated:** October 19, 2025  
**Status:** ✅ Ready for Production Testing  
**Next:** Process real transactions and monitor FX exposure

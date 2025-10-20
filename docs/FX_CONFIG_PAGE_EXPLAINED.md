# FX Configuration Page - Complete User Guide

**Understanding the FX Configuration Page: What It Does, What Inputs You Need, and Expected Results**

---

## 📚 Table of Contents
1. [What Is This Page?](#what-is-this-page)
2. [Why Is It Important?](#why-is-it-important)
3. [Section 1: Base Currency](#section-1-base-currency)
4. [Section 2: FX Gain/Loss Accounts](#section-2-fx-gainloss-accounts)
5. [Step-by-Step Configuration Guide](#step-by-step-configuration-guide)
6. [Real Examples](#real-examples)
7. [What Happens After Configuration](#what-happens-after-configuration)
8. [Troubleshooting](#troubleshooting)

---

## What Is This Page?

The **FX Configuration** page is the control center for your multi-currency accounting setup. It has **TWO main sections**:

1. **Base Currency** - Define your company's "home" currency
2. **FX Gain/Loss Accounts** - Map GL accounts for foreign exchange gains and losses

**Location:** Dashboard → FX Configuration (Globe icon, blue card)

**Access:** `/fx/config`

---

## Why Is It Important?

### Without Proper Configuration:
❌ Multi-currency invoices will fail to post  
❌ Payments in foreign currencies will be rejected  
❌ FX gains/losses won't be recorded  
❌ Financial reports will be inaccurate  

### With Proper Configuration:
✅ Multi-currency transactions work seamlessly  
✅ FX gains/losses automatically posted to GL  
✅ Accurate financial reporting  
✅ Compliance with accounting standards (IAS 21)  

---

## Section 1: Base Currency

### What It Is
Your company's **primary/home currency** used for financial reporting. All transactions ultimately convert to this currency.

### Visual Layout
```
┌─────────────────────────────────────────────────────────────┐
│  🌐 Base Currency                                            │
├─────────────────────────────────────────────────────────────┤
│  Your company's base currency is:                           │
│                                                              │
│  د.إ    AED                                                  │
│         United Arab Emirates Dirham                         │
│                                                              │
│  All financial reports are prepared in this currency.       │
│  Foreign currency transactions are converted to AED.        │
│                                                              │
│                                      [Change Base Currency] │
└─────────────────────────────────────────────────────────────┘
```

### Required Input
- **Select ONE currency** from available currencies (USD, EUR, AED, GBP, etc.)

### How to Set Base Currency

**Option 1: First Time Setup (No Base Currency Set)**
1. Page shows red warning: "⚠️ No base currency is set!"
2. Grid of available currencies displayed
3. Click on your preferred currency (e.g., **AED**)
4. Confirmation dialog appears
5. Click "OK" to confirm

**Option 2: Change Existing Base Currency**
1. Click **"Click to change base currency..."** link
2. Grid of currencies expands
3. Current base currency shown with "Current" badge
4. Click different currency to change
5. Confirmation warning: "Changing the base currency will affect all financial reporting. Are you sure?"
6. Click "OK" to proceed

### Expected Output
✅ Selected currency marked with `is_base = true` in database  
✅ All other currencies set to `is_base = false`  
✅ Blue box displays selected currency prominently  
✅ Success message: "Base currency updated successfully!"  

### Important Notes
⚠️ **One Currency Only:** Only ONE currency can be base currency  
⚠️ **Affects Reporting:** All financial statements will be in this currency  
⚠️ **Changing Impact:** Changing base currency affects historical comparisons  

### Best Practice
- **UAE Companies:** Use AED
- **Saudi Companies:** Use SAR
- **US Companies:** Use USD
- **European Companies:** Use EUR

**Recommendation:** Set this once during initial setup and **rarely change it**.

---

## Section 2: FX Gain/Loss Accounts

### What It Is
Maps 4 types of FX events to specific GL accounts where gains/losses are recorded.

### The 4 Required Types

```
┌─────────────────────────────────────────────────────────────────────┐
│  Type                    │ When Used              │ Account Type   │
├──────────────────────────┼────────────────────────┼────────────────┤
│  ⬆️ REALIZED GAIN        │ Payment settled        │ INCOME         │
│                          │ Rate improved          │                │
├──────────────────────────┼────────────────────────┼────────────────┤
│  ⬇️ REALIZED LOSS        │ Payment settled        │ EXPENSE        │
│                          │ Rate worsened          │                │
├──────────────────────────┼────────────────────────┼────────────────┤
│  ⬆️ UNREALIZED GAIN      │ Period-end revaluation │ INCOME         │
│                          │ Open balances up       │                │
├──────────────────────────┼────────────────────────┼────────────────┤
│  ⬇️ UNREALIZED LOSS      │ Period-end revaluation │ EXPENSE        │
│                          │ Open balances down     │                │
└──────────────────────────┴────────────────────────┴────────────────┘
```

### Visual Layout (Each Type Card)

**Before Configuration:**
```
┌────────────────────────────────────────────┐
│  ⬆️ Realized FX Gain                       │
│  Gains from settled foreign currency       │
│  transactions                              │
│                                            │
│  ⚠️ Not configured - FX transactions      │
│     will fail                              │
└────────────────────────────────────────────┘
```

**After Configuration:**
```
┌────────────────────────────────────────────┐
│  ⬆️ Realized FX Gain                       │
│  Gains from settled foreign currency       │
│  transactions                              │
│                                            │
│  ✅ Configured Account:                    │
│     7150 - Foreign Exchange Gains          │
│                              [Edit] [Delete]│
└────────────────────────────────────────────┘
```

### Required Inputs (For Each Type)

#### Step 1: Click "+ Configure Account"
Form appears with fields:

1. **Type** (Dropdown)
   - Options:
     - Realized FX Gain
     - Realized FX Loss
     - Unrealized FX Gain
     - Unrealized FX Loss
   - **Select:** One that's not yet configured

2. **GL Account** (Dropdown)
   - Shows: All Income (IN) and Expense (EX) accounts
   - Format: `7150 - Foreign Exchange Gains`
   - **Select:** Appropriate account based on type

3. **Description** (Optional text)
   - Purpose: Additional notes
   - **Example:** "Used for settled FX gains on customer payments"

#### Step 2: Click "Create"

### Recommended Account Mapping

| Type              | Account Code | Account Name                  | Type    |
|-------------------|--------------|-------------------------------|---------|
| REALIZED_GAIN     | **7150**     | Foreign Exchange Gains        | INCOME  |
| REALIZED_LOSS     | **8150**     | Foreign Exchange Losses       | EXPENSE |
| UNREALIZED_GAIN   | **7210**     | Unrealized FX Gains           | INCOME  |
| UNREALIZED_LOSS   | **8210**     | Unrealized FX Losses          | EXPENSE |

### Expected Output (Per Configuration)
✅ Account mapping saved to database  
✅ Card turns green with checkmark  
✅ "Configured Account" shows selected GL account  
✅ [Edit] and [Delete] buttons appear  

### Warning Indicators

**Yellow Warning (Top of Page):**
```
⚠️ Incomplete FX Configuration
The following FX account types are not configured:
• Realized FX Loss
• Unrealized FX Gain
• Unrealized FX Loss
```
This appears until all 4 types are configured.

---

## Step-by-Step Configuration Guide

### Complete Setup (From Scratch)

#### Step 1: Set Base Currency
1. Navigate to FX Configuration page
2. If no base currency set, select **AED** (or your preferred currency)
3. Confirm the change
4. Verify blue box shows: "Your company's base currency is: AED"

#### Step 2: Create Accounts (If Not Exist)
**Before configuring FX, ensure these GL accounts exist:**

Go to Chart of Accounts and create:
```
7150 - Foreign Exchange Gains (INCOME)
8150 - Foreign Exchange Losses (EXPENSE)
7210 - Unrealized FX Gains (INCOME)
8210 - Unrealized FX Losses (EXPENSE)
```

#### Step 3: Configure Realized Gain
1. Click **"+ Configure Account"**
2. Form appears
3. Select:
   - **Type:** Realized FX Gain
   - **GL Account:** 7150 - Foreign Exchange Gains
   - **Description:** "Gains from settled customer/supplier payments"
4. Click **"Create"**
5. Card turns green ✅

#### Step 4: Configure Realized Loss
1. Click **"+ Configure Account"** again
2. Select:
   - **Type:** Realized FX Loss
   - **GL Account:** 8150 - Foreign Exchange Losses
   - **Description:** "Losses from settled customer/supplier payments"
3. Click **"Create"**
4. Card turns green ✅

#### Step 5: Configure Unrealized Gain
1. Click **"+ Configure Account"** again
2. Select:
   - **Type:** Unrealized FX Gain
   - **GL Account:** 7210 - Unrealized FX Gains
   - **Description:** "Period-end revaluation gains on open balances"
3. Click **"Create"**
4. Card turns green ✅

#### Step 6: Configure Unrealized Loss
1. Click **"+ Configure Account"** again
2. Select:
   - **Type:** Unrealized FX Loss
   - **GL Account:** 8210 - Unrealized FX Losses
   - **Description:** "Period-end revaluation losses on open balances"
3. Click **"Create"**
4. Card turns green ✅

#### Step 7: Verify Complete Setup
✅ All 4 cards are green  
✅ Yellow warning at top disappears  
✅ Each card shows configured account  
✅ Ready to process multi-currency transactions!  

---

## Real Examples

### Example 1: UAE Company Setup

**Company:** ABC Trading LLC (Dubai)  
**Base Currency:** AED  
**Transactions:** Buy from Europe (EUR), Sell to USA (USD)  

**Configuration:**
```
Base Currency: AED (United Arab Emirates Dirham)

FX Accounts:
├─ Realized Gain:     7150 - Foreign Exchange Gains
├─ Realized Loss:     8150 - Foreign Exchange Losses
├─ Unrealized Gain:   7210 - Unrealized FX Gains
└─ Unrealized Loss:   8210 - Unrealized FX Losses
```

**What Happens:**
- Customer invoice in USD → Converted to AED at posting
- Payment received later → FX gain/loss posted to 7150/8150
- Period-end → Open USD balances revalued, posted to 7210/8210

---

### Example 2: Multi-National Company

**Company:** Global Corp (Headquarters in USA)  
**Base Currency:** USD  
**Transactions:** Operations in UAE, Saudi, Egypt  

**Configuration:**
```
Base Currency: USD (United States Dollar)

FX Accounts:
├─ Realized Gain:     9100 - FX Gain on Operations
├─ Realized Loss:     9200 - FX Loss on Operations
├─ Unrealized Gain:   9110 - Unrealized FX Gain
└─ Unrealized Loss:   9210 - Unrealized FX Loss
```

**What Happens:**
- UAE invoice in AED → Converted to USD
- Saudi invoice in SAR → Converted to USD
- All FX impacts recorded in 9xxx accounts

---

## What Happens After Configuration

### Immediate Effects

#### 1. Multi-Currency Invoices Work
**Before:** Invoice posting fails with "FX accounts not configured"  
**After:** Invoice posts successfully, amount converted to base currency

**Example:**
```
Invoice: EUR 1,000
Rate: 4.00 (1 EUR = 4.00 AED)

Journal Entry Created:
DR  Accounts Receivable    4,000 AED
    CR  Sales Revenue          4,000 AED
```

#### 2. FX Payments Auto-Calculate
**Before:** Payment with FX rejected  
**After:** Payment posts with automatic FX gain/loss entry

**Example:**
```
Invoice: EUR 1,000 @ 4.00 = 4,000 AED (booked)
Payment: EUR 1,000 @ 4.20 = 4,200 AED (received)
FX Gain: 200 AED

Journal Entry Created:
DR  Bank Account           4,200 AED
    CR  Accounts Receivable        4,000 AED
    CR  FX Gain (7150)               200 AED  ← Auto-posted!
```

#### 3. Financial Reports Accurate
**Before:** FX gains/losses not tracked  
**After:** P&L shows separate FX line items

**Profit & Loss Statement:**
```
Revenue:
  Sales Revenue           500,000 AED
  FX Gains (7150)          15,200 AED  ← Now visible!
                          ───────────
  Total Revenue           515,200 AED

Expenses:
  Cost of Goods Sold      300,000 AED
  FX Losses (8150)          3,500 AED  ← Now visible!
  ...
```

---

## Troubleshooting

### Problem 1: Can't Post Multi-Currency Invoice
**Error:** "No FX gain/loss account configured for REALIZED_GAIN"

**Solution:**
1. Go to FX Configuration page
2. Check which types are missing (yellow warning)
3. Configure missing types
4. Try posting invoice again

---

### Problem 2: Multiple Base Currencies
**Error:** "Multiple base currencies found"

**Solution:**
1. Database issue - multiple currencies marked `is_base=True`
2. Run this command:
```python
# In Django shell
from core.models import Currency
Currency.objects.all().update(is_base=False)
Currency.objects.filter(code='AED').update(is_base=True)
```
3. Refresh FX Configuration page

---

### Problem 3: Can't Find GL Accounts
**Error:** Dropdown shows "Select Account..." but no options

**Solution:**
1. Go to Chart of Accounts
2. Create required accounts:
   - 7150 (INCOME type)
   - 8150 (EXPENSE type)
   - 7210 (INCOME type)
   - 8210 (EXPENSE type)
3. Return to FX Configuration
4. Accounts now appear in dropdown

---

### Problem 4: Wrong Account Selected
**Solution:**
1. Find the incorrect configuration card
2. Click **[Edit]** button
3. Change GL Account in dropdown
4. Click **"Update"**

**Or:**
1. Click **[Delete]** to remove
2. Click **"+ Configure Account"** to recreate

---

## Best Practices

### ✅ DO:
1. **Set base currency during initial setup** before any transactions
2. **Configure all 4 FX account types** before going live
3. **Use standard account codes** (7150, 8150, 7210, 8210)
4. **Test with sample transaction** before processing real data
5. **Document your setup** for auditors

### ❌ DON'T:
1. **Don't change base currency** after transactions exist
2. **Don't use random accounts** - follow chart of accounts structure
3. **Don't leave any type unconfigured** - all 4 are needed
4. **Don't delete configurations** during active transactions
5. **Don't use same account** for multiple types

---

## Summary

### Required Setup (Minimum):
1. ✅ **1 Base Currency** (e.g., AED)
2. ✅ **4 FX Account Mappings:**
   - Realized Gain → Income Account
   - Realized Loss → Expense Account
   - Unrealized Gain → Income Account
   - Unrealized Loss → Expense Account

### Time to Complete:
- **First Time:** 10-15 minutes (including creating GL accounts)
- **Already Have Accounts:** 2-3 minutes

### Result:
- ✅ Multi-currency transactions fully functional
- ✅ Automatic FX gain/loss calculation
- ✅ Compliant financial reporting
- ✅ Accurate profit & loss tracking

---

## Quick Reference

### Checklist
```
□ Base currency set (AED, USD, EUR, etc.)
□ Realized Gain account configured (7150)
□ Realized Loss account configured (8150)
□ Unrealized Gain account configured (7210)
□ Unrealized Loss account configured (8210)
□ All cards show green checkmarks
□ No yellow warning at top of page
□ Test transaction successful
```

### Account Code Reference
```
7150 - Foreign Exchange Gains (INCOME)
8150 - Foreign Exchange Losses (EXPENSE)
7210 - Unrealized FX Gains (INCOME)
8210 - Unrealized FX Losses (EXPENSE)
```

---

**Last Updated:** October 19, 2025  
**Status:** ✅ Production Ready  
**Support:** Check docs/FX_CONFIG_PAGE_GUIDE.md for more details

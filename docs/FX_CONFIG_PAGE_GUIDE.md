# FX Configuration Page - Complete Guide

**Location:** `/fx/config`  
**File:** `frontend/src/app/fx/config/page.tsx`  
**Date:** October 15, 2025

---

## 📋 Overview

The FX Configuration page is the **control center** for your multi-currency accounting setup. It manages two critical aspects:

1. **Base Currency** - Your company's primary/home currency
2. **FX Gain/Loss Accounts** - GL accounts for tracking foreign exchange gains and losses

---

## 🎯 Why This Page Is Important

When you do business in multiple currencies, you need to:
- Define which currency is your "home" currency (for reporting)
- Track gains/losses from currency fluctuations
- Ensure proper accounting treatment for FX transactions

Without proper configuration, multi-currency transactions will fail or produce incorrect financial statements.

---

## 🏠 Base Currency Section

### What It Does

The **base currency** (also called "home currency" or "functional currency") is:
- The primary currency your company operates in
- The currency used for financial reporting
- The target currency for all foreign currency conversions

### Visual Indicators

When configured:
```
┌─────────────────────────────────────────────┐
│ Your company's base currency is:            │
│                                             │
│  $  USD                                     │
│     United States Dollar                    │
│                                             │
│ All financial reports are prepared in USD.  │
│ Foreign currency transactions are           │
│ converted to USD.                           │
│                                             │
│           [Change Base Currency]            │
└─────────────────────────────────────────────┘
```

When NOT configured (warning):
```
┌─────────────────────────────────────────────┐
│ ⚠️ No base currency is set!                 │
│    Please select one:                       │
│                                             │
│  [USD]  [EUR]  [AED]  [GBP]               │
│  [INR]  [SAR]  [EGP]  ...                 │
└─────────────────────────────────────────────┘
```

### How to Set/Change Base Currency

1. **First Time Setup:**
   - Click on any currency button
   - Confirm the selection
   - That currency becomes your base currency

2. **Changing Base Currency:**
   - Click "Change Base Currency" button
   - Click "Click to change base currency..." dropdown
   - Select new currency
   - Confirm the change (⚠️ warning shown)

### Important Warning

Changing base currency affects:
- All financial report calculations
- Historical exchange rate conversions
- Comparative financial statements

**Recommendation:** Set base currency once during initial setup and avoid changing it.

---

## 💱 FX Gain/Loss Accounts Section

### What Are FX Gains and Losses?

**Foreign exchange gains and losses** occur when exchange rates change between:
- The transaction date (invoice/payment created)
- The settlement date (payment received/made)
- The period-end (revaluation)

### Four Types of FX Accounts

#### 1. **Realized Gain** (Income Account)
- **When it occurs:** You actually receive MORE money than expected due to favorable exchange rate movement
- **Example:** 
  ```
  Invoice Date: USD $100 @ 3.67 AED = 367 AED
  Payment Date: USD $100 @ 3.70 AED = 370 AED
  Realized Gain: 3 AED (you got more AED than expected!)
  ```
- **GL Entry:**
  ```
  Debit: Bank Account           370 AED
  Credit: Accounts Receivable   367 AED
  Credit: Realized FX Gain        3 AED
  ```

#### 2. **Realized Loss** (Expense Account)
- **When it occurs:** You receive LESS money than expected due to unfavorable exchange rate movement
- **Example:**
  ```
  Invoice Date: USD $100 @ 3.67 AED = 367 AED
  Payment Date: USD $100 @ 3.64 AED = 364 AED
  Realized Loss: 3 AED (you got less AED!)
  ```
- **GL Entry:**
  ```
  Debit: Bank Account          364 AED
  Debit: Realized FX Loss        3 AED
  Credit: Accounts Receivable  367 AED
  ```

#### 3. **Unrealized Gain** (Income Account)
- **When it occurs:** Period-end revaluation shows you WOULD gain if you settled today
- **Example:**
  ```
  Month-End: Outstanding AR $1,000 @ original rate 3.67 = 3,670 AED
  New Rate: $1,000 @ 3.73 = 3,730 AED
  Unrealized Gain: 60 AED (potential gain, not settled yet)
  ```
- **GL Entry (period-end adjustment):**
  ```
  Debit: Accounts Receivable    60 AED
  Credit: Unrealized FX Gain    60 AED
  ```
- **Note:** Reversed next period when settled

#### 4. **Unrealized Loss** (Expense Account)
- **When it occurs:** Period-end revaluation shows you WOULD lose if you settled today
- **Example:**
  ```
  Month-End: Outstanding AR $1,000 @ original rate 3.67 = 3,670 AED
  New Rate: $1,000 @ 3.60 = 3,600 AED
  Unrealized Loss: 70 AED (potential loss)
  ```
- **GL Entry (period-end adjustment):**
  ```
  Debit: Unrealized FX Loss       70 AED
  Credit: Accounts Receivable     70 AED
  ```

---

## 🎨 Visual Design Elements

### Configuration Status Cards

Each FX account type is displayed in a card with:

**Configured (Green):**
```
┌─────────────────────────────────────────┐
│ 📈 Realized FX Gain                     │
│    Gains from settled transactions      │
│                                         │
│ Configured Account:                     │
│ 8010 - Foreign Exchange Gain            │
│                                         │
│                    [Edit]    [Delete]   │
└─────────────────────────────────────────┘
```

**Not Configured (Yellow Warning):**
```
┌─────────────────────────────────────────┐
│ 📈 Realized FX Gain                     │
│    Gains from settled transactions      │
│                                         │
│ ⚠️ Not configured - FX transactions    │
│    will fail                            │
└─────────────────────────────────────────┘
```

### Warning Banner (Top of Page)

When not fully configured:
```
┌────────────────────────────────────────────────────┐
│ ⚠️ Incomplete FX Configuration                     │
│                                                    │
│ The following FX account types are not configured:│
│  • Realized FX Gain                               │
│  • Unrealized FX Loss                             │
└────────────────────────────────────────────────────┘
```

---

## 🛠️ How to Configure FX Accounts

### Step-by-Step Setup

1. **Click "+ Configure Account"** button

2. **Select Type** from dropdown:
   - Realized FX Gain
   - Realized FX Loss
   - Unrealized FX Gain
   - Unrealized FX Loss

3. **Select GL Account:**
   - Choose from Income accounts (for gains)
   - Choose from Expense accounts (for losses)
   - Accounts are filtered to show only IN/EX types

4. **Add Description** (optional):
   - Add notes about the account usage
   - Example: "Auto-posted from payment settlements"

5. **Click "Create"**

### Best Practices

✅ **DO:**
- Configure all 4 account types before processing multi-currency transactions
- Use separate accounts for each type (don't reuse)
- Use Income account types for gains
- Use Expense account types for losses
- Document your choices in the description field

❌ **DON'T:**
- Use the same account for multiple types
- Use Asset/Liability accounts for FX accounts
- Skip configuration and hope it works
- Delete accounts that have transaction history

---

## 🔄 Account Configuration Workflow

### Creating a Configuration

```
User clicks "+ Configure Account"
    ↓
Form appears with dropdowns
    ↓
User selects Type (e.g., "Realized Gain")
    ↓
User selects GL Account (e.g., "8010 - FX Gain")
    ↓
User adds optional description
    ↓
Clicks "Create"
    ↓
API POST /api/fx/accounts/
    ↓
Configuration saved to database
    ↓
Card updates to show "Configured" status
    ↓
Warning banner updates (fewer missing items)
```

### Editing a Configuration

```
User clicks "Edit" on configured card
    ↓
Form pre-fills with existing data
    ↓
User changes account or description
    ↓
Clicks "Update"
    ↓
API PATCH /api/fx/accounts/{id}/
    ↓
Configuration updated
    ↓
Card reflects new settings
```

### Deleting a Configuration

```
User clicks "Delete" on configured card
    ↓
Confirmation dialog appears
    ↓
User confirms deletion
    ↓
API DELETE /api/fx/accounts/{id}/
    ↓
Configuration removed
    ↓
Card shows "Not configured" warning
```

---

## 🔗 Integration with Other Features

### How FX Configuration Is Used

1. **AR/AP Payment Processing:**
   - When payment currency differs from invoice currency
   - System calculates FX difference
   - Posts to configured Realized Gain/Loss account

2. **Period-End Revaluation:**
   - Outstanding foreign currency balances are revalued
   - Posts to configured Unrealized Gain/Loss accounts
   - Reversed next period when settled

3. **Multi-Currency Reporting:**
   - All foreign currency amounts converted to base currency
   - FX gains/losses shown separately in P&L

4. **Exchange Rate Management:**
   - Base currency used as reference for all rates
   - System validates rates exist before transactions

---

## 📊 Example: Complete Setup

### Recommended Account Structure

```
Income Accounts (IN):
  8010 - Realized Foreign Exchange Gain
  8020 - Unrealized Foreign Exchange Gain

Expense Accounts (EX):
  9010 - Realized Foreign Exchange Loss
  9020 - Unrealized Foreign Exchange Loss
```

### Configuration Table

| Type              | GL Account | Code | Description                    |
|-------------------|------------|------|--------------------------------|
| Realized Gain     | 8010       | IN   | Settled FX gains              |
| Realized Loss     | 9010       | EX   | Settled FX losses             |
| Unrealized Gain   | 8020       | IN   | Period-end revaluation gains  |
| Unrealized Loss   | 9020       | EX   | Period-end revaluation losses |

---

## 🎯 Real-World Scenario

### Scenario: UAE Company (Base Currency: AED) with US Client

1. **Setup:**
   - Base Currency: AED (United Arab Emirates Dirham)
   - FX Accounts: All 4 types configured
   - Exchange Rate: USD/AED set daily

2. **Transaction Flow:**

   **Day 1 - Invoice Created:**
   ```
   AR Invoice: USD $1,000
   Exchange Rate: 1 USD = 3.67 AED
   Invoice Value in AED: 3,670 AED
   ```

   **Day 30 - Payment Received:**
   ```
   Payment: USD $1,000
   Exchange Rate: 1 USD = 3.73 AED
   Payment Value in AED: 3,730 AED
   
   Difference: 3,730 - 3,670 = 60 AED GAIN
   ```

   **Automatic GL Entry:**
   ```
   Debit:  Bank Account (AED)         3,730
   Credit: Accounts Receivable (AED)  3,670
   Credit: Realized FX Gain (8010)       60
   ```

3. **Result:**
   - Customer paid USD $1,000 as agreed
   - Due to rate movement, you received 60 AED more
   - System automatically recorded the gain
   - FX Gain appears in Income Statement

---

## 🐛 Troubleshooting

### Error: "Failed to load FX configuration"
**Cause:** Backend API not responding  
**Solution:** Check backend server is running on localhost:8000

### Error: "Failed to save: account already configured"
**Cause:** Account is already assigned to another FX type  
**Solution:** Choose a different GL account

### Warning: "Not configured - FX transactions will fail"
**Cause:** Missing FX account configuration  
**Solution:** Configure all 4 account types before processing FX transactions

### Error: "No base currency is set"
**Cause:** No currency marked as is_base=true  
**Solution:** Click on a currency in the red warning box to set base currency

### Tip: "Choose Income/Expense accounts only"
**Cause:** FX gains/losses affect P&L, not Balance Sheet  
**Solution:** Filter shows only IN/EX accounts in dropdown

---

## 🔐 Permissions & Security

- Page requires user authentication
- API endpoints protected by CSRF token
- Delete operations require confirmation
- Base currency changes show warning before proceeding

---

## 📱 Mobile Responsiveness

- Cards stack vertically on mobile
- Currency selection grid responsive (4 cols → 2 cols → 1 col)
- Form fields stack on small screens
- All actions accessible via touch

---

## 🚀 Performance Notes

- Loads all data in single API call (parallel requests)
- No pagination needed (limited number of FX configs)
- Form validation client-side for speed
- Optimistic UI updates where appropriate

---

## 📚 Related Documentation

- `docs/FRONTEND_IMPLEMENTATION_COMPLETE.md` - Overview of all new features
- `docs/QUICK_REFERENCE_NEW_FEATURES.md` - Quick reference guide
- `docs/BACKEND_FRONTEND_ENDPOINT_ANALYSIS.md` - API endpoint documentation

---

## ✅ Testing Checklist

Before using in production, test:

- [ ] Set base currency for first time
- [ ] Change base currency (warning should appear)
- [ ] Configure all 4 FX account types
- [ ] Edit an existing configuration
- [ ] Delete a configuration (should show warning)
- [ ] Try to use same account twice (should fail)
- [ ] Verify warning banner updates as you configure
- [ ] Check configuration persists after page refresh
- [ ] Test on mobile device/small screen

---

**Page Complete! Ready for Production Use! 🎉**

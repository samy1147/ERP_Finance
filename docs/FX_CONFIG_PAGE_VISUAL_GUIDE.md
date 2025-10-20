# FX Configuration Page - Visual Walkthrough

**Quick Visual Guide: What You See and What to Do**

---

## Page Layout

```
┌───────────────────────────────────────────────────────────────────────────┐
│  FX Configuration                                                          │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│  ⚠️ Incomplete FX Configuration                                           │
│  The following FX account types are not configured:                       │
│  • Realized FX Loss                                                       │
│  • Unrealized FX Gain                                                     │
│  • Unrealized FX Loss                                                     │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│  🌐 Base Currency                                                         │
├───────────────────────────────────────────────────────────────────────────┤
│  Your company's base currency is:                                        │
│                                                                           │
│  د.إ    AED                                                               │
│         United Arab Emirates Dirham                                      │
│                                                                           │
│  All financial reports are prepared in this currency. Foreign currency   │
│  transactions are converted to AED.                                      │
│                                                                           │
│                                           [Change Base Currency]         │
│                                                                           │
│  ▼ Click to change base currency...                                     │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│  FX Gain/Loss Accounts                            [+ Configure Account]  │
├───────────────────────────────────────────────────────────────────────────┤
│  Configure which GL accounts to use for foreign exchange gains and       │
│  losses. These accounts are automatically used when FX differences occur.│
│                                                                           │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐       │
│  │ ⬆️ Realized FX Gain         │  │ ⬇️ Realized FX Loss         │       │
│  │ Gains from settled foreign  │  │ Losses from settled foreign │       │
│  │ currency transactions       │  │ currency transactions       │       │
│  │                             │  │                             │       │
│  │ ✅ Configured Account:      │  │ ⚠️ Not configured - FX      │       │
│  │ 7150 - Foreign Exchange     │  │    transactions will fail   │       │
│  │ Gains                       │  │                             │       │
│  │                [Edit][Delete]│  │                             │       │
│  └─────────────────────────────┘  └─────────────────────────────┘       │
│                                                                           │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐       │
│  │ ⬆️ Unrealized FX Gain       │  │ ⬇️ Unrealized FX Loss       │       │
│  │ Potential gains from        │  │ Potential losses from       │       │
│  │ revaluation of foreign      │  │ revaluation of foreign      │       │
│  │ currency balances           │  │ currency balances           │       │
│  │                             │  │                             │       │
│  │ ⚠️ Not configured - FX      │  │ ⚠️ Not configured - FX      │       │
│  │    transactions will fail   │  │    transactions will fail   │       │
│  └─────────────────────────────┘  └─────────────────────────────┘       │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│  💡 How FX Accounts Work                                                  │
├───────────────────────────────────────────────────────────────────────────┤
│  Realized Gains/Losses: Occur when you actually settle a transaction.    │
│  For example, if you invoice USD $100 when the rate is 3.67 AED (= 367   │
│  AED), but receive payment when the rate is 3.70 AED (= 370 AED), you    │
│  have a realized gain of 3 AED.                                          │
│                                                                           │
│  Unrealized Gains/Losses: Occur at period-end when you revalue foreign   │
│  currency balances. These are "paper" gains/losses that haven't been     │
│  settled yet.                                                            │
│                                                                           │
│  Best Practice: Configure all four account types before processing       │
│  multi-currency transactions. Use Income accounts for gains and Expense  │
│  accounts for losses.                                                    │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Input Form (When You Click "+ Configure Account")

```
┌───────────────────────────────────────────────────────────────────────────┐
│  Add FX Account Configuration                                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Type *                                    GL Account *                  │
│  ┌─────────────────────────────────┐     ┌─────────────────────────────┐│
│  │ Realized FX Gain - Gains from  ▼│     │ Select Account...          ▼││
│  │ settled foreign currency        │     │                             ││
│  │ transactions                    │     │ 7150 - Foreign Exchange     ││
│  │                                 │     │        Gains                ││
│  │ • Realized FX Gain              │     │ 8150 - Foreign Exchange     ││
│  │ • Realized FX Loss              │     │        Losses               ││
│  │ • Unrealized FX Gain            │     │ 7210 - Unrealized FX Gains  ││
│  │ • Unrealized FX Loss            │     │ 8210 - Unrealized FX Losses ││
│  └─────────────────────────────────┘     └─────────────────────────────┘│
│                                                                           │
│  Description (Optional)                                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Used for gains on settled customer and supplier payments          │  │
│  │                                                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  [Create]  [Cancel]                                                      │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step: Setting Base Currency (First Time)

### Before Setup
```
┌───────────────────────────────────────────────────────────────────────────┐
│  🌐 Base Currency                                                         │
├───────────────────────────────────────────────────────────────────────────┤
│  ⚠️ No base currency is set! Please select one:                          │
│                                                                           │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐        │
│  │ AED │  │ USD │  │ EUR │  │ GBP │  │ SAR │  │ EGP │  │ INR │        │
│  │ UAE │  │ US  │  │Euro │  │ UK  │  │Saudi│  │Egypt│  │India│        │
│  │Dirham│  │Dollar│ │     │  │Pound│  │Riyal│  │Pound│  │Rupee│        │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘        │
│                                                                           │
│  Click any currency box to set as base currency                         │
└───────────────────────────────────────────────────────────────────────────┘
```

### Action: Click "AED"
```
┌─────────────────────────────────────────┐
│  Confirm                                │
├─────────────────────────────────────────┤
│  Changing the base currency will affect │
│  all financial reporting. Are you sure? │
│                                         │
│           [Cancel]      [OK]            │
└─────────────────────────────────────────┘
```

### After Setup
```
┌───────────────────────────────────────────────────────────────────────────┐
│  🌐 Base Currency                                                         │
├───────────────────────────────────────────────────────────────────────────┤
│  Your company's base currency is:                                        │
│                                                                           │
│  د.إ    AED                                                               │
│         United Arab Emirates Dirham                                      │
│                                                                           │
│  All financial reports are prepared in this currency. Foreign currency   │
│  transactions are converted to AED.                                      │
│                                                                           │
│  ✅ Success: Base currency updated successfully!                         │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step: Configuring First FX Account

### Step 1: Click "+ Configure Account"
Form appears (see Input Form above)

### Step 2: Fill Form
```
Type:        Realized FX Gain
GL Account:  7150 - Foreign Exchange Gains
Description: Gains from settled customer and supplier payments
```

### Step 3: Click "Create"

### Step 4: Result
```
┌─────────────────────────────────────────────────┐
│ ⬆️ Realized FX Gain                             │
│ Gains from settled foreign currency             │
│ transactions                                    │
│                                                 │
│ ✅ Configured Account:                          │
│ 7150 - Foreign Exchange Gains                   │
│ Gains from settled customer and supplier        │
│ payments                                        │
│                              [Edit]   [Delete]  │
└─────────────────────────────────────────────────┘
```

Card turns from gray to **green** with checkmark!

---

## Complete Configuration Checklist

### Unconfigured State (4 Gray Cards)
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ ⬆️ Realized  │  │ ⬇️ Realized  │  │ ⬆️Unrealized │  │ ⬇️Unrealized │
│    Gain      │  │    Loss      │  │    Gain      │  │    Loss      │
│ ⚠️ Not conf  │  │ ⚠️ Not conf  │  │ ⚠️ Not conf  │  │ ⚠️ Not conf  │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

### Fully Configured State (4 Green Cards)
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ ⬆️ Realized  │  │ ⬇️ Realized  │  │ ⬆️Unrealized │  │ ⬇️Unrealized │
│    Gain      │  │    Loss      │  │    Gain      │  │    Loss      │
│ ✅ 7150      │  │ ✅ 8150      │  │ ✅ 7210      │  │ ✅ 8210      │
│ [Edit][Del]  │  │ [Edit][Del]  │  │ [Edit][Del]  │  │ [Edit][Del]  │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

---

## What Each Input Does

### 1. Base Currency Selection
**Input:** Click on currency (AED, USD, EUR, etc.)  
**Database:** Sets `Currency.is_base = True` for selected  
**Effect:** All GL postings use this as reference currency  

### 2. FX Account Type Selection
**Input:** Dropdown with 4 choices  
**Options:**
- Realized FX Gain → for payment gains
- Realized FX Loss → for payment losses
- Unrealized FX Gain → for period-end gains
- Unrealized FX Loss → for period-end losses

### 3. GL Account Selection
**Input:** Dropdown showing Income/Expense accounts  
**Filtered:** Only shows accounts with type IN or EX  
**Format:** `7150 - Foreign Exchange Gains`  

### 4. Description (Optional)
**Input:** Text area, free-form  
**Purpose:** Notes for auditors or team  
**Example:** "Used for gains when customers pay in foreign currency"  

---

## Expected Outputs

### After Setting Base Currency
```json
{
  "id": 1,
  "code": "AED",
  "name": "United Arab Emirates Dirham",
  "symbol": "د.إ",
  "is_base": true
}
```

### After Creating FX Account Config
```json
{
  "id": 1,
  "account": 7150,
  "account_details": {
    "id": 7150,
    "code": "7150",
    "name": "Foreign Exchange Gains",
    "type": "IN"
  },
  "gain_loss_type": "REALIZED_GAIN",
  "description": "Gains from settled customer and supplier payments",
  "is_active": true
}
```

### Complete Configuration API Response
```json
{
  "base_currency": {
    "id": 1,
    "code": "AED",
    "name": "United Arab Emirates Dirham",
    "symbol": "د.إ",
    "is_base": true
  },
  "fx_accounts": [
    {
      "id": 1,
      "gain_loss_type": "REALIZED_GAIN",
      "account": 7150,
      "account_details": {
        "code": "7150",
        "name": "Foreign Exchange Gains"
      }
    },
    {
      "id": 2,
      "gain_loss_type": "REALIZED_LOSS",
      "account": 8150,
      "account_details": {
        "code": "8150",
        "name": "Foreign Exchange Losses"
      }
    },
    {
      "id": 3,
      "gain_loss_type": "UNREALIZED_GAIN",
      "account": 7210,
      "account_details": {
        "code": "7210",
        "name": "Unrealized FX Gains"
      }
    },
    {
      "id": 4,
      "gain_loss_type": "UNREALIZED_LOSS",
      "account": 8210,
      "account_details": {
        "code": "8210",
        "name": "Unrealized FX Losses"
      }
    }
  ]
}
```

---

## Real-World Example: Complete Setup

### Scenario
**Company:** Dubai Electronics Trading LLC  
**Transactions:** Buy from China (USD), Sell to Europe (EUR)  

### Setup Process

#### 1. Set Base Currency
- Click **AED** button
- Confirm "Yes"
- Result: ✅ Base = AED

#### 2. Configure Realized Gain
- Click "+ Configure Account"
- Type: **Realized FX Gain**
- Account: **7150 - Foreign Exchange Gains**
- Description: "Gains when EUR customers pay"
- Click "Create"
- Result: ✅ Card turns green

#### 3. Configure Realized Loss
- Click "+ Configure Account"
- Type: **Realized FX Loss**
- Account: **8150 - Foreign Exchange Losses**
- Description: "Losses when paying USD suppliers"
- Click "Create"
- Result: ✅ Card turns green

#### 4. Configure Unrealized Gain
- Click "+ Configure Account"
- Type: **Unrealized FX Gain**
- Account: **7210 - Unrealized FX Gains**
- Description: "Month-end revaluation gains"
- Click "Create"
- Result: ✅ Card turns green

#### 5. Configure Unrealized Loss
- Click "+ Configure Account"
- Type: **Unrealized FX Loss**
- Account: **8210 - Unrealized FX Losses**
- Description: "Month-end revaluation losses"
- Click "Create"
- Result: ✅ Card turns green

### Final State
✅ All 4 cards green  
✅ Yellow warning disappeared  
✅ Ready to trade multi-currency!  

---

## Common Questions

### Q: What if I don't see any accounts in the dropdown?
**A:** You need to create GL accounts first:
1. Go to Chart of Accounts
2. Create accounts 7150, 8150, 7210, 8210
3. Return to FX Configuration

### Q: Can I use the same account for multiple types?
**A:** No! Each type needs its own unique account. Database enforces `OneToOneField`.

### Q: What happens if I delete a configuration?
**A:** Card turns gray, FX transactions using that type will fail until reconfigured.

### Q: Can I change the account after configuration?
**A:** Yes! Click [Edit], select new account, click "Update".

### Q: Do I need all 4 types configured?
**A:** For payments: Need Realized Gain + Realized Loss (minimum)  
**For full compliance:** Need all 4 types  

---

**Last Updated:** October 19, 2025  
**Page Location:** `/fx/config`  
**Access Level:** Administrator

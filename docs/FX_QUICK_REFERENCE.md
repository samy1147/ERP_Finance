# FX Testing - Quick Reference Card

**Fast track to seeing FX gains/losses in action**

---

## ⚡ Quick Start (15 minutes total)

### Step 1: Configure (5 min)
```
/fx/config

✓ Set base currency: AED
✓ Map account 7150 → Realized Gain
✓ Map account 8150 → Realized Loss
✓ Map account 7210 → Unrealized Gain
✓ Map account 8210 → Unrealized Loss
```

### Step 2: Load Rates (2 min)
```
/finance/exchange-rates

✓ EUR → AED = 4.00 (today)
✓ EUR → AED = 4.20 (tomorrow)
```

### Step 3: Create Invoice (3 min)
```
/ar/invoices/new

Customer: Test Customer
Amount: EUR 1,000
Date: Today

→ Post to GL (locks rate @ 4.00)
```

### Step 4: Create Payment (3 min)
```
/ar/payments/new

Customer: Same
Amount: EUR 1,000
Date: Tomorrow (uses rate 4.20)

→ Select invoice
→ Create Payment
→ Post to GL
```

### Step 5: See Results! (2 min)
```
/finance/journal-entries

Find payment entry:
DR  Bank             4,200
    CR  AR                   4,000
    CR  FX Gain (7150)         200 ← HERE!

/reports/trial-balance

7150 - FX Gains     Cr 200 ← PROFIT!
```

---

## 🎯 Expected Results

### Invoice Posted
```
EUR 1,000 @ 4.00 = AED 4,000
✓ AR debited: 4,000
✓ Revenue credited: 4,000
✓ Rate locked: 4.00
```

### Payment Posted (Different Rate)
```
EUR 1,000 @ 4.20 = AED 4,200
✓ Bank debited: 4,200
✓ AR credited: 4,000
✓ FX Gain credited: 200 ← AUTO!
```

### Reports Updated
```
Trial Balance:
  7150 - FX Gains         Cr 200

Profit & Loss:
  Income:
    Sales               4,000
    FX Gains              200 ← Profit!
    ─────────────────────────
    Total              4,200
```

---

## 📋 Rate Scenarios

### Scenario A: GAIN (Rate Increased)
```
Invoice: EUR 1,000 @ 4.00 = 4,000 AED
Payment: EUR 1,000 @ 4.20 = 4,200 AED
Result:  GAIN 200 AED → Account 7150 ✅
```

### Scenario B: LOSS (Rate Decreased)
```
Invoice: EUR 1,000 @ 4.00 = 4,000 AED
Payment: EUR 1,000 @ 3.90 = 3,900 AED
Result:  LOSS 100 AED → Account 8150 ❌
```

### Scenario C: NO FX (Same Rate)
```
Invoice: EUR 1,000 @ 4.00 = 4,000 AED
Payment: EUR 1,000 @ 4.00 = 4,000 AED
Result:  NO FX → 2-line entry only
```

---

## 🔢 FX Calculation Formula

```
Booked Amount = Invoice Amount × Invoice Rate
Received Amount = Invoice Amount × Payment Rate
FX Gain/Loss = Received Amount - Booked Amount

Example:
Booked:   1,000 × 4.00 = 4,000
Received: 1,000 × 4.20 = 4,200
FX Gain:  4,200 - 4,000 = 200 ✅
```

---

## ✅ Verification Points

After posting payment, check:

```
□ Journal entry has 3 lines (not 2)
□ FX line uses account 7150 or 8150
□ FX amount = (new_rate - old_rate) × amount
□ Entry balances (DR total = CR total)
□ Trial balance shows FX account balance
□ P&L shows FX in income/expense
□ Payment detail shows FX breakdown
```

---

## 🚨 Common Issues

### "FX accounts not configured"
→ Go to /fx/config, map all 4 types

### "No exchange rate found"
→ Go to /finance/exchange-rates, add rates

### "No FX line in entry"
→ Normal if rate unchanged (same rate = no FX)

### "Wrong FX amount"
→ Check rate date matches payment date

---

## 🎓 Understanding Results

### What You See:
```
Account 7150: Credit 200 AED
```

### What It Means:
- Customer paid EUR 1,000 (as agreed)
- You received AED 4,200 (more than expected)
- Extra 200 AED is profit from currency movement
- Not from sales, but from exchange rate change

### Business Impact:
- ✅ Accurate profit tracking
- ✅ Currency risk visibility
- ✅ Better decision making
- ✅ Compliance with accounting standards

---

## 📊 Test Data Template

### Minimal Test Set
```
CURRENCIES:
✓ AED (base)
✓ EUR
✓ USD

EXCHANGE RATES:
✓ EUR → AED = 4.00 (today)
✓ EUR → AED = 4.20 (tomorrow)
✓ USD → AED = 3.67

CUSTOMERS:
✓ Test Customer (any)

BANK ACCOUNTS:
✓ Main Bank (any)

GL ACCOUNTS:
✓ 1000 - Bank
✓ 1200 - AR
✓ 4000 - Revenue
✓ 7150 - FX Gains
✓ 8150 - FX Losses
```

---

## 🎯 Success Criteria

You've successfully configured FX when:

```
✅ All 4 FX cards are green
✅ Invoice posts with exchange_rate field
✅ Payment posts with FX journal line
✅ Trial Balance shows FX account
✅ P&L shows FX gains/losses
✅ No errors during posting
```

---

## 🚀 Next Actions

### For Testing:
1. Try larger amounts (EUR 10,000)
2. Try different currencies (USD, GBP)
3. Try FX loss scenario (rate down)
4. Try multiple invoices per payment

### For Production:
1. Train team on FX workflows
2. Monitor FX exposure weekly
3. Review FX reports monthly
4. Consider hedging strategies

---

## 📞 Quick Help

### Where to Find Things:

| Feature | Location |
|---------|----------|
| FX Config | /fx/config |
| Exchange Rates | /finance/exchange-rates |
| AR Invoices | /ar/invoices |
| AR Payments | /ar/payments |
| Journal Entries | /finance/journal-entries |
| Trial Balance | /reports/trial-balance |
| Profit & Loss | /reports/profit-loss |

---

**Print this card and keep it handy during testing! 📋**

---

**Last Updated:** October 19, 2025  
**Version:** 1.0  
**Status:** Ready for Testing

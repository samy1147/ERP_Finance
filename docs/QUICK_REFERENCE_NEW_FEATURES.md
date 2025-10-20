# Quick Reference: New Frontend Features

## 🔗 New Page URLs

| Feature | URL | Description |
|---------|-----|-------------|
| Currencies | `/currencies` | Manage all currencies (USD, EUR, AED, etc.) |
| Exchange Rates | `/fx/rates` | Manage FX rates + Currency Converter |
| Tax Rates | `/tax-rates` | Manage VAT/GST rates by country |

## 📡 New API Methods Added

```typescript
// In frontend/src/services/api.ts

// Tax Rates
taxRatesAPI.seedPresets() // Seed default VAT rates

// Exchange Rates
exchangeRatesAPI.list(filters)
exchangeRatesAPI.create(data)
exchangeRatesAPI.update(id, data)
exchangeRatesAPI.delete(id)
exchangeRatesAPI.convert({ amount, from_currency_code, to_currency_code })

// FX Configuration
fxConfigAPI.baseCurrency()
fxConfigAPI.gainLossAccounts.list()
fxConfigAPI.gainLossAccounts.create(data)

// Corporate Tax
corporateTaxAPI.accrual(data)
corporateTaxAPI.breakdown(params)
corporateTaxAPI.filing.get(id)
corporateTaxAPI.filing.file(id)
corporateTaxAPI.filing.reverse(id)

// Journal Enhancements
journalEntriesAPI.post(id) // Post to GL
journalEntriesAPI.export(format) // 'csv' or 'xlsx'
```

## 🎨 Component Usage

### Currency Converter (Built-in to FX Rates page)
```typescript
// Located in /fx/rates page
// Shows inline currency converter with:
// - Amount input
// - From/To currency dropdowns
// - Rate date selector
// - Real-time conversion result
```

## 🗂️ TypeScript Interfaces Added

```typescript
// In frontend/src/types/index.ts

interface Currency {
  id: number;
  code: string;
  name: string;
  symbol: string;
  is_base: boolean; // NEW
}

interface ExchangeRate {
  id: number;
  from_currency: number;
  to_currency: number;
  rate_date: string;
  rate: string;
  rate_type: 'SPOT' | 'AVERAGE' | 'FIXED' | 'CLOSING';
  source?: string;
  is_active: boolean;
}

interface TaxRate {
  id: number;
  name: string;
  rate: number;
  country: string;
  category: 'STANDARD' | 'ZERO' | 'EXEMPT' | 'RC';
  code?: string;
  effective_from?: string;
  effective_to?: string; // NEW
  is_active: boolean;
}

interface FXGainLossAccount {
  id: number;
  account: number;
  gain_loss_type: 'REALIZED_GAIN' | 'REALIZED_LOSS' | 'UNREALIZED_GAIN' | 'UNREALIZED_LOSS';
}

interface CorporateTaxFiling {
  id: number;
  filing_period_start: string;
  filing_period_end: string;
  tax_rate: string;
  taxable_income: string;
  tax_amount: string;
  status: 'DRAFT' | 'ACCRUED' | 'FILED' | 'PAID' | 'REVERSED';
}
```

## 🎯 Common Workflows

### Setting Up Multi-Currency
1. Go to `/currencies`
2. Add currencies: USD, EUR, AED, etc.
3. Mark your base currency (e.g., AED)
4. Go to `/fx/rates`
5. Add exchange rates for each currency pair
6. Now invoices can be created in any currency

### Setting Up Tax Rates
1. Go to `/tax-rates`
2. Click "🌱 Seed Default Rates" (adds common rates for UAE, SA, EG, IN)
3. Or manually add custom rates
4. Rates auto-appear in invoice forms filtered by customer country

### Using Currency Converter
1. Go to `/fx/rates`
2. Click "💱 Currency Converter"
3. Enter amount, select currencies, choose date
4. See instant conversion result

### Exporting Journals
1. Go to `/journals`
2. Click "Export CSV" or "Export Excel"
3. File downloads automatically

### Posting Journals
1. Go to `/journals`
2. Find draft journal (gray "Draft" badge)
3. Click green checkmark icon
4. Journal posts to GL (becomes "Posted")

## 🐛 Troubleshooting

### "Failed to load currencies"
- Check backend is running on `http://localhost:8000`
- Verify `/api/currencies/` endpoint is accessible

### "Failed to save currency: unique constraint"
- Currency code already exists (codes must be unique)
- Try a different 3-letter code

### "Failed to delete currency: in use"
- Currency is used in invoices/journals
- Cannot delete currencies with transactions

### Exchange rate converter returns error
- Make sure exchange rate exists for the selected date
- Check from/to currencies are different
- Verify rate_date format is YYYY-MM-DD

### Tax rates not showing in invoice forms
- Verify tax rates exist for the customer's country
- Check tax rate is_active = true
- Ensure effective_from date is in the past

## 🔐 Permissions

All new features require:
- Backend API authentication (CSRF token)
- User must be logged in
- Some operations may require admin/staff permissions

## 📦 Dependencies

No new dependencies added! Uses existing:
- React
- Next.js
- Tailwind CSS
- Axios
- date-fns
- react-hot-toast
- lucide-react

## 🚀 Performance Notes

- All list views use pagination-ready endpoints
- Filters are applied server-side (no client-side filtering of large datasets)
- Export operations stream to file (no memory overflow)
- Forms use optimistic UI updates where appropriate

## 📱 Mobile Support

All new pages are:
- ✅ Responsive (mobile-friendly)
- ✅ Touch-optimized buttons
- ✅ Horizontal scroll on tables for mobile
- ✅ Stacked form layouts on small screens

---

**Questions?** Check the full documentation: `docs/FRONTEND_IMPLEMENTATION_COMPLETE.md`

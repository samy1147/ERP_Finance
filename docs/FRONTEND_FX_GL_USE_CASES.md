# Frontend FX GL Use Cases - Complete Guide

**Real-world examples with TypeScript/React code for displaying and handling FX transactions**

---

## 📚 Table of Contents
1. [Use Case 1: Invoice List with FX Indicators](#use-case-1-invoice-list-with-fx-indicators)
2. [Use Case 2: Payment Creation with FX Preview](#use-case-2-payment-creation-with-fx-preview)
3. [Use Case 3: FX Gain/Loss Report Dashboard](#use-case-3-fx-gainloss-report-dashboard)
4. [Use Case 4: Payment Detail with FX Breakdown](#use-case-4-payment-detail-with-fx-breakdown)
5. [Use Case 5: Multi-Currency Invoice Warnings](#use-case-5-multi-currency-invoice-warnings)
6. [Use Case 6: FX Rate Comparison Widget](#use-case-6-fx-rate-comparison-widget)
7. [Reusable Components](#reusable-components)

---

## Use Case 1: Invoice List with FX Indicators

### Business Scenario
Show invoices with visual indicators when exchange rates have changed since posting, alerting users to potential FX gain/loss on payment.

### Visual Design
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AR Invoices                                                     [New Invoice]│
├─────────────────────────────────────────────────────────────────────────────┤
│  #      │ Customer  │ Date       │ Amount        │ Outstanding  │ FX Status │
├─────────┼───────────┼────────────┼───────────────┼──────────────┼───────────┤
│  INV-001│ ABC Corp  │ 2025-01-01 │ EUR 10,000.00 │ EUR 10,000   │ ⬆️ +5.2%  │
│         │           │            │ AED 40,000.00 │              │ Potential │
│         │           │            │ @ 4.00        │              │ Gain      │
├─────────┼───────────┼────────────┼───────────────┼──────────────┼───────────┤
│  INV-002│ XYZ Ltd   │ 2025-01-15 │ USD 5,000.00  │ USD 5,000    │ ⬇️ -2.1%  │
│         │           │            │ AED 18,350.00 │              │ Potential │
│         │           │            │ @ 3.67        │              │ Loss      │
├─────────┼───────────┼────────────┼───────────────┼──────────────┼───────────┤
│  INV-003│ DEF Inc   │ 2025-02-01 │ AED 25,000.00 │ AED 25,000   │ ─ No FX   │
└─────────┴───────────┴────────────┴───────────────┴──────────────┴───────────┘
```

### TypeScript Interface
```typescript
// Add to frontend/src/types/index.ts
export interface ARInvoiceWithFX extends ARInvoice {
  // Original invoice data
  exchange_rate?: string;           // Rate at posting
  currency_code?: string;           // Invoice currency
  base_currency_total?: string;     // Amount in base currency
  
  // FX tracking (calculated on frontend)
  current_exchange_rate?: string;   // Today's rate
  fx_rate_change_percent?: number;  // % change since posting
  potential_fx_gain_loss?: number;  // Estimated gain/loss in base currency
  fx_impact_type?: 'gain' | 'loss' | 'neutral';
}
```

### Component Code
```typescript
// frontend/src/app/ar/invoices/page.tsx

'use client';

import React, { useEffect, useState } from 'react';
import { arInvoicesAPI, exchangeRatesAPI } from '../../../services/api';
import { ARInvoiceWithFX, ExchangeRate } from '../../../types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function ARInvoicesWithFXPage() {
  const [invoices, setInvoices] = useState<ARInvoiceWithFX[]>([]);
  const [exchangeRates, setExchangeRates] = useState<ExchangeRate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // Fetch invoices and current exchange rates
      const [invoicesRes, ratesRes] = await Promise.all([
        arInvoicesAPI.list(),
        exchangeRatesAPI.list({ 
          date_from: new Date().toISOString().split('T')[0],
          date_to: new Date().toISOString().split('T')[0]
        })
      ]);

      // Calculate FX impact for each invoice
      const invoicesWithFX = invoicesRes.data.map((invoice: ARInvoiceWithFX) => {
        if (!invoice.exchange_rate || !invoice.outstanding || invoice.status === 'PAID') {
          return { ...invoice, fx_impact_type: 'neutral' as const };
        }

        // Find current rate for this currency
        const currentRate = ratesRes.data.find((r: ExchangeRate) => 
          r.from_currency === invoice.currency && 
          r.to_currency === 1 // Assuming base currency ID is 1
        );

        if (!currentRate) {
          return { ...invoice, fx_impact_type: 'neutral' as const };
        }

        const invoiceRate = parseFloat(invoice.exchange_rate);
        const todayRate = parseFloat(currentRate.rate);
        const outstanding = parseFloat(invoice.outstanding);

        // Calculate % change
        const rateChangePercent = ((todayRate - invoiceRate) / invoiceRate) * 100;

        // Calculate potential FX gain/loss
        const bookedBase = outstanding * invoiceRate;
        const currentBase = outstanding * todayRate;
        const potentialFX = currentBase - bookedBase;

        return {
          ...invoice,
          current_exchange_rate: currentRate.rate,
          fx_rate_change_percent: rateChangePercent,
          potential_fx_gain_loss: potentialFX,
          fx_impact_type: potentialFX > 0 ? 'gain' : potentialFX < 0 ? 'loss' : 'neutral'
        };
      });

      setInvoices(invoicesWithFX);
      setExchangeRates(ratesRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number, code: string) => {
    return `${code} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const FXStatusBadge = ({ invoice }: { invoice: ARInvoiceWithFX }) => {
    if (invoice.fx_impact_type === 'neutral' || !invoice.fx_rate_change_percent) {
      return (
        <div className="flex items-center gap-1 text-gray-500">
          <Minus className="h-4 w-4" />
          <span className="text-sm">No FX</span>
        </div>
      );
    }

    if (invoice.fx_impact_type === 'gain') {
      return (
        <div className="flex flex-col items-start">
          <div className="flex items-center gap-1 text-green-600">
            <TrendingUp className="h-4 w-4" />
            <span className="text-sm font-semibold">
              +{invoice.fx_rate_change_percent.toFixed(1)}%
            </span>
          </div>
          <span className="text-xs text-gray-600">
            Potential Gain: {formatCurrency(invoice.potential_fx_gain_loss!, 'AED')}
          </span>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-start">
        <div className="flex items-center gap-1 text-red-600">
          <TrendingDown className="h-4 w-4" />
          <span className="text-sm font-semibold">
            {invoice.fx_rate_change_percent.toFixed(1)}%
          </span>
        </div>
        <span className="text-xs text-gray-600">
          Potential Loss: {formatCurrency(Math.abs(invoice.potential_fx_gain_loss!), 'AED')}
        </span>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">AR Invoices - FX Tracking</h1>
      
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Invoice #
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Customer
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Amount
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Outstanding
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                FX Status
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {invoices.map((invoice) => (
              <tr key={invoice.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {invoice.number}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {invoice.customer_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(invoice.date).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {formatCurrency(parseFloat(invoice.total_amount), invoice.currency_code || 'AED')}
                  </div>
                  {invoice.exchange_rate && (
                    <div className="text-xs text-gray-500">
                      {formatCurrency(parseFloat(invoice.base_currency_total || '0'), 'AED')} @ {invoice.exchange_rate}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatCurrency(parseFloat(invoice.outstanding || '0'), invoice.currency_code || 'AED')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <FXStatusBadge invoice={invoice} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## Use Case 2: Payment Creation with FX Preview

### Business Scenario
When creating a payment, show user the potential FX gain/loss BEFORE they save, with live calculation as they enter amounts.

### Visual Design
```
┌─────────────────────────────────────────────────────────────────────┐
│  Create AR Payment                                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Customer: ABC Corp                   Date: 2025-02-01              │
│  Payment Currency: AED                Amount: 42,000.00             │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 💰 FX Impact Preview                                         │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │ Invoice #INV-001                                             │   │
│  │ • Invoice Amount:  EUR 10,000 @ 4.00 = AED 40,000 (booked) │   │
│  │ • Payment Amount:  AED 42,000                                │   │
│  │ • Current Rate:    4.20 (1 EUR = 4.20 AED)                  │   │
│  │ • Rate Change:     +5.0% ⬆️                                  │   │
│  │                                                               │   │
│  │ 🎯 Expected FX GAIN: AED 2,000.00                            │   │
│  │                                                               │   │
│  │ Journal Entry Preview:                                        │   │
│  │ DR  Bank Account           42,000.00                         │   │
│  │     CR  Accounts Receivable        40,000.00                 │   │
│  │     CR  FX Gain Income               2,000.00 ← Profit!      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  [Cancel]                                           [Create Payment] │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Code
```typescript
// frontend/src/components/FXPreviewCard.tsx

import React from 'react';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

interface FXPreviewProps {
  invoiceAmount: number;
  invoiceCurrency: string;
  invoiceRate: number;
  paymentAmount: number;
  paymentCurrency: string;
  currentRate: number;
  baseCurrency: string;
}

export const FXPreviewCard: React.FC<FXPreviewProps> = ({
  invoiceAmount,
  invoiceCurrency,
  invoiceRate,
  paymentAmount,
  paymentCurrency,
  currentRate,
  baseCurrency
}) => {
  // Calculate FX impact
  const bookedBase = invoiceAmount * invoiceRate;
  const paymentBase = paymentAmount;
  const fxGainLoss = paymentBase - bookedBase;
  const rateChange = ((currentRate - invoiceRate) / invoiceRate) * 100;
  
  const isGain = fxGainLoss > 0;
  const isLoss = fxGainLoss < 0;

  return (
    <div className="border-2 border-blue-200 rounded-lg p-6 bg-blue-50">
      <div className="flex items-center gap-2 mb-4">
        <DollarSign className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">FX Impact Preview</h3>
      </div>

      <div className="space-y-3 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Invoice Amount:</span>
          <span className="font-medium">
            {invoiceCurrency} {invoiceAmount.toFixed(2)} @ {invoiceRate.toFixed(6)} = {baseCurrency} {bookedBase.toFixed(2)}
          </span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Payment Amount:</span>
          <span className="font-medium">
            {paymentCurrency} {paymentAmount.toFixed(2)}
          </span>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Current Rate:</span>
          <span className="font-medium flex items-center gap-2">
            {currentRate.toFixed(6)}
            {rateChange !== 0 && (
              <span className={`text-xs ${isGain ? 'text-green-600' : 'text-red-600'}`}>
                {isGain ? <TrendingUp className="h-3 w-3 inline" /> : <TrendingDown className="h-3 w-3 inline" />}
                {rateChange > 0 ? '+' : ''}{rateChange.toFixed(1)}%
              </span>
            )}
          </span>
        </div>
      </div>

      <div className={`border-t-2 pt-4 ${isGain ? 'border-green-200' : isLoss ? 'border-red-200' : 'border-gray-200'}`}>
        {isGain && (
          <div className="bg-green-100 border border-green-300 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-5 w-5 text-green-700" />
              <span className="font-semibold text-green-800">Expected FX GAIN</span>
            </div>
            <div className="text-2xl font-bold text-green-700">
              {baseCurrency} {fxGainLoss.toFixed(2)}
            </div>
          </div>
        )}

        {isLoss && (
          <div className="bg-red-100 border border-red-300 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="h-5 w-5 text-red-700" />
              <span className="font-semibold text-red-800">Expected FX LOSS</span>
            </div>
            <div className="text-2xl font-bold text-red-700">
              {baseCurrency} {Math.abs(fxGainLoss).toFixed(2)}
            </div>
          </div>
        )}

        {!isGain && !isLoss && (
          <div className="bg-gray-100 border border-gray-300 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-700">No FX Impact</span>
            </div>
            <div className="text-sm text-gray-600 mt-1">
              Same exchange rate as invoice posting
            </div>
          </div>
        )}
      </div>

      {/* Journal Entry Preview */}
      {fxGainLoss !== 0 && (
        <div className="mt-4 bg-white rounded-lg p-4 border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Journal Entry Preview:</h4>
          <div className="space-y-1 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-gray-600">DR Bank Account</span>
              <span className="font-medium">{paymentBase.toFixed(2)}</span>
            </div>
            <div className="flex justify-between pl-4">
              <span className="text-gray-600">CR Accounts Receivable</span>
              <span className="font-medium">{bookedBase.toFixed(2)}</span>
            </div>
            {isGain && (
              <div className="flex justify-between pl-4 text-green-700">
                <span>CR FX Gain Income</span>
                <span className="font-medium">{fxGainLoss.toFixed(2)}</span>
              </div>
            )}
            {isLoss && (
              <div className="flex justify-between text-red-700">
                <span>DR FX Loss Expense</span>
                <span className="font-medium">{Math.abs(fxGainLoss).toFixed(2)}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
```

### Usage in Payment Form
```typescript
// frontend/src/app/ar/payments/new/page.tsx

export default function NewARPaymentPage() {
  // ... existing state ...
  const [showFXPreview, setShowFXPreview] = useState(false);
  const [fxPreviewData, setFXPreviewData] = useState<FXPreviewProps | null>(null);

  // Calculate FX preview when invoice is selected
  useEffect(() => {
    const selectedInv = invoices.find(inv => inv.selected);
    if (selectedInv && selectedInv.currencyId !== parseInt(formData.currency)) {
      const invoiceRate = parseFloat(selectedInv.exchange_rate || '1');
      const currentRate = getExchangeRate(selectedInv.currencyId!, parseInt(formData.currency));
      
      if (currentRate) {
        setFXPreviewData({
          invoiceAmount: parseFloat(selectedInv.outstanding),
          invoiceCurrency: selectedInv.currency || 'EUR',
          invoiceRate: invoiceRate,
          paymentAmount: parseFloat(formData.total_amount || '0'),
          paymentCurrency: currencies.find(c => c.id === parseInt(formData.currency))?.code || 'AED',
          currentRate: currentRate,
          baseCurrency: 'AED'
        });
        setShowFXPreview(true);
      }
    } else {
      setShowFXPreview(false);
    }
  }, [invoices, formData.currency, formData.total_amount]);

  return (
    <div>
      {/* Payment form fields */}
      
      {/* FX Preview */}
      {showFXPreview && fxPreviewData && (
        <div className="mt-6">
          <FXPreviewCard {...fxPreviewData} />
        </div>
      )}
      
      {/* Submit button */}
    </div>
  );
}
```

---

## Use Case 3: FX Gain/Loss Report Dashboard

### Business Scenario
Dashboard showing realized FX gains and losses from all payments in a period, with charts and breakdown.

### Visual Design
```
┌─────────────────────────────────────────────────────────────────────┐
│  FX Gain/Loss Report                          Period: Jan 2025      │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │ Total FX Gains   │  │ Total FX Losses  │  │ Net FX Impact    │ │
│  │ AED 15,420.00    │  │ AED 3,250.00     │  │ AED 12,170.00 ✅ │ │
│  │ ⬆️ +12.5%        │  │ ⬇️ -5.2%         │  │ Profit           │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                      │
│  📊 FX Gain/Loss by Currency                                        │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │      EUR ████████████████████ AED 8,500 Gain                │  │
│  │      USD ████████████ AED 5,200 Gain                         │  │
│  │      GBP ██████ AED 1,720 Gain                               │  │
│  │      JPY ███ AED -3,250 Loss                                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  📋 Recent FX Transactions                                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Date    │ Ref      │ Invoice  │ Currency │ Rate   │ FX      │  │
│  ├─────────┼──────────┼──────────┼──────────┼────────┼─────────┤  │
│  │ Jan 15  │ PAY-001  │ INV-001  │ EUR→AED  │ 4.00→  │ +2,000  │  │
│  │         │          │          │          │ 4.20   │ Gain    │  │
│  │ Jan 18  │ PAY-002  │ INV-005  │ USD→AED  │ 3.67→  │ -450    │  │
│  │         │          │          │          │ 3.65   │ Loss    │  │
│  └─────────┴──────────┴──────────┴──────────┴────────┴─────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Code
```typescript
// frontend/src/app/reports/fx-gainloss/page.tsx

'use client';

import React, { useState, useEffect } from 'react';
import { arPaymentsAPI, apPaymentsAPI } from '../../../services/api';
import { ARPayment, APPayment } from '../../../types';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

interface FXTransaction {
  date: string;
  reference: string;
  invoiceNumber: string;
  currency: string;
  invoiceRate: number;
  paymentRate: number;
  fxAmount: number;
  type: 'AR' | 'AP';
}

export default function FXGainLossReport() {
  const [fxTransactions, setFXTransactions] = useState<FXTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    to: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchFXData();
  }, [dateRange]);

  const fetchFXData = async () => {
    try {
      const [arPayments, apPayments] = await Promise.all([
        arPaymentsAPI.list(),
        apPaymentsAPI.list()
      ]);

      const transactions: FXTransaction[] = [];

      // Process AR payments
      arPayments.data.forEach((payment: ARPayment) => {
        if (payment.exchange_rate && payment.invoice_currency) {
          payment.allocations?.forEach((alloc: any) => {
            const invoiceRate = parseFloat(alloc.current_exchange_rate || '1');
            const paymentRate = parseFloat(payment.exchange_rate!);
            const amount = parseFloat(alloc.amount);
            
            const bookedBase = amount * invoiceRate;
            const paidBase = amount * paymentRate;
            const fxAmount = paidBase - bookedBase;

            if (Math.abs(fxAmount) > 0.01) {
              transactions.push({
                date: payment.date,
                reference: payment.reference,
                invoiceNumber: alloc.invoice_number || '',
                currency: `${payment.invoice_currency_code}→${payment.payment_currency_code}`,
                invoiceRate: invoiceRate,
                paymentRate: paymentRate,
                fxAmount: fxAmount,
                type: 'AR'
              });
            }
          });
        }
      });

      // Process AP payments similarly...

      setFXTransactions(transactions.sort((a, b) => 
        new Date(b.date).getTime() - new Date(a.date).getTime()
      ));
    } catch (error) {
      console.error('Failed to fetch FX data:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalGains = fxTransactions
    .filter(t => t.fxAmount > 0)
    .reduce((sum, t) => sum + t.fxAmount, 0);

  const totalLosses = fxTransactions
    .filter(t => t.fxAmount < 0)
    .reduce((sum, t) => sum + Math.abs(t.fxAmount), 0);

  const netFX = totalGains - totalLosses;

  const StatCard = ({ title, amount, trend, color }: any) => (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>
      <div className={`text-3xl font-bold ${color}`}>
        AED {amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
      </div>
      {trend && (
        <div className="flex items-center gap-1 mt-2 text-sm">
          {trend > 0 ? (
            <TrendingUp className="h-4 w-4 text-green-600" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-600" />
          )}
          <span className={trend > 0 ? 'text-green-600' : 'text-red-600'}>
            {Math.abs(trend).toFixed(1)}%
          </span>
        </div>
      )}
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">FX Gain/Loss Report</h1>
        <p className="text-gray-600 mt-2">Track foreign exchange impact on your business</p>
      </div>

      {/* Date Range Selector */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">From:</label>
          <input
            type="date"
            value={dateRange.from}
            onChange={(e) => setDateRange({ ...dateRange, from: e.target.value })}
            className="border rounded px-3 py-2"
          />
          <label className="text-sm font-medium text-gray-700">To:</label>
          <input
            type="date"
            value={dateRange.to}
            onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })}
            className="border rounded px-3 py-2"
          />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-6 mb-6">
        <StatCard
          title="Total FX Gains"
          amount={totalGains}
          trend={12.5}
          color="text-green-600"
        />
        <StatCard
          title="Total FX Losses"
          amount={totalLosses}
          trend={-5.2}
          color="text-red-600"
        />
        <StatCard
          title="Net FX Impact"
          amount={netFX}
          color={netFX > 0 ? 'text-green-600' : 'text-red-600'}
        />
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">FX Transactions</h2>
        </div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reference</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Currency</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rates</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">FX Impact</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {fxTransactions.map((tx, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(tx.date).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {tx.reference}
                  <span className="ml-2 text-xs text-gray-500">({tx.type})</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {tx.invoiceNumber}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {tx.currency}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  <div>{tx.invoiceRate.toFixed(6)} →</div>
                  <div>{tx.paymentRate.toFixed(6)}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className={`flex items-center gap-2 ${tx.fxAmount > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {tx.fxAmount > 0 ? (
                      <TrendingUp className="h-4 w-4" />
                    ) : (
                      <TrendingDown className="h-4 w-4" />
                    )}
                    <span className="font-semibold">
                      {tx.fxAmount > 0 ? '+' : ''}{tx.fxAmount.toFixed(2)}
                    </span>
                    <span className="text-xs">
                      {tx.fxAmount > 0 ? 'Gain' : 'Loss'}
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## Use Case 4: Payment Detail with FX Breakdown

### Business Scenario
When viewing a posted payment, show detailed breakdown of the FX calculation and the journal entry that was created.

### Component Code
```typescript
// frontend/src/app/ar/payments/[id]/page.tsx

export default function ARPaymentDetail({ params }: { params: { id: string } }) {
  const [payment, setPayment] = useState<ARPayment | null>(null);
  const [journalEntry, setJournalEntry] = useState<any>(null);

  const FXBreakdown = () => {
    if (!payment || !payment.exchange_rate || !payment.invoice_currency) {
      return null;
    }

    return (
      <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 mt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-blue-600" />
          FX Transaction Breakdown
        </h3>

        <div className="grid grid-cols-2 gap-6">
          {/* Left: Calculation */}
          <div>
            <h4 className="font-medium text-gray-700 mb-3">Calculation:</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Invoice Currency:</span>
                <span className="font-mono">{payment.invoice_currency_code}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Payment Currency:</span>
                <span className="font-mono">{payment.payment_currency_code}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Invoice Rate:</span>
                <span className="font-mono">{payment.allocations?.[0]?.current_exchange_rate}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Payment Rate:</span>
                <span className="font-mono">{payment.exchange_rate}</span>
              </div>
              
              <div className="border-t pt-2 mt-2">
                <div className="flex justify-between font-medium">
                  <span>Booked Amount (Base):</span>
                  <span className="font-mono">
                    AED {(parseFloat(payment.total_amount) * parseFloat(payment.allocations?.[0]?.current_exchange_rate || '1')).toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between font-medium">
                  <span>Received Amount (Base):</span>
                  <span className="font-mono">
                    AED {(parseFloat(payment.total_amount) * parseFloat(payment.exchange_rate)).toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="bg-green-100 border border-green-300 rounded p-2 mt-3">
                <div className="flex justify-between font-bold text-green-800">
                  <span>FX Gain:</span>
                  <span className="font-mono">AED 2,000.00</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Journal Entry */}
          <div>
            <h4 className="font-medium text-gray-700 mb-3">Journal Entry Posted:</h4>
            <div className="bg-white border rounded p-3">
              <div className="space-y-1 text-sm font-mono">
                <div className="flex justify-between border-b pb-1">
                  <span className="font-semibold">Account</span>
                  <span className="font-semibold">Amount</span>
                </div>
                <div className="flex justify-between text-gray-700">
                  <span>DR Bank Account (1000)</span>
                  <span>42,000.00</span>
                </div>
                <div className="flex justify-between text-gray-700 pl-4">
                  <span>CR AR (1200)</span>
                  <span>40,000.00</span>
                </div>
                <div className="flex justify-between text-green-700 pl-4">
                  <span>CR FX Gain (7150)</span>
                  <span>2,000.00</span>
                </div>
                <div className="border-t pt-1 mt-1 flex justify-between font-semibold">
                  <span>Total:</span>
                  <span>42,000.00</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Payment Details</h1>
      
      {/* Payment info */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        {/* ... payment fields ... */}
      </div>

      {/* FX Breakdown */}
      <FXBreakdown />
    </div>
  );
}
```

---

## Use Case 5: Multi-Currency Invoice Warnings

### Business Scenario
When creating an invoice in a foreign currency, warn user about potential FX exposure and suggest best practices.

### Component Code
```typescript
// frontend/src/components/CurrencyWarningBanner.tsx

export const CurrencyWarningBanner: React.FC<{ selectedCurrency: Currency; baseCurrency: Currency }> = ({
  selectedCurrency,
  baseCurrency
}) => {
  if (selectedCurrency.id === baseCurrency.id) {
    return null;
  }

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-yellow-800">
            Foreign Currency Invoice - FX Exposure Warning
          </h3>
          <div className="mt-2 text-sm text-yellow-700">
            <p className="mb-2">
              You're creating an invoice in <strong>{selectedCurrency.code}</strong> while your base currency is <strong>{baseCurrency.code}</strong>.
            </p>
            <p className="font-medium">This means:</p>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>Exchange rate will be locked when invoice is posted</li>
              <li>FX gain/loss may occur when payment is received</li>
              <li>Currency fluctuations could affect your actual revenue</li>
            </ul>
            <p className="mt-3 text-xs">
              💡 <strong>Tip:</strong> Consider adding a currency clause to your terms, or pricing in {baseCurrency.code} to avoid FX risk.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
```

---

## Use Case 6: FX Rate Comparison Widget

### Business Scenario
Show users how current exchange rates compare to when invoices were posted, helping them decide optimal payment timing.

### Component Code
```typescript
// frontend/src/components/FXRateComparisonWidget.tsx

export const FXRateComparisonWidget: React.FC = () => {
  const [rates, setRates] = useState<any[]>([]);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Exchange Rate Trends</h3>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
          <div>
            <div className="font-medium">EUR → AED</div>
            <div className="text-sm text-gray-600">Current: 4.20</div>
          </div>
          <div className="text-right">
            <div className="text-green-600 font-medium">+5.0% ⬆️</div>
            <div className="text-xs text-gray-500">vs 30-day avg</div>
          </div>
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
          <div>
            <div className="font-medium">USD → AED</div>
            <div className="text-sm text-gray-600">Current: 3.67</div>
          </div>
          <div className="text-right">
            <div className="text-red-600 font-medium">-2.1% ⬇️</div>
            <div className="text-xs text-gray-500">vs 30-day avg</div>
          </div>
        </div>
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded">
        <p className="text-sm text-blue-800">
          💡 <strong>Insight:</strong> Good time to collect EUR payments (favorable rate). Consider waiting on USD payments if possible.
        </p>
      </div>
    </div>
  );
};
```

---

## Reusable Components

### FX Badge Component
```typescript
// frontend/src/components/FXBadge.tsx

export const FXBadge: React.FC<{ type: 'gain' | 'loss' | 'neutral' }> = ({ type }) => {
  const configs = {
    gain: { text: 'FX Gain', color: 'bg-green-100 text-green-800', icon: '↑' },
    loss: { text: 'FX Loss', color: 'bg-red-100 text-red-800', icon: '↓' },
    neutral: { text: 'No FX', color: 'bg-gray-100 text-gray-800', icon: '—' }
  };

  const config = configs[type];

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${config.color}`}>
      <span>{config.icon}</span>
      {config.text}
    </span>
  );
};
```

### Currency Converter Tooltip
```typescript
// frontend/src/components/CurrencyTooltip.tsx

export const CurrencyTooltip: React.FC<{ 
  amount: number; 
  fromCurrency: string; 
  toCurrency: string; 
  rate: number 
}> = ({ amount, fromCurrency, toCurrency, rate }) => {
  const [show, setShow] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        className="text-blue-600 hover:text-blue-800 underline cursor-help"
      >
        {fromCurrency} {amount.toFixed(2)}
      </button>
      
      {show && (
        <div className="absolute z-10 px-3 py-2 text-sm bg-gray-900 text-white rounded shadow-lg -top-12 left-0 whitespace-nowrap">
          {fromCurrency} {amount.toFixed(2)} × {rate.toFixed(6)} = {toCurrency} {(amount * rate).toFixed(2)}
        </div>
      )}
    </div>
  );
};
```

---

## Summary

### ✅ Frontend Use Cases Covered:
1. **Invoice List** - Show FX exposure on open invoices
2. **Payment Creation** - Preview FX impact before saving
3. **FX Report** - Dashboard with gains/losses analysis
4. **Payment Detail** - Breakdown of FX calculation and journal entry
5. **Invoice Warnings** - Alert users about FX risk
6. **Rate Comparison** - Help optimize payment timing

### 🎯 Key UI Patterns:
- Color coding (green = gain, red = loss)
- Real-time calculations
- Preview before commit
- Visual indicators (arrows, badges)
- Tooltip explanations
- Journal entry previews

### 💡 Best Practices:
- Calculate FX on frontend for immediate feedback
- Show both original and converted amounts
- Display exchange rates explicitly
- Warn users about FX exposure
- Provide journal entry previews
- Use consistent color scheme

---

**Last Updated:** October 19, 2025
**Status:** ✅ Ready for Implementation

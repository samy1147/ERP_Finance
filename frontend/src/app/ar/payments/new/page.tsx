'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { arPaymentsAPI, customersAPI, outstandingInvoicesAPI, currenciesAPI, bankAccountsAPI, exchangeRatesAPI, segmentsAPI } from '../../../../services/api';
import { Customer, Currency, BankAccount, ExchangeRate, Account, GLDistributionLine } from '../../../../types';
import toast from 'react-hot-toast';
import GLDistributionLines from '../../../../components/GLDistributionLines';

interface InvoiceAllocation {
  invoice: number;
  invoiceNumber: string;
  invoiceTotal: string;
  outstanding: string;
  amount: string;
  selected: boolean;
  currency?: string; // Invoice currency code
  currencyId?: number; // Invoice currency ID
}

export default function NewARPaymentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [invoices, setInvoices] = useState<InvoiceAllocation[]>([]);
  const [loadingInvoices, setLoadingInvoices] = useState(false);
  const [exchangeRates, setExchangeRates] = useState<ExchangeRate[]>([]);
  const [glLines, setGlLines] = useState<Partial<GLDistributionLine>[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  
  const [formData, setFormData] = useState({
    customer: '',
    date: new Date().toISOString().split('T')[0],
    total_amount: '',
    currency: '1',
    reference: '',
    memo: '',
    bank_account: '',
  });

  useEffect(() => {
    fetchCustomers();
    fetchCurrencies();
    fetchBankAccounts();
    fetchAccounts();
  }, []);

  useEffect(() => {
    if (formData.customer) {
      fetchOutstandingInvoices(parseInt(formData.customer));
    } else {
      setInvoices([]);
    }
  }, [formData.customer]);

  useEffect(() => {
    if (formData.date) {
      fetchExchangeRates(formData.date);
    }
  }, [formData.date]);

  const fetchCustomers = async () => {
    try {
      const response = await customersAPI.list();
      setCustomers(response.data);
    } catch (error) {
      console.error('Failed to load customers:', error);
      toast.error('Failed to load customers');
    }
  };

  const fetchCurrencies = async () => {
    try {
      const response = await currenciesAPI.list();
      setCurrencies(response.data);
    } catch (error) {
      console.error('Failed to load currencies:', error);
    }
  };

  const fetchBankAccounts = async () => {
    try {
      const response = await bankAccountsAPI.list();
      setBankAccounts(response.data);
    } catch (error) {
      console.error('Failed to load bank accounts:', error);
    }
  };

  const fetchAccounts = async () => {
    try {
      const response = await segmentsAPI.list();
      // Map segments to Account format expected by GLDistributionLines
      const mappedAccounts: Account[] = response.data.map((seg: any) => ({
        id: seg.id,
        code: seg.code || '',
        name: seg.alias || seg.name || seg.code || '',
        alias: seg.alias,
        type: seg.segment_type?.segment_type || 'account',
        is_active: true,
        level: 0,
        segment_type: seg.segment_type?.id,
      }));
      setAccounts(mappedAccounts);
    } catch (error) {
      console.error('Failed to load accounts:', error);
    }
  };

  const fetchExchangeRates = async (date: string) => {
    try {
      const response = await exchangeRatesAPI.list({ date_from: date, date_to: date });
      setExchangeRates(response.data);
    } catch (error) {
      console.error('Failed to load exchange rates:', error);
    }
  };

  // Get exchange rate between two currencies
  const getExchangeRate = (fromCurrencyId: number, toCurrencyId: number): number | null => {
    if (fromCurrencyId === toCurrencyId) return 1;
    
    // Direct rate
    const directRate = exchangeRates.find(
      r => r.from_currency === fromCurrencyId && r.to_currency === toCurrencyId
    );
    if (directRate) return parseFloat(directRate.rate);
    
    // Inverse rate
    const inverseRate = exchangeRates.find(
      r => r.from_currency === toCurrencyId && r.to_currency === fromCurrencyId
    );
    if (inverseRate) return 1 / parseFloat(inverseRate.rate);
    
    // Try through base currency
    const baseCurrency = currencies.find(c => c.is_base);
    if (baseCurrency) {
      const fromToBase = exchangeRates.find(
        r => r.from_currency === fromCurrencyId && r.to_currency === baseCurrency.id
      );
      const toToBase = exchangeRates.find(
        r => r.from_currency === toCurrencyId && r.to_currency === baseCurrency.id
      );
      
      if (fromToBase && toToBase) {
        const fromBaseRate = parseFloat(fromToBase.rate);
        const toBaseRate = parseFloat(toToBase.rate);
        return fromBaseRate / toBaseRate;
      }
    }
    
    return null;
  };

  // Convert amount from invoice currency to payment currency
  const convertAmount = (amount: number, fromCurrencyId: number, toCurrencyId: number): number | null => {
    const rate = getExchangeRate(fromCurrencyId, toCurrencyId);
    if (rate === null) return null;
    return amount * rate;
  };

  const fetchOutstandingInvoices = async (customerId: number) => {
    setLoadingInvoices(true);
    try {
      const response = await outstandingInvoicesAPI.getByCustomer(customerId);
      // Backend returns array directly, not wrapped in .invoices
      const invoiceData = Array.isArray(response.data) ? response.data : [];
      
      const allocations: InvoiceAllocation[] = invoiceData.map((inv: any) => ({
        invoice: inv.id,
        invoiceNumber: inv.number, // Backend returns 'number', not 'invoice_number'
        invoiceTotal: inv.total || '0',
        outstanding: inv.outstanding || '0', // Backend returns 'outstanding'
        amount: '',
        selected: false,
        currency: inv.currency, // Currency code from backend
        currencyId: inv.currency_id, // Currency ID from backend
      }));
      
      setInvoices(allocations);
    } catch (error) {
      console.error('Failed to load invoices:', error);
      toast.error('Failed to load outstanding invoices');
      setInvoices([]);
    } finally {
      setLoadingInvoices(false);
    }
  };

  const handleInvoiceSelect = (index: number) => {
    const newInvoices = [...invoices];
    newInvoices[index].selected = !newInvoices[index].selected;
    
    // Auto-fill amount with outstanding if selecting
    if (newInvoices[index].selected && !newInvoices[index].amount) {
      newInvoices[index].amount = newInvoices[index].outstanding;
    }
    
    setInvoices(newInvoices);
  };

  const handleAllocationAmountChange = (index: number, value: string) => {
    const newInvoices = [...invoices];
    newInvoices[index].amount = value;
    setInvoices(newInvoices);
  };

  const calculateTotalAllocated = (): number => {
    return invoices
      .filter(inv => inv.selected && inv.amount)
      .reduce((sum, inv) => sum + parseFloat(inv.amount), 0);
  };

  const calculateUnallocated = (): number => {
    const total = parseFloat(formData.total_amount) || 0;
    const allocated = calculateTotalAllocated();
    return total - allocated;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.customer) {
      toast.error('Please select a customer');
      return;
    }

    if (!formData.total_amount || parseFloat(formData.total_amount) <= 0) {
      toast.error('Please enter a valid payment amount');
      return;
    }

    const selectedAllocations = invoices.filter(inv => inv.selected);
    
    if (selectedAllocations.length === 0) {
      toast.error('Please select at least one invoice to allocate the payment');
      return;
    }

    // Validate allocations
    const paymentCurrencyId = parseInt(formData.currency);
    
    for (const inv of selectedAllocations) {
      if (!inv.amount || parseFloat(inv.amount) <= 0) {
        toast.error(`Please enter a valid amount for invoice ${inv.invoiceNumber}`);
        return;
      }
      
      // Get converted outstanding amount in payment currency
      const invoiceCurrencyId = inv.currencyId || paymentCurrencyId;
      const outstandingAmount = parseFloat(inv.outstanding);
      const convertedOutstanding = convertAmount(outstandingAmount, invoiceCurrencyId, paymentCurrencyId);
      
      if (convertedOutstanding === null) {
        toast.error(`Cannot validate ${inv.invoiceNumber}: Missing exchange rate for currency conversion`);
        return;
      }
      
      if (parseFloat(inv.amount) > convertedOutstanding) {
        const paymentCurrency = currencies.find(c => c.id === paymentCurrencyId);
        const invoiceCurrency = currencies.find(c => c.id === invoiceCurrencyId);
        toast.error(`Allocation amount for ${inv.invoiceNumber} exceeds outstanding balance (${invoiceCurrency?.code || ''} ${outstandingAmount.toFixed(2)} = ${paymentCurrency?.code || ''} ${convertedOutstanding.toFixed(2)})`);
        return;
      }
    }

    const totalAllocated = calculateTotalAllocated();
    if (totalAllocated > parseFloat(formData.total_amount)) {
      toast.error(`Total allocated (${totalAllocated.toFixed(2)}) exceeds payment amount (${formData.total_amount})`);
      return;
    }

    // Check for multi-currency scenario
    const paymentCurrency = currencies.find(c => c.id === parseInt(formData.currency));
    const paymentCurrencyCode = paymentCurrency?.code || '';
    const baseCurrency = currencies.find(c => c.is_base)?.code || 'AED';
    
    const hasMultiCurrency = selectedAllocations.some(inv => 
      inv.currency && inv.currency !== paymentCurrencyCode
    );
    
    const hasNonBaseCurrency = selectedAllocations.some(inv => 
      inv.currency && inv.currency !== baseCurrency && inv.currency !== paymentCurrencyCode
    );
    
    // Warn user about cross-currency payment
    if (hasMultiCurrency) {
      const currencyMismatchDetails = selectedAllocations
        .filter(inv => inv.currency && inv.currency !== paymentCurrencyCode)
        .map(inv => `${inv.invoiceNumber} (${inv.currency})`)
        .join(', ');
      
      const message = hasNonBaseCurrency 
        ? `⚠️ MULTI-CURRENCY PAYMENT:\n\n` +
          `Payment Currency: ${paymentCurrencyCode}\n` +
          `Invoices with different currencies: ${currencyMismatchDetails}\n\n` +
          `The system will automatically:\n` +
          `1. Convert all amounts to base currency (${baseCurrency})\n` +
          `2. Calculate FX gains/losses\n` +
          `3. Post correct journal entries\n\n` +
          `Continue with payment creation?`
        : `Cross-currency payment detected:\n` +
          `Payment: ${paymentCurrencyCode}\n` +
          `Invoices: ${currencyMismatchDetails}\n\n` +
          `Exchange rates will be applied automatically. Continue?`;
      
      if (!confirm(message)) {
        return;
      }
    }

    setLoading(true);

    try {
      // Convert GL distribution lines to backend format
      const convertedGlLines = glLines.map(line => ({
        account: line.account || 0,
        line_type: line.line_type || 'DEBIT',
        amount: line.amount || '0',
        description: line.description || '',
        segments: line.segments?.reduce((acc: any, seg) => {
          if (seg.segment_type && seg.segment) {
            acc[seg.segment_type.toString()] = seg.segment;
          }
          return acc;
        }, {}) || {},
      }));

      const paymentData = {
        customer: parseInt(formData.customer),
        date: formData.date,
        total_amount: formData.total_amount,
        currency: parseInt(formData.currency),
        reference: formData.reference,
        memo: formData.memo,
        bank_account: formData.bank_account ? parseInt(formData.bank_account) : undefined,
        allocations: selectedAllocations.map(inv => ({
          invoice: inv.invoice,
          amount: inv.amount,
        })),
        gl_lines: convertedGlLines.length > 0 ? convertedGlLines : undefined,
      };

      await arPaymentsAPI.create(paymentData);
      toast.success('Payment created successfully!');
      router.push('/ar/payments');
    } catch (error: any) {
      console.error('Failed to create payment:', error);
      const errorMsg = error.response?.data?.message || 
                      error.response?.data?.detail ||
                      JSON.stringify(error.response?.data) ||
                      'Failed to create payment';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const unallocated = calculateUnallocated();
  const totalAllocated = calculateTotalAllocated();
  const selectedCount = invoices.filter(inv => inv.selected).length;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">New AR Payment</h1>
          <p className="mt-2 text-gray-600">Create a new payment and allocate to multiple invoices</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Payment Details Card */}
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Payment Details</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Customer */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Customer <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.customer}
                  onChange={(e) => setFormData({ ...formData, customer: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select customer...</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Reference */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Reference Number <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.reference}
                  onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="PMT-001"
                  required
                />
              </div>

              {/* Payment Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Payment Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Total Amount */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Total Payment Amount <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.total_amount}
                  onChange={(e) => setFormData({ ...formData, total_amount: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.00"
                  required
                />
              </div>

              {/* Currency */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Currency
                </label>
                <select
                  value={formData.currency}
                  onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {currencies.map((currency) => (
                    <option key={currency.id} value={currency.id}>
                      {currency.code} - {currency.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Bank Account */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Bank Account
                </label>
                <select
                  value={formData.bank_account}
                  onChange={(e) => setFormData({ ...formData, bank_account: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select bank account...</option>
                  {bankAccounts.map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.name} ({account.account_code})
                    </option>
                  ))}
                </select>
              </div>

              {/* Memo */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Memo
                </label>
                <textarea
                  value={formData.memo}
                  onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={2}
                  placeholder="Payment notes..."
                />
              </div>
            </div>
          </div>

          {/* Allocation Summary */}
          {formData.total_amount && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-sm text-gray-600">Total Payment</div>
                  <div className="text-2xl font-bold text-gray-900">
                    ${parseFloat(formData.total_amount).toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Allocated ({selectedCount} invoices)</div>
                  <div className="text-2xl font-bold text-green-600">
                    ${totalAllocated.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Unallocated</div>
                  <div className={`text-2xl font-bold ${unallocated < 0 ? 'text-red-600' : unallocated > 0 ? 'text-orange-600' : 'text-green-600'}`}>
                    ${Math.abs(unallocated).toFixed(2)}
                  </div>
                </div>
              </div>
              
              {unallocated < 0 && (
                <div className="mt-4 p-3 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
                  ⚠️ Over-allocated by ${Math.abs(unallocated).toFixed(2)}. Please reduce allocation amounts.
                </div>
              )}
              {unallocated > 0 && selectedCount > 0 && (
                <div className="mt-4 p-3 bg-orange-100 border border-orange-300 rounded text-orange-700 text-sm">
                  💡 You have ${unallocated.toFixed(2)} unallocated. This is allowed but consider allocating the full amount.
                </div>
              )}
            </div>
          )}

          {/* Invoice Allocations Card */}
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Invoice Allocations
              {!formData.customer && <span className="text-sm text-gray-500 font-normal ml-2">(Select a customer first)</span>}
            </h2>

            {/* Multi-Currency Info Box */}
            {formData.customer && invoices.length > 0 && (() => {
              const paymentCurrency = currencies.find(c => c.id === parseInt(formData.currency));
              const paymentCurrencyCode = paymentCurrency?.code || '';
              const baseCurrency = currencies.find(c => c.is_base)?.code || 'AED';
              const hasCrossCurrency = invoices.some(inv => inv.currency && inv.currency !== paymentCurrencyCode);
              const hasComplexFX = invoices.some(inv => 
                inv.currency && 
                inv.currency !== baseCurrency && 
                paymentCurrencyCode !== baseCurrency &&
                inv.currency !== paymentCurrencyCode
              );
              
              if (hasCrossCurrency) {
                return (
                  <div className={`mb-4 p-4 rounded-lg border ${
                    hasComplexFX 
                      ? 'bg-orange-50 border-orange-200' 
                      : 'bg-blue-50 border-blue-200'
                  }`}>
                    <div className="flex items-start gap-2">
                      <span className="text-lg">{hasComplexFX ? '⚠️' : 'ℹ️'}</span>
                      <div className="flex-1">
                        <h3 className={`font-semibold mb-2 ${
                          hasComplexFX ? 'text-orange-900' : 'text-blue-900'
                        }`}>
                          {hasComplexFX ? 'Multi-Currency Payment Detected' : 'Cross-Currency Payment'}
                        </h3>
                        <div className={`text-sm space-y-1 ${
                          hasComplexFX ? 'text-orange-800' : 'text-blue-800'
                        }`}>
                          <p><strong>Payment Currency:</strong> {paymentCurrencyCode}</p>
                          <p><strong>Base Currency:</strong> {baseCurrency}</p>
                          {hasComplexFX && (
                            <>
                              <p className="mt-2"><strong>Automatic Processing:</strong></p>
                              <ul className="list-disc list-inside ml-2 space-y-1">
                                <li>Invoice amounts converted: Invoice Currency → {baseCurrency}</li>
                                <li>Payment amount converted: {paymentCurrencyCode} → {baseCurrency}</li>
                                <li>FX gain/loss calculated automatically</li>
                                <li>All GL entries posted in {baseCurrency}</li>
                              </ul>
                            </>
                          )}
                          {!hasComplexFX && (
                            <p className="mt-1">
                              Exchange rate will be applied automatically between invoice and payment currencies.
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              }
              return null;
            })()}

            {loadingInvoices ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                <p className="mt-2 text-gray-600">Loading invoices...</p>
              </div>
            ) : invoices.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                {formData.customer ? 'No outstanding invoices found for this customer' : 'Select a customer to view outstanding invoices'}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Select
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Invoice #
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Currency
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Outstanding
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Converted
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Allocation Amount
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {invoices.map((invoice, index) => {
                      const paymentCurrency = currencies.find(c => c.id === parseInt(formData.currency));
                      const paymentCurrencyCode = paymentCurrency?.code || '';
                      const paymentCurrencyId = paymentCurrency?.id || 1;
                      const baseCurrency = currencies.find(c => c.is_base)?.code || 'AED';
                      const isCrossCurrency = invoice.currency && invoice.currency !== paymentCurrencyCode;
                      const isComplexFX = invoice.currency && 
                                         invoice.currency !== baseCurrency && 
                                         paymentCurrencyCode !== baseCurrency &&
                                         invoice.currency !== paymentCurrencyCode;
                      
                      // Calculate converted amount
                      const invoiceCurrencyId = invoice.currencyId || paymentCurrencyId;
                      const outstandingAmount = parseFloat(invoice.outstanding);
                      const convertedAmount = isCrossCurrency && invoice.currencyId
                        ? convertAmount(outstandingAmount, invoiceCurrencyId, paymentCurrencyId)
                        : outstandingAmount;
                      
                      const hasRate = convertedAmount !== null;
                      const maxAllowed = convertedAmount || outstandingAmount;
                      const currentAmount = parseFloat(invoice.amount) || 0;
                      const exceedsLimit = invoice.selected && currentAmount > maxAllowed;
                      
                      return (
                        <tr key={invoice.invoice} className={invoice.selected ? 'bg-blue-50' : ''}>
                          <td className="px-4 py-3">
                            <input
                              type="checkbox"
                              checked={invoice.selected}
                              onChange={() => handleInvoiceSelect(index)}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                              disabled={isCrossCurrency && !hasRate ? true : undefined}
                              title={isCrossCurrency && !hasRate ? `Exchange rate not available for ${invoice.currency} → ${paymentCurrencyCode}` : ''}
                            />
                          </td>
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {invoice.invoiceNumber}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <div className="flex items-center justify-center gap-1">
                              <span className={`text-sm font-medium ${isCrossCurrency ? 'text-blue-700' : 'text-gray-700'}`}>
                                {invoice.currency || '-'}
                              </span>
                              {isCrossCurrency && (
                                <span 
                                  className={`text-xs px-1.5 py-0.5 rounded ${
                                    isComplexFX 
                                      ? 'bg-orange-100 text-orange-700' 
                                      : 'bg-blue-100 text-blue-700'
                                  }`}
                                  title={isComplexFX 
                                    ? `Complex FX: ${invoice.currency} → ${baseCurrency} → ${paymentCurrencyCode}` 
                                    : `Cross-currency: ${invoice.currency} → ${paymentCurrencyCode}`
                                  }
                                >
                                  {isComplexFX ? 'FX*' : 'FX'}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-right">
                            <div className="font-semibold text-gray-900">
                              {invoice.currency} {outstandingAmount.toFixed(2)}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-right">
                            {isCrossCurrency ? (
                              hasRate ? (
                                <div className="space-y-1">
                                  <div className="font-bold text-green-700">
                                    {paymentCurrencyCode} {convertedAmount!.toFixed(2)}
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    @ {(convertedAmount! / outstandingAmount).toFixed(6)}
                                  </div>
                                </div>
                              ) : (
                                <div className="text-red-600 text-xs font-semibold">
                                  ⚠️ No Rate
                                </div>
                              )
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="space-y-1">
                              <input
                                type="number"
                                step="0.01"
                                value={invoice.amount}
                                onChange={(e) => handleAllocationAmountChange(index, e.target.value)}
                                disabled={!invoice.selected || (isCrossCurrency && !hasRate) ? true : undefined}
                                className={`w-full px-3 py-2 text-right border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                                  !invoice.selected || (isCrossCurrency && !hasRate)
                                    ? 'bg-gray-100 border-gray-200 text-gray-500'
                                    : exceedsLimit
                                    ? 'bg-red-50 border-red-300 text-red-900'
                                    : 'bg-white border-gray-300'
                                }`}
                                placeholder="0.00"
                                max={maxAllowed}
                              />
                              {invoice.selected && isCrossCurrency && hasRate && (
                                <div className="text-xs text-gray-600 text-right">
                                  Max: {paymentCurrencyCode} {maxAllowed.toFixed(2)}
                                </div>
                              )}
                              {exceedsLimit && (
                                <div className="text-xs text-red-600 text-right font-semibold">
                                  ⚠️ Exceeds limit!
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* GL Distribution Card */}
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              GL Distribution (Optional)
            </h2>
            <GLDistributionLines
              lines={glLines}
              onChange={setGlLines}
              accounts={accounts}
              invoiceTotal={parseFloat(formData.total_amount || '0')}
              currencySymbol={currencies.find(c => c.id === parseInt(formData.currency))?.symbol || '$'}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => router.push('/ar/payments')}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || unallocated < 0 || selectedCount === 0}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Creating...' : 'Create Payment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

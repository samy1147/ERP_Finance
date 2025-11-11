'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { arInvoicesAPI, customersAPI, currenciesAPI, taxRatesAPI, exchangeRatesAPI, fxConfigAPI, accountsAPI } from '../../../../services/api';
import { ARInvoiceItem, Customer, Currency, TaxRate, Account, GLDistributionLine } from '../../../../types';
import { Plus, Trash2, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import GLDistributionLines from '../../../../components/GLDistributionLines';

export default function NewARInvoicePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [taxRates, setTaxRates] = useState<TaxRate[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [baseCurrency, setBaseCurrency] = useState<Currency | null>(null);
  const [exchangeRate, setExchangeRate] = useState<number | null>(null);
  const [exchangeRateLoading, setExchangeRateLoading] = useState(false);
  const [manualExchangeRate, setManualExchangeRate] = useState(false);
  const [glLines, setGlLines] = useState<Partial<GLDistributionLine>[]>([]);
  const [formData, setFormData] = useState({
    customer: '',
    number: '',
    date: new Date().toISOString().split('T')[0],
    due_date: new Date().toISOString().split('T')[0],
    currency: '1', // Default currency ID
    country: 'AE', // Default country
  });
  const [items, setItems] = useState<Partial<ARInvoiceItem>[]>([
    { description: '', quantity: '1', unit_price: '0', tax_rate: undefined },
  ]);

  useEffect(() => {
    fetchCustomers();
    fetchCurrencies();
    fetchTaxRates();
    fetchBaseCurrency();
    fetchAccounts();
  }, []);

  useEffect(() => {
    // Reload tax rates when country changes
    if (formData.country) {
      fetchTaxRates(formData.country);
    }
  }, [formData.country]);

  useEffect(() => {
    // Fetch exchange rate when currency or date changes
    if (formData.currency && formData.date && baseCurrency && !manualExchangeRate) {
      fetchExchangeRate();
    }
  }, [formData.currency, formData.date, baseCurrency]);

  const fetchCustomers = async () => {
    try {
      const response = await customersAPI.list();
      setCustomers(response.data);
    } catch (error) {
      toast.error('Failed to load customers');
    }
  };

  const fetchCurrencies = async () => {
    try {
      const response = await currenciesAPI.list();
      setCurrencies(response.data);
      if (response.data.length > 0) {
        setFormData(prev => ({ ...prev, currency: response.data[0].id.toString() }));
      }
    } catch (error) {
      toast.error('Failed to load currencies');
    }
  };

  const fetchTaxRates = async (country?: string) => {
    try {
      const response = await taxRatesAPI.list(country);
      console.log(`📊 Tax rates loaded for ${country || 'all countries'}:`, response.data);
      console.log(`   Found ${response.data.length} tax rates`);
      setTaxRates(response.data);
    } catch (error) {
      console.error('❌ Failed to load tax rates:', error);
      toast.error('Failed to load tax rates. Please refresh the page.');
    }
  };

  const fetchAccounts = async () => {
    try {
      const response = await accountsAPI.list();
      setAccounts(response.data);
    } catch (error) {
      console.error('❌ Failed to load accounts:', error);
      toast.error('Failed to load accounts');
    }
  };

  const fetchBaseCurrency = async () => {
    try {
      const response = await fxConfigAPI.baseCurrency();
      setBaseCurrency(response.data);
      console.log('💱 Base currency loaded:', response.data);
    } catch (error) {
      console.error('❌ Failed to load base currency:', error);
      toast.error('Failed to load base currency');
    }
  };

  const fetchExchangeRate = async () => {
    if (!formData.currency || !formData.date || !baseCurrency) {
      console.log('⏭️ Skipping exchange rate fetch - missing data:', {
        currency: formData.currency,
        date: formData.date,
        baseCurrency: baseCurrency?.code
      });
      return;
    }

    const selectedCurrency = currencies.find(c => c.id === parseInt(formData.currency));
    if (!selectedCurrency) {
      console.log('⏭️ Skipping exchange rate fetch - currency not found in list');
      return;
    }

    console.log('💱 Fetching exchange rate:', {
      from: selectedCurrency.code,
      to: baseCurrency.code,
      date: formData.date
    });

    // If same as base currency, rate is 1
    if (selectedCurrency.code === baseCurrency.code) {
      console.log('✅ Same currency - rate = 1');
      setExchangeRate(1);
      return;
    }

    setExchangeRateLoading(true);
    try {
      // Fetch exchange rate from selected currency to base currency
      const response = await exchangeRatesAPI.list({
        from_currency: selectedCurrency.id,
        to_currency: baseCurrency.id,
        date_from: formData.date,
        date_to: formData.date,
      });

      console.log('📊 Exchange rate API response:', response.data);

      if (response.data && response.data.length > 0) {
        const rate = parseFloat(response.data[0].rate);
        setExchangeRate(rate);
        console.log('✅ Exchange rate set:', rate);
        toast.success(`Exchange rate loaded: 1 ${selectedCurrency.code} = ${rate.toFixed(6)} ${baseCurrency.code}`);
      } else {
        console.log('❌ No exchange rate found');
        toast.error(`No exchange rate found for ${selectedCurrency.code} to ${baseCurrency.code} on ${formData.date}`);
        setExchangeRate(null);
      }
    } catch (error) {
      console.error('❌ Failed to fetch exchange rate:', error);
      toast.error('Failed to fetch exchange rate');
      setExchangeRate(null);
    } finally {
      setExchangeRateLoading(false);
    }
  };

  const handleCustomerChange = async (customerId: string) => {
    setFormData({ ...formData, customer: customerId });
    
    // Auto-set country from customer
    if (customerId) {
      const customer = customers.find(c => c.id === parseInt(customerId));
      if (customer && customer.country) {
        setFormData(prev => ({ ...prev, customer: customerId, country: customer.country || 'AE' }));
      }
    }
  };

  const handleAddItem = () => {
    setItems([...items, { description: '', quantity: '1', unit_price: '0', tax_rate: undefined }]);
  };

  const handleRemoveItem = (index: number) => {
    const newItems = items.filter((_, i) => i !== index);
    setItems(newItems);
  };

  const handleItemChange = (index: number, field: keyof ARInvoiceItem, value: string) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], [field]: value };
    setItems(newItems);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.customer) {
      toast.error('Please select a customer');
      return;
    }

    // Validate exchange rate for foreign currency invoices
    const selectedCurrency = currencies.find(c => c.id === parseInt(formData.currency));
    if (selectedCurrency && baseCurrency && selectedCurrency.code !== baseCurrency.code) {
      if (!exchangeRate || exchangeRate <= 0) {
        toast.error('Exchange rate is required for foreign currency invoices');
        return;
      }
    }

    // Filter valid items (with description)
    const validItems = items.filter(item => item.description && item.description.trim());
    
    // Check if at least one valid item exists
    if (validItems.length === 0) {
      toast.error('Please add at least one item with a description');
      return;
    }

    // Validate that valid items have quantity and price
    const invalidItems = validItems.filter(item => 
      !item.quantity || !item.unit_price || 
      parseFloat(item.quantity) <= 0 || parseFloat(item.unit_price) < 0
    );
    
    if (invalidItems.length > 0) {
      toast.error('All items must have valid quantity (> 0) and unit price (>= 0)');
      return;
    }

    setLoading(true);

    try {
      const invoiceTotal = calculateTotal();
      const baseCurrencyTotal = exchangeRate ? invoiceTotal * exchangeRate : invoiceTotal;
      
      const invoiceData: any = {
        customer: parseInt(formData.customer),
        number: formData.number,
        date: formData.date,
        due_date: formData.due_date,
        currency: parseInt(formData.currency),
        country: formData.country,
        items: validItems.map(item => ({
          description: item.description,
          quantity: item.quantity,
          unit_price: item.unit_price,
          tax_rate: item.tax_rate ? parseInt(item.tax_rate as any) : null
        })),
      };
      
      // Add GL distribution lines (REQUIRED)
      if (!glLines || glLines.length === 0) {
        toast.error('Please add at least one GL distribution line');
        return;
      }
      
      // Validate GL lines before submitting
      const validGlLines = glLines.filter(line => line.account && line.amount);
      if (validGlLines.length === 0) {
        toast.error('Please add valid GL distribution lines with account and amount');
        return;
      }
      
      invoiceData.gl_lines = validGlLines.map(line => ({
        account: line.account,
        line_type: line.line_type,
        amount: line.amount,
        description: line.description || ''
      }));
      
      // Add exchange rate fields if applicable
      if (exchangeRate) {
        invoiceData.exchange_rate = exchangeRate.toString();
        invoiceData.base_currency_total = baseCurrencyTotal.toString();
      }

      console.log('Sending invoice data:', invoiceData); // Debug log
      await arInvoicesAPI.create(invoiceData);
      toast.success('Invoice created successfully');
      router.push('/ar/invoices');
    } catch (error: any) {
      console.error('Invoice creation error:', error); // Debug log
      const errorMessage = error.response?.data?.error 
        || error.response?.data?.message 
        || JSON.stringify(error.response?.data) 
        || 'Failed to create invoice';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Calculate line item with tax
  const calculateLineTotal = (item: Partial<ARInvoiceItem>) => {
    const qty = parseFloat(item.quantity || '0');
    const price = parseFloat(item.unit_price || '0');
    const subtotal = qty * price;
    
    // Find tax rate if selected
    let taxRate = 0;
    if (item.tax_rate) {
      const selectedTaxRate = taxRates.find(tr => tr.id === parseInt(item.tax_rate as any));
      if (selectedTaxRate) {
        taxRate = parseFloat(selectedTaxRate.rate.toString());
      }
    }
    
    const tax = subtotal * (taxRate / 100);
    return {
      subtotal,
      tax,
      total: subtotal + tax
    };
  };

  // Calculate invoice totals (tax applied in invoice currency)
  const calculateTotals = () => {
    let subtotal = 0;
    let tax = 0;
    
    items.forEach(item => {
      const lineCalc = calculateLineTotal(item);
      subtotal += lineCalc.subtotal;
      tax += lineCalc.tax;
    });
    
    return {
      subtotal: subtotal,
      tax: tax,
      total: subtotal + tax
    };
  };

  const calculateTotal = () => {
    return calculateTotals().total;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Create AR Invoice</h1>
        <p className="mt-2 text-gray-600">Create a new customer invoice</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Invoice Header */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Invoice Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Customer *
              </label>
              <select
                required
                className="input-field"
                value={formData.customer}
                onChange={(e) => handleCustomerChange(e.target.value)}
                aria-label="Select customer"
              >
                <option value="">Select a customer...</option>
                {customers.map(customer => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Invoice Number *
              </label>
              <input
                type="text"
                required
                className="input-field"
                value={formData.number}
                onChange={(e) => setFormData({ ...formData, number: e.target.value })}
                aria-label="Invoice number"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Invoice Date *
              </label>
              <input
                type="date"
                required
                className="input-field"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                aria-label="Invoice date"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Due Date *
              </label>
              <input
                type="date"
                required
                className="input-field"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                aria-label="Due date"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Currency *
              </label>
              <select
                required
                className="input-field"
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                aria-label="Select currency"
              >
                {currencies.map(currency => (
                  <option key={currency.id} value={currency.id}>
                    {currency.code} - {currency.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tax Country *
              </label>
              <select
                required
                className="input-field"
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                aria-label="Select tax country"
              >
                <option value="AE">UAE</option>
                <option value="SA">Saudi Arabia (KSA)</option>
                <option value="EG">Egypt</option>
                <option value="IN">India</option>
              </select>
            </div>
            
            {/* Exchange Rate Field */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Exchange Rate
                {baseCurrency && currencies.find(c => c.id === parseInt(formData.currency)) && (
                  <span className="text-xs text-gray-500 ml-2">
                    (1 {currencies.find(c => c.id === parseInt(formData.currency))?.code} = ? {baseCurrency.code})
                  </span>
                )}
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  step="0.000001"
                  className={`input-field ${exchangeRateLoading ? 'bg-gray-100' : ''}`}
                  value={exchangeRate || ''}
                  onChange={(e) => {
                    setExchangeRate(parseFloat(e.target.value) || null);
                    setManualExchangeRate(true);
                  }}
                  placeholder="Auto-fetched"
                  disabled={exchangeRateLoading}
                  aria-label="Exchange rate"
                />
                <button
                  type="button"
                  onClick={() => {
                    setManualExchangeRate(false);
                    fetchExchangeRate();
                  }}
                  className="btn-secondary px-3"
                  disabled={exchangeRateLoading}
                  title="Refresh exchange rate"
                >
                  <RefreshCw className={`h-4 w-4 ${exchangeRateLoading ? 'animate-spin' : ''}`} />
                </button>
              </div>
              {exchangeRate && exchangeRate !== 1 && (
                <p className="text-xs text-green-600 mt-1">
                  ✓ Rate: 1 {currencies.find(c => c.id === parseInt(formData.currency))?.code} = {exchangeRate.toFixed(6)} {baseCurrency?.code}
                </p>
              )}
              {exchangeRate === 1 && (
                <p className="text-xs text-gray-500 mt-1">
                  Same as base currency
                </p>
              )}
              {manualExchangeRate && (
                <p className="text-xs text-amber-600 mt-1">
                  ⚠️ Manual rate (not auto-fetched)
                </p>
              )}
            </div>
          </div>
        </div>

        {/* GL Distribution Lines */}
        <GLDistributionLines
          lines={glLines}
          accounts={accounts}
          invoiceTotal={calculateTotal()}
          currencySymbol={currencies.find(c => c.id === parseInt(formData.currency))?.symbol || ''}
          onChange={setGlLines}
        />

        {/* Invoice Items */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Line Items</h2>
            <button
              type="button"
              onClick={handleAddItem}
              className="btn-secondary flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Add Item
            </button>
          </div>

          <div className="space-y-3">
            <div className="grid grid-cols-12 gap-3 text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              <div className="col-span-4">Description</div>
              <div className="col-span-2">Quantity</div>
              <div className="col-span-2">Unit Price</div>
              <div className="col-span-2">Tax Rate</div>
              <div className="col-span-2">Amount</div>
            </div>
            {items.map((item, index) => (
              <div key={index} className="grid grid-cols-12 gap-3 items-start">
                <div className="col-span-4">
                  <input
                    type="text"
                    placeholder="Description"
                    className="input-field"
                    value={item.description}
                    onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                  />
                </div>
                <div className="col-span-2">
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Qty"
                    className="input-field"
                    value={item.quantity}
                    onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                  />
                </div>
                <div className="col-span-2">
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Unit Price"
                    className="input-field"
                    value={item.unit_price}
                    onChange={(e) => handleItemChange(index, 'unit_price', e.target.value)}
                  />
                </div>
                <div className="col-span-2">
                  <select
                    className="input-field text-sm"
                    value={item.tax_rate || ''}
                    onChange={(e) => handleItemChange(index, 'tax_rate', e.target.value)}
                  >
                    <option value="">No Tax</option>
                    {taxRates.filter(tr => tr.is_active).map(taxRate => (
                      <option key={taxRate.id} value={taxRate.id}>
                        {taxRate.name} ({taxRate.rate}%)
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-span-2 flex items-center gap-2">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">
                      {currencies.find(c => c.id === parseInt(formData.currency))?.code || 'USD'} {calculateLineTotal(item).total.toFixed(2)}
                    </span>
                    {calculateLineTotal(item).tax > 0 && (
                      <span className="text-xs text-gray-500">
                        (Tax: {calculateLineTotal(item).tax.toFixed(2)})
                      </span>
                    )}
                  </div>
                  {items.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(index)}
                      className="text-red-600 hover:text-red-800"
                      aria-label="Remove item"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex justify-end">
              <div className="text-right space-y-2">
                <div className="flex justify-between gap-8">
                  <span className="text-sm text-gray-600">Subtotal:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {currencies.find(c => c.id === parseInt(formData.currency))?.code || 'USD'} {calculateTotals().subtotal.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between gap-8">
                  <span className="text-sm text-gray-600">Tax:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {currencies.find(c => c.id === parseInt(formData.currency))?.code || 'USD'} {calculateTotals().tax.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between gap-8 pt-2 border-t border-gray-200">
                  <span className="text-base font-semibold text-gray-700">Total:</span>
                  <span className="text-2xl font-bold text-gray-900">
                    {currencies.find(c => c.id === parseInt(formData.currency))?.code || 'USD'} {calculateTotal().toFixed(2)}
                  </span>
                </div>
                
                {/* Base Currency Total */}
                {exchangeRate && exchangeRate !== 1 && baseCurrency && (
                  <div className="mt-3 pt-3 border-t border-blue-200 bg-blue-50 -mx-3 px-3 py-2 rounded">
                    <div className="flex justify-between gap-8">
                      <span className="text-sm font-medium text-blue-700">
                        Total in Base Currency:
                      </span>
                      <span className="text-lg font-bold text-blue-900">
                        {baseCurrency.code} {(calculateTotal() * exchangeRate).toFixed(2)}
                      </span>
                    </div>
                    <div className="text-xs text-blue-600 mt-1">
                      @ Rate: {exchangeRate.toFixed(6)} | Date: {formData.date}
                    </div>
                  </div>
                )}
                
                <div className="text-xs text-gray-500 mt-1">
                  Tax calculated in invoice currency
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Invoice'}
          </button>
        </div>
      </form>
    </div>
  );
}

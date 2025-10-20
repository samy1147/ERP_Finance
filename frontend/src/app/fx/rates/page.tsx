'use client';

import { useState, useEffect } from 'react';
import { exchangeRatesAPI, currenciesAPI } from '@/services/api';
import { ExchangeRate, Currency } from '@/types';

export default function ExchangeRatesPage() {
  const [rates, setRates] = useState<ExchangeRate[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showConverter, setShowConverter] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    from_currency: '',
    to_currency: '',
    rate_type: '',
    date_from: '',
    date_to: '',
  });

  // Form data
  const [formData, setFormData] = useState({
    from_currency: '',
    to_currency: '',
    rate_date: new Date().toISOString().split('T')[0],
    rate: '',
    rate_type: 'SPOT',
    source: '',
    is_active: true,
  });

  // Converter data
  const [converterData, setConverterData] = useState({
    amount: '',
    from_currency_code: '',
    to_currency_code: '',
    rate_date: new Date().toISOString().split('T')[0],
    rate_type: 'SPOT',
  });
  const [conversionResult, setConversionResult] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [ratesRes, currenciesRes] = await Promise.all([
        exchangeRatesAPI.list(),
        currenciesAPI.list(),
      ]);
      setRates(ratesRes.data);
      setCurrencies(currenciesRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      alert('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadRatesWithFilters = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filters.from_currency) params.from_currency = parseInt(filters.from_currency);
      if (filters.to_currency) params.to_currency = parseInt(filters.to_currency);
      if (filters.rate_type) params.rate_type = filters.rate_type;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;
      
      const response = await exchangeRatesAPI.list(params);
      setRates(response.data);
    } catch (error) {
      console.error('Error loading rates:', error);
      alert('Failed to load exchange rates');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await exchangeRatesAPI.update(editingId, {
          from_currency: parseInt(formData.from_currency),
          to_currency: parseInt(formData.to_currency),
          rate_date: formData.rate_date,
          rate: formData.rate,
          rate_type: formData.rate_type as any,
          source: formData.source,
          is_active: formData.is_active,
        });
      } else {
        await exchangeRatesAPI.create({
          from_currency: parseInt(formData.from_currency),
          to_currency: parseInt(formData.to_currency),
          rate_date: formData.rate_date,
          rate: formData.rate,
          rate_type: formData.rate_type as any,
          source: formData.source,
          is_active: formData.is_active,
        });
      }
      resetForm();
      loadRatesWithFilters();
    } catch (error: any) {
      console.error('Error saving exchange rate:', error);
      alert(`Failed to save exchange rate: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleEdit = (rate: ExchangeRate) => {
    setFormData({
      from_currency: rate.from_currency.toString(),
      to_currency: rate.to_currency.toString(),
      rate_date: rate.rate_date,
      rate: rate.rate,
      rate_type: rate.rate_type,
      source: rate.source || '',
      is_active: rate.is_active,
    });
    setEditingId(rate.id);
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this exchange rate?')) return;
    try {
      await exchangeRatesAPI.delete(id);
      loadRatesWithFilters();
    } catch (error) {
      console.error('Error deleting exchange rate:', error);
      alert('Failed to delete exchange rate');
    }
  };

  const handleConvert = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await exchangeRatesAPI.convert(converterData);
      setConversionResult(response.data);
    } catch (error: any) {
      console.error('Error converting currency:', error);
      alert(`Conversion failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  const resetForm = () => {
    setFormData({
      from_currency: '',
      to_currency: '',
      rate_date: new Date().toISOString().split('T')[0],
      rate: '',
      rate_type: 'SPOT',
      source: '',
      is_active: true,
    });
    setEditingId(null);
    setShowForm(false);
  };

  const getCurrencyName = (id: number) => {
    const currency = currencies.find(c => c.id === id);
    return currency ? `${currency.code} - ${currency.name}` : id;
  };

  if (loading && rates.length === 0) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-xl">Loading exchange rates...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Exchange Rates</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowConverter(!showConverter)}
            className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded"
          >
            {showConverter ? 'Hide Converter' : '💱 Currency Converter'}
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            {showForm ? 'Cancel' : '+ Add Exchange Rate'}
          </button>
        </div>
      </div>

      {/* Currency Converter */}
      {showConverter && (
        <div className="bg-purple-50 border-2 border-purple-200 rounded-lg px-8 pt-6 pb-8 mb-6">
          <h2 className="text-xl font-bold mb-4 text-purple-800">Currency Converter</h2>
          <form onSubmit={handleConvert}>
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={converterData.amount}
                  onChange={(e) => setConverterData({ ...converterData, amount: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3"
                  required
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">From Currency</label>
                <select
                  value={converterData.from_currency_code}
                  onChange={(e) => setConverterData({ ...converterData, from_currency_code: e.target.value })}
                  className="shadow border rounded w-full py-2 px-3"
                  required
                >
                  <option value="">Select...</option>
                  {currencies.map((c) => (
                    <option key={c.id} value={c.code}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">To Currency</label>
                <select
                  value={converterData.to_currency_code}
                  onChange={(e) => setConverterData({ ...converterData, to_currency_code: e.target.value })}
                  className="shadow border rounded w-full py-2 px-3"
                  required
                >
                  <option value="">Select...</option>
                  {currencies.map((c) => (
                    <option key={c.id} value={c.code}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Rate Date</label>
                <input
                  type="date"
                  value={converterData.rate_date}
                  onChange={(e) => setConverterData({ ...converterData, rate_date: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3"
                  required
                />
              </div>
            </div>
            <button
              type="submit"
              className="bg-purple-600 hover:bg-purple-800 text-white font-bold py-2 px-6 rounded"
            >
              Convert
            </button>
          </form>
          {conversionResult && (
            <div className="mt-4 p-4 bg-white rounded border-2 border-purple-300">
              <p className="text-lg font-bold text-purple-900">
                {conversionResult.amount} {conversionResult.from_currency} = 
                <span className="text-2xl ml-2">{conversionResult.converted_amount} {conversionResult.to_currency}</span>
              </p>
              <p className="text-sm text-gray-600 mt-2">
                Rate: 1 {conversionResult.from_currency} = {conversionResult.rate} {conversionResult.to_currency}
                {conversionResult.rate_date && ` (as of ${conversionResult.rate_date})`}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="bg-gray-50 rounded px-6 py-4 mb-6">
        <h3 className="font-bold mb-3">Filters</h3>
        <div className="grid grid-cols-5 gap-4">
          <div>
            <label className="block text-sm mb-1">From Currency</label>
            <select
              value={filters.from_currency}
              onChange={(e) => setFilters({ ...filters, from_currency: e.target.value })}
              className="shadow border rounded w-full py-2 px-3 text-sm"
            >
              <option value="">All</option>
              {currencies.map((c) => (
                <option key={c.id} value={c.id}>{c.code}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">To Currency</label>
            <select
              value={filters.to_currency}
              onChange={(e) => setFilters({ ...filters, to_currency: e.target.value })}
              className="shadow border rounded w-full py-2 px-3 text-sm"
            >
              <option value="">All</option>
              {currencies.map((c) => (
                <option key={c.id} value={c.id}>{c.code}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Rate Type</label>
            <select
              value={filters.rate_type}
              onChange={(e) => setFilters({ ...filters, rate_type: e.target.value })}
              className="shadow border rounded w-full py-2 px-3 text-sm"
            >
              <option value="">All</option>
              <option value="SPOT">Spot</option>
              <option value="AVERAGE">Average</option>
              <option value="FIXED">Fixed</option>
              <option value="CLOSING">Closing</option>
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Date From</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              className="shadow border rounded w-full py-2 px-3 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Date To</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
              className="shadow border rounded w-full py-2 px-3 text-sm"
            />
          </div>
        </div>
        <button
          onClick={loadRatesWithFilters}
          className="mt-3 bg-gray-600 hover:bg-gray-800 text-white font-bold py-2 px-4 rounded text-sm"
        >
          Apply Filters
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-6">
          <h2 className="text-xl font-bold mb-4">
            {editingId ? 'Edit Exchange Rate' : 'Add New Exchange Rate'}
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">From Currency *</label>
                <select
                  value={formData.from_currency}
                  onChange={(e) => setFormData({ ...formData, from_currency: e.target.value })}
                  className="shadow border rounded w-full py-2 px-3"
                  required
                >
                  <option value="">Select...</option>
                  {currencies.map((c) => (
                    <option key={c.id} value={c.id}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">To Currency *</label>
                <select
                  value={formData.to_currency}
                  onChange={(e) => setFormData({ ...formData, to_currency: e.target.value })}
                  className="shadow border rounded w-full py-2 px-3"
                  required
                >
                  <option value="">Select...</option>
                  {currencies.map((c) => (
                    <option key={c.id} value={c.id}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Rate *</label>
                <input
                  type="number"
                  step="0.000001"
                  value={formData.rate}
                  onChange={(e) => setFormData({ ...formData, rate: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3"
                  required
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Rate Date *</label>
                <input
                  type="date"
                  value={formData.rate_date}
                  onChange={(e) => setFormData({ ...formData, rate_date: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3"
                  required
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Rate Type *</label>
                <select
                  value={formData.rate_type}
                  onChange={(e) => setFormData({ ...formData, rate_type: e.target.value })}
                  className="shadow border rounded w-full py-2 px-3"
                  required
                >
                  <option value="SPOT">Spot Rate</option>
                  <option value="AVERAGE">Average Rate</option>
                  <option value="FIXED">Fixed Rate</option>
                  <option value="CLOSING">Period Closing Rate</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Source</label>
                <input
                  type="text"
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3"
                  placeholder="Central Bank, Manual, etc."
                />
              </div>
              <div className="flex items-center mt-6">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="mr-2 h-5 w-5"
                />
                <label htmlFor="is_active" className="text-gray-700 text-sm font-bold">
                  Active
                </label>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
              >
                {editingId ? 'Update' : 'Create'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Table */}
      <div className="bg-white shadow-md rounded overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">From</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">To</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rate</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rates.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                  No exchange rates found. Click "Add Exchange Rate" to create one.
                </td>
              </tr>
            ) : (
              rates.map((rate) => (
                <tr key={rate.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">{rate.rate_date}</td>
                  <td className="px-4 py-3 whitespace-nowrap font-medium">
                    {rate.from_currency_details?.code || getCurrencyName(rate.from_currency)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap font-medium">
                    {rate.to_currency_details?.code || getCurrencyName(rate.to_currency)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">{parseFloat(rate.rate).toFixed(6)}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">{rate.rate_type}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">{rate.source || '-'}</td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {rate.is_active ? (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    <button
                      onClick={() => handleEdit(rate)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(rate.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

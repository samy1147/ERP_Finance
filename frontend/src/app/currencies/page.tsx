'use client';

import { useState, useEffect } from 'react';
import { currenciesAPI } from '@/services/api';
import { Currency } from '@/types';

export default function CurrenciesPage() {
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    symbol: '$',
    is_base: false,
  });

  useEffect(() => {
    loadCurrencies();
  }, []);

  const loadCurrencies = async () => {
    try {
      const response = await currenciesAPI.list();
      setCurrencies(response.data);
    } catch (error) {
      console.error('Error loading currencies:', error);
      alert('Failed to load currencies');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await currenciesAPI.update(editingId, formData);
      } else {
        await currenciesAPI.create(formData);
      }
      setShowForm(false);
      setEditingId(null);
      setFormData({ code: '', name: '', symbol: '$', is_base: false });
      loadCurrencies();
    } catch (error: any) {
      console.error('Error saving currency:', error);
      alert(`Failed to save currency: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleEdit = (currency: Currency) => {
    setFormData({
      code: currency.code,
      name: currency.name,
      symbol: currency.symbol,
      is_base: currency.is_base,
    });
    setEditingId(currency.id);
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this currency?')) return;
    try {
      await currenciesAPI.delete(id);
      loadCurrencies();
    } catch (error) {
      console.error('Error deleting currency:', error);
      alert('Failed to delete currency. It may be in use.');
    }
  };

  const resetForm = () => {
    setFormData({ code: '', name: '', symbol: '$', is_base: false });
    setEditingId(null);
    setShowForm(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-xl">Loading currencies...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Currencies</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          {showForm ? 'Cancel' : '+ Add Currency'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-6">
          <h2 className="text-xl font-bold mb-4">
            {editingId ? 'Edit Currency' : 'Add New Currency'}
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Currency Code (ISO 4217) *
                </label>
                <input
                  type="text"
                  maxLength={3}
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                  required
                  placeholder="USD"
                  disabled={!!editingId}
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Currency Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                  required
                  placeholder="United States Dollar"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Symbol *
                </label>
                <input
                  type="text"
                  value={formData.symbol}
                  onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                  required
                  placeholder="$"
                />
              </div>
              <div className="flex items-center mt-6">
                <input
                  type="checkbox"
                  id="is_base"
                  checked={formData.is_base}
                  onChange={(e) => setFormData({ ...formData, is_base: e.target.checked })}
                  className="mr-2 h-5 w-5"
                />
                <label htmlFor="is_base" className="text-gray-700 text-sm font-bold">
                  Set as Base Currency
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

      <div className="bg-white shadow-md rounded overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Code
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Symbol
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Base Currency
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {currencies.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No currencies found. Click "Add Currency" to create one.
                </td>
              </tr>
            ) : (
              currencies.map((currency) => (
                <tr key={currency.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium">
                    {currency.code}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {currency.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {currency.symbol}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {currency.is_base && (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Base Currency
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => handleEdit(currency)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(currency.id)}
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

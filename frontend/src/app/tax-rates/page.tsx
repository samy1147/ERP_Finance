'use client';

import { useState, useEffect } from 'react';
import { taxRatesAPI } from '@/services/api';
import { TaxRate } from '@/types';
import api from '@/lib/api';

export default function TaxRatesPage() {
  const [taxRates, setTaxRates] = useState<TaxRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [filterCountry, setFilterCountry] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    rate: '',
    country: 'AE',
    category: 'STANDARD',
    code: '',
    effective_from: '',
    effective_to: '',
    is_active: true,
  });

  const countries = [
    { code: 'AE', name: 'United Arab Emirates' },
    { code: 'SA', name: 'Saudi Arabia' },
    { code: 'EG', name: 'Egypt' },
    { code: 'IN', name: 'India' },
  ];

  const categories = [
    { code: 'STANDARD', name: 'Standard' },
    { code: 'ZERO', name: 'Zero Rated' },
    { code: 'EXEMPT', name: 'Exempt' },
    { code: 'RC', name: 'Reverse Charge' },
  ];

  useEffect(() => {
    loadTaxRates();
  }, [filterCountry]);

  const loadTaxRates = async () => {
    try {
      const response = await taxRatesAPI.list(filterCountry || undefined);
      setTaxRates(response.data);
    } catch (error) {
      console.error('Error loading tax rates:', error);
      alert('Failed to load tax rates');
    } finally {
      setLoading(false);
    }
  };

  const handleSeedPresets = async () => {
    if (!confirm('This will seed default VAT/tax rates for all countries. Continue?')) return;
    try {
      await taxRatesAPI.seedPresets();
      alert('Tax presets seeded successfully!');
      loadTaxRates();
    } catch (error: any) {
      console.error('Error seeding presets:', error);
      alert(`Failed to seed presets: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = {
        name: formData.name,
        rate: formData.rate,
        country: formData.country,
        category: formData.category,
        code: formData.code,
        is_active: formData.is_active,
      };
      if (formData.effective_from) payload.effective_from = formData.effective_from;
      if (formData.effective_to) payload.effective_to = formData.effective_to;

      if (editingId) {
        await api.patch(`/tax/rates/${editingId}/`, payload);
      } else {
        await api.post('/tax/rates/', payload);
      }
      resetForm();
      loadTaxRates();
    } catch (error: any) {
      console.error('Error saving tax rate:', error);
      alert(`Failed to save tax rate: ${error.response?.data?.detail || JSON.stringify(error.response?.data) || error.message}`);
    }
  };

  const handleEdit = (taxRate: TaxRate) => {
    setFormData({
      name: taxRate.name,
      rate: taxRate.rate.toString(),
      country: taxRate.country,
      category: taxRate.category,
      code: taxRate.code || '',
      effective_from: taxRate.effective_from || '',
      effective_to: taxRate.effective_to || '',
      is_active: taxRate.is_active,
    });
    setEditingId(taxRate.id);
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this tax rate?')) return;
    try {
      await api.delete(`/tax/rates/${id}/`);
      loadTaxRates();
    } catch (error) {
      console.error('Error deleting tax rate:', error);
      alert('Failed to delete tax rate. It may be in use.');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      rate: '',
      country: 'AE',
      category: 'STANDARD',
      code: '',
      effective_from: '',
      effective_to: '',
      is_active: true,
    });
    setEditingId(null);
    setShowForm(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-xl">Loading tax rates...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Tax Rates</h1>
        <div className="flex gap-2">
          <button
            onClick={handleSeedPresets}
            className="bg-green-600 hover:bg-green-800 text-white font-bold py-2 px-4 rounded"
          >
            🌱 Seed Default Rates
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            {showForm ? 'Cancel' : '+ Add Tax Rate'}
          </button>
        </div>
      </div>

      {/* Filter */}
      <div className="bg-gray-50 rounded px-6 py-4 mb-6">
        <div className="flex items-center gap-4">
          <label className="font-bold">Filter by Country:</label>
          <select
            value={filterCountry}
            onChange={(e) => setFilterCountry(e.target.value)}
            className="shadow border rounded py-2 px-3"
          >
            <option value="">All Countries</option>
            {countries.map((c) => (
              <option key={c.code} value={c.code}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-6">
          <h2 className="text-xl font-bold mb-4">
            {editingId ? 'Edit Tax Rate' : 'Add New Tax Rate'}
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                  required
                  placeholder="UAE VAT Standard"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Rate (%) *</label>
                <input
                  type="number"
                  step="0.001"
                  value={formData.rate}
                  onChange={(e) => setFormData({ ...formData, rate: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                  required
                  placeholder="5.000"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Code</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                  placeholder="VAT5"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Country *</label>
                <select
                  value={formData.country}
                  onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                  className="shadow border rounded w-full py-2 px-3 text-gray-700"
                  required
                >
                  {countries.map((c) => (
                    <option key={c.code} value={c.code}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Category *</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="shadow border rounded w-full py-2 px-3 text-gray-700"
                  required
                >
                  {categories.map((c) => (
                    <option key={c.code} value={c.code}>{c.name}</option>
                  ))}
                </select>
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
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Effective From</label>
                <input
                  type="date"
                  value={formData.effective_from}
                  onChange={(e) => setFormData({ ...formData, effective_from: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Effective To</label>
                <input
                  type="date"
                  value={formData.effective_to}
                  onChange={(e) => setFormData({ ...formData, effective_to: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                />
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
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rate</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Country</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Effective From</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {taxRates.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                  No tax rates found. Click "Seed Default Rates" to add common rates, or "Add Tax Rate" to create one.
                </td>
              </tr>
            ) : (
              taxRates.map((rate) => (
                <tr key={rate.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap font-medium">{rate.name}</td>
                  <td className="px-4 py-3 whitespace-nowrap">{rate.rate}%</td>
                  <td className="px-4 py-3 whitespace-nowrap">{rate.code || '-'}</td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {countries.find(c => c.code === rate.country)?.name || rate.country}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {categories.find(c => c.code === rate.category)?.name || rate.category}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    {rate.effective_from || '-'}
                  </td>
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

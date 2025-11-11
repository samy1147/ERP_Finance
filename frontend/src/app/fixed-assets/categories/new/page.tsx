'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Segment {
  id: number;
  code: string;
  alias: string;
}

export default function NewAssetCategoryPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [accounts, setAccounts] = useState<Segment[]>([]);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: '',
    major: '',
    minor: '',
    depreciation_method: 'STRAIGHT_LINE',
    useful_life_years: 5,
    min_value: '0.00',
    asset_account: '',
    is_active: true
  });

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await fetch('http://localhost:8007/api/accounts/');
      const data = await response.json();
      setAccounts(data);
    } catch (error) {
      console.error('Error fetching accounts:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8007/api/fixed-assets/categories/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        router.push('/assets/categories');
      } else {
        const error = await response.json();
        alert(`Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error creating category:', error);
      alert('Failed to create category');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">New Asset Category</h1>

      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
        <div className="grid grid-cols-2 gap-6">
          {/* Code */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Code *
            </label>
            <input
              type="text"
              required
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Description */}
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Major */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Major Category
            </label>
            <input
              type="text"
              value={formData.major}
              onChange={(e) => setFormData({ ...formData, major: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Minor */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Minor Category
            </label>
            <input
              type="text"
              value={formData.minor}
              onChange={(e) => setFormData({ ...formData, minor: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Depreciation Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Depreciation Method *
            </label>
            <select
              value={formData.depreciation_method}
              onChange={(e) => setFormData({ ...formData, depreciation_method: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="STRAIGHT_LINE">Straight Line</option>
              <option value="DECLINING_BALANCE">Declining Balance</option>
              <option value="SUM_OF_YEARS">Sum of Years Digits</option>
              <option value="UNITS_OF_PRODUCTION">Units of Production</option>
            </select>
          </div>

          {/* Useful Life */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Useful Life (Years) *
            </label>
            <input
              type="number"
              required
              min="1"
              value={formData.useful_life_years}
              onChange={(e) => setFormData({ ...formData, useful_life_years: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Min Value */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Value for Capitalization
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.min_value}
              onChange={(e) => setFormData({ ...formData, min_value: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Asset Account */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Asset Account *
            </label>
            <select
              required
              value={formData.asset_account}
              onChange={(e) => setFormData({ ...formData, asset_account: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Account</option>
              {accounts.map((acc) => (
                <option key={acc.id} value={acc.id}>
                  {acc.code} - {acc.alias}
                </option>
              ))}
            </select>
          </div>

          {/* Is Active */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
              Active
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-4 mt-6">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Creating...' : 'Create Category'}
          </button>
        </div>
      </form>
    </div>
  );
}

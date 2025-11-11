'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface AssetConfiguration {
  id?: number;
  minimum_capitalization_amount: string;
  base_currency?: number;
  base_currency_code?: string;
  auto_generate_asset_number: boolean;
  asset_number_prefix: string;
  next_asset_number: number;
  auto_calculate_depreciation: boolean;
  depreciation_posting_day: number;
  require_capitalization_approval: boolean;
  require_disposal_approval: boolean;
  updated_at?: string;
  updated_by_name?: string;
}

interface Currency {
  id: number;
  code: string;
  name: string;
}

export default function AssetSettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [config, setConfig] = useState<AssetConfiguration>({
    minimum_capitalization_amount: '1000.00',
    auto_generate_asset_number: true,
    asset_number_prefix: 'ASSET-',
    next_asset_number: 1,
    auto_calculate_depreciation: true,
    depreciation_posting_day: 1,
    require_capitalization_approval: false,
    require_disposal_approval: true,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [configRes, currenciesRes] = await Promise.all([
        fetch('http://localhost:8007/api/fixed-assets/configuration/'),
        fetch('http://localhost:8007/api/currencies/'),
      ]);
      
      const configData = await configRes.json();
      const currenciesData = await currenciesRes.json();
      
      setConfig(configData);
      setCurrencies(currenciesData);
    } catch (error) {
      console.error('Error fetching configuration:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      // Since it's a singleton, we can just PATCH to the base URL or use the ID if available
      const url = config.id 
        ? `http://localhost:8007/api/fixed-assets/configuration/${config.id}/`
        : 'http://localhost:8007/api/fixed-assets/configuration/1/'; // Singleton always has ID 1
      
      const response = await fetch(url, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        alert('Configuration saved successfully!');
        fetchData();
      } else {
        const error = await response.json();
        alert(`Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error saving configuration:', error);
      alert('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Asset Management Settings</h1>
          <p className="text-gray-500 mt-1">Configure asset management system parameters</p>
        </div>
        <Link
          href="/fixed-assets"
          className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
        >
          Back to Assets
        </Link>
      </div>

      <form onSubmit={handleSave} className="bg-white shadow-md rounded-lg p-6">
        {/* Capitalization Settings */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-blue-600 border-b pb-2">
            Capitalization Settings
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Base Currency *
              </label>
              <select
                required
                value={config.base_currency || ''}
                onChange={(e) => setConfig({ ...config, base_currency: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Base Currency</option>
                {currencies.map((curr) => (
                  <option key={curr.id} value={curr.id}>
                    {curr.code} - {curr.name}
                  </option>
                ))}
              </select>
              <p className="text-sm text-gray-500 mt-1">
                Currency for the minimum capitalization threshold
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Capitalization Amount *
              </label>
              <div className="flex items-center gap-2">
                {config.base_currency_code && (
                  <span className="text-gray-600 font-medium">{config.base_currency_code}</span>
                )}
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={config.minimum_capitalization_amount}
                  onChange={(e) => setConfig({ ...config, minimum_capitalization_amount: e.target.value })}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Assets below this amount (in base currency) will show a warning
              </p>
            </div>

            <div className="md:col-span-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.require_capitalization_approval}
                  onChange={(e) => setConfig({ ...config, require_capitalization_approval: e.target.checked })}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  Require approval before capitalizing assets
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Asset Numbering */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-blue-600 border-b pb-2">
            Asset Numbering
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.auto_generate_asset_number}
                  onChange={(e) => setConfig({ ...config, auto_generate_asset_number: e.target.checked })}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  Auto-generate asset numbers
                </span>
              </label>
            </div>

            {config.auto_generate_asset_number && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Asset Number Prefix
                  </label>
                  <input
                    type="text"
                    value={config.asset_number_prefix}
                    onChange={(e) => setConfig({ ...config, asset_number_prefix: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Next Asset Number
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={config.next_asset_number}
                    onChange={(e) => setConfig({ ...config, next_asset_number: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Next number: <strong>{config.asset_number_prefix}{config.next_asset_number}</strong>
                  </p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Depreciation Settings */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-blue-600 border-b pb-2">
            Depreciation Settings
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.auto_calculate_depreciation}
                  onChange={(e) => setConfig({ ...config, auto_calculate_depreciation: e.target.checked })}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  Automatically calculate depreciation monthly
                </span>
              </label>
            </div>

            {config.auto_calculate_depreciation && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Depreciation Posting Day
                </label>
                <input
                  type="number"
                  min="1"
                  max="28"
                  value={config.depreciation_posting_day}
                  onChange={(e) => setConfig({ ...config, depreciation_posting_day: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Day of the month to post depreciation (1-28)
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Disposal Settings */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-blue-600 border-b pb-2">
            Disposal Settings
          </h2>
          <div className="grid grid-cols-1 gap-6">
            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.require_disposal_approval}
                  onChange={(e) => setConfig({ ...config, require_disposal_approval: e.target.checked })}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  Require approval before disposing assets
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Last Updated Info */}
        {config.updated_at && (
          <div className="mb-6 p-4 bg-gray-50 rounded-md border border-gray-200">
            <p className="text-sm text-gray-600">
              Last updated: <strong>{new Date(config.updated_at).toLocaleString()}</strong>
              {config.updated_by_name && ` by ${config.updated_by_name}`}
            </p>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex justify-end gap-4 pt-4 border-t">
          <Link
            href="/fixed-assets"
            className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>

      {/* Help Text */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-800 mb-2">💡 Configuration Guide:</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• <strong>Minimum Capitalization Amount:</strong> Assets below this amount will show a warning suggesting expense treatment</li>
          <li>• <strong>Auto-generate Asset Numbers:</strong> System will automatically assign sequential asset numbers</li>
          <li>• <strong>Depreciation Day:</strong> Monthly depreciation will be posted on this day</li>
          <li>• <strong>Approvals:</strong> Enable workflow approvals for capitalization and disposal actions</li>
        </ul>
      </div>
    </div>
  );
}

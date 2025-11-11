'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface Category {
  id: number;
  code: string;
  name: string;
  depreciation_method: string;
  useful_life_years: number;
  salvage_value_percent: string;
  asset_account: number;
  accumulated_depreciation_account: number;
  depreciation_expense_account: number;
}

interface Location {
  id: number;
  code: string;
  name: string;
}

interface Currency {
  id: number;
  code: string;
  name: string;
}

interface Account {
  id: number;
  code: string;
  alias: string;
}

interface Supplier {
  id: number;
  code: string;
  name: string;
}

export default function NewAssetPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [minCapAmount, setMinCapAmount] = useState<number>(1000);
  const [baseCurrency, setBaseCurrency] = useState<string>('');
  const [showWarning, setShowWarning] = useState(false);
  const [warningMessage, setWarningMessage] = useState<string>('');
  const [convertedAmount, setConvertedAmount] = useState<string>('');
  
  const today = new Date().toISOString().split('T')[0];
  
  const [formData, setFormData] = useState({
    asset_number: '',
    name: '',
    description: '',
    serial_number: '',
    category: '',
    location: '',
    acquisition_date: today,
    acquisition_cost: '',
    currency: '',
    depreciation_method: 'STRAIGHT_LINE',
    useful_life_years: '5',
    salvage_value: '0.00',
    depreciation_start_date: today,
    asset_account: '',
    accumulated_depreciation_account: '',
    depreciation_expense_account: '',
    purchase_order: '',
    supplier: '',
    notes: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    // Auto-populate fields when category is selected
    if (formData.category) {
      const category = categories.find(c => c.id.toString() === formData.category);
      if (category) {
        setSelectedCategory(category);
        setFormData(prev => ({
          ...prev,
          depreciation_method: category.depreciation_method,
          useful_life_years: category.useful_life_years.toString(),
          asset_account: category.asset_account?.toString() || '',
          accumulated_depreciation_account: category.accumulated_depreciation_account?.toString() || '',
          depreciation_expense_account: category.depreciation_expense_account?.toString() || '',
        }));
      }
    }
  }, [formData.category, categories]);

  useEffect(() => {
    // Check if acquisition cost is below minimum capitalization amount with currency conversion
    const checkThreshold = async () => {
      if (formData.acquisition_cost && formData.currency) {
        const cost = parseFloat(formData.acquisition_cost);
        if (cost > 0) {
          try {
            const response = await fetch('http://localhost:8007/api/fixed-assets/configuration/check_threshold/', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                amount: cost,
                currency_id: parseInt(formData.currency),
              }),
            });

            const data = await response.json();
            
            if (data.error) {
              console.error('Error checking threshold:', data.error);
              setShowWarning(false);
              return;
            }

            setShowWarning(!data.meets_threshold);
            setWarningMessage(data.warning_message || '');
            setConvertedAmount(data.amount_in_base_currency || '');
            setBaseCurrency(data.base_currency || '');
            
          } catch (error) {
            console.error('Error checking threshold:', error);
            setShowWarning(false);
          }
        } else {
          setShowWarning(false);
        }
      } else {
        setShowWarning(false);
      }
    };

    checkThreshold();
  }, [formData.acquisition_cost, formData.currency]);

  const fetchData = async () => {
    try {
      const [categoriesRes, locationsRes, currenciesRes, accountsRes, suppliersRes, configRes] = await Promise.all([
        fetch('http://localhost:8007/api/fixed-assets/categories/'),
        fetch('http://localhost:8007/api/fixed-assets/locations/'),
        fetch('http://localhost:8007/api/currencies/'),
        fetch('http://localhost:8007/api/accounts/'),
        fetch('http://localhost:8007/api/ap/vendors/'),
        fetch('http://localhost:8007/api/fixed-assets/configuration/'),
      ]);

      const categoriesData = await categoriesRes.json();
      const locationsData = await locationsRes.json();
      const currenciesData = await currenciesRes.json();
      const accountsData = await accountsRes.json();
      const suppliersData = await suppliersRes.json();
      const configData = await configRes.json();

      setCategories(categoriesData);
      setLocations(locationsData);
      setCurrencies(currenciesData);
      setAccounts(accountsData);
      setSuppliers(suppliersData);
      
      // Set minimum capitalization amount and base currency from configuration
      if (configData.minimum_capitalization_amount) {
        setMinCapAmount(parseFloat(configData.minimum_capitalization_amount));
      }
      if (configData.base_currency_code) {
        setBaseCurrency(configData.base_currency_code);
      }

      // Set default currency to USD if available
      const usdCurrency = currenciesData.find((c: Currency) => c.code === 'USD');
      if (usdCurrency) {
        setFormData(prev => ({ ...prev, currency: usdCurrency.id.toString() }));
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      alert('Failed to fetch data');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Prepare data for submission
      const submitData = {
        ...formData,
        category: parseInt(formData.category),
        location: parseInt(formData.location),
        currency: parseInt(formData.currency),
        useful_life_years: parseFloat(formData.useful_life_years),
        salvage_value: parseFloat(formData.salvage_value),
        acquisition_cost: parseFloat(formData.acquisition_cost),
        asset_account: parseInt(formData.asset_account),
        accumulated_depreciation_account: parseInt(formData.accumulated_depreciation_account),
        depreciation_expense_account: parseInt(formData.depreciation_expense_account),
        supplier: formData.supplier ? parseInt(formData.supplier) : null,
      };

      const response = await fetch('http://localhost:8007/api/fixed-assets/assets/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData),
      });

      if (response.ok) {
        alert('Asset created successfully!');
        router.push('/fixed-assets');
      } else {
        const error = await response.json();
        alert(`Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error creating asset:', error);
      alert('Failed to create asset');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">New Fixed Asset</h1>
        <Link
          href="/fixed-assets"
          className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
        >
          Back to Assets
        </Link>
      </div>

      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
        {/* Asset Identification */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-blue-600 border-b pb-2">
            Asset Identification
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Asset Number *
              </label>
              <input
                type="text"
                required
                value={formData.asset_number}
                onChange={(e) => setFormData({ ...formData, asset_number: e.target.value })}
                placeholder="e.g., ASSET-001"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Asset Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Dell Laptop XPS 15"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                placeholder="Additional details about the asset..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Serial Number
              </label>
              <input
                type="text"
                value={formData.serial_number}
                onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
                placeholder="e.g., SN123456789"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Classification */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-blue-600 border-b pb-2">
            Classification
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category *
              </label>
              <select
                required
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.code} - {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location *
              </label>
              <select
                required
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Location</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.code} - {loc.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Financial Details */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-blue-600 border-b pb-2">
            Financial Details
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Acquisition Date *
              </label>
              <input
                type="date"
                required
                value={formData.acquisition_date}
                onChange={(e) => setFormData({ ...formData, acquisition_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Acquisition Cost *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.acquisition_cost}
                onChange={(e) => setFormData({ ...formData, acquisition_cost: e.target.value })}
                placeholder="0.00"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {showWarning && warningMessage && (
                <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <p className="text-sm text-yellow-800 font-semibold mb-1">
                    ⚠️ Below Capitalization Threshold
                  </p>
                  <p className="text-sm text-yellow-700">
                    {warningMessage}
                  </p>
                  {convertedAmount && baseCurrency && (
                    <p className="text-sm text-yellow-600 mt-1">
                      💱 Converted amount: {baseCurrency} {parseFloat(convertedAmount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  )}
                  <p className="text-xs text-yellow-600 mt-2">
                    Consider expensing this item instead of capitalizing it as a fixed asset.
                  </p>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Currency *
              </label>
              <select
                required
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Currency</option>
                {currencies.map((curr) => (
                  <option key={curr.id} value={curr.id}>
                    {curr.code} - {curr.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Depreciation Settings */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-blue-600 border-b pb-2">
            Depreciation Settings
          </h2>
          {selectedCategory && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
              <p className="text-sm text-blue-800">
                💡 Settings auto-populated from category: <strong>{selectedCategory.name}</strong>
              </p>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Depreciation Method *
              </label>
              <select
                required
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Useful Life (Years) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                value={formData.useful_life_years}
                onChange={(e) => setFormData({ ...formData, useful_life_years: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Salvage Value
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.salvage_value}
                onChange={(e) => setFormData({ ...formData, salvage_value: e.target.value })}
                placeholder="0.00"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Depreciation Start Date *
              </label>
              <input
                type="date"
                required
                value={formData.depreciation_start_date}
                onChange={(e) => setFormData({ ...formData, depreciation_start_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* GL Accounts */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-blue-600 border-b pb-2">
            GL Account Assignments
          </h2>
          {selectedCategory && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
              <p className="text-sm text-blue-800">
                💡 Accounts auto-populated from category. You can override if needed.
              </p>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Accumulated Depreciation Account *
              </label>
              <select
                required
                value={formData.accumulated_depreciation_account}
                onChange={(e) => setFormData({ ...formData, accumulated_depreciation_account: e.target.value })}
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Depreciation Expense Account *
              </label>
              <select
                required
                value={formData.depreciation_expense_account}
                onChange={(e) => setFormData({ ...formData, depreciation_expense_account: e.target.value })}
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
          </div>
        </div>

        {/* Additional Information */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-blue-600 border-b pb-2">
            Additional Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Purchase Order
              </label>
              <input
                type="text"
                value={formData.purchase_order}
                onChange={(e) => setFormData({ ...formData, purchase_order: e.target.value })}
                placeholder="e.g., PO-001"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Supplier
              </label>
              <select
                value={formData.supplier}
                onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Supplier</option>
                {suppliers.map((sup) => (
                  <option key={sup.id} value={sup.id}>
                    {sup.code} - {sup.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                placeholder="Additional notes about this asset..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

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
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Creating...' : 'Create Asset'}
          </button>
        </div>
      </form>

      {/* Help Text */}
      <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold text-gray-800 mb-2">💡 Tips:</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Assets are created in <strong>DRAFT</strong> status by default</li>
          <li>• Use the <strong>Capitalize</strong> action to activate the asset and post to GL</li>
          <li>• Depreciation settings are auto-populated from the selected category</li>
          <li>• GL accounts can be overridden if needed for specific assets</li>
          <li>• Ensure the acquisition date is before the depreciation start date</li>
          <li>• <strong>Minimum capitalization threshold:</strong> {baseCurrency} {minCapAmount.toLocaleString()} (configured in <Link href="/fixed-assets/settings" className="text-blue-600 hover:underline">Settings</Link>)</li>
          <li>• 💱 <strong>Multi-currency support:</strong> Threshold is automatically converted based on exchange rates</li>
        </ul>
      </div>
    </div>
  );
}

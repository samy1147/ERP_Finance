'use client';

import { useState, useEffect } from 'react';
import { fxConfigAPI, currenciesAPI, accountsAPI } from '@/services/api';
import { Currency, Account, FXGainLossAccount } from '@/types';
import { Globe, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

export default function FXConfigPage() {
  const [baseCurrency, setBaseCurrency] = useState<Currency | null>(null);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [fxAccounts, setFxAccounts] = useState<FXGainLossAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [formData, setFormData] = useState({
    account: '',
    gain_loss_type: 'REALIZED_GAIN' as 'REALIZED_GAIN' | 'REALIZED_LOSS' | 'UNREALIZED_GAIN' | 'UNREALIZED_LOSS',
    description: '',
  });

  const gainLossTypes = [
    { 
      code: 'REALIZED_GAIN', 
      name: 'Realized FX Gain',
      description: 'Gains from settled foreign currency transactions',
      icon: TrendingUp,
      color: 'text-green-600 bg-green-100'
    },
    { 
      code: 'REALIZED_LOSS', 
      name: 'Realized FX Loss',
      description: 'Losses from settled foreign currency transactions',
      icon: TrendingDown,
      color: 'text-red-600 bg-red-100'
    },
    { 
      code: 'UNREALIZED_GAIN', 
      name: 'Unrealized FX Gain',
      description: 'Potential gains from revaluation of foreign currency balances',
      icon: TrendingUp,
      color: 'text-emerald-600 bg-emerald-50'
    },
    { 
      code: 'UNREALIZED_LOSS', 
      name: 'Unrealized FX Loss',
      description: 'Potential losses from revaluation of foreign currency balances',
      icon: TrendingDown,
      color: 'text-orange-600 bg-orange-50'
    },
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [baseCurrencyRes, currenciesRes, accountsRes, fxAccountsRes] = await Promise.all([
        fxConfigAPI.baseCurrency(),
        currenciesAPI.list(),
        accountsAPI.list(),
        fxConfigAPI.gainLossAccounts.list(),
      ]);
      
      setBaseCurrency(baseCurrencyRes.data);
      setCurrencies(currenciesRes.data);
      setAccounts(accountsRes.data);
      setFxAccounts(fxAccountsRes.data);
    } catch (error) {
      console.error('Error loading FX configuration:', error);
      alert('Failed to load FX configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSetBaseCurrency = async (currencyId: number) => {
    if (!confirm('Changing the base currency will affect all financial reporting. Are you sure?')) {
      return;
    }
    
    try {
      // First, unset all currencies
      const unsetPromises = currencies.map(c => 
        currenciesAPI.update(c.id, { ...c, is_base: false })
      );
      await Promise.all(unsetPromises);

      // Then set the selected currency as base
      await currenciesAPI.update(currencyId, { is_base: true });
      
      alert('Base currency updated successfully!');
      loadData();
    } catch (error: any) {
      console.error('Error setting base currency:', error);
      alert(`Failed to set base currency: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        account: parseInt(formData.account),
        gain_loss_type: formData.gain_loss_type,
        description: formData.description,
      };

      if (editingId) {
        await fxConfigAPI.gainLossAccounts.update(editingId, payload);
      } else {
        await fxConfigAPI.gainLossAccounts.create(payload);
      }
      
      resetForm();
      loadData();
    } catch (error: any) {
      console.error('Error saving FX account:', error);
      alert(`Failed to save: ${error.response?.data?.detail || JSON.stringify(error.response?.data) || error.message}`);
    }
  };

  const handleEdit = (fxAccount: FXGainLossAccount) => {
    setFormData({
      account: fxAccount.account.toString(),
      gain_loss_type: fxAccount.gain_loss_type,
      description: fxAccount.description || '',
    });
    setEditingId(fxAccount.id);
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this FX account configuration?')) return;
    try {
      await fxConfigAPI.gainLossAccounts.delete(id);
      loadData();
    } catch (error) {
      console.error('Error deleting FX account:', error);
      alert('Failed to delete FX account configuration');
    }
  };

  const resetForm = () => {
    setFormData({
      account: '',
      gain_loss_type: 'REALIZED_GAIN',
      description: '',
    });
    setEditingId(null);
    setShowForm(false);
  };

  const getAccountName = (accountId: number) => {
    const account = accounts.find(a => a.id === accountId);
    return account ? `${account.code} - ${account.name}` : accountId.toString();
  };

  const getConfiguredTypes = () => {
    return fxAccounts.map(fa => fa.gain_loss_type);
  };

  const getMissingConfigurations = () => {
    const configured = getConfiguredTypes();
    return gainLossTypes.filter(type => !configured.includes(type.code as any));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-xl">Loading FX configuration...</div>
      </div>
    );
  }

  const missingConfigs = getMissingConfigurations();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">FX Configuration</h1>
      </div>

      {/* Warning if not fully configured */}
      {missingConfigs.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-yellow-400 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800">
                Incomplete FX Configuration
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>The following FX account types are not configured:</p>
                <ul className="list-disc ml-5 mt-1">
                  {missingConfigs.map(type => (
                    <li key={type.code}>{type.name}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Base Currency Section */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="flex items-center mb-4">
          <Globe className="h-6 w-6 text-blue-600 mr-2" />
          <h2 className="text-2xl font-bold">Base Currency</h2>
        </div>
        
        {baseCurrency ? (
          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Your company's base currency is:</p>
                <div className="flex items-center gap-3">
                  <span className="text-4xl font-bold text-blue-900">
                    {baseCurrency.symbol}
                  </span>
                  <div>
                    <p className="text-2xl font-bold text-blue-900">
                      {baseCurrency.code}
                    </p>
                    <p className="text-sm text-blue-700">
                      {baseCurrency.name}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-gray-600 mt-3">
                  All financial reports are prepared in this currency. Foreign currency transactions are converted to {baseCurrency.code}.
                </p>
              </div>
              <div>
                <button
                  onClick={() => setShowForm(false)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm"
                >
                  Change Base Currency
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6">
            <p className="text-red-800 font-medium mb-3">
              ⚠️ No base currency is set! Please select one:
            </p>
            <div className="grid grid-cols-4 gap-3">
              {currencies.map(currency => (
                <button
                  key={currency.id}
                  onClick={() => handleSetBaseCurrency(currency.id)}
                  className="bg-white hover:bg-gray-50 border-2 border-gray-300 rounded-lg p-3 text-left"
                >
                  <div className="font-bold text-lg">{currency.code}</div>
                  <div className="text-xs text-gray-600">{currency.name}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Change Base Currency Dropdown (shown on button click) */}
        {baseCurrency && showForm === false && (
          <details className="mt-4">
            <summary className="cursor-pointer text-blue-600 text-sm hover:text-blue-800">
              Click to change base currency...
            </summary>
            <div className="mt-3 grid grid-cols-4 gap-3">
              {currencies.map(currency => (
                <button
                  key={currency.id}
                  onClick={() => handleSetBaseCurrency(currency.id)}
                  disabled={currency.id === baseCurrency?.id}
                  className={`border-2 rounded-lg p-3 text-left ${
                    currency.id === baseCurrency?.id
                      ? 'bg-blue-100 border-blue-400 cursor-not-allowed'
                      : 'bg-white hover:bg-gray-50 border-gray-300'
                  }`}
                >
                  <div className="font-bold text-lg">{currency.code}</div>
                  <div className="text-xs text-gray-600">{currency.name}</div>
                  {currency.id === baseCurrency?.id && (
                    <div className="text-xs text-blue-600 mt-1">Current</div>
                  )}
                </button>
              ))}
            </div>
          </details>
        )}
      </div>

      {/* FX Gain/Loss Accounts Section */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">FX Gain/Loss Accounts</h2>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            {showForm ? 'Cancel' : '+ Configure Account'}
          </button>
        </div>

        <p className="text-gray-600 mb-6">
          Configure which GL accounts to use for foreign exchange gains and losses.
          These accounts are automatically used when FX differences occur.
        </p>

        {/* Form */}
        {showForm && (
          <div className="bg-gray-50 rounded-lg p-6 mb-6 border-2 border-gray-200">
            <h3 className="text-lg font-bold mb-4">
              {editingId ? 'Edit FX Account Configuration' : 'Add FX Account Configuration'}
            </h3>
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-gray-700 text-sm font-bold mb-2">
                    Type *
                  </label>
                  <select
                    value={formData.gain_loss_type}
                    onChange={(e) => setFormData({ ...formData, gain_loss_type: e.target.value as any })}
                    className="shadow border rounded w-full py-2 px-3 text-gray-700"
                    required
                  >
                    {gainLossTypes.map(type => (
                      <option key={type.code} value={type.code}>
                        {type.name} - {type.description}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-700 text-sm font-bold mb-2">
                    GL Account *
                  </label>
                  <select
                    value={formData.account}
                    onChange={(e) => setFormData({ ...formData, account: e.target.value })}
                    className="shadow border rounded w-full py-2 px-3 text-gray-700"
                    required
                  >
                    <option value="">Select Account...</option>
                    {accounts
                      .filter(a => a.type === 'IN' || a.type === 'EX') // Income or Expense accounts
                      .map(account => (
                        <option key={account.id} value={account.id}>
                          {account.code} - {account.name}
                        </option>
                      ))}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="block text-gray-700 text-sm font-bold mb-2">
                    Description (Optional)
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                    rows={2}
                    placeholder="Additional notes about this configuration..."
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

        {/* Configuration Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {gainLossTypes.map(type => {
            const Icon = type.icon;
            const config = fxAccounts.find(fa => fa.gain_loss_type === type.code);
            
            return (
              <div
                key={type.code}
                className={`border-2 rounded-lg p-5 ${
                  config ? 'border-green-300 bg-green-50' : 'border-gray-300 bg-gray-50'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className={`p-2 rounded-lg ${type.color}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900">{type.name}</h3>
                      <p className="text-xs text-gray-600">{type.description}</p>
                    </div>
                  </div>
                </div>
                
                {config ? (
                  <div className="mt-3 bg-white rounded p-3 border border-gray-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Configured Account:</p>
                        <p className="font-mono text-sm font-medium text-gray-900">
                          {config.account_details 
                            ? `${config.account_details.code} - ${config.account_details.name}`
                            : getAccountName(config.account)
                          }
                        </p>
                        {config.description && (
                          <p className="text-xs text-gray-600 mt-2">{config.description}</p>
                        )}
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleEdit(config)}
                          className="text-blue-600 hover:text-blue-800 text-xs px-2 py-1"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(config.id)}
                          className="text-red-600 hover:text-red-800 text-xs px-2 py-1"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="mt-3 bg-yellow-50 rounded p-3 border border-yellow-200">
                    <p className="text-sm text-yellow-800">
                      ⚠️ Not configured - FX transactions will fail
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-bold text-blue-900 mb-3">💡 How FX Accounts Work</h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p>
            <strong>Realized Gains/Losses:</strong> Occur when you actually settle a transaction. 
            For example, if you invoice USD $100 when the rate is 3.67 AED (= 367 AED), 
            but receive payment when the rate is 3.70 AED (= 370 AED), you have a realized gain of 3 AED.
          </p>
          <p>
            <strong>Unrealized Gains/Losses:</strong> Occur at period-end when you revalue foreign currency balances. 
            These are "paper" gains/losses that haven't been settled yet. For example, outstanding foreign 
            currency receivables or payables are revalued at current exchange rates.
          </p>
          <p className="pt-2 border-t border-blue-200">
            <strong>Best Practice:</strong> Configure all four account types before processing multi-currency transactions.
            Use Income accounts for gains and Expense accounts for losses.
          </p>
        </div>
      </div>
    </div>
  );
}

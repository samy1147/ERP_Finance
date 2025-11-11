'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Asset {
  id: number;
  asset_number: string;
  name: string;
  description?: string;
  serial_number?: string;
  category: number;
  category_name?: string;
  location: number;
  location_name?: string;
  acquisition_date: string;
  acquisition_cost: string;
  currency_code?: string;
  status: string;
  net_book_value: string;
  total_depreciation: string;
  supplier_name?: string;
}

interface Category {
  id: number;
  code: string;
  name: string;
}

interface Location {
  id: number;
  code: string;
  name: string;
}

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [showCapitalizeModal, setShowCapitalizeModal] = useState(false);
  const [showDisposeModal, setShowDisposeModal] = useState(false);
  
  const [disposeData, setDisposeData] = useState({
    disposal_date: new Date().toISOString().split('T')[0],
    disposal_method: 'SOLD',
    disposal_proceeds: '',
    disposal_notes: '',
  });

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const fetchData = async () => {
    try {
      let url = 'http://localhost:8007/api/fixed-assets/assets/';
      if (statusFilter !== 'ALL') {
        url += `?status=${statusFilter}`;
      }
      
      const [assetsRes, categoriesRes, locationsRes] = await Promise.all([
        fetch(url),
        fetch('http://localhost:8007/api/fixed-assets/categories/'),
        fetch('http://localhost:8007/api/fixed-assets/locations/'),
      ]);

      const assetsData = await assetsRes.json();
      const categoriesData = await categoriesRes.json();
      const locationsData = await locationsRes.json();

      setAssets(assetsData);
      setCategories(categoriesData);
      setLocations(locationsData);
    } catch (error) {
      console.error('Error fetching data:', error);
      alert('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleCapitalize = async () => {
    if (!selectedAsset) return;

    try {
      const response = await fetch(
        `http://localhost:8007/api/fixed-assets/assets/${selectedAsset.id}/capitalize/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            capitalization_date: new Date().toISOString().split('T')[0],
          }),
        }
      );

      if (response.ok) {
        alert('Asset capitalized successfully! Journal entry posted to GL.');
        setShowCapitalizeModal(false);
        setSelectedAsset(null);
        fetchData();
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to capitalize asset');
      }
    } catch (error) {
      console.error(error);
      alert('Network error');
    }
  };

  const handleDispose = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAsset) return;

    try {
      const response = await fetch(
        `http://localhost:8007/api/fixed-assets/assets/${selectedAsset.id}/dispose/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(disposeData),
        }
      );

      if (response.ok) {
        alert('Asset disposed successfully! Disposal journal entry posted to GL.');
        setShowDisposeModal(false);
        setSelectedAsset(null);
        fetchData();
        setDisposeData({
          disposal_date: new Date().toISOString().split('T')[0],
          disposal_method: 'SOLD',
          disposal_proceeds: '',
          disposal_notes: '',
        });
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to dispose asset');
      }
    } catch (error) {
      console.error(error);
      alert('Network error');
    }
  };

  const filteredAssets = assets.filter(asset => {
    const matchesSearch =
      asset.asset_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.serial_number?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'ALL' || asset.status === statusFilter;
    const matchesCategory = categoryFilter === 'ALL' || asset.category.toString() === categoryFilter;
    
    return matchesSearch && matchesStatus && matchesCategory;
  });

  const stats = {
    total: assets.length,
    active: assets.filter(a => a.status === 'ACTIVE').length,
    draft: assets.filter(a => a.status === 'DRAFT').length,
    totalValue: assets.reduce((sum, a) => sum + parseFloat(a.net_book_value || '0'), 0),
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      'DRAFT': 'bg-gray-100 text-gray-800',
      'ACTIVE': 'bg-green-100 text-green-800',
      'DISPOSED': 'bg-red-100 text-red-800',
      'RETIRED': 'bg-yellow-100 text-yellow-800'
    };
    return badges[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Asset Register</h1>
          <p className="text-gray-500 mt-1">Manage your fixed assets and equipment</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/fixed-assets/approvals"
            className="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700 font-semibold"
          >
            ✓ Approvals
          </Link>
          <Link
            href="/fixed-assets/transfers"
            className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
          >
            Transfer
          </Link>
          <Link
            href="/fixed-assets/adjustments"
            className="bg-teal-600 text-white px-4 py-2 rounded hover:bg-teal-700"
          >
            Adjustments
          </Link>
          <Link
            href="/fixed-assets/retirements"
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Retirements
          </Link>
          <Link
            href="/fixed-assets/categories"
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
          >
            Categories
          </Link>
          <Link
            href="/fixed-assets/locations"
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
          >
            Locations
          </Link>
          <Link
            href="/fixed-assets/depreciation"
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
          >
            Depreciation
          </Link>
          <Link
            href="/fixed-assets/settings"
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
          >
            ⚙️ Settings
          </Link>
          <Link
            href="/fixed-assets/new"
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            + New Asset
          </Link>
          <Link
            href="/fixed-assets/from-invoice"
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            📄 From AP Invoice
          </Link>
          <Link
            href="/fixed-assets/from-grn"
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            📦 From GRN
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500 mb-1">Total Assets</div>
          <div className="text-3xl font-bold">{stats.total}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500 mb-1">Active Assets</div>
          <div className="text-3xl font-bold text-green-600">{stats.active}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500 mb-1">Draft Assets</div>
          <div className="text-3xl font-bold text-yellow-600">{stats.draft}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500 mb-1">Total Net Book Value</div>
          <div className="text-2xl font-bold">
            ${stats.totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      <div className="mb-4 flex gap-4">
        <input
          type="text"
          placeholder="Search assets..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border rounded-lg"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="ALL">All Status</option>
          <option value="DRAFT">Draft</option>
          <option value="ACTIVE">Active</option>
          <option value="DISPOSED">Disposed</option>
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="ALL">All Categories</option>
          {categories.map(cat => (
            <option key={cat.id} value={cat.id.toString()}>
              {cat.name}
            </option>
          ))}
        </select>
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Asset Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Location
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acquisition Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Net Book Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAssets.map((asset) => (
                <tr key={asset.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {asset.asset_number}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div>
                      <div className="font-medium">{asset.name}</div>
                      {asset.serial_number && (
                        <div className="text-xs text-gray-500">SN: {asset.serial_number}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {asset.category_name || asset.category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {asset.location_name || asset.location}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${parseFloat(asset.acquisition_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${parseFloat(asset.net_book_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(asset.status)}`}>
                      {asset.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex gap-2">
                      <Link
                        href={`/fixed-assets/${asset.id}`}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                      >
                        View
                      </Link>
                      {asset.status === 'DRAFT' && (
                        <button
                          onClick={() => {
                            setSelectedAsset(asset);
                            setShowCapitalizeModal(true);
                          }}
                          className="text-green-600 hover:text-green-900 font-medium"
                        >
                          Capitalize
                        </button>
                      )}
                      {asset.status === 'ACTIVE' && (
                        <button
                          onClick={() => {
                            setSelectedAsset(asset);
                            setShowDisposeModal(true);
                          }}
                          className="text-red-600 hover:text-red-900 font-medium"
                        >
                          Dispose
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredAssets.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No assets found
          </div>
        )}
      </div>

      <div className="mt-4 text-sm text-gray-600">
        Total Assets: {filteredAssets.length}
      </div>

      {/* Capitalize Modal */}
      {showCapitalizeModal && selectedAsset && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Capitalize Asset</h2>
            <div className="mb-4">
              <p className="font-medium">{selectedAsset.name}</p>
              <p className="text-sm text-gray-500">{selectedAsset.asset_number}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-md mb-4">
              <p className="text-sm font-medium text-blue-900">Journal Entry Preview:</p>
              <p className="text-sm text-blue-700 mt-2">
                DR: Fixed Assets - ${parseFloat(selectedAsset.acquisition_cost).toFixed(2)}
              </p>
              <p className="text-sm text-blue-700">
                CR: Accounts Payable - ${parseFloat(selectedAsset.acquisition_cost).toFixed(2)}
              </p>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowCapitalizeModal(false);
                  setSelectedAsset(null);
                }}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCapitalize}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Capitalize & Post to GL
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dispose Modal */}
      {showDisposeModal && selectedAsset && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Dispose Asset</h2>
            <div className="mb-4">
              <p className="font-medium">{selectedAsset.name}</p>
              <p className="text-sm text-gray-500">
                Net Book Value: ${parseFloat(selectedAsset.net_book_value).toFixed(2)}
              </p>
            </div>
            <form onSubmit={handleDispose} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Disposal Date</label>
                <input
                  type="date"
                  value={disposeData.disposal_date}
                  onChange={(e) => setDisposeData({ ...disposeData, disposal_date: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Disposal Method</label>
                <select
                  value={disposeData.disposal_method}
                  onChange={(e) => setDisposeData({ ...disposeData, disposal_method: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="SOLD">Sold</option>
                  <option value="SCRAPPED">Scrapped</option>
                  <option value="DONATED">Donated</option>
                  <option value="LOST">Lost/Stolen</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Disposal Proceeds</label>
                <input
                  type="number"
                  step="0.01"
                  value={disposeData.disposal_proceeds}
                  onChange={(e) => setDisposeData({ ...disposeData, disposal_proceeds: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="0.00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  value={disposeData.disposal_notes}
                  onChange={(e) => setDisposeData({ ...disposeData, disposal_notes: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  rows={3}
                  placeholder="Disposal notes..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowDisposeModal(false);
                    setSelectedAsset(null);
                  }}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Dispose Asset
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

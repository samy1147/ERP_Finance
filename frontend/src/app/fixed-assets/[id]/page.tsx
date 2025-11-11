'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';

interface Asset {
  id: number;
  asset_number: string;
  name: string;
  description: string;
  status: 'CIP' | 'CAPITALIZED' | 'RETIRED';
  category: number;
  category_name?: string;
  location: number;
  location_name?: string;
  acquisition_cost: string;
  accumulated_depreciation: string;
  net_book_value: string;
  useful_life_months: number;
  capitalization_date: string | null;
  depreciation_start_date: string | null;
}

interface AssetAction {
  id: number;
  type: 'transfer' | 'adjustment' | 'retirement' | 'approval';
  date: string;
  description: string;
  status: string;
  details: any;
}

export default function AssetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const assetId = params.id;

  const [asset, setAsset] = useState<Asset | null>(null);
  const [actions, setActions] = useState<AssetAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [showActionModal, setShowActionModal] = useState(false);
  const [actionType, setActionType] = useState<string>('');
  const [actionData, setActionData] = useState<any>({});
  const [processing, setProcessing] = useState(false);
  const [categories, setCategories] = useState<any[]>([]);
  const [locations, setLocations] = useState<any[]>([]);

  useEffect(() => {
    if (assetId) {
      fetchAsset();
      fetchActions();
      fetchCategories();
      fetchLocations();
    }
  }, [assetId]);

  const fetchAsset = async () => {
    try {
      const response = await fetch(`http://localhost:8007/api/fixed-assets/assets/${assetId}/`);
      if (response.ok) {
        const data = await response.json();
        setAsset(data);
      }
    } catch (error) {
      console.error('Error fetching asset:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchActions = async () => {
    try {
      // Fetch all action types
      const [transfers, adjustments, retirements, approvals] = await Promise.all([
        fetch(`http://localhost:8007/api/fixed-assets/transfers/?asset=${assetId}`).then(r => r.json()),
        fetch(`http://localhost:8007/api/fixed-assets/adjustments/?asset=${assetId}`).then(r => r.json()),
        fetch(`http://localhost:8007/api/fixed-assets/retirements/?asset=${assetId}`).then(r => r.json()),
        fetch(`http://localhost:8007/api/fixed-assets/approvals/?asset=${assetId}`).then(r => r.json()),
      ]);

      const allActions: AssetAction[] = [
        ...transfers.map((t: any) => ({
          id: t.id,
          type: 'transfer' as const,
          date: t.transfer_date,
          description: `Transfer to ${t.to_location}`,
          status: t.approval_status,
          details: t,
        })),
        ...adjustments.map((a: any) => ({
          id: a.id,
          type: 'adjustment' as const,
          date: a.adjustment_date,
          description: `${a.adjustment_type} adjustment`,
          status: a.approval_status,
          details: a,
        })),
        ...retirements.map((r: any) => ({
          id: r.id,
          type: 'retirement' as const,
          date: r.retirement_date,
          description: `Retirement - ${r.retirement_type}`,
          status: r.approval_status,
          details: r,
        })),
        ...approvals.map((a: any) => ({
          id: a.id,
          type: 'approval' as const,
          date: a.requested_at,
          description: `${a.operation_type} request`,
          status: a.approval_status,
          details: a,
        })),
      ];

      allActions.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      setActions(allActions);
    } catch (error) {
      console.error('Error fetching actions:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch('http://localhost:8007/api/fixed-assets/categories/');
      if (response.ok) {
        const data = await response.json();
        setCategories(data);
      }
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await fetch('http://localhost:8007/api/fixed-assets/locations/');
      if (response.ok) {
        const data = await response.json();
        setLocations(data);
      }
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const openActionModal = (type: string) => {
    setActionType(type);
    setActionData({});
    setShowActionModal(true);
  };

  const handleSubmitAction = async () => {
    if (!asset) return;

    try {
      setProcessing(true);
      let url = '';
      let body: any = {};

      switch (actionType) {
        case 'capitalize':
          url = `http://localhost:8007/api/fixed-assets/assets/${asset.id}/submit_for_capitalization/`;
          body = {
            capitalization_date: actionData.capitalization_date || new Date().toISOString().split('T')[0],
            notes: actionData.notes || '',
          };
          break;

        case 'transfer':
          url = `http://localhost:8007/api/fixed-assets/assets/${asset.id}/transfer/`;
          body = {
            to_location: actionData.to_location,
            reason: actionData.reason || '',
            transfer_date: actionData.transfer_date || new Date().toISOString().split('T')[0],
          };
          break;

        case 'recategorize':
          url = `http://localhost:8007/api/fixed-assets/assets/${asset.id}/recategorize/`;
          body = {
            new_category: actionData.new_category,
            reason: actionData.reason || '',
          };
          break;

        case 'adjust_cost':
          url = `http://localhost:8007/api/fixed-assets/assets/${asset.id}/adjust_cost/`;
          body = {
            new_cost: actionData.new_cost,
            reason: actionData.reason || '',
          };
          break;

        case 'adjust_useful_life':
          url = `http://localhost:8007/api/fixed-assets/assets/${asset.id}/adjust_useful_life/`;
          body = {
            new_useful_life: actionData.new_useful_life,
            reason: actionData.reason || '',
          };
          break;

        case 'adjust_depreciation':
          url = `http://localhost:8007/api/fixed-assets/assets/${asset.id}/manual_depreciation_adjustment/`;
          body = {
            new_accumulated_depreciation: actionData.new_accumulated_depreciation,
            reason: actionData.reason || '',
          };
          break;

        case 'retire':
          url = `http://localhost:8007/api/fixed-assets/assets/${asset.id}/submit_for_retirement/`;
          body = {
            retirement_date: actionData.retirement_date || new Date().toISOString().split('T')[0],
            retirement_type: actionData.retirement_type || 'SOLD',
            disposal_proceeds: actionData.disposal_proceeds || 0,
            disposal_costs: actionData.disposal_costs || 0,
            buyer_recipient: actionData.buyer_recipient || '',
            sale_invoice_number: actionData.sale_invoice_number || '',
            reason: actionData.reason || '',
          };
          break;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        alert('Request submitted successfully!');
        setShowActionModal(false);
        fetchAsset();
        fetchActions();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to submit request'}`);
      }
    } catch (error) {
      console.error('Error submitting action:', error);
      alert('Error submitting request');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-600">Loading asset...</p>
      </div>
    );
  }

  if (!asset) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Asset not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">{asset.asset_number}</h1>
            <p className="text-gray-600">{asset.name}</p>
          </div>
          <div className="flex items-center space-x-3">
            <span
              className={`px-3 py-1 rounded-full text-sm font-semibold ${
                asset.status === 'CIP'
                  ? 'bg-yellow-100 text-yellow-800'
                  : asset.status === 'CAPITALIZED'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {asset.status}
            </span>
            <Link
              href={`/fixed-assets/${asset.id}/edit`}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Edit
            </Link>
          </div>
        </div>
      </div>

      {/* Asset Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Asset Information</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">Category</dt>
              <dd className="text-lg">{asset.category_name || `Category #${asset.category}`}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Location</dt>
              <dd className="text-lg">{asset.location_name || `Location #${asset.location}`}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Description</dt>
              <dd className="text-lg">{asset.description || '-'}</dd>
            </div>
          </dl>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Financial Information</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">Acquisition Cost</dt>
              <dd className="text-lg font-semibold">${Number(asset.acquisition_cost).toFixed(2)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Accumulated Depreciation</dt>
              <dd className="text-lg">${Number(asset.accumulated_depreciation).toFixed(2)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Net Book Value</dt>
              <dd className="text-lg font-semibold text-blue-600">
                ${Number(asset.net_book_value).toFixed(2)}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Useful Life</dt>
              <dd className="text-lg">{asset.useful_life_months} months</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">Actions</h2>
        <div className="flex flex-wrap gap-3">
          {asset.status === 'CIP' && (
            <button
              onClick={() => openActionModal('capitalize')}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            >
              Submit for Capitalization
            </button>
          )}

          {asset.status === 'CAPITALIZED' && (
            <>
              <button
                onClick={() => openActionModal('transfer')}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Transfer Location
              </button>
              <button
                onClick={() => openActionModal('recategorize')}
                className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
              >
                Recategorize
              </button>
              <button
                onClick={() => openActionModal('adjust_cost')}
                className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
              >
                Adjust Cost
              </button>
              <button
                onClick={() => openActionModal('adjust_useful_life')}
                className="bg-teal-600 text-white px-4 py-2 rounded hover:bg-teal-700"
              >
                Adjust Useful Life
              </button>
              <button
                onClick={() => openActionModal('adjust_depreciation')}
                className="bg-cyan-600 text-white px-4 py-2 rounded hover:bg-cyan-700"
              >
                Manual Depreciation Adjustment
              </button>
              <button
                onClick={() => openActionModal('retire')}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
              >
                Submit for Retirement
              </button>
            </>
          )}

          {asset.status === 'RETIRED' && (
            <p className="text-gray-500 italic">This asset is retired. No actions available.</p>
          )}
        </div>
      </div>

      {/* Action History */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Action History</h2>
        {actions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No actions recorded yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {actions.map((action, index) => (
                  <tr key={`${action.type}-${action.id}-${index}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium capitalize">{action.type}</span>
                    </td>
                    <td className="px-6 py-4">{action.description}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(action.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          action.status === 'PENDING'
                            ? 'bg-yellow-100 text-yellow-800'
                            : action.status === 'APPROVED'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {action.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Action Modal */}
      {showActionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">
              {actionType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
            </h2>

            <div className="space-y-4">
              {actionType === 'capitalize' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Capitalization Date</label>
                    <input
                      type="date"
                      value={actionData.capitalization_date || ''}
                      onChange={(e) => setActionData({ ...actionData, capitalization_date: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Notes</label>
                    <textarea
                      value={actionData.notes || ''}
                      onChange={(e) => setActionData({ ...actionData, notes: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2 h-24"
                    />
                  </div>
                </>
              )}

              {actionType === 'transfer' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">To Location *</label>
                    <select
                      value={actionData.to_location || ''}
                      onChange={(e) => setActionData({ ...actionData, to_location: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      required
                    >
                      <option value="">Select location...</option>
                      {locations.map((loc) => (
                        <option key={loc.id} value={loc.id}>
                          {loc.name} ({loc.code})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Transfer Date</label>
                    <input
                      type="date"
                      value={actionData.transfer_date || ''}
                      onChange={(e) => setActionData({ ...actionData, transfer_date: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Reason</label>
                    <textarea
                      value={actionData.reason || ''}
                      onChange={(e) => setActionData({ ...actionData, reason: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2 h-24"
                    />
                  </div>
                </>
              )}

              {actionType === 'recategorize' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">New Category *</label>
                    <select
                      value={actionData.new_category || ''}
                      onChange={(e) => setActionData({ ...actionData, new_category: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      required
                    >
                      <option value="">Select category...</option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name} ({cat.code})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Reason</label>
                    <textarea
                      value={actionData.reason || ''}
                      onChange={(e) => setActionData({ ...actionData, reason: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2 h-24"
                    />
                  </div>
                </>
              )}

              {actionType === 'adjust_cost' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Current Cost</label>
                    <input
                      type="text"
                      value={`$${Number(asset.acquisition_cost).toFixed(2)}`}
                      disabled
                      className="w-full border border-gray-300 rounded px-3 py-2 bg-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">New Cost *</label>
                    <input
                      type="number"
                      step="0.01"
                      value={actionData.new_cost || ''}
                      onChange={(e) => setActionData({ ...actionData, new_cost: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Reason</label>
                    <textarea
                      value={actionData.reason || ''}
                      onChange={(e) => setActionData({ ...actionData, reason: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2 h-24"
                    />
                  </div>
                </>
              )}

              {actionType === 'adjust_useful_life' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Current Useful Life</label>
                    <input
                      type="text"
                      value={`${asset.useful_life_months} months`}
                      disabled
                      className="w-full border border-gray-300 rounded px-3 py-2 bg-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">New Useful Life (months) *</label>
                    <input
                      type="number"
                      value={actionData.new_useful_life || ''}
                      onChange={(e) => setActionData({ ...actionData, new_useful_life: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Reason</label>
                    <textarea
                      value={actionData.reason || ''}
                      onChange={(e) => setActionData({ ...actionData, reason: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2 h-24"
                    />
                  </div>
                </>
              )}

              {actionType === 'adjust_depreciation' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Current Accumulated Depreciation</label>
                    <input
                      type="text"
                      value={`$${Number(asset.accumulated_depreciation).toFixed(2)}`}
                      disabled
                      className="w-full border border-gray-300 rounded px-3 py-2 bg-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">New Accumulated Depreciation *</label>
                    <input
                      type="number"
                      step="0.01"
                      value={actionData.new_accumulated_depreciation || ''}
                      onChange={(e) => setActionData({ ...actionData, new_accumulated_depreciation: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Reason</label>
                    <textarea
                      value={actionData.reason || ''}
                      onChange={(e) => setActionData({ ...actionData, reason: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2 h-24"
                    />
                  </div>
                </>
              )}

              {actionType === 'retire' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Retirement Date</label>
                    <input
                      type="date"
                      value={actionData.retirement_date || ''}
                      onChange={(e) => setActionData({ ...actionData, retirement_date: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Retirement Type</label>
                    <select
                      value={actionData.retirement_type || 'SOLD'}
                      onChange={(e) => setActionData({ ...actionData, retirement_type: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    >
                      <option value="SOLD">Sold</option>
                      <option value="SCRAPPED">Scrapped</option>
                      <option value="DONATED">Donated</option>
                      <option value="LOST_STOLEN">Lost/Stolen</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Disposal Proceeds</label>
                    <input
                      type="number"
                      step="0.01"
                      value={actionData.disposal_proceeds || 0}
                      onChange={(e) => setActionData({ ...actionData, disposal_proceeds: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Disposal Costs</label>
                    <input
                      type="number"
                      step="0.01"
                      value={actionData.disposal_costs || 0}
                      onChange={(e) => setActionData({ ...actionData, disposal_costs: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Buyer/Recipient</label>
                    <input
                      type="text"
                      value={actionData.buyer_recipient || ''}
                      onChange={(e) => setActionData({ ...actionData, buyer_recipient: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Sale Invoice Number</label>
                    <input
                      type="text"
                      value={actionData.sale_invoice_number || ''}
                      onChange={(e) => setActionData({ ...actionData, sale_invoice_number: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Reason</label>
                    <textarea
                      value={actionData.reason || ''}
                      onChange={(e) => setActionData({ ...actionData, reason: e.target.value })}
                      className="w-full border border-gray-300 rounded px-3 py-2 h-24"
                    />
                  </div>
                </>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowActionModal(false)}
                disabled={processing}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitAction}
                disabled={processing}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {processing ? 'Submitting...' : 'Submit for Approval'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

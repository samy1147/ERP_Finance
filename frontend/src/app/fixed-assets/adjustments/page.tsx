'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface AssetAdjustment {
  id: number;
  asset: number;
  asset_number?: string;
  adjustment_type: 'COST' | 'USEFUL_LIFE' | 'DEPRECIATION' | 'RECATEGORIZE';
  adjustment_date: string;
  old_value: string;
  new_value: string;
  reason: string;
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  adjusted_at: string;
  approved_at: string | null;
}

const adjustmentTypeLabels = {
  COST: 'Cost Adjustment',
  USEFUL_LIFE: 'Useful Life Adjustment',
  DEPRECIATION: 'Depreciation Adjustment',
  RECATEGORIZE: 'Recategorization',
};

const statusColors = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
};

export default function AdjustmentsPage() {
  const [adjustments, setAdjustments] = useState<AssetAdjustment[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED'>('ALL');
  const [typeFilter, setTypeFilter] = useState<'ALL' | 'COST' | 'USEFUL_LIFE' | 'DEPRECIATION' | 'RECATEGORIZE'>('ALL');

  useEffect(() => {
    fetchAdjustments();
  }, [statusFilter, typeFilter]);

  const fetchAdjustments = async () => {
    try {
      setLoading(true);
      let url = 'http://localhost:8007/api/fixed-assets/adjustments/';
      const params = new URLSearchParams();
      
      if (statusFilter !== 'ALL') {
        params.append('approval_status', statusFilter);
      }
      
      if (typeFilter !== 'ALL') {
        params.append('adjustment_type', typeFilter);
      }
      
      if (params.toString()) {
        url += '?' + params.toString();
      }
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setAdjustments(data);
      }
    } catch (error) {
      console.error('Error fetching adjustments:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Asset Adjustments</h1>
        <p className="text-gray-600">View and manage asset adjustment requests</p>
      </div>

      {/* Filters */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="ALL">All Statuses</option>
              <option value="PENDING">Pending</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Adjustment Type
            </label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as any)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="ALL">All Types</option>
              <option value="COST">Cost Adjustment</option>
              <option value="USEFUL_LIFE">Useful Life Adjustment</option>
              <option value="DEPRECIATION">Depreciation Adjustment</option>
              <option value="RECATEGORIZE">Recategorization</option>
            </select>
          </div>
        </div>
      </div>

      {/* Adjustments List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading adjustments...</p>
        </div>
      ) : adjustments.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 text-lg">No adjustments found</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Asset
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Old Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  New Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
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
              {adjustments.map((adjustment) => (
                <tr key={adjustment.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      href={`/fixed-assets/${adjustment.asset}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Asset #{adjustment.asset}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-medium">
                      {adjustmentTypeLabels[adjustment.adjustment_type]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {adjustment.old_value}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {adjustment.new_value}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(adjustment.adjustment_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        statusColors[adjustment.approval_status]
                      }`}
                    >
                      {adjustment.approval_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <Link
                      href={`/fixed-assets/adjustments/${adjustment.id}`}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      View Details
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

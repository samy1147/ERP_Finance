'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface AssetRetirement {
  id: number;
  asset: number;
  asset_number?: string;
  retirement_date: string;
  retirement_type: 'SOLD' | 'SCRAPPED' | 'DONATED' | 'LOST_STOLEN' | 'OTHER';
  net_book_value_at_retirement: string;
  disposal_proceeds: string;
  disposal_costs: string;
  gain_loss: string;
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  submitted_at: string;
  approved_at: string | null;
}

const retirementTypeLabels = {
  SOLD: 'Sold',
  SCRAPPED: 'Scrapped',
  DONATED: 'Donated',
  LOST_STOLEN: 'Lost/Stolen',
  OTHER: 'Other',
};

const statusColors = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
};

export default function RetirementsPage() {
  const [retirements, setRetirements] = useState<AssetRetirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED'>('ALL');
  const [typeFilter, setTypeFilter] = useState<'ALL' | 'SOLD' | 'SCRAPPED' | 'DONATED' | 'LOST_STOLEN' | 'OTHER'>('ALL');

  useEffect(() => {
    fetchRetirements();
  }, [statusFilter, typeFilter]);

  const fetchRetirements = async () => {
    try {
      setLoading(true);
      let url = 'http://localhost:8007/api/fixed-assets/retirements/';
      const params = new URLSearchParams();
      
      if (statusFilter !== 'ALL') {
        params.append('approval_status', statusFilter);
      }
      
      if (typeFilter !== 'ALL') {
        params.append('retirement_type', typeFilter);
      }
      
      if (params.toString()) {
        url += '?' + params.toString();
      }
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setRetirements(data);
      }
    } catch (error) {
      console.error('Error fetching retirements:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Asset Retirements</h1>
        <p className="text-gray-600">View and manage asset retirement requests</p>
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
              Retirement Type
            </label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as any)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="ALL">All Types</option>
              <option value="SOLD">Sold</option>
              <option value="SCRAPPED">Scrapped</option>
              <option value="DONATED">Donated</option>
              <option value="LOST_STOLEN">Lost/Stolen</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
        </div>
      </div>

      {/* Retirements List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading retirements...</p>
        </div>
      ) : retirements.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 text-lg">No retirements found</p>
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
                  Retirement Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  NBV
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Proceeds
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Gain/Loss
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
              {retirements.map((retirement) => (
                <tr key={retirement.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      href={`/fixed-assets/${retirement.asset}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Asset #{retirement.asset}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {new Date(retirement.retirement_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {retirementTypeLabels[retirement.retirement_type]}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    ${Number(retirement.net_book_value_at_retirement).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    ${Number(retirement.disposal_proceeds).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span
                      className={
                        Number(retirement.gain_loss) >= 0
                          ? 'text-green-600 font-semibold'
                          : 'text-red-600 font-semibold'
                      }
                    >
                      ${Number(retirement.gain_loss).toFixed(2)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        statusColors[retirement.approval_status]
                      }`}
                    >
                      {retirement.approval_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <Link
                      href={`/fixed-assets/retirements/${retirement.id}`}
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

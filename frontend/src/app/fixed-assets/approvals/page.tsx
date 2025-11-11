'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface AssetApproval {
  id: number;
  asset: number;
  asset_number?: string;
  asset_name?: string;
  operation_type: 'CAPITALIZE' | 'RETIRE' | 'ADJUST' | 'TRANSFER';
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
  notes: string;
  requested_by: number | null;
  approved_by: number | null;
  requested_at: string;
  approved_at: string | null;
  rejection_reason: string;
  retirement: number | null;
  adjustment: number | null;
  transfer: number | null;
}

const operationTypeLabels = {
  CAPITALIZE: 'Capitalization',
  RETIRE: 'Retirement',
  ADJUST: 'Adjustment',
  TRANSFER: 'Transfer',
};

const statusColors = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
  CANCELLED: 'bg-gray-100 text-gray-800',
};

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<AssetApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'CAPITALIZE' | 'RETIRE' | 'ADJUST' | 'TRANSFER'>('ALL');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedApproval, setSelectedApproval] = useState<AssetApproval | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchApprovals();
  }, [filter, statusFilter]);

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      let url = 'http://localhost:8007/api/fixed-assets/approvals/';
      const params = new URLSearchParams();
      
      if (statusFilter !== 'ALL') {
        if (statusFilter === 'PENDING') {
          params.append('pending_only', 'true');
        } else {
          params.append('approval_status', statusFilter);
        }
      }
      
      if (filter !== 'ALL') {
        params.append('operation_type', filter);
      }
      
      if (params.toString()) {
        url += '?' + params.toString();
      }
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setApprovals(data);
      }
    } catch (error) {
      console.error('Error fetching approvals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approval: AssetApproval) => {
    if (!confirm(`Are you sure you want to approve this ${operationTypeLabels[approval.operation_type]}?`)) {
      return;
    }

    try {
      setProcessing(true);
      const response = await fetch(
        `http://localhost:8007/api/fixed-assets/approvals/${approval.id}/approve/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        alert('Approval successful!');
        fetchApprovals();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to approve'}`);
      }
    } catch (error) {
      console.error('Error approving:', error);
      alert('Error approving request');
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!selectedApproval || !rejectionReason.trim()) {
      alert('Please provide a rejection reason');
      return;
    }

    try {
      setProcessing(true);
      const response = await fetch(
        `http://localhost:8007/api/fixed-assets/approvals/${selectedApproval.id}/reject/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ rejection_reason: rejectionReason }),
        }
      );

      if (response.ok) {
        alert('Rejection successful!');
        setShowRejectModal(false);
        setRejectionReason('');
        setSelectedApproval(null);
        fetchApprovals();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to reject'}`);
      }
    } catch (error) {
      console.error('Error rejecting:', error);
      alert('Error rejecting request');
    } finally {
      setProcessing(false);
    }
  };

  const openRejectModal = (approval: AssetApproval) => {
    setSelectedApproval(approval);
    setShowRejectModal(true);
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Approval Requests</h1>
        <p className="text-gray-600">Review and approve asset operations</p>
      </div>

      {/* Filters */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Operation Type
            </label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="ALL">All Operations</option>
              <option value="CAPITALIZE">Capitalization</option>
              <option value="RETIRE">Retirement</option>
              <option value="ADJUST">Adjustment</option>
              <option value="TRANSFER">Transfer</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="PENDING">Pending Only</option>
              <option value="ALL">All Statuses</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      {/* Approvals List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading approvals...</p>
        </div>
      ) : approvals.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 text-lg">No approval requests found</p>
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
                  Operation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Notes
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Requested
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
              {approvals.map((approval) => (
                <tr key={approval.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      href={`/fixed-assets/${approval.asset}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Asset #{approval.asset}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-medium">
                      {operationTypeLabels[approval.operation_type]}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 max-w-md truncate">
                      {approval.notes || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(approval.requested_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        statusColors[approval.approval_status]
                      }`}
                    >
                      {approval.approval_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {approval.approval_status === 'PENDING' ? (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleApprove(approval)}
                          disabled={processing}
                          className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 disabled:opacity-50"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => openRejectModal(approval)}
                          disabled={processing}
                          className="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 disabled:opacity-50"
                        >
                          Reject
                        </button>
                      </div>
                    ) : (
                      <span className="text-gray-400">
                        {approval.approved_at
                          ? `Processed on ${new Date(approval.approved_at).toLocaleDateString()}`
                          : '-'}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Reject Request</h2>
            <p className="text-gray-600 mb-4">
              Please provide a reason for rejecting this{' '}
              {selectedApproval && operationTypeLabels[selectedApproval.operation_type]} request:
            </p>
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 mb-4 h-32"
              placeholder="Enter rejection reason..."
            />
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectionReason('');
                  setSelectedApproval(null);
                }}
                disabled={processing}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={processing || !rejectionReason.trim()}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {processing ? 'Processing...' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

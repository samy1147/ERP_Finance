'use client';

import React, { useState, useEffect } from 'react';
import { invoiceApprovalsAPI, arInvoicesAPI, apInvoicesAPI } from '../../services/api';
import { InvoiceApproval, ARInvoice, APInvoice } from '../../types';
import toast from 'react-hot-toast';

type TabType = 'pending' | 'submissions' | 'history';

export default function ApprovalsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('pending');
  const [approvals, setApprovals] = useState<InvoiceApproval[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    fetchApprovals();
  }, [refreshTrigger]);

  const fetchApprovals = async () => {
    setLoading(true);
    try {
      const response = await invoiceApprovalsAPI.list();
      setApprovals(response.data || []);
    } catch (error) {
      console.error('Failed to load approvals:', error);
      toast.error('Failed to load approvals');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approval: InvoiceApproval) => {
    const comments = prompt('Add approval comments (optional):');
    if (comments === null) return; // User cancelled
    
    try {
      await invoiceApprovalsAPI.approve(approval.id!, comments || undefined);
      toast.success(`Invoice ${approval.invoice_number} approved!`);
      setRefreshTrigger(prev => prev + 1);
    } catch (error: any) {
      console.error('Failed to approve:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to approve invoice';
      toast.error(errorMsg);
    }
  };

  const handleReject = async (approval: InvoiceApproval) => {
    const comments = prompt('Add rejection reason (required):');
    if (!comments || comments.trim() === '') {
      toast.error('Please provide a rejection reason');
      return;
    }
    
    try {
      await invoiceApprovalsAPI.reject(approval.id!, comments);
      toast.success(`Invoice ${approval.invoice_number} rejected`);
      setRefreshTrigger(prev => prev + 1);
    } catch (error: any) {
      console.error('Failed to reject:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to reject invoice';
      toast.error(errorMsg);
    }
  };

  const getFilteredApprovals = () => {
    switch (activeTab) {
      case 'pending':
        return approvals.filter(a => a.status === 'PENDING' || a.status === 'PENDING_APPROVAL');
      case 'submissions':
        // In a real app, filter by current user's submissions
        return approvals;
      case 'history':
        return approvals.filter(a => a.status !== 'PENDING' && a.status !== 'PENDING_APPROVAL');
      default:
        return approvals;
    }
  };

  const filteredApprovals = getFilteredApprovals();

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
      case 'PENDING_APPROVAL':
        return <span className="px-3 py-1 text-xs font-semibold text-yellow-800 bg-yellow-100 rounded-full">Pending</span>;
      case 'APPROVED':
        return <span className="px-3 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">Approved</span>;
      case 'REJECTED':
        return <span className="px-3 py-1 text-xs font-semibold text-red-800 bg-red-100 rounded-full">Rejected</span>;
      default:
        return <span className="px-3 py-1 text-xs font-semibold text-gray-800 bg-gray-100 rounded-full">{status}</span>;
    }
  };

  const getInvoiceTypeBadge = (type: string) => {
    return type === 'AR' ? (
      <span className="px-2 py-1 text-xs font-medium text-blue-800 bg-blue-100 rounded">AR</span>
    ) : (
      <span className="px-2 py-1 text-xs font-medium text-purple-800 bg-purple-100 rounded">AP</span>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Invoice Approvals</h1>
          <p className="mt-2 text-gray-600">Manage invoice approval requests</p>
        </div>

        {/* Tabs */}
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('pending')}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'pending'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Pending Approvals
                {approvals.filter(a => a.status === 'PENDING' || a.status === 'PENDING_APPROVAL').length > 0 && (
                  <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                    {approvals.filter(a => a.status === 'PENDING' || a.status === 'PENDING_APPROVAL').length}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('submissions')}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'submissions'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                My Submissions
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'history'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                History
              </button>
            </nav>
          </div>

          {/* Content */}
          <div className="p-6">
            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
                <p className="mt-4 text-gray-600">Loading approvals...</p>
              </div>
            ) : filteredApprovals.length === 0 ? (
              <div className="text-center py-12">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No approvals</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {activeTab === 'pending' && 'No pending approval requests at this time.'}
                  {activeTab === 'submissions' && 'You have not submitted any invoices for approval.'}
                  {activeTab === 'history' && 'No approval history available.'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Invoice #
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Submitted By
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Approver
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Submitted
                      </th>
                      {activeTab === 'pending' && (
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredApprovals.map((approval) => (
                      <tr key={approval.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getInvoiceTypeBadge(approval.invoice_type)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {approval.invoice_number || `#${approval.invoice_id}`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {approval.submitted_by_name || `User #${approval.submitted_by}`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {approval.approver_name || `User #${approval.approver}`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(approval.status)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {approval.submitted_at ? new Date(approval.submitted_at).toLocaleDateString() : '-'}
                        </td>
                        {activeTab === 'pending' && (
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex justify-end space-x-2">
                              <button
                                onClick={() => handleApprove(approval)}
                                className="px-3 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-xs"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleReject(approval)}
                                className="px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-xs"
                              >
                                Reject
                              </button>
                            </div>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Comments/Details Section */}
            {filteredApprovals.length > 0 && activeTab === 'history' && (
              <div className="mt-6 space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Details</h3>
                {filteredApprovals.map((approval) => (
                  approval.comments && (
                    <div key={approval.id} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            Invoice {approval.invoice_number || `#${approval.invoice_id}`}
                          </p>
                          <p className="text-sm text-gray-500 mt-1">{approval.comments}</p>
                        </div>
                        {getStatusBadge(approval.status)}
                      </div>
                    </div>
                  )
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

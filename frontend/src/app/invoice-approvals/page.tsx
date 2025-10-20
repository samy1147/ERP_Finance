'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { invoiceApprovalsAPI, arInvoicesAPI, apInvoicesAPI } from '../../services/api';
import { InvoiceApproval, ARInvoice, APInvoice } from '../../types';
import { CheckCircle, XCircle, Eye, Filter, Search, FileText, Calendar, DollarSign, User } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

type TabType = 'pending' | 'approved' | 'rejected' | 'all';
type InvoiceType = 'all' | 'AR' | 'AP';

export default function InvoiceApprovalsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('pending');
  const [invoiceTypeFilter, setInvoiceTypeFilter] = useState<InvoiceType>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [approvals, setApprovals] = useState<InvoiceApproval[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedApprovals, setSelectedApprovals] = useState<number[]>([]);
  const [showDetails, setShowDetails] = useState<number | null>(null);
  const [invoiceDetails, setInvoiceDetails] = useState<ARInvoice | APInvoice | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  useEffect(() => {
    fetchApprovals();
  }, []);

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

  const fetchInvoiceDetails = async (approval: InvoiceApproval) => {
    setLoadingDetails(true);
    try {
      if (approval.invoice_type === 'AR') {
        const response = await arInvoicesAPI.get(approval.invoice_id);
        setInvoiceDetails(response.data);
      } else {
        const response = await apInvoicesAPI.get(approval.invoice_id);
        setInvoiceDetails(response.data);
      }
      setShowDetails(approval.id!);
    } catch (error) {
      console.error('Failed to load invoice details:', error);
      toast.error('Failed to load invoice details');
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleApprove = async (approvalId: number, comments?: string) => {
    try {
      await invoiceApprovalsAPI.approve(approvalId, comments);
      toast.success('Invoice approved successfully!');
      fetchApprovals();
      setShowDetails(null);
      setInvoiceDetails(null);
      setSelectedApprovals([]);
    } catch (error: any) {
      console.error('Failed to approve:', error);
      toast.error(error.response?.data?.detail || 'Failed to approve invoice');
    }
  };

  const handleReject = async (approvalId: number, comments: string) => {
    if (!comments || comments.trim() === '') {
      toast.error('Please provide a rejection reason');
      return;
    }
    
    try {
      await invoiceApprovalsAPI.reject(approvalId, comments);
      toast.success('Invoice rejected');
      fetchApprovals();
      setShowDetails(null);
      setInvoiceDetails(null);
      setSelectedApprovals([]);
    } catch (error: any) {
      console.error('Failed to reject:', error);
      toast.error(error.response?.data?.detail || 'Failed to reject invoice');
    }
  };

  const handleBulkApprove = async () => {
    if (selectedApprovals.length === 0) {
      toast.error('Please select invoices to approve');
      return;
    }

    const confirmed = confirm(`Approve ${selectedApprovals.length} invoice(s)?`);
    if (!confirmed) return;

    try {
      const promises = selectedApprovals.map(id => invoiceApprovalsAPI.approve(id));
      await Promise.all(promises);
      toast.success(`${selectedApprovals.length} invoice(s) approved!`);
      fetchApprovals();
      setSelectedApprovals([]);
    } catch (error) {
      console.error('Failed to approve invoices:', error);
      toast.error('Some invoices failed to approve');
      fetchApprovals();
    }
  };

  const toggleSelectApproval = (approvalId: number) => {
    setSelectedApprovals(prev =>
      prev.includes(approvalId)
        ? prev.filter(id => id !== approvalId)
        : [...prev, approvalId]
    );
  };

  const toggleSelectAll = () => {
    const filtered = getFilteredApprovals();
    if (selectedApprovals.length === filtered.length) {
      setSelectedApprovals([]);
    } else {
      setSelectedApprovals(filtered.map(a => a.id!));
    }
  };

  const getFilteredApprovals = () => {
    let filtered = approvals;

    // Filter by tab
    switch (activeTab) {
      case 'pending':
        filtered = filtered.filter(a => a.status === 'PENDING_APPROVAL' || a.status === 'PENDING');
        break;
      case 'approved':
        filtered = filtered.filter(a => a.status === 'APPROVED');
        break;
      case 'rejected':
        filtered = filtered.filter(a => a.status === 'REJECTED');
        break;
      case 'all':
        break;
    }

    // Filter by invoice type
    if (invoiceTypeFilter !== 'all') {
      filtered = filtered.filter(a => a.invoice_type === invoiceTypeFilter);
    }

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(a =>
        a.invoice_number?.toLowerCase().includes(query) ||
        a.submitted_by_name?.toLowerCase().includes(query) ||
        a.approver_name?.toLowerCase().includes(query)
      );
    }

    return filtered;
  };

  const filteredApprovals = getFilteredApprovals();

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
      case 'PENDING_APPROVAL':
        return (
          <span className="inline-flex items-center px-3 py-1 text-xs font-semibold text-yellow-800 bg-yellow-100 rounded-full">
            <div className="w-2 h-2 mr-2 bg-yellow-500 rounded-full animate-pulse"></div>
            Pending
          </span>
        );
      case 'APPROVED':
        return (
          <span className="inline-flex items-center px-3 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">
            <CheckCircle className="w-3 h-3 mr-1" />
            Approved
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center px-3 py-1 text-xs font-semibold text-red-800 bg-red-100 rounded-full">
            <XCircle className="w-3 h-3 mr-1" />
            Rejected
          </span>
        );
      default:
        return <span className="px-3 py-1 text-xs font-semibold text-gray-800 bg-gray-100 rounded-full">{status}</span>;
    }
  };

  const getInvoiceTypeBadge = (type: string) => {
    return type === 'AR' ? (
      <span className="px-2 py-1 text-xs font-semibold text-blue-800 bg-blue-100 rounded">
        Receivable
      </span>
    ) : (
      <span className="px-2 py-1 text-xs font-semibold text-purple-800 bg-purple-100 rounded">
        Payable
      </span>
    );
  };

  const getTabCount = (tab: TabType) => {
    switch (tab) {
      case 'pending':
        return approvals.filter(a => a.status === 'PENDING' || a.status === 'PENDING_APPROVAL').length;
      case 'approved':
        return approvals.filter(a => a.status === 'APPROVED').length;
      case 'rejected':
        return approvals.filter(a => a.status === 'REJECTED').length;
      case 'all':
        return approvals.length;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <FileText className="w-8 h-8 text-blue-600" />
            Invoice Approvals
          </h1>
          <p className="mt-2 text-gray-600">Review and approve invoice submissions</p>
        </div>

        {/* Filters and Search */}
        <div className="mb-6 bg-white rounded-lg shadow-sm p-4">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by invoice number, submitter, or approver..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Invoice Type Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-500" />
              <select
                value={invoiceTypeFilter}
                onChange={(e) => setInvoiceTypeFilter(e.target.value as InvoiceType)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Types</option>
                <option value="AR">Receivables</option>
                <option value="AP">Payables</option>
              </select>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {(['pending', 'approved', 'rejected', 'all'] as TabType[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                    activeTab === tab
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {getTabCount(tab)}
                  </span>
                </button>
              ))}
            </nav>
          </div>

          {/* Bulk Actions Bar */}
          {activeTab === 'pending' && selectedApprovals.length > 0 && (
            <div className="bg-blue-50 border-b border-blue-200 px-6 py-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-900 font-medium">
                  {selectedApprovals.length} invoice(s) selected
                </span>
                <button
                  onClick={handleBulkApprove}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center gap-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve Selected
                </button>
              </div>
            </div>
          )}

          {/* Content */}
          <div className="p-6">
            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                <p className="mt-4 text-gray-600">Loading approvals...</p>
              </div>
            ) : filteredApprovals.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="mx-auto h-16 w-16 text-gray-400" />
                <h3 className="mt-4 text-lg font-medium text-gray-900">No approvals found</h3>
                <p className="mt-2 text-sm text-gray-500">
                  {searchQuery ? 'Try adjusting your search criteria' : 'No invoices match the selected filters'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {activeTab === 'pending' && (
                        <th className="px-6 py-3 text-left">
                          <input
                            type="checkbox"
                            checked={selectedApprovals.length === filteredApprovals.length}
                            onChange={toggleSelectAll}
                            className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                          />
                        </th>
                      )}
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
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredApprovals.map((approval) => (
                      <React.Fragment key={approval.id}>
                        <tr className={`hover:bg-gray-50 ${selectedApprovals.includes(approval.id!) ? 'bg-blue-50' : ''}`}>
                          {activeTab === 'pending' && (
                            <td className="px-6 py-4 whitespace-nowrap">
                              <input
                                type="checkbox"
                                checked={selectedApprovals.includes(approval.id!)}
                                onChange={() => toggleSelectApproval(approval.id!)}
                                className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                              />
                            </td>
                          )}
                          <td className="px-6 py-4 whitespace-nowrap">
                            {getInvoiceTypeBadge(approval.invoice_type)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <FileText className="w-4 h-4 text-gray-400" />
                              <span className="text-sm font-medium text-gray-900">
                                {approval.invoice_number || `#${approval.invoice_id}`}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <User className="w-4 h-4 text-gray-400" />
                              <span className="text-sm text-gray-700">
                                {approval.submitted_by_name || `User #${approval.submitted_by}`}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {approval.approver_name || `User #${approval.approver}`}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {getStatusBadge(approval.status)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <Calendar className="w-4 h-4 text-gray-400" />
                              <span className="text-sm text-gray-500">
                                {approval.submitted_at ? format(new Date(approval.submitted_at), 'MMM dd, yyyy') : '-'}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex justify-end gap-2">
                              <button
                                onClick={() => fetchInvoiceDetails(approval)}
                                className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                                title="View Details"
                              >
                                <Eye className="w-4 h-4" />
                                View
                              </button>
                              {(approval.status === 'PENDING' || approval.status === 'PENDING_APPROVAL') && (
                                <>
                                  <button
                                    onClick={() => {
                                      const comments = prompt('Add approval comments (optional):');
                                      if (comments !== null) {
                                        handleApprove(approval.id!, comments || undefined);
                                      }
                                    }}
                                    className="px-3 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center gap-1"
                                  >
                                    <CheckCircle className="w-4 h-4" />
                                    Approve
                                  </button>
                                  <button
                                    onClick={() => {
                                      const comments = prompt('Add rejection reason (required):');
                                      if (comments) {
                                        handleReject(approval.id!, comments);
                                      }
                                    }}
                                    className="px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors flex items-center gap-1"
                                  >
                                    <XCircle className="w-4 h-4" />
                                    Reject
                                  </button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>

                        {/* Details Row */}
                        {showDetails === approval.id && (
                          <tr>
                            <td colSpan={activeTab === 'pending' ? 8 : 7} className="px-6 py-4 bg-gray-50">
                              {loadingDetails ? (
                                <div className="text-center py-4">
                                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                                  <p className="mt-2 text-sm text-gray-600">Loading invoice details...</p>
                                </div>
                              ) : invoiceDetails ? (
                                <div className="bg-white rounded-lg p-6 shadow-inner">
                                  <div className="flex justify-between items-start mb-4">
                                    <h3 className="text-lg font-semibold text-gray-900">Invoice Details</h3>
                                    <button
                                      onClick={() => {
                                        setShowDetails(null);
                                        setInvoiceDetails(null);
                                      }}
                                      className="text-gray-400 hover:text-gray-600"
                                    >
                                      <XCircle className="w-5 h-5" />
                                    </button>
                                  </div>

                                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                    <div>
                                      <label className="text-xs text-gray-500 uppercase">Invoice Number</label>
                                      <p className="text-sm font-semibold text-gray-900">{invoiceDetails.invoice_number}</p>
                                    </div>
                                    <div>
                                      <label className="text-xs text-gray-500 uppercase">Date</label>
                                      <p className="text-sm text-gray-900">
                                        {format(new Date(invoiceDetails.date), 'MMM dd, yyyy')}
                                      </p>
                                    </div>
                                    <div>
                                      <label className="text-xs text-gray-500 uppercase">Due Date</label>
                                      <p className="text-sm text-gray-900">
                                        {format(new Date(invoiceDetails.due_date), 'MMM dd, yyyy')}
                                      </p>
                                    </div>
                                    <div>
                                      <label className="text-xs text-gray-500 uppercase">Total Amount</label>
                                      <p className="text-lg font-bold text-gray-900 flex items-center gap-1">
                                        <DollarSign className="w-4 h-4" />
                                        {invoiceDetails.total}
                                      </p>
                                    </div>
                                  </div>

                                  {/* Approval Actions in Details View */}
                                  {(approval.status === 'PENDING' || approval.status === 'PENDING_APPROVAL') && (
                                    <div className="mt-6 pt-6 border-t border-gray-200">
                                      <div className="flex gap-3">
                                        <button
                                          onClick={() => {
                                            const comments = prompt('Add approval comments (optional):');
                                            if (comments !== null) {
                                              handleApprove(approval.id!, comments || undefined);
                                            }
                                          }}
                                          className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center justify-center gap-2"
                                        >
                                          <CheckCircle className="w-5 h-5" />
                                          Approve Invoice
                                        </button>
                                        <button
                                          onClick={() => {
                                            const comments = prompt('Add rejection reason (required):');
                                            if (comments) {
                                              handleReject(approval.id!, comments);
                                            }
                                          }}
                                          className="flex-1 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium flex items-center justify-center gap-2"
                                        >
                                          <XCircle className="w-5 h-5" />
                                          Reject Invoice
                                        </button>
                                      </div>
                                    </div>
                                  )}

                                  {/* Comments Section */}
                                  {approval.comments && (
                                    <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                                      <h4 className="text-sm font-semibold text-yellow-900 mb-2">Comments</h4>
                                      <p className="text-sm text-yellow-800">{approval.comments}</p>
                                    </div>
                                  )}
                                </div>
                              ) : null}
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Summary Cards */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-3xl font-bold text-yellow-600">{getTabCount('pending')}</p>
              </div>
              <div className="p-3 bg-yellow-100 rounded-full">
                <FileText className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Approved</p>
                <p className="text-3xl font-bold text-green-600">{getTabCount('approved')}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Rejected</p>
                <p className="text-3xl font-bold text-red-600">{getTabCount('rejected')}</p>
              </div>
              <div className="p-3 bg-red-100 rounded-full">
                <XCircle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total</p>
                <p className="text-3xl font-bold text-blue-600">{getTabCount('all')}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

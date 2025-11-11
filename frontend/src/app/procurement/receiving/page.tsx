'use client';

import React, { useState, useEffect } from 'react';
import { goodsReceiptsExtendedAPI, qualityInspectionsAPI, returnToVendorAPI } from '../../../services/procurement-api';
import { GoodsReceipt, QualityInspection, ReturnToVendor } from '../../../types/procurement';
import { Plus, Search, Eye, CheckCircle, XCircle, Package, AlertTriangle, TruckIcon } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function ReceivingPage() {
  const [view, setView] = useState<'receipts' | 'inspections' | 'returns'>('receipts');
  const [receipts, setReceipts] = useState<GoodsReceipt[]>([]);
  const [inspections, setInspections] = useState<QualityInspection[]>([]);
  const [returns, setReturns] = useState<ReturnToVendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    fetchData();
  }, [view, statusFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (statusFilter) params.status = statusFilter;

      if (view === 'receipts') {
        const response = await goodsReceiptsExtendedAPI.list(params);
        setReceipts(Array.isArray(response.data) ? response.data : (response.data as any).results || []);
      } else if (view === 'inspections') {
        const response = await qualityInspectionsAPI.list(params);
        setInspections(Array.isArray(response.data) ? response.data : (response.data as any).results || []);
      } else if (view === 'returns') {
        const response = await returnToVendorAPI.list(params);
        setReturns(Array.isArray(response.data) ? response.data : (response.data as any).results || []);
      }
    } catch (error: any) {
      toast.error('Failed to load data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handlePostReceipt = async (id: number, receiptNumber: string) => {
    if (!confirm(`Post receipt ${receiptNumber} to inventory?`)) return;
    
    try {
      await goodsReceiptsExtendedAPI.post(id);
      toast.success('Receipt posted successfully');
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to post receipt');
      console.error(error);
    }
  };

  const handleStartInspection = async (id: number) => {
    try {
      await qualityInspectionsAPI.start(id, {
        inspector_id: 1, // Replace with actual user ID
        start_date: new Date().toISOString().split('T')[0]
      });
      toast.success('Inspection started');
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to start inspection');
      console.error(error);
    }
  };

  const handleCompleteInspection = async (id: number) => {
    try {
      await qualityInspectionsAPI.complete(id, {
        completion_date: new Date().toISOString().split('T')[0],
        inspection_notes: 'Inspection completed'
      });
      toast.success('Inspection completed');
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to complete inspection');
      console.error(error);
    }
  };

  const handleApproveInspection = async (id: number) => {
    if (!confirm('Approve this inspection?')) return;
    
    try {
      await qualityInspectionsAPI.approve(id);
      toast.success('Inspection approved');
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to approve inspection');
      console.error(error);
    }
  };

  const handleRejectInspection = async (id: number) => {
    const reason = prompt('Rejection reason:');
    if (!reason) return;
    
    try {
      await qualityInspectionsAPI.reject(id, { rejection_reason: reason });
      toast.success('Inspection rejected');
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to reject inspection');
      console.error(error);
    }
  };

  const handleSubmitReturn = async (id: number) => {
    if (!confirm('Submit this return to vendor?')) return;
    
    try {
      await returnToVendorAPI.submit(id);
      toast.success('Return submitted');
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to submit return');
      console.error(error);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      RECEIVED: 'bg-blue-100 text-blue-800',
      INSPECTED: 'bg-yellow-100 text-yellow-800',
      ACCEPTED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
      RETURNED: 'bg-orange-100 text-orange-800',
      PENDING: 'bg-yellow-100 text-yellow-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-800',
      COMPLETED: 'bg-green-100 text-green-800',
      APPROVED: 'bg-green-100 text-green-800',
      SUBMITTED: 'bg-blue-100 text-blue-800',
      SHIPPED: 'bg-purple-100 text-purple-800',
      CANCELLED: 'bg-gray-400 text-white',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getQualityResultBadge = (result: string) => {
    const colors: Record<string, string> = {
      PASS: 'bg-green-100 text-green-800',
      FAIL: 'bg-red-100 text-red-800',
      CONDITIONAL: 'bg-yellow-100 text-yellow-800',
      PENDING: 'bg-gray-100 text-gray-800',
    };
    return colors[result] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Receiving & Quality</h1>
            <p className="text-gray-600">Manage goods receipts, inspections, and returns</p>
          </div>
          <div className="flex gap-2">
            {view === 'receipts' && (
              <Link
                href="/procurement/receiving/new"
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus size={20} />
                New Receipt
              </Link>
            )}
            {view === 'returns' && (
              <Link
                href="/procurement/receiving/returns/new"
                className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
              >
                <Plus size={20} />
                New Return
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* View Tabs */}
      <div className="mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setView('receipts')}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors ${
              view === 'receipts'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Package size={18} />
            Goods Receipts
          </button>
          <button
            onClick={() => setView('inspections')}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors ${
              view === 'inspections'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            <CheckCircle size={18} />
            Quality Inspections
          </button>
          <button
            onClick={() => setView('returns')}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors ${
              view === 'returns'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            <TruckIcon size={18} />
            Returns to Vendor
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder={`Search ${view}...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Status</option>
            {view === 'receipts' && (
              <>
                <option value="DRAFT">Draft</option>
                <option value="RECEIVED">Received</option>
                <option value="INSPECTED">Inspected</option>
                <option value="ACCEPTED">Accepted</option>
                <option value="REJECTED">Rejected</option>
              </>
            )}
            {view === 'inspections' && (
              <>
                <option value="PENDING">Pending</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
              </>
            )}
            {view === 'returns' && (
              <>
                <option value="DRAFT">Draft</option>
                <option value="SUBMITTED">Submitted</option>
                <option value="APPROVED">Approved</option>
                <option value="SHIPPED">Shipped</option>
                <option value="COMPLETED">Completed</option>
              </>
            )}
          </select>

          <button
            onClick={() => {
              setSearchTerm('');
              setStatusFilter('');
            }}
            className="px-4 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow">
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {/* Goods Receipts */}
            {view === 'receipts' && (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Receipt #</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">PO #</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supplier</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Receipt Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {receipts.map((receipt) => (
                      <tr key={receipt.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{receipt.receipt_number}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{receipt.purchase_order_number || 'N/A'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{receipt.supplier_name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {receipt.grn_type && (
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              receipt.grn_type === 'SERVICES' 
                                ? 'bg-purple-100 text-purple-800' 
                                : receipt.grn_type === 'CATEGORIZED_GOODS'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {receipt.grn_type === 'SERVICES' ? '🔧 Services' : 
                               receipt.grn_type === 'CATEGORIZED_GOODS' ? '📋 Cataloged' : '✏️ Free Text'}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{new Date(receipt.receipt_date).toLocaleDateString()}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(receipt.status)}`}>
                            {receipt.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end gap-2">
                            <Link href={`/procurement/receiving/${receipt.id}`} className="text-blue-600 hover:text-blue-900">
                              <Eye size={18} />
                            </Link>
                            {receipt.status === 'RECEIVED' && (
                              <button
                                onClick={() => handlePostReceipt(receipt.id, receipt.receipt_number || '')}
                                className="text-green-600 hover:text-green-900"
                                title="Post to Inventory"
                              >
                                <CheckCircle size={18} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Quality Inspections */}
            {view === 'inspections' && (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Inspection #</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">GRN #</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Inspector</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Result</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {inspections.map((inspection) => (
                      <tr key={inspection.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{inspection.inspection_number}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{inspection.grn_number}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{inspection.inspection_type}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{inspection.inspector_name || 'Unassigned'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(inspection.status)}`}>
                            {inspection.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getQualityResultBadge(inspection.result)}`}>
                            {inspection.result}
                          </span>
                          {inspection.non_conformances && inspection.non_conformances.length > 0 && (
                            <span className="ml-2 flex items-center gap-1 text-red-600">
                              <AlertTriangle size={14} />
                              {inspection.non_conformances.length} NC
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end gap-2">
                            <Link href={`/procurement/receiving/inspections/${inspection.id}`} className="text-blue-600 hover:text-blue-900">
                              <Eye size={18} />
                            </Link>
                            {inspection.status === 'PENDING' && (
                              <button
                                onClick={() => handleStartInspection(inspection.id)}
                                className="text-green-600 hover:text-green-900"
                                title="Start Inspection"
                              >
                                <CheckCircle size={18} />
                              </button>
                            )}
                            {inspection.status === 'IN_PROGRESS' && (
                              <button
                                onClick={() => handleCompleteInspection(inspection.id)}
                                className="text-blue-600 hover:text-blue-900"
                                title="Complete Inspection"
                              >
                                <CheckCircle size={18} />
                              </button>
                            )}
                            {inspection.status === 'COMPLETED' && (
                              <>
                                <button
                                  onClick={() => handleApproveInspection(inspection.id)}
                                  className="text-green-600 hover:text-green-900"
                                  title="Approve"
                                >
                                  <CheckCircle size={18} />
                                </button>
                                <button
                                  onClick={() => handleRejectInspection(inspection.id)}
                                  className="text-red-600 hover:text-red-900"
                                  title="Reject"
                                >
                                  <XCircle size={18} />
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Returns to Vendor */}
            {view === 'returns' && (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">RTV #</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">GRN #</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supplier</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Return Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {returns.map((rtvItem) => (
                      <tr key={rtvItem.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{rtvItem.rtv_number}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{rtvItem.grn_number}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{rtvItem.supplier_name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{new Date(rtvItem.return_date).toLocaleDateString()}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-600 line-clamp-1">{rtvItem.reason}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(rtvItem.status)}`}>
                            {rtvItem.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end gap-2">
                            <Link href={`/procurement/receiving/returns/${rtvItem.id}`} className="text-blue-600 hover:text-blue-900">
                              <Eye size={18} />
                            </Link>
                            {rtvItem.status === 'DRAFT' && (
                              <button
                                onClick={() => handleSubmitReturn(rtvItem.id)}
                                className="text-green-600 hover:text-green-900"
                                title="Submit Return"
                              >
                                <CheckCircle size={18} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { vendorBillsAPI } from '../../../../services/procurement-api';
import { VendorBill } from '../../../../types/procurement';
import { ArrowLeft, FileText, CheckCircle, XCircle, Send, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';

export default function VendorBillDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const [bill, setBill] = useState<VendorBill | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchBill();
    }
  }, [id]);

  const fetchBill = async () => {
    try {
      setLoading(true);
      const response = await vendorBillsAPI.get(parseInt(id));
      console.log('Fetched bill detail:', response.data);
      setBill(response.data);
    } catch (error: any) {
      toast.error('Failed to load vendor bill');
      console.error('Error fetching bill:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePerformMatch = async () => {
    if (!bill) return;
    try {
      const response = await vendorBillsAPI.performMatch(bill.id);
      const message = (response as any).message || 'Match completed successfully';
      toast.success(message);
      fetchBill();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to perform match');
      console.error(error);
    }
  };

  const handleApprove = async () => {
    if (!bill) return;
    try {
      await vendorBillsAPI.approveBill(bill.id);
      toast.success('Vendor bill approved successfully');
      fetchBill();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to approve bill');
      console.error(error);
    }
  };

  const handlePost = async () => {
    if (!bill) return;
    try {
      await vendorBillsAPI.postBill(bill.id);
      toast.success('Bill posted to AP successfully');
      fetchBill();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to post bill');
      console.error(error);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusColors: { [key: string]: string } = {
      'DRAFT': 'bg-gray-200 text-gray-700',
      'SUBMITTED': 'bg-blue-200 text-blue-700',
      'PENDING_MATCH': 'bg-yellow-200 text-yellow-700',
      'MATCHED': 'bg-green-200 text-green-700',
      'EXCEPTION': 'bg-red-200 text-red-700',
      'APPROVED': 'bg-purple-200 text-purple-700',
      'POSTED': 'bg-indigo-200 text-indigo-700',
      'PAID': 'bg-teal-200 text-teal-700',
      'CANCELLED': 'bg-gray-300 text-gray-600',
    };
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[status] || 'bg-gray-200 text-gray-700'}`}>
        {status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!bill) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-red-600">Vendor bill not found</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Vendor Bill: {bill.bill_number}</h1>
            <p className="text-gray-600 mt-1">
              Supplier: {(bill as any).supplier_name || `Supplier #${(bill as any).supplier}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {getStatusBadge(bill.status)}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bill Information */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Info Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Bill Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-600">Bill Number</label>
                <p className="font-medium">{bill.bill_number}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Bill Date</label>
                <p className="font-medium">{new Date(bill.bill_date).toLocaleDateString()}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Due Date</label>
                <p className="font-medium">{bill.due_date ? new Date(bill.due_date).toLocaleDateString() : 'Not set'}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Currency</label>
                <p className="font-medium">{(bill as any).currency_code || bill.currency}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Total Amount</label>
                <p className="font-medium text-lg">{(bill as any).currency_code || bill.currency} {parseFloat(bill.total_amount).toFixed(2)}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Payment Terms</label>
                <p className="font-medium">{(bill as any).payment_terms || 'Not specified'}</p>
              </div>
            </div>
            {(bill as any).description && (
              <div className="mt-4">
                <label className="text-sm text-gray-600">Description</label>
                <p className="font-medium">{(bill as any).description}</p>
              </div>
            )}
          </div>

          {/* Match Status Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Match Status</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-600">Is Matched</label>
                <div className="flex items-center gap-2 mt-1">
                  {bill.is_matched ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-gray-400" />
                  )}
                  <span className="font-medium">{bill.is_matched ? 'Yes' : 'No'}</span>
                </div>
              </div>
              <div>
                <label className="text-sm text-gray-600">Has Exceptions</label>
                <div className="flex items-center gap-2 mt-1">
                  {bill.has_exceptions ? (
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  ) : (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  )}
                  <span className="font-medium">{bill.has_exceptions ? 'Yes' : 'No'}</span>
                </div>
              </div>
              <div>
                <label className="text-sm text-gray-600">Exception Count</label>
                <p className="font-medium">{bill.exception_count || 0}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Match Date</label>
                <p className="font-medium">
                  {bill.match_date ? new Date(bill.match_date).toLocaleDateString() : 'Not matched'}
                </p>
              </div>
            </div>
          </div>

          {/* Line Items */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Line Items</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Line #</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Quantity</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Unit Price</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {bill.lines && bill.lines.length > 0 ? (
                    bill.lines.map((line: any) => (
                      <tr key={line.id}>
                        <td className="px-4 py-3 text-sm">{line.line_number}</td>
                        <td className="px-4 py-3 text-sm">{line.description}</td>
                        <td className="px-4 py-3 text-sm text-right">{line.quantity}</td>
                        <td className="px-4 py-3 text-sm text-right">{parseFloat(line.unit_price).toFixed(2)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">
                          {parseFloat(line.line_total).toFixed(2)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                        No line items found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Actions Sidebar */}
        <div className="space-y-6">
          {/* Action Buttons */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Actions</h2>
            <div className="space-y-3">
              {/* Re-Match Button (for EXCEPTION status) */}
              {bill.status === 'EXCEPTION' && (
                <button
                  onClick={handlePerformMatch}
                  className="w-full px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors inline-flex items-center justify-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  Re-Match Bill
                </button>
              )}

              {/* Approve Button (for MATCHED status) */}
              {bill.status === 'MATCHED' && (
                <button
                  onClick={handleApprove}
                  className="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors inline-flex items-center justify-center gap-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve Bill
                </button>
              )}

              {/* Post Button (for APPROVED status) */}
              {bill.status === 'APPROVED' && (
                <button
                  onClick={handlePost}
                  className="w-full px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors inline-flex items-center justify-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  Post to AP
                </button>
              )}

              {/* Back to List */}
              <button
                onClick={() => router.push('/procurement/vendor-bills')}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Back to List
              </button>
            </div>
          </div>

          {/* Status Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Status Details</h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600">Current Status</label>
                <div className="mt-1">{getStatusBadge(bill.status)}</div>
              </div>
              
              {bill.approval_status && (
                <div>
                  <label className="text-sm text-gray-600">Approval Status</label>
                  <p className="font-medium mt-1">{bill.approval_status}</p>
                </div>
              )}

              {bill.is_posted && (
                <div>
                  <label className="text-sm text-gray-600">Posted to AP</label>
                  <div className="flex items-center gap-2 mt-1">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="font-medium">Yes</span>
                  </div>
                </div>
              )}

              {bill.is_paid && (
                <div>
                  <label className="text-sm text-gray-600">Payment Status</label>
                  <div className="flex items-center gap-2 mt-1">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="font-medium">Paid</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Timestamps */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Timestamps</h2>
            <div className="space-y-2 text-sm">
              <div>
                <label className="text-gray-600">Created</label>
                <p className="font-medium">{new Date(bill.created_at).toLocaleString()}</p>
              </div>
              <div>
                <label className="text-gray-600">Last Updated</label>
                <p className="font-medium">{new Date(bill.updated_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

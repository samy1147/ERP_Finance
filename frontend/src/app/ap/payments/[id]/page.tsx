'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apPaymentsAPI } from '../../../../services/api';
import { ArrowLeft, Edit2, Trash2, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ViewAPPaymentPage() {
  const router = useRouter();
  const params = useParams();
  const paymentId = parseInt(params.id as string);
  
  const [loading, setLoading] = useState(true);
  const [payment, setPayment] = useState<any | null>(null);

  useEffect(() => {
    fetchPayment();
  }, [paymentId]);

  const fetchPayment = async () => {
    try {
      setLoading(true);
      const response = await apPaymentsAPI.get(paymentId);
      setPayment(response.data);
    } catch (error: any) {
      console.error('Failed to load payment:', error);
      toast.error(error.response?.data?.error || 'Failed to load payment');
      router.push('/ap/payments');
    } finally {
      setLoading(false);
    }
  };

  const handlePost = async () => {
    if (!payment) return;
    
    if (window.confirm('Are you sure you want to post this payment?')) {
      try {
        await apPaymentsAPI.post(payment.id);
        toast.success('Payment posted successfully');
        fetchPayment();
      } catch (error: any) {
        toast.error(error.response?.data?.error || 'Failed to post payment');
      }
    }
  };

  const handleDelete = async () => {
    if (!payment) return;
    
    if (window.confirm('Are you sure you want to delete this payment?')) {
      try {
        await apPaymentsAPI.delete(payment.id);
        toast.success('Payment deleted successfully');
        router.push('/ap/payments');
      } catch (error: any) {
        toast.error(error.response?.data?.error || 'Failed to delete payment');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading payment...</div>
      </div>
    );
  }

  if (!payment) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Payment not found</div>
      </div>
    );
  }

  const isPosted = !!payment.posted_at;

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/ap/payments')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Payment {payment.reference || `#${payment.id}`}
            </h1>
            <p className="text-sm text-gray-600 mt-1">AP Payment Details</p>
          </div>
        </div>
        
        <div className="flex gap-2">
          {!isPosted && (
            <>
              <button
                onClick={() => router.push(`/ap/payments/${payment.id}/edit`)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2"
              >
                <Edit2 className="h-4 w-4" />
                Edit
              </button>
              <button
                onClick={handlePost}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
              >
                <CheckCircle className="h-4 w-4" />
                Post
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </button>
            </>
          )}
          {isPosted && (
            <span className="px-3 py-2 bg-green-100 text-green-800 rounded-lg font-semibold">
              Posted
            </span>
          )}
        </div>
      </div>

      {/* Payment Details Card */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Payment Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-500">Supplier</label>
            <p className="mt-1 text-base text-gray-900">{payment.supplier_name || 'N/A'}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Date</label>
            <p className="mt-1 text-base text-gray-900">{payment.date}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Total Amount</label>
            <p className="mt-1 text-2xl font-bold text-gray-900">
              {payment.currency_code} {parseFloat(payment.total_amount || '0').toFixed(2)}
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Reference</label>
            <p className="mt-1 text-base text-gray-900">{payment.reference || 'N/A'}</p>
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-500">Memo</label>
            <p className="mt-1 text-base text-gray-900">{payment.memo || '-'}</p>
          </div>
        </div>
      </div>

      {/* Allocations Card */}
      {payment.allocations && payment.allocations.length > 0 && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Invoice Allocations</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Memo</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {payment.allocations.map((allocation: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-3 text-sm text-gray-900">{allocation.invoice_number || `Invoice #${allocation.invoice}`}</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 text-right">
                      {payment.currency_code} {parseFloat(allocation.amount).toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{allocation.memo || '-'}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-50">
                <tr>
                  <td className="px-4 py-3 text-sm font-semibold text-gray-700 text-right">
                    Total Allocated:
                  </td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-900 text-right">
                    {payment.currency_code} {parseFloat(payment.allocated_amount || '0').toFixed(2)}
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* GL Distribution */}
      {payment.gl_lines_display && payment.gl_lines_display.length > 0 && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">GL Distribution</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Account</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {payment.gl_lines_display.map((line: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <div className="font-medium">
                        {line.segments && line.segments.length > 0 
                          ? line.segments.map((seg: any) => seg.segment_code).join('-')
                          : 'N/A'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {line.segments && line.segments.length > 0 
                          ? line.segments.map((seg: any) => seg.segment_name).join(' - ')
                          : ''}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{line.description || '-'}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${
                        line.line_type === 'DEBIT' 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {line.line_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 text-right">
                      {payment.currency_code} {parseFloat(line.amount).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-50">
                <tr>
                  <td colSpan={3} className="px-4 py-3 text-sm font-semibold text-gray-700 text-right">
                    Total Debits / Credits:
                  </td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-900 text-right">
                    {payment.currency_code} {
                      payment.gl_lines_display
                        .filter((l: any) => l.line_type === 'DEBIT')
                        .reduce((sum: number, l: any) => sum + parseFloat(l.amount), 0)
                        .toFixed(2)
                    } / {payment.currency_code} {
                      payment.gl_lines_display
                        .filter((l: any) => l.line_type === 'CREDIT')
                        .reduce((sum: number, l: any) => sum + parseFloat(l.amount), 0)
                        .toFixed(2)
                    }
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

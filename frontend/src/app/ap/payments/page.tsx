'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apPaymentsAPI } from '../../../services/api';
import { APPayment } from '../../../types';
import { Plus, CheckCircle, Trash2, Edit2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

export default function APPaymentsPage() {
  const [payments, setPayments] = useState<APPayment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    try {
      const response = await apPaymentsAPI.list();
      setPayments(response.data);
    } catch (error) {
      toast.error('Failed to load payments');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handlePost = async (id: number) => {
    if (!confirm('Are you sure you want to post this payment?')) {
      return;
    }
    
    try {
      await apPaymentsAPI.post(id);
      toast.success('Payment posted successfully');
      fetchPayments();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to post payment');
      console.error(error);
    }
  };

  const handleDelete = async (id: number, amount: string) => {
    if (!confirm(`Are you sure you want to delete payment of $${amount}?`)) {
      return;
    }

    try {
      await apPaymentsAPI.delete(id);
      toast.success('Payment deleted successfully');
      fetchPayments();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to delete payment');
      console.error(error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading payments...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AP Payments</h1>
          <p className="mt-2 text-gray-600">Make payments to suppliers</p>
        </div>
        <Link href="/ap/payments/new" className="btn-primary flex items-center gap-2">
          <Plus className="h-5 w-5" />
          New Payment
        </Link>
      </div>

      <div className="table-wrapper">
        <table className="table-base">
          <thead className="table-header" style={{ backgroundColor: '#f9fafb' }}>
            <tr>
              <th className="table-th" scope="col" style={{ padding: '12px 24px', fontSize: '12px', fontWeight: 600, color: '#374151', textTransform: 'uppercase' }}>Payment Date</th>
              <th className="table-th" scope="col" style={{ padding: '12px 24px', fontSize: '12px', fontWeight: 600, color: '#374151', textTransform: 'uppercase' }}>Supplier</th>
              <th className="table-th" scope="col" style={{ padding: '12px 24px', fontSize: '12px', fontWeight: 600, color: '#374151', textTransform: 'uppercase' }}>Amount</th>
              <th className="table-th" scope="col" style={{ padding: '12px 24px', fontSize: '12px', fontWeight: 600, color: '#374151', textTransform: 'uppercase' }}>Currency</th>
              <th className="table-th" scope="col" style={{ padding: '12px 24px', fontSize: '12px', fontWeight: 600, color: '#374151', textTransform: 'uppercase' }}>FX Rate</th>
              <th className="table-th" scope="col" style={{ padding: '12px 24px', fontSize: '12px', fontWeight: 600, color: '#374151', textTransform: 'uppercase' }}>Reference</th>
              <th className="table-th" scope="col" style={{ padding: '12px 24px', fontSize: '12px', fontWeight: 600, color: '#374151', textTransform: 'uppercase' }}>Status</th>
              <th className="table-th" scope="col" style={{ padding: '12px 24px', fontSize: '12px', fontWeight: 600, color: '#374151', textTransform: 'uppercase' }}>Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {payments.map((payment) => {
              // Check if payment is cross-currency
              const isCrossCurrency = payment.invoice_currency_code && 
                                       payment.payment_currency_code && 
                                       payment.invoice_currency_code !== payment.payment_currency_code;
              
              return (
                <tr key={payment.id} className="hover:bg-gray-50">
                  <td className="table-td">
                    {payment.date 
                      ? format(new Date(payment.date), 'MMM dd, yyyy')
                      : '-'
                    }
                  </td>
                  <td className="table-td">{payment.supplier_name || `Supplier #${payment.supplier}`}</td>
                  <td className="table-td font-medium">${payment.total_amount}</td>
                  <td className="table-td">
                    <div className="flex items-center gap-1">
                      <span className="font-medium">{payment.payment_currency_code || payment.currency_code || '-'}</span>
                      {isCrossCurrency && (
                        <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded" title="Cross-currency payment">
                          FX
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="table-td">
                    {isCrossCurrency && payment.exchange_rate ? (
                      <div className="text-sm">
                        <span className="text-gray-600">
                          1 {payment.invoice_currency_code} = {parseFloat(payment.exchange_rate).toFixed(6)} {payment.payment_currency_code}
                        </span>
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="table-td">{payment.reference || '-'}</td>
                  <td className="table-td">
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        payment.posted_at
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {payment.posted_at ? 'POSTED' : 'DRAFT'}
                    </span>
                  </td>
                  <td className="table-td">
                    <div className="flex gap-2">
                      {!payment.posted_at && (
                        <Link
                          href={`/ap/payments/${payment.id}/edit`}
                          className="text-blue-600 hover:text-blue-900"
                          title="Edit Payment"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Link>
                      )}
                      {!payment.posted_at && (
                        <button
                          onClick={() => handlePost(payment.id!)}
                          className="text-sm text-green-600 hover:text-green-900 flex items-center gap-1"
                        >
                          <CheckCircle className="h-4 w-4" />
                          Post
                        </button>
                      )}
                      {!payment.posted_at && (
                        <button
                          onClick={() => handleDelete(payment.id!, payment.total_amount)}
                          className="text-red-600 hover:text-red-800"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {payments.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No payments found.
          </div>
        )}
      </div>
    </div>
  );
}

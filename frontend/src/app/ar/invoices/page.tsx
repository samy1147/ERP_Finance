'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { arInvoicesAPI, invoiceApprovalsAPI } from '../../../services/api';
import { ARInvoice } from '../../../types';
import { Plus, FileText, CheckCircle, Trash2, Edit2, Send } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

export default function ARInvoicesPage() {
  const router = useRouter();
  const [invoices, setInvoices] = useState<ARInvoice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    try {
      const response = await arInvoicesAPI.list();
      setInvoices(response.data);
    } catch (error) {
      toast.error('Failed to load invoices');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handlePostToGL = async (id: number) => {
    if (!confirm('Are you sure you want to post this invoice to the General Ledger?')) {
      return;
    }
    
    try {
      await arInvoicesAPI.post(id);
      toast.success('Invoice posted to GL successfully');
      fetchInvoices();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.error || 'Failed to post invoice';
      toast.error(errorMessage);
      console.error('GL Posting Error:', error.response?.data || error);
    }
  };

  const handleDelete = async (id: number, invoiceNumber: string) => {
    if (!confirm(`Are you sure you want to delete invoice "${invoiceNumber}"?`)) {
      return;
    }

    try {
      await arInvoicesAPI.delete(id);
      toast.success('Invoice deleted successfully');
      fetchInvoices();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to delete invoice');
      console.error(error);
    }
  };

  const handleSubmitForApproval = async (invoiceId: number, invoiceNumber: string) => {
    if (!confirm(`Submit invoice ${invoiceNumber} for approval?`)) {
      return;
    }

    try {
      const response = await arInvoicesAPI.submitForApproval(invoiceId, {
        submitted_by: 'Current User' // TODO: Get from authentication context
      });
      toast.success(`Invoice ${invoiceNumber} submitted for approval successfully`);
      fetchInvoices(); // Refresh the list to show updated status
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Failed to submit for approval';
      toast.error(errorMessage);
      console.error('Submit for approval error:', error.response?.data || error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading invoices...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AR Invoices</h1>
          <p className="mt-2 text-gray-600">Manage customer invoices</p>
        </div>
        <Link href="/ar/invoices/new" className="btn-primary flex items-center gap-2">
          <Plus className="h-5 w-5" />
          New Invoice
        </Link>
      </div>

      {/* Invoices Table */}
      <div className="table-wrapper">
        <table className="table-base">
          <thead className="table-header">
            <tr>
              <th className="table-th">Invoice #</th>
              <th className="table-th">Customer</th>
              <th className="table-th">Date</th>
              <th className="table-th">Due Date</th>
              <th className="table-th">Currency</th>
              <th className="table-th">Total</th>
              <th className="table-th">Rate</th>
              <th className="table-th">Base Total</th>
              <th className="table-th">Balance</th>
              <th className="table-th">Posting Status</th>
              <th className="table-th">Payment Status</th>
              <th className="table-th">Approval Status</th>
              <th className="table-th">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {invoices.map((invoice) => (
              <tr key={invoice.id} className="hover:bg-gray-50">
                <td className="table-td font-medium">{invoice.invoice_number}</td>
                <td className="table-td">{invoice.customer_name || `Customer #${invoice.customer}`}</td>
                <td className="table-td">{format(new Date(invoice.date), 'MMM dd, yyyy')}</td>
                <td className="table-td">{format(new Date(invoice.due_date), 'MMM dd, yyyy')}</td>
                <td className="table-td">
                  <span className="text-xs font-medium text-gray-600">{invoice.currency_code || 'N/A'}</span>
                </td>
                <td className="table-td font-mono">{invoice.currency_code || ''} {invoice.total || '0.00'}</td>
                <td className="table-td text-xs text-gray-500">
                  {invoice.exchange_rate ? parseFloat(invoice.exchange_rate).toFixed(4) : '—'}
                </td>
                <td className="table-td font-mono font-semibold">
                  {invoice.base_currency_total ? 
                    `${parseFloat(invoice.base_currency_total).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` 
                    : '—'}
                </td>
                <td className="table-td font-mono">{invoice.currency_code || ''} {invoice.balance || '0.00'}</td>
                {/* Column 1: Posting Status (Posted/Unposted) */}
                <td className="table-td">
                  {invoice.is_cancelled ? (
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                      Cancelled
                    </span>
                  ) : (
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        invoice.is_posted
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {invoice.is_posted ? 'Posted' : 'Unposted'}
                    </span>
                  )}
                </td>
                {/* Column 2: Payment Status (Paid/Unpaid/Partially Paid) */}
                <td className="table-td">
                  {!invoice.is_cancelled ? (
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        invoice.payment_status === 'PAID'
                          ? 'bg-blue-100 text-blue-800'
                          : invoice.payment_status === 'PARTIALLY_PAID'
                          ? 'bg-purple-100 text-purple-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {invoice.payment_status === 'PAID' 
                        ? 'Paid' 
                        : invoice.payment_status === 'PARTIALLY_PAID' 
                        ? 'Partially Paid' 
                        : invoice.payment_status || 'Unpaid'}
                    </span>
                  ) : (
                    <span className="px-2 py-1 text-xs text-gray-400">—</span>
                  )}
                </td>
                {/* Column 3: Approval Status (Pending/Approved/Rejected) */}
                <td className="table-td">
                  {invoice.approval_status ? (
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        invoice.approval_status === 'APPROVED'
                          ? 'bg-emerald-100 text-emerald-800'
                          : invoice.approval_status === 'REJECTED'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {invoice.approval_status === 'PENDING_APPROVAL'
                        ? 'Pending' 
                        : invoice.approval_status === 'APPROVED'
                        ? 'Approved'
                        : invoice.approval_status === 'REJECTED'
                        ? 'Rejected'
                        : invoice.approval_status}
                    </span>
                  ) : (
                    <span className="px-2 py-1 text-xs text-gray-400">—</span>
                  )}
                </td>
                <td className="table-td">
                  <div className="flex gap-2">
                    {/* Edit - Only for Draft (not posted, not cancelled) */}
                    {!invoice.is_posted && !invoice.is_cancelled && (
                      <button
                        onClick={() => router.push(`/ar/invoices/${invoice.id}/edit`)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Edit Invoice"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                    )}
                    {/* Submit for Approval - Only for Draft status */}
                    {!invoice.is_posted && !invoice.is_cancelled && 
                     (invoice.approval_status === 'DRAFT' || !invoice.approval_status) && (
                      <button
                        onClick={() => handleSubmitForApproval(invoice.id, invoice.invoice_number)}
                        className="text-purple-600 hover:text-purple-900"
                        title="Submit for Approval"
                      >
                        <Send className="h-4 w-4" />
                      </button>
                    )}
                    {/* Post to GL - Only for Draft */}
                    {!invoice.is_posted && !invoice.is_cancelled && (
                      <button
                        onClick={() => handlePostToGL(invoice.id)}
                        className="text-green-600 hover:text-green-900"
                        title="Post to GL"
                      >
                        <CheckCircle className="h-4 w-4" />
                      </button>
                    )}
                    {/* Delete - Only for Draft */}
                    {!invoice.is_posted && !invoice.is_cancelled && (
                      <button
                        onClick={() => handleDelete(invoice.id, invoice.invoice_number)}
                        className="text-red-600 hover:text-red-800"
                        title="Delete Invoice"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                    {/* View - For all invoices */}
                    <Link
                      href={`/ar/invoices/${invoice.id}`}
                      className="text-gray-600 hover:text-gray-900"
                      title="View Invoice"
                    >
                      <FileText className="h-4 w-4" />
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {invoices.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No invoices found. Create your first invoice!
          </div>
        )}
      </div>
    </div>
  );
}

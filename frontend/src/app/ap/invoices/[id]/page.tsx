'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apInvoicesAPI } from '../../../../services/api';
import { APInvoice } from '../../../../types';
import { Edit2, Trash2, CheckCircle, XCircle, Send } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ViewAPInvoicePage() {
  const router = useRouter();
  const params = useParams();
  const invoiceId = params.id as string;
  
  const [loading, setLoading] = useState(true);
  const [invoice, setInvoice] = useState<any | null>(null);

  useEffect(() => {
    fetchInvoice();
  }, [invoiceId]);

  const fetchInvoice = async () => {
    try {
      setLoading(true);
      const response = await apInvoicesAPI.get(parseInt(invoiceId));
      setInvoice(response.data);
    } catch (error: any) {
      console.error('Failed to load invoice:', error);
      toast.error(error.response?.data?.error || 'Failed to load invoice');
      router.push('/ap/invoices');
    } finally {
      setLoading(false);
    }
  };

  const handlePost = async () => {
    if (!invoice) return;
    
    if (window.confirm('Are you sure you want to post this invoice? This action cannot be undone.')) {
      try {
        await apInvoicesAPI.post(invoice.id);
        toast.success('Invoice posted successfully');
        fetchInvoice();
      } catch (error: any) {
        toast.error(error.response?.data?.error || 'Failed to post invoice');
      }
    }
  };

  const handleSubmitForApproval = async () => {
    if (!invoice) return;
    
    if (window.confirm(`Submit invoice ${invoice.invoice_number} for approval?`)) {
      try {
        await apInvoicesAPI.submitForApproval(invoice.id, {
          submitted_by: 'Current User' // TODO: Get from authentication context
        });
        toast.success('Invoice submitted for approval successfully');
        fetchInvoice(); // Refresh to show updated status
      } catch (error: any) {
        const errorMessage = error.response?.data?.error || 'Failed to submit for approval';
        toast.error(errorMessage);
        console.error('Submit for approval error:', error.response?.data || error);
      }
    }
  };

  const handleDelete = async () => {
    if (!invoice) return;
    
    if (window.confirm('Are you sure you want to delete this invoice?')) {
      try {
        await apInvoicesAPI.delete(invoice.id);
        toast.success('Invoice deleted successfully');
        router.push('/ap/invoices');
      } catch (error: any) {
        toast.error(error.response?.data?.error || 'Failed to delete invoice');
      }
    }
  };

  const getStatusBadge = (invoice: APInvoice) => {
    if (invoice.is_cancelled) {
      return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Cancelled</span>;
    }
    if (!invoice.is_posted) {
      return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">Draft</span>;
    }
    if (invoice.payment_status === 'PAID') {
      return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Paid</span>;
    }
    if (invoice.payment_status === 'PARTIALLY_PAID') {
      return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">Partially Paid</span>;
    }
    if (invoice.payment_status === 'UNPAID') {
      return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">Unpaid</span>;
    }
    return null;
  };

  const calculateLineTotal = (item: any) => {
    const subtotal = parseFloat(item.quantity) * parseFloat(item.unit_price);
    const taxRate = item.tax_rate_details ? parseFloat(item.tax_rate_details.rate) : 0;
    const tax = subtotal * (taxRate / 100);
    return {
      subtotal,
      tax,
      total: subtotal + tax
    };
  };

  const calculateInvoiceTotals = () => {
    if (!invoice || !invoice.items) return { subtotal: 0, tax: 0, total: 0 };
    
    let subtotal = 0;
    let tax = 0;
    
    invoice.items.forEach((item: any) => {
      const lineCalc = calculateLineTotal(item);
      subtotal += lineCalc.subtotal;
      tax += lineCalc.tax;
    });
    
    return {
      subtotal,
      tax,
      total: subtotal + tax
    };
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading invoice...</div>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Invoice not found</div>
      </div>
    );
  }

  const isDraft = !invoice.is_posted && !invoice.is_cancelled;
  const isApproved = invoice.approval_status === 'APPROVED';
  const isPendingApproval = invoice.approval_status === 'PENDING_APPROVAL';
  const isRejected = invoice.approval_status === 'REJECTED';
  const isDraftStatus = !invoice.approval_status || invoice.approval_status === 'DRAFT';
  const totals = calculateInvoiceTotals();

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AP Invoice #{invoice.invoice_number}</h1>
          <p className="mt-2 text-gray-600">Invoice Details</p>
        </div>
        <div className="flex gap-2">
          {/* Edit and Delete: Only available in DRAFT status (not submitted for approval, not posted) */}
          {isDraft && isDraftStatus && (
            <>
              <button
                onClick={() => router.push(`/ap/invoices/${invoice.id}/edit`)}
                className="btn-secondary flex items-center gap-2"
              >
                <Edit2 className="h-4 w-4" />
                Edit
              </button>
              <button
                onClick={handleDelete}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </button>
            </>
          )}
          
          {/* Submit for Approval: Only in DRAFT or REJECTED status */}
          {isDraft && (isDraftStatus || isRejected) && (
            <button
              onClick={handleSubmitForApproval}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
            >
              <Send className="h-4 w-4" />
              Submit for Approval
            </button>
          )}
          
          {/* Post to GL: Only when APPROVED */}
          {isDraft && isApproved && (
            <button
              onClick={handlePost}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
            >
              <CheckCircle className="h-4 w-4" />
              Post
            </button>
          )}
          
          {/* Back Button: Always available */}
          <button
            onClick={() => router.push('/ap/invoices')}
            className="btn-secondary"
          >
            Back to List
          </button>
        </div>
      </div>

      {/* Invoice Details Card */}
      <div className="card mb-6">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-xl font-semibold">Invoice Information</h2>
          <div className="flex gap-2">
            {getStatusBadge(invoice)}
            {invoice.approval_status && (
              <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                invoice.approval_status === 'APPROVED' ? 'bg-green-100 text-green-800'
                : invoice.approval_status === 'REJECTED' ? 'bg-red-100 text-red-800'
                : invoice.approval_status === 'PENDING_APPROVAL' ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-800'
              }`}>
                {invoice.approval_status === 'PENDING_APPROVAL' ? 'Pending Approval' 
                 : invoice.approval_status === 'APPROVED' ? 'Approved'
                 : invoice.approval_status === 'REJECTED' ? 'Rejected'
                 : invoice.approval_status}
              </span>
            )}
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-500">Supplier</label>
            <p className="mt-1 text-base text-gray-900">{invoice.supplier_details?.name || invoice.supplier_name || 'N/A'}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Invoice Number</label>
            <p className="mt-1 text-base text-gray-900">{invoice.invoice_number}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Date</label>
            <p className="mt-1 text-base text-gray-900">{invoice.date}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Due Date</label>
            <p className="mt-1 text-base text-gray-900">{invoice.due_date}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Currency</label>
            <p className="mt-1 text-base text-gray-900">{invoice.currency_details?.code || 'USD'}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500">Country</label>
            <p className="mt-1 text-base text-gray-900">
              {invoice.country === 'AE' ? 'UAE' : 
               invoice.country === 'SA' ? 'Saudi Arabia' :
               invoice.country === 'EG' ? 'Egypt' :
               invoice.country === 'IN' ? 'India' : invoice.country}
            </p>
          </div>
        </div>
      </div>

      {/* Line Items Card */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold mb-4">Line Items</h2>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Unit Price</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tax Rate</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Subtotal</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Tax</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {invoice.items && invoice.items.map((item: any, index: number) => {
                const lineCalc = calculateLineTotal(item);
                return (
                  <tr key={index}>
                    <td className="px-4 py-3 text-sm text-gray-900">{item.description}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-right">{parseFloat(item.quantity).toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-right">
                      {invoice.currency_details?.code} {parseFloat(item.unit_price).toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {item.tax_rate_details ? `${item.tax_rate_details.name} (${item.tax_rate_details.rate}%)` : 'No Tax'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-right">
                      {invoice.currency_details?.code} {lineCalc.subtotal.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-right">
                      {invoice.currency_details?.code} {lineCalc.tax.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 text-right">
                      {invoice.currency_details?.code} {lineCalc.total.toFixed(2)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Totals */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex justify-end">
            <div className="text-right space-y-2 min-w-[300px]">
              <div className="flex justify-between gap-8">
                <span className="text-sm text-gray-600">Subtotal:</span>
                <span className="text-sm font-medium text-gray-900">
                  {invoice.currency_details?.code} {totals.subtotal.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between gap-8">
                <span className="text-sm text-gray-600">Tax:</span>
                <span className="text-sm font-medium text-gray-900">
                  {invoice.currency_details?.code} {totals.tax.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between gap-8 pt-2 border-t border-gray-200">
                <span className="text-base font-semibold text-gray-700">Total (Invoice Currency):</span>
                <span className="text-2xl font-bold text-gray-900">
                  {invoice.currency_details?.code} {totals.total.toFixed(2)}
                </span>
              </div>
              {invoice.base_currency_total && (
                <div className="flex justify-between gap-8 pt-2 border-t border-gray-200">
                  <span className="text-sm text-gray-600">Total (Base Currency):</span>
                  <span className="text-base font-semibold text-gray-900">
                    {invoice.base_currency_total}
                  </span>
                </div>
              )}
              <div className="text-xs text-gray-500 mt-2">
                Tax calculated in invoice currency
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Payment Information (if posted) */}
      {invoice.is_posted && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Payment Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Payment Status</label>
              <p className="mt-1 text-base text-gray-900">{invoice.payment_status}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Amount Paid</label>
              <p className="mt-1 text-base text-gray-900">
                {invoice.currency_details?.code} {invoice.amount_paid || '0.00'}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Balance Due</label>
              <p className="mt-1 text-base text-gray-900">
                {invoice.currency_details?.code} {invoice.balance_due || totals.total.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

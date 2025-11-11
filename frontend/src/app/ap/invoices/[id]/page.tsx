'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apInvoicesAPI } from '../../../../services/api';
import { APInvoice } from '../../../../types';
import { Edit2, Trash2, CheckCircle, XCircle, Send, Shield, AlertCircle, CheckCheck } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ViewAPInvoicePage() {
  const router = useRouter();
  const params = useParams();
  const invoiceId = params.id as string;
  
  const [loading, setLoading] = useState(true);
  const [matchLoading, setMatchLoading] = useState(false);
  const [invoice, setInvoice] = useState<any | null>(null);
  const [varianceDetails, setVarianceDetails] = useState<any[]>([]);
  const [showVarianceModal, setShowVarianceModal] = useState(false);

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

  const handleRunThreeWayMatch = async () => {
    if (!invoice) return;
    
    try {
      setMatchLoading(true);
      const response = await apInvoicesAPI.threeWayMatch(invoice.id);
      const result = response.data;
      
      // Update invoice state
      setInvoice((prev: any) => ({
        ...prev,
        three_way_match_status: result.status,
        match_variance_amount: result.variance_amount,
        match_variance_notes: result.notes
      }));
      
      // Show variance details if any
      if (result.variance_details && result.variance_details.length > 0) {
        setVarianceDetails(result.variance_details);
        setShowVarianceModal(true);
        toast(`Match completed with ${result.variance_details.length} variance(s)`, {
          icon: '⚠️',
          duration: 5000,
        });
      } else {
        toast.success('Invoice matched successfully! No variances detected.');
      }
    } catch (error: any) {
      console.error('Error running 3-way match:', error);
      const errorMessage = error.response?.data?.error || 'Error running match validation';
      toast.error(errorMessage);
    } finally {
      setMatchLoading(false);
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

  const getMatchStatusBadge = (status: string) => {
    switch (status) {
      case 'MATCHED':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 flex items-center gap-1">
            <CheckCheck className="h-3 w-3" />
            Matched
          </span>
        );
      case 'VARIANCE':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800 flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            Variance
          </span>
        );
      case 'FAILED':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800 flex items-center gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </span>
        );
      case 'NOT_REQUIRED':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
            Not Required
          </span>
        );
      default:
        return null;
    }
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

      {/* 3-Way Match Section - Only show if invoice is linked to GRN */}
      {(invoice.goods_receipt || invoice.goods_receipt_id || invoice.grn_number || invoice.grn) && (
        <div className="card mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Shield className="h-5 w-5 text-blue-600" />
                3-Way Match Validation
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Validates invoice against GRN (Receipt) and Purchase Order
              </p>
            </div>
            <button
              onClick={handleRunThreeWayMatch}
              disabled={matchLoading}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                matchLoading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700'
              } text-white`}
            >
              {matchLoading ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  Running Match...
                </>
              ) : (
                <>
                  <Shield className="h-4 w-4" />
                  Run 3-Way Match
                </>
              )}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-gray-500">GRN Number</label>
              <p className="mt-1 text-base text-gray-900">{invoice.grn_number || invoice.goods_receipt || invoice.grn || 'N/A'}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">PO Number</label>
              <p className="mt-1 text-base text-gray-900">{invoice.po_number || invoice.po_header || 'N/A'}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500">Match Status</label>
              <div className="mt-1">
                {invoice.three_way_match_status ? (
                  getMatchStatusBadge(invoice.three_way_match_status)
                ) : (
                  <span className="text-sm text-gray-500">Not Run</span>
                )}
              </div>
            </div>
          </div>

          {/* Match Variance Info */}
          {invoice.three_way_match_status && (invoice.three_way_match_status === 'VARIANCE' || invoice.three_way_match_status === 'FAILED') && (
            <div className={`mt-4 p-4 rounded-lg border-l-4 ${
              invoice.three_way_match_status === 'FAILED' 
                ? 'bg-red-50 border-red-500' 
                : 'bg-yellow-50 border-yellow-500'
            }`}>
              <div className="flex items-start gap-3">
                <AlertCircle className={`h-5 w-5 mt-0.5 ${
                  invoice.three_way_match_status === 'FAILED' ? 'text-red-600' : 'text-yellow-600'
                }`} />
                <div className="flex-1">
                  <h3 className={`font-semibold ${
                    invoice.three_way_match_status === 'FAILED' ? 'text-red-800' : 'text-yellow-800'
                  }`}>
                    {invoice.three_way_match_status === 'FAILED' ? 'Critical Variance Detected' : 'Variance Detected'}
                  </h3>
                  <p className={`text-sm mt-1 ${
                    invoice.three_way_match_status === 'FAILED' ? 'text-red-700' : 'text-yellow-700'
                  }`}>
                    {invoice.match_variance_notes}
                  </p>
                  {invoice.match_variance_amount && parseFloat(invoice.match_variance_amount) > 0 && (
                    <p className={`text-sm font-semibold mt-2 ${
                      invoice.three_way_match_status === 'FAILED' ? 'text-red-800' : 'text-yellow-800'
                    }`}>
                      Total Variance Amount: {invoice.currency_details?.code || 'USD'} {parseFloat(invoice.match_variance_amount).toFixed(2)}
                    </p>
                  )}
                  {varianceDetails.length > 0 && (
                    <button
                      onClick={() => setShowVarianceModal(true)}
                      className={`mt-3 text-sm font-medium underline ${
                        invoice.three_way_match_status === 'FAILED' ? 'text-red-700' : 'text-yellow-700'
                      }`}
                    >
                      View Detailed Variance Report →
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Match Success Info */}
          {invoice.three_way_match_status === 'MATCHED' && (
            <div className="mt-4 p-4 rounded-lg border-l-4 bg-green-50 border-green-500">
              <div className="flex items-start gap-3">
                <CheckCheck className="h-5 w-5 mt-0.5 text-green-600" />
                <div>
                  <h3 className="font-semibold text-green-800">Invoice Matched Successfully</h3>
                  <p className="text-sm text-green-700 mt-1">
                    All line items match the GRN and Purchase Order within acceptable tolerances.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Approval Blocking Warning */}
          {invoice.three_way_match_status === 'FAILED' && isDraft && (
            <div className="mt-4 p-4 rounded-lg bg-red-100 border border-red-300">
              <div className="flex items-start gap-3">
                <XCircle className="h-5 w-5 mt-0.5 text-red-600" />
                <div>
                  <h3 className="font-semibold text-red-800">Approval Blocked</h3>
                  <p className="text-sm text-red-700 mt-1">
                    This invoice cannot be approved due to critical variances. Please review and resolve the variances before proceeding with approval.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Variance Details Modal */}
      {showVarianceModal && varianceDetails.length > 0 && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Variance Details Report</h2>
              <button
                onClick={() => setShowVarianceModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <XCircle className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-auto p-6">
              <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> The following variances were detected when comparing the invoice 
                  against the Goods Receipt Note (GRN) and Purchase Order (PO). Please review each variance 
                  and take appropriate action.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Line
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Item
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Issue
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Invoice Value
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Expected Value
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Variance
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        %
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {varianceDetails.map((detail, index) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                          {detail.line_number}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {detail.item}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            detail.issue.includes('exceeds') 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {detail.issue}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                          {parseFloat(detail.invoice_value).toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 text-right">
                          {parseFloat(detail.expected_value).toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-sm text-red-600 text-right font-semibold">
                          {parseFloat(detail.variance_amount).toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-sm text-red-600 text-right font-semibold">
                          {parseFloat(detail.variance_percentage).toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Summary */}
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm text-gray-600">Total Variances Detected:</p>
                    <p className="text-lg font-semibold text-gray-900">{varianceDetails.length} line item(s)</p>
                  </div>
                  {invoice.match_variance_amount && (
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Total Variance Amount:</p>
                      <p className="text-2xl font-bold text-red-600">
                        {invoice.currency_details?.code || 'USD'} {parseFloat(invoice.match_variance_amount).toFixed(2)}
                      </p>
                    </div>
                  )}
                </div>
                {invoice.match_variance_notes && (
                  <p className="text-sm text-gray-700 mt-4 pt-4 border-t border-gray-200">
                    <strong>Notes:</strong> {invoice.match_variance_notes}
                  </p>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={() => setShowVarianceModal(false)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

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

      {/* GL Distribution */}
      {invoice.gl_lines && invoice.gl_lines.length > 0 && (
        <div className="card mt-6">
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
                {invoice.gl_lines.map((line: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <div className="font-medium">{line.account_code || 'N/A'}</div>
                      <div className="text-xs text-gray-500">{line.account_name || ''}</div>
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
                      {invoice.currency_details?.code} {parseFloat(line.amount).toFixed(2)}
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
                    {invoice.currency_details?.code} {
                      invoice.gl_lines
                        .filter((l: any) => l.line_type === 'DEBIT')
                        .reduce((sum: number, l: any) => sum + parseFloat(l.amount), 0)
                        .toFixed(2)
                    } / {invoice.currency_details?.code} {
                      invoice.gl_lines
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

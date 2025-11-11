'use client';

import React, { useState, useEffect } from 'react';
import { vendorBillsAPI } from '../../../services/procurement-api';
import { VendorBill } from '../../../types/procurement';
import { Plus, Edit, Trash2, Search, FileText, CheckCircle, XCircle, Eye, Send } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function VendorBillsPage() {
  const [bills, setBills] = useState<VendorBill[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [matchStatusFilter, setMatchStatusFilter] = useState<string>('');

  useEffect(() => {
    fetchBills();
  }, [statusFilter, matchStatusFilter]);

  const fetchBills = async () => {
    try {
      const params: any = {};
      if (statusFilter) params.status = statusFilter;
      if (matchStatusFilter) params.match_status = matchStatusFilter;
      
      const response = await vendorBillsAPI.list(params);
      // Handle both array and object responses
      const data = Array.isArray(response.data) ? response.data : ((response.data as any)?.results || []);
      console.log('Fetched bills:', data);
      setBills(data);
    } catch (error: any) {
      toast.error('Failed to load vendor bills');
      console.error('Error fetching bills:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePerformMatch = async (id: number) => {
    try {
      const response = await vendorBillsAPI.performMatch(id);
      const message = (response as any).message || 'Match completed successfully';
      toast.success(message);
      fetchBills();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to perform match');
      console.error(error);
    }
  };

  const handleSubmitBill = async (id: number) => {
    try {
      await vendorBillsAPI.submit(id);
      toast.success('Bill submitted successfully');
      fetchBills();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to submit bill');
      console.error(error);
    }
  };

  const handleApproveBill = async (id: number) => {
    try {
      await vendorBillsAPI.approveBill(id);
      toast.success('Bill approved successfully');
      fetchBills();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to approve bill');
      console.error(error);
    }
  };

  const handlePostBill = async (id: number) => {
    try {
      await vendorBillsAPI.postBill(id);
      toast.success('Bill posted successfully');
      fetchBills();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to post bill');
      console.error(error);
    }
  };

  const handleDelete = async (id: number, billNumber: string) => {
    if (!confirm(`Are you sure you want to delete bill "${billNumber}"?`)) return;

    try {
      await vendorBillsAPI.delete(id);
      toast.success('Bill deleted successfully');
      fetchBills();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to delete bill');
      console.error(error);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      SUBMITTED: 'bg-blue-100 text-blue-800',
      PENDING_MATCH: 'bg-yellow-100 text-yellow-800',
      MATCHED: 'bg-green-100 text-green-800',
      EXCEPTION: 'bg-orange-100 text-orange-800',
      APPROVED: 'bg-blue-100 text-blue-800',
      POSTED: 'bg-purple-100 text-purple-800',
      PAID: 'bg-green-100 text-green-800',
      CANCELLED: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getMatchStatusBadge = (matchStatus: string) => {
    const colors: Record<string, string> = {
      UNMATCHED: 'bg-gray-100 text-gray-800',
      PARTIAL: 'bg-yellow-100 text-yellow-800',
      FULLY_MATCHED: 'bg-green-100 text-green-800',
      OVER_RECEIPT: 'bg-red-100 text-red-800',
    };
    return colors[matchStatus] || 'bg-gray-100 text-gray-800';
  };

  const filteredBills = bills.filter(bill =>
    bill.bill_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    bill.supplier_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading vendor bills...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Vendor Bills</h1>
        <Link href="/procurement/vendor-bills/new">
          <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 flex items-center gap-2">
            <Plus size={20} />
            New Vendor Bill
          </button>
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-3 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search bills..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <select
            className="px-4 py-2 border rounded-lg"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="PENDING_MATCH">Pending Match</option>
            <option value="MATCHED">Matched</option>
            <option value="EXCEPTION">Exception</option>
            <option value="APPROVED">Approved</option>
            <option value="POSTED">Posted</option>
            <option value="PAID">Paid</option>
            <option value="CANCELLED">Cancelled</option>
          </select>

          <select
            className="px-4 py-2 border rounded-lg"
            value={matchStatusFilter}
            onChange={(e) => setMatchStatusFilter(e.target.value)}
          >
            <option value="">All Match Statuses</option>
            <option value="UNMATCHED">Unmatched</option>
            <option value="PARTIAL">Partial Match</option>
            <option value="FULLY_MATCHED">Fully Matched</option>
            <option value="OVER_RECEIPT">Over Receipt</option>
          </select>

          <button
            onClick={fetchBills}
            className="bg-gray-100 px-4 py-2 rounded-lg hover:bg-gray-200"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Bills Table */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Bill #</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supplier</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Balance</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Match</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredBills.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                  No vendor bills found
                </td>
              </tr>
            ) : (
              filteredBills.map((bill) => {
                console.log('Rendering bill:', bill.id, bill.bill_number, bill.status);
                return (
                <tr key={bill.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link href={`/procurement/vendor-bills/${bill.id}`} className="text-blue-600 hover:underline">
                      {bill.bill_number}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">{bill.supplier_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{bill.invoice_date}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {bill.currency_code} {parseFloat(bill.total_amount).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {bill.currency_code} {parseFloat(bill.balance_due).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(bill.status)}`}>
                      {bill.status?.replace('_', ' ') || 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${getMatchStatusBadge(bill.match_status)}`}>
                      {bill.match_status?.replace('_', ' ') || 'Not Matched'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex gap-2 items-center">
                      {/* DEBUG TEXT - Remove after testing */}
                      <span className="text-red-600 font-bold">ACTIONS HERE →</span>
                      
                      {/* View button - ALWAYS VISIBLE */}
                      <Link 
                        href={`/procurement/vendor-bills/${bill.id}`}
                        className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 inline-flex items-center gap-1"
                      >
                        <Eye size={16} />
                        <span>View</span>
                      </Link>
                      
                      {/* DRAFT status actions */}
                      {bill.status === 'DRAFT' && (
                        <>
                          <button
                            onClick={() => handleSubmitBill(bill.id)}
                            className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 inline-flex items-center gap-1"
                          >
                            <Send size={16} />
                            <span>Submit</span>
                          </button>
                          <Link 
                            href={`/procurement/vendor-bills/${bill.id}/edit`}
                            className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600 inline-flex items-center gap-1"
                          >
                            <Edit size={16} />
                            <span>Edit</span>
                          </Link>
                          <button
                            onClick={() => handleDelete(bill.id, bill.bill_number)}
                            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 inline-flex items-center gap-1"
                          >
                            <Trash2 size={16} />
                            <span>Delete</span>
                          </button>
                        </>
                      )}
                      
                      {/* SUBMITTED or PENDING_MATCH status actions */}
                      {(bill.status === 'SUBMITTED' || bill.status === 'PENDING_MATCH') && (
                        <button
                          onClick={() => handlePerformMatch(bill.id)}
                          className="px-3 py-1 bg-purple-500 text-white rounded hover:bg-purple-600 inline-flex items-center gap-1"
                        >
                          <FileText size={16} />
                          <span>Match</span>
                        </button>
                      )}
                      
                      {/* EXCEPTION status actions */}
                      {bill.status === 'EXCEPTION' && (
                        <button
                          onClick={() => handlePerformMatch(bill.id)}
                          className="px-3 py-1 bg-orange-500 text-white rounded hover:bg-orange-600 inline-flex items-center gap-1"
                        >
                          <FileText size={16} />
                          <span>Re-Match</span>
                        </button>
                      )}
                      
                      {/* MATCHED status actions */}
                      {bill.status === 'MATCHED' && bill.approval_status === 'PENDING' && (
                        <button
                          onClick={() => handleApproveBill(bill.id)}
                          className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 inline-flex items-center gap-1"
                        >
                          <CheckCircle size={16} />
                          <span>Approve</span>
                        </button>
                      )}
                      
                      {/* APPROVED status actions */}
                      {bill.status === 'APPROVED' && (
                        <button
                          onClick={() => handlePostBill(bill.id)}
                          className="px-3 py-1 bg-indigo-500 text-white rounded hover:bg-indigo-600 inline-flex items-center gap-1"
                        >
                          <FileText size={16} />
                          <span>Post</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <div className="mt-6 bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-600">{filteredBills.length}</div>
            <div className="text-sm text-gray-600">Total Bills</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-yellow-600">
              {filteredBills.filter(b => b.status === 'PENDING_MATCH').length}
            </div>
            <div className="text-sm text-gray-600">Pending Match</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">
              {filteredBills.filter(b => b.match_status === 'FULLY_MATCHED').length}
            </div>
            <div className="text-sm text-gray-600">Matched</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-600">
              {filteredBills.filter(b => b.status === 'POSTED').length}
            </div>
            <div className="text-sm text-gray-600">Posted</div>
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import { prHeadersAPI } from '../../../services/procurement-api';
import { PRHeader } from '../../../types/procurement';
import { Plus, Search, Eye, CheckCircle, XCircle, FileText, DollarSign, Clock, AlertCircle, ShoppingCart } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function RequisitionsPage() {
  const [requisitions, setRequisitions] = useState<PRHeader[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [view, setView] = useState<'my' | 'pending' | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetchRequisitions();
    fetchStatistics();
  }, [view, statusFilter]);

  const fetchRequisitions = async () => {
    try {
      setLoading(true);
      let response;
      
      if (view === 'my') {
        // Pass user ID 2 (admin) for non-authenticated requests
        // TODO: Get from auth context when authentication is implemented
        response = await prHeadersAPI.myPRs(2);
      } else if (view === 'pending') {
        response = await prHeadersAPI.pendingApproval();
      } else {
        const params: any = {};
        if (statusFilter) params.status = statusFilter;
        response = await prHeadersAPI.list(params);
      }
      
      setRequisitions(response.data.results || response.data);
    } catch (error: any) {
      toast.error('Failed to load requisitions');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await prHeadersAPI.statistics();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load statistics', error);
    }
  };

  // Removed direct approve/reject - must use approval workflow
  // const handleApprove = async (id: number, prNumber: string) => {
  //   if (!confirm(`Are you sure you want to approve PR ${prNumber}?`)) return;
  //   
  //   try {
  //     await prHeadersAPI.approve(id);
  //     toast.success('Requisition approved successfully');
  //     fetchRequisitions();
  //   } catch (error: any) {
  //     toast.error(error.response?.data?.error || 'Failed to approve requisition');
  //     console.error(error);
  //   }
  // };

  // const handleReject = async (id: number, prNumber: string) => {
  //   const reason = prompt(`Rejection reason for PR ${prNumber}:`);
  //   if (!reason) return;
  //   
  //   try {
  //     await prHeadersAPI.reject(id, { rejection_reason: reason });
  //     toast.success('Requisition rejected');
  //     fetchRequisitions();
  //   } catch (error: any) {
  //     toast.error(error.response?.data?.error || 'Failed to reject requisition');
  //     console.error(error);
  //   }
  // };

  const handleCheckBudget = async (id: number) => {
    try {
      const response = await prHeadersAPI.checkBudget(id);
      if (response.data.budget_available) {
        toast.success(`Budget available: $${response.data.available_amount}`);
      } else {
        toast.error(`Insufficient budget. Shortfall: $${response.data.shortfall}`);
      }
    } catch (error: any) {
      toast.error('Failed to check budget');
      console.error(error);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      SUBMITTED: 'bg-blue-100 text-blue-800',
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
      CONVERTED: 'bg-purple-100 text-purple-800',
      CANCELLED: 'bg-gray-400 text-white',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityBadge = (priority: string) => {
    const colors: Record<string, string> = {
      LOW: 'bg-gray-100 text-gray-800',
      MEDIUM: 'bg-blue-100 text-blue-800',
      HIGH: 'bg-orange-100 text-orange-800',
      URGENT: 'bg-red-100 text-red-800',
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  const filteredRequisitions = requisitions.filter(pr =>
    pr.pr_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pr.requester_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Purchase Requisitions</h1>
            <p className="text-gray-600">Manage purchase requests and approvals</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/procurement/pr-to-po"
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-colors font-semibold"
            >
              <ShoppingCart size={20} />
              Create PO from PRs
            </Link>
            <Link
              href="/procurement/requisitions/new"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus size={20} />
              New Requisition
            </Link>
          </div>
        </div>

        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center gap-2 mb-2">
                <FileText size={20} className="text-blue-600" />
                <div className="text-sm text-gray-600">Total PRs</div>
              </div>
              <div className="text-2xl font-bold text-gray-900">{stats.total_prs || 0}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center gap-2 mb-2">
                <Clock size={20} className="text-yellow-600" />
                <div className="text-sm text-gray-600">Pending Approval</div>
              </div>
              <div className="text-2xl font-bold text-yellow-600">{stats.pending_approval || 0}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle size={20} className="text-green-600" />
                <div className="text-sm text-gray-600">Approved</div>
              </div>
              <div className="text-2xl font-bold text-green-600">{stats.approved || 0}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign size={20} className="text-purple-600" />
                <div className="text-sm text-gray-600">Total Value</div>
              </div>
              <div className="text-2xl font-bold text-purple-600">${stats.total_value || 0}</div>
            </div>
          </div>
        )}
      </div>

      {/* View Tabs */}
      <div className="mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setView('my')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              view === 'my'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            My PRs
          </button>
          <button
            onClick={() => setView('pending')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              view === 'pending'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            Pending My Approval
            {stats?.pending_my_approval > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
                {stats.pending_my_approval}
              </span>
            )}
          </button>
          <button
            onClick={() => setView('all')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              view === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            All PRs
          </button>
        </div>
      </div>

      {/* Info Banner for Pending Approval View */}
      {view === 'pending' && requisitions.filter(pr => pr.status === 'SUBMITTED').length > 0 && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="text-blue-600 flex-shrink-0 mt-0.5" size={20} />
          <div className="flex-1">
            <h3 className="font-semibold text-blue-900 mb-1">Approval Workflow Required</h3>
            <p className="text-blue-700 text-sm">
              PRs with SUBMITTED status require formal approval through the approval workflow. 
              Click "Go to Approvals" to review and approve/reject these requests.
            </p>
          </div>
          <Link
            href="/procurement/approvals"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap"
          >
            Go to Approvals →
          </Link>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search by PR# or requester..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          {view === 'all' && (
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Status</option>
              <option value="DRAFT">Draft</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="CONVERTED">Converted to PO</option>
            </select>
          )}

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

      {/* Requisitions List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex justify-center items-center py-12 bg-white rounded-lg shadow">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredRequisitions.length === 0 ? (
          <div className="bg-white rounded-lg shadow text-center py-12">
            <FileText size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 mb-4">No requisitions found</p>
            {view === 'my' && (
              <Link
                href="/procurement/requisitions/new"
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus size={20} />
                Create First Requisition
              </Link>
            )}
          </div>
        ) : (
          filteredRequisitions.map((pr) => (
            <div key={pr.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-gray-900">PR #{pr.pr_number}</h3>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(pr.status)}`}>
                        {pr.status}
                      </span>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPriorityBadge(pr.priority)}`}>
                        {pr.priority}
                      </span>
                      {pr.pr_type && (
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          pr.pr_type === 'SERVICES' 
                            ? 'bg-purple-100 text-purple-800' 
                            : pr.pr_type === 'CATEGORIZED_GOODS'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {pr.pr_type === 'SERVICES' ? '🔧 Services' : pr.pr_type === 'CATEGORIZED_GOODS' ? '📋 Cataloged' : '✏️ Free Text'}
                        </span>
                      )}
                      {!pr.budget_available && pr.status === 'SUBMITTED' && (
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                          Budget Exceeded
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Requester:</span>
                        <div className="font-medium">{pr.requester_name}</div>
                      </div>
                      <div>
                        <span className="text-gray-600">Cost Center:</span>
                        <div className="font-medium">{pr.cost_center_name || 'N/A'}</div>
                      </div>
                      <div>
                        <span className="text-gray-600">Required Date:</span>
                        <div className="font-medium">{new Date(pr.required_date).toLocaleDateString()}</div>
                      </div>
                      <div>
                        <span className="text-gray-600">Total Amount:</span>
                        <div className="font-medium text-lg">${parseFloat(pr.total_amount).toLocaleString()}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Clock size={16} />
                    Created {new Date(pr.created_at).toLocaleDateString()}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/procurement/requisitions/${pr.id}`}
                      className="flex items-center gap-1 px-3 py-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      <Eye size={16} />
                      View
                    </Link>
                    
                    {pr.status === 'DRAFT' && (
                      <button
                        onClick={() => handleCheckBudget(pr.id)}
                        className="flex items-center gap-1 px-3 py-1.5 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                      >
                        <DollarSign size={16} />
                        Check Budget
                      </button>
                    )}
                    
                    {view === 'pending' && pr.status === 'SUBMITTED' && (
                      <Link
                        href="/procurement/approvals"
                        className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors"
                      >
                        <CheckCircle size={16} />
                        Go to Approvals
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

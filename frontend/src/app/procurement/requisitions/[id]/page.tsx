'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { prHeadersAPI } from '../../../../services/procurement-api';
import { ArrowLeft, Calendar, User, Building2, DollarSign, FileText, CheckCircle, XCircle, Clock, Package } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';
import FileAttachment from '@/components/FileAttachment';

interface PRLine {
  id: number;
  line_number: number;
  item_description: string;
  specifications: string;
  quantity: number;
  unit_of_measure: {
    id: number;
    code: string;
    name: string;
  };
  estimated_unit_price: number;
  line_total: number;
  need_by_date: string;
  catalog_item_details?: any;
  item_type?: 'CATEGORIZED' | 'NON_CATEGORIZED';
}

interface PRDetail {
  id: number;
  pr_number: string;
  pr_date: string;
  required_date: string;
  title: string;
  description: string;
  business_justification: string;
  priority: string;
  pr_type?: 'CATEGORIZED_GOODS' | 'UNCATEGORIZED_GOODS' | 'SERVICES';
  status: string;
  requestor_details: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
  };
  cost_center_details: {
    id: number;
    code: string;
    name: string;
  };
  project_details?: {
    id: number;
    code: string;
    name: string;
  };
  currency: {
    id: number;
    code: string;
    name: string;
  };
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  budget_check_passed: boolean;
  budget_check_message: string;
  lines: PRLine[];
  submitted_at?: string;
  submitted_by_details?: any;
  approved_at?: string;
  approved_by_details?: any;
  rejected_at?: string;
  rejected_by_details?: any;
  rejection_reason?: string;
  created_at: string;
  created_by_details?: any;
}

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-800',
  SUBMITTED: 'bg-blue-100 text-blue-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
  CONVERTED: 'bg-purple-100 text-purple-800',
  CANCELLED: 'bg-orange-100 text-orange-800',
};

const priorityColors: Record<string, string> = {
  LOW: 'bg-gray-100 text-gray-800',
  NORMAL: 'bg-blue-100 text-blue-800',
  HIGH: 'bg-orange-100 text-orange-800',
  URGENT: 'bg-red-100 text-red-800',
};

export default function RequisitionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [pr, setPr] = useState<PRDetail | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (params.id) {
      fetchPRDetail();
    }
  }, [params.id]);

  const fetchPRDetail = async () => {
    setLoading(true);
    try {
      const response = await prHeadersAPI.get(Number(params.id));
      setPr(response.data);
    } catch (error) {
      console.error('Failed to load PR details', error);
      toast.error('Failed to load purchase requisition');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!pr) return;
    
    setActionLoading(true);
    try {
      await prHeadersAPI.submit(pr.id);
      toast.success(`PR ${pr.pr_number} submitted successfully!`);
      fetchPRDetail(); // Refresh data
    } catch (error: any) {
      console.error('Failed to submit PR', error);
      toast.error(error.response?.data?.message || 'Failed to submit PR');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCheckBudget = async () => {
    if (!pr) return;
    
    setActionLoading(true);
    try {
      const response = await prHeadersAPI.checkBudget(pr.id);
      toast.success(response.data.message || 'Budget check completed');
      fetchPRDetail(); // Refresh data
    } catch (error: any) {
      console.error('Budget check failed', error);
      toast.error(error.response?.data?.message || 'Budget check failed');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading purchase requisition...</p>
        </div>
      </div>
    );
  }

  if (!pr) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <XCircle size={48} className="mx-auto text-red-500 mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Purchase Requisition Not Found</h2>
            <p className="text-gray-600 mb-6">The requested PR could not be found.</p>
            <Link
              href="/procurement/requisitions"
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <ArrowLeft size={20} />
              Back to Requisitions
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/procurement/requisitions"
          className="flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4"
        >
          <ArrowLeft size={20} />
          <span>Back to Requisitions</span>
        </Link>
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{pr.pr_number}</h1>
            <p className="text-gray-600">{pr.title}</p>
          </div>
          
          <div className="flex gap-3">
            <span className={`px-4 py-2 rounded-lg font-semibold ${statusColors[pr.status] || 'bg-gray-100 text-gray-800'}`}>
              {pr.status}
            </span>
            <span className={`px-4 py-2 rounded-lg font-semibold ${priorityColors[pr.priority] || 'bg-gray-100 text-gray-800'}`}>
              {pr.priority}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* PR Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <FileText size={20} />
              Requisition Information
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-600">PR Number</label>
                <p className="font-semibold">{pr.pr_number}</p>
              </div>
              
              <div>
                <label className="text-sm text-gray-600">PR Date</label>
                <p className="font-semibold">{new Date(pr.pr_date).toLocaleDateString()}</p>
              </div>
              
              <div>
                <label className="text-sm text-gray-600">Required Date</label>
                <p className="font-semibold">{new Date(pr.required_date).toLocaleDateString()}</p>
              </div>
              
              <div>
                <label className="text-sm text-gray-600">PR Type</label>
                <p className="font-semibold">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded-full ${
                    pr.pr_type === 'SERVICES' 
                      ? 'bg-purple-100 text-purple-800' 
                      : pr.pr_type === 'CATEGORIZED_GOODS'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {pr.pr_type === 'SERVICES' ? '🔧 Services' : pr.pr_type === 'CATEGORIZED_GOODS' ? '📋 Cataloged Goods' : '✏️ Uncategorized Goods'}
                  </span>
                </p>
              </div>
              
              <div>
                <label className="text-sm text-gray-600">Requestor</label>
                <p className="font-semibold">
                  {pr.requestor_details.first_name || pr.requestor_details.last_name 
                    ? `${pr.requestor_details.first_name} ${pr.requestor_details.last_name}`.trim()
                    : pr.requestor_details.username}
                </p>
              </div>
              
              {pr.cost_center_details && (
                <div>
                  <label className="text-sm text-gray-600">Cost Center</label>
                  <p className="font-semibold">{pr.cost_center_details.code} - {pr.cost_center_details.name}</p>
                </div>
              )}
              
              {pr.project_details && (
                <div>
                  <label className="text-sm text-gray-600">Project</label>
                  <p className="font-semibold">{pr.project_details.code} - {pr.project_details.name}</p>
                </div>
              )}
              
              {pr.description && (
                <div className="md:col-span-2">
                  <label className="text-sm text-gray-600">Description</label>
                  <p className="text-gray-900">{pr.description}</p>
                </div>
              )}
              
              {pr.business_justification && (
                <div className="md:col-span-2">
                  <label className="text-sm text-gray-600">Business Justification</label>
                  <p className="text-gray-900">{pr.business_justification}</p>
                </div>
              )}
            </div>
          </div>

          {/* Line Items */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Package size={20} />
              Line Items ({pr.lines.length})
            </h2>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-2 text-sm font-semibold text-gray-600">#</th>
                    <th className="text-left py-3 px-2 text-sm font-semibold text-gray-600">Description</th>
                    <th className="text-left py-3 px-2 text-sm font-semibold text-gray-600">Type</th>
                    <th className="text-right py-3 px-2 text-sm font-semibold text-gray-600">Qty</th>
                    <th className="text-left py-3 px-2 text-sm font-semibold text-gray-600">UoM</th>
                    <th className="text-right py-3 px-2 text-sm font-semibold text-gray-600">Unit Price</th>
                    <th className="text-right py-3 px-2 text-sm font-semibold text-gray-600">Total</th>
                    <th className="text-left py-3 px-2 text-sm font-semibold text-gray-600">Need By</th>
                  </tr>
                </thead>
                <tbody>
                  {pr.lines.map((line) => (
                    <tr key={line.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-2 text-sm">{line.line_number}</td>
                      <td className="py-3 px-2">
                        <div className="font-medium">{line.item_description}</div>
                        {line.specifications && (
                          <div className="text-sm text-gray-600 mt-1">{line.specifications}</div>
                        )}
                      </td>
                      <td className="py-3 px-2">
                        {line.item_type === 'CATEGORIZED' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
                            📋 Catalog
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700">
                            ✏️ Free Text
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-2 text-right">{line.quantity}</td>
                      <td className="py-3 px-2">{line.unit_of_measure?.code || 'N/A'}</td>
                      <td className="py-3 px-2 text-right">${parseFloat(line.estimated_unit_price.toString()).toFixed(2)}</td>
                      <td className="py-3 px-2 text-right font-semibold">${parseFloat(line.line_total.toString()).toFixed(2)}</td>
                      <td className="py-3 px-2 text-sm">{new Date(line.need_by_date).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Financial Summary */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <DollarSign size={20} />
              Financial Summary
            </h2>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span className="font-semibold">${parseFloat(pr.subtotal.toString()).toFixed(2)}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Tax Amount</span>
                <span className="font-semibold">${parseFloat(pr.tax_amount.toString()).toFixed(2)}</span>
              </div>
              
              <div className="border-t border-gray-200 pt-3 flex justify-between">
                <span className="text-lg font-semibold">Total Amount</span>
                <span className="text-lg font-bold text-blue-600">${parseFloat(pr.total_amount.toString()).toFixed(2)}</span>
              </div>
              
              <div className="mt-4">
                <div className="flex items-center gap-2">
                  {pr.budget_check_passed ? (
                    <CheckCircle size={20} className="text-green-600" />
                  ) : (
                    <XCircle size={20} className="text-red-600" />
                  )}
                  <span className={`font-semibold ${pr.budget_check_passed ? 'text-green-600' : 'text-red-600'}`}>
                    {pr.budget_check_passed ? 'Budget Available' : 'Budget Check Needed'}
                  </span>
                </div>
                {pr.budget_check_message && (
                  <p className="text-sm text-gray-600 mt-2">{pr.budget_check_message}</p>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          {pr.status === 'DRAFT' && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Actions</h2>
              
              <div className="space-y-3">
                <button
                  onClick={handleCheckBudget}
                  disabled={actionLoading}
                  className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors flex items-center justify-center gap-2"
                >
                  <DollarSign size={20} />
                  {actionLoading ? 'Checking...' : 'Check Budget'}
                </button>
                
                <button
                  onClick={handleSubmit}
                  disabled={actionLoading}
                  className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors flex items-center justify-center gap-2"
                >
                  <CheckCircle size={20} />
                  {actionLoading ? 'Submitting...' : 'Submit for Approval'}
                </button>
              </div>
            </div>
          )}

          {/* Workflow History */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Clock size={20} />
              Workflow History
            </h2>
            
            <div className="space-y-4">
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <User size={16} className="text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold">Created</p>
                  <p className="text-xs text-gray-600">
                    {pr.created_by_details?.username || 'System'} • {new Date(pr.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
              
              {pr.submitted_at && (
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <CheckCircle size={16} className="text-green-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold">Submitted</p>
                    <p className="text-xs text-gray-600">
                      {pr.submitted_by_details?.username || 'System'} • {new Date(pr.submitted_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              )}
              
              {pr.approved_at && (
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <CheckCircle size={16} className="text-green-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold">Approved</p>
                    <p className="text-xs text-gray-600">
                      {pr.approved_by_details?.username || 'System'} • {new Date(pr.approved_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              )}
              
              {pr.rejected_at && (
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                    <XCircle size={16} className="text-red-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold">Rejected</p>
                    <p className="text-xs text-gray-600">
                      {pr.rejected_by_details?.username || 'System'} • {new Date(pr.rejected_at).toLocaleString()}
                    </p>
                    {pr.rejection_reason && (
                      <p className="text-sm text-gray-700 mt-1 italic">&quot;{pr.rejection_reason}&quot;</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* File Attachments Section - Only show for existing PRs */}
        {pr.id > 0 && (
          <div className="bg-white shadow-sm rounded-lg p-6 mt-6">
            <FileAttachment
              documentType="PR"
              documentId={pr.id}
            />
          </div>
        )}
      </div>
    </div>
  );
}

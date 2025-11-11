'use client';

import React, { useState, useEffect } from 'react';
import { approvalInstancesAPI, approvalStepsAPI } from '../../../services/procurement-api';
import { ApprovalInstance } from '../../../types/procurement';
import { CheckCircle, XCircle, Clock, Eye, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function ApprovalsPage() {
  const [instances, setInstances] = useState<ApprovalInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'pending' | 'all'>('all');

  useEffect(() => {
    fetchInstances();
  }, [filter]);

  const fetchInstances = async () => {
    try {
      setLoading(true);
      let response;
      
      if (filter === 'pending') {
        response = await approvalInstancesAPI.myPending();
      } else {
        response = await approvalInstancesAPI.list();
      }
      
      setInstances(Array.isArray(response.data) ? response.data : (response.data as any).results || []);
    } catch (error: any) {
      toast.error('Failed to load approvals');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (stepId: number, instanceId: number) => {
    const comments = prompt('Approval comments (optional):');
    
    try {
      await approvalStepsAPI.approve(stepId, comments ? { comments } : undefined);
      toast.success('Approved successfully');
      fetchInstances();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to approve');
      console.error(error);
    }
  };

  const handleReject = async (stepId: number, instanceId: number) => {
    const comments = prompt('Rejection reason (required):');
    if (!comments) return;
    
    try {
      await approvalStepsAPI.reject(stepId, { comments });
      toast.success('Rejected');
      fetchInstances();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to reject');
      console.error(error);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      PENDING: 'bg-yellow-100 text-yellow-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-800',
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
      CANCELLED: 'bg-gray-400 text-white',
      SKIPPED: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getEntityTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      PR: 'Purchase Requisition',
      PO: 'Purchase Order',
      BILL: 'Vendor Bill',
      PAYMENT: 'Payment',
      CONTRACT: 'Contract',
      RFX: 'RFx Event',
    };
    return labels[type] || type;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Approval Workflows</h1>
        <p className="text-gray-600">Manage pending approvals and workflow instances</p>
      </div>

      {/* Filter Tabs */}
      <div className="mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('pending')}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors ${
              filter === 'pending'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Clock size={18} />
            Pending My Approval
            {instances.length > 0 && filter === 'pending' && (
              <span className="px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
                {instances.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setFilter('all')}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            <CheckCircle size={18} />
            All Approvals
          </button>
          <Link
            href="/procurement/approvals/workflows"
            className="flex items-center gap-2 px-6 py-2 bg-white text-gray-600 hover:bg-gray-50 rounded-lg font-medium transition-colors"
          >
            <Eye size={18} />
            Manage Workflows
          </Link>
        </div>
      </div>

      {/* Approvals List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex justify-center items-center py-12 bg-white rounded-lg shadow">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : instances.length === 0 ? (
          <div className="bg-white rounded-lg shadow text-center py-12">
            <CheckCircle size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">
              {filter === 'pending' ? 'No pending approvals' : 'No approval instances found'}
            </p>
          </div>
        ) : (
          instances.map((inst) => {
            const instance = inst as any; // Cast to bypass type mismatch
            const currentStep = instance.step_instances?.find((s: any) => s.status === 'PENDING' || s.status === 'ACTIVE');
            const completedSteps = instance.step_instances?.filter((s: any) => s.status === 'APPROVED' || s.status === 'REJECTED').length || 0;
            const totalSteps = instance.step_instances?.length || 0;
            
            // Get PR reference from object_id
            const prReference = `PR-${instance.object_id}`;
            
            return (
              <div key={instance.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
                <div className="p-6">
                  {/* Header */}
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-semibold text-gray-900">
                          Purchase Requisition #{prReference}
                        </h3>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(instance.status)}`}>
                          {instance.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <div>Workflow: {instance.workflow_details?.name || 'N/A'}</div>
                        <div>Submitted: {new Date(instance.requested_at).toLocaleDateString()}</div>
                        <div>Progress: {completedSteps}/{totalSteps} steps</div>
                      </div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${(completedSteps / totalSteps) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Approval Steps */}
                  <div className="space-y-3 mb-4">
                    {instance.step_instances?.map((step: any, index: number) => (
                      <div
                        key={step.id}
                        className={`flex items-center gap-4 p-3 rounded-lg ${
                          step.status === 'PENDING' || step.status === 'ACTIVE'
                            ? 'bg-yellow-50 border-2 border-yellow-300'
                            : step.status === 'APPROVED'
                            ? 'bg-green-50 border border-green-200'
                            : step.status === 'REJECTED'
                            ? 'bg-red-50 border border-red-200'
                            : 'bg-gray-50 border border-gray-200'
                        }`}
                      >
                        <div className="flex-shrink-0">
                          {step.status === 'APPROVED' ? (
                            <CheckCircle className="text-green-600" size={24} />
                          ) : step.status === 'REJECTED' ? (
                            <XCircle className="text-red-600" size={24} />
                          ) : step.status === 'PENDING' || step.status === 'ACTIVE' ? (
                            <Clock className="text-yellow-600" size={24} />
                          ) : (
                            <AlertCircle className="text-gray-400" size={24} />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">
                            Step {step.workflow_step_details?.sequence || index + 1}: {step.workflow_step_details?.name || 'Approval'}
                          </div>
                          <div className="text-sm text-gray-600">
                            Approver: {step.workflow_step_details?.approvers_details?.[0]?.username || 'N/A'}
                            {step.completed_at && (
                              <span className="ml-2">
                                • {step.status} on {new Date(step.completed_at).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                          {step.notes && (
                            <div className="text-sm text-gray-600 italic mt-1">"{step.notes}"</div>
                          )}
                          {step.due_at && (step.status === 'PENDING' || step.status === 'ACTIVE') && (
                            <div className="text-sm text-red-600 mt-1">
                              Due: {new Date(step.due_at).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                        {(step.status === 'PENDING' || step.status === 'ACTIVE') && (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleApprove(step.id, instance.id)}
                              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-1"
                            >
                              <CheckCircle size={16} />
                              Approve
                            </button>
                            <button
                              onClick={() => handleReject(step.id, instance.id)}
                              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-1"
                            >
                              <XCircle size={16} />
                              Reject
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Footer */}
                  <div className="flex justify-between items-center pt-4 border-t border-gray-200">
                    <div className="text-sm text-gray-600">
                      {instance.status === 'APPROVED' && instance.completed_at && (
                        <span className="text-green-600">Completed on {new Date(instance.completed_at).toLocaleDateString()}</span>
                      )}
                      {instance.status === 'REJECTED' && instance.completed_at && (
                        <span className="text-red-600">Rejected on {new Date(instance.completed_at).toLocaleDateString()}</span>
                      )}
                    </div>
                    <Link
                      href={`/procurement/approvals/${instance.id}`}
                      className="flex items-center gap-1 px-3 py-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      <Eye size={16} />
                      View Details
                    </Link>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

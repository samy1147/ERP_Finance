'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { approvalInstancesAPI, approvalStepsAPI } from '../../../../services/procurement-api';
import { ApprovalInstance } from '../../../../types/procurement';
import { CheckCircle, XCircle, Clock, AlertCircle, ArrowLeft, User } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function ApprovalDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const [instance, setInstance] = useState<ApprovalInstance | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchInstance();
    }
  }, [id]);

  const fetchInstance = async () => {
    try {
      setLoading(true);
      const response = await approvalInstancesAPI.get(Number(id));
      setInstance(response.data);
    } catch (error: any) {
      console.error('Failed to load approval instance', error);
      toast.error('Failed to load approval details');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (stepId: number) => {
    const comments = prompt('Approval comments (optional):');
    
    try {
      await approvalStepsAPI.approve(stepId, comments ? { comments } : undefined);
      toast.success('Approved successfully');
      fetchInstance();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to approve');
      console.error(error);
    }
  };

  const handleReject = async (stepId: number) => {
    const comments = prompt('Rejection reason (required):');
    if (!comments) return;
    
    try {
      await approvalStepsAPI.reject(stepId, { comments });
      toast.success('Rejected');
      fetchInstance();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to reject');
      console.error(error);
    }
  };

  const handleCancel = async () => {
    const reason = prompt('Cancellation reason (required):');
    if (!reason) return;
    
    try {
      await approvalInstancesAPI.cancel(Number(id), { cancellation_reason: reason });
      toast.success('Approval cancelled');
      fetchInstance();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to cancel');
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
      ACTIVE: 'bg-blue-100 text-blue-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <CheckCircle size={20} className="text-green-600" />;
      case 'REJECTED':
        return <XCircle size={20} className="text-red-600" />;
      case 'PENDING':
      case 'IN_PROGRESS':
      case 'ACTIVE':
        return <Clock size={20} className="text-blue-600" />;
      default:
        return <AlertCircle size={20} className="text-gray-600" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!instance) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <AlertCircle size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 mb-4">Approval instance not found</p>
          <Link href="/procurement/approvals" className="text-blue-600 hover:underline">
            Back to Approvals
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/procurement/approvals"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft size={20} />
          Back to Approvals
        </Link>
        
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Approval Instance #{instance.id}
            </h1>
            <p className="text-gray-600">
              {instance.entity_type} - {instance.entity_reference || `ID: ${instance.entity_id}`}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <span className={`px-4 py-2 rounded-lg font-medium ${getStatusBadge(instance.status)}`}>
              {instance.status}
            </span>
            {instance.status === 'IN_PROGRESS' && (
              <button
                onClick={handleCancel}
                className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
              >
                Cancel Approval
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Instance Details */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Approval Details</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-600">Workflow</label>
            <p className="font-medium">{instance.workflow_name || `Workflow #${instance.workflow}`}</p>
          </div>
          <div>
            <label className="text-sm text-gray-600">Submitted By</label>
            <p className="font-medium">User #{instance.submitted_by}</p>
          </div>
          <div>
            <label className="text-sm text-gray-600">Submitted At</label>
            <p className="font-medium">{new Date(instance.submitted_at).toLocaleString()}</p>
          </div>
          {instance.completed_at && (
            <div>
              <label className="text-sm text-gray-600">Completed At</label>
              <p className="font-medium">{new Date(instance.completed_at).toLocaleString()}</p>
            </div>
          )}
          {instance.current_step && (
            <div>
              <label className="text-sm text-gray-600">Current Step</label>
              <p className="font-medium">Step #{instance.current_step}</p>
            </div>
          )}
        </div>
      </div>

      {/* Approval Steps */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Approval Steps</h2>
        
        {instance.steps && instance.steps.length > 0 ? (
          <div className="space-y-4">
            {instance.steps.map((step) => (
              <div
                key={step.id}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    {getStatusIcon(step.status)}
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-gray-900">
                          Step {step.step_number}: {step.step_name}
                        </h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(step.status)}`}>
                          {step.status}
                        </span>
                      </div>
                      
                      <div className="text-sm text-gray-600 space-y-1">
                        <div className="flex items-center gap-2">
                          <User size={14} />
                          <span>Approver: {step.approver_name || `User #${step.approver}`}</span>
                        </div>
                        
                        {step.due_date && (
                          <div>Due: {new Date(step.due_date).toLocaleDateString()}</div>
                        )}
                        
                        {step.action_date && (
                          <div>Action taken: {new Date(step.action_date).toLocaleString()}</div>
                        )}
                        
                        {step.comments && (
                          <div className="mt-2 p-2 bg-gray-50 rounded">
                            <strong>Comments:</strong> {step.comments}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Action Buttons */}
                  {step.status === 'PENDING' && instance.status === 'IN_PROGRESS' && (
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => handleApprove(step.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                      >
                        <CheckCircle size={16} />
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(step.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                      >
                        <XCircle size={16} />
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No approval steps found
          </div>
        )}
      </div>
    </div>
  );
}

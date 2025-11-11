'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { approvalWorkflowsAPI } from '../../../../../services/procurement-api';
import { ApprovalWorkflow } from '../../../../../types/procurement';
import { ArrowLeft, Edit, Trash, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function WorkflowDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const [workflow, setWorkflow] = useState<ApprovalWorkflow | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchWorkflow();
    }
  }, [id]);

  const fetchWorkflow = async () => {
    try {
      setLoading(true);
      const response = await approvalWorkflowsAPI.get(Number(id));
      setWorkflow(response.data);
    } catch (error: any) {
      console.error('Failed to load workflow', error);
      toast.error('Failed to load workflow details');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Delete this workflow? This action cannot be undone.')) return;
    
    try {
      await approvalWorkflowsAPI.delete(Number(id));
      toast.success('Workflow deleted');
      router.push('/procurement/approvals/workflows');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete workflow');
      console.error(error);
    }
  };

  const getApproverTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      USER: 'Specific User',
      ROLE: 'Role/Group',
      MANAGER: 'Manager',
      BUDGET_OWNER: 'Budget Owner',
    };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <AlertCircle size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 mb-4">Workflow not found</p>
          <Link href="/procurement/approvals/workflows" className="text-blue-600 hover:underline">
            Back to Workflows
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
          href="/procurement/approvals/workflows"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft size={20} />
          Back to Workflows
        </Link>
        
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{workflow.name}</h1>
            {workflow.description && (
              <p className="text-gray-600 mt-1">{workflow.description}</p>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            {workflow.active ? (
              <span className="px-4 py-2 bg-green-100 text-green-800 rounded-lg font-medium flex items-center gap-2">
                <CheckCircle size={16} />
                Active
              </span>
            ) : (
              <span className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium flex items-center gap-2">
                <XCircle size={16} />
                Inactive
              </span>
            )}
            
            <Link
              href={`/procurement/approvals/workflows/${id}/edit`}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Edit size={16} />
              Edit
            </Link>
            
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
            >
              <Trash size={16} />
              Delete
            </button>
          </div>
        </div>
      </div>

      {/* Workflow Details */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Workflow Details</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-600">Entity Type</label>
            <p className="font-medium">{workflow.entity_type}</p>
          </div>
          <div>
            <label className="text-sm text-gray-600">Status</label>
            <p className="font-medium">{workflow.active ? 'Active' : 'Inactive'}</p>
          </div>
          <div>
            <label className="text-sm text-gray-600">Created At</label>
            <p className="font-medium">{new Date(workflow.created_at).toLocaleString()}</p>
          </div>
          <div>
            <label className="text-sm text-gray-600">Updated At</label>
            <p className="font-medium">{new Date(workflow.updated_at).toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Workflow Steps */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Approval Steps</h2>
        
        {workflow.steps && workflow.steps.length > 0 ? (
          <div className="space-y-4">
            {workflow.steps
              .sort((a, b) => a.step_number - b.step_number)
              .map((step, index) => (
                <div
                  key={step.id || index}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start gap-4">
                    {/* Step Number Badge */}
                    <div className="flex-shrink-0 w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                      {step.step_number}
                    </div>
                    
                    {/* Step Details */}
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 text-lg mb-2">
                        {step.step_name}
                      </h3>
                      
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-gray-600">Approver Type:</span>
                          <span className="ml-2 font-medium">
                            {getApproverTypeLabel(step.approver_type)}
                          </span>
                        </div>
                        
                        {step.approver_name && (
                          <div>
                            <span className="text-gray-600">Approver:</span>
                            <span className="ml-2 font-medium">{step.approver_name}</span>
                          </div>
                        )}
                        
                        <div>
                          <span className="text-gray-600">Approval Required:</span>
                          <span className="ml-2 font-medium">
                            {step.approval_required ? (
                              <span className="text-green-600">Yes</span>
                            ) : (
                              <span className="text-gray-500">No</span>
                            )}
                          </span>
                        </div>
                        
                        <div>
                          <span className="text-gray-600">Parallel Approval:</span>
                          <span className="ml-2 font-medium">
                            {step.parallel_approval ? (
                              <span className="text-blue-600">Yes</span>
                            ) : (
                              <span className="text-gray-500">No</span>
                            )}
                          </span>
                        </div>
                        
                        {(step.min_amount || step.max_amount) && (
                          <div className="col-span-2">
                            <span className="text-gray-600">Amount Range:</span>
                            <span className="ml-2 font-medium">
                              {step.min_amount && `Min: ${step.min_amount}`}
                              {step.min_amount && step.max_amount && ' | '}
                              {step.max_amount && `Max: ${step.max_amount}`}
                            </span>
                          </div>
                        )}
                        
                        {step.condition && (
                          <div className="col-span-2">
                            <span className="text-gray-600">Condition:</span>
                            <span className="ml-2 font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                              {step.condition}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No approval steps configured
          </div>
        )}
      </div>
    </div>
  );
}

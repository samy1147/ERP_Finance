'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { approvalWorkflowsAPI } from '../../../../services/procurement-api';
import { ApprovalWorkflow } from '../../../../types/procurement';
import { Eye, PlusCircle, Edit, Trash } from 'lucide-react';

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<ApprovalWorkflow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      const res = await approvalWorkflowsAPI.list();
      const data = Array.isArray(res.data) ? res.data : (res.data as any).results || [];
      setWorkflows(data);
    } catch (err: any) {
      console.error('Failed to load workflows', err);
      toast.error('Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this workflow? This action cannot be undone.')) return;
    try {
      await approvalWorkflowsAPI.delete(id);
      toast.success('Workflow deleted');
      setWorkflows((prev) => prev.filter((w) => w.id !== id));
    } catch (err: any) {
      console.error('Delete failed', err);
      toast.error(err?.response?.data?.detail || 'Failed to delete workflow');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Approval Workflows</h1>
          <p className="text-gray-600">Manage approval workflows for procurement documents</p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/procurement/approvals/workflows/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <PlusCircle size={16} />
            New Workflow
          </Link>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        {loading ? (
          <div className="p-12 flex justify-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
          </div>
        ) : workflows.length === 0 ? (
          <div className="p-12 text-center text-gray-600">
            <Eye size={48} className="mx-auto mb-4 text-gray-300" />
            <div>No workflows found.</div>
            <div className="mt-4">
              <Link href="/procurement/approvals/workflows/new" className="text-blue-600 underline">
                Create your first workflow
              </Link>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entity Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Active</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {workflows.map((wf) => (
                  <tr key={wf.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{wf.name}</div>
                      {wf.description && <div className="text-xs text-gray-500">{wf.description}</div>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{wf.entity_type}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {wf.active ? (
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">Active</span>
                      ) : (
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs">Inactive</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex justify-end gap-2">
                      <Link href={`/procurement/approvals/workflows/${wf.id}`} className="text-blue-600 px-3 py-1 rounded hover:bg-gray-50">
                        <Eye size={16} />
                      </Link>
                      <Link href={`/procurement/approvals/workflows/${wf.id}/edit`} className="text-gray-700 px-3 py-1 rounded hover:bg-gray-50">
                        <Edit size={16} />
                      </Link>
                      <button onClick={() => handleDelete(wf.id)} className="text-red-600 px-3 py-1 rounded hover:bg-gray-50">
                        <Trash size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

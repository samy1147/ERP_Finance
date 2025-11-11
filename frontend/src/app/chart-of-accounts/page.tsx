'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import segmentService from '@/services/segmentService';
import { Account } from '@/types/segment';

export default function ChartOfAccountsPage() {
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      const data = await segmentService.getAccountHierarchy();
      setAccounts(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load accounts');
      console.error('Error loading accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleNode = (code: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(code)) {
      newExpanded.delete(code);
    } else {
      newExpanded.add(code);
    }
    setExpandedNodes(newExpanded);
  };

  const renderAccount = (account: Account, level: number = 0) => {
    const hasChildren = account.children && account.children.length > 0;
    const isExpanded = expandedNodes.has(account.code);
    const indent = level * 24;

    return (
      <div key={account.code}>
        <div 
          className={`flex items-center py-2 px-4 border-b hover:bg-gray-50 ${
            level === 0 ? 'bg-gray-50 font-semibold' : ''
          }`}
        >
          <div style={{ paddingLeft: `${indent}px` }} className="flex items-center flex-1">
            {hasChildren && (
              <button
                onClick={() => toggleNode(account.code)}
                className="mr-2 text-gray-500 hover:text-gray-700 w-6 text-left"
              >
                {isExpanded ? '▼' : '▶'}
              </button>
            )}
            {!hasChildren && <div className="w-6 mr-2"></div>}
            
            <span className="text-sm text-gray-900 font-mono mr-4">{account.code}</span>
            <span className="text-sm text-gray-700 flex-1">{account.name}</span>
            
            <span className={`px-2 py-1 text-xs rounded ${
              account.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
            }`}>
              {account.is_active ? 'Active' : 'Inactive'}
            </span>

            <div className="ml-4">
              <button
                onClick={() => router.push(`/chart-of-accounts/${account.code}/edit`)}
                className="text-blue-600 hover:text-blue-800 text-sm mr-3"
              >
                Edit
              </button>
              <button
                onClick={() => router.push(`/chart-of-accounts/${account.code}`)}
                className="text-indigo-600 hover:text-indigo-800 text-sm"
              >
                Details
              </button>
            </div>
          </div>
        </div>
        
        {hasChildren && isExpanded && (
          <div>
            {account.children!.map((child) => renderAccount(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Chart of Accounts</h1>
          <p className="text-gray-600 mt-1">Hierarchical view of all GL accounts</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setExpandedNodes(new Set(accounts.map(a => a.code)))}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
          >
            Expand All
          </button>
          <button
            onClick={() => setExpandedNodes(new Set())}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
          >
            Collapse All
          </button>
          <button
            onClick={() => router.push('/chart-of-accounts/new')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            + New Account
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="bg-gray-100 px-4 py-3 border-b font-semibold text-gray-700 text-sm flex">
          <div className="flex-1">Account Code & Name</div>
          <div className="w-32 text-center">Status</div>
          <div className="w-32 text-right">Actions</div>
        </div>
        
        {accounts.length > 0 ? (
          <div>
            {accounts.map((account) => renderAccount(account, 0))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            No accounts found. Create one to get started.
          </div>
        )}
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">Legend</h3>
        <div className="grid grid-cols-2 gap-2 text-sm text-blue-800">
          <div>• <strong>Active</strong>: Account available for transactions</div>
          <div>• <strong>Inactive</strong>: Account disabled for new transactions</div>
          <div>• <strong>Level</strong>: Hierarchy depth (0 = root account)</div>
          <div>• Indentation shows parent-child relationships</div>
        </div>
      </div>
    </div>
  );
}

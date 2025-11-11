'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { journalEntriesAPI, accountsAPI, segmentTypesAPI, segmentsAPI } from '../../../services/api';
import { Account, JournalEntry, JournalLine, GLDistributionLine } from '../../../types';
import { SegmentType, Segment } from '../../../services/api';
import { ArrowLeft, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';
import GLDistributionLines from '../../../components/GLDistributionLines';

export default function CreateJournalEntryPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [accounts, setAccounts] = useState<Account[]>([]);
  
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    currency: 1, // Default currency ID
    memo: '',
  });

  const [glLines, setGlLines] = useState<Partial<GLDistributionLine>[]>([
    { account: 0, line_type: 'DEBIT', amount: '0.00', description: '', segments: [] },
    { account: 0, line_type: 'CREDIT', amount: '0.00', description: '', segments: [] },
  ]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const accountsRes = await accountsAPI.list();
      setAccounts(accountsRes.data.filter((acc: Account) => acc.is_active));
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load form data');
    }
  };

  const getTotals = () => {
    const totalDebit = glLines.reduce(
      (sum, line) => (line.line_type === 'DEBIT' ? sum + parseFloat(line.amount || '0') : sum),
      0
    );
    const totalCredit = glLines.reduce(
      (sum, line) => (line.line_type === 'CREDIT' ? sum + parseFloat(line.amount || '0') : sum),
      0
    );
    const difference = totalDebit - totalCredit;
    return { totalDebit, totalCredit, difference };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const { totalDebit, totalCredit, difference } = getTotals();
    
    if (Math.abs(difference) > 0.01) {
      toast.error(`Journal entry is out of balance by ${difference.toFixed(2)}`);
      return;
    }

    // Validate all lines have accounts selected
    if (glLines.some((line) => !line.account || line.account === 0)) {
      toast.error('All lines must have an account selected');
      return;
    }

    setLoading(true);

    try {
      // Convert GL distribution lines to journal lines format
      const journalData = {
        ...formData,
        lines: glLines.map((line) => ({
          account: line.account,
          debit: line.line_type === 'DEBIT' ? line.amount : '0.00',
          credit: line.line_type === 'CREDIT' ? line.amount : '0.00',
          segments: (line.segments || [])
            .filter((s) => s.segment !== 0)
            .map((s) => ({
              segment_type: s.segment_type,
              segment: s.segment,
            })),
        })),
      };

      await journalEntriesAPI.create(journalData);
      toast.success('Journal entry created successfully');
      router.push('/journals');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.error ||
                          JSON.stringify(error.response?.data) || 
                          'Failed to create journal entry';
      toast.error(errorMessage);
      console.error('Create Error:', error.response?.data || error);
    } finally {
      setLoading(false);
    }
  };

  const { totalDebit, totalCredit, difference } = getTotals();
  const isBalanced = Math.abs(difference) < 0.01;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/journals"
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Journal Entries
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Create Manual Journal Entry</h1>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6">
          {/* Header Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Entry Date *
              </label>
              <input
                type="date"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Currency *
              </label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value={1}>USD</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Memo / Description
              </label>
              <input
                type="text"
                value={formData.memo}
                onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Description of the entry"
              />
            </div>
          </div>

          {/* GL Distribution Lines */}
          <GLDistributionLines
            lines={glLines}
            accounts={accounts}
            invoiceTotal={0} // Not applicable for manual journal entries
            currencySymbol="$"
            onChange={setGlLines}
          />

          {/* Balance Summary */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-sm text-gray-600">Total Debits</p>
                <p className="text-2xl font-bold text-green-600">${totalDebit.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Credits</p>
                <p className="text-2xl font-bold text-blue-600">${totalCredit.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Difference</p>
                <p className={`text-2xl font-bold ${isBalanced ? 'text-green-600' : 'text-red-600'}`}>
                  ${difference.toFixed(2)} {isBalanced ? '✓' : '✗'}
                </p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-4 mt-6">
            <Link
              href="/journals"
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading || !isBalanced}
              className={`flex items-center gap-2 px-6 py-2 rounded-md text-white ${
                loading || !isBalanced
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              <Save className="w-4 h-4" />
              {loading ? 'Creating...' : 'Create Journal Entry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

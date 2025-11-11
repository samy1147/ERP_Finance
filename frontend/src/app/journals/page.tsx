'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { journalEntriesAPI, accountsAPI } from '../../services/api';
import { JournalEntry, Account } from '../../types';
import { BookOpen, FileText, CheckCircle, XCircle, Eye, Plus } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

export default function JournalEntriesPage() {
  const [journals, setJournals] = useState<JournalEntry[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJournal, setSelectedJournal] = useState<JournalEntry | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [journalsResponse, accountsResponse] = await Promise.all([
        journalEntriesAPI.list(),
        accountsAPI.list(),
      ]);
      setJournals(journalsResponse.data);
      setAccounts(accountsResponse.data);
    } catch (error) {
      toast.error('Failed to load journal entries');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = (journal: JournalEntry) => {
    setSelectedJournal(journal);
    setShowDetail(true);
  };

  const handlePost = async (id: number) => {
    if (!confirm('Are you sure you want to post this journal entry to the General Ledger?')) {
      return;
    }
    
    try {
      await journalEntriesAPI.post(id);
      toast.success('Journal entry posted successfully');
      fetchData();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.error || 'Failed to post journal entry';
      toast.error(errorMessage);
      console.error('Post Error:', error.response?.data || error);
    }
  };

  const handleReverse = async (id: number) => {
    if (!confirm('Are you sure you want to reverse this journal entry?')) {
      return;
    }
    
    try {
      await journalEntriesAPI.reverse(id);
      toast.success('Journal entry reversed successfully');
      fetchData();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.error || 'Failed to reverse journal entry';
      toast.error(errorMessage);
      console.error('Reverse Error:', error.response?.data || error);
    }
  };

  const handleExport = async (format: 'csv' | 'xlsx') => {
    try {
      const response = await journalEntriesAPI.export(format);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `journals.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success(`Journals exported as ${format.toUpperCase()}`);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to export journals';
      toast.error(errorMessage);
      console.error('Export Error:', error);
    }
  };

  const getAccountName = (line: any) => {
    // If API provides account_code and account_name, use them
    if (line.account_code && line.account_name) {
      return `${line.account_code} - ${line.account_name}`;
    }
    // Otherwise, look up from accounts list
    const account = accounts.find(a => a.id === line.account);
    return account ? `${account.code} - ${account.name}` : line.account.toString();
  };

  const calculateTotals = (journal: JournalEntry) => {
    let totalDebit = 0;
    let totalCredit = 0;
    journal.lines.forEach(line => {
      totalDebit += parseFloat(line.debit || '0');
      totalCredit += parseFloat(line.credit || '0');
    });
    return { totalDebit, totalCredit };
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading journal entries...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Journal Entries</h1>
          <p className="mt-2 text-gray-600">View all general ledger entries</p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/journals/create"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create Journal Entry
          </Link>
          <button
            onClick={() => handleExport('csv')}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-medium"
          >
            Export CSV
          </button>
          <button
            onClick={() => handleExport('xlsx')}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-medium"
          >
            Export Excel
          </button>
          <Link href="/" className="btn-secondary">
            ← Back to Dashboard
          </Link>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Entries</p>
              <p className="text-2xl font-bold text-gray-900">{journals.length}</p>
            </div>
            <BookOpen className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Posted</p>
              <p className="text-2xl font-bold text-green-600">
                {journals.filter(j => j.posted).length}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Draft</p>
              <p className="text-2xl font-bold text-yellow-600">
                {journals.filter(j => !j.posted).length}
              </p>
            </div>
            <FileText className="h-8 w-8 text-yellow-600" />
          </div>
        </div>
      </div>

      {/* Journal Entries Table */}
      <div className="table-wrapper">
        <table className="table-base">
          <thead className="table-header">
            <tr>
              <th className="table-th">ID</th>
              <th className="table-th">Date</th>
              <th className="table-th">Memo</th>
              <th className="table-th">Lines</th>
              <th className="table-th">Total Debit</th>
              <th className="table-th">Total Credit</th>
              <th className="table-th">Status</th>
              <th className="table-th">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {journals.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                  No journal entries found
                </td>
              </tr>
            ) : (
              journals.map((journal) => {
                const { totalDebit, totalCredit } = calculateTotals(journal);
                return (
                  <tr key={journal.id} className="hover:bg-gray-50">
                    <td className="table-td font-medium">JE-{journal.id}</td>
                    <td className="table-td">
                      {format(new Date(journal.date), 'MMM dd, yyyy')}
                    </td>
                    <td className="table-td max-w-xs truncate">{journal.memo}</td>
                    <td className="table-td">
                      <span className="badge-info">{journal.lines.length} lines</span>
                    </td>
                    <td className="table-td font-mono">
                      ${totalDebit.toFixed(2)}
                    </td>
                    <td className="table-td font-mono">
                      ${totalCredit.toFixed(2)}
                    </td>
                    <td className="table-td">
                      {journal.posted ? (
                        <span className="badge-success flex items-center gap-1">
                          <CheckCircle className="h-4 w-4" />
                          Posted
                        </span>
                      ) : (
                        <span className="badge-warning">Draft</span>
                      )}
                    </td>
                    <td className="table-td">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleViewDetail(journal)}
                          className="text-blue-600 hover:text-blue-800 p-1"
                          title="View Details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        {!journal.posted && (
                          <button
                            onClick={() => handlePost(journal.id)}
                            className="text-green-600 hover:text-green-800 p-1"
                            title="Post to GL"
                          >
                            <CheckCircle className="h-4 w-4" />
                          </button>
                        )}
                        {journal.posted && (
                          <button
                            onClick={() => handleReverse(journal.id)}
                            className="text-red-600 hover:text-red-800 p-1"
                            title="Reverse Entry"
                          >
                            <XCircle className="h-4 w-4" />
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

      {/* Detail Modal */}
      {showDetail && selectedJournal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Journal Entry JE-{selectedJournal.id}
                  </h2>
                  <p className="text-gray-600 mt-1">
                    {format(new Date(selectedJournal.date), 'MMMM dd, yyyy')}
                  </p>
                </div>
                <button
                  onClick={() => setShowDetail(false)}
                  className="text-gray-400 hover:text-gray-600"
                  title="Close"
                  aria-label="Close"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              <div className="mb-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Status</label>
                    <div className="mt-1">
                      {selectedJournal.posted ? (
                        <span className="badge-success">Posted</span>
                      ) : (
                        <span className="badge-warning">Draft</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Memo</label>
                    <p className="mt-1 text-gray-900">{selectedJournal.memo}</p>
                  </div>
                </div>
              </div>

              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Journal Lines</h3>
                <div className="table-wrapper">
                  <table className="table-base">
                    <thead className="table-header">
                      <tr>
                        <th className="table-th">Account</th>
                        <th className="table-th text-right">Debit</th>
                        <th className="table-th text-right">Credit</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {selectedJournal.lines.map((line, index) => (
                        <tr key={line.id || index}>
                          <td className="table-td">{getAccountName(line)}</td>
                          <td className="table-td text-right font-mono">
                            {parseFloat(line.debit || '0') > 0 ? (
                              <span className="text-green-600 font-semibold">
                                ${parseFloat(line.debit).toFixed(2)}
                              </span>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="table-td text-right font-mono">
                            {parseFloat(line.credit || '0') > 0 ? (
                              <span className="text-blue-600 font-semibold">
                                ${parseFloat(line.credit).toFixed(2)}
                              </span>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                      <tr className="bg-gray-50 font-bold">
                        <td className="table-td">TOTAL</td>
                        <td className="table-td text-right font-mono text-green-600">
                          ${calculateTotals(selectedJournal).totalDebit.toFixed(2)}
                        </td>
                        <td className="table-td text-right font-mono text-blue-600">
                          ${calculateTotals(selectedJournal).totalCredit.toFixed(2)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                {selectedJournal.posted && (
                  <button
                    onClick={() => {
                      setShowDetail(false);
                      handleReverse(selectedJournal.id);
                    }}
                    className="btn-danger"
                  >
                    Reverse Entry
                  </button>
                )}
                <button
                  onClick={() => setShowDetail(false)}
                  className="btn-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

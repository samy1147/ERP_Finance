'use client';

import { useState, useEffect } from 'react';
import { journalLinesAPI, accountsAPI, JournalLineDetail } from '@/services/api';
import { Account } from '@/types';
import { BookOpen, Filter, Search, Calendar, CheckCircle, XCircle, TrendingUp, TrendingDown, Eye } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

export default function JournalLinesPage() {
  const [lines, setLines] = useState<JournalLineDetail[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(true);
  const [selectedLine, setSelectedLine] = useState<JournalLineDetail | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  // Filters
  const [filters, setFilters] = useState({
    account_code: '',
    account_name: '',
    date_from: '',
    date_to: '',
    posted: '',
    entry_id: '',
  });

  // Summary stats
  const [stats, setStats] = useState({
    totalDebit: 0,
    totalCredit: 0,
    lineCount: 0,
    postedCount: 0,
    draftCount: 0,
  });

  useEffect(() => {
    fetchAccounts();
  }, []);

  useEffect(() => {
    fetchLines();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await accountsAPI.list();
      setAccounts(response.data);
    } catch (error) {
      console.error('Error fetching accounts:', error);
    }
  };

  const fetchLines = async () => {
    try {
      setLoading(true);
      const params: any = {};
      
      if (filters.account_code) params.account_code = filters.account_code;
      if (filters.account_name) params.account_name = filters.account_name;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;
      if (filters.posted) params.posted = filters.posted === 'true';
      if (filters.entry_id) params.entry_id = parseInt(filters.entry_id);

      const response = await journalLinesAPI.list(params);
      setLines(response.data);
      calculateStats(response.data);
      toast.success(`Loaded ${response.data.length} journal lines`);
    } catch (error: any) {
      toast.error('Failed to load journal lines');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (data: JournalLineDetail[]) => {
    const totalDebit = data.reduce((sum, line) => sum + parseFloat(line.debit || '0'), 0);
    const totalCredit = data.reduce((sum, line) => sum + parseFloat(line.credit || '0'), 0);
    const lineCount = data.length;
    const postedCount = data.filter(line => line.entry.posted).length;
    const draftCount = data.filter(line => !line.entry.posted).length;

    setStats({ totalDebit, totalCredit, lineCount, postedCount, draftCount });
  };

  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const handleApplyFilters = () => {
    fetchLines();
  };

  const handleClearFilters = () => {
    setFilters({
      account_code: '',
      account_name: '',
      date_from: '',
      date_to: '',
      posted: '',
      entry_id: '',
    });
    setTimeout(() => fetchLines(), 100);
  };

  const handleViewDetail = (line: JournalLineDetail) => {
    setSelectedLine(line);
    setShowDetail(true);
  };

  const getAccountTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      'AS': 'Asset',
      'LI': 'Liability',
      'EQ': 'Equity',
      'IN': 'Income',
      'EX': 'Expense',
      'ASSET': 'Asset',
      'LIABILITY': 'Liability',
      'EQUITY': 'Equity',
      'INCOME': 'Income',
      'EXPENSE': 'Expense',
    };
    return types[type] || type;
  };

  const getAccountTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'AS': 'bg-blue-100 text-blue-800',
      'ASSET': 'bg-blue-100 text-blue-800',
      'LI': 'bg-red-100 text-red-800',
      'LIABILITY': 'bg-red-100 text-red-800',
      'EQ': 'bg-purple-100 text-purple-800',
      'EQUITY': 'bg-purple-100 text-purple-800',
      'IN': 'bg-green-100 text-green-800',
      'INCOME': 'bg-green-100 text-green-800',
      'EX': 'bg-orange-100 text-orange-800',
      'EXPENSE': 'bg-orange-100 text-orange-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  if (loading && lines.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading journal lines...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <BookOpen className="h-8 w-8 text-blue-600" />
              Journal Lines
            </h1>
            <p className="text-gray-600 mt-2">
              Detailed view of all journal entry line items with filtering and analysis
            </p>
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
          >
            <Filter className="h-4 w-4" />
            {showFilters ? 'Hide' : 'Show'} Filters
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Total Lines</div>
          <div className="text-2xl font-bold text-gray-900">{stats.lineCount}</div>
        </div>
        <div className="bg-green-50 shadow rounded-lg p-4 border border-green-200">
          <div className="text-sm text-green-700 mb-1 flex items-center gap-1">
            <TrendingUp className="h-4 w-4" />
            Total Debits
          </div>
          <div className="text-2xl font-bold text-green-700">
            ${stats.totalDebit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
        </div>
        <div className="bg-red-50 shadow rounded-lg p-4 border border-red-200">
          <div className="text-sm text-red-700 mb-1 flex items-center gap-1">
            <TrendingDown className="h-4 w-4" />
            Total Credits
          </div>
          <div className="text-2xl font-bold text-red-700">
            ${stats.totalCredit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
        </div>
        <div className="bg-blue-50 shadow rounded-lg p-4 border border-blue-200">
          <div className="text-sm text-blue-700 mb-1 flex items-center gap-1">
            <CheckCircle className="h-4 w-4" />
            Posted
          </div>
          <div className="text-2xl font-bold text-blue-700">{stats.postedCount}</div>
        </div>
        <div className="bg-yellow-50 shadow rounded-lg p-4 border border-yellow-200">
          <div className="text-sm text-yellow-700 mb-1">Draft</div>
          <div className="text-2xl font-bold text-yellow-700">{stats.draftCount}</div>
        </div>
      </div>

      {/* Balance Check */}
      {stats.totalDebit !== stats.totalCredit && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 text-red-800">
            <XCircle className="h-5 w-5" />
            <span className="font-bold">Warning: Debits and Credits are NOT balanced!</span>
          </div>
          <div className="text-sm text-red-700 mt-2">
            Difference: ${Math.abs(stats.totalDebit - stats.totalCredit).toFixed(2)}
          </div>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-6">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </h3>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Account Code</label>
              <input
                type="text"
                value={filters.account_code}
                onChange={(e) => handleFilterChange('account_code', e.target.value)}
                placeholder="e.g., 1001"
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Account Name</label>
              <input
                type="text"
                value={filters.account_name}
                onChange={(e) => handleFilterChange('account_name', e.target.value)}
                placeholder="e.g., Cash"
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Date From</label>
              <input
                type="date"
                value={filters.date_from}
                onChange={(e) => handleFilterChange('date_from', e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Date To</label>
              <input
                type="date"
                value={filters.date_to}
                onChange={(e) => handleFilterChange('date_to', e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Status</label>
              <select
                value={filters.posted}
                onChange={(e) => handleFilterChange('posted', e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm"
              >
                <option value="">All</option>
                <option value="true">Posted</option>
                <option value="false">Draft</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Journal Entry ID</label>
              <input
                type="number"
                value={filters.entry_id}
                onChange={(e) => handleFilterChange('entry_id', e.target.value)}
                placeholder="e.g., 100"
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div className="col-span-2 flex items-end gap-2">
              <button
                onClick={handleApplyFilters}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded flex items-center justify-center gap-2"
              >
                <Search className="h-4 w-4" />
                Apply Filters
              </button>
              <button
                onClick={handleClearFilters}
                className="flex-1 bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Journal Lines Table */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Line ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Journal Entry</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debit</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Credit</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {lines.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-6 py-12 text-center text-gray-500">
                  <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-lg">No journal lines found</p>
                  <p className="text-sm mt-1">Try adjusting your filters or create new journal entries</p>
                </td>
              </tr>
            ) : (
              lines.map((line) => {
                const debit = parseFloat(line.debit || '0');
                const credit = parseFloat(line.credit || '0');
                return (
                  <tr key={line.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{line.id}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <span className="font-medium text-blue-600">JE-{line.entry.id}</span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                      {format(new Date(line.entry.date), 'MMM dd, yyyy')}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="font-medium text-gray-900">{line.account.code}</div>
                      <div className="text-xs text-gray-500 truncate max-w-xs">{line.account.name}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getAccountTypeColor(line.account.type)}`}>
                        {getAccountTypeLabel(line.account.type)}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right font-mono text-sm">
                      {debit > 0 ? (
                        <span className="text-green-700 font-medium">
                          ${debit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right font-mono text-sm">
                      {credit > 0 ? (
                        <span className="text-red-700 font-medium">
                          ${credit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {line.entry.posted ? (
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 flex items-center gap-1 w-fit">
                          <CheckCircle className="h-3 w-3" />
                          Posted
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                          Draft
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <button
                        onClick={() => handleViewDetail(line)}
                        className="text-blue-600 hover:text-blue-900"
                        title="View Details"
                      >
                        <Eye className="h-4 w-4 inline" />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
          {lines.length > 0 && (
            <tfoot className="bg-gray-50 font-bold">
              <tr>
                <td colSpan={5} className="px-4 py-3 text-right text-sm">
                  TOTALS:
                </td>
                <td className="px-4 py-3 text-right text-sm font-mono text-green-700">
                  ${stats.totalDebit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-3 text-right text-sm font-mono text-red-700">
                  ${stats.totalCredit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </td>
                <td colSpan={2} className="px-4 py-3 text-left text-sm">
                  {stats.totalDebit === stats.totalCredit ? (
                    <span className="text-green-700 flex items-center gap-1">
                      <CheckCircle className="h-4 w-4" />
                      Balanced
                    </span>
                  ) : (
                    <span className="text-red-700 flex items-center gap-1">
                      <XCircle className="h-4 w-4" />
                      Out of Balance
                    </span>
                  )}
                </td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>

      {/* Detail Modal */}
      {showDetail && selectedLine && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Journal Line #{selectedLine.id}
                  </h2>
                  <p className="text-gray-600 mt-1">
                    Part of Journal Entry JE-{selectedLine.entry.id}
                  </p>
                </div>
                <button
                  onClick={() => setShowDetail(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Entry Information */}
                <div className="bg-blue-50 p-4 rounded border border-blue-200">
                  <h3 className="font-bold text-blue-900 mb-3">Journal Entry Details</h3>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-blue-700 font-medium">Entry ID:</span>
                      <span className="ml-2 text-blue-900">JE-{selectedLine.entry.id}</span>
                    </div>
                    <div>
                      <span className="text-blue-700 font-medium">Date:</span>
                      <span className="ml-2 text-blue-900">
                        {format(new Date(selectedLine.entry.date), 'MMM dd, yyyy')}
                      </span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-blue-700 font-medium">Memo:</span>
                      <div className="ml-2 text-blue-900 mt-1">{selectedLine.entry.memo || 'No memo'}</div>
                    </div>
                    <div>
                      <span className="text-blue-700 font-medium">Status:</span>
                      <span className="ml-2">
                        {selectedLine.entry.posted ? (
                          <span className="px-2 py-1 text-xs font-semibold rounded bg-green-100 text-green-800">
                            Posted
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs font-semibold rounded bg-yellow-100 text-yellow-800">
                            Draft
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Account Information */}
                <div className="bg-gray-50 p-4 rounded border border-gray-200">
                  <h3 className="font-bold text-gray-900 mb-3">Account Details</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-gray-700 font-medium">Code:</span>
                      <span className="ml-2 text-gray-900 font-mono">{selectedLine.account.code}</span>
                    </div>
                    <div>
                      <span className="text-gray-700 font-medium">Name:</span>
                      <span className="ml-2 text-gray-900">{selectedLine.account.name}</span>
                    </div>
                    <div>
                      <span className="text-gray-700 font-medium">Type:</span>
                      <span className="ml-2">
                        <span className={`px-2 py-1 text-xs font-semibold rounded ${getAccountTypeColor(selectedLine.account.type)}`}>
                          {getAccountTypeLabel(selectedLine.account.type)}
                        </span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Amounts */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-green-50 p-4 rounded border border-green-200">
                    <div className="text-sm text-green-700 mb-1 flex items-center gap-1">
                      <TrendingUp className="h-4 w-4" />
                      Debit
                    </div>
                    <div className="text-2xl font-bold text-green-800 font-mono">
                      ${parseFloat(selectedLine.debit || '0').toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div className="bg-red-50 p-4 rounded border border-red-200">
                    <div className="text-sm text-red-700 mb-1 flex items-center gap-1">
                      <TrendingDown className="h-4 w-4" />
                      Credit
                    </div>
                    <div className="text-2xl font-bold text-red-800 font-mono">
                      ${parseFloat(selectedLine.credit || '0').toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <button
                    onClick={() => setShowDetail(false)}
                    className="w-full bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

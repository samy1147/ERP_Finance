'use client';

import { useState, useEffect } from 'react';
import { corporateTaxAPI } from '@/services/api';
import { FileText, Calendar, TrendingUp, CheckCircle, XCircle, AlertTriangle, RefreshCw } from 'lucide-react';

interface TaxFiling {
  id: number;
  filing_period_start: string;
  filing_period_end: string;
  tax_rate: string;
  taxable_income: string;
  tax_amount: string;
  status: 'DRAFT' | 'ACCRUED' | 'FILED' | 'PAID' | 'REVERSED';
  journal_entry?: number;
  filed_date?: string;
  created_at: string;
  updated_at: string;
}

interface TaxBreakdown {
  meta: {
    country?: string;
    date_from?: string;
    date_to?: string;
    org_id?: string;
    income: number;
    expense: number;
    profit: number;
  };
  rows: Array<{
    date: string;
    journal_id: number;
    account_code: string;
    account_name: string;
    type: string;
    delta: number;
    debit: number;
    credit: number;
  }>;
  download_links: {
    xlsx: string;
    csv: string;
  };
}

export default function CorporateTaxPage() {
  const [activeTab, setActiveTab] = useState<'accrual' | 'filings' | 'breakdown'>('accrual');
  const [breakdown, setBreakdown] = useState<TaxBreakdown | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFiling, setSelectedFiling] = useState<TaxFiling | null>(null);
  const [showFilingDetail, setShowFilingDetail] = useState(false);

  // Accrual form data
  const [accrualForm, setAccrualForm] = useState({
    country: 'AE',
    period_start: '',
    period_end: '',
    tax_rate: '9',
  });

  // Breakdown filter
  const [breakdownFilter, setBreakdownFilter] = useState({
    period_start: '',
    period_end: '',
  });

  useEffect(() => {
    // Load initial breakdown for current year
    const now = new Date();
    const yearStart = `${now.getFullYear()}-01-01`;
    const yearEnd = `${now.getFullYear()}-12-31`;
    setBreakdownFilter({ period_start: yearStart, period_end: yearEnd });
  }, []);

  useEffect(() => {
    if (activeTab === 'breakdown' && breakdownFilter.period_start && breakdownFilter.period_end) {
      loadBreakdown();
    }
  }, [activeTab, breakdownFilter]);

  const loadBreakdown = async () => {
    try {
      setLoading(true);
      const response = await corporateTaxAPI.breakdown(breakdownFilter);
      setBreakdown(response.data);
    } catch (error: any) {
      console.error('Error loading breakdown:', error);
      alert(`Failed to load breakdown: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAccrual = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!confirm('Create corporate tax accrual? This will create a journal entry for the tax liability.')) {
      return;
    }

    try {
      setLoading(true);
      const response = await corporateTaxAPI.accrual(accrualForm);
      alert(`Tax accrual created successfully!\nTaxable Income: ${response.data.taxable_income}\nTax Amount: ${response.data.tax_amount}\nJournal Entry: ${response.data.journal_entry || 'N/A'}`);
      setAccrualForm({ country: accrualForm.country, period_start: '', period_end: '', tax_rate: '9' });
      if (activeTab === 'breakdown') {
        loadBreakdown();
      }
    } catch (error: any) {
      console.error('Error creating accrual:', error);
      alert(`Failed to create accrual: ${error.response?.data?.detail || JSON.stringify(error.response?.data) || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFilingAction = async (filingId: number, action: 'file' | 'reverse') => {
    const confirmMessage = action === 'file' 
      ? 'File this tax return? This will mark it as filed.'
      : 'Reverse this tax filing? This will create a reversing journal entry.';
    
    if (!confirm(confirmMessage)) return;

    try {
      setLoading(true);
      if (action === 'file') {
        await corporateTaxAPI.filing.file(filingId);
        alert('Tax return filed successfully!');
      } else {
        await corporateTaxAPI.filing.reverse(filingId);
        alert('Tax filing reversed successfully!');
      }
      loadBreakdown();
      setShowFilingDetail(false);
    } catch (error: any) {
      console.error(`Error ${action}ing tax:`, error);
      alert(`Failed to ${action} tax: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleViewFiling = async (filing: TaxFiling) => {
    try {
      setLoading(true);
      const response = await corporateTaxAPI.filing.get(filing.id);
      setSelectedFiling(response.data);
      setShowFilingDetail(true);
    } catch (error: any) {
      console.error('Error loading filing:', error);
      alert(`Failed to load filing: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'DRAFT': return 'bg-gray-100 text-gray-800';
      case 'ACCRUED': return 'bg-blue-100 text-blue-800';
      case 'FILED': return 'bg-green-100 text-green-800';
      case 'PAID': return 'bg-purple-100 text-purple-800';
      case 'REVERSED': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'DRAFT': return <AlertTriangle className="h-4 w-4" />;
      case 'ACCRUED': return <CheckCircle className="h-4 w-4" />;
      case 'FILED': return <FileText className="h-4 w-4" />;
      case 'PAID': return <CheckCircle className="h-4 w-4" />;
      case 'REVERSED': return <XCircle className="h-4 w-4" />;
      default: return null;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Corporate Tax Management</h1>
        <p className="text-gray-600 mt-2">Manage corporate income tax accruals, filings, and reporting</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          onClick={() => setActiveTab('accrual')}
          className={`px-6 py-3 font-medium ${
            activeTab === 'accrual'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Tax Accrual
          </div>
        </button>
        <button
          onClick={() => setActiveTab('breakdown')}
          className={`px-6 py-3 font-medium ${
            activeTab === 'breakdown'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Tax Breakdown
          </div>
        </button>
      </div>

      {/* Tax Accrual Tab */}
      {activeTab === 'accrual' && (
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Create Tax Accrual</h2>
          <p className="text-gray-600 mb-6">
            Calculate and accrue corporate income tax for a period. This will analyze your income and expenses
            to calculate taxable income and create a journal entry for the tax liability.
          </p>

          <form onSubmit={handleAccrual}>
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Country *
                </label>
                <select
                  value={accrualForm.country}
                  onChange={(e) => setAccrualForm({ ...accrualForm, country: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                  required
                >
                  <option value="AE">UAE</option>
                  <option value="SA">KSA</option>
                  <option value="EG">Egypt</option>
                  <option value="IN">India</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Period Start Date *
                </label>
                <input
                  type="date"
                  value={accrualForm.period_start}
                  onChange={(e) => setAccrualForm({ ...accrualForm, period_start: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                  required
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Period End Date *
                </label>
                <input
                  type="date"
                  value={accrualForm.period_end}
                  onChange={(e) => setAccrualForm({ ...accrualForm, period_end: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                  required
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Tax Rate (%) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={accrualForm.tax_rate}
                  onChange={(e) => setAccrualForm({ ...accrualForm, tax_rate: e.target.value })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700"
                  required
                  placeholder="9.00"
                />
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-6">
              <h3 className="font-bold text-blue-900 mb-2">How Tax Accrual Works:</h3>
              <ul className="text-sm text-blue-800 space-y-1 list-disc ml-5">
                <li>System calculates Net Income (Revenue - Expenses) for the period</li>
                <li>Applies your tax rate to determine tax amount</li>
                <li>Creates journal entry: Debit Tax Expense, Credit Tax Payable</li>
                <li>Creates a tax filing record in ACCRUED status</li>
              </ul>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Create Tax Accrual'}
            </button>
          </form>

          {/* Example */}
          <div className="mt-8 bg-gray-50 rounded-lg p-6 border border-gray-200">
            <h3 className="font-bold text-gray-900 mb-3">📝 Example: Quarterly Tax Accrual</h3>
            <div className="text-sm text-gray-700 space-y-2">
              <p><strong>Period:</strong> Q1 2025 (Jan 1 - Mar 31)</p>
              <p><strong>Tax Rate:</strong> 9% (UAE Corporate Tax)</p>
              <p className="pt-2 border-t border-gray-300"><strong>Calculation:</strong></p>
              <ul className="list-disc ml-5 space-y-1">
                <li>Revenue: 500,000 AED</li>
                <li>Expenses: 350,000 AED</li>
                <li>Net Income: 150,000 AED</li>
                <li>Tax @ 9%: 13,500 AED</li>
              </ul>
              <p className="pt-2 border-t border-gray-300"><strong>Journal Entry:</strong></p>
              <div className="bg-white p-3 rounded border border-gray-300 font-mono text-xs">
                <div>Dr. Corporate Tax Expense    13,500</div>
                <div>Cr. Corporate Tax Payable    13,500</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tax Breakdown Tab */}
      {activeTab === 'breakdown' && (
        <div>
          {/* Filters */}
          <div className="bg-white shadow-md rounded-lg p-4 mb-6">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <label className="block text-sm font-bold mb-1">Period Start</label>
                <input
                  type="date"
                  value={breakdownFilter.period_start}
                  onChange={(e) => setBreakdownFilter({ ...breakdownFilter, period_start: e.target.value })}
                  className="shadow border rounded w-full py-2 px-3 text-sm"
                />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-bold mb-1">Period End</label>
                <input
                  type="date"
                  value={breakdownFilter.period_end}
                  onChange={(e) => setBreakdownFilter({ ...breakdownFilter, period_end: e.target.value })}
                  className="shadow border rounded w-full py-2 px-3 text-sm"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={loadBreakdown}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded text-sm font-medium disabled:opacity-50"
                >
                  {loading ? 'Loading...' : 'Load Breakdown'}
                </button>
              </div>
            </div>
          </div>

          {/* Summary Cards */}
          {breakdown && (
            <>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-white shadow rounded-lg p-5">
                  <div className="text-sm text-gray-600 mb-1">Income</div>
                  <div className="text-2xl font-bold text-green-600">
                    {breakdown.meta.income.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className="bg-white shadow rounded-lg p-5">
                  <div className="text-sm text-gray-600 mb-1">Expenses</div>
                  <div className="text-2xl font-bold text-red-600">
                    {breakdown.meta.expense.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className="bg-white shadow rounded-lg p-5">
                  <div className="text-sm text-gray-600 mb-1">Net Profit</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {breakdown.meta.profit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </div>
                </div>
              </div>

              {/* Transaction Details Table */}
              <div className="bg-white shadow-md rounded-lg overflow-hidden mb-6">
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                  <h3 className="text-lg font-bold">Transaction Details</h3>
                  <div className="flex gap-2">
                    <a
                      href={breakdown.download_links.csv}
                      className="text-sm bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
                    >
                      Download CSV
                    </a>
                    <a
                      href={breakdown.download_links.xlsx}
                      className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                    >
                      Download Excel
                    </a>
                  </div>
                </div>
                <div className="overflow-x-auto max-h-96">
                  <table className="min-w-full">
                    <thead className="bg-gray-100 sticky top-0">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Journal ID</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debit</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Credit</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Delta</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {breakdown.rows.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                            No transactions found for this period.
                          </td>
                        </tr>
                      ) : (
                        breakdown.rows.map((row, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                              {row.date}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                              #{row.journal_id}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <div className="font-medium">{row.account_code}</div>
                              <div className="text-gray-500 text-xs">{row.account_name}</div>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs font-semibold rounded ${
                                row.type === 'INCOME' ? 'bg-green-100 text-green-800' :
                                row.type === 'EXPENSE' ? 'bg-red-100 text-red-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {row.type}
                              </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-right font-mono text-sm">
                              {row.debit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-right font-mono text-sm">
                              {row.credit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                            <td className={`px-4 py-3 whitespace-nowrap text-right font-mono font-medium ${
                              row.delta > 0 ? 'text-green-600' : row.delta < 0 ? 'text-red-600' : 'text-gray-600'
                            }`}>
                              {row.delta > 0 ? '+' : ''}{row.delta.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          {!breakdown && !loading && (
            <div className="bg-white shadow-md rounded-lg p-12 text-center">
              <TrendingUp className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Select a period and click "Load Breakdown" to view tax analysis</p>
            </div>
          )}
        </div>
      )}

      {/* Filing Detail Modal */}
      {showFilingDetail && selectedFiling && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Tax Filing #{selectedFiling.id}
                  </h2>
                  <p className="text-gray-600 mt-1">
                    {selectedFiling.filing_period_start} to {selectedFiling.filing_period_end}
                  </p>
                </div>
                <button
                  onClick={() => setShowFilingDetail(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600 mb-1">Status</div>
                    <span className={`px-3 py-1 inline-flex text-sm font-semibold rounded-full ${getStatusColor(selectedFiling.status)} items-center gap-1`}>
                      {getStatusIcon(selectedFiling.status)}
                      {selectedFiling.status}
                    </span>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600 mb-1">Tax Rate</div>
                    <div className="text-lg font-bold">{parseFloat(selectedFiling.tax_rate).toFixed(2)}%</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600 mb-1">Taxable Income</div>
                    <div className="text-lg font-bold font-mono">
                      {parseFloat(selectedFiling.taxable_income).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600 mb-1">Tax Amount</div>
                    <div className="text-lg font-bold font-mono text-purple-600">
                      {parseFloat(selectedFiling.tax_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>

                {selectedFiling.journal_entry && (
                  <div className="bg-blue-50 p-4 rounded border border-blue-200">
                    <div className="text-sm text-blue-800 mb-1">Journal Entry</div>
                    <div className="font-mono font-medium text-blue-900">
                      JE-{selectedFiling.journal_entry}
                    </div>
                  </div>
                )}

                {selectedFiling.filed_date && (
                  <div className="bg-green-50 p-4 rounded border border-green-200">
                    <div className="text-sm text-green-800 mb-1">Filed Date</div>
                    <div className="font-medium text-green-900">
                      {new Date(selectedFiling.filed_date).toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                      })}
                    </div>
                  </div>
                )}

                <div className="pt-4 border-t">
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>Created: {new Date(selectedFiling.created_at).toLocaleString()}</p>
                    <p>Updated: {new Date(selectedFiling.updated_at).toLocaleString()}</p>
                  </div>
                </div>

                <div className="flex gap-2 pt-4">
                  {selectedFiling.status === 'ACCRUED' && (
                    <button
                      onClick={() => handleFilingAction(selectedFiling.id, 'file')}
                      className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded font-medium"
                    >
                      File Tax Return
                    </button>
                  )}
                  {selectedFiling.status === 'FILED' && (
                    <button
                      onClick={() => handleFilingAction(selectedFiling.id, 'reverse')}
                      className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded font-medium"
                    >
                      Reverse Filing
                    </button>
                  )}
                  <button
                    onClick={() => setShowFilingDetail(false)}
                    className="bg-gray-500 hover:bg-gray-700 text-white px-6 py-2 rounded font-medium"
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

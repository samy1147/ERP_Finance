'use client';

import React, { useState } from 'react';
import { reportsAPI } from '../../services/api';
import { Download, FileSpreadsheet } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<'trial-balance' | 'ar-aging' | 'ap-aging'>('trial-balance');
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState<any>(null);
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: '',
    asOf: new Date().toISOString().split('T')[0],
  });

  const fetchReport = async (format: string = 'json') => {
    setLoading(true);
    try {
      let response;
      if (activeTab === 'trial-balance') {
        response = await reportsAPI.trialBalance(filters.dateFrom, filters.dateTo, format);
      } else if (activeTab === 'ar-aging') {
        response = await reportsAPI.arAging(filters.asOf, format);
      } else {
        response = await reportsAPI.apAging(filters.asOf, format);
      }

      if (format === 'json') {
        setReportData(response.data);
        toast.success('Report loaded successfully');
      } else {
        // Handle file download
        let blob;
        if (response.data instanceof Blob) {
          blob = response.data;
        } else {
          blob = new Blob([response.data], {
            type: format === 'csv' ? 'text/csv' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          });
        }
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${activeTab}-${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        }, 100);
        
        toast.success(`${format.toUpperCase()} file downloaded successfully`);
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || 'Failed to fetch report';
      toast.error(errorMessage);
      console.error('Report error:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderTrialBalance = () => {
    if (!reportData || !Array.isArray(reportData)) return null;
    
    const totalDebit = reportData.reduce((sum: number, row: any) => sum + (parseFloat(row.debit) || 0), 0);
    const totalCredit = reportData.reduce((sum: number, row: any) => sum + (parseFloat(row.credit) || 0), 0);

    return (
      <div className="table-wrapper">
        <table className="table-base">
          <thead className="table-header">
            <tr>
              <th className="table-th">Account Code</th>
              <th className="table-th">Account Name</th>
              <th className="table-th text-right">Debit</th>
              <th className="table-th text-right">Credit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {reportData.map((row: any, index: number) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="table-td font-medium">{row.code}</td>
                <td className="table-td">{row.name}</td>
                <td className="table-td text-right">${parseFloat(row.debit || 0).toFixed(2)}</td>
                <td className="table-td text-right">${parseFloat(row.credit || 0).toFixed(2)}</td>
              </tr>
            ))}
            <tr className="bg-gray-100 font-bold">
              <td className="table-td" colSpan={2}>Total</td>
              <td className="table-td text-right">${totalDebit.toFixed(2)}</td>
              <td className="table-td text-right">${totalCredit.toFixed(2)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  };

  const renderARAging = () => {
    if (!reportData || !Array.isArray(reportData)) return null;

    return (
      <div className="table-wrapper">
        <table className="table-base">
          <thead className="table-header">
            <tr>
              <th className="table-th">Customer</th>
              <th className="table-th text-right">Current</th>
              <th className="table-th text-right">1-30 Days</th>
              <th className="table-th text-right">31-60 Days</th>
              <th className="table-th text-right">61-90 Days</th>
              <th className="table-th text-right">Over 90 Days</th>
              <th className="table-th text-right">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {reportData.map((row: any, index: number) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="table-td font-medium">{row.customer}</td>
                <td className="table-td text-right">${parseFloat(row.current || 0).toFixed(2)}</td>
                <td className="table-td text-right">${parseFloat(row.days_30 || 0).toFixed(2)}</td>
                <td className="table-td text-right">${parseFloat(row.days_60 || 0).toFixed(2)}</td>
                <td className="table-td text-right">${parseFloat(row.days_90 || 0).toFixed(2)}</td>
                <td className="table-td text-right">${parseFloat(row.over_90 || 0).toFixed(2)}</td>
                <td className="table-td text-right font-medium">${parseFloat(row.total || 0).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderAPAging = () => {
    if (!reportData || !Array.isArray(reportData)) return null;

    return (
      <div className="table-wrapper">
        <table className="table-base">
          <thead className="table-header">
            <tr>
              <th className="table-th">Supplier</th>
              <th className="table-th text-right">Current</th>
              <th className="table-th text-right">1-30 Days</th>
              <th className="table-th text-right">31-60 Days</th>
              <th className="table-th text-right">61-90 Days</th>
              <th className="table-th text-right">Over 90 Days</th>
              <th className="table-th text-right">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {reportData.map((row: any, index: number) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="table-td font-medium">{row.supplier}</td>
                <td className="table-td text-right">${parseFloat(row.current || 0).toFixed(2)}</td>
                <td className="table-td text-right">${parseFloat(row.days_30 || 0).toFixed(2)}</td>
                <td className="table-td text-right">${parseFloat(row.days_60 || 0).toFixed(2)}</td>
                <td className="table-td text-right">${parseFloat(row.days_90 || 0).toFixed(2)}</td>
                <td className="table-td text-right">${parseFloat(row.over_90 || 0).toFixed(2)}</td>
                <td className="table-td text-right font-medium">${parseFloat(row.total || 0).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Financial Reports</h1>
        <p className="mt-2 text-gray-600">View and export financial reports</p>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'trial-balance', name: 'Trial Balance' },
              { id: 'ar-aging', name: 'AR Aging' },
              { id: 'ap-aging', name: 'AP Aging' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id as any);
                  setReportData(null);
                }}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {activeTab === 'trial-balance' ? (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date From
                </label>
                <input
                  type="date"
                  className="input-field"
                  value={filters.dateFrom}
                  onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                  aria-label="Report start date"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date To
                </label>
                <input
                  type="date"
                  className="input-field"
                  value={filters.dateTo}
                  onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                  aria-label="Report end date"
                />
              </div>
            </>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                As Of Date
              </label>
              <input
                type="date"
                className="input-field"
                value={filters.asOf}
                onChange={(e) => setFilters({ ...filters, asOf: e.target.value })}
                aria-label="Report as of date"
              />
            </div>
          )}
          <div className="flex items-end gap-2">
            <button
              onClick={() => fetchReport('json')}
              disabled={loading}
              className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <span className="inline-block animate-spin mr-2">⏳</span>
                  Loading...
                </>
              ) : (
                'View Report'
              )}
            </button>
          </div>
        </div>

        {/* Export Buttons */}
        {reportData && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600 mb-2">Export report data:</p>
            <div className="flex gap-2">
              <button
                onClick={() => fetchReport('csv')}
                disabled={loading}
                className="btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="h-4 w-4" />
                {loading ? 'Downloading...' : 'Export CSV'}
              </button>
              <button
                onClick={() => fetchReport('xlsx')}
                disabled={loading}
                className="btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FileSpreadsheet className="h-4 w-4" />
                {loading ? 'Downloading...' : 'Export Excel'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Report Display */}
      {reportData && (
        <>
          {activeTab === 'trial-balance' && renderTrialBalance()}
          {activeTab === 'ar-aging' && renderARAging()}
          {activeTab === 'ap-aging' && renderAPAging()}
        </>
      )}

      {!reportData && !loading && (
        <div className="card text-center text-gray-500">
          Select filters and click &quot;View Report&quot; to display the report
        </div>
      )}
    </div>
  );
}

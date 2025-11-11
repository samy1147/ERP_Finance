'use client';

import React, { useState, useEffect } from 'react';
import { procurementReportsAPI } from '../../../services/procurement-api';
import { 
  PurchaseAnalytics, 
  SupplierPerformance, 
  ContractExpiry, 
  PaymentSchedule,
  ProcurementCompliance 
} from '../../../types/procurement';
import { 
  DollarSign, 
  TrendingUp, 
  Users, 
  FileText, 
  AlertCircle, 
  Calendar,
  Download,
  ShoppingCart
} from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function ProcurementDashboard() {
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<PurchaseAnalytics | null>(null);
  const [topSuppliers, setTopSuppliers] = useState<SupplierPerformance[]>([]);
  const [expiringContracts, setExpiringContracts] = useState<ContractExpiry[]>([]);
  const [upcomingPayments, setUpcomingPayments] = useState<PaymentSchedule[]>([]);
  const [compliance, setCompliance] = useState<ProcurementCompliance | null>(null);
  
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    fetchDashboardData();
  }, [dateRange]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Fetch purchase analytics
      try {
        const analyticsRes = await procurementReportsAPI.purchaseAnalytics({
          period_start: dateRange.start,
          period_end: dateRange.end,
        });
        setAnalytics(analyticsRes.data);
      } catch (error) {
        console.error('Failed to load analytics', error);
      }

      // Fetch top suppliers
      try {
        const suppliersRes = await procurementReportsAPI.supplierPerformance({
          date_from: dateRange.start,
          date_to: dateRange.end,
        });
        const data = Array.isArray(suppliersRes.data) ? suppliersRes.data : [];
        setTopSuppliers(data.slice(0, 5));
      } catch (error) {
        console.error('Failed to load suppliers', error);
      }

      // Fetch expiring contracts (next 30 days)
      try {
        const contractsRes = await procurementReportsAPI.contractExpiry({ days: 30 });
        const data = Array.isArray(contractsRes.data) ? contractsRes.data : [];
        setExpiringContracts(data.slice(0, 5));
      } catch (error) {
        console.error('Failed to load contracts', error);
      }

      // Fetch upcoming payments (next 7 days)
      try {
        const today = new Date();
        const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
        const paymentsRes = await procurementReportsAPI.paymentSchedule({
          date_from: today.toISOString().split('T')[0],
          date_to: nextWeek.toISOString().split('T')[0],
        });
        const data = Array.isArray(paymentsRes.data) ? paymentsRes.data : [];
        setUpcomingPayments(data.slice(0, 5));
      } catch (error) {
        console.error('Failed to load payments', error);
      }

      // Fetch compliance data
      try {
        const complianceRes = await procurementReportsAPI.procurementCompliance({
          period_start: dateRange.start,
          period_end: dateRange.end,
        });
        setCompliance(complianceRes.data);
      } catch (error) {
        console.error('Failed to load compliance', error);
      }

    } catch (error: any) {
      console.error('Dashboard error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportAnalytics = async (format: 'csv' | 'xlsx' | 'pdf') => {
    try {
      const response = await procurementReportsAPI.exportPurchaseAnalytics({
        period_start: dateRange.start,
        period_end: dateRange.end,
        format,
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `purchase_analytics_${dateRange.start}_to_${dateRange.end}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(`Analytics exported as ${format.toUpperCase()}`);
    } catch (error: any) {
      toast.error('Failed to export analytics');
      console.error(error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Procurement Dashboard</h1>
        <div className="flex gap-2">
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
            className="px-4 py-2 border rounded-lg"
          />
          <span className="flex items-center">to</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
            className="px-4 py-2 border rounded-lg"
          />
          <button
            onClick={() => handleExportAnalytics('xlsx')}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 flex items-center gap-2"
          >
            <Download size={20} />
            Export
          </button>
        </div>
      </div>

      {/* Procurement Modules Navigation */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Link href="/procurement/requisitions" className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105">
          <div className="flex flex-col items-center text-center">
            <FileText className="mb-3" size={48} />
            <h3 className="text-lg font-bold mb-1">Requisitions</h3>
            <p className="text-sm opacity-90">Purchase Requests & Approvals</p>
          </div>
        </Link>

        <Link href="/procurement/pr-to-po" className="bg-gradient-to-br from-indigo-500 to-blue-600 text-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105">
          <div className="flex flex-col items-center text-center">
            <ShoppingCart className="mb-3" size={48} />
            <h3 className="text-lg font-bold mb-1">PR to PO</h3>
            <p className="text-sm opacity-90">Create POs from PRs</p>
          </div>
        </Link>

        <Link href="/procurement/purchase-orders" className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105">
          <div className="flex flex-col items-center text-center">
            <FileText className="mb-3" size={48} />
            <h3 className="text-lg font-bold mb-1">Purchase Orders</h3>
            <p className="text-sm opacity-90">Manage POs & Orders</p>
          </div>
        </Link>

        <Link href="/procurement/receiving" className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105">
          <div className="flex flex-col items-center text-center">
            <DollarSign className="mb-3" size={48} />
            <h3 className="text-lg font-bold mb-1">Receiving</h3>
            <p className="text-sm opacity-90">Goods Receipt & Quality</p>
          </div>
        </Link>

        <Link href="/procurement/vendor-bills" className="bg-gradient-to-br from-yellow-500 to-yellow-600 text-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105">
          <div className="flex flex-col items-center text-center">
            <FileText className="mb-3" size={48} />
            <h3 className="text-lg font-bold mb-1">Vendor Bills</h3>
            <p className="text-sm opacity-90">Invoice Management</p>
          </div>
        </Link>

        <Link href="/procurement/catalog-management" className="bg-gradient-to-br from-orange-500 to-orange-600 text-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105">
          <div className="flex flex-col items-center text-center">
            <DollarSign className="mb-3" size={48} />
            <h3 className="text-lg font-bold mb-1">Catalog Reference</h3>
            <p className="text-sm opacity-90">Browse Items & Prices</p>
          </div>
        </Link>

        <Link href="/procurement/approvals" className="bg-gradient-to-br from-red-500 to-red-600 text-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105">
          <div className="flex flex-col items-center text-center">
            <AlertCircle className="mb-3" size={48} />
            <h3 className="text-lg font-bold mb-1">Approvals</h3>
            <p className="text-sm opacity-90">Workflow Management</p>
          </div>
        </Link>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Spend</p>
              <p className="text-2xl font-bold text-blue-600">
                ${analytics?.total_spend ? parseFloat(analytics.total_spend).toLocaleString() : '0'}
              </p>
            </div>
            <DollarSign className="text-blue-500" size={40} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Invoices</p>
              <p className="text-2xl font-bold text-green-600">
                {analytics?.total_invoices || 0}
              </p>
            </div>
            <FileText className="text-green-500" size={40} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Suppliers</p>
              <p className="text-2xl font-bold text-purple-600">
                {analytics?.total_suppliers || 0}
              </p>
            </div>
            <Users className="text-purple-500" size={40} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Invoice Value</p>
              <p className="text-2xl font-bold text-orange-600">
                ${analytics?.average_invoice_value ? parseFloat(analytics.average_invoice_value).toLocaleString() : '0'}
              </p>
            </div>
            <TrendingUp className="text-orange-500" size={40} />
          </div>
        </div>
      </div>

      {/* Compliance Metrics */}
      {compliance && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-xl font-bold mb-4">Procurement Compliance</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <p className="text-sm text-gray-600">PO Compliance Rate</p>
              <p className="text-3xl font-bold text-blue-600">
                {parseFloat(compliance.po_compliance_rate).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500">
                {compliance.invoices_with_po} of {compliance.total_invoices} invoices
              </p>
            </div>
            <div className="border-l-4 border-green-500 pl-4">
              <p className="text-sm text-gray-600">3-Way Match Rate</p>
              <p className="text-3xl font-bold text-green-600">
                {parseFloat(compliance.three_way_match_rate).toFixed(1)}%
              </p>
            </div>
            <div className="border-l-4 border-purple-500 pl-4">
              <p className="text-sm text-gray-600">Avg Approval Time</p>
              <p className="text-3xl font-bold text-purple-600">
                {compliance.average_approval_time} hrs
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Top Suppliers */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Top Suppliers by Spend</h2>
            <Link href="/procurement/reports/supplier-performance" className="text-blue-600 hover:underline text-sm">
              View All
            </Link>
          </div>
          <div className="space-y-3">
            {topSuppliers.map((supplier, index) => (
              <div key={supplier.supplier_id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div className="flex items-center gap-3">
                  <div className="text-2xl font-bold text-gray-400">#{index + 1}</div>
                  <div>
                    <p className="font-semibold">{supplier.supplier_name}</p>
                    <p className="text-sm text-gray-600">{supplier.total_orders} orders</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-blue-600">
                    ${parseFloat(supplier.total_value).toLocaleString()}
                  </p>
                  <div className="flex gap-2 text-xs text-gray-600">
                    <span>Quality: {parseFloat(supplier.quality_score).toFixed(1)}%</span>
                    <span>On-time: {parseFloat(supplier.on_time_delivery_rate).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Expiring Contracts */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Contracts Expiring Soon</h2>
            <Link href="/procurement/reports/contract-expiry" className="text-blue-600 hover:underline text-sm">
              View All
            </Link>
          </div>
          <div className="space-y-3">
            {expiringContracts.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No contracts expiring in next 30 days</p>
            ) : (
              expiringContracts.map((contract) => (
                <div key={contract.contract_id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <Link href={`/procurement/contracts/${contract.contract_id}`} className="font-semibold text-blue-600 hover:underline">
                      {contract.contract_number}
                    </Link>
                    <p className="text-sm text-gray-600">{contract.title}</p>
                    <p className="text-xs text-gray-500">{contract.supplier_name || contract.customer_name}</p>
                  </div>
                  <div className="text-right">
                    <p className={`font-bold ${contract.days_until_expiry <= 7 ? 'text-red-600' : 'text-orange-600'}`}>
                      {contract.days_until_expiry} days
                    </p>
                    <p className="text-xs text-gray-600">{contract.end_date}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Upcoming Payments */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Upcoming Payments (Next 7 Days)</h2>
          <Link href="/procurement/reports/payment-schedule" className="text-blue-600 hover:underline text-sm">
            View All
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Supplier</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Bill #</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Due Date</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Amount</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {upcomingPayments.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-4 text-center text-gray-500">
                    No upcoming payments in next 7 days
                  </td>
                </tr>
              ) : (
                upcomingPayments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">{payment.supplier_name}</td>
                    <td className="px-4 py-3">
                      <Link href={`/procurement/vendor-bills/${payment.vendor_bill_id}`} className="text-blue-600 hover:underline">
                        {payment.vendor_bill_number}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{payment.due_date}</td>
                    <td className="px-4 py-3 font-semibold">
                      {payment.currency_code} {parseFloat(payment.amount).toFixed(2)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        payment.payment_status === 'OVERDUE' ? 'bg-red-100 text-red-800' :
                        payment.payment_status === 'SCHEDULED' ? 'bg-green-100 text-green-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {payment.payment_status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Spend by Category Chart */}
      {analytics && analytics.spend_by_category && analytics.spend_by_category.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Spend by Category</h2>
          <div className="space-y-3">
            {analytics.spend_by_category.map((category) => (
              <div key={category.category}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">{category.category}</span>
                  <span className="text-sm font-bold text-blue-600">
                    ${parseFloat(category.amount).toLocaleString()} ({parseFloat(category.percentage).toFixed(1)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${category.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

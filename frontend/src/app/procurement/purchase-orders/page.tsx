'use client';

import { useState, useEffect } from 'react';
import { 
  FileText, 
  Plus, 
  Search, 
  Filter,
  Package,
  Clock,
  CheckCircle,
  Send,
  Eye,
  Edit,
  XCircle
} from 'lucide-react';
import Link from 'next/link';

interface POHeader {
  id: number;
  po_number: string;
  po_date: string;
  po_type?: 'CATEGORIZED_GOODS' | 'UNCATEGORIZED_GOODS' | 'SERVICES';
  status: string;
  delivery_status: string;
  vendor_name: string;
  title: string;
  total_amount: string;
  currency: number;  // Currency ID
  currency_code?: string;
  currency_symbol?: string;
  line_count: number;
  pr_number: string;
  created_by_name: string;
  created_at: string;
}

const STATUS_COLORS = {
  DRAFT: 'bg-gray-100 text-gray-800',
  SUBMITTED: 'bg-blue-100 text-blue-800',
  APPROVED: 'bg-green-100 text-green-800',
  CONFIRMED: 'bg-purple-100 text-purple-800',
  PARTIALLY_RECEIVED: 'bg-yellow-100 text-yellow-800',
  RECEIVED: 'bg-teal-100 text-teal-800',
  CLOSED: 'bg-gray-100 text-gray-600',
  CANCELLED: 'bg-red-100 text-red-800',
};

const DELIVERY_STATUS_COLORS = {
  NOT_RECEIVED: 'bg-orange-100 text-orange-800',
  PARTIALLY_RECEIVED: 'bg-yellow-100 text-yellow-800',
  RECEIVED: 'bg-green-100 text-green-800',
};

const DELIVERY_STATUS_LABELS = {
  NOT_RECEIVED: 'Not Received',
  PARTIALLY_RECEIVED: 'Partially Received',
  RECEIVED: 'Fully Received',
};

const STATUS_ICONS = {
  DRAFT: Edit,
  SUBMITTED: Clock,
  APPROVED: CheckCircle,
  CONFIRMED: Send,
  PARTIALLY_RECEIVED: Package,
  RECEIVED: CheckCircle,
  CLOSED: CheckCircle,
  CANCELLED: XCircle,
};

export default function PurchaseOrdersPage() {
  const [orders, setOrders] = useState<POHeader[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetchOrders();
  }, [statusFilter]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      let url = 'http://127.0.0.1:8007/api/procurement/purchase-orders/';
      if (statusFilter) {
        url += `?status=${statusFilter}`;
      }
      const response = await fetch(url);
      const data = await response.json();
      setOrders(data);
    } catch (error) {
      console.error('Error fetching purchase orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredOrders = orders.filter(order =>
    order.po_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    order.vendor_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    order.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const StatusIcon = ({ status }: { status: string }) => {
    const Icon = STATUS_ICONS[status as keyof typeof STATUS_ICONS] || FileText;
    return <Icon className="h-4 w-4" />;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Purchase Orders</h1>
          <p className="text-gray-600 mt-1">
            Manage and track all purchase orders
          </p>
        </div>
        <Link
          href="/procurement/purchase-orders/new"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-5 w-5 mr-2" />
          New PO
        </Link>
      </div>

      {/* Info Banner */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start">
          <FileText className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
          <div>
            <h3 className="text-sm font-semibold text-blue-900">Purchase Order Workflow</h3>
            <p className="text-sm text-blue-800 mt-1">
              After a PR is approved, it's converted to a DRAFT PO. You can then edit vendor details, 
              adjust prices, and set delivery dates before submitting for approval.
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by PO number, vendor, or title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Status Filter */}
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="APPROVED">Approved</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="PARTIALLY_RECEIVED">Partially Received</option>
            <option value="RECEIVED">Fully Received</option>
            <option value="CLOSED">Closed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Draft</p>
              <p className="text-2xl font-bold text-gray-900">
                {orders.filter(o => o.status === 'DRAFT').length}
              </p>
            </div>
            <Edit className="h-8 w-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Submitted</p>
              <p className="text-2xl font-bold text-blue-900">
                {orders.filter(o => o.status === 'SUBMITTED').length}
              </p>
            </div>
            <Clock className="h-8 w-8 text-blue-400" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Approved</p>
              <p className="text-2xl font-bold text-green-900">
                {orders.filter(o => o.status === 'APPROVED').length}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-400" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Confirmed</p>
              <p className="text-2xl font-bold text-purple-900">
                {orders.filter(o => o.status === 'CONFIRMED').length}
              </p>
            </div>
            <Send className="h-8 w-8 text-purple-400" />
          </div>
        </div>
      </div>

      {/* Orders List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading purchase orders...</p>
        </div>
      ) : filteredOrders.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <Package className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Purchase Orders Found</h3>
          <p className="text-gray-600 mb-4">
            {searchTerm || statusFilter
              ? 'Try adjusting your search or filter criteria'
              : 'Get started by converting an approved PR to a PO'}
          </p>
          {!searchTerm && !statusFilter && (
            <Link
              href="/procurement/requisitions"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <FileText className="h-5 w-5 mr-2" />
              Go to Purchase Requisitions
            </Link>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    PO Number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Vendor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Delivery
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredOrders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <FileText className="h-5 w-5 text-gray-400 mr-2" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">{order.po_number}</div>
                        {order.pr_number && (
                          <div className="text-xs text-gray-500">From: {order.pr_number}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(order.po_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{order.vendor_name || 'Not Selected'}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">{order.title}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500">{order.line_count} line(s)</span>
                      {order.po_type && (
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          order.po_type === 'SERVICES' 
                            ? 'bg-purple-100 text-purple-800' 
                            : order.po_type === 'CATEGORIZED_GOODS'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {order.po_type === 'SERVICES' ? '� Services' : order.po_type === 'CATEGORIZED_GOODS' ? '� Cataloged' : '✏️ Free Text'}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[order.status as keyof typeof STATUS_COLORS]}`}>
                      <StatusIcon status={order.status} />
                      <span className="ml-1">{order.status.replace('_', ' ')}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${DELIVERY_STATUS_COLORS[order.delivery_status as keyof typeof DELIVERY_STATUS_COLORS] || 'bg-gray-100 text-gray-800'}`}>
                      {order.delivery_status === 'NOT_RECEIVED' && '📦'}
                      {order.delivery_status === 'PARTIALLY_RECEIVED' && '📦'}
                      {order.delivery_status === 'RECEIVED' && '✅'}
                      <span className="ml-1">{DELIVERY_STATUS_LABELS[order.delivery_status as keyof typeof DELIVERY_STATUS_LABELS] || order.delivery_status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {order.currency_symbol || '$'}{parseFloat(order.total_amount).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <Link
                      href={`/procurement/purchase-orders/${order.id}`}
                      className="inline-flex items-center text-blue-600 hover:text-blue-900"
                    >
                      {order.status === 'DRAFT' ? (
                        <>
                          <Edit className="h-4 w-4 mr-1" />
                          Edit
                        </>
                      ) : (
                        <>
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </>
                      )}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}
    </div>
  );
}

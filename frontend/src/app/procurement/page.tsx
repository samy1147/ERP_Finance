'use client';

import Link from 'next/link';
import { ClipboardList, Package, FileText, CreditCard, CheckCircle, FileSignature, TruckIcon } from 'lucide-react';

export default function ProcurementPage() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Procurement Management</h1>
        <p className="mt-2 text-gray-600">
          Manage purchase requisitions, purchase orders, vendor bills, and payments
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {/* Purchase Requisitions */}
        <Link
          href="/procurement/requisitions"
          className="card hover:shadow-lg transition-shadow cursor-pointer bg-gradient-to-br from-cyan-50 to-blue-50"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClipboardList className="h-8 w-8 text-cyan-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Purchase Requisitions</h3>
              <p className="text-sm text-gray-600">Create & Track PRs</p>
            </div>
          </div>
        </Link>

        {/* Purchase Orders */}
        <Link
          href="/procurement/purchase-orders"
          className="card hover:shadow-lg transition-shadow cursor-pointer bg-gradient-to-br from-indigo-50 to-purple-50"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Package className="h-8 w-8 text-indigo-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Purchase Orders</h3>
              <p className="text-sm text-gray-600">Manage POs</p>
            </div>
          </div>
        </Link>

        {/* Vendor Bills */}
        <Link
          href="/procurement/vendor-bills"
          className="card hover:shadow-lg transition-shadow cursor-pointer bg-gradient-to-br from-green-50 to-emerald-50"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <FileText className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Vendor Bills</h3>
              <p className="text-sm text-gray-600">3-Way Match & Approval</p>
            </div>
          </div>
        </Link>

        {/* Goods Receipt */}
        <Link
          href="/procurement/receiving"
          className="card hover:shadow-lg transition-shadow cursor-pointer bg-gradient-to-br from-teal-50 to-cyan-50"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TruckIcon className="h-8 w-8 text-teal-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Goods Receipt</h3>
              <p className="text-sm text-gray-600">Record Deliveries</p>
            </div>
          </div>
        </Link>

        {/* Approvals */}
        <Link
          href="/procurement/approvals"
          className="card hover:shadow-lg transition-shadow cursor-pointer bg-gradient-to-br from-yellow-50 to-orange-50"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Approvals</h3>
              <p className="text-sm text-gray-600">Workflow Management</p>
            </div>
          </div>
        </Link>

        {/* Catalog Management */}
        <Link
          href="/procurement/catalog-management"
          className="card hover:shadow-lg transition-shadow cursor-pointer bg-gradient-to-br from-purple-50 to-pink-50"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <FileSignature className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Catalog Management</h3>
              <p className="text-sm text-gray-600">Product Catalogs</p>
            </div>
          </div>
        </Link>
      </div>

      <div className="mt-8 card">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Link href="/procurement/requisitions/new" className="btn-primary text-center">
            Create Purchase Requisition
          </Link>
          <Link href="/procurement/purchase-orders/new" className="btn-primary text-center">
            Create Purchase Order
          </Link>
          <Link href="/procurement/vendor-bills" className="btn-primary text-center bg-green-600 hover:bg-green-700">
            Create Vendor Bill
          </Link>
          <Link href="/procurement/receiving" className="btn-primary text-center bg-teal-600 hover:bg-teal-700">
            Record Goods Receipt
          </Link>
          <Link href="/procurement/approvals" className="btn-primary text-center bg-yellow-600 hover:bg-yellow-700">
            View Pending Approvals
          </Link>
        </div>
      </div>
    </div>
  );
}

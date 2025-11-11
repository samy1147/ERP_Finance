'use client';

import Link from 'next/link';
import { BarChart3, FileText, DollarSign, BookOpen, List, Globe, Receipt, TrendingUp, Building2, CheckCircle, ShoppingCart, CreditCard, FileSignature, LayoutDashboard, ClipboardList, Package, Boxes, MapPin, Calculator } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome to Finance ERP - Manage your GL, AR, AP, Multi-Currency, and Tax operations
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* Setup Card */}
        <Link
          href="/setup"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BookOpen className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Setup</h3>
              <p className="text-sm text-gray-600">Segments & Types</p>
            </div>
          </div>
        </Link>

        {/* Journal Entries Card */}
        <Link
          href="/journals"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <List className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Journal Entries</h3>
              <p className="text-sm text-gray-600">General Ledger</p>
            </div>
          </div>
        </Link>

        {/* Journal Lines Card */}
        <Link
          href="/journal-lines"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BookOpen className="h-8 w-8 text-indigo-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Journal Lines</h3>
              <p className="text-sm text-gray-600">Line Item Analysis</p>
            </div>
          </div>
        </Link>

        {/* AR Card */}
        <Link
          href="/ar/invoices"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <FileText className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">
                Accounts Receivable
              </h3>
              <p className="text-sm text-gray-600">Customer Invoices</p>
            </div>
          </div>
        </Link>

        {/* AP Card */}
        <Link
          href="/ap/invoices"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DollarSign className="h-8 w-8 text-red-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">
                Accounts Payable
              </h3>
              <p className="text-sm text-gray-600">Supplier Invoices</p>
            </div>
          </div>
        </Link>

        {/* Reports Card */}
        <Link
          href="/reports"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BarChart3 className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Reports</h3>
              <p className="text-sm text-gray-600">Financial Reports</p>
            </div>
          </div>
        </Link>

        {/* Currencies Card */}
        <Link
          href="/currencies"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Globe className="h-8 w-8 text-indigo-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Currencies</h3>
              <p className="text-sm text-gray-600">Currency Management</p>
            </div>
          </div>
        </Link>

        {/* Exchange Rates Card */}
        <Link
          href="/fx/rates"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-cyan-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Exchange Rates</h3>
              <p className="text-sm text-gray-600">FX Management</p>
            </div>
          </div>
        </Link>

        {/* FX Configuration Card */}
        <Link
          href="/fx/config"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Globe className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">FX Configuration</h3>
              <p className="text-sm text-gray-600">Base Currency & Accounts</p>
            </div>
          </div>
        </Link>

        {/* Tax Rates Card */}
        <Link
          href="/tax-rates"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Receipt className="h-8 w-8 text-orange-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Tax Rates</h3>
              <p className="text-sm text-gray-600">VAT/Tax Configuration</p>
            </div>
          </div>
        </Link>

        {/* Corporate Tax Card */}
        <Link
          href="/tax/corporate"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Building2 className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Corporate Tax</h3>
              <p className="text-sm text-gray-600">Income Tax Management</p>
            </div>
          </div>
        </Link>

        {/* Customers Card */}
        <Link
          href="/customers"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BookOpen className="h-8 w-8 text-teal-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Customers</h3>
              <p className="text-sm text-gray-600">Customer Management</p>
            </div>
          </div>
        </Link>

        {/* Suppliers Card */}
        <Link
          href="/suppliers"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <FileText className="h-8 w-8 text-amber-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Suppliers</h3>
              <p className="text-sm text-gray-600">Supplier Management</p>
            </div>
          </div>
        </Link>

        {/* Invoice Approvals Card */}
        <Link
          href="/invoice-approvals"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Invoice Approvals</h3>
              <p className="text-sm text-gray-600">Review & Approve</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Asset Management Section */}
      <div className="mt-12">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Boxes className="h-7 w-7 text-emerald-600 mr-2" />
            Asset Management
          </h2>
          <p className="mt-2 text-gray-600">
            Track and manage fixed assets, depreciation, and asset lifecycle
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {/* Asset Register */}
          <Link
            href="/fixed-assets"
            className="card hover:shadow-lg transition-shadow cursor-pointer bg-gradient-to-br from-emerald-50 to-teal-50"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Boxes className="h-8 w-8 text-emerald-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Asset Register</h3>
                <p className="text-sm text-gray-600">All Assets</p>
              </div>
            </div>
          </Link>

          {/* Asset Categories */}
          <Link
            href="/fixed-assets/categories"
            className="card hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <List className="h-8 w-8 text-teal-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Asset Categories</h3>
                <p className="text-sm text-gray-600">Categories & Setup</p>
              </div>
            </div>
          </Link>

          {/* Asset Locations */}
          <Link
            href="/fixed-assets/locations"
            className="card hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <MapPin className="h-8 w-8 text-cyan-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Asset Locations</h3>
                <p className="text-sm text-gray-600">Locations & Custodians</p>
              </div>
            </div>
          </Link>

          {/* Depreciation */}
          <Link
            href="/fixed-assets/depreciation"
            className="card hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Calculator className="h-8 w-8 text-orange-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Depreciation</h3>
                <p className="text-sm text-gray-600">Calculate & Post</p>
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* Procurement Section */}
      <div className="mt-12">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <ShoppingCart className="h-7 w-7 text-blue-600 mr-2" />
            Procurement Management
          </h2>
          <p className="mt-2 text-gray-600">
            Access procurement dashboard and all procurement operations
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-2">
          {/* Procurement Dashboard */}
          <Link
            href="/procurement/dashboard"
            className="card hover:shadow-lg transition-shadow cursor-pointer bg-gradient-to-br from-blue-50 to-indigo-50"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <LayoutDashboard className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Procurement Dashboard</h3>
                <p className="text-sm text-gray-600">Analytics & Insights</p>
              </div>
            </div>
          </Link>

          {/* Procurement Module */}
          <Link
            href="/procurement"
            className="card hover:shadow-lg transition-shadow cursor-pointer bg-gradient-to-br from-indigo-50 to-purple-50"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ShoppingCart className="h-8 w-8 text-indigo-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Procurement</h3>
                <p className="text-sm text-gray-600">PRs, POs, Bills & Payments</p>
              </div>
            </div>
          </Link>
        </div>
      </div>

      <div className="mt-8 card">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Link href="/ar/invoices/new" className="btn-primary text-center">
            Create AR Invoice
          </Link>
          <Link href="/ap/invoices/new" className="btn-primary text-center">
            Create AP Invoice
          </Link>
          <Link href="/ar/payments/new" className="btn-primary text-center">
            Receive Payment
          </Link>
          <Link href="/ap/payments/new" className="btn-primary text-center">
            Make Payment
          </Link>
          <Link href="/procurement/vendor-bills" className="btn-primary text-center bg-green-600 hover:bg-green-700">
            Create Vendor Bill
          </Link>
          <Link href="/procurement/payment-requests" className="btn-primary text-center bg-purple-600 hover:bg-purple-700">
            New Payment Request
          </Link>
          <Link href="/fixed-assets/categories/new" className="btn-primary text-center bg-emerald-600 hover:bg-emerald-700">
            New Asset Category
          </Link>
          <Link href="/fixed-assets" className="btn-primary text-center bg-teal-600 hover:bg-teal-700">
            Register New Asset
          </Link>
        </div>
      </div>
    </div>
  );
}

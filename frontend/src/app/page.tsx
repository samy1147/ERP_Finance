'use client';

import Link from 'next/link';
import { BarChart3, FileText, DollarSign, BookOpen, List, Globe, Receipt, TrendingUp, Building2, CheckCircle } from 'lucide-react';

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
        {/* Accounts Card */}
        <Link
          href="/accounts"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BookOpen className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Accounts</h3>
              <p className="text-sm text-gray-600">Chart of Accounts</p>
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

      <div className="mt-8 card">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
        </div>
      </div>
    </div>
  );
}

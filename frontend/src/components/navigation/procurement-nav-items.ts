// Add these navigation items to your existing navigation component

export const procurementNavItems = [
  {
    title: 'Procurement',
    icon: 'ShoppingCart', // or any icon from lucide-react
    children: [
      {
        title: 'Dashboard',
        href: '/procurement/dashboard',
        icon: 'LayoutDashboard',
        description: 'Analytics and insights'
      },
      {
        title: 'Vendor Bills',
        href: '/procurement/vendor-bills',
        icon: 'FileText',
        description: '3-way matching & approval'
      },
      {
        title: 'Payment Requests',
        href: '/procurement/payment-requests',
        icon: 'CreditCard',
        description: 'Payment processing & approval'
      },
      {
        title: 'Payment Batches',
        href: '/procurement/payment-batches',
        icon: 'Layers',
        description: 'Batch payment processing'
      },
      {
        title: 'Contracts',
        href: '/procurement/contracts',
        icon: 'FileSignature',
        description: 'Contract management'
      },
      {
        title: 'Purchase Requisitions',
        href: '/procurement/requisitions',
        icon: 'ShoppingBag',
        description: 'PR approval workflow'
      },
      {
        title: 'Goods Receipts',
        href: '/procurement/goods-receipts',
        icon: 'Package',
        description: 'Receiving & inspection'
      },
      {
        title: 'Bank Reconciliation',
        href: '/procurement/bank-reconciliation',
        icon: 'Building',
        description: 'Reconcile bank statements'
      },
      {
        title: 'Reports',
        icon: 'BarChart3',
        children: [
          {
            title: 'Purchase Analytics',
            href: '/procurement/reports/purchase-analytics',
            description: 'Spend analysis by category'
          },
          {
            title: 'Supplier Performance',
            href: '/procurement/reports/supplier-performance',
            description: 'Vendor scorecards'
          },
          {
            title: 'Contract Expiry',
            href: '/procurement/reports/contract-expiry',
            description: 'Upcoming contract renewals'
          },
          {
            title: 'Payment Schedule',
            href: '/procurement/reports/payment-schedule',
            description: 'Cash flow forecast'
          },
          {
            title: 'Compliance Report',
            href: '/procurement/reports/compliance',
            description: 'PO compliance & 3-way match'
          },
        ]
      },
      {
        title: 'Configuration',
        icon: 'Settings',
        children: [
          {
            title: 'Payment Methods',
            href: '/procurement/config/payment-methods',
            description: 'Configure payment methods'
          },
          {
            title: 'Payment Terms',
            href: '/procurement/config/payment-terms',
            description: 'Configure payment terms'
          },
          {
            title: 'Bank Accounts',
            href: '/procurement/config/bank-accounts',
            description: 'Manage bank accounts'
          },
          {
            title: 'Contract Templates',
            href: '/procurement/config/contract-templates',
            description: 'Manage contract templates'
          },
        ]
      }
    ]
  }
];

// Example integration with existing navigation
// If you have a sidebar component, add this:

/*
import { 
  LayoutDashboard, 
  FileText, 
  CreditCard, 
  Layers,
  FileSignature,
  ShoppingBag,
  Package,
  Building,
  BarChart3,
  Settings,
  ShoppingCart
} from 'lucide-react';

const navigation = [
  // ... existing nav items (Accounts, Journals, Invoices, etc.)
  
  // Add Procurement section
  {
    name: 'Procurement',
    icon: ShoppingCart,
    children: [
      { name: 'Dashboard', href: '/procurement/dashboard', icon: LayoutDashboard },
      { name: 'Vendor Bills', href: '/procurement/vendor-bills', icon: FileText },
      { name: 'Payment Requests', href: '/procurement/payment-requests', icon: CreditCard },
      { name: 'Contracts', href: '/procurement/contracts', icon: FileSignature },
      // ... more items
    ]
  }
];
*/

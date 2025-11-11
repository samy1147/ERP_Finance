import api from '../lib/api';
import {
  Account,
  ARInvoice,
  ARPayment,
  APInvoice,
  APPayment,
  BankAccount,
  Customer,
  Supplier,
  Currency,
  JournalEntry,
  JournalLine,
  TaxRate,
  ExchangeRate,
  FXGainLossAccount,
  CorporateTaxFiling,
  InvoiceApproval,
} from '../types';

// Accounts (now using segment API)
export const accountsAPI = {
  list: () => api.get<Account[]>('/segment/accounts/'),
  get: (code: string) => api.get<Account>(`/segment/accounts/${code}/`),
  create: (data: Partial<Account>) => api.post<Account>('/segment/accounts/', data),
  update: (code: string, data: Partial<Account>) => api.patch<Account>(`/segment/accounts/${code}/`, data),
  delete: (code: string) => api.delete(`/segment/accounts/${code}/`),
  hierarchy: () => api.get<Account[]>('/segment/accounts/hierarchy/'),
};

// Segment Types
export interface SegmentType {
  segment_id: number;
  segment_name: string;
  segment_type: string;
  description?: string;
  is_required: boolean;
  has_hierarchy: boolean;
  is_active: boolean;
  display_order: number;
  code_length?: number;
}

export const segmentTypesAPI = {
  list: () => api.get<SegmentType[]>('/segment/types/'),
  get: (id: number) => api.get<SegmentType>(`/segment/types/${id}/`),
};

// Segments
export interface Segment {
  id: number;
  segment_type: number;
  code: string;
  alias: string;
  node_type: 'parent' | 'child';
  parent_code?: string;
  level: number;
  is_active: boolean;
}

export const segmentsAPI = {
  list: (params?: { segment_type?: number; node_type?: string; is_active?: boolean }) => 
    api.get<Segment[]>('/segment/values/', { params }),
  get: (id: number) => api.get<Segment>(`/segment/values/${id}/`),
};

// Journal Entries
export const journalEntriesAPI = {
  list: () => api.get<JournalEntry[]>('/journals/'),
  get: (id: number) => api.get<JournalEntry>(`/journals/${id}/`),
  create: (data: Partial<JournalEntry>) => api.post<JournalEntry>('/journals/', data),
  update: (id: number, data: Partial<JournalEntry>) => api.patch<JournalEntry>(`/journals/${id}/`, data),
  delete: (id: number) => api.delete(`/journals/${id}/`),
  reverse: (id: number) => api.post(`/journals/${id}/reverse/`),
  post: (id: number) => api.post(`/journals/${id}/post/`),
  export: (format: 'csv' | 'xlsx') => api.get('/journals/export/', {
    params: { format },
    responseType: 'blob'
  }),
};

// Journal Lines
export interface JournalLineDetail {
  id: number;
  debit: string;
  credit: string;
  entry: {
    id: number;
    date: string;
    memo: string;
    posted: boolean;
    currency: number;
  };
  account: {
    id: number;
    code: string;
    name: string;
    type: string;
  };
}

export const journalLinesAPI = {
  list: (params?: {
    account_code?: string;
    account_name?: string;
    date_from?: string;
    date_to?: string;
    posted?: boolean;
    entry_id?: number;
  }) => api.get<JournalLineDetail[]>('/journal-lines/', { params }),
  get: (id: number) => api.get<JournalLineDetail>(`/journal-lines/${id}/`),
};

// AR Invoices
export const arInvoicesAPI = {
  list: () => api.get<ARInvoice[]>('/ar/invoices/'),
  get: (id: number) => api.get<ARInvoice>(`/ar/invoices/${id}/`),
  create: (data: Partial<ARInvoice>) => api.post<ARInvoice>('/ar/invoices/', data),
  update: (id: number, data: Partial<ARInvoice>) => api.patch<ARInvoice>(`/ar/invoices/${id}/`, data),
  delete: (id: number) => api.delete(`/ar/invoices/${id}/`),
  post: (id: number) => api.post(`/ar/invoices/${id}/post-gl/`),
  reverse: (id: number) => api.post(`/ar/invoices/${id}/reverse/`),
  submitForApproval: (id: number, data: { submitted_by: string }) => 
    api.post(`/ar/invoices/${id}/submit-for-approval/`, data),
};

// AR Payments
export const arPaymentsAPI = {
  list: () => api.get<ARPayment[]>('/ar/payments/'),
  get: (id: number) => api.get<ARPayment>(`/ar/payments/${id}/`),
  create: (data: Partial<ARPayment>) => api.post<ARPayment>('/ar/payments/', data),
  update: (id: number, data: Partial<ARPayment>) => api.patch<ARPayment>(`/ar/payments/${id}/`, data),
  delete: (id: number) => api.delete(`/ar/payments/${id}/`),
  post: (id: number) => api.post(`/ar/payments/${id}/post/`),
};

// AP Invoices
export const apInvoicesAPI = {
  list: () => api.get<APInvoice[]>('/ap/invoices/'),
  get: (id: number) => api.get<APInvoice>(`/ap/invoices/${id}/`),
  create: (data: Partial<APInvoice>) => api.post<APInvoice>('/ap/invoices/', data),
  update: (id: number, data: Partial<APInvoice>) => api.patch<APInvoice>(`/ap/invoices/${id}/`, data),
  delete: (id: number) => api.delete(`/ap/invoices/${id}/`),
  post: (id: number) => api.post(`/ap/invoices/${id}/post-gl/`),
  reverse: (id: number) => api.post(`/ap/invoices/${id}/reverse/`),
  submitForApproval: (id: number, data: { submitted_by: string }) => 
    api.post(`/ap/invoices/${id}/submit-for-approval/`, data),
  threeWayMatch: (id: number) => api.post(`/ap/invoices/${id}/three-way-match/`),
};

// AP Payments
export const apPaymentsAPI = {
  list: () => api.get<APPayment[]>('/ap/payments/'),
  get: (id: number) => api.get<APPayment>(`/ap/payments/${id}/`),
  create: (data: Partial<APPayment>) => api.post<APPayment>('/ap/payments/', data),
  update: (id: number, data: Partial<APPayment>) => api.patch<APPayment>(`/ap/payments/${id}/`, data),
  delete: (id: number) => api.delete(`/ap/payments/${id}/`),
  post: (id: number) => api.post(`/ap/payments/${id}/post/`),
};

// Bank Accounts
export const bankAccountsAPI = {
  list: () => api.get<BankAccount[]>('/bank-accounts/'),
  get: (id: number) => api.get<BankAccount>(`/bank-accounts/${id}/`),
  create: (data: Partial<BankAccount>) => api.post<BankAccount>('/bank-accounts/', data),
  update: (id: number, data: Partial<BankAccount>) => api.patch<BankAccount>(`/bank-accounts/${id}/`, data),
  delete: (id: number) => api.delete(`/bank-accounts/${id}/`),
};

// Customers
export const customersAPI = {
  list: () => api.get<Customer[]>('/customers/'),
  get: (id: number) => api.get<Customer>(`/customers/${id}/`),
  create: (data: Partial<Customer>) => api.post<Customer>('/customers/', data),
  update: (id: number, data: Partial<Customer>) => api.patch<Customer>(`/customers/${id}/`, data),
  delete: (id: number) => api.delete(`/customers/${id}/`),
};

// Suppliers - Updated to use correct endpoint
export const suppliersAPI = {
  list: () => api.get<Supplier[]>('/ap/vendors/'),
  get: (id: number) => api.get<Supplier>(`/ap/vendors/${id}/`),
  create: (data: Partial<Supplier>) => api.post<Supplier>('/ap/vendors/', data),
  update: (id: number, data: Partial<Supplier>) => api.patch<Supplier>(`/ap/vendors/${id}/`, data),
  delete: (id: number) => api.delete(`/ap/vendors/${id}/`),
  
  // Vendor-specific custom actions
  markPreferred: (id: number) => api.post(`/ap/vendors/${id}/mark_preferred/`, {}),
  removePreferred: (id: number) => api.post(`/ap/vendors/${id}/remove_preferred/`, {}),
  putOnHold: (id: number, data: { reason: string }) => api.post(`/ap/vendors/${id}/put_on_hold/`, data),
  removeHold: (id: number) => api.post(`/ap/vendors/${id}/remove_hold/`, {}),
  blacklist: (id: number, data: { reason: string }) => api.post(`/ap/vendors/${id}/blacklist/`, data),
  removeBlacklist: (id: number) => api.post(`/ap/vendors/${id}/remove_blacklist/`, {}),
  updatePerformance: (id: number, data: { 
    performance_score?: number;
    quality_score?: number;
    delivery_score?: number;
  }) => api.post(`/ap/vendors/${id}/update_performance/`, data),
};

// Currencies
export const currenciesAPI = {
  list: () => api.get<Currency[]>('/currencies/'),
  get: (id: number) => api.get<Currency>(`/currencies/${id}/`),
  create: (data: Partial<Currency>) => api.post<Currency>('/currencies/', data),
  update: (id: number, data: Partial<Currency>) => api.patch<Currency>(`/currencies/${id}/`, data),
  delete: (id: number) => api.delete(`/currencies/${id}/`),
};

// Tax Rates
export const taxRatesAPI = {
  list: (country?: string) => api.get('/tax/rates/', { params: { country } }),
  seedPresets: () => api.post('/tax/seed-presets/'),
};

// Exchange Rates
export const exchangeRatesAPI = {
  list: (params?: { from_currency?: number; to_currency?: number; rate_type?: string; date_from?: string; date_to?: string }) => 
    api.get<ExchangeRate[]>('/fx/rates/', { params }),
  get: (id: number) => api.get<ExchangeRate>(`/fx/rates/${id}/`),
  create: (data: Partial<ExchangeRate>) => api.post<ExchangeRate>('/fx/rates/', data),
  createByCode: (data: { from_currency_code: string; to_currency_code: string; rate: string; rate_date: string; rate_type?: string; source?: string }) => 
    api.post('/fx/create-rate/', data),
  update: (id: number, data: Partial<ExchangeRate>) => api.patch<ExchangeRate>(`/fx/rates/${id}/`, data),
  delete: (id: number) => api.delete(`/fx/rates/${id}/`),
  convert: (data: { amount: string; from_currency_code: string; to_currency_code: string; rate_date?: string; rate_type?: string }) => 
    api.post('/fx/convert/', data),
};

// FX Configuration
export const fxConfigAPI = {
  baseCurrency: () => api.get('/fx/base-currency/'),
  gainLossAccounts: {
    list: () => api.get<FXGainLossAccount[]>('/fx/accounts/'),
    get: (id: number) => api.get<FXGainLossAccount>(`/fx/accounts/${id}/`),
    create: (data: Partial<FXGainLossAccount>) => api.post<FXGainLossAccount>('/fx/accounts/', data),
    update: (id: number, data: Partial<FXGainLossAccount>) => api.patch<FXGainLossAccount>(`/fx/accounts/${id}/`, data),
    delete: (id: number) => api.delete(`/fx/accounts/${id}/`),
  },
};

// Corporate Tax
export const corporateTaxAPI = {
  accrual: (data: { country: string; period_start: string; period_end: string; tax_rate: string }) => 
    api.post('/tax/corporate-accrual/', {
      country: data.country,
      date_from: data.period_start,
      date_to: data.period_end
    }),
  breakdown: (params?: { period_start?: string; period_end?: string }) => 
    api.get('/tax/corporate-breakdown/', { 
      params: {
        date_from: params?.period_start,
        date_to: params?.period_end
      }
    }),
  filing: {
    get: (filingId: number) => api.get(`/tax/corporate-filing/${filingId}/`),
    file: (filingId: number) => api.post(`/tax/corporate-file/${filingId}/`),
    reversePreview: (filingId: number) => api.get(`/tax/corporate-reverse/${filingId}/`),
    reverse: (filingId: number) => api.post(`/tax/corporate-reverse/${filingId}/`),
  },
};

// Reports
export const reportsAPI = {
  trialBalance: (dateFrom?: string, dateTo?: string, format?: string) => 
    api.get('/reports/trial-balance/', { 
      params: { date_from: dateFrom, date_to: dateTo, file_type: format },
      responseType: format === 'csv' || format === 'xlsx' ? 'blob' : 'json'
    }),
  arAging: (asOfDate?: string, format?: string) => 
    api.get('/reports/ar-aging/', { 
      params: { as_of: asOfDate, file_type: format },
      responseType: format === 'csv' || format === 'xlsx' ? 'blob' : 'json'
    }),
  apAging: (asOfDate?: string, format?: string) => 
    api.get('/reports/ap-aging/', { 
      params: { as_of: asOfDate, file_type: format },
      responseType: format === 'csv' || format === 'xlsx' ? 'blob' : 'json'
    }),
};

// Invoice Approvals
export const invoiceApprovalsAPI = {
  list: () => api.get<InvoiceApproval[]>('/invoice-approvals/'),
  get: (id: number) => api.get<InvoiceApproval>(`/invoice-approvals/${id}/`),
  create: (data: Partial<InvoiceApproval>) => api.post<InvoiceApproval>('/invoice-approvals/', data),
  update: (id: number, data: Partial<InvoiceApproval>) => api.patch<InvoiceApproval>(`/invoice-approvals/${id}/`, data),
  delete: (id: number) => api.delete(`/invoice-approvals/${id}/`),
  approve: (id: number, comments?: string) => api.post(`/invoice-approvals/${id}/approve/`, { comments }),
  reject: (id: number, comments?: string) => api.post(`/invoice-approvals/${id}/reject/`, { comments }),
};

// Outstanding Invoices
export const outstandingInvoicesAPI = {
  getByCustomer: (customerId: number) => api.get(`/outstanding-invoices/?customer=${customerId}`),
  getBySupplier: (supplierId: number) => api.get(`/outstanding-invoices/?supplier=${supplierId}`),
};

// Attachments API
export const attachmentsAPI = {
  // List attachments with optional filters
  list: (params?: { po_header?: number; pr_header?: number; temp_session?: string }) => 
    api.get('/procurement/attachments/', { params }),
  
  // Get single attachment
  get: (id: number) => 
    api.get(`/procurement/attachments/${id}/`),
  
  // Upload file for PO
  uploadPO: (poId: number, file: File, documentType: string, description: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('po_header', poId.toString());
    formData.append('document_type', documentType);
    formData.append('description', description);
    formData.append('is_temporary', 'false');
    
    return api.post('/procurement/attachments/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // Upload file for PR
  uploadPR: (prId: number, file: File, documentType: string, description: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('pr_header', prId.toString());
    formData.append('document_type', documentType);
    formData.append('description', description);
    formData.append('is_temporary', 'false');
    
    return api.post('/procurement/attachments/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // Upload temporary file (before document creation)
  uploadTemp: (tempSession: string, file: File, documentType: string, description: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('temp_session', tempSession);
    formData.append('document_type', documentType);
    formData.append('description', description);
    formData.append('is_temporary', 'true');
    
    return api.post('/procurement/attachments/upload-temp/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // Link temporary attachments to PO
  linkToPO: (tempSession: string, poId: number) => {
    return api.post('/procurement/attachments/link-to-po/', {
      temp_session: tempSession,
      po_header: poId,
    });
  },
  
  // Link temporary attachments to PR
  linkToPR: (tempSession: string, prId: number) => {
    return api.post('/procurement/attachments/link-to-pr/', {
      temp_session: tempSession,
      pr_header: prId,
    });
  },
  
  // Delete attachment
  delete: (id: number) => 
    api.delete(`/procurement/attachments/${id}/`),
  
  // Download attachment (returns the file URL)
  getDownloadUrl: (fileUrl: string) => {
    // If it's a relative URL, prepend the API base URL
    if (fileUrl.startsWith('/media/')) {
      return `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8007'}${fileUrl}`;
    }
    return fileUrl;
  },
};

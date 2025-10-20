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

// Accounts
export const accountsAPI = {
  list: () => api.get<Account[]>('/accounts/'),
  get: (id: number) => api.get<Account>(`/accounts/${id}/`),
  create: (data: Partial<Account>) => api.post<Account>('/accounts/', data),
  update: (id: number, data: Partial<Account>) => api.patch<Account>(`/accounts/${id}/`, data),
  delete: (id: number) => api.delete(`/accounts/${id}/`),
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

// Suppliers
export const suppliersAPI = {
  list: () => api.get<Supplier[]>('/suppliers/'),
  get: (id: number) => api.get<Supplier>(`/suppliers/${id}/`),
  create: (data: Partial<Supplier>) => api.post<Supplier>('/suppliers/', data),
  update: (id: number, data: Partial<Supplier>) => api.patch<Supplier>(`/suppliers/${id}/`, data),
  delete: (id: number) => api.delete(`/suppliers/${id}/`),
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

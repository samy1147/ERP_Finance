import api from '../lib/api';
import {
  VendorBill,
  ThreeWayMatchResult,
  MatchingIssue,
  BillAttachment,
  PaymentRequest,
  PaymentBatch,
  PaymentApproval,
  BankReconciliation,
  ReconciliationItem,
  PaymentMethod,
  PaymentTerm,
  BankAccount,
  Contract,
  ContractMilestone,
  ContractAmendment,
  ContractAttachment,
  ContractTemplate,
  PurchaseAnalytics,
  SupplierPerformance,
  ContractExpiry,
  PaymentSchedule,
  VendorSpend,
  ProcurementCompliance,
  CashFlowForecast,
  PurchaseRequisition,
  GoodsReceipt,
} from '../types/procurement';

// ============================================================================
// VENDOR BILL API
// ============================================================================

export const vendorBillsAPI = {
  // CRUD Operations
  list: (params?: {
    status?: string;
    match_status?: string;
    supplier?: number;
    date_from?: string;
    date_to?: string;
  }) => api.get<VendorBill[]>('/procurement/vendor-bills/bills/', { params }),
  
  get: (id: number) => api.get<VendorBill>(`/procurement/vendor-bills/bills/${id}/`),
  
  create: (data: Partial<VendorBill>) => api.post<VendorBill>('/procurement/vendor-bills/bills/', data),
  
  update: (id: number, data: Partial<VendorBill>) => 
    api.patch<VendorBill>(`/procurement/vendor-bills/bills/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/vendor-bills/bills/${id}/`),

  // Custom Actions
  submit: (id: number) => 
    api.post(`/procurement/vendor-bills/bills/${id}/submit/`, {}),
  
  performMatch: (id: number, data?: { tolerance_percentage?: number }) => 
    api.post<ThreeWayMatchResult>(`/procurement/vendor-bills/bills/${id}/match/`, data),
  
  validateBill: (id: number) => 
    api.post(`/procurement/vendor-bills/bills/${id}/validate_bill/`, {}),
  
  approveBill: (id: number, data?: { comments?: string }) => 
    api.post(`/procurement/vendor-bills/bills/${id}/approve/`, data),
  
  rejectBill: (id: number, data: { reason: string }) => 
    api.post(`/procurement/vendor-bills/bills/${id}/reject/`, data),
  
  postBill: (id: number) => 
    api.post(`/procurement/vendor-bills/bills/${id}/post_to_ap/`, {}),
  
  cancelBill: (id: number, data: { reason: string }) => 
    api.post(`/procurement/vendor-bills/bills/${id}/cancel/`, data),
  
  createAPInvoice: (id: number) => 
    api.post(`/procurement/vendor-bills/bills/${id}/create_ap_invoice/`, {}),
  
  // Matching Issues
  getMatchingIssues: (billId: number) => 
    api.get<MatchingIssue[]>(`/procurement/vendor-bills/bills/${billId}/matching-issues/`),
  
  resolveIssue: (billId: number, issueId: number, data: { resolution_notes: string }) => 
    api.post(`/procurement/vendor-bills/bills/${billId}/resolve-issue/${issueId}/`, data),
  
  // Attachments
  uploadAttachment: (billId: number, formData: FormData) => 
    api.post<BillAttachment>(`/procurement/vendor-bills/bills/${billId}/upload-attachment/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  
  deleteAttachment: (billId: number, attachmentId: number) => 
    api.delete(`/procurement/vendor-bills/bills/${billId}/attachments/${attachmentId}/`),

  // Bulk Operations
  bulkApprove: (billIds: number[]) => 
    api.post('/procurement/vendor-bills/bills/bulk-approve/', { bill_ids: billIds }),
  
  bulkPost: (billIds: number[]) => 
    api.post('/procurement/vendor-bills/bills/bulk-post/', { bill_ids: billIds }),
};

// ============================================================================
// PAYMENT INTEGRATION API
// ============================================================================

export const paymentRequestsAPI = {
  list: (params?: {
    status?: string;
    supplier?: number;
    date_from?: string;
    date_to?: string;
    priority?: string;
  }) => api.get<PaymentRequest[]>('/procurement/payments/requests/', { params }),
  
  get: (id: number) => api.get<PaymentRequest>(`/procurement/payments/requests/${id}/`),
  
  create: (data: Partial<PaymentRequest>) => 
    api.post<PaymentRequest>('/procurement/payments/requests/', data),
  
  update: (id: number, data: Partial<PaymentRequest>) => 
    api.patch<PaymentRequest>(`/procurement/payments/requests/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/payments/requests/${id}/`),

  // Custom Actions
  submit: (id: number) => 
    api.post(`/procurement/payments/requests/${id}/submit/`, {}),
  
  approve: (id: number, data?: { comments?: string }) => 
    api.post(`/procurement/payments/requests/${id}/approve/`, data),
  
  reject: (id: number, data: { reason: string }) => 
    api.post(`/procurement/payments/requests/${id}/reject/`, data),
  
  process: (id: number) => 
    api.post(`/procurement/payments/requests/${id}/process/`, {}),
  
  cancel: (id: number, data: { reason: string }) => 
    api.post(`/procurement/payments/requests/${id}/cancel/`, data),
  
  generatePaymentFile: (id: number, format: 'ACH' | 'WIRE' | 'CHECK') => 
    api.post(`/procurement/payments/requests/${id}/generate-file/`, { format }, { responseType: 'blob' }),
};

export const paymentBatchesAPI = {
  list: (params?: {
    status?: string;
    payment_method?: string;
    date_from?: string;
    date_to?: string;
  }) => api.get<PaymentBatch[]>('/procurement/payments/batches/', { params }),
  
  get: (id: number) => api.get<PaymentBatch>(`/procurement/payments/batches/${id}/`),
  
  create: (data: Partial<PaymentBatch>) => 
    api.post<PaymentBatch>('/procurement/payments/batches/', data),
  
  update: (id: number, data: Partial<PaymentBatch>) => 
    api.patch<PaymentBatch>(`/procurement/payments/batches/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/payments/batches/${id}/`),

  // Custom Actions
  addPayments: (id: number, paymentIds: number[]) => 
    api.post(`/procurement/payments/batches/${id}/add-payments/`, { payment_ids: paymentIds }),
  
  removePayment: (id: number, paymentId: number) => 
    api.post(`/procurement/payments/batches/${id}/remove-payment/`, { payment_id: paymentId }),
  
  finalize: (id: number) => 
    api.post(`/procurement/payments/batches/${id}/finalize/`, {}),
  
  process: (id: number) => 
    api.post(`/procurement/payments/batches/${id}/process/`, {}),
  
  generateBatchFile: (id: number) => 
    api.post(`/procurement/payments/batches/${id}/generate-file/`, {}, { responseType: 'blob' }),
  
  export: (id: number, format: 'csv' | 'xlsx') => 
    api.get(`/procurement/payments/batches/${id}/export/`, { 
      params: { format }, 
      responseType: 'blob' 
    }),
};

export const paymentApprovalsAPI = {
  list: (params?: {
    status?: string;
    approver?: number;
    payment_request?: number;
  }) => api.get<PaymentApproval[]>('/procurement/payments/approvals/', { params }),
  
  get: (id: number) => api.get<PaymentApproval>(`/procurement/payments/approvals/${id}/`),
  
  create: (data: Partial<PaymentApproval>) => 
    api.post<PaymentApproval>('/procurement/payments/approvals/', data),
  
  approve: (id: number, data?: { comments?: string }) => 
    api.post(`/procurement/payments/approvals/${id}/approve/`, data),
  
  reject: (id: number, data: { comments: string }) => 
    api.post(`/procurement/payments/approvals/${id}/reject/`, data),

  // Get pending approvals for current user
  myPending: () => 
    api.get<PaymentApproval[]>('/procurement/payments/approvals/my-pending/'),
};

export const bankReconciliationAPI = {
  list: (params?: {
    status?: string;
    bank_account?: number;
    date_from?: string;
    date_to?: string;
  }) => api.get<BankReconciliation[]>('/procurement/payments/reconciliations/', { params }),
  
  get: (id: number) => api.get<BankReconciliation>(`/procurement/payments/reconciliations/${id}/`),
  
  create: (data: Partial<BankReconciliation>) => 
    api.post<BankReconciliation>('/procurement/payments/reconciliations/', data),
  
  update: (id: number, data: Partial<BankReconciliation>) => 
    api.patch<BankReconciliation>(`/procurement/payments/reconciliations/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/payments/reconciliations/${id}/`),

  // Custom Actions
  matchTransaction: (id: number, itemId: number, paymentId: number) => 
    api.post(`/procurement/payments/reconciliations/${id}/match-transaction/`, { 
      item_id: itemId, 
      payment_id: paymentId 
    }),
  
  unmatchTransaction: (id: number, itemId: number) => 
    api.post(`/procurement/payments/reconciliations/${id}/unmatch-transaction/`, { item_id: itemId }),
  
  complete: (id: number) => 
    api.post(`/procurement/payments/reconciliations/${id}/complete/`, {}),
  
  import: (id: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/procurement/payments/reconciliations/${id}/import/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};

export const paymentMethodsAPI = {
  list: () => api.get<PaymentMethod[]>('/procurement/payments/methods/'),
  get: (id: number) => api.get<PaymentMethod>(`/procurement/payments/methods/${id}/`),
  create: (data: Partial<PaymentMethod>) => api.post<PaymentMethod>('/procurement/payments/methods/', data),
  update: (id: number, data: Partial<PaymentMethod>) => 
    api.patch<PaymentMethod>(`/procurement/payments/methods/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/payments/methods/${id}/`),
};

export const paymentTermsAPI = {
  list: () => api.get<PaymentTerm[]>('/procurement/payments/terms/'),
  get: (id: number) => api.get<PaymentTerm>(`/procurement/payments/terms/${id}/`),
  create: (data: Partial<PaymentTerm>) => api.post<PaymentTerm>('/procurement/payments/terms/', data),
  update: (id: number, data: Partial<PaymentTerm>) => 
    api.patch<PaymentTerm>(`/procurement/payments/terms/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/payments/terms/${id}/`),
};

export const procurementBankAccountsAPI = {
  list: () => api.get<BankAccount[]>('/procurement/payments/bank-accounts/'),
  get: (id: number) => api.get<BankAccount>(`/procurement/payments/bank-accounts/${id}/`),
  create: (data: Partial<BankAccount>) => api.post<BankAccount>('/procurement/payments/bank-accounts/', data),
  update: (id: number, data: Partial<BankAccount>) => 
    api.patch<BankAccount>(`/procurement/payments/bank-accounts/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/payments/bank-accounts/${id}/`),
};

// ============================================================================
// CONTRACT MANAGEMENT API
// ============================================================================

export const contractsAPI = {
  list: (params?: {
    status?: string;
    contract_type?: string;
    party_type?: string;
    party_id?: number;
    expiring_within_days?: number;
  }) => api.get<Contract[]>('/procurement/contracts/contracts/', { params }),
  
  get: (id: number) => api.get<Contract>(`/procurement/contracts/contracts/${id}/`),
  
  create: (data: Partial<Contract>) => 
    api.post<Contract>('/procurement/contracts/contracts/', data),
  
  update: (id: number, data: Partial<Contract>) => 
    api.patch<Contract>(`/procurement/contracts/contracts/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/contracts/contracts/${id}/`),

  // Custom Actions
  submit: (id: number) => 
    api.post(`/procurement/contracts/contracts/${id}/submit/`, {}),
  
  approve: (id: number, data?: { comments?: string }) => 
    api.post(`/procurement/contracts/contracts/${id}/approve/`, data),
  
  reject: (id: number, data: { reason: string }) => 
    api.post(`/procurement/contracts/contracts/${id}/reject/`, data),
  
  activate: (id: number) => 
    api.post(`/procurement/contracts/contracts/${id}/activate/`, {}),
  
  suspend: (id: number, data: { reason: string }) => 
    api.post(`/procurement/contracts/contracts/${id}/suspend/`, data),
  
  terminate: (id: number, data: { reason: string; effective_date: string }) => 
    api.post(`/procurement/contracts/contracts/${id}/terminate/`, data),
  
  renew: (id: number, data: { new_end_date: string; new_value?: string }) => 
    api.post(`/procurement/contracts/contracts/${id}/renew/`, data),
  
  // Milestones
  addMilestone: (id: number, data: Partial<ContractMilestone>) => 
    api.post<ContractMilestone>(`/procurement/contracts/contracts/${id}/milestones/`, data),
  
  updateMilestone: (id: number, milestoneId: number, data: Partial<ContractMilestone>) => 
    api.patch<ContractMilestone>(`/procurement/contracts/contracts/${id}/milestones/${milestoneId}/`, data),
  
  completeMilestone: (id: number, milestoneId: number, data?: { completion_notes?: string }) => 
    api.post(`/procurement/contracts/contracts/${id}/milestones/${milestoneId}/complete/`, data),
  
  generateInvoice: (id: number, milestoneId: number) => 
    api.post(`/procurement/contracts/contracts/${id}/milestones/${milestoneId}/generate-invoice/`, {}),
  
  // Amendments
  addAmendment: (id: number, data: Partial<ContractAmendment>) => 
    api.post<ContractAmendment>(`/procurement/contracts/contracts/${id}/amendments/`, data),
  
  approveAmendment: (id: number, amendmentId: number) => 
    api.post(`/procurement/contracts/contracts/${id}/amendments/${amendmentId}/approve/`, {}),
  
  // Attachments
  uploadAttachment: (id: number, formData: FormData) => 
    api.post<ContractAttachment>(`/procurement/contracts/${id}/attachments/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  
  deleteAttachment: (id: number, attachmentId: number) => 
    api.delete(`/procurement/contracts/${id}/attachments/${attachmentId}/`),
  
  // Export
  exportPDF: (id: number) => 
    api.get(`/procurement/contracts/${id}/export-pdf/`, { responseType: 'blob' }),
};

export const contractTemplatesAPI = {
  list: () => api.get<ContractTemplate[]>('/procurement/contracts/templates/'),
  get: (id: number) => api.get<ContractTemplate>(`/procurement/contracts/templates/${id}/`),
  create: (data: Partial<ContractTemplate>) => 
    api.post<ContractTemplate>('/procurement/contracts/templates/', data),
  update: (id: number, data: Partial<ContractTemplate>) => 
    api.patch<ContractTemplate>(`/procurement/contracts/templates/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/contracts/templates/${id}/`),
  
  useTemplate: (id: number, data: { party_type: string; party_id: number; start_date: string; end_date: string }) => 
    api.post<Contract>(`/procurement/contracts/templates/${id}/use-template/`, data),
};

// ============================================================================
// PROCUREMENT REPORTS API
// ============================================================================

export const procurementReportsAPI = {
  // Dashboard KPIs - Use the actual endpoint that exists
  dashboard: (params?: {
    period_start?: string;
    period_end?: string;
  }) => api.get('/procurement/reports/dashboard/', { params }),
  
  // Purchase Analytics (using spend-analysis endpoint)
  purchaseAnalytics: (params: {
    period_start: string;
    period_end: string;
    supplier_id?: number;
    category?: string;
  }) => api.get<PurchaseAnalytics>('/procurement/reports/spend-analysis/', { params }),
  
  // Supplier Performance (using dashboard for now)
  supplierPerformance: (params?: {
    supplier_id?: number;
    date_from?: string;
    date_to?: string;
    min_score?: number;
  }) => api.get<SupplierPerformance[]>('/procurement/reports/dashboard/', { params }),
  
  // Contract Expiry (placeholder - no backend endpoint yet)
  contractExpiry: (params?: {
    days?: number;
    contract_type?: string;
    party_type?: string;
  }) => api.get<ContractExpiry[]>('/procurement/contracts/contracts/', { params }),
  
  // Payment Schedule (placeholder - no backend endpoint yet)
  paymentSchedule: (params?: {
    date_from?: string;
    date_to?: string;
    supplier_id?: number;
    status?: string;
  }) => api.get<PaymentSchedule[]>('/procurement/vendor-bills/bills/', { params }),
  
  // Vendor Spend Analysis
  vendorSpend: (params: {
    period_start: string;
    period_end: string;
    supplier_id?: number;
    category?: string;
  }) => api.get<VendorSpend[]>('/procurement/reports/spend-analysis/', { params }),
  
  // Procurement Compliance (placeholder)
  procurementCompliance: (params: {
    period_start: string;
    period_end: string;
  }) => api.get<ProcurementCompliance>('/procurement/reports/dashboard/', { params }),
  
  // Cash Flow Forecast (placeholder)
  cashFlowForecast: (params: {
    forecast_days: number;
    include_receivables?: boolean;
  }) => api.get<CashFlowForecast>('/procurement/reports/dashboard/', { params }),
  
  // Export Reports
  exportPurchaseAnalytics: (params: {
    period_start: string;
    period_end: string;
    format: 'csv' | 'xlsx' | 'pdf';
  }) => api.get('/procurement/reports/vendor-bills/export/', { 
    params, 
    responseType: 'blob' 
  }),
  
  exportSupplierPerformance: (format: 'csv' | 'xlsx' | 'pdf') => 
    api.get('/procurement/reports/vendor-bills/export/', { 
      params: { format }, 
      responseType: 'blob' 
    }),
};

// ============================================================================
// PURCHASE REQUISITION API (if enabled)
// ============================================================================

export const purchaseRequisitionsAPI = {
  list: (params?: {
    status?: string;
    requester?: number;
    date_from?: string;
    date_to?: string;
  }) => api.get<PurchaseRequisition[]>('/procurement/requisitions/pr-headers/', { params }),
  
  get: (id: number) => api.get<PurchaseRequisition>(`/procurement/requisitions/pr-headers/${id}/`),
  
  create: (data: Partial<PurchaseRequisition>) => 
    api.post<PurchaseRequisition>('/procurement/requisitions/pr-headers/', data),
  
  update: (id: number, data: Partial<PurchaseRequisition>) => 
    api.patch<PurchaseRequisition>(`/procurement/requisitions/pr-headers/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/requisitions/pr-headers/${id}/`),

  // Custom Actions
  submit: (id: number) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/submit/`, {}),
  
  approve: (id: number, data?: { comments?: string }) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/approve/`, data),
  
  reject: (id: number, data: { reason: string }) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/reject/`, data),
  
  convertToPO: (id: number, data?: { supplier_id?: number }) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/convert_to_po/`, data),
};

// ============================================================================
// GOODS RECEIPT API
// ============================================================================

export const goodsReceiptsAPI = {
  list: (params?: {
    status?: string;
    supplier?: number;
    date_from?: string;
    date_to?: string;
  }) => api.get<GoodsReceipt[]>('/procurement/receiving/receipts/', { params }),
  
  get: (id: number) => api.get<GoodsReceipt>(`/procurement/receiving/receipts/${id}/`),
  
  create: (data: Partial<GoodsReceipt>) => 
    api.post<GoodsReceipt>('/procurement/receiving/receipts/', data),
  
  update: (id: number, data: Partial<GoodsReceipt>) => 
    api.patch<GoodsReceipt>(`/procurement/receiving/receipts/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/receiving/receipts/${id}/`),

  // Custom Actions
  postReceipt: (id: number) => 
    api.post(`/procurement/receiving/receipts/${id}/post-receipt/`, {}),
  
  inspect: (id: number, data: { 
    inspector_id: number;
    inspection_notes?: string;
    line_statuses: { line_id: number; quality_status: string; rejection_reason?: string }[];
  }) => 
    api.post(`/procurement/receiving/receipts/${id}/inspect/`, data),
  
  accept: (id: number) => 
    api.post(`/procurement/receiving/receipts/${id}/accept/`, {}),
  
  reject: (id: number, data: { reason: string }) => 
    api.post(`/procurement/receiving/receipts/${id}/reject/`, data),
  
  returnToVendor: (id: number, data: { 
    return_reason: string;
    return_quantity: string;
    line_ids: number[];
  }) => 
    api.post(`/procurement/receiving/receipts/${id}/return-to-vendor/`, data),
};

// ============================================================================
// VENDOR BILLS - MISSING APIs (3-Way Match, Exceptions, Tolerances)
// ============================================================================

export const threeWayMatchesAPI = {
  list: (params?: {
    bill_id?: number;
    status?: string;
  }) => api.get('/procurement/vendor-bills/matches/', { params }),
  
  get: (id: number) => api.get(`/procurement/vendor-bills/matches/${id}/`),
  
  resolve: (id: number, data: { resolution_notes: string; resolved_by: number }) => 
    api.post(`/procurement/vendor-bills/matches/${id}/resolve/`, data),
};

export const matchExceptionsAPI = {
  list: (params?: {
    match_id?: number;
    exception_type?: string;
    status?: string;
  }) => api.get('/procurement/vendor-bills/exceptions/', { params }),
  
  get: (id: number) => api.get(`/procurement/vendor-bills/exceptions/${id}/`),
  
  create: (data: any) => api.post('/procurement/vendor-bills/exceptions/', data),
  
  update: (id: number, data: any) => 
    api.patch(`/procurement/vendor-bills/exceptions/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/vendor-bills/exceptions/${id}/`),
  
  resolve: (id: number, data: { resolution_notes: string }) => 
    api.post(`/procurement/vendor-bills/exceptions/${id}/resolve/`, data),
};

export const matchTolerancesAPI = {
  list: () => api.get('/procurement/vendor-bills/tolerances/'),
  
  get: (id: number) => api.get(`/procurement/vendor-bills/tolerances/${id}/`),
  
  create: (data: any) => api.post('/procurement/vendor-bills/tolerances/', data),
  
  update: (id: number, data: any) => 
    api.patch(`/procurement/vendor-bills/tolerances/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/vendor-bills/tolerances/${id}/`),
};

// ============================================================================
// PAYMENTS - MISSING APIs (Tax, Corporate Tax Accruals)
// ============================================================================

export const taxJurisdictionsAPI = {
  list: () => api.get('/procurement/payments/jurisdictions/'),
  get: (id: number) => api.get(`/procurement/payments/jurisdictions/${id}/`),
  create: (data: any) => api.post('/procurement/payments/jurisdictions/', data),
  update: (id: number, data: any) => api.patch(`/procurement/payments/jurisdictions/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/payments/jurisdictions/${id}/`),
};

export const taxRatesAPI = {
  list: (params?: { jurisdiction?: number }) => 
    api.get('/procurement/payments/rates/', { params }),
  get: (id: number) => api.get(`/procurement/payments/rates/${id}/`),
  create: (data: any) => api.post('/procurement/payments/rates/', data),
  update: (id: number, data: any) => api.patch(`/procurement/payments/rates/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/payments/rates/${id}/`),
};

export const taxComponentsAPI = {
  list: () => api.get('/procurement/payments/components/'),
  get: (id: number) => api.get(`/procurement/payments/components/${id}/`),
  create: (data: any) => api.post('/procurement/payments/components/', data),
  update: (id: number, data: any) => api.patch(`/procurement/payments/components/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/payments/components/${id}/`),
};

export const taxPeriodsAPI = {
  list: (params?: { jurisdiction?: number; year?: number }) => 
    api.get('/procurement/payments/tax-periods/', { params }),
  get: (id: number) => api.get(`/procurement/payments/tax-periods/${id}/`),
  create: (data: any) => api.post('/procurement/payments/tax-periods/', data),
  update: (id: number, data: any) => api.patch(`/procurement/payments/tax-periods/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/payments/tax-periods/${id}/`),
  
  calculateTax: (id: number) => 
    api.post(`/procurement/payments/tax-periods/${id}/calculate_tax/`, {}),
  
  closePeriod: (id: number) => 
    api.post(`/procurement/payments/tax-periods/${id}/close_period/`, {}),
  
  fileReturn: (id: number, data: { filed_date: string; filing_reference?: string }) => 
    api.post(`/procurement/payments/tax-periods/${id}/file_return/`, data),
  
  recordPayment: (id: number, data: { payment_date: string; amount: string; reference?: string }) => 
    api.post(`/procurement/payments/tax-periods/${id}/record_payment/`, data),
};

export const corporateTaxAccrualsAPI = {
  list: (params?: { period_start?: string; period_end?: string }) => 
    api.get('/procurement/payments/tax-accruals/', { params }),
  get: (id: number) => api.get(`/procurement/payments/tax-accruals/${id}/`),
  create: (data: any) => api.post('/procurement/payments/tax-accruals/', data),
  update: (id: number, data: any) => api.patch(`/procurement/payments/tax-accruals/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/payments/tax-accruals/${id}/`),
  
  postAccrual: (id: number) => 
    api.post(`/procurement/payments/tax-accruals/${id}/post_accrual/`, {}),
};

// Enhanced payment batches with missing actions
export const enhancedPaymentBatchesAPI = {
  ...paymentBatchesAPI,
  
  submit: (id: number) => 
    api.post(`/procurement/payments/batches/${id}/submit/`, {}),
  
  approve: (id: number, data?: { comments?: string }) => 
    api.post(`/procurement/payments/batches/${id}/approve/`, data),
  
  reject: (id: number, data: { reason: string }) => 
    api.post(`/procurement/payments/batches/${id}/reject/`, data),
  
  postToFinance: (id: number) => 
    api.post(`/procurement/payments/batches/${id}/post_to_finance/`, {}),
  
  reconcile: (id: number, data: { reconciliation_date: string; reference?: string }) => 
    api.post(`/procurement/payments/batches/${id}/reconcile/`, data),
  
  getSummary: (id: number) => 
    api.get(`/procurement/payments/batches/${id}/summary/`),
};

// ============================================================================
// CONTRACTS - MISSING APIs (SLAs, Penalties, Renewals, Notes)
// ============================================================================

export const clauseLibraryAPI = {
  list: (params?: { category?: string; language?: string }) => 
    api.get('/procurement/contracts/clauses/', { params }),
  get: (id: number) => api.get(`/procurement/contracts/clauses/${id}/`),
  create: (data: any) => api.post('/procurement/contracts/clauses/', data),
  update: (id: number, data: any) => api.patch(`/procurement/contracts/clauses/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/contracts/clauses/${id}/`),
};

export const contractSLAsAPI = {
  list: (params?: { contract?: number }) => 
    api.get('/procurement/contracts/slas/', { params }),
  get: (id: number) => api.get(`/procurement/contracts/slas/${id}/`),
  create: (data: any) => api.post('/procurement/contracts/slas/', data),
  update: (id: number, data: any) => api.patch(`/procurement/contracts/slas/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/contracts/slas/${id}/`),
  
  recordMeasurement: (id: number, data: { measurement_date: string; value: string; notes?: string }) => 
    api.post(`/procurement/contracts/slas/${id}/record_measurement/`, data),
};

export const contractPenaltiesAPI = {
  list: (params?: { contract?: number; status?: string }) => 
    api.get('/procurement/contracts/penalties/', { params }),
  get: (id: number) => api.get(`/procurement/contracts/penalties/${id}/`),
  create: (data: any) => api.post('/procurement/contracts/penalties/', data),
  update: (id: number, data: any) => api.patch(`/procurement/contracts/penalties/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/contracts/penalties/${id}/`),
  
  applyPenalty: (id: number, data: { applied_date: string; invoice_id?: number }) => 
    api.post(`/procurement/contracts/penalties/${id}/apply_penalty/`, data),
};

export const contractRenewalsAPI = {
  list: (params?: { contract?: number; status?: string }) => 
    api.get('/procurement/contracts/renewals/', { params }),
  get: (id: number) => api.get(`/procurement/contracts/renewals/${id}/`),
  create: (data: any) => api.post('/procurement/contracts/renewals/', data),
  update: (id: number, data: any) => api.patch(`/procurement/contracts/renewals/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/contracts/renewals/${id}/`),
};

export const contractAttachmentsAPI = {
  list: (params?: { contract?: number }) => 
    api.get('/procurement/contracts/attachments/', { params }),
  get: (id: number) => api.get(`/procurement/contracts/attachments/${id}/`),
  delete: (id: number) => api.delete(`/procurement/contracts/attachments/${id}/`),
};

export const contractNotesAPI = {
  list: (params?: { contract?: number }) => 
    api.get('/procurement/contracts/notes/', { params }),
  get: (id: number) => api.get(`/procurement/contracts/notes/${id}/`),
  create: (data: any) => api.post('/procurement/contracts/notes/', data),
  update: (id: number, data: any) => api.patch(`/procurement/contracts/notes/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/contracts/notes/${id}/`),
};

// Enhanced contracts API with missing actions
export const enhancedContractsAPI = {
  ...contractsAPI,
  
  sendRenewalReminder: (id: number) => 
    api.post(`/procurement/contracts/${id}/send_renewal_reminder/`, {}),
  
  updateStatus: (id: number, data: { status: string; notes?: string }) => 
    api.post(`/procurement/contracts/${id}/update_status/`, data),
  
  getSummary: (id: number) => 
    api.get(`/procurement/contracts/${id}/summary/`),
};

// ============================================================================
// RFx/SOURCING - MISSING APIs (Complete Implementation)
// ============================================================================

export const rfxEventsAPI = {
  list: (params?: { 
    event_type?: string; 
    status?: string;
    date_from?: string;
    date_to?: string;
  }) => api.get('/procurement/rfx/rfx-events/', { params }),
  
  get: (id: number) => api.get(`/procurement/rfx/rfx-events/${id}/`),
  
  create: (data: any) => api.post('/procurement/rfx/rfx-events/', data),
  
  update: (id: number, data: any) => api.patch(`/procurement/rfx/rfx-events/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/rfx/rfx-events/${id}/`),
  
  publish: (id: number) => 
    api.post(`/procurement/rfx/rfx-events/${id}/publish/`, {}),
  
  close: (id: number) => 
    api.post(`/procurement/rfx/rfx-events/${id}/close/`, {}),
  
  inviteSuppliers: (id: number, data: { supplier_ids: number[] }) => 
    api.post(`/procurement/rfx/rfx-events/${id}/invite_suppliers/`, data),
  
  quoteComparison: (id: number) => 
    api.get(`/procurement/rfx/rfx-events/${id}/quote_comparison/`),
  
  createAward: (id: number, data: { 
    winning_quote_ids: number[];
    award_type: 'single' | 'split';
    notes?: string;
  }) => api.post(`/procurement/rfx/rfx-events/${id}/create_award/`, data),
  
  statistics: () => 
    api.get('/procurement/rfx/rfx-events/statistics/'),
};

export const rfxItemsAPI = {
  list: (params?: { event?: number }) => 
    api.get('/procurement/rfx/rfx-items/', { params }),
  get: (id: number) => api.get(`/procurement/rfx/rfx-items/${id}/`),
  create: (data: any) => api.post('/procurement/rfx/rfx-items/', data),
  update: (id: number, data: any) => api.patch(`/procurement/rfx/rfx-items/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/rfx/rfx-items/${id}/`),
};

export const supplierInvitationsAPI = {
  list: (params?: { event?: number; supplier?: number }) => 
    api.get('/procurement/rfx/supplier-invitations/', { params }),
  get: (id: number) => api.get(`/procurement/rfx/supplier-invitations/${id}/`),
  create: (data: any) => api.post('/procurement/rfx/supplier-invitations/', data),
  update: (id: number, data: any) => api.patch(`/procurement/rfx/supplier-invitations/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/rfx/supplier-invitations/${id}/`),
};

export const supplierQuotesAPI = {
  list: (params?: { event?: number; supplier?: number; status?: string }) => 
    api.get('/procurement/rfx/supplier-quotes/', { params }),
  get: (id: number) => api.get(`/procurement/rfx/supplier-quotes/${id}/`),
  create: (data: any) => api.post('/procurement/rfx/supplier-quotes/', data),
  update: (id: number, data: any) => api.patch(`/procurement/rfx/supplier-quotes/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/rfx/supplier-quotes/${id}/`),
  
  submit: (id: number) => 
    api.post(`/procurement/rfx/supplier-quotes/${id}/submit/`, {}),
  
  calculateTotals: (id: number) => 
    api.post(`/procurement/rfx/supplier-quotes/${id}/calculate_totals/`, {}),
  
  calculateScores: (id: number) => 
    api.post(`/procurement/rfx/supplier-quotes/${id}/calculate_scores/`, {}),
  
  setTechnicalScore: (id: number, data: { technical_score: number; evaluator_notes?: string }) => 
    api.post(`/procurement/rfx/supplier-quotes/${id}/set_technical_score/`, data),
};

export const rfxAwardsAPI = {
  list: (params?: { event?: number; status?: string }) => 
    api.get('/procurement/rfx/rfx-awards/', { params }),
  get: (id: number) => api.get(`/procurement/rfx/rfx-awards/${id}/`),
  create: (data: any) => api.post('/procurement/rfx/rfx-awards/', data),
  update: (id: number, data: any) => api.patch(`/procurement/rfx/rfx-awards/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/rfx/rfx-awards/${id}/`),
  
  approve: (id: number, data?: { approver_notes?: string }) => 
    api.post(`/procurement/rfx/rfx-awards/${id}/approve/`, data),
  
  createPO: (id: number) => 
    api.post(`/procurement/rfx/rfx-awards/${id}/create_po/`, {}),
};

export const auctionBidsAPI = {
  list: (params?: { event?: number; supplier?: number }) => 
    api.get('/procurement/rfx/auction-bids/', { params }),
  get: (id: number) => api.get(`/procurement/rfx/auction-bids/${id}/`),
  create: (data: any) => api.post('/procurement/rfx/auction-bids/', data),
  update: (id: number, data: any) => api.patch(`/procurement/rfx/auction-bids/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/rfx/auction-bids/${id}/`),
  
  submitBid: (data: { 
    event: number;
    supplier: number;
    bid_amount: string;
  }) => api.post('/procurement/rfx/auction-bids/submit_bid/', data),
};

// ============================================================================
// REQUISITIONS - MISSING APIs (Cost Centers, Projects, Complete PR Workflow)
// ============================================================================

export const costCentersAPI = {
  list: () => api.get('/procurement/requisitions/cost-centers/'),
  get: (id: number) => api.get(`/procurement/requisitions/cost-centers/${id}/`),
  create: (data: any) => api.post('/procurement/requisitions/cost-centers/', data),
  update: (id: number, data: any) => api.patch(`/procurement/requisitions/cost-centers/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/requisitions/cost-centers/${id}/`),
  
  budgetSummary: (id: number, params?: { fiscal_year?: number }) => 
    api.get(`/procurement/requisitions/cost-centers/${id}/budget_summary/`, { params }),
  
  utilization: (id: number, params?: { start_date?: string; end_date?: string }) => 
    api.get(`/procurement/requisitions/cost-centers/${id}/utilization/`, { params }),
};

export const projectsAPI = {
  list: (params?: { status?: string }) => 
    api.get('/procurement/requisitions/projects/', { params }),
  get: (id: number) => api.get(`/procurement/requisitions/projects/${id}/`),
  create: (data: any) => api.post('/procurement/requisitions/projects/', data),
  update: (id: number, data: any) => api.patch(`/procurement/requisitions/projects/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/requisitions/projects/${id}/`),
  
  active: () => 
    api.get('/procurement/requisitions/projects/active/'),
  
  utilization: (id: number) => 
    api.get(`/procurement/requisitions/projects/${id}/utilization/`),
};

export const prHeadersAPI = {
  list: (params?: { 
    status?: string;
    requester?: number;
    cost_center?: number;
    date_from?: string;
    date_to?: string;
  }) => api.get('/procurement/requisitions/pr-headers/', { params }),
  
  get: (id: number) => api.get(`/procurement/requisitions/pr-headers/${id}/`),
  
  create: (data: any) => api.post('/procurement/requisitions/pr-headers/', data),
  
  update: (id: number, data: any) => api.patch(`/procurement/requisitions/pr-headers/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/requisitions/pr-headers/${id}/`),
  
  submit: (id: number) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/submit/`, {}),
  
  approve: (id: number, data?: { approver_comments?: string }) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/approve/`, data),
  
  reject: (id: number, data: { rejection_reason: string }) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/reject/`, data),
  
  cancel: (id: number, data: { cancellation_reason: string }) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/cancel/`, data),
  
  checkBudget: (id: number) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/check_budget/`, {}),
  
  generateSuggestions: (id: number) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/generate_suggestions/`, {}),
  
  convertToPO: (id: number, data?: { supplier_id?: number }) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/convert_to_po/`, data),
  
  splitByVendor: (id: number) => 
    api.post(`/procurement/requisitions/pr-headers/${id}/split_by_vendor/`, {}),
  
  myPRs: (requestorId?: number) => 
    api.get('/procurement/requisitions/pr-headers/my_prs/', { 
      params: requestorId ? { requestor_id: requestorId } : {} 
    }),
  
  pendingApproval: () => 
    api.get('/procurement/requisitions/pr-headers/pending_approval/'),
  
  statistics: () => 
    api.get('/procurement/requisitions/pr-headers/statistics/'),
  
  // PR to PO Conversion APIs
  getConvertibleLines: (prHeaderIds?: number[]) => 
    api.get('/procurement/requisitions/pr-headers/convertible_lines/', { 
      params: prHeaderIds && prHeaderIds.length > 0 
        ? { pr_header_ids: prHeaderIds.join(',') } 
        : {} 
    }),
  
  convertLinesToPO: (data: {
    pr_line_selections: Array<{
      pr_line_id: number;
      quantity: number;
      unit_price: number;
      notes?: string;
    }>;
    title: string;
    vendor_name?: string;
    vendor_email?: string;
    vendor_phone?: string;
    delivery_date?: string | null;
    delivery_address?: string;
    special_instructions?: string;
    payment_terms?: string;
  }) => api.post('/procurement/requisitions/pr-headers/convert_lines_to_po/', data),
  
  getConversionSummary: (prHeaderId: number) => 
    api.get(`/procurement/requisitions/pr-headers/${prHeaderId}/conversion_summary/`),
  
  retrieve: (prHeaderId: number) => 
    api.get(`/procurement/requisitions/pr-headers/${prHeaderId}/`),
};

export const prLinesAPI = {
  list: (params?: { pr_header?: number }) => 
    api.get('/procurement/requisitions/pr-lines/', { params }),
  get: (id: number) => api.get(`/procurement/requisitions/pr-lines/${id}/`),
  create: (data: any) => api.post('/procurement/requisitions/pr-lines/', data),
  update: (id: number, data: any) => api.patch(`/procurement/requisitions/pr-lines/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/requisitions/pr-lines/${id}/`),
};

// ============================================================================
// RECEIVING - MISSING APIs (Warehouses, Quality, Non-Conformance, RTV)
// ============================================================================

export const warehousesAPI = {
  list: () => api.get('/procurement/receiving/warehouses/'),
  get: (id: number) => api.get(`/procurement/receiving/warehouses/${id}/`),
  create: (data: any) => api.post('/procurement/receiving/warehouses/', data),
  update: (id: number, data: any) => api.patch(`/procurement/receiving/warehouses/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/receiving/warehouses/${id}/`),
};

export const storageLocationsAPI = {
  list: (params?: { warehouse?: number }) => 
    api.get('/procurement/receiving/locations/', { params }),
  get: (id: number) => api.get(`/procurement/receiving/locations/${id}/`),
  create: (data: any) => api.post('/procurement/receiving/locations/', data),
  update: (id: number, data: any) => api.patch(`/procurement/receiving/locations/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/receiving/locations/${id}/`),
};

export const goodsReceiptsExtendedAPI = {
  ...goodsReceiptsAPI,
  
  post: (id: number) => 
    api.post(`/procurement/receiving/receipts/${id}/post/`, {}),
  
  cancel: (id: number, data: { cancellation_reason: string }) => 
    api.post(`/procurement/receiving/receipts/${id}/cancel/`, data),
};

export const grnLinesAPI = {
  list: (params?: { grn?: number }) => 
    api.get('/procurement/receiving/grn-lines/', { params }),
  get: (id: number) => api.get(`/procurement/receiving/grn-lines/${id}/`),
  create: (data: any) => api.post('/procurement/receiving/grn-lines/', data),
  update: (id: number, data: any) => api.patch(`/procurement/receiving/grn-lines/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/receiving/grn-lines/${id}/`),
};

export const qualityInspectionsAPI = {
  list: (params?: { grn?: number; status?: string }) => 
    api.get('/procurement/receiving/inspections/', { params }),
  get: (id: number) => api.get(`/procurement/receiving/inspections/${id}/`),
  create: (data: any) => api.post('/procurement/receiving/inspections/', data),
  update: (id: number, data: any) => api.patch(`/procurement/receiving/inspections/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/receiving/inspections/${id}/`),
  
  start: (id: number, data: { inspector_id: number; start_date: string }) => 
    api.post(`/procurement/receiving/inspections/${id}/start/`, data),
  
  complete: (id: number, data: { completion_date: string; inspection_notes?: string }) => 
    api.post(`/procurement/receiving/inspections/${id}/complete/`, data),
  
  approve: (id: number, data?: { approval_notes?: string }) => 
    api.post(`/procurement/receiving/inspections/${id}/approve/`, data),
  
  reject: (id: number, data: { rejection_reason: string }) => 
    api.post(`/procurement/receiving/inspections/${id}/reject/`, data),
};

export const nonConformancesAPI = {
  list: (params?: { inspection?: number; status?: string }) => 
    api.get('/procurement/receiving/non-conformances/', { params }),
  get: (id: number) => api.get(`/procurement/receiving/non-conformances/${id}/`),
  create: (data: any) => api.post('/procurement/receiving/non-conformances/', data),
  update: (id: number, data: any) => api.patch(`/procurement/receiving/non-conformances/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/receiving/non-conformances/${id}/`),
  
  resolve: (id: number, data: { resolution_notes: string; resolved_date: string }) => 
    api.post(`/procurement/receiving/non-conformances/${id}/resolve/`, data),
};

export const returnToVendorAPI = {
  list: (params?: { grn?: number; status?: string }) => 
    api.get('/procurement/receiving/returns/', { params }),
  get: (id: number) => api.get(`/procurement/receiving/returns/${id}/`),
  create: (data: any) => api.post('/procurement/receiving/returns/', data),
  update: (id: number, data: any) => api.patch(`/procurement/receiving/returns/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/receiving/returns/${id}/`),
  
  submit: (id: number) => 
    api.post(`/procurement/receiving/returns/${id}/submit/`, {}),
  
  approve: (id: number, data?: { approval_notes?: string }) => 
    api.post(`/procurement/receiving/returns/${id}/approve/`, data),
  
  ship: (id: number, data: { ship_date: string; tracking_number?: string }) => 
    api.post(`/procurement/receiving/returns/${id}/ship/`, data),
  
  complete: (id: number, data: { completion_date: string; credit_note_id?: number }) => 
    api.post(`/procurement/receiving/returns/${id}/complete/`, data),
};

export const rtvLinesAPI = {
  list: (params?: { rtv?: number }) => 
    api.get('/procurement/receiving/rtv-lines/', { params }),
  get: (id: number) => api.get(`/procurement/receiving/rtv-lines/${id}/`),
  create: (data: any) => api.post('/procurement/receiving/rtv-lines/', data),
  update: (id: number, data: any) => api.patch(`/procurement/receiving/rtv-lines/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/receiving/rtv-lines/${id}/`),
};

// ============================================================================
// CATALOG - MISSING APIs (UOM, Categories, Price Tiers, Framework Agreements, Call-offs)
// ============================================================================

export const unitsOfMeasureAPI = {
  list: () => api.get('/procurement/catalog/units-of-measure/'),
  get: (id: number) => api.get(`/procurement/catalog/units-of-measure/${id}/`),
  create: (data: any) => api.post('/procurement/catalog/units-of-measure/', data),
  update: (id: number, data: any) => api.patch(`/procurement/catalog/units-of-measure/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/catalog/units-of-measure/${id}/`),
};

export const categoriesAPI = {
  list: () => api.get('/procurement/catalog/categories/'),
  get: (id: number) => api.get(`/procurement/catalog/categories/${id}/`),
  create: (data: any) => api.post('/procurement/catalog/categories/', data),
  update: (id: number, data: any) => api.patch(`/procurement/catalog/categories/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/catalog/categories/${id}/`),
  
  tree: () => 
    api.get('/procurement/catalog/categories/tree/'),
};

export const catalogItemsAPI = {
  list: (params?: { 
    category?: number; 
    active?: boolean;
    search?: string;
  }) => api.get('/procurement/catalog/items/', { params }),
  
  get: (id: number) => api.get(`/procurement/catalog/items/${id}/`),
  
  create: (data: any) => api.post('/procurement/catalog/items/', data),
  
  update: (id: number, data: any) => api.patch(`/procurement/catalog/items/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/catalog/items/${id}/`),
  
  priceTiers: (id: number) => 
    api.get(`/procurement/catalog/items/${id}/price_tiers/`),
  
  getEffectivePrice: (id: number, data: { quantity: number; supplier_id?: number }) => 
    api.post(`/procurement/catalog/items/${id}/get_effective_price/`, data),
  
  searchCatalog: (params: { query: string; category?: number; supplier?: number }) => 
    api.get('/procurement/catalog/items/search_catalog/', { params }),
};

export const priceTiersAPI = {
  list: (params?: { item?: number }) => 
    api.get('/procurement/catalog/price-tiers/', { params }),
  get: (id: number) => api.get(`/procurement/catalog/price-tiers/${id}/`),
  create: (data: any) => api.post('/procurement/catalog/price-tiers/', data),
  update: (id: number, data: any) => api.patch(`/procurement/catalog/price-tiers/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/catalog/price-tiers/${id}/`),
};

export const frameworkAgreementsAPI = {
  list: (params?: { 
    supplier?: number; 
    status?: string;
    expiring_days?: number;
  }) => api.get('/procurement/catalog/framework-agreements/', { params }),
  
  get: (id: number) => api.get(`/procurement/catalog/framework-agreements/${id}/`),
  
  create: (data: any) => api.post('/procurement/catalog/framework-agreements/', data),
  
  update: (id: number, data: any) => api.patch(`/procurement/catalog/framework-agreements/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/catalog/framework-agreements/${id}/`),
  
  activate: (id: number, data: { activation_date: string }) => 
    api.post(`/procurement/catalog/framework-agreements/${id}/activate/`, data),
  
  suspend: (id: number, data: { suspension_reason: string }) => 
    api.post(`/procurement/catalog/framework-agreements/${id}/suspend/`, data),
  
  terminate: (id: number, data: { termination_date: string; termination_reason: string }) => 
    api.post(`/procurement/catalog/framework-agreements/${id}/terminate/`, data),
  
  renew: (id: number, data: { new_end_date: string; new_limit?: string }) => 
    api.post(`/procurement/catalog/framework-agreements/${id}/renew/`, data),
  
  utilization: (id: number) => 
    api.get(`/procurement/catalog/framework-agreements/${id}/utilization/`),
  
  activeFrameworks: () => 
    api.get('/procurement/catalog/framework-agreements/active_frameworks/'),
  
  expiringSoon: (params?: { days?: number }) => 
    api.get('/procurement/catalog/framework-agreements/expiring_soon/', { params }),
  
  statistics: () => 
    api.get('/procurement/catalog/framework-agreements/statistics/'),
};

export const frameworkItemsAPI = {
  list: (params?: { framework?: number }) => 
    api.get('/procurement/catalog/framework-items/', { params }),
  get: (id: number) => api.get(`/procurement/catalog/framework-items/${id}/`),
  create: (data: any) => api.post('/procurement/catalog/framework-items/', data),
  update: (id: number, data: any) => api.patch(`/procurement/catalog/framework-items/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/catalog/framework-items/${id}/`),
};

export const callOffOrdersAPI = {
  list: (params?: { 
    framework?: number; 
    status?: string;
    date_from?: string;
    date_to?: string;
  }) => api.get('/procurement/catalog/calloff-orders/', { params }),
  
  get: (id: number) => api.get(`/procurement/catalog/calloff-orders/${id}/`),
  
  create: (data: any) => api.post('/procurement/catalog/calloff-orders/', data),
  
  update: (id: number, data: any) => api.patch(`/procurement/catalog/calloff-orders/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/catalog/calloff-orders/${id}/`),
  
  submit: (id: number) => 
    api.post(`/procurement/catalog/calloff-orders/${id}/submit/`, {}),
  
  approve: (id: number, data?: { approval_notes?: string }) => 
    api.post(`/procurement/catalog/calloff-orders/${id}/approve/`, data),
  
  send: (id: number) => 
    api.post(`/procurement/catalog/calloff-orders/${id}/send/`, {}),
  
  confirm: (id: number, data: { confirmation_date: string; supplier_reference?: string }) => 
    api.post(`/procurement/catalog/calloff-orders/${id}/confirm/`, data),
  
  complete: (id: number) => 
    api.post(`/procurement/catalog/calloff-orders/${id}/complete/`, {}),
  
  cancel: (id: number, data: { cancellation_reason: string }) => 
    api.post(`/procurement/catalog/calloff-orders/${id}/cancel/`, data),
};

export const callOffLinesAPI = {
  list: (params?: { calloff_order?: number }) => 
    api.get('/procurement/catalog/calloff-lines/', { params }),
  get: (id: number) => api.get(`/procurement/catalog/calloff-lines/${id}/`),
  create: (data: any) => api.post('/procurement/catalog/calloff-lines/', data),
  update: (id: number, data: any) => api.patch(`/procurement/catalog/calloff-lines/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/catalog/calloff-lines/${id}/`),
  
  receive: (id: number, data: { received_quantity: string; receipt_date: string }) => 
    api.post(`/procurement/catalog/calloff-lines/${id}/receive/`, data),
};

// ============================================================================
// APPROVALS - COMPLETE NEW MODULE
// ============================================================================

export const approvalWorkflowsAPI = {
  list: (params?: { entity_type?: string; active?: boolean }) => 
    api.get('/procurement/approvals/workflows/', { params }),
  get: (id: number) => api.get(`/procurement/approvals/workflows/${id}/`),
  create: (data: any) => api.post('/procurement/approvals/workflows/', data),
  update: (id: number, data: any) => api.patch(`/procurement/approvals/workflows/${id}/`, data),
  delete: (id: number) => api.delete(`/procurement/approvals/workflows/${id}/`),
};

export const approvalInstancesAPI = {
  list: (params?: { 
    workflow?: number;
    status?: string;
    entity_type?: string;
    entity_id?: number;
  }) => api.get('/procurement/approvals/instances/', { params }),
  
  get: (id: number) => api.get(`/procurement/approvals/instances/${id}/`),
  
  create: (data: any) => api.post('/procurement/approvals/instances/', data),
  
  update: (id: number, data: any) => api.patch(`/procurement/approvals/instances/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/approvals/instances/${id}/`),
  
  myPending: () => 
    api.get('/procurement/approvals/instances/my_pending/'),
  
  cancel: (id: number, data: { cancellation_reason: string }) => 
    api.post(`/procurement/approvals/instances/${id}/cancel/`, data),
};

export const approvalStepsAPI = {
  list: (params?: { instance?: number }) => 
    api.get('/procurement/approvals/steps/', { params }),
  
  get: (id: number) => api.get(`/procurement/approvals/steps/${id}/`),
  
  create: (data: any) => api.post('/procurement/approvals/steps/', data),
  
  update: (id: number, data: any) => api.patch(`/procurement/approvals/steps/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/approvals/steps/${id}/`),
  
  approve: (id: number, data?: { comments?: string }) => 
    api.post(`/procurement/approvals/steps/${id}/approve/`, data),
  
  reject: (id: number, data: { comments: string }) => 
    api.post(`/procurement/approvals/steps/${id}/reject/`, data),
};

export const approvalDelegationsAPI = {
  list: (params?: { delegator?: number; delegate?: number; active?: boolean }) => 
    api.get('/procurement/approvals/delegations/', { params }),
  
  get: (id: number) => api.get(`/procurement/approvals/delegations/${id}/`),
  
  create: (data: any) => api.post('/procurement/approvals/delegations/', data),
  
  update: (id: number, data: any) => api.patch(`/procurement/approvals/delegations/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/approvals/delegations/${id}/`),
  
  myDelegations: () => 
    api.get('/procurement/approvals/delegations/my_delegations/'),
  
  activeNow: () => 
    api.get('/procurement/approvals/delegations/active_now/'),
};

export const budgetAllocationsAPI = {
  list: (params?: { 
    cost_center?: number;
    fiscal_year?: number;
    status?: string;
  }) => api.get('/procurement/approvals/budgets/', { params }),
  
  get: (id: number) => api.get(`/procurement/approvals/budgets/${id}/`),
  
  create: (data: any) => api.post('/procurement/approvals/budgets/', data),
  
  update: (id: number, data: any) => api.patch(`/procurement/approvals/budgets/${id}/`, data),
  
  delete: (id: number) => api.delete(`/procurement/approvals/budgets/${id}/`),
  
  checkAvailability: (id: number, data: { amount: string }) => 
    api.post(`/procurement/approvals/budgets/${id}/check_availability/`, data),
  
  overBudget: () => 
    api.get('/procurement/approvals/budgets/over_budget/'),
  
  atWarning: () => 
    api.get('/procurement/approvals/budgets/at_warning/'),
};

export const budgetChecksAPI = {
  list: (params?: { 
    pr_header?: number;
    passed?: boolean;
  }) => api.get('/procurement/approvals/budget-checks/', { params }),
  
  get: (id: number) => api.get(`/procurement/approvals/budget-checks/${id}/`),
};

// ============================================================================
// REPORTS - MISSING APIs (Enhanced Analytics)
// ============================================================================

export const enhancedProcurementReportsAPI = {
  ...procurementReportsAPI,
  
  poCycleTime: (params: { start_date: string; end_date: string }) => 
    api.get('/procurement/reports/po-cycle-time/', { params }),
  
  onTimeDelivery: (params: { start_date: string; end_date: string; supplier_id?: number }) => 
    api.get('/procurement/reports/on-time-delivery/', { params }),
  
  priceVariance: (params: { start_date: string; end_date: string }) => 
    api.get('/procurement/reports/price-variance/', { params }),
  
  spendAnalysis: (params: { 
    group_by: 'supplier' | 'category' | 'month';
    start_date: string;
    end_date: string;
  }) => api.get('/procurement/reports/spend-analysis/', { params }),
  
  exceptions: (params?: { start_date?: string; end_date?: string }) => 
    api.get('/procurement/reports/exceptions/', { params }),
  
  dashboard: () => 
    api.get('/procurement/reports/dashboard/'),
  
  // Export functions
  exportVendorBills: (params: { 
    format: 'csv' | 'xlsx';
    start_date?: string;
    end_date?: string;
  }) => api.get('/procurement/reports/vendor-bills/export/', { 
    params, 
    responseType: 'blob' 
  }),
  
  exportPurchaseRequisitions: (params: { 
    format: 'csv' | 'xlsx';
    start_date?: string;
    end_date?: string;
  }) => api.get('/procurement/reports/purchase-requisitions/export/', { 
    params, 
    responseType: 'blob' 
  }),
  
  exportGRNs: (params: { 
    format: 'csv' | 'xlsx';
    start_date?: string;
    end_date?: string;
  }) => api.get('/procurement/reports/grns/export/', { 
    params, 
    responseType: 'blob' 
  }),
};





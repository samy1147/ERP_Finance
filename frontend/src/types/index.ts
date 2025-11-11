// Account Types (now using segment structure)
export interface Account {
  id: number;
  code: string;
  name: string;
  alias?: string;
  type: string; // segment type (e.g., 'account')
  parent_code?: string | null;
  is_active: boolean;
  level: number; // 0 = root, 1 = first level child, etc.
  hierarchy_level?: number;
  full_path?: string;
  envelope_amount?: string | null;
  segment_type?: number;
  children?: Account[];
  created_at?: string;
  updated_at?: string;
}

// Currency
export interface Currency {
  id: number;
  code: string;
  name: string;
  symbol: string;
  is_base: boolean;
}

// Journal Entry
export interface JournalEntry {
  id: number;
  date: string;
  currency: number;
  memo: string;
  posted: boolean;
  lines: JournalLine[];
}

export interface JournalLineSegment {
  id?: number;
  segment_type: number;
  segment_type_name?: string;
  segment: number;
  segment_code?: string;
  segment_alias?: string;
}

export interface JournalLine {
  id?: number;
  account: number;
  account_code?: string;
  account_name?: string;
  debit: string;
  credit: string;
  segments?: JournalLineSegment[];
}

// GL Distribution Line
export interface GLDistributionLine {
  id?: number;
  account: number;
  line_type: 'DEBIT' | 'CREDIT';
  amount: string;
  description?: string;
  segments?: JournalLineSegment[];
}

// Customer (AR)
export interface Customer {
  id: number;
  code?: string;
  name: string;
  email?: string;
  country?: string;
  currency?: number;
  currency_name?: string;
  vat_number?: string;
  is_active: boolean;
}

// AR Invoice
export interface ARInvoice {
  id: number;
  customer: number;
  customer_name?: string;
  invoice_number: string;
  date: string;
  due_date: string;
  currency: number;
  currency_code?: string;
  country: string; // Tax country for the invoice
  // New separated status fields
  is_posted: boolean;
  payment_status: 'UNPAID' | 'PARTIALLY_PAID' | 'PAID';
  is_cancelled: boolean;
  approval_status?: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED';
  posted_at?: string;
  paid_at?: string;
  cancelled_at?: string;
  items: ARInvoiceItem[];
  subtotal?: string;
  tax_amount?: string;
  total?: string;
  paid_amount?: string;
  balance?: string;
  // Nested details from serializer
  customer_details?: { id: number; name: string };
  currency_details?: { id: number; code: string; name: string; symbol: string };
  base_currency_total?: string;
  exchange_rate?: string;
  gl_lines?: GLDistributionLine[];
}

export interface ARInvoiceItem {
  id?: number;
  description: string;
  quantity: string;
  unit_price: string;
  amount?: string;
  tax_rate?: number;
  tax_amount?: string;
  account?: number;
}

// AR Payment Allocation
export interface ARPaymentAllocation {
  id?: number;
  invoice: number;
  invoice_number?: string;
  invoice_total?: string;
  invoice_outstanding?: string;
  amount: string;
  memo?: string;
  invoice_currency?: number;
  invoice_currency_code?: string;
  current_exchange_rate?: string;
}

// AR Payment (NEW with allocations)
export interface ARPayment {
  id?: number;
  customer: number;
  customer_name?: string;
  reference: string;
  date: string;
  total_amount: string;
  currency: number;
  currency_code?: string;
  memo?: string;
  bank_account?: number;
  posted_at?: string;
  reconciled?: boolean;
  reconciliation_ref?: string;
  reconciled_at?: string;
  allocations?: ARPaymentAllocation[];
  allocated_amount?: string;
  unallocated_amount?: string;
  invoice_currency?: number;
  invoice_currency_code?: string;
  exchange_rate?: string;
  payment_currency_code?: string;
}

// Supplier (AP)
export interface Supplier {
  id: number;
  code?: string;
  name: string;
  email?: string;
  country?: string;
  currency?: number;
  currency_name?: string;
  vat_number?: string;
  is_active: boolean;
}

// AP Invoice
export interface APInvoice {
  id: number;
  supplier: number;
  supplier_name?: string;
  invoice_number: string;
  date: string;
  due_date: string;
  currency: number;
  currency_code?: string;
  country: string; // Tax country for the invoice
  // New separated status fields
  is_posted: boolean;
  payment_status: 'UNPAID' | 'PARTIALLY_PAID' | 'PAID';
  is_cancelled: boolean;
  approval_status?: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED';
  posted_at?: string;
  paid_at?: string;
  cancelled_at?: string;
  items: APInvoiceItem[];
  subtotal?: string;
  tax_amount?: string;
  total?: string;
  paid_amount?: string;
  balance?: string;
  // Nested details from serializer
  supplier_details?: { id: number; name: string };
  currency_details?: { id: number; code: string; name: string; symbol: string };
  base_currency_total?: string;
  exchange_rate?: string;
  gl_lines?: GLDistributionLine[];
}

export interface APInvoiceItem {
  id?: number;
  description: string;
  quantity: string;
  unit_price: string;
  amount?: string;
  tax_rate?: number;
  tax_amount?: string;
  account?: number;
}

// AP Payment Allocation
export interface APPaymentAllocation {
  id?: number;
  invoice: number;
  invoice_number?: string;
  invoice_total?: string;
  invoice_outstanding?: string;
  amount: string;
  memo?: string;
  invoice_currency?: number;
  invoice_currency_code?: string;
  current_exchange_rate?: string;
}

// AP Payment (NEW with allocations)
export interface APPayment {
  id?: number;
  supplier: number;
  supplier_name?: string;
  reference: string;
  date: string;
  total_amount: string;
  currency: number;
  currency_code?: string;
  memo?: string;
  bank_account?: number;
  posted_at?: string;
  reconciled?: boolean;
  reconciliation_ref?: string;
  reconciled_at?: string;
  allocations?: APPaymentAllocation[];
  allocated_amount?: string;
  unallocated_amount?: string;
  invoice_currency?: number;
  invoice_currency_code?: string;
  exchange_rate?: string;
  payment_currency_code?: string;
}

// Bank Account
export interface BankAccount {
  id: number;
  name: string;
  account_code: string;
  iban?: string;
  swift?: string;
  currency?: number;
  active: boolean;
}

// Tax Rate
export interface TaxRate {
  id: number;
  name: string;
  rate: number;
  country: string;
  category: 'STANDARD' | 'ZERO' | 'EXEMPT' | 'RC';
  code?: string;
  effective_from?: string;
  effective_to?: string;
  is_active: boolean;
}

// Reports
export interface TrialBalanceRow {
  code: string;
  name: string;
  debit: number;
  credit: number;
}

export interface ARAgingRow {
  customer: string;
  current: number;
  days_30: number;
  days_60: number;
  days_90: number;
  over_90: number;
  total: number;
}

export interface APAgingRow {
  supplier: string;
  current: number;
  days_30: number;
  days_60: number;
  days_90: number;
  over_90: number;
  total: number;
}

// Exchange Rate
export interface ExchangeRate {
  id: number;
  from_currency: number;
  from_currency_details?: Currency;
  to_currency: number;
  to_currency_details?: Currency;
  rate_date: string;
  rate: string;
  rate_type: 'SPOT' | 'AVERAGE' | 'FIXED' | 'CLOSING';
  source?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// FX Gain/Loss Account
export interface FXGainLossAccount {
  id: number;
  account: number;
  account_details?: Account;
  gain_loss_type: 'REALIZED_GAIN' | 'REALIZED_LOSS' | 'UNREALIZED_GAIN' | 'UNREALIZED_LOSS';
  description?: string;
  created_at?: string;
  updated_at?: string;
}

// Corporate Tax Filing
export interface CorporateTaxFiling {
  id: number;
  filing_period_start: string;
  filing_period_end: string;
  tax_rate: string;
  taxable_income: string;
  tax_amount: string;
  status: 'DRAFT' | 'ACCRUED' | 'FILED' | 'PAID' | 'REVERSED';
  journal_entry?: number;
  filed_date?: string;
  created_at: string;
  updated_at: string;
}

// Invoice Approval
export interface InvoiceApproval {
  id?: number;
  invoice_type: 'AR' | 'AP';
  invoice_id: number;
  invoice_number?: string;
  submitted_by: number;
  submitted_by_name?: string;
  approver: number;
  approver_name?: string;
  approval_level: number;
  status: 'DRAFT' | 'PENDING' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'POSTED';
  comments?: string;
  submitted_at?: string;
  approved_rejected_at?: string;
  created_at?: string;
  updated_at?: string;
}

// Attachment Types
export interface Attachment {
  id: number;
  po_header?: number;
  pr_header?: number;
  file: string;
  file_url: string;
  document_type: 'PO' | 'PR' | 'QUOTE' | 'CONTRACT' | 'SPEC' | 'OTHER';
  description: string;
  file_size: number;
  file_size_display: string;
  file_extension: string;
  original_filename: string;
  uploaded_by: number;
  uploaded_by_name: string;
  uploaded_at: string;
}

export interface AttachmentUpload {
  file: File;
  document_type: 'PO' | 'PR' | 'QUOTE' | 'CONTRACT' | 'SPEC' | 'OTHER';
  description: string;
}

// Export all procurement types
export * from './procurement';

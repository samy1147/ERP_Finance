// Procurement Module Types

// ============================================================================
// VENDOR BILL MODULE
// ============================================================================

export interface VendorBill {
  id: number;
  bill_number: string;
  supplier: number;
  supplier_name?: string;
  supplier_invoice_number?: string;
  supplier_invoice_date?: string;
  bill_type?: string;
  bill_type_display?: string;
  purchase_order_number?: string;
  bill_date: string;
  invoice_date?: string;
  due_date: string;
  payment_terms?: string;
  currency: number;
  currency_code?: string;
  exchange_rate?: string;
  subtotal: string;
  tax_amount: string;
  total_amount: string;
  base_currency_total?: string;
  paid_amount: string;
  balance_due?: string;
  status: 'DRAFT' | 'SUBMITTED' | 'PENDING_MATCH' | 'MATCHED' | 'EXCEPTION' | 'APPROVED' | 'POSTED' | 'PAID' | 'CANCELLED';
  status_display?: string;
  match_status?: 'UNMATCHED' | 'PARTIAL' | 'FULLY_MATCHED' | 'OVER_RECEIPT';
  is_matched?: boolean;
  match_date?: string;
  has_exceptions?: boolean;
  exception_count?: number;
  approval_status?: 'PENDING' | 'APPROVED' | 'REJECTED';
  approved_by?: number;
  approved_date?: string;
  ap_invoice?: number;
  ap_posted_date?: string;
  ap_posted_by?: number;
  is_posted?: boolean;
  is_paid?: boolean;
  posted_at?: string;
  paid_at?: string;
  paid_date?: string;
  cancelled_at?: string;
  notes?: string;
  internal_notes?: string;
  description?: string;
  lines: VendorBillLine[];
  matching_issues?: MatchingIssue[];
  attachments?: BillAttachment[];
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface VendorBillLine {
  id?: number;
  line_number: number;
  description: string;
  quantity: string;
  unit_price: string;
  tax_rate?: number;
  tax_amount: string;
  line_total: string;
  account?: number;
  purchase_order_line?: number;
  goods_receipt_line?: number;
  match_status: 'UNMATCHED' | 'MATCHED' | 'VARIANCE';
  variance_amount?: string;
  variance_reason?: string;
}

export interface MatchingIssue {
  id: number;
  vendor_bill: number;
  issue_type: 'PRICE_VARIANCE' | 'QUANTITY_VARIANCE' | 'NO_PO' | 'NO_GR' | 'OTHER';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  affected_line?: number;
  variance_amount?: string;
  resolved: boolean;
  resolved_at?: string;
  resolved_by?: number;
  resolution_notes?: string;
}

export interface BillAttachment {
  id: number;
  vendor_bill: number;
  file: string;
  file_name: string;
  file_type: string;
  file_size: number;
  uploaded_by: number;
  uploaded_at: string;
  description?: string;
}

export interface ThreeWayMatchResult {
  can_match: boolean;
  match_status: 'FULL' | 'PARTIAL' | 'NONE';
  matched_lines: number;
  total_lines: number;
  variances: {
    line_number: number;
    type: 'PRICE' | 'QUANTITY';
    expected: string;
    actual: string;
    difference: string;
    percentage: string;
  }[];
  total_variance: string;
  within_tolerance: boolean;
}

// ============================================================================
// PAYMENT INTEGRATION MODULE
// ============================================================================

export interface PaymentRequest {
  id: number;
  request_number: string;
  supplier: number;
  supplier_name?: string;
  vendor_bills: number[];
  vendor_bill_numbers?: string[];
  payment_method: 'BANK_TRANSFER' | 'CHECK' | 'CASH' | 'CARD' | 'WIRE' | 'ACH';
  payment_date: string;
  amount: string;
  currency: number;
  currency_code?: string;
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  bank_account?: number;
  reference?: string;
  notes?: string;
  created_by: number;
  created_by_name?: string;
  approved_by?: number;
  approved_by_name?: string;
  approved_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentBatch {
  id: number;
  batch_number: string;
  payment_method: 'BANK_TRANSFER' | 'CHECK' | 'CASH' | 'CARD' | 'WIRE' | 'ACH';
  payment_date: string;
  total_amount: string;
  currency: number;
  currency_code?: string;
  status: 'DRAFT' | 'READY' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  payment_count: number;
  bank_account?: number;
  batch_file?: string;
  created_by: number;
  processed_at?: string;
  notes?: string;
  payments: PaymentRequest[];
  created_at: string;
  updated_at: string;
}

export interface PaymentApproval {
  id: number;
  payment_request: number;
  payment_request_number?: string;
  approver: number;
  approver_name?: string;
  approval_level: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  comments?: string;
  approved_at?: string;
  created_at: string;
}

export interface BankReconciliation {
  id: number;
  bank_account: number;
  bank_account_name?: string;
  statement_date: string;
  statement_balance: string;
  book_balance: string;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'REVIEWED';
  reconciled_by?: number;
  reconciled_at?: string;
  notes?: string;
  reconciliation_items: ReconciliationItem[];
  created_at: string;
  updated_at: string;
}

export interface ReconciliationItem {
  id: number;
  reconciliation: number;
  transaction_type: 'PAYMENT' | 'DEPOSIT' | 'FEE' | 'OTHER';
  transaction_date: string;
  description: string;
  amount: string;
  bank_reference?: string;
  book_reference?: string;
  matched: boolean;
  matched_payment?: number;
  notes?: string;
}

export interface PaymentMethod {
  id: number;
  name: string;
  code: string;
  method_type: 'BANK_TRANSFER' | 'CHECK' | 'CASH' | 'CARD' | 'WIRE' | 'ACH';
  requires_approval: boolean;
  approval_threshold?: string;
  default_bank_account?: number;
  is_active: boolean;
  processing_days: number;
  description?: string;
}

export interface PaymentTerm {
  id: number;
  name: string;
  code: string;
  days: number;
  discount_days?: number;
  discount_percentage?: string;
  description?: string;
  is_active: boolean;
}

export interface BankAccount {
  id: number;
  account_name: string;
  account_number: string;
  bank_name: string;
  branch?: string;
  swift_code?: string;
  iban?: string;
  currency: number;
  currency_code?: string;
  account_type: 'CHECKING' | 'SAVINGS' | 'MONEY_MARKET';
  current_balance: string;
  is_active: boolean;
  gl_account?: number;
}

// ============================================================================
// CONTRACT MANAGEMENT MODULE
// ============================================================================

export interface Contract {
  id: number;
  contract_number: string;
  title: string;
  contract_type: 'PURCHASE' | 'SALES' | 'SERVICE' | 'LEASE' | 'NDA' | 'FRAMEWORK' | 'OTHER';
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'ACTIVE' | 'SUSPENDED' | 'TERMINATED' | 'EXPIRED' | 'COMPLETED';
  party_type: 'SUPPLIER' | 'CUSTOMER';
  party_id: number;
  party_name?: string;
  start_date: string;
  end_date: string;
  auto_renew: boolean;
  renewal_notice_days: number;
  total_value: string;
  currency: number;
  currency_code?: string;
  payment_terms?: string;
  payment_schedule: 'MONTHLY' | 'QUARTERLY' | 'ANNUALLY' | 'MILESTONE' | 'ONE_TIME';
  description?: string;
  terms_and_conditions?: string;
  cancellation_policy?: string;
  approved_by?: number;
  approved_at?: string;
  terminated_at?: string;
  termination_reason?: string;
  lines: ContractLine[];
  milestones: ContractMilestone[];
  amendments: ContractAmendment[];
  attachments: ContractAttachment[];
  created_at: string;
  updated_at: string;
}

export interface ContractLine {
  id?: number;
  line_number: number;
  description: string;
  quantity: string;
  unit_price: string;
  total_amount: string;
  account?: number;
  start_date?: string;
  end_date?: string;
}

export interface ContractMilestone {
  id: number;
  contract: number;
  milestone_number: number;
  title: string;
  description?: string;
  due_date: string;
  amount: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'DELAYED' | 'CANCELLED';
  completion_date?: string;
  completion_notes?: string;
  invoice_generated: boolean;
  invoice_id?: number;
}

export interface ContractAmendment {
  id: number;
  contract: number;
  amendment_number: number;
  amendment_type: 'VALUE_CHANGE' | 'DATE_EXTENSION' | 'SCOPE_CHANGE' | 'TERMS_CHANGE' | 'OTHER';
  effective_date: string;
  description: string;
  old_value?: string;
  new_value?: string;
  approved_by?: number;
  approved_at?: string;
  created_at: string;
}

export interface ContractAttachment {
  id: number;
  contract: number;
  file: string;
  file_name: string;
  file_type: string;
  file_size: number;
  document_type: 'CONTRACT_PDF' | 'AMENDMENT' | 'INVOICE' | 'CORRESPONDENCE' | 'OTHER';
  uploaded_by: number;
  uploaded_at: string;
  description?: string;
}

export interface ContractTemplate {
  id: number;
  name: string;
  template_type: 'PURCHASE' | 'SALES' | 'SERVICE' | 'LEASE' | 'NDA' | 'FRAMEWORK' | 'OTHER';
  description?: string;
  default_payment_terms?: string;
  default_payment_schedule: 'MONTHLY' | 'QUARTERLY' | 'ANNUALLY' | 'MILESTONE' | 'ONE_TIME';
  default_terms_and_conditions?: string;
  default_cancellation_policy?: string;
  is_active: boolean;
  created_at: string;
}

// ============================================================================
// PROCUREMENT REPORTS MODULE
// ============================================================================

export interface PurchaseAnalytics {
  period_start: string;
  period_end: string;
  total_spend: string;
  total_invoices: number;
  total_suppliers: number;
  average_invoice_value: string;
  spend_by_category: {
    category: string;
    amount: string;
    percentage: string;
  }[];
  spend_by_supplier: {
    supplier_id: number;
    supplier_name: string;
    amount: string;
    percentage: string;
    invoice_count: number;
  }[];
  monthly_trend: {
    month: string;
    amount: string;
    invoice_count: number;
  }[];
}

export interface SupplierPerformance {
  supplier_id: number;
  supplier_name: string;
  total_orders: number;
  total_value: string;
  on_time_delivery_rate: string;
  quality_score: string;
  lead_time_average: number;
  defect_rate: string;
  compliance_score: string;
  last_evaluation_date?: string;
}

export interface ContractExpiry {
  contract_id: number;
  contract_number: string;
  title: string;
  supplier_id?: number;
  supplier_name?: string;
  customer_id?: number;
  customer_name?: string;
  contract_type: string;
  start_date: string;
  end_date: string;
  days_until_expiry: number;
  total_value: string;
  auto_renew: boolean;
  status: string;
}

export interface PaymentSchedule {
  id: number;
  vendor_bill_id?: number;
  vendor_bill_number?: string;
  contract_id?: number;
  contract_number?: string;
  supplier_id: number;
  supplier_name: string;
  due_date: string;
  amount: string;
  currency_code: string;
  payment_status: 'PENDING' | 'SCHEDULED' | 'PAID' | 'OVERDUE' | 'CANCELLED';
  days_overdue?: number;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
}

export interface VendorSpend {
  supplier_id: number;
  supplier_name: string;
  period_start: string;
  period_end: string;
  total_spend: string;
  invoice_count: number;
  average_invoice_value: string;
  payment_terms_average: number;
  early_payment_discount_taken: string;
  spend_category: string;
  year_over_year_change?: string;
}

export interface ProcurementCompliance {
  total_invoices: number;
  invoices_with_po: number;
  po_compliance_rate: string;
  invoices_with_contract: number;
  contract_compliance_rate: string;
  three_way_match_rate: string;
  average_approval_time: number;
  policy_violations: {
    violation_type: string;
    count: number;
    total_value: string;
  }[];
  period_start: string;
  period_end: string;
}

export interface CashFlowForecast {
  forecast_date: string;
  projected_payables: {
    date: string;
    amount: string;
    invoice_count: number;
    supplier_count: number;
  }[];
  projected_receivables: {
    date: string;
    amount: string;
    invoice_count: number;
    customer_count: number;
  }[];
  net_cash_flow: {
    date: string;
    amount: string;
  }[];
  confidence_level: 'LOW' | 'MEDIUM' | 'HIGH';
}

// ============================================================================
// ADDITIONAL REQUISITION MODULE (if needed)
// ============================================================================

export interface PurchaseRequisition {
  id: number;
  pr_number: string;
  requester: number;
  requester_name?: string;
  department?: string;
  request_date: string;
  required_by_date: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'CONVERTED' | 'CANCELLED';
  total_amount: string;
  currency: number;
  currency_code?: string;
  justification?: string;
  approved_by?: number;
  approved_at?: string;
  rejection_reason?: string;
  lines: PurchaseRequisitionLine[];
  created_at: string;
  updated_at: string;
}

export interface PurchaseRequisitionLine {
  id?: number;
  line_number: number;
  description: string;
  quantity: string;
  estimated_unit_price: string;
  estimated_total: string;
  suggested_supplier?: number;
  suggested_supplier_name?: string;
  account?: number;
  delivery_date?: string;
  specifications?: string;
  item_type?: 'CATEGORIZED' | 'NON_CATEGORIZED'; // Item categorization status
}

// ============================================================================
// RECEIVING MODULE
// ============================================================================

export interface GoodsReceipt {
  id: number;
  receipt_number?: string; // Alias for grn_number
  grn_number?: string; // Backend field name
  grn_type?: 'CATEGORIZED_GOODS' | 'UNCATEGORIZED_GOODS' | 'SERVICES'; // GRN Type
  purchase_order?: number;
  po_header?: number; // Backend field name
  purchase_order_number?: string;
  po_number?: string; // Backend field name
  po_reference?: string; // Backend field name
  supplier?: number;
  supplier_name?: string;
  vendor_name?: string; // Alternative field name
  receipt_date: string;
  received_by?: number;
  received_by_name?: string;
  status: 'DRAFT' | 'RECEIVED' | 'INSPECTED' | 'ACCEPTED' | 'REJECTED' | 'RETURNED' | 'PENDING' | 'COMPLETED' | 'IN_PROGRESS';
  inspection_required?: boolean;
  inspection_date?: string;
  inspected_by?: number;
  inspection_notes?: string;
  lines: GoodsReceiptLine[];
  // Additional backend fields
  warehouse?: number;
  warehouse_name?: string;
  posted_to_inventory?: boolean;
  posted_by?: number;
  posted_at?: string;
  notes?: string;
  remarks?: string; // Alternative field name
  // Delivery tracking fields
  delivery_note_number?: string;
  vehicle_number?: string;
  driver_name?: string;
  carrier?: string;
  tracking_number?: string;
  created_at?: string;
  updated_at?: string;
}

export interface GoodsReceiptLine {
  id?: number;
  line_number: number;
  purchase_order_line?: number;
  po_line?: number; // Backend field name
  description: string;
  item?: number; // Backend field name
  item_name?: string; // Backend field name
  ordered_quantity?: string;
  received_quantity: string;
  accepted_quantity?: string;
  rejected_quantity?: string;
  unit_price?: string;
  line_total?: string;
  quality_status: 'PENDING' | 'PASS' | 'FAIL' | 'CONDITIONAL';
  rejection_reason?: string;
  storage_location?: string;
  // Additional backend fields
  unit_of_measure?: string;
  uom?: string; // Backend field name
  notes?: string;
}

// ============================================================================
// RFx/SOURCING MODULE
// ============================================================================

export interface RFxEvent {
  id: number;
  event_number: string;
  event_type: 'RFQ' | 'RFP' | 'RFI' | 'AUCTION';
  title: string;
  description: string;
  status: 'DRAFT' | 'PUBLISHED' | 'OPEN' | 'CLOSED' | 'AWARDED' | 'CANCELLED';
  publish_date?: string;
  open_date?: string;
  close_date: string;
  currency: number;
  currency_code?: string;
  evaluation_criteria?: string;
  technical_weight?: number;
  commercial_weight?: number;
  items: RFxItem[];
  invitations?: SupplierInvitation[];
  quotes?: SupplierQuote[];
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface RFxItem {
  id?: number;
  line_number: number;
  description: string;
  specifications?: string;
  quantity: string;
  unit_of_measure?: string;
  estimated_price?: string;
  target_price?: string;
  delivery_date?: string;
}

export interface SupplierInvitation {
  id: number;
  rfx_event: number;
  supplier: number;
  supplier_name?: string;
  invited_date: string;
  invitation_sent: boolean;
  responded: boolean;
  response_date?: string;
  status: 'INVITED' | 'VIEWED' | 'RESPONDED' | 'DECLINED';
}

export interface SupplierQuote {
  id: number;
  rfx_event: number;
  supplier: number;
  supplier_name?: string;
  quote_number: string;
  submission_date?: string;
  valid_until?: string;
  currency: number;
  currency_code?: string;
  total_amount: string;
  payment_terms?: string;
  delivery_terms?: string;
  technical_score?: number;
  commercial_score?: number;
  total_score?: number;
  status: 'DRAFT' | 'SUBMITTED' | 'EVALUATED' | 'AWARDED' | 'REJECTED';
  evaluator_notes?: string;
  items: QuoteItem[];
  created_at: string;
  updated_at: string;
}

export interface QuoteItem {
  id?: number;
  rfx_item: number;
  line_number: number;
  description?: string;
  unit_price: string;
  quantity: string;
  line_total: string;
  delivery_date?: string;
  notes?: string;
}

export interface RFxAward {
  id: number;
  rfx_event: number;
  award_number: string;
  award_type: 'SINGLE' | 'SPLIT' | 'PARTIAL';
  award_date: string;
  winning_quotes: number[];
  total_amount: string;
  status: 'PENDING' | 'APPROVED' | 'CONVERTED' | 'CANCELLED';
  approval_notes?: string;
  purchase_orders?: number[];
  created_at: string;
}

// ============================================================================
// REQUISITIONS MODULE (Extended)
// ============================================================================

export interface PRHeader {
  id: number;
  pr_number: string;
  requester: number;
  requester_name?: string;
  cost_center?: number;
  cost_center_name?: string;
  project?: number;
  project_name?: string;
  request_date: string;
  required_date: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  pr_type?: 'CATEGORIZED_GOODS' | 'UNCATEGORIZED_GOODS' | 'SERVICES'; // Updated field
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'CONVERTED' | 'CANCELLED';
  total_amount: string;
  currency: number;
  currency_code?: string;
  budget_checked: boolean;
  budget_available: boolean;
  justification?: string;
  lines: PRLine[];
  approval_history?: ApprovalStep[];
  created_at: string;
  updated_at: string;
}

export interface PRLine {
  id?: number;
  line_number: number;
  description: string;
  quantity: string;
  estimated_price: string;
  line_total: string;
  suggested_supplier?: number;
  suggested_supplier_name?: string;
  catalog_item?: number;
  account?: number;
  delivery_date?: string;
}

export interface CostCenter {
  id: number;
  code: string;
  name: string;
  description?: string;
  manager?: number;
  manager_name?: string;
  budget_amount?: string;
  spent_amount?: string;
  committed_amount?: string;
  available_amount?: string;
  active: boolean;
}

export interface Project {
  id: number;
  code: string;
  name: string;
  description?: string;
  project_manager?: number;
  manager_name?: string;
  start_date?: string;
  end_date?: string;
  budget_amount?: string;
  spent_amount?: string;
  status: 'PLANNED' | 'ACTIVE' | 'ON_HOLD' | 'COMPLETED' | 'CANCELLED';
}

// ============================================================================
// QUALITY/RECEIVING EXTENDED
// ============================================================================

export interface QualityInspection {
  id: number;
  inspection_number: string;
  grn: number;
  grn_number?: string;
  inspection_type: 'VISUAL' | 'DIMENSIONAL' | 'FUNCTIONAL' | 'DESTRUCTIVE' | 'SAMPLING';
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'APPROVED' | 'REJECTED';
  inspector?: number;
  inspector_name?: string;
  start_date?: string;
  completion_date?: string;
  inspection_notes?: string;
  result: 'PASS' | 'FAIL' | 'CONDITIONAL' | 'PENDING';
  non_conformances?: NonConformance[];
  created_at: string;
}

export interface NonConformance {
  id: number;
  inspection: number;
  nc_number: string;
  description: string;
  severity: 'MINOR' | 'MAJOR' | 'CRITICAL';
  quantity_affected: string;
  disposition: 'USE_AS_IS' | 'REWORK' | 'RETURN' | 'SCRAP' | 'PENDING';
  resolution_notes?: string;
  resolved: boolean;
  resolved_date?: string;
}

export interface ReturnToVendor {
  id: number;
  rtv_number: string;
  grn: number;
  grn_number?: string;
  supplier: number;
  supplier_name?: string;
  return_date: string;
  reason: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'SHIPPED' | 'COMPLETED' | 'CANCELLED';
  lines: RTVLine[];
  tracking_number?: string;
  credit_note_received: boolean;
  created_at: string;
}

export interface RTVLine {
  id?: number;
  grn_line: number;
  description: string;
  return_quantity: string;
  reason: string;
}

// ============================================================================
// CATALOG MODULE
// ============================================================================

export interface CatalogItem {
  id: number;
  sku: string;
  item_code: string;
  name: string;
  short_description?: string;
  long_description?: string;
  category?: number;
  category_name?: string;
  item_type?: string;
  unit_of_measure: number;
  uom_code?: string;
  list_price: string;
  currency: number;
  currency_code?: string;
  preferred_supplier?: number;
  supplier_name?: string;
  lead_time_days?: number;
  minimum_order_quantity?: string;
  order_multiple?: string;
  is_active: boolean;
  is_purchasable?: boolean;
  is_restricted?: boolean;
  price_tiers?: PriceTier[];
  specifications?: any;
  attributes?: any;
  image_url?: string;
  datasheet_url?: string;
  additional_images?: any;
  manufacturer?: string;
  manufacturer_part_number?: string;
  brand?: string;
  model_number?: string;
  is_taxable?: boolean;
  tax_category?: string;
  gl_account_code?: string;
  restriction_notes?: string;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface PriceTier {
  id?: number;
  catalog_item: number;
  min_quantity: string;
  unit_price: string;
  discount_percentage?: string;
}

export interface FrameworkAgreement {
  id: number;
  agreement_number: string;
  title: string;
  supplier: number;
  supplier_name?: string;
  start_date: string;
  end_date: string;
  total_value_limit?: string;
  currency: number;
  currency_code?: string;
  status: 'DRAFT' | 'ACTIVE' | 'SUSPENDED' | 'EXPIRED' | 'TERMINATED';
  payment_terms?: string;
  delivery_terms?: string;
  items: FrameworkItem[];
  utilized_amount?: string;
  remaining_amount?: string;
  created_at: string;
  updated_at: string;
}

export interface FrameworkItem {
  id?: number;
  catalog_item?: number;
  item_code: string;
  description: string;
  unit_price: string;
  unit_of_measure?: string;
  maximum_quantity?: string;
  ordered_quantity?: string;
}

export interface CallOffOrder {
  id: number;
  calloff_number: string;
  framework_agreement: number;
  agreement_number?: string;
  order_date: string;
  delivery_date: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'SENT' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED';
  total_amount: string;
  lines: CallOffLine[];
  delivery_address?: string;
  supplier_reference?: string;
  created_at: string;
  updated_at: string;
}

export interface CallOffLine {
  id?: number;
  framework_item: number;
  line_number: number;
  description: string;
  quantity: string;
  unit_price: string;
  line_total: string;
  delivery_date?: string;
  received_quantity?: string;
}

// ============================================================================
// APPROVAL WORKFLOWS MODULE
// ============================================================================

export interface ApprovalWorkflow {
  id: number;
  name: string;
  description?: string;
  entity_type: 'PR' | 'PO' | 'BILL' | 'PAYMENT' | 'CONTRACT' | 'RFX';
  active: boolean;
  steps: WorkflowStep[];
  created_at: string;
  updated_at: string;
}

export interface WorkflowStep {
  id?: number;
  step_number: number;
  step_name: string;
  approver_type: 'USER' | 'ROLE' | 'MANAGER' | 'BUDGET_OWNER';
  approver_id?: number;
  approver_name?: string;
  approval_required: boolean;
  parallel_approval: boolean;
  condition?: string;
  min_amount?: string;
  max_amount?: string;
}

export interface ApprovalInstance {
  id: number;
  workflow: number;
  workflow_name?: string;
  entity_type: string;
  entity_id: number;
  entity_reference?: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
  submitted_by: number;
  submitted_at: string;
  current_step?: number;
  steps: ApprovalStep[];
  completed_at?: string;
}

export interface ApprovalStep {
  id: number;
  instance: number;
  step_number: number;
  step_name: string;
  approver: number;
  approver_name?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'SKIPPED';
  comments?: string;
  action_date?: string;
  due_date?: string;
}

export interface ApprovalDelegation {
  id: number;
  delegator: number;
  delegator_name?: string;
  delegate: number;
  delegate_name?: string;
  start_date: string;
  end_date: string;
  reason?: string;
  active: boolean;
  created_at: string;
}

export interface BudgetAllocation {
  id: number;
  cost_center: number;
  cost_center_name?: string;
  fiscal_year: number;
  period?: string;
  budget_amount: string;
  spent_amount: string;
  committed_amount: string;
  available_amount: string;
  warning_threshold?: number;
  status: 'ACTIVE' | 'OVER_BUDGET' | 'AT_WARNING' | 'EXHAUSTED';
}


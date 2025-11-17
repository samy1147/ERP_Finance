"""
AP (Accounts Payable) Models
Supplier/Vendor, APInvoice, APItem, APPayment
Vendor Management: Contacts, Documents, Performance
"""
from django.db import models
from core.models import Currency, TaxRate

TAX_COUNTRIES = [("AE","UAE"),("SA","KSA"),("EG","Egypt"),("IN","India")]
TAX_CATS = [("STANDARD","Standard"),("ZERO","Zero"),("EXEMPT","Exempt"),("RC","Reverse Charge")]


class Supplier(models.Model):
    """
    Supplier/Vendor master data
    Note: Supplier and Vendor refer to the same entity
    """
    # Basic Information
    code = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Unique supplier/vendor code")
    name = models.CharField(max_length=128, help_text="Legal name of supplier/vendor")
    legal_name = models.CharField(max_length=255, blank=True, help_text="Full legal entity name (if different from name)")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Location & Tax
    country = models.CharField(max_length=2, default="AE", help_text="ISO 2-letter country code")
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Tax & Registration
    vat_number = models.CharField(max_length=50, blank=True, help_text="VAT/Tax registration number (TRN)")
    tax_id = models.CharField(max_length=50, blank=True, help_text="Alternative tax ID")
    trade_license_number = models.CharField(max_length=100, blank=True)
    trade_license_expiry = models.DateField(null=True, blank=True)
    
    # Financial Details
    currency = models.ForeignKey("core.Currency", on_delete=models.PROTECT, null=True, blank=True,
                                 help_text="Supplier's default currency",
                                 related_name="ap_suppliers")
    payment_terms_days = models.IntegerField(default=30, help_text="Default payment terms in days")
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text="Credit limit for this vendor")
    
    # Bank Details
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_iban = models.CharField(max_length=50, blank=True, help_text="IBAN number")
    bank_swift = models.CharField(max_length=20, blank=True, help_text="SWIFT/BIC code")
    bank_routing_number = models.CharField(max_length=50, blank=True)
    
    # Vendor Classification & Status
    VENDOR_CATEGORIES = [
        ('GOODS', 'Goods Supplier'),
        ('SERVICES', 'Services Provider'),
        ('BOTH', 'Goods & Services'),
        ('CONTRACTOR', 'Contractor'),
        ('CONSULTANT', 'Consultant'),
    ]
    vendor_category = models.CharField(max_length=20, choices=VENDOR_CATEGORIES, default='GOODS')
    is_preferred = models.BooleanField(default=False, help_text="Preferred supplier/vendor")
    is_active = models.BooleanField(default=True)
    is_blacklisted = models.BooleanField(default=False, help_text="Vendor is blacklisted")
    is_on_hold = models.BooleanField(default=False, help_text="Vendor is on hold (temporary suspension)")
    hold_reason = models.TextField(blank=True, help_text="Reason for hold status")
    blacklist_reason = models.TextField(blank=True, help_text="Reason for blacklisting")
    
    # Onboarding & Compliance
    ONBOARDING_STATUSES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    ]
    onboarding_status = models.CharField(max_length=20, choices=ONBOARDING_STATUSES, default='PENDING')
    onboarding_completed_date = models.DateField(null=True, blank=True)
    compliance_verified = models.BooleanField(default=False, help_text="Compliance documents verified")
    compliance_verified_date = models.DateField(null=True, blank=True)
    
    # Performance Metrics (calculated fields - updated by background jobs)
    performance_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Overall performance score (0-100)"
    )
    quality_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Quality score (0-100)"
    )
    delivery_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="On-time delivery score (0-100)"
    )
    price_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Price adherence score (0-100)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='suppliers_created')
    
    # Notes
    notes = models.TextField(blank=True, help_text="Internal notes about this vendor")
    
    class Meta:
        ordering = ['code']
        db_table = 'ap_supplier'  # NEW table name
        verbose_name = 'Supplier/Vendor'
        verbose_name_plural = 'Suppliers/Vendors'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_overall_performance_score(self):
        """Calculate overall performance score from component scores"""
        from decimal import Decimal
        scores = [
            self.quality_score,
            self.delivery_score,
            self.price_score
        ]
        valid_scores = [s for s in scores if s is not None]
        if valid_scores:
            return sum(valid_scores) / len(valid_scores)
        return None
    
    def can_transact(self):
        """Check if vendor can be used for transactions"""
        return self.is_active and not self.is_blacklisted and not self.is_on_hold


class VendorContact(models.Model):
    """Contact persons for vendors/suppliers"""
    vendor = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='contacts')
    
    # Contact Details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True, help_text="Job title/position")
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    
    # Contact Type & Roles
    CONTACT_TYPES = [
        ('PRIMARY', 'Primary Contact'),
        ('ACCOUNTING', 'Accounting/Finance'),
        ('SALES', 'Sales Representative'),
        ('TECHNICAL', 'Technical Support'),
        ('MANAGEMENT', 'Management'),
        ('OTHER', 'Other'),
    ]
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES, default='OTHER')
    is_primary = models.BooleanField(default=False, help_text="Primary contact for this vendor")
    is_active = models.BooleanField(default=True)
    
    # Communication preferences
    receives_invoices = models.BooleanField(default=False)
    receives_payments = models.BooleanField(default=False)
    receives_orders = models.BooleanField(default=False)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ap_vendor_contact'
        ordering = ['-is_primary', 'last_name', 'first_name']
        verbose_name = 'Vendor Contact'
        verbose_name_plural = 'Vendor Contacts'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.vendor.name})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class VendorDocument(models.Model):
    """Document repository for vendor compliance and onboarding"""
    vendor = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='documents')
    
    # Document Details
    DOCUMENT_TYPES = [
        ('TRADE_LICENSE', 'Trade License'),
        ('TAX_CERTIFICATE', 'Tax Registration Certificate'),
        ('VAT_CERTIFICATE', 'VAT Certificate'),
        ('BANK_LETTER', 'Bank Letter'),
        ('INSURANCE', 'Insurance Certificate'),
        ('CONTRACT', 'Contract/Agreement'),
        ('NDA', 'Non-Disclosure Agreement'),
        ('W9', 'W-9 Form (US)'),
        ('W8', 'W-8 Form (US)'),
        ('QUALITY_CERT', 'Quality Certificate'),
        ('ISO_CERT', 'ISO Certification'),
        ('OTHER', 'Other Document'),
    ]
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=255, help_text="Document name/title")
    document_number = models.CharField(max_length=100, blank=True, help_text="Document reference number")
    
    # File storage
    file = models.FileField(upload_to='vendor_documents/%Y/%m/', blank=True, null=True)
    file_url = models.URLField(blank=True, help_text="External URL if document is stored elsewhere")
    
    # Validity & Compliance
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True, help_text="Expiry date for time-limited documents")
    is_verified = models.BooleanField(default=False, help_text="Document has been verified")
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_vendor_docs')
    verified_date = models.DateField(null=True, blank=True)
    
    # Required for onboarding
    is_required_for_onboarding = models.BooleanField(default=False)
    is_submitted = models.BooleanField(default=True, help_text="Document has been submitted")
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_vendor_docs')
    
    class Meta:
        db_table = 'ap_vendor_document'
        ordering = ['-created_at']
        verbose_name = 'Vendor Document'
        verbose_name_plural = 'Vendor Documents'
    
    def __str__(self):
        return f"{self.vendor.name} - {self.get_document_type_display()}"
    
    @property
    def is_expired(self):
        """Check if document has expired"""
        if self.expiry_date:
            from django.utils import timezone
            return timezone.now().date() > self.expiry_date
        return False
    
    @property
    def days_until_expiry(self):
        """Calculate days until expiry"""
        if self.expiry_date:
            from django.utils import timezone
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None


class VendorPerformanceRecord(models.Model):
    """Track vendor performance metrics over time"""
    vendor = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='performance_records')
    
    # Time period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Delivery Performance
    total_orders = models.IntegerField(default=0, help_text="Total orders in period")
    on_time_deliveries = models.IntegerField(default=0, help_text="Number of on-time deliveries")
    late_deliveries = models.IntegerField(default=0, help_text="Number of late deliveries")
    avg_delivery_delay_days = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Average delay in days for late deliveries"
    )
    
    # Quality Performance
    total_items_received = models.IntegerField(default=0)
    rejected_items = models.IntegerField(default=0, help_text="Items rejected for quality issues")
    defect_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Defect rate as percentage"
    )
    
    # Price Performance
    price_changes = models.IntegerField(default=0, help_text="Number of price changes in period")
    price_increase_count = models.IntegerField(default=0)
    avg_price_variance = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Average price variance percentage"
    )
    
    # Invoice & Payment
    total_invoices = models.IntegerField(default=0)
    disputed_invoices = models.IntegerField(default=0)
    invoice_accuracy_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Invoice accuracy as percentage"
    )
    
    # Calculated Scores (0-100)
    delivery_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Risk Assessment
    RISK_LEVELS = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    ]
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS, null=True, blank=True)
    risk_notes = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'ap_vendor_performance'
        ordering = ['-period_end']
        verbose_name = 'Vendor Performance Record'
        verbose_name_plural = 'Vendor Performance Records'
        unique_together = ['vendor', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.vendor.name} - {self.period_start} to {self.period_end}"
    
    def calculate_scores(self):
        """Calculate performance scores"""
        from decimal import Decimal
        
        # Delivery Score (0-100)
        if self.total_orders > 0:
            on_time_rate = (self.on_time_deliveries / self.total_orders) * 100
            self.delivery_score = Decimal(str(on_time_rate))
        
        # Quality Score (0-100)
        if self.total_items_received > 0:
            acceptance_rate = ((self.total_items_received - self.rejected_items) / self.total_items_received) * 100
            self.quality_score = Decimal(str(acceptance_rate))
            self.defect_rate = Decimal(str((self.rejected_items / self.total_items_received) * 100))
        
        # Price Score (based on stability - fewer changes and increases = higher score)
        base_price_score = Decimal('100')
        if self.price_changes > 0:
            # Deduct points for price changes
            base_price_score -= Decimal(str(min(self.price_changes * 5, 30)))
        if self.price_increase_count > 0:
            # Additional deduction for increases
            base_price_score -= Decimal(str(min(self.price_increase_count * 10, 40)))
        self.price_score = max(Decimal('0'), base_price_score)
        
        # Invoice accuracy
        if self.total_invoices > 0:
            accuracy = ((self.total_invoices - self.disputed_invoices) / self.total_invoices) * 100
            self.invoice_accuracy_rate = Decimal(str(accuracy))
        
        # Overall Score (weighted average)
        scores = []
        if self.delivery_score is not None:
            scores.append(self.delivery_score * Decimal('0.4'))  # 40% weight
        if self.quality_score is not None:
            scores.append(self.quality_score * Decimal('0.4'))   # 40% weight
        if self.price_score is not None:
            scores.append(self.price_score * Decimal('0.2'))     # 20% weight
        
        if scores:
            self.overall_score = sum(scores) / Decimal(str(len(scores)))
        
        # Determine risk level based on overall score
        if self.overall_score is not None:
            if self.overall_score >= 80:
                self.risk_level = 'LOW'
            elif self.overall_score >= 60:
                self.risk_level = 'MEDIUM'
            elif self.overall_score >= 40:
                self.risk_level = 'HIGH'
            else:
                self.risk_level = 'CRITICAL'
        
        self.save()


class VendorOnboardingChecklist(models.Model):
    """Onboarding checklist items for vendors"""
    vendor = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='onboarding_checklist')
    
    # Checklist Item
    item_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Status
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    completed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Priority & Requirements
    is_required = models.BooleanField(default=True, help_text="Required for onboarding completion")
    priority = models.IntegerField(default=0, help_text="Lower number = higher priority")
    
    # Related document
    related_document = models.ForeignKey(VendorDocument, on_delete=models.SET_NULL, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ap_vendor_onboarding_checklist'
        ordering = ['priority', 'item_name']
        verbose_name = 'Vendor Onboarding Checklist Item'
        verbose_name_plural = 'Vendor Onboarding Checklist Items'
    
    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.vendor.name} - {self.item_name}"


class APInvoice(models.Model):
    """Accounts Payable Invoice"""
    # Payment status choices
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    PAYMENT_STATUSES = [
        (UNPAID, "Unpaid"),
        (PARTIALLY_PAID, "Partially Paid"),
        (PAID, "Paid"),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    number = models.CharField(max_length=32, unique=True)
    date = models.DateField()
    due_date = models.DateField()
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="ap_invoices")
    country = models.CharField(max_length=2, choices=TAX_COUNTRIES, default="AE",help_text="Tax country for this invoice (defaults to supplier country)")
    period = models.ForeignKey('periods.FiscalPeriod', on_delete=models.PROTECT, null=True, blank=True, related_name='ap_invoices', help_text="Fiscal period for this invoice")
    
    # 3-Way Match fields (PO → GR → Invoice matching)
    po_header = models.ForeignKey(
        'purchase_orders.POHeader',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ap_invoices',
        help_text="Purchase Order linked to this invoice"
    )
    goods_receipt = models.ForeignKey(
        'receiving.GoodsReceipt',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ap_invoices',
        help_text="Goods Receipt linked to this invoice"
    )
    
    # 3-Way Match Status
    MATCH_NOT_REQUIRED = 'NOT_REQUIRED'
    MATCH_PENDING = 'PENDING'
    MATCH_MATCHED = 'MATCHED'
    MATCH_VARIANCE = 'VARIANCE'
    MATCH_FAILED = 'FAILED'
    MATCH_STATUSES = [
        (MATCH_NOT_REQUIRED, 'Not Required'),
        (MATCH_PENDING, 'Pending Match'),
        (MATCH_MATCHED, 'Matched'),
        (MATCH_VARIANCE, 'Variance Detected'),
        (MATCH_FAILED, 'Match Failed'),
    ]
    three_way_match_status = models.CharField(
        max_length=20,
        choices=MATCH_STATUSES,
        default=MATCH_NOT_REQUIRED,
        help_text="3-way match validation status"
    )
    match_variance_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Variance amount between invoice and PO (if any)"
    )
    match_variance_notes = models.TextField(
        blank=True,
        help_text="Notes about match variances"
    )
    match_performed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When 3-way match was last performed"
    )
    
    # Approval workflow
    APPROVAL_STATUSES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUSES,
        default='DRAFT',
        help_text="Approval workflow status"
    )
    
    # Posting status - separates draft/posted state
    is_posted = models.BooleanField(default=False, help_text="Whether invoice is posted to GL")
    posted_at = models.DateTimeField(null=True, blank=True)
    
    # Payment status - separates payment state
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUSES, 
        default=UNPAID,
        help_text="Payment status of the invoice"
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Cancellation flag
    is_cancelled = models.BooleanField(default=False, help_text="Whether invoice is cancelled")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    gl_journal = models.OneToOneField(
        "finance.JournalEntry", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="ap_source_new")  # Changed related_name to avoid conflict
    
    # FX tracking fields
    exchange_rate = models.DecimalField(
        max_digits=18, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Exchange rate used when posting (invoice currency to base currency)"
    )
    base_currency_total = models.DecimalField(
        max_digits=14, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Total amount in base currency"
    )
    
    # Stored total fields
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Invoice subtotal (before tax)"
    )
    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total tax amount"
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Invoice total (subtotal + tax)"
    )
    
    class Meta:
        db_table = 'ap_apinvoice'  # NEW table name
    
    def save(self, *args, **kwargs):
        # Auto-set country from supplier if not explicitly set
        if not self.country and self.supplier and self.supplier.country:
            self.country = self.supplier.country
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"AP-{self.number}"
    
    def calculate_and_save_totals(self):
        """Calculate invoice totals from items and save to database"""
        from decimal import Decimal
        
        subtotal_amt = Decimal('0.00')
        tax_amt = Decimal('0.00')
        
        for item in self.items.all():
            line_subtotal = item.quantity * item.unit_price
            line_tax = Decimal('0.00')
            if item.tax_rate:
                line_tax = line_subtotal * (item.tax_rate.rate / 100)
            subtotal_amt += line_subtotal
            tax_amt += line_tax
        
        self.subtotal = subtotal_amt
        self.tax_amount = tax_amt
        self.total = subtotal_amt + tax_amt
        self.save(update_fields=['subtotal', 'tax_amount', 'total'])
        
        return {
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'total': self.total
        }
    
    def has_distributions(self):
        """Check if invoice has GL distribution lines (DEPRECATED - Always returns True)"""
        # Note: GL distribution lines are now deprecated
        # Distributions are created when invoice is posted to GL via JournalEntry
        # This method returns True to avoid validation errors
        return True
    
    def validate_distributions(self):
        """
        Validate GL distribution lines (DEPRECATED - Always returns valid)
        
        Returns:
            dict: {'valid': True, 'errors': [], 'warnings': []}
        """
        # Note: GL distribution lines are now deprecated
        # Distributions are created when invoice is posted to GL
        # This method returns valid to avoid blocking invoice creation
        return {
            'valid': True,
            'errors': [],
            'warnings': ['GL distributions are created when invoice is posted to GL']
        }
    
    def create_distributions_from_items(self, default_account=None):
        """
        Create GL distribution lines from items (DEPRECATED - No-op)
        
        Args:
            default_account: Default expense account (ignored)
            
        Returns:
            list: Empty list (no distributions created)
        """
        # Note: GL distribution lines are now deprecated
        # Distributions are created when invoice is posted to GL via JournalEntry
        # This method returns empty list to avoid errors but doesn't create anything
        print("DEBUG: create_distributions_from_items called (deprecated - no-op)")
        return []
    
    def calculate_total(self):
        """Calculate invoice total from items (backward compatibility)"""
        from decimal import Decimal
        
        total = Decimal('0.00')
        for item in self.items.all():
            subtotal = item.quantity * item.unit_price
            tax_amount = Decimal('0.00')
            if item.tax_rate:
                tax_amount = subtotal * (item.tax_rate.rate / 100)
            total += subtotal + tax_amount
        return total
    
    def perform_three_way_match(self):
        """
        Perform 3-way match between PO, Goods Receipt, and Invoice
        
        Returns:
            dict: {
                'status': 'MATCHED'|'VARIANCE'|'FAILED',
                'variances': [list of variance details],
                'total_variance': Decimal (total variance amount),
                'can_auto_approve': bool,
                'messages': [list of messages]
            }
        """
        from decimal import Decimal
        from django.utils import timezone
        
        result = {
            'status': self.MATCH_MATCHED,
            'variances': [],
            'total_variance': Decimal('0.00'),
            'can_auto_approve': False,
            'messages': []
        }
        
        # Validation: Must have PO and GR
        if not self.po_header:
            result['status'] = self.MATCH_FAILED
            result['messages'].append('Invoice must be linked to a Purchase Order')
            return result
        
        if not self.goods_receipt:
            result['status'] = self.MATCH_FAILED
            result['messages'].append('Invoice must be linked to a Goods Receipt')
            return result
        
        # Validate that GR belongs to the PO
        if self.goods_receipt.po_header_id != self.po_header.id:
            result['status'] = self.MATCH_FAILED
            result['messages'].append('Goods Receipt does not match the Purchase Order')
            return result
        
        # Validate supplier matches
        if self.supplier_id != self.po_header.supplier_id:
            result['status'] = self.MATCH_FAILED
            result['messages'].append('Invoice supplier does not match PO supplier')
            return result
        
        # Compare invoice total vs PO total
        po_total = self.po_header.total_amount or Decimal('0.00')
        invoice_total = self.total or Decimal('0.00')
        
        # Calculate variance
        variance = invoice_total - po_total
        variance_pct = (variance / po_total * 100) if po_total > 0 else Decimal('0.00')
        
        # Tolerance thresholds (configurable in production)
        TOLERANCE_AMOUNT = Decimal('100.00')  # $100
        TOLERANCE_PCT = Decimal('5.00')  # 5%
        
        if abs(variance) > Decimal('0.01'):  # More than 1 cent
            result['variances'].append({
                'type': 'price',
                'field': 'total',
                'po_value': float(po_total),
                'invoice_value': float(invoice_total),
                'variance': float(variance),
                'variance_pct': float(variance_pct)
            })
            result['total_variance'] = abs(variance)
            
            # Check if within tolerance
            if abs(variance) <= TOLERANCE_AMOUNT or abs(variance_pct) <= TOLERANCE_PCT:
                result['status'] = self.MATCH_VARIANCE
                result['can_auto_approve'] = True
                result['messages'].append(
                    f'Variance of {variance:.2f} ({variance_pct:.2f}%) is within acceptable tolerance'
                )
            else:
                result['status'] = self.MATCH_VARIANCE
                result['can_auto_approve'] = False
                result['messages'].append(
                    f'Variance of {variance:.2f} ({variance_pct:.2f}%) exceeds tolerance - manual approval required'
                )
        else:
            result['status'] = self.MATCH_MATCHED
            result['can_auto_approve'] = True
            result['messages'].append('Invoice matches PO exactly')
        
        # Update match fields
        self.three_way_match_status = result['status']
        self.match_variance_amount = result['total_variance']
        self.match_variance_notes = '; '.join(result['messages'])
        self.match_performed_at = timezone.now()
        
        # Auto-approve if within tolerance
        if result['can_auto_approve'] and self.approval_status == 'PENDING_APPROVAL':
            self.approval_status = 'APPROVED'
            result['messages'].append('Invoice auto-approved based on 3-way match')
        
        self.save()
        
        return result
    
    def paid_amount(self):
        """Return total amount paid via allocations (converted to invoice currency)"""
        from decimal import Decimal
        
        paid = Decimal('0.00')
        for alloc in self.payment_allocations.all():
            alloc_amount = alloc.amount
            
            # Check if payment currency differs from invoice currency
            if alloc.payment and alloc.payment.currency_id != self.currency_id:
                # Convert payment amount to invoice currency
                if alloc.current_exchange_rate and alloc.current_exchange_rate != Decimal("0"):
                    # Payment amount in invoice currency = payment amount / exchange rate
                    # (exchange rate is FROM invoice TO payment, so divide to go back)
                    alloc_amount = alloc.amount / alloc.current_exchange_rate
                else:
                    # No exchange rate available, try to fetch on the fly
                    try:
                        from finance.fx_services import get_exchange_rate
                        rate = get_exchange_rate(
                            from_currency=alloc.payment.currency,
                            to_currency=self.currency,
                            rate_date=alloc.payment.date,
                            rate_type="SPOT"
                        )
                        # Payment currency to invoice currency
                        alloc_amount = alloc.amount * rate
                    except:
                        pass  # Keep original amount if conversion fails
            
            paid += alloc_amount
        
        return paid
    
    def outstanding_amount(self):
        """Return unpaid balance (in invoice currency)"""
        return self.calculate_total() - self.paid_amount()


class APItem(models.Model):
    """AP Invoice Line Item"""
    invoice = models.ForeignKey(APInvoice, related_name="items", on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.ForeignKey(TaxRate, null=True, blank=True, on_delete=models.SET_NULL, related_name="ap_items")
    tax_country  = models.CharField(max_length=2, choices=TAX_COUNTRIES, null=True, blank=True)
    tax_category = models.CharField(max_length=16, choices=TAX_CATS, null=True, blank=True)
    
    class Meta:
        db_table = 'ap_apitem'  # NEW table name
    
    def __str__(self):
        return f"{self.invoice.number} - {self.description[:30]}"


# REMOVED: APInvoiceGLLine model - table dropped in migration 0015
# Kept as stub to prevent import errors in serializers
class APInvoiceGLLine(models.Model):
    """GL Distribution Line for AP Invoice with dynamic segment support
    
    Replaces the old single-account model with a flexible multi-segment system.
    Each distribution can have multiple segment assignments (Account, Department, Cost Center, etc.)
    """
    invoice = models.ForeignKey('APInvoice', on_delete=models.CASCADE, related_name='distributions')
    amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Distribution amount")
    description = models.CharField(max_length=500, blank=True, help_text="Description of this distribution")
    line_type = models.CharField(max_length=50, default='distribution', help_text="Type of GL line")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ap_invoice_distribution'
        ordering = ['id']
    
    def __str__(self):
        return f"Distribution #{self.id} - {self.invoice.number} - {self.amount}"


class APInvoiceDistributionSegment(models.Model):
    """Segment assignment for AP Invoice GL Distribution
    
    Links a distribution line to specific segment values for each segment type.
    Enables multi-dimensional GL coding (Account + Department + Cost Center + Project + etc.)
    """
    distribution = models.ForeignKey(APInvoiceGLLine, on_delete=models.CASCADE, related_name='segments')
    segment_type = models.ForeignKey('segment.XX_SegmentType', on_delete=models.PROTECT, help_text="Segment type (Account, Department, etc.)")
    segment = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT, help_text="Specific segment value")
    
    class Meta:
        db_table = 'ap_invoice_distribution_segment'
        unique_together = [['distribution', 'segment_type']]  # One segment per type per distribution
        ordering = ['segment_type__segment_id']
    
    def __str__(self):
        return f"{self.segment_type.segment_name}: {self.segment.code}"


class APPayment(models.Model):
    """AP Payment - can be allocated to multiple invoices"""
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, blank=True, help_text="Supplier receiving the payment")
    reference = models.CharField(max_length=64, unique=True, null=True, blank=True, help_text="Payment reference number")
    date = models.DateField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text="Total payment amount")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="ap_payments_currency", null=True, blank=True, help_text="Payment currency (currency paid)")
    memo = models.CharField(max_length=255, blank=True, help_text="Payment memo/notes")
    bank_account = models.ForeignKey("finance.BankAccount", null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="ap_payments")
    period = models.ForeignKey('periods.FiscalPeriod', on_delete=models.PROTECT, null=True, blank=True, related_name='ap_payments', help_text="Fiscal period for this payment")
    posted_at = models.DateTimeField(null=True, blank=True)
    reconciled = models.BooleanField(default=False)
    reconciliation_ref = models.CharField(max_length=64, blank=True)
    reconciled_at = models.DateField(null=True, blank=True)
    gl_journal = models.ForeignKey("finance.JournalEntry", null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="ap_payment_source_new")
    payment_fx_rate = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    
    # FX gain/loss tracking fields
    invoice_currency = models.ForeignKey(
        Currency, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name="ap_payments_invoice_currency",
        help_text="Currency of the invoice(s) being paid - for FX tracking"
    )
    exchange_rate = models.DecimalField(
        max_digits=18, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Exchange rate from invoice currency to payment currency (for FX gain/loss)"
    )
    
    # Legacy support - keep for backward compatibility but make optional
    invoice = models.ForeignKey(APInvoice, related_name="payments_legacy", on_delete=models.PROTECT, 
                                null=True, blank=True, help_text="DEPRECATED: Use allocations instead")
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                 help_text="DEPRECATED: Use total_amount instead")
    
    class Meta:
        db_table = 'ap_appayment'
        ordering = ['-date', '-id']
    
    def __str__(self):
        return f"Payment {self.reference or 'N/A'} - {self.total_amount or 0}"
    
    def allocated_amount(self):
        """Return sum of all allocations"""
        from decimal import Decimal
        return self.allocations.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    
    def unallocated_amount(self):
        """Return unallocated amount"""
        from decimal import Decimal
        total = self.total_amount if self.total_amount is not None else Decimal('0.00')
        return total - self.allocated_amount()
    
    def update_exchange_rate_from_allocations(self):
        """
        Update invoice_currency and exchange_rate based on allocated invoices.
        If all allocations are to invoices in the same currency (different from payment currency),
        fetch and store the exchange rate for FX gain/loss calculations.
        """
        from decimal import Decimal
        
        allocations = self.allocations.all()
        if not allocations.exists():
            return
        
        # Get all unique invoice currencies from allocations
        invoice_currencies = set(
            alloc.invoice.currency for alloc in allocations if alloc.invoice
        )
        
        # If all invoices are in the same currency and it's different from payment currency
        if len(invoice_currencies) == 1:
            inv_currency = invoice_currencies.pop()
            
            if self.currency and inv_currency.id != self.currency.id:
                # Different currencies - fetch exchange rate
                self.invoice_currency = inv_currency
                
                try:
                    from finance.fx_services import get_exchange_rate
                    self.exchange_rate = get_exchange_rate(
                        from_currency=inv_currency,
                        to_currency=self.currency,
                        rate_date=self.date,
                        rate_type="SPOT"
                    )
                    self.save(update_fields=['invoice_currency', 'exchange_rate'])
                    print(f"Payment {self.reference}: Set exchange rate {inv_currency.code} -> {self.currency.code} = {self.exchange_rate}")
                except Exception as e:
                    print(f"Warning: Could not fetch exchange rate for payment {self.reference}: {e}")
            else:
                # Same currency - no FX rate needed
                self.invoice_currency = inv_currency
                self.exchange_rate = Decimal('1.000000')
                self.save(update_fields=['invoice_currency', 'exchange_rate'])
    
    def post_to_gl(self):
        """
        Post this payment to the General Ledger.
        Creates journal entry: DR Accounts Payable, CR Bank
        Handles multi-currency with FX gain/loss.
        Returns: (JournalEntry, created: bool, invoices_closed: list)
        """
        # Import here to avoid circular dependency
        from finance.services import post_ap_payment
        
        if self.gl_journal:
            # Already posted
            return self.gl_journal, False, []
        
        return post_ap_payment(self)


class APPaymentAllocation(models.Model):
    """Allocation of AP payment to specific invoices"""
    payment = models.ForeignKey(APPayment, related_name="allocations", on_delete=models.CASCADE)
    invoice = models.ForeignKey(APInvoice, related_name="payment_allocations", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=14, decimal_places=2, help_text="Amount allocated to this invoice")
    memo = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Currency tracking fields
    invoice_currency = models.ForeignKey(
        Currency, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name="ap_payment_allocations_invoice_currency",
        help_text="Currency of the invoice (copied from invoice at allocation time)"
    )
    current_exchange_rate = models.DecimalField(
        max_digits=18, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Exchange rate from invoice currency to payment currency at allocation time"
    )
    
    class Meta:
        db_table = 'ap_appaymentallocation'
        unique_together = [['payment', 'invoice']]
    
    def __str__(self):
        return f"{self.payment.reference} -> {self.invoice.number}: {self.amount}"
    
    def save(self, *args, **kwargs):
        """Auto-populate invoice_currency and current_exchange_rate on save"""
        if self.invoice and not self.invoice_currency:
            # Get invoice currency
            self.invoice_currency = self.invoice.currency
            
            # Calculate exchange rate if payment and invoice currencies differ
            if self.payment and self.payment.currency and self.invoice.currency:
                from_currency = self.invoice.currency
                to_currency = self.payment.currency
                
                # Only fetch exchange rate if currencies are different
                if from_currency.id != to_currency.id:
                    try:
                        from finance.fx_services import get_exchange_rate
                        self.current_exchange_rate = get_exchange_rate(
                            from_currency=from_currency,
                            to_currency=to_currency,
                            rate_date=self.payment.date,
                            rate_type="SPOT"
                        )
                    except Exception as e:
                        print(f"Warning: Could not fetch exchange rate: {e}")
                        self.current_exchange_rate = None
                else:
                    # Same currency, rate is 1.0
                    from decimal import Decimal
                    self.current_exchange_rate = Decimal('1.000000')
        
        super().save(*args, **kwargs)

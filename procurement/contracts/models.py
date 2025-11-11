"""
Contracts & Compliance Models

Implements comprehensive contract management:
- Contract register with value, term, renewal tracking
- Clause library with reusable templates
- SLA (Service Level Agreement) tracking
- Penalty and incentive management
- Renewal and expiry reminders
- Attachments and document management
- Approval workflow integration
- Audit trail and compliance tracking
"""

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import json


class ClauseLibrary(models.Model):
    """
    Reusable clause library for contracts.
    
    Contains standard clauses that can be referenced in contracts.
    """
    
    CLAUSE_CATEGORY_CHOICES = [
        ('GENERAL', 'General Terms'),
        ('PAYMENT', 'Payment Terms'),
        ('DELIVERY', 'Delivery Terms'),
        ('WARRANTY', 'Warranty'),
        ('LIABILITY', 'Liability & Indemnity'),
        ('CONFIDENTIALITY', 'Confidentiality'),
        ('TERMINATION', 'Termination'),
        ('DISPUTE', 'Dispute Resolution'),
        ('COMPLIANCE', 'Compliance & Regulatory'),
        ('SLA', 'Service Level Agreement'),
        ('IP', 'Intellectual Property'),
        ('DATA_PROTECTION', 'Data Protection'),
        ('FORCE_MAJEURE', 'Force Majeure'),
        ('OTHER', 'Other'),
    ]
    
    # Clause identification
    clause_code = models.CharField(max_length=50, unique=True, db_index=True,
                                  help_text="Unique clause code (e.g., PAY-NET30)")
    clause_title = models.CharField(max_length=200)
    clause_category = models.CharField(max_length=30, choices=CLAUSE_CATEGORY_CHOICES,
                                      db_index=True)
    
    # Clause content
    clause_text = models.TextField(help_text="Standard clause text with placeholders")
    placeholders = models.JSONField(default=list, blank=True,
                                   help_text="List of placeholders in clause text (e.g., {{SUPPLIER_NAME}})")
    
    # Metadata
    description = models.TextField(blank=True,
                                  help_text="When and how to use this clause")
    notes = models.TextField(blank=True)
    
    # Version control
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    
    # Audit trail
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, related_name='created_clauses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, related_name='updated_clauses')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['clause_category', 'clause_code']
        indexes = [
            models.Index(fields=['clause_category', 'is_active']),
        ]
        verbose_name = 'Clause Library'
        verbose_name_plural = 'Clause Libraries'
    
    def __str__(self):
        return f"{self.clause_code} - {self.clause_title}"


class Contract(models.Model):
    """
    Contract register with comprehensive tracking.
    
    Types:
    - Purchase contracts (with suppliers)
    - Sales contracts (with customers)
    - Service contracts
    - Master agreements
    - Framework agreements
    """
    
    CONTRACT_TYPE_CHOICES = [
        ('PURCHASE', 'Purchase Contract'),
        ('SALES', 'Sales Contract'),
        ('SERVICE', 'Service Contract'),
        ('MASTER', 'Master Agreement'),
        ('FRAMEWORK', 'Framework Agreement'),
        ('NDA', 'Non-Disclosure Agreement'),
        ('SLA', 'Service Level Agreement'),
        ('LICENSE', 'License Agreement'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('UNDER_REVIEW', 'Under Review'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('EXPIRING_SOON', 'Expiring Soon'),
        ('EXPIRED', 'Expired'),
        ('TERMINATED', 'Terminated'),
        ('RENEWED', 'Renewed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Auto-generated number: CTR-YYYYMM-NNNN
    contract_number = models.CharField(max_length=50, unique=True, db_index=True)
    contract_title = models.CharField(max_length=200)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES,
                                    db_index=True)
    
    # Party information
    # Polymorphic party reference (Supplier or Customer)
    party_content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT,
                                          limit_choices_to={'model__in': ['supplier', 'customer']})
    party_object_id = models.PositiveIntegerField()
    party = GenericForeignKey('party_content_type', 'party_object_id')
    
    # Contract dates
    contract_date = models.DateField(help_text="Contract signature date")
    effective_date = models.DateField(help_text="When contract becomes effective")
    expiry_date = models.DateField(help_text="Contract expiration date")
    
    # Contract value
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    total_value = models.DecimalField(max_digits=15, decimal_places=2,
                                     help_text="Total contract value")
    annual_value = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                      help_text="Annual contract value")
    
    # Term and renewal
    term_months = models.IntegerField(help_text="Contract term in months")
    auto_renewal = models.BooleanField(default=False,
                                      help_text="Auto-renew on expiry")
    renewal_notice_days = models.IntegerField(default=90,
                                             help_text="Days notice required for renewal/termination")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                            default='DRAFT', db_index=True)
    
    # Renewal tracking
    is_renewable = models.BooleanField(default=True)
    renewed_from = models.ForeignKey('self', on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='renewals',
                                    help_text="Previous contract if this is a renewal")
    
    # Termination
    is_terminated = models.BooleanField(default=False)
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)
    terminated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='terminated_contracts')
    
    # Responsible parties
    contract_owner = models.ForeignKey(User, on_delete=models.SET_NULL,
                                      null=True, related_name='owned_contracts',
                                      help_text="Internal contract owner/manager")
    legal_reviewer = models.ForeignKey(User, on_delete=models.SET_NULL,
                                      null=True, blank=True,
                                      related_name='reviewed_contracts',
                                      help_text="Legal team reviewer")
    
    # Approval workflow
    approval_status = models.CharField(max_length=20, default='PENDING',
                                      choices=[
                                          ('PENDING', 'Pending'),
                                          ('APPROVED', 'Approved'),
                                          ('REJECTED', 'Rejected'),
                                      ])
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='approved_contracts')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Document reference
    original_document = models.FileField(upload_to='contracts/', null=True, blank=True,
                                        help_text="Original signed contract document")
    
    # Reminders
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_date = models.DateField(null=True, blank=True)
    
    # Notes
    description = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal notes (use ContractNote for audit trail)")
    
    # Audit trail
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, related_name='created_contracts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, related_name='updated_contracts')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-contract_date', '-contract_number']
        indexes = [
            models.Index(fields=['status', 'expiry_date']),
            models.Index(fields=['contract_type', 'status']),
            models.Index(fields=['expiry_date', 'status']),
            models.Index(fields=['party_content_type', 'party_object_id']),
        ]
        verbose_name = 'Contract'
        verbose_name_plural = 'Contracts'
    
    def __str__(self):
        return f"{self.contract_number} - {self.contract_title}"
    
    def save(self, *args, **kwargs):
        if not self.contract_number:
            self.contract_number = self.generate_contract_number()
        
        # Calculate annual value
        if self.term_months > 0:
            self.annual_value = (self.total_value / self.term_months) * 12
        
        # Update status based on dates
        self.update_status()
        
        super().save(*args, **kwargs)
    
    def generate_contract_number(self):
        """Generate contract number: CTR-YYYYMM-NNNN"""
        today = timezone.now()
        prefix = f"CTR-{today.year}{today.month:02d}"
        last_contract = Contract.objects.filter(
            contract_number__startswith=prefix
        ).order_by('-contract_number').first()
        
        if last_contract:
            last_num = int(last_contract.contract_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def update_status(self):
        """Update contract status based on current date"""
        today = timezone.now().date()
        
        if self.is_terminated:
            self.status = 'TERMINATED'
        elif today < self.effective_date:
            if self.approval_status == 'APPROVED':
                self.status = 'APPROVED'
        elif today >= self.effective_date and today < self.expiry_date:
            # Check if expiring soon (within renewal notice period)
            days_until_expiry = (self.expiry_date - today).days
            if days_until_expiry <= self.renewal_notice_days:
                self.status = 'EXPIRING_SOON'
            else:
                self.status = 'ACTIVE'
        elif today >= self.expiry_date:
            self.status = 'EXPIRED'
    
    def get_days_until_expiry(self):
        """Calculate days until contract expires"""
        today = timezone.now().date()
        if self.expiry_date > today:
            return (self.expiry_date - today).days
        return 0
    
    def is_expiring_soon(self):
        """Check if contract is expiring within renewal notice period"""
        days_until_expiry = self.get_days_until_expiry()
        return 0 < days_until_expiry <= self.renewal_notice_days
    
    def approve(self, user):
        """Approve contract"""
        if self.status not in ['DRAFT', 'UNDER_REVIEW', 'PENDING_APPROVAL']:
            raise ValidationError("Cannot approve contract in current status")
        
        self.approval_status = 'APPROVED'
        self.approved_by = user
        self.approved_date = timezone.now()
        self.status = 'APPROVED'
        self.save()
    
    def activate(self, user):
        """Activate contract (on effective date)"""
        if self.approval_status != 'APPROVED':
            raise ValidationError("Contract must be approved before activation")
        
        today = timezone.now().date()
        if today < self.effective_date:
            raise ValidationError("Cannot activate contract before effective date")
        
        self.status = 'ACTIVE'
        self.save()
    
    def terminate(self, user, reason):
        """Terminate contract"""
        if self.status in ['EXPIRED', 'TERMINATED', 'CANCELLED']:
            raise ValidationError("Contract already ended")
        
        self.is_terminated = True
        self.termination_date = timezone.now().date()
        self.termination_reason = reason
        self.terminated_by = user
        self.status = 'TERMINATED'
        self.save()
    
    def renew(self, user, new_expiry_date, new_value=None):
        """
        Renew contract by creating new contract.
        
        Returns new Contract object.
        """
        if self.status != 'ACTIVE' and not self.is_expiring_soon():
            raise ValidationError("Can only renew active or expiring contracts")
        
        # Create renewed contract
        new_contract = Contract.objects.create(
            contract_title=f"{self.contract_title} (Renewed)",
            contract_type=self.contract_type,
            party_content_type=self.party_content_type,
            party_object_id=self.party_object_id,
            contract_date=timezone.now().date(),
            effective_date=self.expiry_date + timedelta(days=1),
            expiry_date=new_expiry_date,
            currency=self.currency,
            total_value=new_value or self.total_value,
            term_months=self.term_months,
            auto_renewal=self.auto_renewal,
            renewal_notice_days=self.renewal_notice_days,
            status='APPROVED',
            is_renewable=True,
            renewed_from=self,
            contract_owner=self.contract_owner,
            legal_reviewer=self.legal_reviewer,
            approval_status='APPROVED',
            approved_by=user,
            approved_date=timezone.now(),
            created_by=user,
        )
        
        # Mark current contract as renewed
        self.status = 'RENEWED'
        self.save()
        
        return new_contract


class ContractClause(models.Model):
    """
    Specific clause in a contract.
    Can reference ClauseLibrary or be custom.
    """
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE,
                                related_name='clauses')
    clause_number = models.CharField(max_length=20,
                                    help_text="Clause numbering (e.g., 3.2.1)")
    
    # Reference to clause library (optional)
    library_clause = models.ForeignKey(ClauseLibrary, on_delete=models.SET_NULL,
                                      null=True, blank=True,
                                      related_name='contract_clauses',
                                      help_text="Reference to standard clause")
    
    # Clause content
    clause_title = models.CharField(max_length=200)
    clause_text = models.TextField(help_text="Actual clause text in contract")
    
    # Clause importance
    is_critical = models.BooleanField(default=False,
                                     help_text="Critical clause requiring special attention")
    is_negotiable = models.BooleanField(default=True,
                                       help_text="Whether clause is negotiable")
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['clause_number']
        verbose_name = 'Contract Clause'
        verbose_name_plural = 'Contract Clauses'
    
    def __str__(self):
        return f"{self.contract.contract_number} - Clause {self.clause_number}: {self.clause_title}"


class ContractSLA(models.Model):
    """
    Service Level Agreement metrics and tracking.
    """
    
    MEASUREMENT_TYPE_CHOICES = [
        ('UPTIME', 'Uptime %'),
        ('RESPONSE_TIME', 'Response Time'),
        ('RESOLUTION_TIME', 'Resolution Time'),
        ('AVAILABILITY', 'Availability %'),
        ('PERFORMANCE', 'Performance Score'),
        ('QUALITY', 'Quality Score'),
        ('DELIVERY', 'Delivery Time'),
        ('CUSTOM', 'Custom Metric'),
    ]
    
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ANNUAL', 'Annual'),
    ]
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE,
                                related_name='slas')
    
    # SLA details
    sla_name = models.CharField(max_length=200)
    measurement_type = models.CharField(max_length=30, choices=MEASUREMENT_TYPE_CHOICES)
    description = models.TextField()
    
    # Target metrics
    target_value = models.DecimalField(max_digits=10, decimal_places=2,
                                      help_text="Target value/percentage")
    minimum_value = models.DecimalField(max_digits=10, decimal_places=2,
                                       help_text="Minimum acceptable value")
    
    # Measurement
    measurement_unit = models.CharField(max_length=50,
                                       help_text="Unit of measurement (%, seconds, hours, etc.)")
    measurement_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    # Current performance
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                       help_text="Current performance value")
    last_measured_date = models.DateField(null=True, blank=True)
    
    # Compliance tracking
    is_compliant = models.BooleanField(default=True)
    breach_count = models.IntegerField(default=0,
                                      help_text="Number of SLA breaches")
    
    # Penalties and remedies
    has_penalty = models.BooleanField(default=False)
    penalty_description = models.TextField(blank=True)
    
    # Active status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['contract', 'sla_name']
        verbose_name = 'Contract SLA'
        verbose_name_plural = 'Contract SLAs'
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.sla_name}"
    
    def check_compliance(self):
        """Check if current value meets minimum threshold"""
        if self.current_value < self.minimum_value:
            self.is_compliant = False
            self.breach_count += 1
        else:
            self.is_compliant = True
        self.save()
    
    def record_measurement(self, value, measured_date=None):
        """Record SLA measurement"""
        self.current_value = value
        self.last_measured_date = measured_date or timezone.now().date()
        self.check_compliance()


class ContractPenalty(models.Model):
    """
    Penalty or incentive clause in contract.
    """
    
    PENALTY_TYPE_CHOICES = [
        ('PENALTY', 'Penalty'),
        ('LIQUIDATED_DAMAGES', 'Liquidated Damages'),
        ('INCENTIVE', 'Incentive/Bonus'),
        ('DISCOUNT', 'Discount'),
    ]
    
    TRIGGER_TYPE_CHOICES = [
        ('SLA_BREACH', 'SLA Breach'),
        ('LATE_DELIVERY', 'Late Delivery'),
        ('QUALITY_ISSUE', 'Quality Issue'),
        ('EARLY_DELIVERY', 'Early Delivery (Incentive)'),
        ('PERFORMANCE_BONUS', 'Performance Bonus'),
        ('OTHER', 'Other'),
    ]
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE,
                                related_name='penalties')
    
    # Penalty details
    penalty_type = models.CharField(max_length=30, choices=PENALTY_TYPE_CHOICES)
    trigger_type = models.CharField(max_length=30, choices=TRIGGER_TYPE_CHOICES)
    description = models.TextField()
    
    # SLA reference (if applicable)
    related_sla = models.ForeignKey(ContractSLA, on_delete=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='penalties')
    
    # Penalty calculation
    calculation_method = models.CharField(max_length=200,
                                         help_text="How penalty is calculated")
    penalty_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                        help_text="Fixed penalty amount (if applicable)")
    penalty_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                            help_text="Percentage of contract value (if applicable)")
    
    # Caps
    max_penalty_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                            help_text="Maximum total penalty")
    max_penalty_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                 help_text="Max penalty as % of contract value")
    
    # Tracking
    total_penalties_applied = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    penalty_count = models.IntegerField(default=0)
    
    # Active status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['contract', 'penalty_type']
        verbose_name = 'Contract Penalty'
        verbose_name_plural = 'Contract Penalties'
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.get_penalty_type_display()}: {self.description[:50]}"
    
    def apply_penalty(self, amount, notes=''):
        """Apply penalty and track total"""
        self.total_penalties_applied += amount
        self.penalty_count += 1
        self.save()
        
        # Create penalty instance
        ContractPenaltyInstance.objects.create(
            penalty=self,
            applied_date=timezone.now().date(),
            penalty_amount=amount,
            notes=notes,
        )


class ContractPenaltyInstance(models.Model):
    """
    Individual instance of penalty being applied.
    """
    
    penalty = models.ForeignKey(ContractPenalty, on_delete=models.CASCADE,
                               related_name='instances')
    
    applied_date = models.DateField()
    penalty_amount = models.DecimalField(max_digits=15, decimal_places=2)
    notes = models.TextField(blank=True)
    
    # Invoice adjustment (if linked)
    invoice_reference = models.CharField(max_length=100, blank=True)
    is_applied_to_invoice = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-applied_date']
        verbose_name = 'Penalty Instance'
        verbose_name_plural = 'Penalty Instances'
    
    def __str__(self):
        return f"{self.penalty.contract.contract_number} - {self.applied_date} - {self.penalty_amount}"


class ContractRenewal(models.Model):
    """
    Contract renewal tracking and reminder.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('UNDER_NEGOTIATION', 'Under Negotiation'),
        ('APPROVED', 'Approved for Renewal'),
        ('RENEWED', 'Renewed'),
        ('NOT_RENEWED', 'Not Renewed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE,
                                related_name='renewal_records')
    
    # Renewal details
    renewal_date = models.DateField(help_text="Date renewal was initiated")
    proposed_expiry_date = models.DateField(help_text="Proposed new expiry date")
    proposed_value = models.DecimalField(max_digits=15, decimal_places=2,
                                        help_text="Proposed contract value")
    
    # Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES,
                            default='PENDING')
    
    # Decision
    decision_date = models.DateField(null=True, blank=True)
    decision_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='contract_renewal_decisions')
    decision_notes = models.TextField(blank=True)
    
    # Renewed contract reference
    renewed_contract = models.ForeignKey(Contract, on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='renewal_source',
                                        help_text="New contract created from renewal")
    
    # Audit trail
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, related_name='created_renewals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-renewal_date']
        verbose_name = 'Contract Renewal'
        verbose_name_plural = 'Contract Renewals'
    
    def __str__(self):
        return f"{self.contract.contract_number} - Renewal {self.renewal_date}"


class ContractAttachment(models.Model):
    """
    Document attachments for contracts.
    """
    
    DOCUMENT_TYPE_CHOICES = [
        ('CONTRACT', 'Main Contract Document'),
        ('AMENDMENT', 'Amendment'),
        ('EXHIBIT', 'Exhibit/Appendix'),
        ('CORRESPONDENCE', 'Correspondence'),
        ('INVOICE', 'Invoice'),
        ('REPORT', 'Report'),
        ('CERTIFICATE', 'Certificate'),
        ('OTHER', 'Other'),
    ]
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE,
                                related_name='attachments')
    
    # Document details
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    document_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # File
    file = models.FileField(upload_to='contract_attachments/')
    file_size = models.IntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=50, help_text="MIME type")
    
    # Version control
    version = models.CharField(max_length=20, default='1.0')
    is_latest = models.BooleanField(default=True)
    
    # Metadata
    document_date = models.DateField(null=True, blank=True)
    
    # Audit trail
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, related_name='uploaded_contract_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Contract Attachment'
        verbose_name_plural = 'Contract Attachments'
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.document_name}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class ContractNote(models.Model):
    """
    Notes and comments on contracts for audit trail.
    """
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE,
                                related_name='notes')
    
    note_type = models.CharField(max_length=30, default='GENERAL',
                                choices=[
                                    ('GENERAL', 'General Note'),
                                    ('NEGOTIATION', 'Negotiation Note'),
                                    ('AMENDMENT', 'Amendment Note'),
                                    ('REVIEW', 'Review Comment'),
                                    ('COMPLIANCE', 'Compliance Note'),
                                    ('RENEWAL', 'Renewal Note'),
                                ])
    
    note_text = models.TextField()
    
    # Audit trail
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contract Note'
        verbose_name_plural = 'Contract Notes'
    
    def __str__(self):
        return f"{self.contract.contract_number} - Note {self.created_at.strftime('%Y-%m-%d')}"

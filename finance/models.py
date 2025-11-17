from django.db import models, transaction
from core.models import Currency, TaxRate
from simple_history.models import HistoricalRecords
from django.utils import timezone
from django.core.exceptions import ValidationError
TAX_COUNTRIES = [("AE","UAE"),("SA","KSA"),("EG","Egypt"),("IN","India")]
TAX_CATS = [("STANDARD","Standard"),("ZERO","Zero"),("EXEMPT","Exempt"),("RC","Reverse Charge")]
class BankAccount(models.Model):
    name = models.CharField(max_length=128)
    account_code = models.CharField(max_length=32, blank=True)  # map to GL cash/bank account code (e.g., "1000")
    iban = models.CharField(max_length=64, blank=True)
    swift = models.CharField(max_length=32, blank=True)
    currency = models.ForeignKey("core.Currency", on_delete=models.PROTECT, null=True, blank=True)
    active = models.BooleanField(default=True)
    history = HistoricalRecords()
    def __str__(self):
        return self.name


class JournalEntry(models.Model):
    date = models.DateField()
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    memo = models.CharField(max_length=255, blank=True)
    posted = models.BooleanField(default=False)
    period = models.ForeignKey('periods.FiscalPeriod', on_delete=models.PROTECT, null=True, blank=True, related_name='journal_entries', help_text="Fiscal period for this journal entry")
    history = HistoricalRecords()

class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, related_name="lines", on_delete=models.CASCADE)
    account = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)


class JournalLineSegment(models.Model):
    """
    Stores segment assignments for journal lines.
    Each journal line must have one segment from each required segment type.
    Only child segments are allowed (node_type='child').
    """
    journal_line = models.ForeignKey(JournalLine, related_name="segments", on_delete=models.CASCADE)
    segment_type = models.ForeignKey('segment.XX_SegmentType', on_delete=models.PROTECT)
    segment = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT)
    
    class Meta:
        db_table = "JOURNAL_LINE_SEGMENT"
        unique_together = ("journal_line", "segment_type")
        indexes = [
            models.Index(fields=["journal_line", "segment_type"]),
            models.Index(fields=["segment"]),
        ]
    
    def clean(self):
        """Validate that only child segments are assigned"""
        if self.segment and self.segment.node_type != 'child':
            raise ValidationError(
                f"Only child segments can be assigned to journal lines. "
                f"Segment '{self.segment.code}' is a '{self.segment.node_type}' type."
            )
        
        # Validate that segment belongs to the correct segment_type
        if self.segment and self.segment.segment_type_id != self.segment_type_id:
            raise ValidationError(
                f"Segment '{self.segment.code}' does not belong to segment type '{self.segment_type.segment_name}'"
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"JL#{self.journal_line_id} - {self.segment_type.segment_name}: {self.segment.code}"




class CorporateTaxRule(models.Model):
    COUNTRY_CHOICES = [("AE","UAE"),("SA","KSA"),("EG","Egypt"),("IN","India")]
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
    rate = models.DecimalField(max_digits=6, decimal_places=3, help_text="Percent, e.g., 9 = 9%")
    threshold = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True,
                                    help_text="Optional profit threshold for tax applicability")
    active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.country} CorpTax {self.rate}%"

class CorporateTaxFiling(models.Model):
   STATUS = [("ACCRUED","Accrued"),("FILED","Filed (locked)"),("REVERSED","Reversed")]
   country = models.CharField(max_length=2, choices=[("AE","UAE"),("SA","KSA"),("EG","Egypt"),("IN","India")])
   period_start = models.DateField()
   period_end   = models.DateField()
   organization_id = models.IntegerField(null=True, blank=True)  # optional org scope (int to avoid hard FK)
   accrual_journal = models.OneToOneField("JournalEntry", null=True, blank=True, on_delete=models.SET_NULL, related_name="corp_tax_accrual")
   reversal_journal = models.OneToOneField("JournalEntry", null=True, blank=True, on_delete=models.SET_NULL, related_name="corp_tax_reversal")
   status = models.CharField(max_length=16, choices=STATUS, default="ACCRUED")
   filed_at = models.DateTimeField(null=True, blank=True)
   notes = models.CharField(max_length=255, blank=True)
   history = HistoricalRecords()
   class Meta:
       unique_together = ("country","period_start","period_end","organization_id")


# ============================================================================
# INVOICE APPROVAL WORKFLOW MODELS
# ============================================================================

class InvoiceApprovalStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    POSTED = "POSTED", "Posted"


class InvoiceApproval(models.Model):
    """Approval records for AR/AP invoices"""
    # Polymorphic reference to either AR or AP invoice
    invoice_type = models.CharField(max_length=2, choices=[('AR', 'AR Invoice'), ('AP', 'AP Invoice')])
    invoice_id = models.IntegerField()
    
    status = models.CharField(max_length=20, choices=InvoiceApprovalStatus.choices, 
                             default=InvoiceApprovalStatus.PENDING_APPROVAL)
    submitted_by = models.CharField(max_length=128, help_text="User who submitted for approval")
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    approver = models.CharField(max_length=128, blank=True, help_text="User who approved/rejected")
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    
    comments = models.TextField(blank=True, help_text="Approval/rejection comments")
    approval_level = models.IntegerField(default=1, help_text="Level in multi-level approval chain")
    
    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['invoice_type', 'invoice_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.invoice_type} Invoice #{self.invoice_id} - {self.status}"


class SegmentAssignmentRule(models.Model):
    """
    Rules for auto-assigning segments to GL distributions.
    Used when posting invoices/payments to automatically determine segment assignments.
    """
    
    # Rule identification
    name = models.CharField(max_length=255, help_text="Rule name/description")
    priority = models.IntegerField(default=100, help_text="Lower number = higher priority")
    is_active = models.BooleanField(default=True)
    
    # Conditions (all are optional - most specific rule wins)
    customer = models.ForeignKey('ar.Customer', on_delete=models.CASCADE, null=True, blank=True,
                                 help_text="Apply to specific customer")
    supplier = models.ForeignKey('ap.Supplier', on_delete=models.CASCADE, null=True, blank=True,
                                help_text="Apply to specific supplier")
    
    # Account segment that triggers this rule
    account_segment = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                       related_name='assignment_rules_for_account',
                                       help_text="When this account is used, apply these segment assignments")
    
    # Segment assignments (required segments)
    department_segment = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                          related_name='assignment_rules_dept',
                                          null=True, blank=True,
                                          help_text="Department to assign")
    
    cost_center_segment = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                           related_name='assignment_rules_cc',
                                           null=True, blank=True,
                                           help_text="Cost center to assign")
    
    project_segment = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                       related_name='assignment_rules_proj',
                                       null=True, blank=True,
                                       help_text="Project to assign")
    
    product_segment = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                       related_name='assignment_rules_prod',
                                       null=True, blank=True,
                                       help_text="Product to assign")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'finance_segment_assignment_rule'
        ordering = ['priority', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'priority']),
            models.Index(fields=['customer', 'account_segment']),
            models.Index(fields=['supplier', 'account_segment']),
        ]
    
    def __str__(self):
        entity = f"Customer {self.customer.name}" if self.customer else \
                 f"Supplier {self.supplier.name}" if self.supplier else "Default"
        return f"{self.name} ({entity} → {self.account_segment.code})"
    
    def get_segment_assignments(self):
        """Return dict of segment type ID to segment ID for this rule"""
        assignments = {}
        
        # Account is always included
        account_type_id = self.account_segment.segment_type_id
        assignments[account_type_id] = self.account_segment.id
        
        # Add other segments if specified
        if self.department_segment:
            dept_type_id = self.department_segment.segment_type_id
            assignments[dept_type_id] = self.department_segment.id
        
        if self.cost_center_segment:
            cc_type_id = self.cost_center_segment.segment_type_id
            assignments[cc_type_id] = self.cost_center_segment.id
        
        if self.project_segment:
            proj_type_id = self.project_segment.segment_type_id
            assignments[proj_type_id] = self.project_segment.id
        
        if self.product_segment:
            prod_type_id = self.product_segment.segment_type_id
            assignments[prod_type_id] = self.product_segment.id
        
        return assignments


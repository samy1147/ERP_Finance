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


class InvoiceStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    POSTED = "POSTED", "Posted"
    REVERSED = "REVERSED", "Reversed"

class LockOnPostedMixin(models.Model):
    """
    Prevent updates once 'status' is POSTED, except controlled fields explicitly allowed.
    """
    status = models.CharField(
        max_length=16, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT, db_index=True
    )

    class Meta:
        abstract = True

    # Fields allowed to change after POSTED (e.g., add reversal link or system timestamps)
    _POSTED_EDITABLE_FIELDS = {"status", "reversal_ref_id", "updated_at"}

    def _is_posted_locked_update(self):
        if not self.pk:
            return False  # create always ok
        # Compare DB state vs new state
        Model = self.__class__
        db_state = Model.objects.only(*[f.name for f in Model._meta.fields]).get(pk=self.pk)
        
        # Check if the OLD status (in DB) is POSTED
        if getattr(db_state, "status", None) != InvoiceStatus.POSTED:
            return False  # Old status not POSTED, no restriction
        
        # Old status IS POSTED - check for protected field changes
        for field in Model._meta.fields:
            fname = field.name
            if fname in self._POSTED_EDITABLE_FIELDS:
                continue
            if getattr(db_state, fname) != getattr(self, fname):
                return True
        return False

    def save(self, *args, **kwargs):
        if self._is_posted_locked_update():
            raise ValidationError("Posted documents are read-only. Use reversal API.")
        super().save(*args, **kwargs)


class Invoice(LockOnPostedMixin):
    customer = models.ForeignKey("ar.Customer", on_delete=models.PROTECT)  # Changed from crm.Customer to ar.Customer
    invoice_no = models.CharField(max_length=64, unique=True)
    currency = models.CharField(max_length=8)
    total_net = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_gross = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    posted_at = models.DateTimeField(null=True, blank=True)
    reversal_ref = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="reversals")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "customer"]),
        ]

    # ---------- Helper flags ----------
    def has_lines(self):
        return self.lines.exists()

    def any_line_missing_account_or_tax(self):
        return self.lines.filter(models.Q(account__isnull=True) | models.Q(tax_code__isnull=True)).exists()

    def is_zero_totals(self):
        return (self.total_net or 0) == 0 and (self.total_tax or 0) == 0 and (self.total_gross or 0) == 0

    # Recompute totals from lines (call before posting)
    def recompute_totals(self):
        agg = self.lines.aggregate(
            net=models.Sum("amount_net"), tax=models.Sum("tax_amount"), gross=models.Sum("amount_gross")
        )
        self.total_net = agg["net"] or 0
        self.total_tax = agg["tax"] or 0
        self.total_gross = agg["gross"] or 0

    def clean(self):
        """
        Base validation (runs on full_clean and admin/forms). Posting-time checks are in service.
        """
        if self.status == InvoiceStatus.POSTED and self.reversal_ref_id:
            raise ValidationError("A posted invoice cannot reference a reversal. Use reversal on the original.")
        super().clean()


class TaxCode(models.Model):
    code = models.CharField(max_length=32, unique=True)
    rate = models.DecimalField(max_digits=6, decimal_places=4)  # e.g., 0.0500 for 5%

class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="lines", on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    account = models.ForeignKey('segment.XX_Segment', null=True, blank=True, on_delete=models.PROTECT)
    tax_code = models.ForeignKey(TaxCode, null=True, blank=True, on_delete=models.PROTECT)

    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    amount_net = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    amount_gross = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    def recompute(self):
        from decimal import Decimal
        net = (self.quantity or 0) * (self.unit_price or 0)
        rate = self.tax_code.rate if self.tax_code_id else Decimal('0')
        tax = (net * rate).quantize(Decimal('0.01'))
        self.amount_net = net
        self.tax_amount = tax
        self.amount_gross = net + tax

    def save(self, *args, **kwargs):
        self.recompute()
        super().save(*args, **kwargs)


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


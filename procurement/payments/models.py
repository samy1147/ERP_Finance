"""
Payments & Finance Integration Models

Implements:
- AP Payment Batches with push to Finance module
- Tax Configuration for VAT/GST periodization (AE/KSA/EG/IN)
- Tax rates: standard, zero, exempt, reverse charge
- Corporate tax P&L integration
- Payment reconciliation back from Finance

Countries Supported:
- AE (UAE): 5% Standard VAT
- KSA (Saudi Arabia): 15% Standard VAT
- EG (Egypt): 14% Standard VAT
- IN (India): 18% GST (CGST + SGST)
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
import json


class TaxJurisdiction(models.Model):
    """
    Tax jurisdiction configuration for different countries.
    
    Supports:
    - UAE (AE): VAT 5%
    - Saudi Arabia (KSA): VAT 15%
    - Egypt (EG): VAT 14%
    - India (IN): GST 18% (CGST+SGST)
    """
    
    TAX_SYSTEM_CHOICES = [
        ('VAT', 'Value Added Tax'),
        ('GST', 'Goods and Services Tax'),
        ('SALES_TAX', 'Sales Tax'),
    ]
    
    # ISO country code
    country_code = models.CharField(max_length=3, unique=True, db_index=True,
                                   help_text="ISO country code (AE, KSA, EG, IN, etc.)")
    country_name = models.CharField(max_length=100)
    
    # Tax system type
    tax_system = models.CharField(max_length=20, choices=TAX_SYSTEM_CHOICES)
    
    # Standard tax rate
    standard_rate = models.DecimalField(max_digits=5, decimal_places=2,
                                       help_text="Standard tax rate as percentage")
    
    # Tax authority
    tax_authority_name = models.CharField(max_length=200,
                                         help_text="Name of tax authority")
    tax_registration_number = models.CharField(max_length=100, blank=True,
                                              help_text="Company's tax registration number")
    
    # Periodization settings
    tax_period = models.CharField(max_length=20, default='MONTHLY',
                                 choices=[
                                     ('MONTHLY', 'Monthly'),
                                     ('QUARTERLY', 'Quarterly'),
                                     ('ANNUAL', 'Annual'),
                                 ])
    
    # Currency
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    
    # Active status
    is_active = models.BooleanField(default=True)
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['country_code']
        verbose_name = 'Tax Jurisdiction'
        verbose_name_plural = 'Tax Jurisdictions'
    
    def __str__(self):
        return f"{self.country_name} ({self.country_code}) - {self.get_tax_system_display()}"


class TaxRate(models.Model):
    """
    Tax rate configuration with support for different rate types.
    
    Rate Types:
    - STANDARD: Normal tax rate
    - ZERO: Zero-rated (0%)
    - EXEMPT: Tax-exempt
    - REVERSE_CHARGE: Reverse charge mechanism
    - REDUCED: Reduced rate (for specific goods/services)
    """
    
    RATE_TYPE_CHOICES = [
        ('STANDARD', 'Standard Rate'),
        ('ZERO', 'Zero-Rated'),
        ('EXEMPT', 'Tax Exempt'),
        ('REVERSE_CHARGE', 'Reverse Charge'),
        ('REDUCED', 'Reduced Rate'),
    ]
    
    jurisdiction = models.ForeignKey(TaxJurisdiction, on_delete=models.CASCADE,
                                    related_name='tax_rates')
    
    # Rate details
    rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, db_index=True)
    rate_code = models.CharField(max_length=20, db_index=True,
                                help_text="Short code (e.g., STD, ZR, EX, RC)")
    rate_name = models.CharField(max_length=100)
    rate_percentage = models.DecimalField(max_digits=5, decimal_places=2,
                                         help_text="Tax rate as percentage")
    
    # Description and applicability
    description = models.TextField(blank=True)
    applicable_to = models.CharField(max_length=200, blank=True,
                                    help_text="What this rate applies to")
    
    # GL Account mapping for tax collection
    tax_payable_account = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                           related_name='tax_payable_rates',
                                           help_text="Tax payable GL account")
    tax_receivable_account = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                              related_name='tax_receivable_rates',
                                              null=True, blank=True,
                                              help_text="Tax receivable GL account (for reverse charge)")
    
    # Effective dates
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    
    # Active status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False,
                                    help_text="Default rate for this jurisdiction and type")
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['jurisdiction', 'rate_type', '-effective_from']
        indexes = [
            models.Index(fields=['jurisdiction', 'rate_type', 'is_active']),
            models.Index(fields=['rate_code', 'is_active']),
        ]
        unique_together = [('jurisdiction', 'rate_code')]
        verbose_name = 'Tax Rate'
        verbose_name_plural = 'Tax Rates'
    
    def __str__(self):
        return f"{self.jurisdiction.country_code} - {self.rate_code} ({self.rate_percentage}%)"
    
    def is_effective(self, date=None):
        """Check if rate is effective on given date"""
        if date is None:
            date = timezone.now().date()
        
        if date < self.effective_from:
            return False
        
        if self.effective_to and date > self.effective_to:
            return False
        
        return True


class TaxComponent(models.Model):
    """
    Tax component for composite taxes (e.g., GST = CGST + SGST).
    
    Used primarily for India GST where tax is split into:
    - CGST (Central GST): 9%
    - SGST (State GST): 9%
    - Total GST: 18%
    """
    
    COMPONENT_TYPE_CHOICES = [
        ('CGST', 'Central GST'),
        ('SGST', 'State GST'),
        ('IGST', 'Integrated GST'),
        ('UGST', 'Union Territory GST'),
        ('CESS', 'Cess'),
    ]
    
    tax_rate = models.ForeignKey(TaxRate, on_delete=models.CASCADE,
                                related_name='components')
    
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPE_CHOICES)
    component_name = models.CharField(max_length=100)
    component_percentage = models.DecimalField(max_digits=5, decimal_places=2,
                                              help_text="Component percentage of total tax")
    
    # GL Account for this component
    gl_account = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                  related_name='tax_components',
                                  help_text="GL account for this tax component")
    
    # Active status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['tax_rate', 'component_type']
        unique_together = [('tax_rate', 'component_type')]
        verbose_name = 'Tax Component'
        verbose_name_plural = 'Tax Components'
    
    def __str__(self):
        return f"{self.tax_rate.rate_code} - {self.component_type} ({self.component_percentage}%)"


class APPaymentBatch(models.Model):
    """
    AP Payment Batch that groups multiple AP payments for processing.
    
    Workflow:
    DRAFT → SUBMITTED → APPROVED → PROCESSING → POSTED_TO_FINANCE → RECONCILED
    
    Integration with Finance module:
    - Creates journal entries in finance.JournalEntry
    - Posts to AP payable accounts
    - Records bank account transactions
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('PROCESSING', 'Processing'),
        ('POSTED_TO_FINANCE', 'Posted to Finance'),
        ('RECONCILED', 'Reconciled'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHECK', 'Check'),
        ('CASH', 'Cash'),
        ('CREDIT_CARD', 'Credit Card'),
        ('ACH', 'ACH Transfer'),
        ('WIRE', 'Wire Transfer'),
    ]
    
    # Auto-generated number: PB-YYYYMM-NNNN
    batch_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Batch details
    batch_date = models.DateField(default=timezone.now)
    payment_date = models.DateField(help_text="Date when payments will be made")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Bank account
    bank_account = models.ForeignKey('finance.BankAccount', on_delete=models.PROTECT,
                                    related_name='payment_batches')
    
    # Currency and totals
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                      help_text="Total payment amount")
    payment_count = models.IntegerField(default=0,
                                       help_text="Number of payments in batch")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                            default='DRAFT', db_index=True)
    
    # Finance integration
    journal_entry = models.ForeignKey('finance.JournalEntry', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='payment_batch',
                                     help_text="Created journal entry in Finance")
    posted_to_finance_date = models.DateTimeField(null=True, blank=True)
    posted_to_finance_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                            null=True, blank=True,
                                            related_name='posted_payment_batches')
    
    # Reconciliation
    is_reconciled = models.BooleanField(default=False)
    reconciled_date = models.DateField(null=True, blank=True)
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='reconciled_payment_batches')
    
    # Approval workflow
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='submitted_payment_batches')
    submitted_date = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='approved_payment_batches')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Audit trail
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, related_name='created_payment_batches')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, related_name='updated_payment_batches')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_integration_appaymentbatch'
        ordering = ['-batch_date', '-batch_number']
        indexes = [
            models.Index(fields=['status', 'batch_date']),
            models.Index(fields=['payment_date', 'status']),
            models.Index(fields=['is_reconciled', 'status']),
        ]
        verbose_name = 'AP Payment Batch'
        verbose_name_plural = 'AP Payment Batches'
    
    def __str__(self):
        return f"{self.batch_number} - {self.payment_date} ({self.payment_count} payments)"
    
    def save(self, *args, **kwargs):
        if not self.batch_number:
            self.batch_number = self.generate_batch_number()
        super().save(*args, **kwargs)
    
    def generate_batch_number(self):
        """Generate batch number: PB-YYYYMM-NNNN"""
        today = timezone.now()
        prefix = f"PB-{today.year}{today.month:02d}"
        last_batch = APPaymentBatch.objects.filter(
            batch_number__startswith=prefix
        ).order_by('-batch_number').first()
        
        if last_batch:
            last_num = int(last_batch.batch_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def recalculate_totals(self):
        """Recalculate batch totals from payment lines"""
        lines = self.payment_lines.all()
        self.total_amount = sum(line.payment_amount for line in lines)
        self.payment_count = lines.count()
        self.save()
    
    def submit(self, user):
        """Submit batch for approval"""
        if self.status != 'DRAFT':
            raise ValidationError("Only draft batches can be submitted")
        
        if not self.payment_lines.exists():
            raise ValidationError("Cannot submit batch without payment lines")
        
        self.status = 'SUBMITTED'
        self.submitted_by = user
        self.submitted_date = timezone.now()
        self.save()
    
    def approve(self, user):
        """Approve batch"""
        if self.status != 'SUBMITTED':
            raise ValidationError("Only submitted batches can be approved")
        
        self.status = 'APPROVED'
        self.approved_by = user
        self.approved_date = timezone.now()
        self.save()
    
    def post_to_finance(self, user):
        """
        Post payment batch to Finance module.
        
        Creates journal entry:
        DR AP Payable (per supplier)
        CR Bank Account
        DR Tax components (if any withholding tax)
        """
        if self.status != 'APPROVED':
            raise ValidationError("Only approved batches can be posted to Finance")
        
        if self.journal_entry:
            # Already posted (idempotent)
            return self.journal_entry
        
        from finance.models import JournalEntry, JournalLine
        
        # Create journal entry
        journal_entry = JournalEntry.objects.create(
            entry_date=self.payment_date,
            reference=self.batch_number,
            description=f"AP Payment Batch {self.batch_number}",
            currency=self.currency,
            created_by=user,
        )
        
        # Create journal lines for each payment
        line_number = 1
        for payment_line in self.payment_lines.all():
            # DR AP Payable
            JournalLine.objects.create(
                journal_entry=journal_entry,
                line_number=line_number,
                account=payment_line.ap_invoice.supplier.payable_account,  # Assumes supplier has payable_account
                description=f"Payment to {payment_line.ap_invoice.supplier.name} - Invoice {payment_line.ap_invoice.invoice_number}",
                debit=payment_line.payment_amount,
                credit=0,
            )
            line_number += 1
            
            # Process tax withholding if any
            if payment_line.withholding_tax_amount > 0:
                # DR Withholding Tax (Asset)
                JournalLine.objects.create(
                    journal_entry=journal_entry,
                    line_number=line_number,
                    account=payment_line.withholding_tax_account,
                    description=f"Withholding tax on payment to {payment_line.ap_invoice.supplier.name}",
                    debit=payment_line.withholding_tax_amount,
                    credit=0,
                )
                line_number += 1
        
        # CR Bank Account (total payment)
        JournalLine.objects.create(
            journal_entry=journal_entry,
            line_number=line_number,
            account=self.bank_account.gl_account,
            description=f"Payment batch {self.batch_number}",
            debit=0,
            credit=self.total_amount,
        )
        
        # Link journal entry and update status
        self.journal_entry = journal_entry
        self.status = 'POSTED_TO_FINANCE'
        self.posted_to_finance_date = timezone.now()
        self.posted_to_finance_by = user
        self.save()
        
        # Update AP invoices to paid
        for payment_line in self.payment_lines.all():
            payment_line.mark_as_paid()
        
        return journal_entry
    
    def reconcile(self, user):
        """Mark batch as reconciled"""
        if self.status != 'POSTED_TO_FINANCE':
            raise ValidationError("Only posted batches can be reconciled")
        
        self.is_reconciled = True
        self.reconciled_date = timezone.now().date()
        self.reconciled_by = user
        self.status = 'RECONCILED'
        self.save()
    
    def reject(self, user, reason):
        """Reject batch"""
        if self.status not in ['SUBMITTED', 'APPROVED']:
            raise ValidationError("Cannot reject batch in current status")
        
        self.status = 'REJECTED'
        self.notes += f"\n[{timezone.now()}] Rejected by {user.username}: {reason}"
        self.save()
    
    def cancel(self, user):
        """Cancel batch"""
        if self.status in ['POSTED_TO_FINANCE', 'RECONCILED']:
            raise ValidationError("Cannot cancel posted or reconciled batches")
        
        self.status = 'CANCELLED'
        self.updated_by = user
        self.save()


class APPaymentLine(models.Model):
    """
    Individual payment line in AP Payment Batch.
    Links to AP Invoice and tracks payment details including tax withholding.
    """
    
    payment_batch = models.ForeignKey(APPaymentBatch, on_delete=models.CASCADE,
                                     related_name='payment_lines')
    line_number = models.IntegerField()
    
    # Invoice reference
    ap_invoice = models.ForeignKey('ap.APInvoice', on_delete=models.PROTECT,
                                  related_name='payment_lines')
    
    # Payment details
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2,
                                        help_text="Amount to pay (may be partial)")
    
    # Withholding tax (if applicable)
    withholding_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                              help_text="Withholding tax rate as percentage")
    withholding_tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                                 help_text="Withholding tax amount")
    withholding_tax_account = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                               null=True, blank=True,
                                               related_name='withholding_tax_lines',
                                               help_text="GL account for withholding tax")
    
    # Net payment (payment_amount - withholding_tax_amount)
    net_payment_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                            help_text="Net amount paid to supplier")
    
    # Discount taken
    discount_taken = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                        help_text="Early payment discount taken")
    
    # Payment status
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['line_number']
        unique_together = [('payment_batch', 'line_number')]
        indexes = [
            models.Index(fields=['ap_invoice', 'is_paid']),
        ]
        verbose_name = 'AP Payment Line'
        verbose_name_plural = 'AP Payment Lines'
    
    def __str__(self):
        return f"{self.payment_batch.batch_number} - Line {self.line_number} - {self.ap_invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        # Calculate net payment
        self.net_payment_amount = self.payment_amount - self.withholding_tax_amount - self.discount_taken
        super().save(*args, **kwargs)
    
    def mark_as_paid(self):
        """Mark payment line as paid and update AP invoice"""
        self.is_paid = True
        self.paid_date = self.payment_batch.payment_date
        self.save()
        
        # Update AP invoice payment status
        from ap.models import APPayment
        
        # Create AP Payment record
        APPayment.objects.create(
            invoice=self.ap_invoice,
            payment_date=self.paid_date,
            amount=self.payment_amount,
            payment_method=self.payment_batch.payment_method,
            reference_number=self.payment_batch.batch_number,
            notes=f"Paid via payment batch {self.payment_batch.batch_number}",
        )


class TaxPeriod(models.Model):
    """
    Tax period for VAT/GST reporting and periodization.
    
    Tracks tax collected and paid for a specific period.
    """
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('FILED', 'Filed'),
        ('PAID', 'Paid'),
    ]
    
    jurisdiction = models.ForeignKey(TaxJurisdiction, on_delete=models.PROTECT,
                                    related_name='tax_periods')
    
    # Period details
    period_start = models.DateField(db_index=True)
    period_end = models.DateField(db_index=True)
    period_name = models.CharField(max_length=50,
                                   help_text="e.g., '2024-Q1', '2024-Jan', '2024'")
    
    # Tax amounts
    output_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                    help_text="Tax collected on sales")
    input_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                   help_text="Tax paid on purchases")
    net_tax_payable = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                         help_text="Output tax - Input tax")
    
    # Filing details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                            default='OPEN', db_index=True)
    filing_due_date = models.DateField(null=True, blank=True)
    filed_date = models.DateField(null=True, blank=True)
    filed_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                null=True, blank=True,
                                related_name='filed_tax_periods')
    
    # Payment
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Journal entry for tax payment
    journal_entry = models.ForeignKey('finance.JournalEntry', on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='tax_period')
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_end']
        unique_together = [('jurisdiction', 'period_start', 'period_end')]
        indexes = [
            models.Index(fields=['jurisdiction', 'status']),
            models.Index(fields=['period_end', 'status']),
        ]
        verbose_name = 'Tax Period'
        verbose_name_plural = 'Tax Periods'
    
    def __str__(self):
        return f"{self.jurisdiction.country_code} - {self.period_name} ({self.get_status_display()})"
    
    def calculate_tax_amounts(self):
        """
        Calculate tax amounts for this period from invoices.
        
        Output tax: From AR invoices (sales)
        Input tax: From AP invoices (purchases)
        """
        from ar.models import ARInvoice
        from ap.models import APInvoice
        
        # Output tax (sales)
        output_tax = ARInvoice.objects.filter(
            invoice_date__gte=self.period_start,
            invoice_date__lte=self.period_end,
            # Filter by jurisdiction if needed
        ).aggregate(
            total=Sum('tax_amount')
        )['total'] or Decimal('0.00')
        
        # Input tax (purchases)
        input_tax = APInvoice.objects.filter(
            invoice_date__gte=self.period_start,
            invoice_date__lte=self.period_end,
            # Filter by jurisdiction if needed
        ).aggregate(
            total=Sum('tax_amount')
        )['total'] or Decimal('0.00')
        
        self.output_tax = output_tax
        self.input_tax = input_tax
        self.net_tax_payable = output_tax - input_tax
        self.save()
    
    def close_period(self, user):
        """Close tax period"""
        if self.status != 'OPEN':
            raise ValidationError("Only open periods can be closed")
        
        self.calculate_tax_amounts()
        self.status = 'CLOSED'
        self.save()
    
    def file_return(self, user):
        """File tax return"""
        if self.status != 'CLOSED':
            raise ValidationError("Only closed periods can be filed")
        
        self.status = 'FILED'
        self.filed_date = timezone.now().date()
        self.filed_by = user
        self.save()
    
    def record_payment(self, user, payment_reference):
        """
        Record tax payment and create journal entry.
        
        Journal Entry:
        DR Tax Payable
        CR Bank Account
        """
        if self.status != 'FILED':
            raise ValidationError("Only filed periods can be paid")
        
        if self.journal_entry:
            # Already recorded
            return self.journal_entry
        
        from finance.models import JournalEntry, JournalLine
        
        # Create journal entry
        journal_entry = JournalEntry.objects.create(
            entry_date=timezone.now().date(),
            reference=f"TAX-{self.period_name}",
            description=f"Tax payment for {self.jurisdiction.country_code} - {self.period_name}",
            currency=self.jurisdiction.currency,
            created_by=user,
        )
        
        # Get tax rate for GL accounts
        tax_rate = self.jurisdiction.tax_rates.filter(
            rate_type='STANDARD',
            is_active=True
        ).first()
        
        if not tax_rate:
            raise ValidationError("No active standard tax rate found for jurisdiction")
        
        # DR Tax Payable
        JournalLine.objects.create(
            journal_entry=journal_entry,
            line_number=1,
            account=tax_rate.tax_payable_account,
            description=f"Tax payment for {self.period_name}",
            debit=self.net_tax_payable,
            credit=0,
        )
        
        # CR Bank Account (would need to specify which bank account)
        # For now, just create the debit side
        
        self.journal_entry = journal_entry
        self.status = 'PAID'
        self.payment_date = timezone.now().date()
        self.payment_reference = payment_reference
        self.save()
        
        return journal_entry


class CorporateTaxAccrual(models.Model):
    """
    Corporate tax accrual for P&L integration.
    
    Tracks monthly/quarterly corporate tax accruals based on profit.
    """
    
    # Period
    fiscal_year = models.IntegerField(db_index=True)
    period_month = models.IntegerField(help_text="Month (1-12)")
    period_quarter = models.IntegerField(help_text="Quarter (1-4)")
    
    # Financial data
    revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit_before_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Tax calculation
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2,
                                   help_text="Corporate tax rate as percentage")
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                    help_text="Accrued tax amount")
    
    # Cumulative for year
    cumulative_profit_before_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cumulative_tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # GL Integration
    tax_expense_account = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                           related_name='corporate_tax_expenses',
                                           help_text="Tax expense account (P&L)")
    tax_payable_account = models.ForeignKey('segment.XX_Segment', on_delete=models.PROTECT,
                                           related_name='corporate_tax_payables',
                                           help_text="Tax payable account (Balance Sheet)")
    
    # Journal entry
    journal_entry = models.ForeignKey('finance.JournalEntry', on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='corporate_tax_accrual')
    
    # Status
    is_posted = models.BooleanField(default=False)
    posted_date = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                 null=True, blank=True,
                                 related_name='posted_tax_accruals')
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fiscal_year', '-period_month']
        unique_together = [('fiscal_year', 'period_month')]
        indexes = [
            models.Index(fields=['fiscal_year', 'period_quarter']),
            models.Index(fields=['is_posted']),
        ]
        verbose_name = 'Corporate Tax Accrual'
        verbose_name_plural = 'Corporate Tax Accruals'
    
    def __str__(self):
        return f"FY{self.fiscal_year} - {self.period_month:02d} - Tax: {self.tax_amount}"
    
    def save(self, *args, **kwargs):
        # Calculate profit before tax
        self.profit_before_tax = self.revenue - self.expenses
        
        # Calculate tax amount
        self.tax_amount = self.profit_before_tax * (self.tax_rate / 100)
        
        super().save(*args, **kwargs)
    
    def post_accrual(self, user):
        """
        Post corporate tax accrual to Finance.
        
        Journal Entry:
        DR Tax Expense (P&L)
        CR Tax Payable (Balance Sheet)
        """
        if self.is_posted:
            # Already posted (idempotent)
            return self.journal_entry
        
        from finance.models import JournalEntry, JournalLine
        
        # Create journal entry
        journal_entry = JournalEntry.objects.create(
            entry_date=timezone.now().date(),
            reference=f"CORP-TAX-{self.fiscal_year}-{self.period_month:02d}",
            description=f"Corporate tax accrual for FY{self.fiscal_year} Month {self.period_month}",
            created_by=user,
        )
        
        # DR Tax Expense
        JournalLine.objects.create(
            journal_entry=journal_entry,
            line_number=1,
            account=self.tax_expense_account,
            description=f"Corporate tax expense for FY{self.fiscal_year}-{self.period_month:02d}",
            debit=self.tax_amount,
            credit=0,
        )
        
        # CR Tax Payable
        JournalLine.objects.create(
            journal_entry=journal_entry,
            line_number=2,
            account=self.tax_payable_account,
            description=f"Corporate tax payable for FY{self.fiscal_year}-{self.period_month:02d}",
            debit=0,
            credit=self.tax_amount,
        )
        
        self.journal_entry = journal_entry
        self.is_posted = True
        self.posted_date = timezone.now()
        self.posted_by = user
        self.save()
        
        return journal_entry


class PaymentRequest(models.Model):
    """
    Payment Request model for managing payment requests from vendor bills.
    
    Workflow:
    DRAFT → SUBMITTED → APPROVED → SCHEDULED → PAID → CLOSED
    
    Rejection states:
    REJECTED → (revise) → DRAFT
    CANCELLED → End
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SCHEDULED', 'Scheduled for Payment'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
        ('CLOSED', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHECK', 'Check'),
        ('CASH', 'Cash'),
        ('CREDIT_CARD', 'Credit Card'),
        ('WIRE', 'Wire Transfer'),
        ('ACH', 'ACH Transfer'),
        ('OTHER', 'Other'),
    ]
    
    # Auto-generated number: PR-YYYYMM-NNNN
    request_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Vendor reference
    supplier = models.ForeignKey('ap.Supplier', on_delete=models.PROTECT, related_name='payment_requests')
    
    # Related vendor bill (optional - can be standalone payment request)
    vendor_bill = models.ForeignKey('vendor_bills.VendorBill', on_delete=models.CASCADE, 
                                   null=True, blank=True, related_name='payment_requests')
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='BANK_TRANSFER')
    requested_date = models.DateField(default=timezone.now)
    requested_payment_date = models.DateField(help_text="Date when payment should be made")
    
    # Financial details
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Exchange rate for multi-currency
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, default=1)
    base_currency_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                              help_text="Amount in base currency")
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    
    # Approval tracking
    approval_required = models.BooleanField(default=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='approved_payment_requests')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Payment execution
    payment_batch = models.ForeignKey(APPaymentBatch, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='payment_requests',
                                     help_text="Payment batch this request belongs to")
    scheduled_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    
    # Payment reference from bank/system
    payment_reference = models.CharField(max_length=100, blank=True,
                                        help_text="Bank reference or check number")
    
    # Notes and attachments
    purpose = models.TextField(help_text="Purpose or reason for payment")
    notes = models.TextField(blank=True)
    attachment_url = models.URLField(blank=True, help_text="Link to supporting documents")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                  null=True, related_name='created_payment_requests')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='updated_payment_requests')
    
    class Meta:
        db_table = 'payment_integration_paymentrequest'
        ordering = ['-requested_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'requested_payment_date']),
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['payment_batch']),
        ]
        verbose_name = 'Payment Request'
        verbose_name_plural = 'Payment Requests'
    
    def __str__(self):
        return f"{self.request_number} - {self.supplier.name} - {self.payment_amount} {self.currency.code}"
    
    def save(self, *args, **kwargs):
        """Auto-generate request number if not set."""
        if not self.request_number:
            from django.utils import timezone
            now = timezone.now()
            prefix = f"PR-{now.strftime('%Y%m')}"
            
            # Get the last request number for this month
            last_request = PaymentRequest.objects.filter(
                request_number__startswith=prefix
            ).order_by('-request_number').first()
            
            if last_request:
                last_num = int(last_request.request_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.request_number = f"{prefix}-{new_num:04d}"
        
        # Calculate base currency amount
        if self.exchange_rate and self.payment_amount:
            self.base_currency_amount = self.payment_amount * self.exchange_rate
        
        super().save(*args, **kwargs)
    
    def submit(self, user=None):
        """Submit payment request for approval."""
        if self.status != 'DRAFT':
            raise ValidationError("Only draft payment requests can be submitted")
        
        self.status = 'SUBMITTED'
        if user:
            self.updated_by = user
        self.save()
    
    def approve(self, user):
        """Approve payment request."""
        if self.status != 'SUBMITTED':
            raise ValidationError("Only submitted payment requests can be approved")
        
        self.status = 'APPROVED'
        self.approved_by = user
        self.approved_date = timezone.now()
        self.updated_by = user
        self.save()
    
    def reject(self, user, reason=None):
        """Reject payment request."""
        if self.status not in ['SUBMITTED', 'APPROVED']:
            raise ValidationError("Only submitted or approved payment requests can be rejected")
        
        self.status = 'REJECTED'
        if reason:
            self.notes = f"{self.notes}\n\nRejection Reason: {reason}" if self.notes else f"Rejection Reason: {reason}"
        self.updated_by = user
        self.save()
    
    def schedule(self, payment_batch, scheduled_date):
        """Schedule payment request in a payment batch."""
        if self.status != 'APPROVED':
            raise ValidationError("Only approved payment requests can be scheduled")
        
        self.status = 'SCHEDULED'
        self.payment_batch = payment_batch
        self.scheduled_date = scheduled_date
        self.save()
    
    def mark_paid(self, paid_date=None, reference=None):
        """Mark payment request as paid."""
        if self.status != 'SCHEDULED':
            raise ValidationError("Only scheduled payment requests can be marked as paid")
        
        self.status = 'PAID'
        self.paid_date = paid_date or timezone.now().date()
        if reference:
            self.payment_reference = reference
        self.save()
    
    def cancel(self, user, reason=None):
        """Cancel payment request."""
        if self.status in ['PAID', 'CLOSED']:
            raise ValidationError("Paid or closed payment requests cannot be cancelled")
        
        self.status = 'CANCELLED'
        if reason:
            self.notes = f"{self.notes}\n\nCancellation Reason: {reason}" if self.notes else f"Cancellation Reason: {reason}"
        self.updated_by = user
        self.save()

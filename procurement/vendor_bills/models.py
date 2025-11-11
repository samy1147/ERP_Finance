"""
3-Way Match & Vendor Bills Models

Implements comprehensive 3-way matching between:
- Purchase Orders (PO)
- Goods Receipt Notes (GRN)
- Vendor Bills

Features:
- Automatic matching based on PO number, item, quantity, price
- Tolerance checking for quantity and price variances
- Exception handling with blocking mechanism
- Idempotent AP Invoice creation
- Audit trail and approval workflow
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime


class VendorBill(models.Model):
    """
    Vendor Bill (Supplier Invoice) awaiting 3-way match and AP posting.
    
    Workflow:
    DRAFT → SUBMITTED → MATCHED → APPROVED → POSTED_TO_AP → PAID
    
    Exception states:
    EXCEPTION → (resolve) → SUBMITTED
    REJECTED → (revise) → DRAFT
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('MATCHED', 'Matched'),
        ('EXCEPTION', 'Exception'),
        ('APPROVED', 'Approved'),
        ('POSTED_TO_AP', 'Posted to AP'),
        ('PAID', 'Paid'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    BILL_TYPE_CHOICES = [
        ('STANDARD', 'Standard Bill'),
        ('CREDIT_MEMO', 'Credit Memo'),
        ('DEBIT_MEMO', 'Debit Memo'),
        ('PREPAYMENT', 'Prepayment'),
    ]
    
    # Auto-generated number: VB-YYYYMM-NNNN
    bill_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Vendor reference
    supplier = models.ForeignKey('ap.Supplier', on_delete=models.PROTECT, related_name='vendor_bills')
    supplier_invoice_number = models.CharField(max_length=100, db_index=True, 
                                               help_text="Vendor's invoice number")
    supplier_invoice_date = models.DateField()
    
    # Source documents for matching
    po_header = models.ForeignKey('purchase_orders.POHeader', on_delete=models.PROTECT,
                                   null=True, blank=True, related_name='vendor_bills',
                                   help_text="Purchase Order for 3-way match")
    grn_header = models.ForeignKey('receiving.GoodsReceipt', on_delete=models.PROTECT,
                                    null=True, blank=True, related_name='vendor_bills',
                                    help_text="Goods Receipt Note for 3-way match")
    
    # Bill details
    bill_type = models.CharField(max_length=20, choices=BILL_TYPE_CHOICES, default='STANDARD')
    bill_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    
    # Financial details
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Exchange rate for multi-currency
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, default=1)
    base_currency_total = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                             help_text="Total in base currency")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True)
    
    # Matching status
    is_matched = models.BooleanField(default=False)
    match_date = models.DateTimeField(null=True, blank=True)
    has_exceptions = models.BooleanField(default=False, db_index=True)
    exception_count = models.IntegerField(default=0)
    
    # AP Integration
    ap_invoice = models.ForeignKey('ap.APInvoice', on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='vendor_bill',
                                   help_text="Created AP Invoice (idempotent)")
    ap_posted_date = models.DateTimeField(null=True, blank=True)
    ap_posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='ap_posted_bills')
    
    # Payment tracking
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Approval workflow
    approval_status = models.CharField(max_length=20, default='PENDING',
                                      choices=[
                                          ('PENDING', 'Pending'),
                                          ('APPROVED', 'Approved'),
                                          ('REJECTED', 'Rejected'),
                                      ])
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='approved_bills')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Notes and attachments
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal notes not visible to supplier")
    
    # Audit trail
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bills')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_bills')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_bill_vendorbill'
        ordering = ['-bill_date', '-bill_number']
        indexes = [
            models.Index(fields=['status', 'bill_date']),
            models.Index(fields=['supplier', 'bill_date']),
            models.Index(fields=['supplier_invoice_number', 'supplier']),
            models.Index(fields=['has_exceptions', 'status']),
        ]
        verbose_name = 'Vendor Bill'
        verbose_name_plural = 'Vendor Bills'
    
    def __str__(self):
        return f"{self.bill_number} - {self.supplier.name} ({self.supplier_invoice_number})"
    
    def save(self, *args, **kwargs):
        if not self.bill_number:
            self.bill_number = self.generate_bill_number()
        
        # Validate no duplicate invoice for same GRN
        self.validate_no_duplicate_grn_invoice()
        
        self.base_currency_total = self.total_amount * self.exchange_rate
        super().save(*args, **kwargs)
    
    def validate_no_duplicate_grn_invoice(self):
        """
        Prevent creating multiple invoices for the same GRN.
        Allows invoices without GRN (manual entry).
        """
        if not self.grn_header:
            # No GRN linked - allow (manual invoice entry)
            return
        
        # Check if another invoice already exists for this GRN
        existing_bills = VendorBill.objects.filter(
            grn_header=self.grn_header
        ).exclude(
            status__in=['CANCELLED', 'REJECTED']  # Exclude cancelled/rejected bills
        )
        
        # If updating existing bill, exclude self
        if self.pk:
            existing_bills = existing_bills.exclude(pk=self.pk)
        
        if existing_bills.exists():
            existing_bill = existing_bills.first()
            raise ValidationError(
                f"An invoice already exists for GRN {self.grn_header.grn_number}. "
                f"Existing invoice: {existing_bill.bill_number} "
                f"(Supplier Invoice: {existing_bill.supplier_invoice_number}). "
                f"Cannot create duplicate invoices for the same goods receipt."
            )
    
    def generate_bill_number(self):
        """Generate bill number: VB-YYYYMM-NNNN"""
        today = timezone.now()
        prefix = f"VB-{today.year}{today.month:02d}"
        last_bill = VendorBill.objects.filter(
            bill_number__startswith=prefix
        ).order_by('-bill_number').first()
        
        if last_bill:
            last_num = int(last_bill.bill_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def recalculate_totals(self):
        """Recalculate totals from lines"""
        lines = self.lines.all()
        self.subtotal = sum(line.line_total for line in lines)
        self.tax_amount = sum(line.tax_amount for line in lines)
        self.total_amount = self.subtotal + self.tax_amount
        self.base_currency_total = self.total_amount * self.exchange_rate
        self.save()
    
    def submit(self, user):
        """Submit bill for matching"""
        if self.status != 'DRAFT':
            raise ValidationError("Only draft bills can be submitted")
        
        if not self.lines.exists():
            raise ValidationError("Cannot submit bill without line items")
        
        self.status = 'SUBMITTED'
        self.updated_by = user
        self.save()
        
        # Auto-trigger 3-way match
        self.perform_three_way_match(user)
    
    def perform_three_way_match(self, user):
        """
        Perform 3-way matching for all lines.
        Creates ThreeWayMatch records and checks tolerances.
        """
        from .services import ThreeWayMatchService
        
        match_service = ThreeWayMatchService()
        result = match_service.match_vendor_bill(self, user)
        
        # Update bill status based on match results
        if result['has_exceptions']:
            self.status = 'EXCEPTION'
            self.has_exceptions = True
            self.exception_count = result['exception_count']
        else:
            self.status = 'MATCHED'
            self.is_matched = True
            self.match_date = timezone.now()
        
        self.save()
        return result
    
    def approve(self, user):
        """Approve matched bill"""
        if self.status not in ['MATCHED', 'EXCEPTION']:
            raise ValidationError("Can only approve matched bills")
        
        if self.has_exceptions:
            # Check if all exceptions are resolved
            unresolved = self.match_records.filter(
                has_exception=True,
                exception__resolution_status='UNRESOLVED'
            ).count()
            if unresolved > 0:
                raise ValidationError(f"Cannot approve: {unresolved} unresolved exceptions remain")
        
        self.status = 'APPROVED'
        self.approval_status = 'APPROVED'
        self.approved_by = user
        self.approved_date = timezone.now()
        self.save()
    
    def post_to_ap(self, user):
        """
        Create AP Invoice (idempotent).
        Only creates invoice if not already created.
        """
        if self.status != 'APPROVED':
            raise ValidationError("Can only post approved bills to AP")
        
        if self.ap_invoice:
            # Already posted - idempotent
            return self.ap_invoice
        
        # Create AP Invoice
        from ap.models import APInvoice, APItem
        
        ap_invoice = APInvoice.objects.create(
            supplier=self.supplier,
            number=self.supplier_invoice_number,
            date=self.supplier_invoice_date,
            due_date=self.due_date,
            currency=self.currency,
            country=self.supplier.country if hasattr(self.supplier, 'country') else 'AE',
            payment_status=APInvoice.UNPAID,
            approval_status='APPROVED',
        )
        
        # Create AP Invoice Lines (APItem)
        for bill_line in self.lines.all():
            APItem.objects.create(
                invoice=ap_invoice,
                description=bill_line.description,
                quantity=bill_line.quantity,
                unit_price=bill_line.unit_price,
                tax_rate=None,  # APItem expects a TaxRate FK, not a percentage
            )
        
        # Link back to vendor bill
        self.ap_invoice = ap_invoice
        self.status = 'POSTED_TO_AP'
        self.ap_posted_date = timezone.now()
        self.ap_posted_by = user if user and user.is_authenticated else None
        self.save()
        
        return ap_invoice
    
    def reject(self, user, reason):
        """Reject bill"""
        if self.status not in ['SUBMITTED', 'MATCHED', 'EXCEPTION']:
            raise ValidationError("Cannot reject bill in current status")
        
        self.status = 'REJECTED'
        self.approval_status = 'REJECTED'
        self.internal_notes += f"\n[{timezone.now()}] Rejected by {user.username}: {reason}"
        self.updated_by = user
        self.save()
    
    def cancel(self, user):
        """Cancel bill"""
        if self.status in ['POSTED_TO_AP', 'PAID']:
            raise ValidationError("Cannot cancel posted or paid bills")
        
        self.status = 'CANCELLED'
        self.updated_by = user
        self.save()


class VendorBillLine(models.Model):
    """
    Line item in vendor bill with matching information.
    """
    
    vendor_bill = models.ForeignKey(VendorBill, on_delete=models.CASCADE, related_name='lines')
    line_number = models.IntegerField()
    
    # Item details
    catalog_item = models.ForeignKey('catalog.CatalogItem', on_delete=models.PROTECT, 
                                    null=True, blank=True)
    description = models.CharField(max_length=500)
    
    # Quantity and UOM
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    unit_of_measure = models.ForeignKey('catalog.UnitOfMeasure', on_delete=models.PROTECT)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=15, decimal_places=4)
    line_total = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Tax
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                   help_text="Tax rate as percentage")
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Reference to PO (if known)
    po_number = models.CharField(max_length=50, blank=True, db_index=True,
                                help_text="PO number from vendor bill")
    po_line_number = models.IntegerField(null=True, blank=True,
                                        help_text="PO line number from vendor bill")
    
    # Reference to GRN (if known)
    grn_number = models.CharField(max_length=50, blank=True, db_index=True,
                                 help_text="GRN number from vendor bill")
    
    # Matching status
    is_matched = models.BooleanField(default=False)
    has_exception = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'vendor_bill_vendorbillline'
        ordering = ['line_number']
        unique_together = [('vendor_bill', 'line_number')]
        indexes = [
            models.Index(fields=['catalog_item']),
            models.Index(fields=['po_number', 'po_line_number']),
        ]
        verbose_name = 'Vendor Bill Line'
        verbose_name_plural = 'Vendor Bill Lines'
    
    def __str__(self):
        return f"{self.vendor_bill.bill_number} - Line {self.line_number}"
    
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        self.tax_amount = self.line_total * (self.tax_rate / 100)
        super().save(*args, **kwargs)
    
    def get_line_total_with_tax(self):
        """Get line total including tax"""
        return self.line_total + self.tax_amount


class ThreeWayMatch(models.Model):
    """
    3-Way Match record linking PO ↔ GRN ↔ Vendor Bill.
    
    Performs tolerance checking on:
    - Quantity variance (ordered vs received vs billed)
    - Price variance (PO price vs bill price)
    
    Exception handling:
    - Creates MatchException if tolerances exceeded
    - Blocks AP posting until exceptions resolved
    """
    
    MATCH_STATUS_CHOICES = [
        ('MATCHED', 'Matched'),
        ('EXCEPTION', 'Exception'),
        ('PARTIALLY_MATCHED', 'Partially Matched'),
        ('UNMATCHED', 'Unmatched'),
    ]
    
    # Auto-generated number: 3WM-YYYYMM-NNNN
    match_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Documents being matched
    vendor_bill_line = models.ForeignKey(VendorBillLine, on_delete=models.CASCADE, 
                                        related_name='match_records')
    
    # PO reference (from procurement module - to be implemented)
    # For now, using CharField for PO number
    po_number = models.CharField(max_length=50, blank=True, db_index=True)
    po_line_number = models.IntegerField(null=True, blank=True)
    
    # GRN reference (from receiving module)
    grn_line = models.ForeignKey('receiving.GRNLine', on_delete=models.PROTECT,
                                null=True, blank=True, related_name='match_records')
    
    # Match details
    catalog_item = models.ForeignKey('catalog.CatalogItem', on_delete=models.PROTECT)
    
    # Quantities
    po_quantity = models.DecimalField(max_digits=15, decimal_places=3, default=0,
                                     help_text="Quantity ordered in PO")
    grn_quantity = models.DecimalField(max_digits=15, decimal_places=3, default=0,
                                      help_text="Quantity received in GRN")
    bill_quantity = models.DecimalField(max_digits=15, decimal_places=3, default=0,
                                       help_text="Quantity billed")
    
    # Prices
    po_unit_price = models.DecimalField(max_digits=15, decimal_places=4, default=0,
                                       help_text="Unit price in PO")
    bill_unit_price = models.DecimalField(max_digits=15, decimal_places=4, default=0,
                                         help_text="Unit price in bill")
    
    # Variance calculations
    quantity_variance = models.DecimalField(max_digits=15, decimal_places=3, default=0,
                                           help_text="Bill qty - GRN qty")
    quantity_variance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                               help_text="Variance as percentage")
    
    price_variance = models.DecimalField(max_digits=15, decimal_places=4, default=0,
                                        help_text="Bill price - PO price")
    price_variance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                            help_text="Variance as percentage")
    
    # Tolerance checking
    quantity_tolerance_exceeded = models.BooleanField(default=False)
    price_tolerance_exceeded = models.BooleanField(default=False)
    
    # Match status
    match_status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES, 
                                   default='UNMATCHED', db_index=True)
    has_exception = models.BooleanField(default=False, db_index=True)
    
    # Match metadata
    matched_date = models.DateTimeField(auto_now_add=True)
    matched_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name='matched_documents')
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'vendor_bill_threewaymatch'
        ordering = ['-matched_date']
        indexes = [
            models.Index(fields=['match_status', 'matched_date']),
            models.Index(fields=['has_exception', 'match_status']),
            models.Index(fields=['catalog_item']),
        ]
        verbose_name = '3-Way Match'
        verbose_name_plural = '3-Way Matches'
    
    def __str__(self):
        return f"{self.match_number} - {self.catalog_item.item_code}"
    
    def save(self, *args, **kwargs):
        if not self.match_number:
            self.match_number = self.generate_match_number()
        
        # Calculate variances
        self.calculate_variances()
        
        # Check tolerances
        self.check_tolerances()
        
        # Update match status
        self.update_match_status()
        
        super().save(*args, **kwargs)
    
    def generate_match_number(self):
        """Generate match number: 3WM-YYYYMM-NNNN"""
        today = timezone.now()
        prefix = f"3WM-{today.year}{today.month:02d}"
        last_match = ThreeWayMatch.objects.filter(
            match_number__startswith=prefix
        ).order_by('-match_number').first()
        
        if last_match:
            last_num = int(last_match.match_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def calculate_variances(self):
        """Calculate quantity and price variances"""
        # Quantity variance: Bill qty - GRN qty
        self.quantity_variance = self.bill_quantity - self.grn_quantity
        
        if self.grn_quantity != 0:
            self.quantity_variance_pct = (self.quantity_variance / self.grn_quantity) * 100
        else:
            self.quantity_variance_pct = 0
        
        # Price variance: Bill price - PO price
        self.price_variance = self.bill_unit_price - self.po_unit_price
        
        if self.po_unit_price != 0:
            self.price_variance_pct = (self.price_variance / self.po_unit_price) * 100
        else:
            self.price_variance_pct = 0
    
    def check_tolerances(self):
        """
        Check if variances exceed tolerances.
        
        Default tolerances:
        - Quantity: ±5%
        - Price: ±3%
        
        Can be customized per supplier/item in MatchTolerance model.
        """
        from .models import MatchTolerance
        
        # Get tolerance configuration
        tolerance = MatchTolerance.get_tolerance(
            supplier=self.vendor_bill_line.vendor_bill.supplier,
            catalog_item=self.catalog_item
        )
        
        # Check quantity tolerance
        if abs(self.quantity_variance_pct) > tolerance.quantity_tolerance_pct:
            self.quantity_tolerance_exceeded = True
        else:
            self.quantity_tolerance_exceeded = False
        
        # Check price tolerance
        if abs(self.price_variance_pct) > tolerance.price_tolerance_pct:
            self.price_tolerance_exceeded = True
        else:
            self.price_tolerance_exceeded = False
        
        # Set exception flag
        self.has_exception = (self.quantity_tolerance_exceeded or self.price_tolerance_exceeded)
    
    def update_match_status(self):
        """Update match status based on variances and exceptions"""
        if self.has_exception:
            self.match_status = 'EXCEPTION'
        elif self.quantity_variance == 0 and self.price_variance == 0:
            self.match_status = 'MATCHED'
        else:
            self.match_status = 'PARTIALLY_MATCHED'


class MatchException(models.Model):
    """
    Exception raised during 3-way matching.
    
    Blocks AP posting until resolved.
    """
    
    EXCEPTION_TYPE_CHOICES = [
        ('QUANTITY_OVER', 'Quantity Over Tolerance'),
        ('QUANTITY_UNDER', 'Quantity Under Tolerance'),
        ('PRICE_OVER', 'Price Over Tolerance'),
        ('PRICE_UNDER', 'Price Under Tolerance'),
        ('PO_NOT_FOUND', 'PO Not Found'),
        ('GRN_NOT_FOUND', 'GRN Not Found'),
        ('ITEM_MISMATCH', 'Item Mismatch'),
        ('DUPLICATE_BILL', 'Duplicate Bill'),
        ('OTHER', 'Other'),
    ]
    
    RESOLUTION_STATUS_CHOICES = [
        ('UNRESOLVED', 'Unresolved'),
        ('IN_REVIEW', 'In Review'),
        ('RESOLVED', 'Resolved'),
        ('WAIVED', 'Waived'),
    ]
    
    RESOLUTION_ACTION_CHOICES = [
        ('ADJUST_BILL', 'Adjust Bill'),
        ('ADJUST_PO', 'Adjust PO'),
        ('ADJUST_GRN', 'Adjust GRN'),
        ('WAIVE', 'Waive Exception'),
        ('REJECT_BILL', 'Reject Bill'),
        ('CONTACT_SUPPLIER', 'Contact Supplier'),
        ('OTHER', 'Other'),
    ]
    
    # Auto-generated number: EXC-YYYYMM-NNNN
    exception_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Link to match
    three_way_match = models.OneToOneField(ThreeWayMatch, on_delete=models.CASCADE,
                                          related_name='exception')
    
    # Exception details
    exception_type = models.CharField(max_length=30, choices=EXCEPTION_TYPE_CHOICES)
    severity = models.CharField(max_length=20, default='MEDIUM',
                               choices=[
                                   ('LOW', 'Low'),
                                   ('MEDIUM', 'Medium'),
                                   ('HIGH', 'High'),
                                   ('CRITICAL', 'Critical'),
                               ])
    
    # Description
    description = models.TextField(help_text="Auto-generated description of the exception")
    
    # Variance details
    variance_amount = models.DecimalField(max_digits=15, decimal_places=4, default=0,
                                         help_text="Absolute variance amount")
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                             help_text="Variance as percentage")
    
    # Financial impact
    financial_impact = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                          help_text="Financial impact of variance")
    
    # Resolution tracking
    resolution_status = models.CharField(max_length=20, choices=RESOLUTION_STATUS_CHOICES,
                                        default='UNRESOLVED', db_index=True)
    resolution_action = models.CharField(max_length=30, choices=RESOLUTION_ACTION_CHOICES,
                                        blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Resolution details
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='resolved_exceptions')
    resolved_date = models.DateTimeField(null=True, blank=True)
    
    # Waiver approval (for high-value exceptions)
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_exceptions')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Blocking status
    blocks_posting = models.BooleanField(default=True,
                                        help_text="If True, blocks AP posting until resolved")
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_bill_matchexception'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resolution_status', 'created_at']),
            models.Index(fields=['exception_type', 'resolution_status']),
            models.Index(fields=['blocks_posting', 'resolution_status']),
        ]
        verbose_name = 'Match Exception'
        verbose_name_plural = 'Match Exceptions'
    
    def __str__(self):
        return f"{self.exception_number} - {self.get_exception_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.exception_number:
            self.exception_number = self.generate_exception_number()
        
        # Auto-generate description if not provided
        if not self.description:
            self.description = self.generate_description()
        
        # Determine if approval required (high financial impact)
        if self.financial_impact > 10000:  # Configurable threshold
            self.requires_approval = True
        
        super().save(*args, **kwargs)
    
    def generate_exception_number(self):
        """Generate exception number: EXC-YYYYMM-NNNN"""
        today = timezone.now()
        prefix = f"EXC-{today.year}{today.month:02d}"
        last_exc = MatchException.objects.filter(
            exception_number__startswith=prefix
        ).order_by('-exception_number').first()
        
        if last_exc:
            last_num = int(last_exc.exception_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def generate_description(self):
        """Auto-generate exception description"""
        match = self.three_way_match
        
        if self.exception_type == 'QUANTITY_OVER':
            return (f"Billed quantity ({match.bill_quantity}) exceeds received quantity "
                   f"({match.grn_quantity}) by {abs(match.quantity_variance_pct):.2f}%")
        
        elif self.exception_type == 'QUANTITY_UNDER':
            return (f"Billed quantity ({match.bill_quantity}) is less than received quantity "
                   f"({match.grn_quantity}) by {abs(match.quantity_variance_pct):.2f}%")
        
        elif self.exception_type == 'PRICE_OVER':
            return (f"Billed price ({match.bill_unit_price}) exceeds PO price "
                   f"({match.po_unit_price}) by {abs(match.price_variance_pct):.2f}%")
        
        elif self.exception_type == 'PRICE_UNDER':
            return (f"Billed price ({match.bill_unit_price}) is less than PO price "
                   f"({match.po_unit_price}) by {abs(match.price_variance_pct):.2f}%")
        
        else:
            return f"Exception: {self.get_exception_type_display()}"
    
    def resolve(self, user, action, notes):
        """Resolve exception"""
        if self.resolution_status == 'RESOLVED':
            raise ValidationError("Exception already resolved")
        
        if self.requires_approval and not self.approved_by:
            raise ValidationError("Exception requires approval before resolution")
        
        self.resolution_status = 'RESOLVED'
        self.resolution_action = action
        self.resolution_notes = notes
        self.resolved_by = user
        self.resolved_date = timezone.now()
        self.blocks_posting = False
        self.save()
        
        # Update match status
        self.three_way_match.has_exception = False
        self.three_way_match.match_status = 'MATCHED'
        self.three_way_match.save()
        
        # Update vendor bill
        bill = self.three_way_match.vendor_bill_line.vendor_bill
        bill.exception_count = bill.match_records.filter(has_exception=True).count()
        if bill.exception_count == 0:
            bill.has_exceptions = False
            bill.status = 'MATCHED'
        bill.save()
    
    def waive(self, user, notes):
        """Waive exception (requires approval for high-value)"""
        if self.resolution_status == 'RESOLVED':
            raise ValidationError("Exception already resolved")
        
        if self.requires_approval and not self.approved_by:
            raise ValidationError("High-value exception requires approval for waiver")
        
        self.resolve(user, 'WAIVE', notes)
    
    def approve_waiver(self, user):
        """Approve exception waiver"""
        if not self.requires_approval:
            raise ValidationError("Exception does not require approval")
        
        if self.approved_by:
            raise ValidationError("Exception already approved")
        
        self.approved_by = user
        self.approved_date = timezone.now()
        self.save()


class MatchTolerance(models.Model):
    """
    Configurable tolerance thresholds for 3-way matching.
    
    Can be set at different levels:
    - Global default
    - Per supplier
    - Per item category
    - Per specific item
    """
    
    SCOPE_CHOICES = [
        ('GLOBAL', 'Global Default'),
        ('SUPPLIER', 'Supplier Specific'),
        ('CATEGORY', 'Category Specific'),
        ('ITEM', 'Item Specific'),
    ]
    
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='GLOBAL')
    
    # Scope references
    supplier = models.ForeignKey('ap.Supplier', on_delete=models.CASCADE, 
                                null=True, blank=True, related_name='match_tolerances')
    catalog_item = models.ForeignKey('catalog.CatalogItem', on_delete=models.CASCADE,
                                    null=True, blank=True, related_name='match_tolerances')
    
    # Tolerance thresholds (as percentages)
    quantity_tolerance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=5.00,
                                                 help_text="Quantity tolerance as percentage (default 5%)")
    price_tolerance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=3.00,
                                             help_text="Price tolerance as percentage (default 3%)")
    
    # Value thresholds for auto-approval
    auto_approve_threshold = models.DecimalField(max_digits=15, decimal_places=2, default=1000,
                                                help_text="Auto-approve exceptions below this amount")
    
    # Active status
    is_active = models.BooleanField(default=True)
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_bill_matchtolerance'
        ordering = ['scope', '-created_at']
        indexes = [
            models.Index(fields=['scope', 'is_active']),
            models.Index(fields=['supplier']),
            models.Index(fields=['catalog_item']),
        ]
        verbose_name = 'Match Tolerance'
        verbose_name_plural = 'Match Tolerances'
    
    def __str__(self):
        if self.scope == 'GLOBAL':
            return f"Global Tolerance (Qty: ±{self.quantity_tolerance_pct}%, Price: ±{self.price_tolerance_pct}%)"
        elif self.scope == 'SUPPLIER' and self.supplier:
            return f"{self.supplier.name} Tolerance"
        elif self.scope == 'ITEM' and self.catalog_item:
            return f"{self.catalog_item.item_code} Tolerance"
        else:
            return f"{self.get_scope_display()} Tolerance"
    
    @classmethod
    def get_tolerance(cls, supplier=None, catalog_item=None):
        """
        Get applicable tolerance configuration.
        
        Priority:
        1. Item-specific
        2. Supplier-specific
        3. Global default
        """
        # Try item-specific
        if catalog_item:
            tolerance = cls.objects.filter(
                scope='ITEM',
                catalog_item=catalog_item,
                is_active=True
            ).first()
            if tolerance:
                return tolerance
        
        # Try supplier-specific
        if supplier:
            tolerance = cls.objects.filter(
                scope='SUPPLIER',
                supplier=supplier,
                is_active=True
            ).first()
            if tolerance:
                return tolerance
        
        # Get global default
        tolerance = cls.objects.filter(
            scope='GLOBAL',
            is_active=True
        ).first()
        
        if not tolerance:
            # Create default if doesn't exist
            tolerance = cls.objects.create(
                scope='GLOBAL',
                quantity_tolerance_pct=5.00,
                price_tolerance_pct=3.00,
                auto_approve_threshold=1000
            )
        
        return tolerance

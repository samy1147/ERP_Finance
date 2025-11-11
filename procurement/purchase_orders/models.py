"""
Purchase Order models for procurement.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from decimal import Decimal
from core.models import Currency
from procurement.catalog.models import UnitOfMeasure


class POHeader(models.Model):
    """Purchase Order Header."""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted for Approval'),
        ('APPROVED', 'Approved'),
        ('CONFIRMED', 'Confirmed/Sent to Vendor'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('RECEIVED', 'Fully Received'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_TERMS_CHOICES = [
        ('NET_30', 'Net 30'),
        ('NET_60', 'Net 60'),
        ('NET_90', 'Net 90'),
        ('COD', 'Cash on Delivery'),
        ('CIA', 'Cash in Advance'),
        ('DUE_ON_RECEIPT', 'Due on Receipt'),
    ]
    
    # PO Type (same as PR Type)
    PO_TYPE_CHOICES = [
        ('CATEGORIZED_GOODS', 'Categorized Goods'),
        ('UNCATEGORIZED_GOODS', 'Uncategorized Goods'),
        ('SERVICES', 'Services'),
    ]
    
    # PO Information
    po_number = models.CharField(max_length=50, unique=True, db_index=True)
    po_date = models.DateField(default=date.today)
    po_type = models.CharField(
        max_length=30,
        choices=PO_TYPE_CHOICES,
        default='UNCATEGORIZED_GOODS',
        help_text="Type of PO: Categorized Goods, Uncategorized Goods, or Services"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True)
    
    # Source PR Headers - Track multiple PRs that contribute to this PO
    source_pr_headers = models.ManyToManyField(
        'requisitions.PRHeader',
        blank=True,
        related_name='converted_pos',
        help_text="Source PR Headers that contribute to this PO"
    )
    
    # Vendor Information - using string for now until Vendor model is ready
    vendor_name = models.CharField(max_length=200, blank=True, help_text="Vendor/Supplier name")
    vendor_email = models.EmailField(blank=True)
    vendor_phone = models.CharField(max_length=50, blank=True)
    vendor_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Vendor's quote/reference number"
    )
    
    # Delivery Information
    delivery_date = models.DateField(null=True, blank=True)
    delivery_address = models.TextField(blank=True)
    delivery_contact = models.CharField(max_length=200, blank=True)
    delivery_phone = models.CharField(max_length=50, blank=True)
    
    # Delivery Status - tracks receiving progress
    DELIVERY_STATUS_CHOICES = [
        ('NOT_RECEIVED', 'Not Received'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('RECEIVED', 'Fully Received'),
    ]
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='NOT_RECEIVED',
        db_index=True,
        help_text="Tracks the delivery/receiving status of the PO"
    )
    
    # Payment Terms
    payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS_CHOICES,
        default='NET_30'
    )
    payment_terms_description = models.TextField(blank=True)
    
    # Financial - Transaction Currency
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, help_text="Transaction currency")
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Subtotal in transaction currency")
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Tax in transaction currency")
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Discount in transaction currency")
    shipping_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Shipping in transaction currency")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Total in transaction currency")
    
    # Multi-Currency Support
    exchange_rate = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=Decimal('1.000000'),
        help_text="Exchange rate from transaction currency to base currency"
    )
    base_currency_subtotal = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Subtotal in base currency"
    )
    base_currency_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total amount in base currency"
    )
    
    # Cost Center & Project - simplified for now
    cost_center_code = models.CharField(max_length=50, blank=True)
    cost_center_name = models.CharField(max_length=200, blank=True)
    project_code = models.CharField(max_length=50, blank=True)
    project_name = models.CharField(max_length=200, blank=True)
    
    # Notes
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Workflow
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='purchase_orders_created')
    created_at = models.DateTimeField(auto_now_add=True)
    
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_submitted')
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_confirmed')
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_cancelled')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'procurement_poheader'
        ordering = ['-po_date', '-po_number']
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['status']),
            models.Index(fields=['vendor_name']),
            models.Index(fields=['po_date']),
        ]
    
    def __str__(self):
        return f"{self.po_number} - {self.vendor_name}"
    
    def save(self, *args, **kwargs):
        # Generate PO number if not set
        if not self.po_number:
            self.po_number = self.generate_po_number()
        
        # Calculate totals
        self.calculate_totals()
        
        super().save(*args, **kwargs)
    
    def generate_po_number(self):
        """Generate unique PO number."""
        from datetime import date
        today = date.today()
        prefix = f"PO-{today.strftime('%Y%m')}"
        
        last_po = POHeader.objects.filter(
            po_number__startswith=prefix
        ).order_by('-po_number').first()
        
        if last_po:
            try:
                last_num = int(last_po.po_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def calculate_totals(self):
        """Calculate PO totals from lines in both transaction and base currency."""
        # Skip if PO hasn't been saved yet (no pk means no lines can exist)
        if not self.pk:
            return
        
        lines = self.lines.all()
        self.subtotal = sum(line.line_total for line in lines)
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        
        # Calculate base currency amounts
        if self.exchange_rate and self.exchange_rate > 0:
            self.base_currency_subtotal = (self.subtotal * self.exchange_rate).quantize(Decimal('0.01'))
            self.base_currency_total = (self.total_amount * self.exchange_rate).quantize(Decimal('0.01'))
        else:
            self.base_currency_subtotal = self.subtotal
            self.base_currency_total = self.total_amount
    
    def update_exchange_rate(self, rate_date=None):
        """
        Update exchange rate from current exchange rate table.
        
        Args:
            rate_date: Date to use for exchange rate lookup (defaults to PO date)
        """
        from finance.fx_services import get_exchange_rate, get_base_currency
        
        try:
            base_currency = get_base_currency()
            
            # If PO currency is same as base, rate is 1
            if self.currency.id == base_currency.id:
                self.exchange_rate = Decimal('1.000000')
            else:
                # Use provided date or PO date
                lookup_date = rate_date or self.po_date
                
                # Get exchange rate from table
                self.exchange_rate = get_exchange_rate(
                    from_currency=self.currency,
                    to_currency=base_currency,
                    rate_date=lookup_date,
                    rate_type='SPOT'
                )
            
            # Recalculate totals with new exchange rate
            self.calculate_totals()
            
        except Exception as e:
            # If exchange rate lookup fails, default to 1
            self.exchange_rate = Decimal('1.000000')
            raise ValueError(f"Could not fetch exchange rate: {str(e)}")
    
    def submit(self, user):
        """Submit PO for approval."""
        if self.status != 'DRAFT':
            raise ValueError("Only draft POs can be submitted")
        
        if not self.vendor_name:
            raise ValueError("Vendor must be selected before submitting")
        
        if not self.lines.exists():
            raise ValueError("PO must have at least one line item")
        
        self.status = 'SUBMITTED'
        self.submitted_by = user
        self.submitted_at = timezone.now()
        self.save()
        
        # Trigger approval workflow
        from procurement.approvals.models import ApprovalWorkflow
        try:
            workflow = ApprovalWorkflow.objects.get(
                document_type='purchase_orders.POHeader',
                is_active=True
            )
            workflow.initiate_approval(
                document=self,
                amount=self.total_amount,
                requested_by=user
            )
        except ApprovalWorkflow.DoesNotExist:
            pass  # No workflow configured
        
        return True
    
    def approve(self, user):
        """Approve PO."""
        if self.status != 'SUBMITTED':
            raise ValueError("Only submitted POs can be approved")
        
        self.status = 'APPROVED'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
        
        return True
    
    def confirm_and_send(self, user):
        """Confirm PO and mark as sent to vendor."""
        if self.status != 'APPROVED':
            raise ValueError("Only approved POs can be confirmed")
        
        self.status = 'CONFIRMED'
        self.confirmed_by = user
        self.confirmed_at = timezone.now()
        self.save()
        
        # TODO: Send email to vendor
        return True
    
    def cancel_delivery(self, user, reason=''):
        """
        Cancel delivery and revert to APPROVED status.
        Use this when a CONFIRMED PO needs to be recalled before receiving goods.
        """
        if self.status != 'CONFIRMED':
            raise ValueError("Only confirmed POs can have their delivery cancelled")
        
        # Revert to APPROVED status
        self.status = 'APPROVED'
        # Clear confirmation details
        self.confirmed_by = None
        self.confirmed_at = None
        # Store cancellation note in internal notes
        cancellation_note = f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Delivery cancelled by {user.username}"
        if reason:
            cancellation_note += f": {reason}"
        self.internal_notes += cancellation_note
        self.save()
        
        return True
    
    def cancel(self, user, reason):
        """Cancel PO."""
        if self.status in ['CLOSED', 'CANCELLED']:
            raise ValueError("Cannot cancel closed or already cancelled PO")
        
        self.status = 'CANCELLED'
        self.cancelled_by = user
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()
        
        return True
    
    def reset_approval(self, user):
        """
        Reset approval status when PO is edited after approval.
        - If APPROVED: Reset to SUBMITTED (needs re-approval)
        - If SUBMITTED: Keep as SUBMITTED
        This allows the PO to go through approval again without manual resubmission.
        """
        if self.status == 'APPROVED':
            self.status = 'SUBMITTED'
            self.approved_by = None
            self.approved_at = None
            # Keep submitted_by and submitted_at since it's going back to approval
            self.save()
            
            # Trigger approval workflow again
            from procurement.approvals.models import ApprovalWorkflow
            try:
                workflow = ApprovalWorkflow.objects.get(
                    document_type='purchase_orders.POHeader',
                    is_active=True
                )
                # Initiate a new approval instance for the edited PO
                workflow.initiate_approval(
                    document=self,
                    amount=self.total_amount,
                    requested_by=user
                )
            except ApprovalWorkflow.DoesNotExist:
                pass  # No workflow configured
            
            return True
        elif self.status == 'SUBMITTED':
            # Already in submitted state, no change needed
            return True
        return False
    
    def can_edit(self):
        """Check if PO can be edited."""
        # Can edit if not confirmed/sent to vendor yet
        return self.status in ['DRAFT', 'SUBMITTED', 'APPROVED']
    
    def on_approved(self):
        """Callback when approval workflow completes."""
        if self.status == 'SUBMITTED':
            # Get approver from workflow
            from django.contrib.auth.models import User
            approver = User.objects.get(id=2)  # Default to admin in dev
            self.approve(approver)
    
    def get_receiving_status(self):
        """
        Get receiving status of the PO.
        Returns: 'NOT_RECEIVED', 'PARTIALLY_RECEIVED', or 'RECEIVED'
        """
        lines = self.lines.all()
        
        if not lines.exists():
            return 'NOT_RECEIVED'
        
        # Check if any quantity has been received
        any_received = any(line.quantity_received > 0 for line in lines)
        
        # Check if all lines are fully received
        all_received = all(line.quantity_received >= line.quantity for line in lines)
        
        if all_received:
            return 'RECEIVED'
        elif any_received:
            return 'PARTIALLY_RECEIVED'
        else:
            return 'NOT_RECEIVED'
    
    def can_receive(self):
        """
        Check if PO is ready to receive goods.
        Only CONFIRMED, PARTIALLY_RECEIVED POs can have goods received.
        """
        return self.status in ['CONFIRMED', 'PARTIALLY_RECEIVED']
    
    def has_outstanding_items(self):
        """Check if PO has any items pending receipt."""
        return any(line.quantity_received < line.quantity for line in self.lines.all())


class POLine(models.Model):
    """Purchase Order Line Item."""
    
    po_header = models.ForeignKey(
        POHeader,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    
    line_number = models.PositiveIntegerField()
    
    # Item Information
    item_description = models.TextField()
    specifications = models.TextField(blank=True)
    
    # Source PR Lines - Many-to-Many through PRToPOLineMapping
    # Access via: po_line.pr_line_mappings.all()
    # or: po_line.source_pr_lines (reverse from mapping)
    
    # From Catalog
    catalog_item = models.ForeignKey(
        'catalog.CatalogItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Item Categorization Status (same as PR)
    ITEM_TYPE_CHOICES = [
        ('CATEGORIZED', 'Categorized - Linked to Catalog'),
        ('NON_CATEGORIZED', 'Non-Categorized - Free Text'),
    ]
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        default='NON_CATEGORIZED',
        help_text="Whether item is linked to catalog or is free text"
    )
    
    # Vendor Product Reference
    vendor_part_number = models.CharField(max_length=200, blank=True)
    
    # Quantity & UOM
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    
    # Pricing - Transaction Currency
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, help_text="Unit price in transaction currency")
    line_total = models.DecimalField(max_digits=15, decimal_places=2, help_text="Line total in transaction currency")
    
    # Multi-Currency Support - Base Currency Amounts
    base_currency_unit_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Unit price in base currency"
    )
    base_currency_line_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Line total in base currency"
    )
    
    # Delivery
    need_by_date = models.DateField(null=True, blank=True)
    
    # Receiving tracking
    quantity_received = models.DecimalField(max_digits=15, decimal_places=3, default=Decimal('0.000'))
    quantity_billed = models.DecimalField(max_digits=15, decimal_places=3, default=Decimal('0.000'))
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'procurement_poline'
        ordering = ['po_header', 'line_number']
        unique_together = ['po_header', 'line_number']
        verbose_name = 'PO Line'
        verbose_name_plural = 'PO Lines'
    
    def __str__(self):
        return f"{self.po_header.po_number} - Line {self.line_number}"
    
    def save(self, *args, **kwargs):
        # Auto-set item_type based on catalog_item presence
        if self.catalog_item:
            self.item_type = 'CATEGORIZED'
        else:
            self.item_type = 'NON_CATEGORIZED'
        
        # Calculate line total in transaction currency
        self.line_total = self.quantity * self.unit_price
        
        # Calculate base currency amounts using PO header's exchange rate
        if self.po_header and self.po_header.exchange_rate:
            exchange_rate = self.po_header.exchange_rate
            self.base_currency_unit_price = (self.unit_price * exchange_rate).quantize(Decimal('0.01'))
            self.base_currency_line_total = (self.line_total * exchange_rate).quantize(Decimal('0.01'))
        else:
            self.base_currency_unit_price = self.unit_price
            self.base_currency_line_total = self.line_total
        
        super().save(*args, **kwargs)
        
        # Update PO header totals
        if self.po_header_id:
            self.po_header.calculate_totals()
            self.po_header.save()
    
    @property
    def quantity_outstanding(self):
        """Quantity not yet received."""
        return self.quantity - self.quantity_received
    
    @property
    def is_fully_received(self):
        """Check if line is fully received."""
        return self.quantity_received >= self.quantity
    
    def get_source_pr_lines(self):
        """Get all source PR lines for this PO line."""
        return [mapping.pr_line for mapping in self.pr_line_mappings.all()]
    
    def get_source_pr_numbers(self):
        """Get list of source PR numbers."""
        pr_numbers = set()
        for mapping in self.pr_line_mappings.all():
            pr_numbers.add(mapping.pr_line.pr_header.pr_number)
        return sorted(list(pr_numbers))

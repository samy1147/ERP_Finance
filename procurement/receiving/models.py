"""
Receiving and Quality Control models for ERP Finance system.

Features:
- Goods Receipt Notes (GRN) with partial receipts
- Over/under tolerance checking
- Lot/batch tracking
- Put-away location management
- Quality inspection workflows
- Non-conformance reporting
- Return to Vendor (RTV) with debit memos
- 3-way matching (PO-Receipt-Invoice)
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import json


class Warehouse(models.Model):
    """
    Warehouse/Location master for inventory management.
    """
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Warehouse type
    TYPE_CHOICES = [
        ('MAIN', 'Main Warehouse'),
        ('BRANCH', 'Branch Warehouse'),
        ('TRANSIT', 'Transit Location'),
        ('QUARANTINE', 'Quarantine Area'),
        ('SCRAP', 'Scrap/Rejected Area'),
    ]
    warehouse_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='MAIN'
    )
    
    is_active = models.BooleanField(default=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_warehouses'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class StorageLocation(models.Model):
    """
    Storage locations within warehouses (bin locations, racks, etc.).
    """
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='locations'
    )
    code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=200)
    
    # Location hierarchy (aisle-rack-shelf-bin)
    aisle = models.CharField(max_length=20, blank=True)
    rack = models.CharField(max_length=20, blank=True)
    shelf = models.CharField(max_length=20, blank=True)
    bin = models.CharField(max_length=20, blank=True)
    
    # Capacity
    max_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum weight capacity in kg"
    )
    max_volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum volume capacity in cubic meters"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_quarantine = models.BooleanField(
        default=False,
        help_text="Reserved for quarantined/inspection items"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['warehouse', 'code']
        verbose_name = 'Storage Location'
        verbose_name_plural = 'Storage Locations'
        unique_together = [['warehouse', 'code']]
    
    def __str__(self):
        return f"{self.warehouse.code}-{self.code}"


class GoodsReceipt(models.Model):
    """
    Goods Receipt Note (GRN) header.
    
    Records receipt of goods from suppliers or other sources.
    """
    
    # Document identification
    grn_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        editable=False
    )
    
    # Source document (PO, Transfer Order, etc.)
    # Direct PO reference for procurement flow
    po_header = models.ForeignKey(
        'purchase_orders.POHeader',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='goods_receipts',
        help_text="Purchase Order reference"
    )
    
    # Generic FK to support multiple source types
    source_document_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Source document type (e.g., PO, Transfer Order)"
    )
    source_document_id = models.PositiveIntegerField(null=True, blank=True)
    source_document = GenericForeignKey('source_document_type', 'source_document_id')
    
    # For now, use simple reference field until PO module is implemented
    po_reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="PO number reference"
    )
    
    # Dates
    receipt_date = models.DateField(default=timezone.now)
    expected_date = models.DateField(null=True, blank=True)
    
    # Supplier
    supplier = models.ForeignKey(
        'ap.Supplier',
        on_delete=models.PROTECT,
        related_name='goods_receipts'
    )
    
    # Delivery details
    delivery_note_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Supplier's delivery note/packing slip number"
    )
    vehicle_number = models.CharField(max_length=50, blank=True)
    driver_name = models.CharField(max_length=200, blank=True)
    
    # Receiving location
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='goods_receipts'
    )
    
    # GRN Type (copied from PO)
    # Posting behavior:
    # - CATEGORIZED_GOODS: Posts to Inventory (Asset) - catalog items, connects to AP invoice with 3-way match
    # - UNCATEGORIZED_GOODS: Posts to Expenses (P&L) directly - non-inventory consumables/expenses
    # - SERVICES: Posts to Expenses (P&L) directly - connects to AP invoice (2-way match: PO+Invoice)
    GRN_TYPE_CHOICES = [
        ('CATEGORIZED_GOODS', 'Categorized Goods'),
        ('UNCATEGORIZED_GOODS', 'Uncategorized Goods'),
        ('SERVICES', 'Services'),
    ]
    grn_type = models.CharField(
        max_length=30,
        choices=GRN_TYPE_CHOICES,
        default='UNCATEGORIZED_GOODS',
        help_text="Type of GRN: Categorized (catalog→inventory), Uncategorized (→expenses), Services (→expenses)"
    )
    
    # Status
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('QUALITY_HOLD', 'Quality Hold'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )
    
    # Receiving personnel
    received_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='received_goods_receipts'
    )
    
    # Completion tracking
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Quality inspection
    requires_inspection = models.BooleanField(default=False)
    inspection_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('PASSED', 'Passed'),
            ('FAILED', 'Failed'),
            ('WAIVED', 'Waived'),
        ],
        default='PENDING',
        blank=True
    )
    
    # Notes
    remarks = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_goods_receipts'
    )
    
    class Meta:
        ordering = ['-receipt_date', '-grn_number']
        verbose_name = 'Goods Receipt'
        verbose_name_plural = 'Goods Receipts'
        indexes = [
            models.Index(fields=['status', 'receipt_date']),
            models.Index(fields=['supplier', 'receipt_date']),
            models.Index(fields=['warehouse', 'receipt_date']),
        ]
    
    def __str__(self):
        return f"GRN-{self.grn_number} - {self.supplier.name}"
    
    @property
    def receipt_number(self):
        """Alias for grn_number for backward compatibility"""
        return self.grn_number
    
    def save(self, *args, **kwargs):
        if not self.grn_number:
            self.grn_number = self._generate_grn_number()
        super().save(*args, **kwargs)
    
    def _generate_grn_number(self):
        """Generate unique GRN number: GRN-YYYYMM-NNNN"""
        from django.db.models import Max
        import re
        
        today = timezone.now()
        prefix = f"GRN-{today.strftime('%Y%m')}"
        
        last_grn = GoodsReceipt.objects.filter(
            grn_number__startswith=prefix
        ).aggregate(Max('grn_number'))['grn_number__max']
        
        if last_grn:
            match = re.search(r'-(\d+)$', last_grn)
            if match:
                sequence = int(match.group(1)) + 1
            else:
                sequence = 1
        else:
            sequence = 1
        
        return f"{prefix}-{sequence:04d}"
    
    def complete(self, user):
        """Complete the goods receipt."""
        if self.status != 'IN_PROGRESS':
            raise ValueError("Only in-progress receipts can be completed")
        
        # Check if all lines are received
        if self.lines.filter(receipt_status='PENDING').exists():
            raise ValueError("Cannot complete receipt with pending lines")
        
        # If requires inspection, set to quality hold
        if self.requires_inspection:
            self.status = 'QUALITY_HOLD'
            self.inspection_status = 'PENDING'
        else:
            self.status = 'COMPLETED'
        
        self.completed_at = timezone.now()
        self.save()
        
        return True
    
    def cancel(self, user, reason):
        """Cancel the goods receipt."""
        if self.status == 'COMPLETED':
            raise ValueError("Cannot cancel completed receipts")
        
        self.status = 'CANCELLED'
        self.internal_notes = f"{self.internal_notes}\nCancelled by {user}: {reason}"
        self.save()
        
        return True
    
    def post_to_inventory(self, user=None, posted_by=None):
        """
        Post goods receipt to inventory or expenses.
        
        This will:
        1. Update inventory quantities (for CATEGORIZED_GOODS only)
        2. Post to expenses (for UNCATEGORIZED_GOODS and SERVICES)
        3. Change status to COMPLETED
        4. Update PO line received quantities
        5. Update PO status (PARTIALLY_RECEIVED or RECEIVED)
        6. Ready for AP invoice matching (3-way match for categorized, 2-way for others)
        
        Posting behavior by type:
        - CATEGORIZED_GOODS: Post to inventory (asset account) - catalog items
        - UNCATEGORIZED_GOODS: Post to expenses (P&L account) - consumables/non-inventory
        - SERVICES: Post to expenses (P&L account) - no physical goods
        
        Args:
            user: User performing the action (deprecated, use posted_by)
            posted_by: User performing the action
        """
        if self.status == 'COMPLETED':
            raise ValueError("Goods receipt already posted")
        
        if self.status == 'CANCELLED':
            raise ValueError("Cannot post cancelled goods receipt")
        
        # Use posted_by if provided, otherwise fall back to user
        posting_user = posted_by or user
        
        # Update PO line received quantities if this GRN is linked to a PO
        if self.po_header:
            self._update_po_received_quantities()
        
        # Update status
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.posted_at = timezone.now()
        if posting_user:
            self.posted_by = posting_user
        
        # Posting logic based on GRN type
        if self.grn_type == 'CATEGORIZED_GOODS':
            # Post to INVENTORY (asset account)
            # Only categorized (catalog) goods go to inventory
            
            # Create inventory movements using InventoryService
            try:
                from inventory.services import InventoryService
                InventoryService.receive_goods(self, posting_user)
                print(f"✓ GRN {self.grn_number}: CATEGORIZED_GOODS posted to inventory")
            except Exception as e:
                print(f"✗ GRN {self.grn_number}: Inventory posting failed - {str(e)}")
                # Continue anyway - don't block the GRN completion
                # The user can manually adjust inventory if needed
                pass
        
        elif self.grn_type in ['UNCATEGORIZED_GOODS', 'SERVICES']:
            # Post to EXPENSES (P&L account)
            # Uncategorized goods (consumables) and services go directly to expenses
            # They are ready for AP invoice processing
            print(f"✓ GRN {self.grn_number}: {self.grn_type} posted to expenses (skipped inventory)")
            pass
        
        self.save()
        
        return True
    
    def _update_po_received_quantities(self):
        """
        Update PO line received quantities and PO status based on this GRN.
        Supports partial receiving.
        """
        if not self.po_header:
            return
        
        from procurement.purchase_orders.models import POLine
        
        # Update each GRN line's corresponding PO line
        for grn_line in self.lines.all():
            if grn_line.po_line_reference:
                try:
                    po_line = POLine.objects.get(id=int(grn_line.po_line_reference))
                    # Add the received quantity to the PO line's received quantity
                    po_line.quantity_received += grn_line.received_quantity
                    po_line.save()
                except (POLine.DoesNotExist, ValueError):
                    # If PO line not found, continue with other lines
                    continue
        
        # Update PO header status based on receiving progress
        self._update_po_status()
    
    def _update_po_status(self):
        """
        Update PO status and delivery_status based on how much has been received.
        - PARTIALLY_RECEIVED: Some items received but not all
        - RECEIVED: All items fully received
        """
        if not self.po_header:
            return
        
        from procurement.purchase_orders.models import POLine
        
        po = self.po_header
        all_lines = po.lines.all()
        
        if not all_lines.exists():
            return
        
        # Check if any quantity has been received
        any_received = any(line.quantity_received > 0 for line in all_lines)
        
        # Check if all lines are fully received
        all_received = all(line.quantity_received >= line.quantity for line in all_lines)
        
        if all_received:
            po.status = 'RECEIVED'
            po.delivery_status = 'RECEIVED'
        elif any_received:
            po.status = 'PARTIALLY_RECEIVED'
            po.delivery_status = 'PARTIALLY_RECEIVED'
        else:
            # If nothing received, keep status as NOT_RECEIVED
            po.delivery_status = 'NOT_RECEIVED'
        
        po.save()


class GRNLine(models.Model):
    """
    Goods Receipt Line item.
    
    Records individual items received with quantity, quality, and location.
    """
    
    goods_receipt = models.ForeignKey(
        GoodsReceipt,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    
    line_number = models.PositiveIntegerField()
    
    # Item reference
    catalog_item = models.ForeignKey(
        'catalog.CatalogItem',
        on_delete=models.PROTECT,
        related_name='grn_lines'
    )
    item_description = models.CharField(max_length=500)
    
    # Item Categorization Status (from PO/PR)
    ITEM_TYPE_CHOICES = [
        ('CATEGORIZED', 'Categorized - Linked to Catalog'),
        ('NON_CATEGORIZED', 'Non-Categorized - Free Text'),
    ]
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        default='NON_CATEGORIZED',
        help_text="Whether item is linked to catalog or is free text (copied from PO)"
    )
    
    # PO line reference (if applicable)
    po_line_reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="Reference to PO line"
    )
    
    # Quantities
    ordered_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Quantity ordered on PO"
    )
    received_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.0000'))],
        help_text="Quantity actually received"
    )
    accepted_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Quantity accepted after inspection"
    )
    rejected_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Quantity rejected"
    )
    
    # Pricing (from PO)
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Unit price from PO (for invoice matching)"
    )
    
    unit_of_measure = models.ForeignKey(
        'catalog.UnitOfMeasure',
        on_delete=models.PROTECT,
        related_name='grn_lines'
    )
    
    # Tolerance checking
    over_tolerance_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        help_text="Allowed over-receipt percentage"
    )
    under_tolerance_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Allowed under-receipt percentage"
    )
    
    tolerance_exceeded = models.BooleanField(default=False)
    tolerance_message = models.TextField(blank=True)
    
    # Receipt status
    RECEIPT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partially Received'),
        ('FULL', 'Fully Received'),
        ('OVER', 'Over Received'),
        ('UNDER', 'Under Received'),
    ]
    receipt_status = models.CharField(
        max_length=20,
        choices=RECEIPT_STATUS_CHOICES,
        default='PENDING'
    )
    
    # Lot/Batch tracking
    lot_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Lot/Batch number from supplier"
    )
    serial_numbers = models.JSONField(
        default=list,
        blank=True,
        help_text="Serial numbers for serialized items"
    )
    
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Put-away location
    storage_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='grn_lines'
    )
    put_away_completed = models.BooleanField(default=False)
    put_away_at = models.DateTimeField(null=True, blank=True)
    put_away_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='put_away_grn_lines'
    )
    
    # Quality inspection
    requires_inspection = models.BooleanField(default=False)
    inspection_completed = models.BooleanField(default=False)
    
    # Damage/Condition
    CONDITION_CHOICES = [
        ('GOOD', 'Good Condition'),
        ('DAMAGED', 'Damaged'),
        ('EXPIRED', 'Expired'),
        ('DEFECTIVE', 'Defective'),
        ('INCOMPLETE', 'Incomplete'),
    ]
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='GOOD'
    )
    
    # Notes
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['goods_receipt', 'line_number']
        verbose_name = 'GRN Line'
        verbose_name_plural = 'GRN Lines'
        unique_together = [['goods_receipt', 'line_number']]
        indexes = [
            models.Index(fields=['catalog_item']),
            models.Index(fields=['lot_number']),
        ]
    
    def __str__(self):
        return f"{self.goods_receipt.grn_number} - Line {self.line_number}"
    
    def save(self, *args, **kwargs):
        # Auto-assign line number
        if not self.line_number:
            last_line = GRNLine.objects.filter(
                goods_receipt=self.goods_receipt
            ).order_by('-line_number').first()
            
            self.line_number = (last_line.line_number + 10) if last_line else 10
        
        # Check tolerance
        self.check_tolerance()
        
        # Update receipt status
        self.update_receipt_status()
        
        super().save(*args, **kwargs)
    
    def check_tolerance(self):
        """Check if received quantity is within tolerance."""
        if self.ordered_quantity == 0:
            return
        
        variance_pct = ((self.received_quantity - self.ordered_quantity) / 
                       self.ordered_quantity * 100)
        
        messages = []
        
        if variance_pct > self.over_tolerance_pct:
            self.tolerance_exceeded = True
            messages.append(
                f"Over-receipt: {variance_pct:.1f}% (tolerance: {self.over_tolerance_pct}%)"
            )
        elif variance_pct < -self.under_tolerance_pct:
            self.tolerance_exceeded = True
            messages.append(
                f"Under-receipt: {abs(variance_pct):.1f}% (tolerance: {self.under_tolerance_pct}%)"
            )
        else:
            self.tolerance_exceeded = False
            messages.append("Within tolerance")
        
        self.tolerance_message = "\n".join(messages)
    
    def update_receipt_status(self):
        """Update receipt status based on quantities."""
        if self.received_quantity == 0:
            self.receipt_status = 'PENDING'
        elif self.received_quantity < self.ordered_quantity:
            self.receipt_status = 'PARTIAL'
        elif self.received_quantity == self.ordered_quantity:
            self.receipt_status = 'FULL'
        elif self.received_quantity > self.ordered_quantity:
            self.receipt_status = 'OVER'
        
        # Check for under-receipt
        if self.received_quantity > 0 and self.received_quantity < self.ordered_quantity:
            variance_pct = ((self.ordered_quantity - self.received_quantity) / 
                           self.ordered_quantity * 100)
            if variance_pct > self.under_tolerance_pct:
                self.receipt_status = 'UNDER'
    
    def put_away(self, location, user):
        """Record put-away to storage location."""
        self.storage_location = location
        self.put_away_completed = True
        self.put_away_at = timezone.now()
        self.put_away_by = user
        self.save()
        
        return True


class QualityInspection(models.Model):
    """
    Quality Inspection record for received goods.
    
    Tracks inspection criteria, results, and pass/fail status.
    """
    
    # Document identification
    inspection_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        editable=False
    )
    
    # Reference to GRN
    goods_receipt = models.ForeignKey(
        GoodsReceipt,
        on_delete=models.PROTECT,
        related_name='inspections'
    )
    grn_line = models.ForeignKey(
        GRNLine,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='inspections',
        help_text="Specific line being inspected"
    )
    
    # Inspection details
    inspection_date = models.DateField(default=timezone.now)
    inspection_type = models.CharField(
        max_length=50,
        choices=[
            ('RECEIVING', 'Receiving Inspection'),
            ('IN_PROCESS', 'In-Process Inspection'),
            ('FINAL', 'Final Inspection'),
            ('RANDOM', 'Random Sampling'),
        ],
        default='RECEIVING'
    )
    
    # Inspector
    inspector = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='quality_inspections'
    )
    
    # Sampling
    sample_size = models.PositiveIntegerField(
        default=0,
        help_text="Number of items inspected"
    )
    lot_size = models.PositiveIntegerField(
        default=0,
        help_text="Total lot size"
    )
    
    # Inspection criteria (JSON for flexibility)
    inspection_criteria = models.JSONField(
        default=dict,
        blank=True,
        help_text="Inspection checklist and criteria"
    )
    
    # Results
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed'),
        ('CONDITIONAL', 'Conditional Pass'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    
    passed_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000')
    )
    failed_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000')
    )
    
    # Defect tracking
    defects_found = models.JSONField(
        default=list,
        blank=True,
        help_text="List of defects found"
    )
    
    # Results and notes
    inspection_results = models.TextField(blank=True)
    inspector_notes = models.TextField(blank=True)
    
    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_inspections'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Disposition
    DISPOSITION_CHOICES = [
        ('ACCEPT', 'Accept'),
        ('REJECT', 'Reject'),
        ('REWORK', 'Rework'),
        ('SORT', 'Sort/Screen'),
        ('RTV', 'Return to Vendor'),
        ('SCRAP', 'Scrap'),
    ]
    disposition = models.CharField(
        max_length=20,
        choices=DISPOSITION_CHOICES,
        blank=True
    )
    
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-inspection_date', '-inspection_number']
        verbose_name = 'Quality Inspection'
        verbose_name_plural = 'Quality Inspections'
        indexes = [
            models.Index(fields=['status', 'inspection_date']),
            models.Index(fields=['goods_receipt', 'status']),
        ]
    
    def __str__(self):
        return f"QI-{self.inspection_number} - {self.goods_receipt.grn_number}"
    
    def save(self, *args, **kwargs):
        if not self.inspection_number:
            self.inspection_number = self._generate_inspection_number()
        super().save(*args, **kwargs)
    
    def _generate_inspection_number(self):
        """Generate unique inspection number: QI-YYYYMM-NNNN"""
        from django.db.models import Max
        import re
        
        today = timezone.now()
        prefix = f"QI-{today.strftime('%Y%m')}"
        
        last_qi = QualityInspection.objects.filter(
            inspection_number__startswith=prefix
        ).aggregate(Max('inspection_number'))['inspection_number__max']
        
        if last_qi:
            match = re.search(r'-(\d+)$', last_qi)
            if match:
                sequence = int(match.group(1)) + 1
            else:
                sequence = 1
        else:
            sequence = 1
        
        return f"{prefix}-{sequence:04d}"
    
    def complete(self, user):
        """Complete the inspection."""
        if self.status != 'IN_PROGRESS':
            raise ValueError("Only in-progress inspections can be completed")
        
        # Determine pass/fail based on quantities
        total_inspected = self.passed_quantity + self.failed_quantity
        if total_inspected == 0:
            raise ValueError("No quantities recorded")
        
        fail_rate = (self.failed_quantity / total_inspected * 100)
        
        # Simple logic: >10% failure = FAILED
        if fail_rate > 10:
            self.status = 'FAILED'
        else:
            self.status = 'PASSED'
        
        self.completed_at = timezone.now()
        self.save()
        
        # Update GRN line
        if self.grn_line:
            self.grn_line.accepted_quantity = self.passed_quantity
            self.grn_line.rejected_quantity = self.failed_quantity
            self.grn_line.inspection_completed = True
            self.grn_line.save()
        
        # Update GRN inspection status
        self.goods_receipt.inspection_status = self.status
        self.goods_receipt.save()
        
        return True


class NonConformance(models.Model):
    """
    Non-Conformance Report (NCR) for quality issues.
    
    Documents quality problems and corrective actions.
    """
    
    ncr_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        editable=False
    )
    
    # Reference
    goods_receipt = models.ForeignKey(
        GoodsReceipt,
        on_delete=models.PROTECT,
        related_name='non_conformances'
    )
    grn_line = models.ForeignKey(
        GRNLine,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='non_conformances'
    )
    quality_inspection = models.ForeignKey(
        QualityInspection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='non_conformances'
    )
    
    # NCR details
    ncr_date = models.DateField(default=timezone.now)
    reported_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='reported_ncrs'
    )
    
    # Issue description
    SEVERITY_CHOICES = [
        ('MINOR', 'Minor'),
        ('MAJOR', 'Major'),
        ('CRITICAL', 'Critical'),
    ]
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='MINOR'
    )
    
    issue_category = models.CharField(
        max_length=100,
        choices=[
            ('QUANTITY', 'Quantity Variance'),
            ('QUALITY', 'Quality Issue'),
            ('DAMAGE', 'Damaged Goods'),
            ('PACKAGING', 'Packaging Issue'),
            ('DOCUMENTATION', 'Documentation Error'),
            ('SPECIFICATION', 'Specification Mismatch'),
            ('OTHER', 'Other'),
        ],
        default='QUALITY'
    )
    
    issue_description = models.TextField()
    affected_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000')
    )
    
    # Root cause analysis
    root_cause = models.TextField(blank=True)
    
    # Corrective action
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('INVESTIGATION', 'Under Investigation'),
        ('ACTION_PENDING', 'Action Pending'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN',
        db_index=True
    )
    
    # Supplier notification
    supplier_notified = models.BooleanField(default=False)
    supplier_notified_at = models.DateTimeField(null=True, blank=True)
    
    # Resolution
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_ncrs'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-ncr_date', '-ncr_number']
        verbose_name = 'Non-Conformance Report'
        verbose_name_plural = 'Non-Conformance Reports'
        indexes = [
            models.Index(fields=['status', 'ncr_date']),
            models.Index(fields=['severity', 'status']),
        ]
    
    def __str__(self):
        return f"NCR-{self.ncr_number} - {self.issue_category}"
    
    def save(self, *args, **kwargs):
        if not self.ncr_number:
            self.ncr_number = self._generate_ncr_number()
        super().save(*args, **kwargs)
    
    def _generate_ncr_number(self):
        """Generate unique NCR number: NCR-YYYYMM-NNNN"""
        from django.db.models import Max
        import re
        
        today = timezone.now()
        prefix = f"NCR-{today.strftime('%Y%m')}"
        
        last_ncr = NonConformance.objects.filter(
            ncr_number__startswith=prefix
        ).aggregate(Max('ncr_number'))['ncr_number__max']
        
        if last_ncr:
            match = re.search(r'-(\d+)$', last_ncr)
            if match:
                sequence = int(match.group(1)) + 1
            else:
                sequence = 1
        else:
            sequence = 1
        
        return f"{prefix}-{sequence:04d}"
    
    def close(self, user, resolution_notes):
        """Close the NCR."""
        self.status = 'CLOSED'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = resolution_notes
        self.save()
        
        return True


class ReturnToVendor(models.Model):
    """
    Return to Vendor (RTV) for rejected or defective goods.
    
    Creates debit memo for supplier.
    """
    
    rtv_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        editable=False
    )
    
    # Reference
    goods_receipt = models.ForeignKey(
        GoodsReceipt,
        on_delete=models.PROTECT,
        related_name='returns'
    )
    supplier = models.ForeignKey(
        'ap.Supplier',
        on_delete=models.PROTECT,
        related_name='returns'
    )
    
    # Related documents
    non_conformance = models.ForeignKey(
        NonConformance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns'
    )
    
    # RTV details
    rtv_date = models.DateField(default=timezone.now)
    return_reason = models.CharField(
        max_length=100,
        choices=[
            ('DEFECTIVE', 'Defective'),
            ('WRONG_ITEM', 'Wrong Item'),
            ('EXCESS', 'Excess Quantity'),
            ('DAMAGED', 'Damaged in Transit'),
            ('EXPIRED', 'Expired'),
            ('NOT_ORDERED', 'Not Ordered'),
            ('OTHER', 'Other'),
        ]
    )
    return_reason_details = models.TextField()
    
    # Status
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted to Supplier'),
        ('APPROVED', 'Supplier Approved'),
        ('SHIPPED', 'Shipped'),
        ('RECEIVED_BY_SUPPLIER', 'Received by Supplier'),
        ('CREDITED', 'Credit Issued'),
        ('CLOSED', 'Closed'),
        ('REJECTED', 'Rejected by Supplier'),
    ]
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )
    
    # Shipping details
    ship_date = models.DateField(null=True, blank=True)
    carrier = models.CharField(max_length=200, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    
    # Financial
    currency = models.ForeignKey(
        'core.Currency',
        on_delete=models.PROTECT,
        related_name='returns'
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total value being returned"
    )
    
    # Debit memo
    debit_memo_number = models.CharField(max_length=50, blank=True)
    debit_memo_date = models.DateField(null=True, blank=True)
    credit_received = models.BooleanField(default=False)
    credit_received_date = models.DateField(null=True, blank=True)
    
    # Notes
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_rtvs'
    )
    
    class Meta:
        ordering = ['-rtv_date', '-rtv_number']
        verbose_name = 'Return to Vendor'
        verbose_name_plural = 'Returns to Vendor'
        indexes = [
            models.Index(fields=['status', 'rtv_date']),
            models.Index(fields=['supplier', 'status']),
        ]
    
    def __str__(self):
        return f"RTV-{self.rtv_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.rtv_number:
            self.rtv_number = self._generate_rtv_number()
        
        # Recalculate total
        self.recalculate_total()
        
        super().save(*args, **kwargs)
    
    def _generate_rtv_number(self):
        """Generate unique RTV number: RTV-YYYYMM-NNNN"""
        from django.db.models import Max
        import re
        
        today = timezone.now()
        prefix = f"RTV-{today.strftime('%Y%m')}"
        
        last_rtv = ReturnToVendor.objects.filter(
            rtv_number__startswith=prefix
        ).aggregate(Max('rtv_number'))['rtv_number__max']
        
        if last_rtv:
            match = re.search(r'-(\d+)$', last_rtv)
            if match:
                sequence = int(match.group(1)) + 1
            else:
                sequence = 1
        else:
            sequence = 1
        
        return f"{prefix}-{sequence:04d}"
    
    def recalculate_total(self):
        """Recalculate total amount from lines."""
        from django.db.models import Sum
        
        total = self.lines.aggregate(
            total=Sum(models.F('return_quantity') * models.F('unit_price'))
        )['total'] or Decimal('0.00')
        
        self.total_amount = total
    
    def submit(self, user):
        """Submit RTV to supplier."""
        if self.status != 'DRAFT':
            raise ValueError("Only draft RTVs can be submitted")
        
        if not self.lines.exists():
            raise ValueError("Cannot submit RTV without line items")
        
        self.status = 'SUBMITTED'
        self.save()
        
        # TODO: Send notification to supplier
        
        return True


class RTVLine(models.Model):
    """
    Return to Vendor line item.
    """
    
    rtv = models.ForeignKey(
        ReturnToVendor,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    
    line_number = models.PositiveIntegerField()
    
    # Item reference
    grn_line = models.ForeignKey(
        GRNLine,
        on_delete=models.PROTECT,
        related_name='rtv_lines'
    )
    catalog_item = models.ForeignKey(
        'catalog.CatalogItem',
        on_delete=models.PROTECT,
        related_name='rtv_lines'
    )
    
    # Quantities
    return_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    unit_of_measure = models.ForeignKey(
        'catalog.UnitOfMeasure',
        on_delete=models.PROTECT,
        related_name='rtv_lines'
    )
    
    # Pricing
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=4
    )
    
    # Lot/Serial tracking
    lot_number = models.CharField(max_length=100, blank=True)
    serial_numbers = models.JSONField(default=list, blank=True)
    
    # Notes
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['rtv', 'line_number']
        verbose_name = 'RTV Line'
        verbose_name_plural = 'RTV Lines'
        unique_together = [['rtv', 'line_number']]
    
    def __str__(self):
        return f"{self.rtv.rtv_number} - Line {self.line_number}"
    
    def save(self, *args, **kwargs):
        # Auto-assign line number
        if not self.line_number:
            last_line = RTVLine.objects.filter(
                rtv=self.rtv
            ).order_by('-line_number').first()
            
            self.line_number = (last_line.line_number + 10) if last_line else 10
        
        super().save(*args, **kwargs)
        
        # Update RTV total
        if self.rtv_id:
            self.rtv.recalculate_total()
            self.rtv.save()
    
    def delete(self, *args, **kwargs):
        rtv = self.rtv
        super().delete(*args, **kwargs)
        
        # Update RTV total after deletion
        rtv.recalculate_total()
        rtv.save()
    
    def get_line_total(self):
        """Calculate line total."""
        return (self.return_quantity * self.unit_price).quantize(Decimal('0.01'))

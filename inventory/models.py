"""
Inventory Management Models

Features:
- Real-time inventory balances by warehouse/location
- Stock movements (receipts, issues, transfers, adjustments)
- Lot/batch tracking
- Serial number tracking
- Inventory valuation (FIFO, weighted average)
- Cycle counting and stock adjustments
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models import Sum, F, Q
from decimal import Decimal
import json


class InventoryBalance(models.Model):
    """
    Real-time inventory balance by item, warehouse, and location.
    Single source of truth for stock quantities.
    """
    
    # Item reference (from catalog)
    catalog_item = models.ForeignKey(
        'catalog.CatalogItem',
        on_delete=models.PROTECT,
        related_name='inventory_balances'
    )
    
    # Location
    warehouse = models.ForeignKey(
        'receiving.Warehouse',
        on_delete=models.PROTECT,
        related_name='inventory_balances'
    )
    storage_location = models.ForeignKey(
        'receiving.StorageLocation',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='inventory_balances',
        help_text="Specific bin location (optional)"
    )
    
    # Lot/Batch tracking
    lot_number = models.CharField(max_length=100, blank=True, db_index=True)
    
    # Quantities
    quantity_on_hand = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Physical quantity available"
    )
    quantity_reserved = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Quantity reserved for orders"
    )
    quantity_in_transit = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Quantity being transferred"
    )
    
    # Calculated field
    @property
    def quantity_available(self):
        """Available quantity = On Hand - Reserved"""
        return self.quantity_on_hand - self.quantity_reserved
    
    # Valuation
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Current average unit cost"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_movement_date = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_balance'
        ordering = ['warehouse', 'catalog_item']
        verbose_name = 'Inventory Balance'
        verbose_name_plural = 'Inventory Balances'
        unique_together = [['catalog_item', 'warehouse', 'storage_location', 'lot_number']]
        indexes = [
            models.Index(fields=['catalog_item', 'warehouse']),
            models.Index(fields=['warehouse', 'quantity_on_hand']),
            models.Index(fields=['lot_number']),
        ]
    
    def __str__(self):
        loc = f" - {self.storage_location.code}" if self.storage_location else ""
        lot = f" - Lot: {self.lot_number}" if self.lot_number else ""
        return f"{self.catalog_item.sku} @ {self.warehouse.code}{loc}{lot}: {self.quantity_on_hand}"
    
    @classmethod
    def get_or_create_balance(cls, catalog_item, warehouse, storage_location=None, lot_number=''):
        """Get or create inventory balance record"""
        balance, created = cls.objects.get_or_create(
            catalog_item=catalog_item,
            warehouse=warehouse,
            storage_location=storage_location,
            lot_number=lot_number,
            defaults={
                'quantity_on_hand': Decimal('0.0000'),
                'quantity_reserved': Decimal('0.0000'),
                'quantity_in_transit': Decimal('0.0000'),
                'unit_cost': Decimal('0.0000'),
            }
        )
        return balance


class StockMovement(models.Model):
    """
    Stock movements tracking all inventory transactions.
    Audit trail for every inventory change.
    """
    
    MOVEMENT_TYPES = [
        # Inbound
        ('RECEIPT', 'Goods Receipt'),
        ('PURCHASE_RETURN', 'Return from Purchase'),
        ('TRANSFER_IN', 'Transfer In'),
        ('PRODUCTION_IN', 'Production Receipt'),
        ('ADJUSTMENT_IN', 'Adjustment Increase'),
        
        # Outbound
        ('ISSUE', 'Inventory Issue'),
        ('SALES_RETURN', 'Sales Return'),
        ('TRANSFER_OUT', 'Transfer Out'),
        ('PRODUCTION_OUT', 'Production Issue'),
        ('ADJUSTMENT_OUT', 'Adjustment Decrease'),
        ('SCRAP', 'Scrap/Write-off'),
    ]
    
    # Movement details
    movement_number = models.CharField(max_length=50, unique=True, db_index=True)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    movement_date = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Item
    catalog_item = models.ForeignKey(
        'catalog.CatalogItem',
        on_delete=models.PROTECT,
        related_name='stock_movements'
    )
    
    # Location (From/To)
    from_warehouse = models.ForeignKey(
        'receiving.Warehouse',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movements_out'
    )
    from_location = models.ForeignKey(
        'receiving.StorageLocation',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movements_out'
    )
    
    to_warehouse = models.ForeignKey(
        'receiving.Warehouse',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movements_in'
    )
    to_location = models.ForeignKey(
        'receiving.StorageLocation',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movements_in'
    )
    
    # Quantity
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    
    # Lot/Batch
    lot_number = models.CharField(max_length=100, blank=True, db_index=True)
    serial_numbers = models.JSONField(default=list, blank=True)
    
    # Costing
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000')
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Reference documents
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.IntegerField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # User tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='stock_movements'
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_stock_movement'
        ordering = ['-movement_date', '-movement_number']
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        indexes = [
            models.Index(fields=['movement_type', 'movement_date']),
            models.Index(fields=['catalog_item', 'movement_date']),
            models.Index(fields=['from_warehouse', 'movement_date']),
            models.Index(fields=['to_warehouse', 'movement_date']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]
    
    def __str__(self):
        return f"{self.movement_number} - {self.get_movement_type_display()}"
    
    def save(self, *args, **kwargs):
        # Generate movement number
        if not self.movement_number:
            self.movement_number = self._generate_movement_number()
        
        # Calculate total value
        self.total_value = self.quantity * self.unit_cost
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update inventory balances
        if is_new:
            self.update_inventory_balances()
    
    def _generate_movement_number(self):
        """Generate unique movement number"""
        from django.db.models import Max
        
        prefix = f"STK-{timezone.now().strftime('%Y%m')}"
        last_movement = StockMovement.objects.filter(
            movement_number__startswith=prefix
        ).aggregate(Max('movement_number'))['movement_number__max']
        
        if last_movement:
            last_number = int(last_movement.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}-{new_number:05d}"
    
    def update_inventory_balances(self):
        """Update inventory balance records based on movement"""
        
        # Outbound movements (decrease inventory)
        if self.movement_type in ['ISSUE', 'TRANSFER_OUT', 'PRODUCTION_OUT', 
                                   'ADJUSTMENT_OUT', 'SCRAP', 'SALES_RETURN']:
            if self.from_warehouse:
                balance = InventoryBalance.get_or_create_balance(
                    self.catalog_item,
                    self.from_warehouse,
                    self.from_location,
                    self.lot_number
                )
                balance.quantity_on_hand -= self.quantity
                balance.last_movement_date = self.movement_date
                balance.save()
        
        # Inbound movements (increase inventory)
        if self.movement_type in ['RECEIPT', 'TRANSFER_IN', 'PRODUCTION_IN', 
                                   'ADJUSTMENT_IN', 'PURCHASE_RETURN']:
            if self.to_warehouse:
                balance = InventoryBalance.get_or_create_balance(
                    self.catalog_item,
                    self.to_warehouse,
                    self.to_location,
                    self.lot_number
                )
                balance.quantity_on_hand += self.quantity
                balance.last_movement_date = self.movement_date
                
                # Update weighted average cost for receipts
                if self.movement_type == 'RECEIPT':
                    old_value = balance.quantity_on_hand * balance.unit_cost
                    new_value = self.quantity * self.unit_cost
                    new_qty = balance.quantity_on_hand + self.quantity
                    
                    if new_qty > 0:
                        balance.unit_cost = (old_value + new_value) / new_qty
                
                balance.save()


class StockAdjustment(models.Model):
    """
    Stock adjustments for cycle counts, corrections, and write-offs.
    """
    
    ADJUSTMENT_TYPES = [
        ('CYCLE_COUNT', 'Cycle Count'),
        ('PHYSICAL_COUNT', 'Physical Inventory Count'),
        ('DAMAGE', 'Damage/Loss'),
        ('OBSOLETE', 'Obsolescence'),
        ('CORRECTION', 'Data Correction'),
        ('WRITE_OFF', 'Write-off'),
        ('FOUND', 'Found Inventory'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('POSTED', 'Posted'),
        ('REJECTED', 'Rejected'),
    ]
    
    # Header
    adjustment_number = models.CharField(max_length=50, unique=True, db_index=True)
    adjustment_date = models.DateField(default=timezone.now)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Location
    warehouse = models.ForeignKey(
        'receiving.Warehouse',
        on_delete=models.PROTECT,
        related_name='stock_adjustments'
    )
    
    # Description
    description = models.TextField()
    notes = models.TextField(blank=True)
    
    # Approval
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='submitted_adjustments'
    )
    submitted_date = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='approved_adjustments'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Posting
    posted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='posted_adjustments'
    )
    posted_date = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_stock_adjustment'
        ordering = ['-adjustment_date', '-adjustment_number']
        verbose_name = 'Stock Adjustment'
        verbose_name_plural = 'Stock Adjustments'
        indexes = [
            models.Index(fields=['status', 'adjustment_date']),
            models.Index(fields=['warehouse', 'status']),
        ]
    
    def __str__(self):
        return f"{self.adjustment_number} - {self.get_adjustment_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.adjustment_number:
            self.adjustment_number = self._generate_adjustment_number()
        super().save(*args, **kwargs)
    
    def _generate_adjustment_number(self):
        """Generate unique adjustment number"""
        from django.db.models import Max
        
        prefix = f"ADJ-{timezone.now().strftime('%Y%m')}"
        last_adj = StockAdjustment.objects.filter(
            adjustment_number__startswith=prefix
        ).aggregate(Max('adjustment_number'))['adjustment_number__max']
        
        if last_adj:
            last_number = int(last_adj.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}-{new_number:05d}"
    
    def post(self, user):
        """Post adjustment and create stock movements"""
        if self.status != 'APPROVED':
            raise ValueError("Only approved adjustments can be posted")
        
        for line in self.lines.all():
            if line.adjustment_quantity != 0:
                # Create stock movement
                movement_type = 'ADJUSTMENT_IN' if line.adjustment_quantity > 0 else 'ADJUSTMENT_OUT'
                
                StockMovement.objects.create(
                    movement_type=movement_type,
                    movement_date=timezone.now(),
                    catalog_item=line.catalog_item,
                    to_warehouse=self.warehouse if line.adjustment_quantity > 0 else None,
                    to_location=line.storage_location if line.adjustment_quantity > 0 else None,
                    from_warehouse=self.warehouse if line.adjustment_quantity < 0 else None,
                    from_location=line.storage_location if line.adjustment_quantity < 0 else None,
                    quantity=abs(line.adjustment_quantity),
                    lot_number=line.lot_number,
                    unit_cost=line.unit_cost,
                    reference_type='StockAdjustment',
                    reference_id=self.id,
                    reference_number=self.adjustment_number,
                    notes=f"Adjustment: {self.description}",
                    created_by=user
                )
        
        self.status = 'POSTED'
        self.posted_by = user
        self.posted_date = timezone.now()
        self.save()


class StockAdjustmentLine(models.Model):
    """
    Line items for stock adjustments.
    """
    adjustment = models.ForeignKey(
        StockAdjustment,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.IntegerField()
    
    # Item
    catalog_item = models.ForeignKey(
        'catalog.CatalogItem',
        on_delete=models.PROTECT,
        related_name='adjustment_lines'
    )
    storage_location = models.ForeignKey(
        'receiving.StorageLocation',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    lot_number = models.CharField(max_length=100, blank=True)
    
    # Quantities
    system_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Quantity per system"
    )
    physical_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Actual counted quantity"
    )
    adjustment_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Difference (Physical - System)"
    )
    
    # Costing
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4)
    adjustment_value = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Notes
    reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'inventory_stock_adjustment_line'
        ordering = ['adjustment', 'line_number']
        unique_together = [['adjustment', 'line_number']]
    
    def __str__(self):
        return f"{self.adjustment.adjustment_number} - Line {self.line_number}"
    
    def save(self, *args, **kwargs):
        # Calculate adjustment quantity
        self.adjustment_quantity = self.physical_quantity - self.system_quantity
        self.adjustment_value = self.adjustment_quantity * self.unit_cost
        super().save(*args, **kwargs)


class StockTransfer(models.Model):
    """
    Stock transfers between warehouses or locations.
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('IN_TRANSIT', 'In Transit'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Header
    transfer_number = models.CharField(max_length=50, unique=True, db_index=True)
    transfer_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # From/To
    from_warehouse = models.ForeignKey(
        'receiving.Warehouse',
        on_delete=models.PROTECT,
        related_name='transfers_out'
    )
    to_warehouse = models.ForeignKey(
        'receiving.Warehouse',
        on_delete=models.PROTECT,
        related_name='transfers_in'
    )
    
    # Expected delivery
    expected_date = models.DateField(null=True, blank=True)
    actual_received_date = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # User tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_transfers'
    )
    received_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='received_transfers'
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_stock_transfer'
        ordering = ['-transfer_date', '-transfer_number']
        verbose_name = 'Stock Transfer'
        verbose_name_plural = 'Stock Transfers'
        indexes = [
            models.Index(fields=['status', 'transfer_date']),
            models.Index(fields=['from_warehouse', 'status']),
            models.Index(fields=['to_warehouse', 'status']),
        ]
    
    def __str__(self):
        return f"{self.transfer_number} - {self.from_warehouse.code} → {self.to_warehouse.code}"
    
    def save(self, *args, **kwargs):
        if not self.transfer_number:
            self.transfer_number = self._generate_transfer_number()
        super().save(*args, **kwargs)
    
    def _generate_transfer_number(self):
        """Generate unique transfer number"""
        from django.db.models import Max
        
        prefix = f"TRF-{timezone.now().strftime('%Y%m')}"
        last_transfer = StockTransfer.objects.filter(
            transfer_number__startswith=prefix
        ).aggregate(Max('transfer_number'))['transfer_number__max']
        
        if last_transfer:
            last_number = int(last_transfer.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}-{new_number:05d}"
    
    def ship(self, user):
        """Ship the transfer (create outbound movements)"""
        if self.status != 'DRAFT':
            raise ValueError("Only draft transfers can be shipped")
        
        for line in self.lines.all():
            StockMovement.objects.create(
                movement_type='TRANSFER_OUT',
                movement_date=timezone.now(),
                catalog_item=line.catalog_item,
                from_warehouse=self.from_warehouse,
                from_location=line.from_location,
                quantity=line.quantity,
                lot_number=line.lot_number,
                serial_numbers=line.serial_numbers,
                unit_cost=line.unit_cost,
                reference_type='StockTransfer',
                reference_id=self.id,
                reference_number=self.transfer_number,
                notes=f"Transfer to {self.to_warehouse.code}",
                created_by=user
            )
        
        self.status = 'IN_TRANSIT'
        self.save()
    
    def receive(self, user):
        """Receive the transfer (create inbound movements)"""
        if self.status != 'IN_TRANSIT':
            raise ValueError("Only in-transit transfers can be received")
        
        for line in self.lines.all():
            StockMovement.objects.create(
                movement_type='TRANSFER_IN',
                movement_date=timezone.now(),
                catalog_item=line.catalog_item,
                to_warehouse=self.to_warehouse,
                to_location=line.to_location,
                quantity=line.quantity,
                lot_number=line.lot_number,
                serial_numbers=line.serial_numbers,
                unit_cost=line.unit_cost,
                reference_type='StockTransfer',
                reference_id=self.id,
                reference_number=self.transfer_number,
                notes=f"Transfer from {self.from_warehouse.code}",
                created_by=user
            )
        
        self.status = 'RECEIVED'
        self.received_by = user
        self.actual_received_date = timezone.now()
        self.save()


class StockTransferLine(models.Model):
    """
    Line items for stock transfers.
    """
    transfer = models.ForeignKey(
        StockTransfer,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.IntegerField()
    
    # Item
    catalog_item = models.ForeignKey(
        'catalog.CatalogItem',
        on_delete=models.PROTECT,
        related_name='transfer_lines'
    )
    
    # From/To locations
    from_location = models.ForeignKey(
        'receiving.StorageLocation',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transfer_lines_out'
    )
    to_location = models.ForeignKey(
        'receiving.StorageLocation',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transfer_lines_in'
    )
    
    # Quantity
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    
    # Lot/Serial
    lot_number = models.CharField(max_length=100, blank=True)
    serial_numbers = models.JSONField(default=list, blank=True)
    
    # Costing
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'inventory_stock_transfer_line'
        ordering = ['transfer', 'line_number']
        unique_together = [['transfer', 'line_number']]
    
    def __str__(self):
        return f"{self.transfer.transfer_number} - Line {self.line_number}"

"""
Inventory Management Services

Business logic for inventory operations and integration with other modules.
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import InventoryBalance, StockMovement


class InventoryService:
    """Service class for inventory operations"""
    
    @staticmethod
    @transaction.atomic
    def receive_goods(grn, user):
        """
        Create inventory receipt from GoodsReceipt.
        Called when GRN is posted/confirmed.
        
        Posting behavior:
        - CATEGORIZED_GOODS: Posts to inventory (catalog items ONLY)
        - UNCATEGORIZED_GOODS: Does NOT post to inventory (goes to expenses)
        - SERVICES: Does NOT post to inventory (goes to expenses)
        
        Args:
            grn: GoodsReceipt instance
            user: User posting the receipt
        """
        # Only CATEGORIZED_GOODS post to inventory
        if grn.grn_type != 'CATEGORIZED_GOODS':
            # Uncategorized goods and services don't post to inventory
            print(f"✓ GRN {grn.grn_number}: {grn.grn_type} type - skipping inventory posting (goes to expenses)")
            return
        
        # CATEGORIZED_GOODS: Post to inventory
        print(f"✓ GRN {grn.grn_number}: CATEGORIZED_GOODS type - posting to inventory")
        
        for line in grn.lines.all():
            # Skip if no quantity received
            if line.received_quantity <= 0:
                continue
            
            # Skip if no catalog item
            if not line.catalog_item:
                print(f"  ⚠ Line {line.line_number}: No catalog item - skipping")
                continue
            
            # Create stock movement for cataloged items
            movement = StockMovement.objects.create(
                movement_type='RECEIPT',
                movement_date=grn.receipt_date or timezone.now(),
                catalog_item=line.catalog_item,
                to_warehouse=grn.warehouse,
                to_location=line.put_away_location,
                quantity=line.received_quantity,
                lot_number=line.lot_number or '',
                serial_numbers=line.serial_numbers or [],
                unit_cost=line.unit_price,  # Use PO price as cost
                reference_type='GoodsReceipt',
                reference_id=grn.id,
                reference_number=grn.grn_number,
                notes=f"Goods Receipt from PO {grn.po_header.po_number if grn.po_header else grn.po_reference}",
                created_by=user
            )
            
            print(f"  ✓ Line {line.line_number}: Posted {line.received_quantity} {line.uom} of {line.catalog_item.item_name}")
            
            # Update inventory balance (already handled by StockMovement.save())
            # But we can explicitly verify/update
            balance = InventoryBalance.get_or_create_balance(
                catalog_item=line.catalog_item,
                warehouse=grn.warehouse,
                storage_location=line.put_away_location,
                lot_number=line.lot_number or ''
            )
    
    @staticmethod
    @transaction.atomic
    def issue_goods(catalog_item, warehouse, quantity, user, notes='', 
                    storage_location=None, lot_number='', reference_type='',
                    reference_id=None, reference_number=''):
        """
        Issue goods from inventory (for sales orders, production, etc.)
        
        Args:
            catalog_item: CatalogItem instance
            warehouse: Warehouse instance
            quantity: Quantity to issue
            user: User issuing the goods
            notes: Optional notes
            storage_location: Optional StorageLocation
            lot_number: Optional lot number
            reference_type: Type of reference document (e.g., 'SalesOrder')
            reference_id: ID of reference document
            reference_number: Number of reference document
        
        Returns:
            StockMovement instance
        
        Raises:
            ValueError: If insufficient stock
        """
        # Check available quantity
        balance = InventoryBalance.objects.filter(
            catalog_item=catalog_item,
            warehouse=warehouse,
            storage_location=storage_location,
            lot_number=lot_number
        ).first()
        
        if not balance or balance.quantity_available < quantity:
            available = balance.quantity_available if balance else Decimal('0')
            raise ValueError(
                f"Insufficient stock. Required: {quantity}, Available: {available}"
            )
        
        # Create stock movement
        movement = StockMovement.objects.create(
            movement_type='ISSUE',
            movement_date=timezone.now(),
            catalog_item=catalog_item,
            from_warehouse=warehouse,
            from_location=storage_location,
            quantity=quantity,
            lot_number=lot_number,
            unit_cost=balance.unit_cost,
            reference_type=reference_type,
            reference_id=reference_id,
            reference_number=reference_number,
            notes=notes,
            created_by=user
        )
        
        return movement
    
    @staticmethod
    @transaction.atomic
    def transfer_stock(catalog_item, from_warehouse, to_warehouse, quantity, user,
                      from_location=None, to_location=None, lot_number='', notes=''):
        """
        Transfer stock between warehouses.
        Creates both outbound and inbound movements.
        
        Args:
            catalog_item: CatalogItem instance
            from_warehouse: Source Warehouse
            to_warehouse: Destination Warehouse
            quantity: Quantity to transfer
            user: User performing transfer
            from_location: Optional source StorageLocation
            to_location: Optional destination StorageLocation
            lot_number: Optional lot number
            notes: Optional notes
        
        Returns:
            Tuple of (outbound_movement, inbound_movement)
        
        Raises:
            ValueError: If insufficient stock
        """
        # Check available quantity
        balance = InventoryBalance.objects.filter(
            catalog_item=catalog_item,
            warehouse=from_warehouse,
            storage_location=from_location,
            lot_number=lot_number
        ).first()
        
        if not balance or balance.quantity_available < quantity:
            available = balance.quantity_available if balance else Decimal('0')
            raise ValueError(
                f"Insufficient stock. Required: {quantity}, Available: {available}"
            )
        
        # Create outbound movement
        movement_out = StockMovement.objects.create(
            movement_type='TRANSFER_OUT',
            movement_date=timezone.now(),
            catalog_item=catalog_item,
            from_warehouse=from_warehouse,
            from_location=from_location,
            quantity=quantity,
            lot_number=lot_number,
            unit_cost=balance.unit_cost,
            notes=f"Transfer to {to_warehouse.code}: {notes}",
            created_by=user
        )
        
        # Create inbound movement
        movement_in = StockMovement.objects.create(
            movement_type='TRANSFER_IN',
            movement_date=timezone.now(),
            catalog_item=catalog_item,
            to_warehouse=to_warehouse,
            to_location=to_location,
            quantity=quantity,
            lot_number=lot_number,
            unit_cost=balance.unit_cost,
            notes=f"Transfer from {from_warehouse.code}: {notes}",
            created_by=user
        )
        
        return (movement_out, movement_in)
    
    @staticmethod
    def get_available_quantity(catalog_item, warehouse=None, storage_location=None, 
                               lot_number=''):
        """
        Get available quantity for an item.
        
        Args:
            catalog_item: CatalogItem instance
            warehouse: Optional Warehouse filter
            storage_location: Optional StorageLocation filter
            lot_number: Optional lot number filter
        
        Returns:
            Decimal: Total available quantity
        """
        query = InventoryBalance.objects.filter(
            catalog_item=catalog_item,
            is_active=True
        )
        
        if warehouse:
            query = query.filter(warehouse=warehouse)
        if storage_location:
            query = query.filter(storage_location=storage_location)
        if lot_number:
            query = query.filter(lot_number=lot_number)
        
        total = Decimal('0')
        for balance in query:
            total += balance.quantity_available
        
        return total
    
    @staticmethod
    def reserve_stock(catalog_item, warehouse, quantity, storage_location=None, 
                     lot_number=''):
        """
        Reserve stock for sales orders or production.
        
        Args:
            catalog_item: CatalogItem instance
            warehouse: Warehouse instance
            quantity: Quantity to reserve
            storage_location: Optional StorageLocation
            lot_number: Optional lot number
        
        Returns:
            InventoryBalance instance
        
        Raises:
            ValueError: If insufficient available stock
        """
        balance = InventoryBalance.get_or_create_balance(
            catalog_item=catalog_item,
            warehouse=warehouse,
            storage_location=storage_location,
            lot_number=lot_number
        )
        
        if balance.quantity_available < quantity:
            raise ValueError(
                f"Insufficient available stock. Required: {quantity}, "
                f"Available: {balance.quantity_available}"
            )
        
        balance.quantity_reserved += quantity
        balance.save()
        
        return balance
    
    @staticmethod
    def unreserve_stock(catalog_item, warehouse, quantity, storage_location=None,
                       lot_number=''):
        """
        Release reserved stock.
        
        Args:
            catalog_item: CatalogItem instance
            warehouse: Warehouse instance
            quantity: Quantity to unreserve
            storage_location: Optional StorageLocation
            lot_number: Optional lot number
        
        Returns:
            InventoryBalance instance
        """
        balance = InventoryBalance.objects.filter(
            catalog_item=catalog_item,
            warehouse=warehouse,
            storage_location=storage_location,
            lot_number=lot_number
        ).first()
        
        if balance:
            balance.quantity_reserved = max(
                Decimal('0'),
                balance.quantity_reserved - quantity
            )
            balance.save()
        
        return balance

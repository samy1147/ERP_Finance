# procurement/receiving/serializers.py
from rest_framework import serializers
from decimal import Decimal
from .models import (
    Warehouse, GoodsReceipt, GRNLine,
    QualityInspection, NonConformance,
    ReturnToVendor, RTVLine
)
from procurement.purchase_orders.models import POHeader, POLine


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'


class GRNLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = GRNLine
        fields = [
            'id', 'goods_receipt', 'line_number', 'catalog_item',
            'item_description', 'item_type', 'ordered_quantity', 'received_quantity', 
            'unit_of_measure', 'unit_price', 'lot_number', 'expiry_date', 
            'storage_location', 'condition', 'receipt_status', 'remarks',
            'po_line_reference'
        ]
        read_only_fields = ['id', 'line_number', 'goods_receipt', 'item_type']
        extra_kwargs = {
            'catalog_item': {'required': False, 'allow_null': True},
            'unit_of_measure': {'required': False, 'allow_null': True},
            'storage_location': {'required': False, 'allow_null': True},
            'ordered_quantity': {'required': False},
            'item_description': {'required': False, 'allow_blank': True},
            'received_quantity': {'required': False},  # Remove default=0
            'unit_price': {'required': False, 'allow_null': True},
            'condition': {'required': False, 'default': 'GOOD'},
            'receipt_status': {'required': False, 'default': 'PENDING'},
        }


class GoodsReceiptListSerializer(serializers.ModelSerializer):
    # Field aliases for frontend compatibility
    receipt_number = serializers.CharField(source='grn_number', read_only=True)
    purchase_order_number = serializers.CharField(source='po_header.po_number', read_only=True, allow_null=True)
    supplier_name = serializers.SerializerMethodField()
    
    # Backend field names
    po_number = serializers.CharField(source='po_header.po_number', read_only=True, allow_null=True)
    vendor_name = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    
    class Meta:
        model = GoodsReceipt
        fields = [
            'id', 'grn_number', 'receipt_number', 'grn_type', 
            'po_header', 'po_number', 'purchase_order_number', 'po_reference',
            'supplier', 'vendor_name', 'supplier_name', 'receipt_date', 
            'warehouse', 'warehouse_name', 'status', 
            'delivery_note_number', 'vehicle_number', 'driver_name', 'received_by'
        ]
    
    def get_vendor_name(self, obj):
        if obj.po_header:
            return obj.po_header.vendor_name
        elif obj.supplier:
            return obj.supplier.name
        return None
    
    def get_supplier_name(self, obj):
        """Alias for vendor_name for frontend compatibility"""
        return self.get_vendor_name(obj)


class GoodsReceiptDetailSerializer(serializers.ModelSerializer):
    lines = serializers.SerializerMethodField(read_only=True)  # For reading
    lines_input = serializers.ListField(required=False, write_only=True)  # For writing
    po_number = serializers.CharField(source='po_header.po_number', read_only=True, allow_null=True)
    vendor_name = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    
    class Meta:
        model = GoodsReceipt
        fields = '__all__'
        read_only_fields = ['grn_number']
        extra_kwargs = {
            'supplier': {'required': False, 'allow_null': True},
            'received_by': {'required': False, 'allow_null': True},
            'warehouse': {'required': False, 'allow_null': True},
        }
    
    def get_lines(self, obj):
        """Return lines using the GRNLineSerializer for reading."""
        return GRNLineSerializer(obj.lines.all(), many=True).data
    
    def get_vendor_name(self, obj):
        if obj.po_header:
            return obj.po_header.vendor_name
        elif obj.supplier:
            return obj.supplier.name
        return None
    
    def to_internal_value(self, data):
        """
        Override to map frontend field names to backend field names before validation.
        Frontend sends 'lines' with 'quantity_received', backend expects 'lines_input' with 'received_quantity'.
        """
        # Make a mutable copy of the data
        if hasattr(data, '_mutable'):
            data._mutable = True
        
        print(f"\n>>> to_internal_value called")
        print(f">>> data keys: {data.keys() if hasattr(data, 'keys') else 'N/A'}")
        
        # Map 'lines' to 'lines_input' for processing
        if 'lines' in data:
            lines_data = data.pop('lines')  # Remove 'lines'
            data['lines_input'] = lines_data  # Add as 'lines_input'
            print(f">>> Mapped 'lines' to 'lines_input', count: {len(lines_data)}")
            
            # Map field names within each line
            if isinstance(lines_data, list):
                for i, line in enumerate(lines_data):
                    print(f">>> Processing line {i+1}: {line}")
                    # Map quantity_received to received_quantity
                    if 'quantity_received' in line:
                        line['received_quantity'] = line.pop('quantity_received')
                        print(f">>> Mapped quantity_received to received_quantity: {line['received_quantity']}")
        
        return super().to_internal_value(data)
    
    def create(self, validated_data):
        print("\n" + "="*70)
        print(">>> GoodsReceiptSerializer.create() START")
        print(f">>> validated_data keys: {validated_data.keys()}")
        print("="*70)
        
        # Handle both 'lines' and 'lines_input' for backward compatibility
        lines_data = validated_data.pop('lines_input', None) or validated_data.pop('lines', [])
        
        # DEBUG: Print what we received
        print(f">>> Number of lines extracted: {len(lines_data)}")
        for i, line in enumerate(lines_data):
            print(f"\n>>> Line {i+1} data:")
            for key, value in line.items():
                print(f"    {key}: {value} (type: {type(value).__name__})")
        print("="*70 + "\n")
        
        # Set received_by if not provided
        if not validated_data.get('received_by'):
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                validated_data['received_by'] = request.user
            else:
                # Use default user
                from django.contrib.auth import get_user_model
                User = get_user_model()
                validated_data['received_by'] = User.objects.get(id=2)
        
        # If po_header is provided, auto-fill supplier, po_reference, and grn_type
        if 'po_header' in validated_data and validated_data['po_header']:
            po = validated_data['po_header']
            if not validated_data.get('po_reference'):
                validated_data['po_reference'] = po.po_number
            # Copy PO type to GRN type
            if not validated_data.get('grn_type'):
                validated_data['grn_type'] = po.po_type
        
        # Handle warehouse - create default if needed
        if not validated_data.get('warehouse'):
            warehouse, created = Warehouse.objects.get_or_create(
                code='MAIN',
                defaults={
                    'name': 'Main Warehouse',
                    'warehouse_type': 'STANDARD',
                    'is_active': True
                }
            )
            validated_data['warehouse'] = warehouse
        
        # Handle supplier - create a default one if needed
        if not validated_data.get('supplier'):
            from ap.models import Supplier
            # Try to get default supplier or create one
            supplier, created = Supplier.objects.get_or_create(
                code='DEFAULT',
                defaults={
                    'name': 'Default Supplier',
                    'is_active': True
                }
            )
            validated_data['supplier'] = supplier
        
        # Create the goods receipt
        goods_receipt = GoodsReceipt.objects.create(**validated_data)
        
        # Create receipt lines - simplified without catalog dependencies
        from procurement.catalog.models import CatalogItem, UnitOfMeasure, CatalogCategory
        from core.models import Currency
        
        # Get or create default currency
        default_currency, _ = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'US Dollar',
                'symbol': '$',
                'is_active': True
            }
        )
        
        # Get or create default UOM
        default_uom, _ = UnitOfMeasure.objects.get_or_create(
            code='EA',
            defaults={
                'name': 'Each',
                'description': 'Default unit of measure',
                'is_active': True
            }
        )
        
        # Get or create default category
        default_category, _ = CatalogCategory.objects.get_or_create(
            code='DEFAULT',
            defaults={
                'name': 'Default Category',
                'description': 'Default catalog category',
                'is_active': True
            }
        )
        
        # Get or create default catalog item
        default_item, _ = CatalogItem.objects.get_or_create(
            item_code='DEFAULT',
            defaults={
                'sku': 'DEFAULT-SKU',
                'name': 'Default Item',
                'short_description': 'Default catalog item for receipts without catalog reference',
                'category': default_category,
                'unit_of_measure': default_uom,
                'list_price': Decimal('0.00'),
                'currency': default_currency,
                'is_active': True
            }
        )
        
        line_number = 1
        for line_data in lines_data:
            print(f"\n>>> Processing line {line_number}")
            print(f">>> line_data keys: {line_data.keys()}")
            print(f">>> line_data: {line_data}")
            
            # Map frontend field names to model field names
            # Frontend sends 'quantity_received', backend model expects 'received_quantity'
            # Use .get() instead of .pop() to preserve the value
            quantity_received = line_data.get('quantity_received', None)
            if quantity_received is None:
                quantity_received = line_data.get('received_quantity', None)
            
            print(f">>> Extracted quantity_received: {quantity_received} (type: {type(quantity_received).__name__})")
            
            # Convert to Decimal if it's a string or number
            if quantity_received is not None:
                try:
                    quantity_received = Decimal(str(quantity_received))
                    print(f">>> Converted to Decimal: {quantity_received}")
                except Exception as e:
                    print(f">>> ERROR converting to Decimal: {e}")
                    quantity_received = Decimal('0')
            else:
                print(f">>> quantity_received is None, defaulting to 0")
                quantity_received = Decimal('0')
            
            # Now remove these fields from line_data to avoid conflicts
            line_data.pop('quantity_received', None)
            line_data.pop('received_quantity', None)
            
            location = line_data.pop('location', None)
            notes_field = line_data.pop('notes', None)
            po_line_ref = line_data.pop('po_line', None)
            
            # Remove fields that don't exist in model
            line_data.pop('storage_location', None)
            
            # Set catalog_item if not provided
            if 'catalog_item' not in line_data or line_data['catalog_item'] is None:
                line_data['catalog_item'] = default_item
            
            # Set unit_of_measure if not provided
            if 'unit_of_measure' not in line_data or line_data['unit_of_measure'] is None:
                line_data['unit_of_measure'] = default_uom
            
            # Set required fields
            line_data['line_number'] = line_number
            
            # Fetch ordered_quantity and other details from PO line if available
            po_quantity = None
            if po_line_ref:
                try:
                    from procurement.purchase_orders.models import POLine
                    po_line = POLine.objects.get(id=po_line_ref)
                    line_data['ordered_quantity'] = po_line.quantity
                    po_quantity = po_line.quantity
                    line_data['item_description'] = po_line.item_description or 'Received item'
                    line_data['item_type'] = po_line.item_type  # Copy item categorization status from PO
                    line_data['unit_price'] = po_line.unit_price  # Copy unit price from PO for invoice matching
                    line_data['po_line_reference'] = str(po_line_ref)
                    print(f">>> Set po_line_reference to: {line_data['po_line_reference']}")
                    print(f">>> Copied unit_price: {line_data.get('unit_price')}")
                except Exception as e:
                    print(f">>> ERROR fetching PO line {po_line_ref}: {e}")
                    import traceback
                    traceback.print_exc()
                    line_data['ordered_quantity'] = line_data.get('ordered_quantity', quantity_received)
                    line_data['item_description'] = 'Received item'
                    # Still set the reference even if we can't fetch the PO line
                    line_data['po_line_reference'] = str(po_line_ref)
                    print(f">>> Set po_line_reference anyway: {line_data['po_line_reference']}")
            else:
                # If no PO line reference, use ordered_quantity from data or default to received
                ordered_qty = line_data.get('ordered_quantity', None)
                if ordered_qty:
                    line_data['ordered_quantity'] = Decimal(str(ordered_qty))
                else:
                    line_data['ordered_quantity'] = quantity_received
            
            # CRITICAL: Set received_quantity from frontend input
            # This is the actual quantity received by the warehouse
            line_data['received_quantity'] = quantity_received
            
            # Auto-accept the received quantity for now (can add inspection workflow later)
            line_data['accepted_quantity'] = quantity_received
            line_data['rejected_quantity'] = Decimal('0')
            
            # Set item_description if not already set
            if not line_data.get('item_description'):
                line_data['item_description'] = 'Received item'
            
            # Set remarks from notes
            if notes_field:
                line_data['remarks'] = notes_field
            
            # Set storage_location from location if provided (but field doesn't exist, so skip)
            # line_data['storage_location'] = location if location else None
            
            # Create the line
            GRNLine.objects.create(goods_receipt=goods_receipt, **line_data)
            line_number += 1
        
        # NOTE: Automatic posting disabled - user will manually post via UI
        # This allows users to review GRN before posting to inventory/expenses
        # Posting happens via the post_to_inventory() API endpoint
        
        # # Automatically post to inventory to update PO status
        # try:
        #     print("\n" + "="*70)
        #     print(">>> Auto-posting GRN to inventory...")
        #     print(f">>> GRN ID: {goods_receipt.id}")
        #     print(f">>> GRN Number: {goods_receipt.grn_number}")
        #     print(f">>> PO Header: {goods_receipt.po_header}")
        #     print(f">>> Number of lines: {goods_receipt.lines.count()}")
        #     
        #     for line in goods_receipt.lines.all():
        #         print(f"\n>>> Line {line.line_number}:")
        #         print(f"    po_line_reference: '{line.po_line_reference}'")
        #         print(f"    received_quantity: {line.received_quantity}")
        #     
        #     goods_receipt.post_to_inventory()
        #     print(f"\n>>> GRN posted successfully. Status: {goods_receipt.status}")
        #     
        #     # Check PO status after posting
        #     if goods_receipt.po_header:
        #         po = goods_receipt.po_header
        #         print(f"\n>>> PO Status after posting:")
        #         print(f"    PO Number: {po.po_number}")
        #         print(f"    Status: {po.status}")
        #         print(f"    Delivery Status: {po.delivery_status}")
        #         for po_line in po.lines.all():
        #             print(f"    Line {po_line.line_number}: received {po_line.quantity_received} of {po_line.quantity}")
        #     
        #     print("="*70 + "\n")
        # except Exception as e:
        #     print(f"\n>>> ERROR posting GRN to inventory: {e}")
        #     import traceback
        #     traceback.print_exc()
        #     print("="*70 + "\n")
        
        return goods_receipt


class QualityInspectionSerializer(serializers.ModelSerializer):
    grn_number = serializers.CharField(source='grn.receipt_number', read_only=True)
    inspector_name = serializers.CharField(source='inspector.get_full_name', read_only=True)
    
    class Meta:
        model = QualityInspection
        fields = '__all__'
        read_only_fields = ['inspection_number']


class NonConformanceSerializer(serializers.ModelSerializer):
    inspection_number = serializers.CharField(source='inspection.inspection_number', read_only=True)
    
    class Meta:
        model = NonConformance
        fields = '__all__'


class RTVLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = RTVLine
        fields = '__all__'


class ReturnToVendorSerializer(serializers.ModelSerializer):
    lines = RTVLineSerializer(many=True, read_only=True)
    grn_number = serializers.CharField(source='grn.receipt_number', read_only=True)
    
    class Meta:
        model = ReturnToVendor
        fields = '__all__'
        read_only_fields = ['rtv_number']

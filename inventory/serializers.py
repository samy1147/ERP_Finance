"""
Serializers for Inventory Management API.
"""

from rest_framework import serializers
from .models import (
    InventoryBalance, StockMovement, StockAdjustment, StockAdjustmentLine,
    StockTransfer, StockTransferLine
)


class InventoryBalanceSerializer(serializers.ModelSerializer):
    catalog_item_sku = serializers.CharField(source='catalog_item.sku', read_only=True)
    catalog_item_name = serializers.CharField(source='catalog_item.name', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    location_code = serializers.CharField(source='storage_location.code', read_only=True, allow_null=True)
    quantity_available = serializers.DecimalField(max_digits=15, decimal_places=4, read_only=True)
    
    class Meta:
        model = InventoryBalance
        fields = [
            'id', 'catalog_item', 'catalog_item_sku', 'catalog_item_name',
            'warehouse', 'warehouse_code', 'warehouse_name',
            'storage_location', 'location_code', 'lot_number',
            'quantity_on_hand', 'quantity_reserved', 'quantity_in_transit',
            'quantity_available', 'unit_cost', 'is_active',
            'last_movement_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_movement_date', 'created_at', 'updated_at'
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    catalog_item_sku = serializers.CharField(source='catalog_item.sku', read_only=True)
    catalog_item_name = serializers.CharField(source='catalog_item.name', read_only=True)
    from_warehouse_code = serializers.CharField(source='from_warehouse.code', read_only=True, allow_null=True)
    to_warehouse_code = serializers.CharField(source='to_warehouse.code', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'movement_number', 'movement_type', 'movement_date',
            'catalog_item', 'catalog_item_sku', 'catalog_item_name',
            'from_warehouse', 'from_warehouse_code', 'from_location',
            'to_warehouse', 'to_warehouse_code', 'to_location',
            'quantity', 'lot_number', 'serial_numbers',
            'unit_cost', 'total_value',
            'reference_type', 'reference_id', 'reference_number',
            'notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'movement_number', 'total_value', 'created_at'
        ]


class StockAdjustmentLineSerializer(serializers.ModelSerializer):
    catalog_item_sku = serializers.CharField(source='catalog_item.sku', read_only=True)
    catalog_item_name = serializers.CharField(source='catalog_item.name', read_only=True)
    location_code = serializers.CharField(source='storage_location.code', read_only=True, allow_null=True)
    
    class Meta:
        model = StockAdjustmentLine
        fields = [
            'id', 'line_number', 'catalog_item', 'catalog_item_sku', 'catalog_item_name',
            'storage_location', 'location_code', 'lot_number',
            'system_quantity', 'physical_quantity', 'adjustment_quantity',
            'unit_cost', 'adjustment_value', 'reason'
        ]
        read_only_fields = ['id', 'adjustment_quantity', 'adjustment_value']


class StockAdjustmentSerializer(serializers.ModelSerializer):
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    posted_by_name = serializers.CharField(source='posted_by.username', read_only=True, allow_null=True)
    lines = StockAdjustmentLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = StockAdjustment
        fields = [
            'id', 'adjustment_number', 'adjustment_date', 'adjustment_type', 'status',
            'warehouse', 'warehouse_code', 'warehouse_name',
            'description', 'notes',
            'submitted_by', 'submitted_by_name', 'submitted_date',
            'approved_by', 'approved_by_name', 'approved_date',
            'posted_by', 'posted_by_name', 'posted_date',
            'lines', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'adjustment_number', 'submitted_date', 'approved_date',
            'posted_date', 'created_at', 'updated_at'
        ]


class StockTransferLineSerializer(serializers.ModelSerializer):
    catalog_item_sku = serializers.CharField(source='catalog_item.sku', read_only=True)
    catalog_item_name = serializers.CharField(source='catalog_item.name', read_only=True)
    from_location_code = serializers.CharField(source='from_location.code', read_only=True, allow_null=True)
    to_location_code = serializers.CharField(source='to_location.code', read_only=True, allow_null=True)
    
    class Meta:
        model = StockTransferLine
        fields = [
            'id', 'line_number', 'catalog_item', 'catalog_item_sku', 'catalog_item_name',
            'from_location', 'from_location_code', 'to_location', 'to_location_code',
            'quantity', 'lot_number', 'serial_numbers', 'unit_cost', 'notes'
        ]
        read_only_fields = ['id']


class StockTransferSerializer(serializers.ModelSerializer):
    from_warehouse_code = serializers.CharField(source='from_warehouse.code', read_only=True)
    from_warehouse_name = serializers.CharField(source='from_warehouse.name', read_only=True)
    to_warehouse_code = serializers.CharField(source='to_warehouse.code', read_only=True)
    to_warehouse_name = serializers.CharField(source='to_warehouse.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    received_by_name = serializers.CharField(source='received_by.username', read_only=True, allow_null=True)
    lines = StockTransferLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = StockTransfer
        fields = [
            'id', 'transfer_number', 'transfer_date', 'status',
            'from_warehouse', 'from_warehouse_code', 'from_warehouse_name',
            'to_warehouse', 'to_warehouse_code', 'to_warehouse_name',
            'expected_date', 'actual_received_date', 'notes',
            'created_by', 'created_by_name', 'received_by', 'received_by_name',
            'lines', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transfer_number', 'actual_received_date',
            'created_at', 'updated_at'
        ]

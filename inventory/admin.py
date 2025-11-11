"""
Admin interfaces for Inventory Management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import (
    InventoryBalance, StockMovement, StockAdjustment, StockAdjustmentLine,
    StockTransfer, StockTransferLine
)


@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):
    list_display = [
        'catalog_item', 'warehouse', 'storage_location', 'lot_number',
        'quantity_on_hand', 'quantity_reserved', 'quantity_available_display',
        'unit_cost', 'total_value_display', 'last_movement_date'
    ]
    list_filter = ['warehouse', 'is_active', 'last_movement_date']
    search_fields = ['catalog_item__sku', 'catalog_item__name', 'lot_number']
    readonly_fields = ['created_at', 'updated_at', 'last_movement_date']
    
    fieldsets = (
        ('Item & Location', {
            'fields': ('catalog_item', 'warehouse', 'storage_location', 'lot_number')
        }),
        ('Quantities', {
            'fields': ('quantity_on_hand', 'quantity_reserved', 'quantity_in_transit')
        }),
        ('Costing', {
            'fields': ('unit_cost',)
        }),
        ('Status', {
            'fields': ('is_active', 'last_movement_date')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def quantity_available_display(self, obj):
        available = obj.quantity_available
        color = 'green' if available > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, available
        )
    quantity_available_display.short_description = 'Available'
    
    def total_value_display(self, obj):
        total = obj.quantity_on_hand * obj.unit_cost
        return format_html('${:,.2f}', total)
    total_value_display.short_description = 'Total Value'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'movement_number', 'movement_type', 'movement_date', 'catalog_item',
        'quantity', 'from_warehouse', 'to_warehouse', 'lot_number',
        'unit_cost', 'total_value', 'created_by'
    ]
    list_filter = ['movement_type', 'movement_date', 'from_warehouse', 'to_warehouse']
    search_fields = ['movement_number', 'catalog_item__sku', 'lot_number', 'reference_number']
    readonly_fields = ['movement_number', 'total_value', 'created_at']
    date_hierarchy = 'movement_date'
    
    fieldsets = (
        ('Movement Details', {
            'fields': ('movement_number', 'movement_type', 'movement_date')
        }),
        ('Item', {
            'fields': ('catalog_item', 'quantity', 'lot_number', 'serial_numbers')
        }),
        ('From Location', {
            'fields': ('from_warehouse', 'from_location')
        }),
        ('To Location', {
            'fields': ('to_warehouse', 'to_location')
        }),
        ('Costing', {
            'fields': ('unit_cost', 'total_value')
        }),
        ('Reference', {
            'fields': ('reference_type', 'reference_id', 'reference_number', 'notes')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at')
        }),
    )


class StockAdjustmentLineInline(admin.TabularInline):
    model = StockAdjustmentLine
    extra = 0
    readonly_fields = ['adjustment_quantity', 'adjustment_value']
    fields = [
        'line_number', 'catalog_item', 'storage_location', 'lot_number',
        'system_quantity', 'physical_quantity', 'adjustment_quantity',
        'unit_cost', 'adjustment_value', 'reason'
    ]


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = [
        'adjustment_number', 'adjustment_date', 'adjustment_type', 'status',
        'warehouse', 'total_lines', 'submitted_by', 'approved_by'
    ]
    list_filter = ['status', 'adjustment_type', 'adjustment_date', 'warehouse']
    search_fields = ['adjustment_number', 'description']
    readonly_fields = [
        'adjustment_number', 'submitted_date', 'approved_date', 'posted_date',
        'created_at', 'updated_at'
    ]
    inlines = [StockAdjustmentLineInline]
    date_hierarchy = 'adjustment_date'
    
    fieldsets = (
        ('Header', {
            'fields': ('adjustment_number', 'adjustment_date', 'adjustment_type', 'status')
        }),
        ('Location', {
            'fields': ('warehouse',)
        }),
        ('Details', {
            'fields': ('description', 'notes')
        }),
        ('Workflow', {
            'fields': (
                ('submitted_by', 'submitted_date'),
                ('approved_by', 'approved_date'),
                ('posted_by', 'posted_date')
            )
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_lines(self, obj):
        return obj.lines.count()
    total_lines.short_description = 'Lines'


class StockTransferLineInline(admin.TabularInline):
    model = StockTransferLine
    extra = 0
    fields = [
        'line_number', 'catalog_item', 'from_location', 'to_location',
        'quantity', 'lot_number', 'unit_cost', 'notes'
    ]


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = [
        'transfer_number', 'transfer_date', 'status', 'from_warehouse',
        'to_warehouse', 'total_lines', 'expected_date', 'created_by'
    ]
    list_filter = ['status', 'transfer_date', 'from_warehouse', 'to_warehouse']
    search_fields = ['transfer_number', 'notes']
    readonly_fields = [
        'transfer_number', 'actual_received_date', 'created_at', 'updated_at'
    ]
    inlines = [StockTransferLineInline]
    date_hierarchy = 'transfer_date'
    
    fieldsets = (
        ('Header', {
            'fields': ('transfer_number', 'transfer_date', 'status')
        }),
        ('From/To', {
            'fields': ('from_warehouse', 'to_warehouse')
        }),
        ('Delivery', {
            'fields': ('expected_date', 'actual_received_date')
        }),
        ('Details', {
            'fields': ('notes',)
        }),
        ('Users', {
            'fields': ('created_by', 'received_by')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_lines(self, obj):
        return obj.lines.count()
    total_lines.short_description = 'Lines'

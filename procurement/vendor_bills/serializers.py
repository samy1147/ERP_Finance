"""
Vendor Bill Serializers

Serializers for 3-Way Match & Vendor Bills module.
"""

from rest_framework import serializers
from .models import (
    VendorBill, VendorBillLine, ThreeWayMatch,
    MatchException, MatchTolerance
)
from core.models import Currency


class VendorBillLineSerializer(serializers.ModelSerializer):
    """Serializer for vendor bill line items."""
    
    class Meta:
        model = VendorBillLine
        fields = [
            'id', 'vendor_bill', 'line_number',
            'catalog_item', 'description',
            'quantity', 'unit_of_measure',
            'unit_price', 'line_total',
            'tax_rate', 'tax_amount',
            'po_number', 'po_line_number',
            'grn_number', 'is_matched', 'has_exception',
            'notes'
        ]
        read_only_fields = ['id', 'vendor_bill', 'is_matched', 'has_exception']
        extra_kwargs = {
            'unit_of_measure': {'required': False, 'allow_null': True},
            'catalog_item': {'required': False, 'allow_null': True},
            'tax_rate': {'required': False, 'default': 0},
            'tax_amount': {'required': False, 'default': 0},
            'po_number': {'required': False, 'allow_blank': True},
            'po_line_number': {'required': False, 'allow_null': True},
            'grn_number': {'required': False, 'allow_blank': True},
            'notes': {'required': False, 'allow_blank': True},
        }


class VendorBillSerializer(serializers.ModelSerializer):
    """Serializer for vendor bills."""
    
    lines = VendorBillLineSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    bill_type_display = serializers.CharField(source='get_bill_type_display', read_only=True)
    po_number = serializers.CharField(source='po_header.po_number', read_only=True, allow_null=True)
    grn_number = serializers.CharField(source='grn_header.grn_number', read_only=True, allow_null=True)
    
    class Meta:
        model = VendorBill
        fields = [
            'id', 'bill_number', 'supplier', 'supplier_name',
            'supplier_invoice_number', 'supplier_invoice_date',
            'po_header', 'po_number', 'grn_header', 'grn_number',
            'bill_type', 'bill_type_display', 'bill_date', 'due_date',
            'currency', 'currency_code',
            'exchange_rate', 'subtotal', 'tax_amount', 'total_amount',
            'base_currency_total', 'status', 'status_display',
            'is_matched', 'match_date',
            'has_exceptions', 'exception_count',
            'ap_invoice', 'ap_posted_date', 'ap_posted_by',
            'is_paid', 'paid_date', 'paid_amount',
            'approval_status', 'approved_by', 'approved_date',
            'notes', 'internal_notes',
            'lines', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'bill_number', 'base_currency_total', 'is_matched', 'match_date',
            'has_exceptions', 'exception_count',
            'ap_invoice', 'ap_posted_date', 'ap_posted_by',
            'is_paid', 'paid_date', 'paid_amount',
            'approved_by', 'approved_date',
            'created_by', 'created_at', 'updated_at'
        ]


class VendorBillCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vendor bills with lines."""
    
    lines = VendorBillLineSerializer(many=True)
    
    class Meta:
        model = VendorBill
        fields = [
            'supplier', 'supplier_invoice_number', 'supplier_invoice_date',
            'bill_type', 'bill_date', 'due_date', 
            'currency', 'exchange_rate',
            'subtotal', 'tax_amount', 'total_amount',
            'notes', 'internal_notes', 'lines'
        ]
    
    def create(self, validated_data):
        """Create vendor bill with lines."""
        lines_data = validated_data.pop('lines')
        
        # Set created_by if request context is available
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        try:
            vendor_bill = VendorBill.objects.create(**validated_data)
        except Exception as e:
            import traceback
            print(f"Error creating vendor bill: {e}")
            print(f"Validated data: {validated_data}")
            traceback.print_exc()
            raise
        
        for i, line_data in enumerate(lines_data):
            try:
                # Calculate line_total if not provided
                if 'line_total' not in line_data:
                    quantity = line_data.get('quantity', 0)
                    unit_price = line_data.get('unit_price', 0)
                    line_data['line_total'] = quantity * unit_price
                
                # Set unit_of_measure to a default if not provided
                if 'unit_of_measure' not in line_data or line_data['unit_of_measure'] is None:
                    from procurement.catalog.models import UnitOfMeasure
                    default_uom, _ = UnitOfMeasure.objects.get_or_create(
                        code='EA',
                        defaults={'name': 'Each', 'is_active': True}
                    )
                    line_data['unit_of_measure'] = default_uom
                
                VendorBillLine.objects.create(
                    vendor_bill=vendor_bill,
                    **line_data
                )
            except Exception as e:
                import traceback
                print(f"Error creating line {i}: {e}")
                print(f"Line data: {line_data}")
                traceback.print_exc()
                raise
        
        # Recalculate totals
        vendor_bill.recalculate_totals()
        
        return vendor_bill


class ThreeWayMatchSerializer(serializers.ModelSerializer):
    """Serializer for 3-way match records."""
    
    vendor_bill_number = serializers.CharField(source='vendor_bill_line.vendor_bill.bill_number', read_only=True)
    match_status_display = serializers.CharField(source='get_match_status_display', read_only=True)
    
    class Meta:
        model = ThreeWayMatch
        fields = [
            'id', 'match_number', 'vendor_bill_number',
            'vendor_bill_line', 'po_number', 'po_line_number',
            'grn_line', 'catalog_item',
            'po_quantity', 'po_unit_price',
            'grn_quantity',
            'bill_quantity', 'bill_unit_price',
            'quantity_variance', 'quantity_variance_pct',
            'price_variance', 'price_variance_pct',
            'quantity_tolerance_exceeded', 'price_tolerance_exceeded',
            'match_status', 'match_status_display',
            'has_exception',
            'matched_by', 'matched_date',
            'notes'
        ]
        read_only_fields = [
            'id', 'match_number', 'po_quantity', 'po_unit_price',
            'grn_quantity',
            'bill_quantity', 'bill_unit_price',
            'quantity_variance', 'quantity_variance_pct',
            'price_variance', 'price_variance_pct',
            'quantity_tolerance_exceeded', 'price_tolerance_exceeded',
            'has_exception', 'matched_by', 'matched_date',
        ]


class MatchExceptionSerializer(serializers.ModelSerializer):
    """Serializer for match exceptions."""
    
    vendor_bill_number = serializers.CharField(source='three_way_match.vendor_bill_line.vendor_bill.bill_number', read_only=True)
    match_description = serializers.SerializerMethodField()
    exception_type_display = serializers.CharField(source='get_exception_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    resolution_status_display = serializers.CharField(source='get_resolution_status_display', read_only=True)
    
    class Meta:
        model = MatchException
        fields = [
            'id', 'exception_number', 'vendor_bill_number',
            'three_way_match', 'match_description',
            'exception_type', 'exception_type_display',
            'severity', 'severity_display',
            'resolution_status', 'resolution_status_display',
            'resolution_action', 'resolution_notes',
            'description', 'blocks_posting',
            'variance_amount', 'variance_percentage', 'financial_impact',
            'resolved_by', 'resolved_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'exception_number', 'created_at', 'updated_at',
            'resolved_by', 'resolved_date'
        ]
    
    def get_match_description(self, obj):
        """Get description of the match record."""
        if obj.three_way_match:
            return f"{obj.three_way_match.match_status} - Qty Var: {obj.three_way_match.quantity_variance_pct:.1f}%, Price Var: {obj.three_way_match.price_variance_pct:.1f}%"
        return ""


class MatchToleranceSerializer(serializers.ModelSerializer):
    """Serializer for match tolerances."""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)
    catalog_item_name = serializers.CharField(source='catalog_item.name', read_only=True, allow_null=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    
    class Meta:
        model = MatchTolerance
        fields = [
            'id', 'scope', 'scope_display',
            'supplier', 'supplier_name', 'catalog_item', 'catalog_item_name',
            'quantity_tolerance_pct', 'price_tolerance_pct',
            'auto_approve_threshold', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VendorBillSummarySerializer(serializers.Serializer):
    """Summary serializer for dashboard."""
    
    total_bills = serializers.IntegerField()
    draft_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    matched_count = serializers.IntegerField()
    approved_count = serializers.IntegerField()
    posted_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_match_count = serializers.IntegerField()
    exceptions_count = serializers.IntegerField()
    blocked_count = serializers.IntegerField()

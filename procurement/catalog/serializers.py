# catalog/serializers.py
from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import (
    UnitOfMeasure, CatalogCategory, CatalogItem, SupplierPriceTier,
    FrameworkAgreement, FrameworkItem, CallOffOrder, CallOffLine
)


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ['id', 'code', 'name', 'description', 'uom_type', 
                 'base_uom', 'conversion_factor', 'is_active']
        read_only_fields = ['id']


class CatalogCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    unspsc_full_code = serializers.SerializerMethodField()
    
    class Meta:
        model = CatalogCategory
        fields = ['id', 'code', 'name', 'description', 'parent', 'parent_name',
                 'level', 'full_path', 'unspsc_segment', 'unspsc_family',
                 'unspsc_class', 'unspsc_commodity', 'unspsc_full_code', 'is_active']
        read_only_fields = ['id', 'level', 'full_path']
    
    def get_unspsc_full_code(self, obj):
        return obj.get_full_code()


class SupplierPriceTierSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierPriceTier
        fields = ['id', 'catalog_item', 'supplier', 'supplier_name',
                 'min_quantity', 'unit_price', 'currency', 'currency_code',
                 'discount_percent', 'valid_from', 'valid_to', 'lead_time_days',
                 'supplier_item_code', 'supplier_quote_reference', 'is_active', 'is_valid']
        read_only_fields = ['id']
    
    def get_is_valid(self, obj):
        return obj.is_valid_today()


class CatalogItemListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    uom_code = serializers.CharField(source='unit_of_measure.code', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    supplier_name = serializers.CharField(source='preferred_supplier.name', read_only=True)
    
    class Meta:
        model = CatalogItem
        fields = ['id', 'sku', 'item_code', 'name', 'short_description',
                 'category', 'category_name', 'item_type', 'unit_of_measure', 'uom_code',
                 'list_price', 'currency', 'currency_code', 'preferred_supplier', 'supplier_name',
                 'is_active', 'is_purchasable']
        read_only_fields = ['id']


class CatalogItemDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    uom_code = serializers.CharField(source='unit_of_measure.code', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    supplier_name = serializers.CharField(source='preferred_supplier.name', read_only=True)
    price_tiers = SupplierPriceTierSerializer(source='supplier_price_tiers', many=True, read_only=True)
    
    class Meta:
        model = CatalogItem
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class CatalogItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        exclude = ['created_by', 'created_at', 'updated_at']
    
    def validate_order_multiple(self, value):
        if value <= 0:
            raise serializers.ValidationError("Order multiple must be positive")
        return value
    
    def validate(self, data):
        # Validate minimum order quantity vs order multiple
        moq = data.get('minimum_order_quantity', Decimal('1.000'))
        multiple = data.get('order_multiple', Decimal('1.000'))
        
        if moq % multiple != 0:
            raise serializers.ValidationError({
                'minimum_order_quantity': 'Minimum order quantity must be a multiple of order_multiple'
            })
        
        return data


class FrameworkItemSerializer(serializers.ModelSerializer):
    catalog_item_name = serializers.CharField(source='catalog_item.name', read_only=True)
    catalog_item_sku = serializers.CharField(source='catalog_item.sku', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    remaining_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = FrameworkItem
        fields = ['id', 'framework', 'catalog_item', 'catalog_item_name', 'catalog_item_sku',
                 'line_number', 'unit_price', 'currency', 'currency_code',
                 'minimum_order_quantity', 'maximum_order_quantity', 'total_quantity_limit',
                 'quantity_ordered', 'quantity_received', 'total_value_ordered',
                 'remaining_quantity', 'lead_time_days', 'delivery_location',
                 'is_active', 'notes']
        read_only_fields = ['id', 'quantity_ordered', 'quantity_received', 'total_value_ordered']
    
    def get_remaining_quantity(self, obj):
        remaining = obj.get_remaining_quantity()
        return str(remaining) if remaining is not None else None


class FrameworkAgreementListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    utilization_percent = serializers.SerializerMethodField()
    is_active_status = serializers.SerializerMethodField()
    
    class Meta:
        model = FrameworkAgreement
        fields = ['id', 'agreement_number', 'title', 'agreement_type', 'supplier', 'supplier_name',
                 'start_date', 'end_date', 'status', 'currency', 'currency_code',
                 'total_contract_value', 'total_committed', 'total_spent',
                 'utilization_percent', 'is_active_status']
        read_only_fields = ['id', 'agreement_number', 'total_committed', 'total_spent']
    
    def get_utilization_percent(self, obj):
        return round(obj.get_utilization_percent(), 2)
    
    def get_is_active_status(self, obj):
        return obj.is_active()


class FrameworkAgreementDetailSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    framework_items = FrameworkItemSerializer(many=True, read_only=True)
    utilization_percent = serializers.SerializerMethodField()
    remaining_value = serializers.SerializerMethodField()
    is_active_status = serializers.SerializerMethodField()
    is_expiring_soon = serializers.SerializerMethodField()
    
    class Meta:
        model = FrameworkAgreement
        fields = '__all__'
        read_only_fields = ['id', 'agreement_number', 'total_committed', 'total_spent',
                           'approved_date', 'created_by', 'created_at', 'updated_at']
    
    def get_utilization_percent(self, obj):
        return round(obj.get_utilization_percent(), 2)
    
    def get_remaining_value(self, obj):
        remaining = obj.get_remaining_value()
        return str(remaining) if remaining is not None else None
    
    def get_is_active_status(self, obj):
        return obj.is_active()
    
    def get_is_expiring_soon(self, obj):
        return obj.is_expiring_soon(30)


class FrameworkAgreementCreateUpdateSerializer(serializers.ModelSerializer):
    framework_items = FrameworkItemSerializer(many=True, required=False)
    
    class Meta:
        model = FrameworkAgreement
        exclude = ['agreement_number', 'total_committed', 'total_spent',
                  'approved_by', 'approved_date', 'created_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Validate date range
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        # Validate limit warning percent
        warning_pct = data.get('limit_warning_percent', 80)
        if not 0 <= warning_pct <= 100:
            raise serializers.ValidationError({
                'limit_warning_percent': 'Must be between 0 and 100'
            })
        
        return data
    
    def create(self, validated_data):
        framework_items_data = validated_data.pop('framework_items', [])
        framework = FrameworkAgreement.objects.create(**validated_data)
        
        # Create framework items
        for item_data in framework_items_data:
            FrameworkItem.objects.create(framework=framework, **item_data)
        
        return framework
    
    def update(self, instance, validated_data):
        framework_items_data = validated_data.pop('framework_items', None)
        
        # Update framework
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update framework items if provided
        if framework_items_data is not None:
            # Clear existing items
            instance.framework_items.all().delete()
            
            # Create new items
            for item_data in framework_items_data:
                FrameworkItem.objects.create(framework=instance, **item_data)
        
        return instance


class CallOffLineSerializer(serializers.ModelSerializer):
    catalog_item_name = serializers.CharField(source='catalog_item.name', read_only=True)
    catalog_item_sku = serializers.CharField(source='catalog_item.sku', read_only=True)
    line_total_calculated = serializers.SerializerMethodField()
    
    class Meta:
        model = CallOffLine
        fields = ['id', 'calloff', 'framework_item', 'line_number',
                 'catalog_item', 'catalog_item_name', 'catalog_item_sku', 'description',
                 'quantity', 'unit_price', 'line_total', 'line_total_calculated',
                 'requested_delivery_date', 'actual_delivery_date',
                 'quantity_received', 'is_received', 'notes']
        read_only_fields = ['id', 'line_total']
    
    def get_line_total_calculated(self, obj):
        return str(obj.get_line_total())


class CallOffOrderListSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(source='framework.title', read_only=True)
    framework_number = serializers.CharField(source='framework.agreement_number', read_only=True)
    supplier_name = serializers.CharField(source='framework.supplier.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    
    class Meta:
        model = CallOffOrder
        fields = ['id', 'calloff_number', 'framework', 'framework_name', 'framework_number',
                 'supplier_name', 'order_date', 'requested_delivery_date',
                 'status', 'currency', 'currency_code', 'total_amount',
                 'requested_by', 'requested_by_name', 'approved_by']
        read_only_fields = ['id', 'calloff_number']


class CallOffOrderDetailSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(source='framework.title', read_only=True)
    framework_number = serializers.CharField(source='framework.agreement_number', read_only=True)
    supplier_name = serializers.CharField(source='framework.supplier.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    lines = CallOffLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = CallOffOrder
        fields = '__all__'
        read_only_fields = ['id', 'calloff_number', 'subtotal', 'tax_amount', 'total_amount',
                           'approved_date', 'cancelled_date', 'created_by', 'created_at', 'updated_at']


class CallOffOrderCreateUpdateSerializer(serializers.ModelSerializer):
    lines = CallOffLineSerializer(many=True, required=False)
    
    class Meta:
        model = CallOffOrder
        exclude = ['calloff_number', 'subtotal', 'tax_amount', 'total_amount',
                  'approved_by', 'approved_date', 'cancelled_date',
                  'created_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        framework = data.get('framework')
        
        # Check if framework is active
        if framework and not framework.is_active():
            raise serializers.ValidationError({
                'framework': 'Framework agreement is not active'
            })
        
        # Validate delivery date
        requested_date = data.get('requested_delivery_date')
        if requested_date and requested_date < timezone.now().date():
            raise serializers.ValidationError({
                'requested_delivery_date': 'Delivery date cannot be in the past'
            })
        
        return data
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        calloff = CallOffOrder.objects.create(**validated_data)
        
        # Create call-off lines
        for line_data in lines_data:
            CallOffLine.objects.create(calloff=calloff, **line_data)
        
        # Calculate totals
        calloff.calculate_totals()
        
        return calloff
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        # Update call-off
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update lines if provided
        if lines_data is not None:
            # Clear existing lines
            instance.lines.all().delete()
            
            # Create new lines
            for line_data in lines_data:
                CallOffLine.objects.create(calloff=instance, **line_data)
            
            # Recalculate totals
            instance.calculate_totals()
        
        return instance

"""
Serializers for Purchase Requisition API.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CostCenter, Project, PRHeader, PRLine


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class CostCenterSerializer(serializers.ModelSerializer):
    manager_details = UserSerializer(source='manager', read_only=True)
    committed = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()
    
    class Meta:
        model = CostCenter
        fields = [
            'id', 'code', 'name', 'description', 'parent',
            'manager', 'manager_details', 'is_active',
            'annual_budget', 'committed', 'available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'committed', 'available']
    
    def get_committed(self, obj):
        return float(obj.get_total_committed())
    
    def get_available(self, obj):
        return float(obj.get_available_budget())


class ProjectSerializer(serializers.ModelSerializer):
    project_manager_details = UserSerializer(source='project_manager', read_only=True)
    committed = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'code', 'name', 'description',
            'project_manager', 'project_manager_details',
            'budget', 'start_date', 'end_date', 'status',
            'committed', 'available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'committed', 'available']
    
    def get_committed(self, obj):
        return float(obj.get_total_committed())
    
    def get_available(self, obj):
        return float(obj.get_available_budget())


class PRLineSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()
    line_total_with_tax = serializers.SerializerMethodField()
    catalog_item_details = serializers.SerializerMethodField()
    supplier_details = serializers.SerializerMethodField()
    quantity_remaining = serializers.SerializerMethodField()
    is_fully_converted = serializers.SerializerMethodField()
    source_pos = serializers.SerializerMethodField()
    
    class Meta:
        model = PRLine
        fields = [
            'id', 'line_number', 'item_description', 'specifications',
            'catalog_item', 'catalog_item_details',
            'item_type',  # NEW: Categorization status
            'suggested_catalog_items',
            'quantity', 'unit_of_measure',
            'estimated_unit_price', 'line_total',
            'tax_code', 'tax_rate', 'tax_amount', 'line_total_with_tax',
            'need_by_date',
            'suggested_supplier', 'supplier_details',
            'gl_account', 'notes',
            'conversion_status', 'quantity_converted', 'quantity_remaining', 'is_fully_converted',
            'source_pos',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 
            'line_number', 'tax_amount', 'line_total',
            'line_total_with_tax', 'suggested_catalog_items',
            'item_type',  # Auto-set based on catalog_item
            'conversion_status', 'quantity_converted', 'quantity_remaining',
            'is_fully_converted', 'source_pos'
        ]
    
    def get_line_total(self, obj):
        return float(obj.get_line_total())
    
    def get_line_total_with_tax(self, obj):
        return float(obj.get_line_total_with_tax())
    
    def get_catalog_item_details(self, obj):
        if obj.catalog_item:
            return {
                'id': obj.catalog_item.id,
                'name': obj.catalog_item.name,
                'sku': obj.catalog_item.sku,
                'item_code': obj.catalog_item.item_code,
            }
        return None
    
    def get_supplier_details(self, obj):
        if obj.suggested_supplier:
            return {
                'id': obj.suggested_supplier.id,
                'name': obj.suggested_supplier.name,
                'code': obj.suggested_supplier.code,
            }
        return None
    
    def get_quantity_remaining(self, obj):
        return float(obj.quantity_remaining)
    
    def get_is_fully_converted(self, obj):
        return obj.is_fully_converted
    
    def get_source_pos(self, obj):
        """Get list of POs created from this PR line."""
        mappings = obj.po_line_mappings.select_related('po_line__po_header').all()
        return [
            {
                'po_number': mapping.po_line.po_header.po_number,
                'po_line_number': mapping.po_line.line_number,
                'quantity_converted': float(mapping.quantity_converted),
                'po_status': mapping.po_line.po_header.status,
            }
            for mapping in mappings
        ]


class PRHeaderListSerializer(serializers.ModelSerializer):
    requestor_details = UserSerializer(source='requestor', read_only=True)
    cost_center_details = serializers.SerializerMethodField()
    project_details = serializers.SerializerMethodField()
    line_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PRHeader
        fields = [
            'id', 'pr_number', 'pr_date', 'required_date',
            'title', 'status', 'priority', 'pr_type',
            'requestor', 'requestor_details',
            'cost_center', 'cost_center_details',
            'project', 'project_details',
            'currency', 'total_amount',
            'budget_check_passed',
            'line_count',
            'created_at', 'updated_at'
        ]
    
    def get_cost_center_details(self, obj):
        if obj.cost_center:
            return {
                'id': obj.cost_center.id,
                'code': obj.cost_center.code,
                'name': obj.cost_center.name,
            }
        return None
    
    def get_project_details(self, obj):
        if obj.project:
            return {
                'id': obj.project.id,
                'code': obj.project.code,
                'name': obj.project.name,
            }
        return None
    
    def get_line_count(self, obj):
        return obj.lines.count()


class PRHeaderDetailSerializer(serializers.ModelSerializer):
    requestor_details = UserSerializer(source='requestor', read_only=True)
    cost_center_details = CostCenterSerializer(source='cost_center', read_only=True)
    project_details = ProjectSerializer(source='project', read_only=True)
    
    lines = PRLineSerializer(many=True, read_only=True)
    
    submitted_by_details = UserSerializer(source='submitted_by', read_only=True)
    approved_by_details = UserSerializer(source='approved_by', read_only=True)
    rejected_by_details = UserSerializer(source='rejected_by', read_only=True)
    converted_by_details = UserSerializer(source='converted_by', read_only=True)
    cancelled_by_details = UserSerializer(source='cancelled_by', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = PRHeader
        fields = [
            'id', 'pr_number', 'pr_date', 'required_date',
            'requestor', 'requestor_details',
            'cost_center', 'cost_center_details',
            'project', 'project_details',
            'title', 'description', 'business_justification',
            'priority', 'pr_type', 'status',
            'currency', 'subtotal', 'tax_amount', 'total_amount',
            'budget_check_passed', 'budget_check_message', 'budget_checked_at',
            'catalog_suggestions_generated', 'can_split_by_vendor',
            'lines',
            'submitted_at', 'submitted_by', 'submitted_by_details',
            'approved_at', 'approved_by', 'approved_by_details',
            'rejected_at', 'rejected_by', 'rejected_by_details',
            'rejection_reason',
            'converted_at', 'converted_by', 'converted_by_details',
            'cancelled_at', 'cancelled_by', 'cancelled_by_details',
            'cancellation_reason',
            'internal_notes',
            'created_at', 'created_by', 'created_by_details',
            'updated_at'
        ]
        read_only_fields = ['id', 
            'pr_number', 'subtotal', 'tax_amount', 'total_amount',
            'budget_check_passed', 'budget_check_message', 'budget_checked_at',
            'catalog_suggestions_generated',
            'submitted_at', 'submitted_by',
            'approved_at', 'approved_by',
            'rejected_at', 'rejected_by',
            'converted_at', 'converted_by',
            'cancelled_at', 'cancelled_by',
        ]


class PRHeaderCreateUpdateSerializer(serializers.ModelSerializer):
    lines = PRLineSerializer(many=True, required=False)
    requestor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = PRHeader
        fields = [
            'id', 'pr_date', 'required_date',
            'requestor', 'cost_center', 'project',
            'title', 'description', 'business_justification',
            'priority', 'pr_type', 'currency', 'can_split_by_vendor',
            'internal_notes', 'lines'
        ]
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        
        # Auto-assign requestor if not provided
        if 'requestor' not in validated_data or validated_data.get('requestor') is None:
            # Try to use the request user from context
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                validated_data['requestor'] = request.user
            else:
                # Fall back to first user (for development/testing)
                validated_data['requestor'] = User.objects.first()
                if not validated_data['requestor']:
                    raise serializers.ValidationError({
                        'requestor': 'No users found in database. Please create a user first.'
                    })
        
        pr_header = PRHeader.objects.create(**validated_data)
        
        for line_data in lines_data:
            PRLine.objects.create(pr_header=pr_header, **line_data)
        
        return pr_header
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        # Update header fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update lines if provided
        if lines_data is not None:
            # Delete existing lines not in the update
            line_ids = [line_data.get('id') for line_data in lines_data if line_data.get('id')]
            instance.lines.exclude(id__in=line_ids).delete()
            
            # Update or create lines
            for line_data in lines_data:
                line_id = line_data.pop('id', None)
                if line_id:
                    # Update existing line
                    PRLine.objects.filter(id=line_id, pr_header=instance).update(**line_data)
                else:
                    # Create new line
                    PRLine.objects.create(pr_header=instance, **line_data)
        
        return instance


class PRSubmitSerializer(serializers.Serializer):
    """Serializer for PR submission."""
    pass


class PRApproveSerializer(serializers.Serializer):
    """Serializer for PR approval."""
    pass


class PRRejectSerializer(serializers.Serializer):
    """Serializer for PR rejection."""
    reason = serializers.CharField(required=True)


class PRCancelSerializer(serializers.Serializer):
    """Serializer for PR cancellation."""
    reason = serializers.CharField(required=True)


class PRConvertSerializer(serializers.Serializer):
    """Serializer for PR to PO conversion."""
    split_by_vendor = serializers.BooleanField(default=True)
    po_type = serializers.ChoiceField(
        choices=['STANDARD', 'SERVICE', 'BLANKET'],
        default='STANDARD'
    )

from rest_framework import serializers
from .models import XX_SegmentType, XX_Segment


class SegmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = XX_SegmentType
        fields = [
            "segment_id", "segment_name", "segment_type",
            "is_required", "has_hierarchy", "length", "display_order",
            "description", "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]


class SegmentSerializer(serializers.ModelSerializer):
    segment_type_name = serializers.CharField(source='segment_type.segment_name', read_only=True)
    name = serializers.ReadOnlyField()
    type = serializers.ReadOnlyField()
    full_path = serializers.ReadOnlyField()
    parent = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = XX_Segment
        fields = [
            "id", "segment_type", "segment_type_name", "code", "parent_code",
            "alias", "name", "type", "node_type", "level", "is_active", "envelope_amount",
            "full_path", "parent", "children", "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at", "name", "type", "full_path"]
    
    def validate(self, data):
        """
        Validate that the code length matches the segment_type's required length
        """
        code = data.get('code')
        segment_type = data.get('segment_type')
        
        # If updating, get segment_type from instance if not in data
        if not segment_type and self.instance:
            segment_type = self.instance.segment_type
        
        # Validate code length against segment_type length
        if code and segment_type:
            required_length = segment_type.length
            code_length = len(code)
            
            if code_length != required_length:
                raise serializers.ValidationError({
                    'code': f"Code must be exactly {required_length} characters long. "
                            f"Current length: {code_length}. "
                            f"Segment type '{segment_type.segment_name}' requires codes of length {required_length}."
                })
        
        return data
    
    def get_parent(self, obj):
        if obj.parent:
            return {
                "id": obj.parent.id,
                "code": obj.parent.code,
                "alias": obj.parent.alias
            }
        return None
    
    def get_children(self, obj):
        children = XX_Segment.objects.filter(
            segment_type=obj.segment_type,
            parent_code=obj.code
        )
        return [{"id": c.id, "code": c.code, "alias": c.alias} for c in children]


class AccountSerializer(serializers.ModelSerializer):
    """
    DEPRECATED: Use SegmentSerializer instead
    This serializer is kept for backward compatibility with Account model references
    """
    level = serializers.ReadOnlyField(source='hierarchy_level')
    hierarchy_level = serializers.ReadOnlyField()
    full_path = serializers.ReadOnlyField()
    parent_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    name = serializers.CharField(source='alias', required=False)
    
    class Meta:
        model = XX_Segment
        fields = [
            "id", "code", "name", "alias", "node_type", "is_active", "parent_code",
            "level", "hierarchy_level", "full_path", "envelope_amount"
        ]
        read_only_fields = ["level", "hierarchy_level", "full_path"]
    
    def validate(self, data):
        """
        Validate that the code length matches the segment_type's required length
        """
        code = data.get('code')
        
        # Get segment_type from instance or default to Account
        segment_type = None
        if self.instance:
            segment_type = self.instance.segment_type
        else:
            # For create operations, get Account segment type
            from .utils import SegmentHelper
            try:
                segment_type = SegmentHelper.get_segment_type('Account')
            except ValueError:
                pass
        
        # Validate code length against segment_type length
        if code and segment_type:
            required_length = segment_type.length
            code_length = len(code)
            
            if code_length != required_length:
                raise serializers.ValidationError({
                    'code': f"Code must be exactly {required_length} characters long. "
                            f"Current length: {code_length}. "
                            f"Account segment type requires codes of length {required_length}."
                })
        
        return data
    
    def create(self, validated_data):
        # Set alias from name if provided
        if 'alias' not in validated_data and 'name' in validated_data:
            validated_data['alias'] = validated_data.pop('name')
        
        # Ensure segment_type is set to 'Account'
        from .utils import SegmentHelper
        if 'segment_type' not in validated_data:
            try:
                account_type = SegmentHelper.get_segment_type('Account')
                validated_data['segment_type'] = account_type
            except ValueError:
                raise serializers.ValidationError(
                    "Account segment type must be configured first"
                )
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Set alias from name if provided
        if 'alias' not in validated_data and 'name' in validated_data:
            validated_data['alias'] = validated_data.pop('name')
        return super().update(instance, validated_data)


"""
Segment utility functions for dynamic segment management
"""
from django.db.models import QuerySet
from .models import XX_Segment, XX_SegmentType


class SegmentHelper:
    """
    Helper class for working with dynamic segments
    Replaces hardcoded Account model with flexible segment queries
    """
    
    @staticmethod
    def get_segment_type(segment_name: str) -> XX_SegmentType:
        """Get segment type by name (e.g., 'Account', 'Department', 'Project')"""
        try:
            return XX_SegmentType.objects.get(segment_name=segment_name)
        except XX_SegmentType.DoesNotExist:
            raise ValueError(f"Segment type '{segment_name}' does not exist")
    
    @staticmethod
    def get_segments_by_type(segment_name: str) -> QuerySet:
        """Get all segments of a specific type"""
        segment_type = SegmentHelper.get_segment_type(segment_name)
        return XX_Segment.objects.filter(segment_type=segment_type)
    
    @staticmethod
    def get_account_segments() -> QuerySet:
        """
        Get all account segments (backward compatibility helper)
        Returns segments where segment_type.segment_name = 'Account'
        """
        return SegmentHelper.get_segments_by_type('Account')
    
    @staticmethod
    def get_segment_by_code(segment_name: str, code: str) -> XX_Segment:
        """Get a specific segment by type and code"""
        segment_type = SegmentHelper.get_segment_type(segment_name)
        return XX_Segment.objects.get(segment_type=segment_type, code=code)
    
    @staticmethod
    def get_account_by_code(code: str) -> XX_Segment:
        """Get account segment by code (backward compatibility)"""
        return SegmentHelper.get_segment_by_code('Account', code)
    
    @staticmethod
    def create_segment(segment_name: str, code: str, alias: str, **kwargs) -> XX_Segment:
        """
        Create a new segment dynamically
        
        Args:
            segment_name: Name of segment type (e.g., 'Account', 'Department')
            code: Unique code for the segment
            alias: Display name/description
            **kwargs: Additional fields (parent_code, node_type, level, etc.)
        """
        segment_type = SegmentHelper.get_segment_type(segment_name)
        return XX_Segment.objects.create(
            segment_type=segment_type,
            code=code,
            alias=alias,
            **kwargs
        )
    
    @staticmethod
    def get_or_create_segment(segment_name: str, code: str, defaults: dict = None) -> tuple:
        """
        Get or create a segment dynamically
        
        Returns:
            tuple: (segment_instance, created)
        """
        segment_type = SegmentHelper.get_segment_type(segment_name)
        defaults = defaults or {}
        return XX_Segment.objects.get_or_create(
            segment_type=segment_type,
            code=code,
            defaults=defaults
        )
    
    @staticmethod
    def get_hierarchy_tree(segment_name: str) -> list:
        """
        Get hierarchical tree structure for a segment type
        Returns list of parent segments with their children
        """
        segments = SegmentHelper.get_segments_by_type(segment_name)
        parents = segments.filter(node_type='parent')
        
        tree = []
        for parent in parents:
            tree.append({
                'code': parent.code,
                'alias': parent.alias,
                'node_type': parent.node_type,
                'children': parent.get_children()
            })
        return tree
    
    @staticmethod
    def ensure_segment_type_exists(
        segment_name: str,
        segment_type: str,
        defaults: dict = None
    ) -> XX_SegmentType:
        """
        Ensure a segment type exists, create if not
        Useful for migrations and initial setup
        """
        defaults = defaults or {}
        segment_type_obj, created = XX_SegmentType.objects.get_or_create(
            segment_name=segment_name,
            defaults={
                'segment_type': segment_type,
                'is_required': defaults.get('is_required', False),
                'has_hierarchy': defaults.get('has_hierarchy', False),
                'length': defaults.get('length', 50),
                'display_order': defaults.get('display_order', 99),
                'description': defaults.get('description', ''),
                **{k: v for k, v in defaults.items() if k not in [
                    'is_required', 'has_hierarchy', 'length', 'display_order', 'description'
                ]}
            }
        )
        return segment_type_obj


# Backward compatibility aliases
def get_accounts():
    """Legacy function - returns account segments"""
    return SegmentHelper.get_account_segments()


def get_account_by_code(code: str):
    """Legacy function - returns account by code"""
    return SegmentHelper.get_account_by_code(code)

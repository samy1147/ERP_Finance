from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError
from .models import XX_SegmentType, XX_Segment
from .serializers import SegmentTypeSerializer, SegmentSerializer
from .utils import SegmentHelper


class SegmentTypeViewSet(viewsets.ModelViewSet):
    queryset = XX_SegmentType.objects.all()
    serializer_class = SegmentTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_required", "has_hierarchy", "is_active", "segment_type"]
    search_fields = ["segment_name", "segment_type", "description"]
    ordering_fields = ["segment_id", "display_order", "segment_name"]
    ordering = ["display_order", "segment_id"]
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to handle deletion validation errors gracefully.
        """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response(
                {"error": str(e.message) if hasattr(e, 'message') else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=["get"])
    def values(self, request, pk=None):
        """Get all segment values for this segment type"""
        segment_type = self.get_object()
        segments = XX_Segment.objects.filter(segment_type=segment_type)
        serializer = SegmentSerializer(segments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def names(self, request):
        """
        Returns a list of segment type names only.
        """
        names = self.get_queryset().values_list('segment_name', flat=True)
        return Response(list(names))

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """
        Deactivate a segment type instead of deleting it.
        Safer alternative when segment type is used in transactions.
        """
        segment_type = self.get_object()
        segment_type.is_active = False
        segment_type.save()
        serializer = self.get_serializer(segment_type)
        return Response({
            "message": f"Segment type '{segment_type.segment_name}' has been deactivated.",
            "data": serializer.data
        })
    
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Reactivate a segment type"""
        segment_type = self.get_object()
        segment_type.is_active = True
        segment_type.save()
        serializer = self.get_serializer(segment_type)
        return Response({
            "message": f"Segment type '{segment_type.segment_name}' has been activated.",
            "data": serializer.data
        })


class SegmentViewSet(viewsets.ModelViewSet):
    queryset = XX_Segment.objects.all()
    serializer_class = SegmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["segment_type", "is_active", "level", "parent_code", "code"]
    search_fields = ["code", "alias"]
    ordering_fields = ["code", "level", "created_at"]
    ordering = ["segment_type", "level", "code"]
    # Use 'id' for detail lookups (default pk behavior)
    lookup_field = 'pk'
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to handle deletion validation errors gracefully.
        """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response(
                {"error": str(e.message) if hasattr(e, 'message') else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """
        Deactivate a segment instead of deleting it.
        Safer alternative when segment is used in transactions.
        """
        segment = self.get_object()
        segment.is_active = False
        segment.save()
        serializer = self.get_serializer(segment)
        return Response({
            "message": f"Segment '{segment.code} - {segment.alias}' has been deactivated.",
            "data": serializer.data
        })
    
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Reactivate a segment"""
        segment = self.get_object()
        segment.is_active = True
        segment.save()
        serializer = self.get_serializer(segment)
        return Response({
            "message": f"Segment '{segment.code} - {segment.alias}' has been activated.",
            "data": serializer.data
        })
    
    @action(detail=True, methods=["get"])
    def check_usage(self, request, pk=None):
        """
        Check if a segment is used in any transactions.
        Returns usage details without attempting deletion.
        """
        segment = self.get_object()
        is_used, usage_details = segment.is_used_in_transactions()
        
        return Response({
            "segment_id": segment.id,
            "segment_code": segment.code,
            "segment_alias": segment.alias,
            "is_used": is_used,
            "can_delete": not is_used,
            "usage_details": usage_details,
            "suggestion": "Mark as inactive instead of deleting" if is_used else "Safe to delete"
        })
    
    @action(detail=True, methods=["get"])
    def children(self, request, pk=None):
        """Get all children of this segment"""
        segment = self.get_object()
        children = XX_Segment.objects.filter(
            segment_type=segment.segment_type,
            parent_code=segment.code
        )
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["get"])
    def descendants(self, request, pk=None):
        """Get all descendants (recursive children) of this segment"""
        segment = self.get_object()
        descendant_codes = segment.get_all_children()
        descendants = XX_Segment.objects.filter(
            segment_type=segment.segment_type,
            code__in=descendant_codes
        )
        serializer = self.get_serializer(descendants, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def child_segments(self, request):
        """
        Get only child (leaf) segments for a segment type.
        Use this endpoint for journal line segment selection.
        Query params:
        - segment_type: Required - segment type ID
        - is_active: Optional - filter by active status (default: true)
        """
        segment_type_id = request.query_params.get('segment_type')
        if not segment_type_id:
            return Response(
                {"error": "segment_type parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_active = request.query_params.get('is_active', 'true').lower() == 'true'
        
        # Get only child segments (node_type='child')
        queryset = XX_Segment.objects.filter(
            segment_type_id=segment_type_id,
            node_type='child'
        )
        
        if is_active:
            queryset = queryset.filter(is_active=True)
        
        queryset = queryset.order_by('code')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def hierarchy(self, request):
        """Get hierarchical tree structure for a segment type"""
        segment_type_id = request.query_params.get('segment_type')
        if not segment_type_id:
            return Response(
                {"error": "segment_type parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get root segments (no parent)
        roots = XX_Segment.objects.filter(
            segment_type_id=segment_type_id,
            parent_code__isnull=True
        )
        
        def build_tree(segment):
            children = XX_Segment.objects.filter(
                segment_type=segment.segment_type,
                parent_code=segment.code
            )
            return {
                "id": segment.id,
                "code": segment.code,
                "alias": segment.alias,
                "level": segment.level,
                "is_active": segment.is_active,
                "children": [build_tree(child) for child in children]
            }
        
        tree = [build_tree(root) for root in roots]
        return Response(tree)


class AccountViewSet(viewsets.ModelViewSet):
    """
    DEPRECATED: Use SegmentViewSet with segment_type='Account' instead
    This viewset is kept for backward compatibility only
    """
    serializer_class = SegmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "level", "parent_code", "code"]
    search_fields = ["code", "alias"]
    ordering_fields = ["code", "level"]
    ordering = ["code"]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """Return segments where segment_type.segment_name = 'Account'"""
        try:
            return SegmentHelper.get_account_segments()
        except ValueError:
            # If 'Account' segment type doesn't exist, return empty queryset
            return XX_Segment.objects.none()
    
    @action(detail=False, methods=["get"])
    def hierarchy(self, request):
        """Get hierarchical chart of accounts"""
        try:
            account_type = SegmentHelper.get_segment_type('Account')
            roots = XX_Segment.objects.filter(
                segment_type=account_type,
                parent_code__isnull=True
            )
            
            def build_tree(segment):
                children = XX_Segment.objects.filter(
                    segment_type=segment.segment_type,
                    parent_code=segment.code
                )
                return {
                    "id": segment.id,
                    "code": segment.code,
                    "alias": segment.alias,
                    "node_type": segment.node_type,
                    "level": segment.level,
                    "is_active": segment.is_active,
                    "children": [build_tree(child) for child in children]
                }
            
            tree = [build_tree(root) for root in roots]
            return Response(tree)
        except ValueError:
            return Response(
                {"error": "Account segment type not configured"},
                status=status.HTTP_404_NOT_FOUND
            )


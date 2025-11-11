"""
API for Inventory Management.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F, Q

from .models import (
    InventoryBalance, StockMovement, StockAdjustment, StockAdjustmentLine,
    StockTransfer, StockTransferLine
)
from .serializers import (
    InventoryBalanceSerializer, StockMovementSerializer,
    StockAdjustmentSerializer, StockAdjustmentLineSerializer,
    StockTransferSerializer, StockTransferLineSerializer
)


class InventoryBalanceViewSet(viewsets.ModelViewSet):
    """API for Inventory Balance management"""
    queryset = InventoryBalance.objects.select_related(
        'catalog_item', 'warehouse', 'storage_location'
    )
    serializer_class = InventoryBalanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['catalog_item', 'warehouse', 'storage_location', 'lot_number', 'is_active']
    search_fields = ['catalog_item__sku', 'catalog_item__name', 'lot_number']
    ordering_fields = ['warehouse', 'catalog_item', 'quantity_on_hand', 'last_movement_date']
    ordering = ['warehouse', 'catalog_item']
    
    @action(detail=False, methods=['get'])
    def summary_by_warehouse(self, request):
        """Get inventory summary grouped by warehouse"""
        warehouse_id = request.query_params.get('warehouse_id')
        
        queryset = self.get_queryset()
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        summary = queryset.values(
            'warehouse__code', 'warehouse__name'
        ).annotate(
            total_items=Sum('quantity_on_hand'),
            total_value=Sum(F('quantity_on_hand') * F('unit_cost'))
        ).order_by('warehouse__code')
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get items with low or zero stock"""
        threshold = float(request.query_params.get('threshold', 0))
        
        low_stock_items = self.get_queryset().filter(
            quantity_on_hand__lte=threshold,
            is_active=True
        ).order_by('quantity_on_hand')
        
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_item(self, request):
        """Get all inventory balances for a specific item across warehouses"""
        item_id = request.query_params.get('item_id')
        
        if not item_id:
            return Response(
                {"error": "item_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        balances = self.get_queryset().filter(catalog_item_id=item_id)
        serializer = self.get_serializer(balances, many=True)
        return Response(serializer.data)


class StockMovementViewSet(viewsets.ModelViewSet):
    """API for Stock Movement tracking"""
    queryset = StockMovement.objects.select_related(
        'catalog_item', 'from_warehouse', 'to_warehouse', 'created_by'
    )
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'movement_type', 'catalog_item', 'from_warehouse', 'to_warehouse',
        'lot_number', 'reference_type', 'reference_id'
    ]
    search_fields = ['movement_number', 'catalog_item__sku', 'reference_number']
    ordering_fields = ['movement_date', 'movement_number']
    ordering = ['-movement_date', '-movement_number']
    
    @action(detail=False, methods=['get'])
    def by_item(self, request):
        """Get all movements for a specific item"""
        item_id = request.query_params.get('item_id')
        
        if not item_id:
            return Response(
                {"error": "item_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movements = self.get_queryset().filter(catalog_item_id=item_id)
        serializer = self.get_serializer(movements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_reference(self, request):
        """Get movements by reference document"""
        reference_type = request.query_params.get('reference_type')
        reference_id = request.query_params.get('reference_id')
        
        if not reference_type or not reference_id:
            return Response(
                {"error": "reference_type and reference_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movements = self.get_queryset().filter(
            reference_type=reference_type,
            reference_id=reference_id
        )
        serializer = self.get_serializer(movements, many=True)
        return Response(serializer.data)


class StockAdjustmentViewSet(viewsets.ModelViewSet):
    """API for Stock Adjustments"""
    queryset = StockAdjustment.objects.select_related(
        'warehouse', 'submitted_by', 'approved_by', 'posted_by'
    ).prefetch_related('lines')
    serializer_class = StockAdjustmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'adjustment_type', 'warehouse', 'adjustment_date']
    search_fields = ['adjustment_number', 'description']
    ordering_fields = ['adjustment_date', 'adjustment_number']
    ordering = ['-adjustment_date', '-adjustment_number']
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit adjustment for approval"""
        adjustment = self.get_object()
        
        if adjustment.status != 'DRAFT':
            return Response(
                {"error": "Only draft adjustments can be submitted"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        adjustment.status = 'PENDING_APPROVAL'
        adjustment.submitted_by = request.user
        adjustment.submitted_date = timezone.now()
        adjustment.save()
        
        serializer = self.get_serializer(adjustment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve adjustment"""
        adjustment = self.get_object()
        
        if adjustment.status != 'PENDING_APPROVAL':
            return Response(
                {"error": "Only pending adjustments can be approved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        adjustment.status = 'APPROVED'
        adjustment.approved_by = request.user
        adjustment.approved_date = timezone.now()
        adjustment.save()
        
        serializer = self.get_serializer(adjustment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def post_adjustment(self, request, pk=None):
        """Post adjustment to inventory"""
        adjustment = self.get_object()
        
        try:
            adjustment.post(request.user)
            serializer = self.get_serializer(adjustment)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class StockTransferViewSet(viewsets.ModelViewSet):
    """API for Stock Transfers"""
    queryset = StockTransfer.objects.select_related(
        'from_warehouse', 'to_warehouse', 'created_by', 'received_by'
    ).prefetch_related('lines')
    serializer_class = StockTransferSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'from_warehouse', 'to_warehouse', 'transfer_date']
    search_fields = ['transfer_number', 'notes']
    ordering_fields = ['transfer_date', 'transfer_number']
    ordering = ['-transfer_date', '-transfer_number']
    
    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """Ship the transfer (create outbound movements)"""
        transfer = self.get_object()
        
        try:
            transfer.ship(request.user)
            serializer = self.get_serializer(transfer)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """Receive the transfer (create inbound movements)"""
        transfer = self.get_object()
        
        try:
            transfer.receive(request.user)
            serializer = self.get_serializer(transfer)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# Import timezone at top
from django.utils import timezone

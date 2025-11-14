"""
API views for Purchase Orders.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.contrib.auth.models import User

from .models import POHeader, POLine
from .serializers import (
    POHeaderListSerializer, POHeaderDetailSerializer,
    POLineSerializer, POCreateSerializer, POSubmitSerializer,
    POApproveSerializer, POConfirmSerializer, POCancelSerializer
)


class POHeaderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Purchase Order Headers.
    
    Endpoints:
    - GET /api/procurement/purchase-orders/ - List all POs
    - POST /api/procurement/purchase-orders/ - Create new PO
    - GET /api/procurement/purchase-orders/{id}/ - Get PO details
    - PUT/PATCH /api/procurement/purchase-orders/{id}/ - Update PO
    - DELETE /api/procurement/purchase-orders/{id}/ - Delete PO
    
    Actions:
    - POST /api/procurement/purchase-orders/{id}/submit/ - Submit for approval
    - POST /api/procurement/purchase-orders/{id}/approve/ - Approve PO
    - POST /api/procurement/purchase-orders/{id}/confirm/ - Confirm and send to vendor
    - POST /api/procurement/purchase-orders/{id}/cancel/ - Cancel PO
    - GET /api/procurement/purchase-orders/my_pos/ - Get user's POs
    - GET /api/procurement/purchase-orders/pending_approval/ - Get POs pending approval
    """
    
    queryset = POHeader.objects.all()
    permission_classes = [AllowAny]  # TODO: Change to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'vendor_name', 'created_by']
    search_fields = ['po_number', 'title', 'description', 'vendor__name']
    ordering_fields = ['po_date', 'total_amount', 'delivery_date', 'created_at']
    ordering = ['-po_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return POHeaderListSerializer
        return POHeaderDetailSerializer
    
    def perform_create(self, serializer):
        # Use authenticated user or default to first user (dev mode)
        user = self.request.user if self.request.user.is_authenticated else User.objects.first()
        serializer.save(created_by=user)
    
    def perform_update(self, serializer):
        """
        When updating a PO, if it's already approved/submitted,
        reset to SUBMITTED to require re-approval.
        """
        po = self.get_object()
        user = self.request.user if self.request.user.is_authenticated else User.objects.first()
        
        # Track if PO was approved before update
        was_approved = po.status == 'APPROVED'
        
        # Save the changes first
        serializer.save()
        
        # If PO was approved, reset it to SUBMITTED after saving
        if was_approved:
            po.reset_approval(user)
            # Refresh the instance to reflect the status change
            po.refresh_from_db()
    
    @action(detail=False, methods=['get'])
    def my_pos(self, request):
        """Get POs created by current user."""
        # For development: get user ID from query param or use default
        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = request.query_params.get('created_by', 2)
        
        pos = self.queryset.filter(created_by_id=user_id)
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            pos = pos.filter(status=status_filter)
        
        serializer = self.get_serializer(pos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """Get POs pending approval."""
        pos = self.queryset.filter(status='SUBMITTED')
        serializer = self.get_serializer(pos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def receivable(self, request):
        """
        Get POs that are ready to receive goods.
        Returns POs with status CONFIRMED or PARTIALLY_RECEIVED that have outstanding items.
        This is used in the receiving page to show only POs that need receiving.
        """
        # Get POs that can receive goods
        pos = self.queryset.filter(
            status__in=['CONFIRMED', 'PARTIALLY_RECEIVED']
        ).select_related('created_by').prefetch_related('lines')
        
        # Filter to only POs with outstanding items
        receivable_pos = []
        for po in pos:
            if po.has_outstanding_items():
                receivable_pos.append(po)
        
        serializer = self.get_serializer(receivable_pos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def receiving_status(self, request, pk=None):
        """
        Get detailed receiving status for a PO.
        Shows overall status and line-by-line receiving progress.
        """
        po = self.get_object()
        
        lines_status = []
        for line in po.lines.all():
            outstanding = line.quantity - line.quantity_received
            lines_status.append({
                'id': line.id,
                'line_number': line.line_number,
                'item_description': line.item_description,
                'ordered_quantity': str(line.quantity),
                'received_quantity': str(line.quantity_received),
                'outstanding_quantity': str(outstanding),
                'percentage_received': (float(line.quantity_received) / float(line.quantity) * 100) if line.quantity > 0 else 0,
                'is_fully_received': line.is_fully_received
            })
        
        total_ordered = sum(float(line.quantity) for line in po.lines.all())
        total_received = sum(float(line.quantity_received) for line in po.lines.all())
        
        return Response({
            'po_id': po.id,
            'po_number': po.po_number,
            'po_status': po.status,
            'receiving_status': po.get_receiving_status(),
            'can_receive': po.can_receive(),
            'has_outstanding': po.has_outstanding_items(),
            'vendor_name': po.vendor_name,
            'total_ordered': str(total_ordered),
            'total_received': str(total_received),
            'percentage_received': (total_received / total_ordered * 100) if total_ordered > 0 else 0,
            'lines': lines_status
        })
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit PO for approval."""
        po = self.get_object()
        serializer = POSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get user - use default in dev mode
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        try:
            po.submit(user)
            return Response({
                'status': 'success',
                'message': 'PO submitted for approval',
                'po': POHeaderDetailSerializer(po).data
            })
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve PO."""
        po = self.get_object()
        serializer = POApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get user - use default in dev mode
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        try:
            po.approve(user)
            return Response({
                'status': 'success',
                'message': 'PO approved',
                'po': POHeaderDetailSerializer(po).data
            })
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm PO and send to vendor."""
        po = self.get_object()
        serializer = POConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get user - use default in dev mode
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        try:
            po.confirm_and_send(user)
            return Response({
                'status': 'success',
                'message': 'PO confirmed and sent to vendor',
                'po': POHeaderDetailSerializer(po).data
            })
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel PO."""
        po = self.get_object()
        serializer = POCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reason = serializer.validated_data['reason']
        
        # Get user - use default in dev mode
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        try:
            po.cancel(user, reason)
            return Response({
                'status': 'success',
                'message': 'PO cancelled',
                'po': POHeaderDetailSerializer(po).data
            })
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel_delivery(self, request, pk=None):
        """
        Cancel delivery and revert CONFIRMED PO back to APPROVED status.
        Use when delivery needs to be recalled or rescheduled.
        """
        po = self.get_object()
        reason = request.data.get('reason', '')
        
        # Get user - use default in dev mode
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        try:
            po.cancel_delivery(user, reason)
            return Response({
                'status': 'success',
                'message': 'Delivery cancelled. PO reverted to APPROVED status.',
                'po': POHeaderDetailSerializer(po).data
            })
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reset_approval(self, request, pk=None):
        """
        Reset PO approval status when edited.
        - APPROVED → SUBMITTED (needs re-approval)
        - SUBMITTED → stays SUBMITTED
        """
        po = self.get_object()
        
        # Get user - use default in dev mode
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        if po.reset_approval(user):
            message = 'PO approval reset to SUBMITTED. It will need to be approved again.' if po.status == 'SUBMITTED' else 'PO status updated.'
            return Response({
                'status': 'success',
                'message': message,
                'po': POHeaderDetailSerializer(po).data
            })
        else:
            return Response({
                'status': 'error',
                'message': f'Cannot reset approval for PO in {po.status} status'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_exchange_rate(self, request, pk=None):
        """
        Update exchange rate for PO.
        Optionally provide rate_date or use PO date.
        Optionally provide manual exchange_rate or fetch from table.
        """
        po = self.get_object()
        
        # Get rate_date from request or use PO date
        rate_date_str = request.data.get('rate_date')
        if rate_date_str:
            from datetime import datetime
            rate_date = datetime.strptime(rate_date_str, '%Y-%m-%d').date()
        else:
            rate_date = po.po_date
        
        # Check if manual rate provided
        manual_rate = request.data.get('exchange_rate')
        
        try:
            if manual_rate:
                # Use manual rate
                from decimal import Decimal
                po.exchange_rate = Decimal(str(manual_rate))
                po.calculate_totals()
                po.save()
                message = f'Exchange rate manually set to {po.exchange_rate}'
            else:
                # Fetch from exchange rate table
                po.update_exchange_rate(rate_date)
                po.save()
                message = f'Exchange rate updated to {po.exchange_rate} for date {rate_date}'
            
            return Response({
                'status': 'success',
                'message': message,
                'exchange_rate': str(po.exchange_rate),
                'base_currency_total': str(po.base_currency_total),
                'po': POHeaderDetailSerializer(po).data
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class POLineViewSet(viewsets.ModelViewSet):
    """ViewSet for PO Lines."""
    
    queryset = POLine.objects.all()
    serializer_class = POLineSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['po_header', 'catalog_item']
    ordering = ['po_header', 'line_number']

# procurement/receiving/api.py
"""
API for Receiving module - Goods receipts, quality inspections, and returns
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import (
    Warehouse, GoodsReceipt, GRNLine,
    QualityInspection, NonConformance,
    ReturnToVendor, RTVLine
)
from .serializers import (
    WarehouseSerializer, GoodsReceiptListSerializer, GoodsReceiptDetailSerializer,
    GRNLineSerializer, QualityInspectionSerializer,
    NonConformanceSerializer, ReturnToVendorSerializer, RTVLineSerializer
)


class WarehouseViewSet(viewsets.ModelViewSet):
    """API for Warehouse management"""
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code', 'location']


class GoodsReceiptViewSet(viewsets.ModelViewSet):
    """API for Goods Receipt management"""
    queryset = GoodsReceipt.objects.select_related('po_header', 'warehouse').prefetch_related('lines')
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'po_header', 'warehouse', 'receipt_date']
    search_fields = ['receipt_number', 'delivery_note_number', 'tracking_number']
    ordering_fields = ['receipt_date', 'receipt_number', 'created_at']
    ordering = ['-receipt_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return GoodsReceiptListSerializer
        return GoodsReceiptDetailSerializer
    
    def perform_create(self, serializer):
        # Set received_by to current user (or default user ID 2)
        user = self.request.user if self.request.user.is_authenticated else None
        if not user or user.is_anonymous:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=2)  # Default user
        
        serializer.save(received_by=user)
    
    @action(detail=False, methods=['get'])
    def po_outstanding_quantities(self, request):
        """
        Get outstanding quantities for a PO that still need to be received.
        
        Query params:
        - po_id: Purchase Order ID
        
        Returns items with quantities remaining to be received.
        """
        po_id = request.query_params.get('po_id')
        
        if not po_id:
            return Response(
                {"error": "po_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from procurement.purchase_orders.models import POHeader, POLine
            
            po = POHeader.objects.get(id=po_id)
            
            outstanding_items = []
            for po_line in po.lines.all():
                outstanding_qty = po_line.quantity - po_line.quantity_received
                
                if outstanding_qty > 0:
                    outstanding_items.append({
                        'po_line_id': po_line.id,
                        'line_number': po_line.line_number,
                        'item_description': po_line.item_description,
                        'catalog_item_id': po_line.catalog_item.id if po_line.catalog_item else None,
                        'ordered_quantity': str(po_line.quantity),
                        'received_quantity': str(po_line.quantity_received),
                        'outstanding_quantity': str(outstanding_qty),
                        'unit_of_measure': po_line.unit_of_measure.code if po_line.unit_of_measure else None
                    })
            
            return Response({
                "po_id": po.id,
                "po_number": po.po_number,
                "po_status": po.status,
                "vendor_name": po.vendor_name,
                "outstanding_items": outstanding_items,
                "has_outstanding": len(outstanding_items) > 0
            })
        
        except POHeader.DoesNotExist:
            return Response(
                {"error": "Purchase Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        """Post receipt to inventory"""
        receipt = self.get_object()
        
        try:
            receipt.post_to_inventory(posted_by=request.user if request.user.is_authenticated else None)
            return Response({
                "status": "success",
                "message": f"Receipt {receipt.receipt_number} posted to inventory"
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def partial_receive(self, request, pk=None):
        """
        Record partial receipt of goods.
        
        Request body should contain:
        {
            "lines": [
                {
                    "id": 1,  # GRN Line ID
                    "received_quantity": 50  # Quantity actually received
                },
                ...
            ]
        }
        """
        receipt = self.get_object()
        
        if receipt.status == 'COMPLETED':
            return Response(
                {"error": "Cannot update completed receipt"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if receipt.status == 'CANCELLED':
            return Response(
                {"error": "Cannot update cancelled receipt"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lines_data = request.data.get('lines', [])
        
        if not lines_data:
            return Response(
                {"error": "No line data provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            updated_lines = []
            for line_data in lines_data:
                line_id = line_data.get('id')
                received_qty = line_data.get('received_quantity')
                
                if line_id is None or received_qty is None:
                    continue
                
                try:
                    grn_line = receipt.lines.get(id=line_id)
                    grn_line.received_quantity = received_qty
                    grn_line.save()  # This will trigger update_receipt_status()
                    updated_lines.append({
                        'id': grn_line.id,
                        'line_number': grn_line.line_number,
                        'item_description': grn_line.item_description,
                        'ordered_quantity': str(grn_line.ordered_quantity),
                        'received_quantity': str(grn_line.received_quantity),
                        'receipt_status': grn_line.receipt_status
                    })
                except GRNLine.DoesNotExist:
                    continue
            
            # Update GRN status to IN_PROGRESS if it was DRAFT
            if receipt.status == 'DRAFT':
                receipt.status = 'IN_PROGRESS'
                receipt.save()
            
            return Response({
                "status": "success",
                "message": f"Partial receipt recorded for {receipt.receipt_number}",
                "receipt_status": receipt.status,
                "updated_lines": updated_lines
            })
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def create_assets(self, request, pk=None):
        """
        Create assets from a GRN (for capitalizable items)
        Only works for CATEGORIZED_GOODS GRNs
        """
        receipt = self.get_object()
        
        try:
            # Import asset service
            from fixed_assets.services import AssetProcurementService
            
            service = AssetProcurementService()
            result = service.bulk_create_assets_from_grn(
                receipt,
                user=request.user if request.user.is_authenticated else None
            )
            
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def complete_receipt(self, request, pk=None):
        """
        Complete the receipt and post to inventory.
        This can be used after partial receipts to finalize everything.
        """
        receipt = self.get_object()
        
        try:
            # Check if there are still pending lines
            pending_lines = receipt.lines.filter(receipt_status='PENDING')
            partial_lines = receipt.lines.filter(receipt_status='PARTIAL')
            
            if pending_lines.exists() or partial_lines.exists():
                return Response({
                    "warning": "Receipt has pending or partial lines",
                    "pending_count": pending_lines.count(),
                    "partial_count": partial_lines.count(),
                    "message": "You can still post this receipt, but some items are not fully received"
                }, status=status.HTTP_200_OK)
            
            # Post to inventory
            receipt.post_to_inventory(posted_by=request.user if request.user.is_authenticated else None)
            
            return Response({
                "status": "success",
                "message": f"Receipt {receipt.receipt_number} completed and posted to inventory"
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def receiving_status(self, request, pk=None):
        """
        Get detailed receiving status for a GRN.
        Shows which lines are fully received, partially received, or pending.
        """
        receipt = self.get_object()
        
        lines_status = []
        for line in receipt.lines.all():
            lines_status.append({
                'id': line.id,
                'line_number': line.line_number,
                'item_description': line.item_description,
                'ordered_quantity': str(line.ordered_quantity),
                'received_quantity': str(line.received_quantity),
                'receipt_status': line.receipt_status,
                'percentage_received': (float(line.received_quantity) / float(line.ordered_quantity) * 100) if line.ordered_quantity > 0 else 0
            })
        
        total_ordered = sum(float(line.ordered_quantity) for line in receipt.lines.all())
        total_received = sum(float(line.received_quantity) for line in receipt.lines.all())
        
        return Response({
            "receipt_number": receipt.receipt_number,
            "receipt_status": receipt.status,
            "po_number": receipt.po_header.po_number if receipt.po_header else receipt.po_reference,
            "total_ordered": str(total_ordered),
            "total_received": str(total_received),
            "percentage_received": (total_received / total_ordered * 100) if total_ordered > 0 else 0,
            "lines": lines_status
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel receipt"""
        receipt = self.get_object()
        cancellation_reason = request.data.get('cancellation_reason', '')
        
        try:
            receipt.cancel(cancellation_reason=cancellation_reason)
            return Response({
                "status": "success",
                "message": f"Receipt {receipt.receipt_number} cancelled"
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class GRNLineViewSet(viewsets.ModelViewSet):
    """API for GRN Line management"""
    queryset = GRNLine.objects.select_related('goods_receipt', 'catalog_item')
    serializer_class = GRNLineSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['goods_receipt', 'condition']


class QualityInspectionViewSet(viewsets.ModelViewSet):
    """API for Quality Inspection management"""
    queryset = QualityInspection.objects.select_related('goods_receipt', 'inspector')
    serializer_class = QualityInspectionSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'goods_receipt', 'inspection_type', 'disposition']
    search_fields = ['inspection_number']
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start inspection"""
        inspection = self.get_object()
        inspector_id = request.data.get('inspector_id')
        start_date = request.data.get('start_date')
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            inspector = User.objects.get(id=inspector_id)
            
            inspection.inspector = inspector
            inspection.inspection_date = start_date
            inspection.status = 'IN_PROGRESS'
            inspection.save()
            
            return Response({
                "status": "success",
                "message": f"Inspection {inspection.inspection_number} started"
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete inspection"""
        inspection = self.get_object()
        completion_date = request.data.get('completion_date')
        notes = request.data.get('inspection_notes', '')
        
        try:
            inspection.completion_date = completion_date
            inspection.inspection_notes = notes
            inspection.status = 'COMPLETED'
            inspection.save()
            
            return Response({
                "status": "success",
                "message": f"Inspection {inspection.inspection_number} completed"
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve inspection"""
        inspection = self.get_object()
        
        try:
            inspection.status = 'APPROVED'
            inspection.inspection_result = 'PASS'
            inspection.save()
            
            return Response({
                "status": "success",
                "message": f"Inspection {inspection.inspection_number} approved"
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject inspection"""
        inspection = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        try:
            inspection.status = 'REJECTED'
            inspection.inspection_result = 'FAIL'
            inspection.rejection_reason = rejection_reason
            inspection.save()
            
            return Response({
                "status": "success",
                "message": f"Inspection {inspection.inspection_number} rejected"
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class NonConformanceViewSet(viewsets.ModelViewSet):
    """API for Non-Conformance management"""
    queryset = NonConformance.objects.select_related('quality_inspection', 'goods_receipt')
    serializer_class = NonConformanceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'quality_inspection', 'severity', 'issue_category']
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve non-conformance"""
        nc = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        resolved_date = request.data.get('resolved_date')
        
        try:
            nc.resolution_notes = resolution_notes
            nc.resolved_date = resolved_date
            nc.status = 'RESOLVED'
            nc.save()
            
            return Response({
                "status": "success",
                "message": "Non-conformance resolved"
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ReturnToVendorViewSet(viewsets.ModelViewSet):
    """API for Return to Vendor management"""
    queryset = ReturnToVendor.objects.select_related('goods_receipt').prefetch_related('lines')
    serializer_class = ReturnToVendorSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'goods_receipt', 'return_reason']
    search_fields = ['rtv_number']
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit RTV"""
        rtv = self.get_object()
        rtv.status = 'SUBMITTED'
        rtv.save()
        return Response({"status": "success", "message": "RTV submitted"})
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve RTV"""
        rtv = self.get_object()
        rtv.status = 'APPROVED'
        rtv.save()
        return Response({"status": "success", "message": "RTV approved"})
    
    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """Ship RTV"""
        rtv = self.get_object()
        rtv.status = 'SHIPPED'
        rtv.ship_date = request.data.get('ship_date')
        rtv.save()
        return Response({"status": "success", "message": "RTV shipped"})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete RTV"""
        rtv = self.get_object()
        rtv.status = 'COMPLETED'
        rtv.save()
        return Response({"status": "success", "message": "RTV completed"})


class RTVLineViewSet(viewsets.ModelViewSet):
    """API for RTV Line management"""
    queryset = RTVLine.objects.select_related('rtv', 'grn_line')
    serializer_class = RTVLineSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rtv']


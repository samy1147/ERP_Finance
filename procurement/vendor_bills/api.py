"""
Vendor Bill API

REST API endpoints for 3-Way Match & Vendor Bills module.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Sum, Q
from django.utils import timezone

from .models import (
    VendorBill, VendorBillLine, ThreeWayMatch,
    MatchException, MatchTolerance
)
from .serializers import (
    VendorBillSerializer, VendorBillCreateSerializer,
    VendorBillLineSerializer, ThreeWayMatchSerializer,
    MatchExceptionSerializer, MatchToleranceSerializer,
    VendorBillSummarySerializer
)
from .services import ThreeWayMatchService


class VendorBillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Vendor Bills.
    
    Endpoints:
    - list: Get all vendor bills
    - retrieve: Get single vendor bill
    - create: Create new vendor bill
    - update: Update vendor bill
    - destroy: Delete vendor bill
    - submit: Submit bill for matching (POST)
    - match: Run 3-way match (POST)
    - approve: Approve matched bill (POST)
    - reject: Reject bill (POST)
    - post_to_ap: Post to AP module (POST)
    - summary: Get bills summary (GET)
    """
    
    queryset = VendorBill.objects.all().select_related(
        'supplier', 'currency', 'ap_invoice'
    ).prefetch_related('lines')
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VendorBillCreateSerializer
        return VendorBillSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to add detailed error logging."""
        print("=" * 80)
        print("VENDOR BILL CREATE REQUEST")
        print("=" * 80)
        print(f"Request data: {request.data}")
        print("=" * 80)
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            print("VALIDATION ERRORS:")
            print(serializer.errors)
            print("=" * 80)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            import traceback
            print("EXCEPTION DURING CREATE:")
            print(traceback.format_exc())
            print("=" * 80)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by match status
        match_status = self.request.query_params.get('match_status')
        if match_status:
            queryset = queryset.filter(match_status=match_status)
        
        # Filter by supplier
        supplier_id = self.request.query_params.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        
        # Filter by PO
        po_id = self.request.query_params.get('po')
        if po_id:
            queryset = queryset.filter(po_id=po_id)
        
        # Filter by exceptions
        has_exceptions = self.request.query_params.get('has_exceptions')
        if has_exceptions == 'true':
            queryset = queryset.filter(has_exceptions=True)
        
        # Filter by posted status
        is_posted = self.request.query_params.get('is_posted_to_ap')
        if is_posted == 'true':
            queryset = queryset.filter(is_posted_to_ap=True)
        elif is_posted == 'false':
            queryset = queryset.filter(is_posted_to_ap=False)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit vendor bill for matching."""
        vendor_bill = self.get_object()
        
        if vendor_bill.status != 'DRAFT':
            return Response(
                {'error': 'Only draft bills can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vendor_bill.submit(request.user)
            serializer = self.get_serializer(vendor_bill)
            return Response({
                'message': 'Vendor bill submitted successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def match(self, request, pk=None):
        """Run 3-way match on vendor bill."""
        vendor_bill = self.get_object()
        
        # Allow re-matching for EXCEPTION status bills (after exception resolution)
        if vendor_bill.status not in ['SUBMITTED', 'PARTIALLY_MATCHED', 'EXCEPTION']:
            return Response(
                {'error': 'Bill must be submitted before matching'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            match_service = ThreeWayMatchService()
            result = match_service.match_vendor_bill(vendor_bill, request.user)
            
            # Update bill status based on match results (same logic as perform_three_way_match)
            if result['has_exceptions']:
                vendor_bill.status = 'EXCEPTION'
                vendor_bill.has_exceptions = True
                vendor_bill.exception_count = result['exception_count']
            else:
                vendor_bill.status = 'MATCHED'
                vendor_bill.is_matched = True
                vendor_bill.match_date = timezone.now()
            
            vendor_bill.save()
            vendor_bill.refresh_from_db()
            serializer = self.get_serializer(vendor_bill)
            
            return Response({
                'message': f'Matched {result["matched_lines"]} line(s), {result["exception_lines"]} exception(s)',
                'matches_created': result['matched_lines'],
                'is_matched': vendor_bill.is_matched,
                'has_exceptions': vendor_bill.has_exceptions,
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def force_matched(self, request, pk=None):
        """TESTING ONLY: Force bill to MATCHED status to skip exception resolution"""
        vendor_bill = self.get_object()
        
        vendor_bill.status = 'MATCHED'
        vendor_bill.is_matched = True
        vendor_bill.has_exceptions = False
        vendor_bill.exception_count = 0
        vendor_bill.match_date = timezone.now()
        vendor_bill.save()
        
        serializer = self.get_serializer(vendor_bill)
        return Response({
            'message': 'Bill forced to MATCHED status (testing only)',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve matched vendor bill."""
        vendor_bill = self.get_object()
        
        if not vendor_bill.is_matched:
            return Response(
                {'error': 'Bill must be fully matched before approval'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if vendor_bill.has_exceptions and not vendor_bill.exceptions_resolved:
            return Response(
                {'error': 'All exceptions must be resolved before approval'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vendor_bill.approve(request.user)
            serializer = self.get_serializer(vendor_bill)
            return Response({
                'message': 'Vendor bill approved successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject vendor bill."""
        vendor_bill = self.get_object()
        reason = request.data.get('reason', '')
        
        if vendor_bill.status == 'POSTED_TO_AP':
            return Response(
                {'error': 'Cannot reject bill that is already posted to AP'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vendor_bill.status = 'REJECTED'
            vendor_bill.notes = f"{vendor_bill.notes}\n\nREJECTED by {request.user.username}: {reason}".strip()
            vendor_bill.save()
            
            serializer = self.get_serializer(vendor_bill)
            return Response({
                'message': 'Vendor bill rejected',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def post_to_ap(self, request, pk=None):
        """Post vendor bill to AP module (creates AP Invoice)."""
        vendor_bill = self.get_object()
        
        if vendor_bill.status != 'APPROVED':
            return Response(
                {'error': 'Only approved bills can be posted to AP'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if vendor_bill.ap_invoice:
            return Response(
                {'error': 'Bill is already posted to AP'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ap_invoice = vendor_bill.post_to_ap(request.user)
            serializer = self.get_serializer(vendor_bill)
            return Response({
                'message': 'Posted to AP successfully',
                'ap_invoice_id': ap_invoice.id,
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], url_path='grns-needing-invoice')
    def grns_needing_invoice(self, request):
        """
        Get list of GRNs (Goods Receipt Notes) that need invoicing.
        Returns COMPLETED GRNs that don't have associated vendor bills yet.
        """
        from procurement.receiving.models import GoodsReceipt
        from procurement.receiving.serializers import GoodsReceiptListSerializer
        
        # Get all COMPLETED GRNs
        grns = GoodsReceipt.objects.filter(
            status='COMPLETED'
        ).exclude(
            # Exclude GRNs that already have non-cancelled/rejected bills
            id__in=VendorBill.objects.exclude(
                status__in=['CANCELLED', 'REJECTED']
            ).values_list('grn_header_id', flat=True).distinct()
        ).select_related(
            'supplier', 'po_header', 'warehouse'
        ).order_by('-receipt_date')
        
        # Apply filters
        supplier_id = request.query_params.get('supplier')
        if supplier_id:
            grns = grns.filter(supplier_id=supplier_id)
        
        po_number = request.query_params.get('po_number')
        if po_number:
            grns = grns.filter(po_header__po_number__icontains=po_number)
        
        serializer = GoodsReceiptListSerializer(grns, many=True)
        return Response({
            'count': grns.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get vendor bills summary for dashboard."""
        queryset = self.get_queryset()
        
        summary = {
            'total_bills': queryset.count(),
            'draft_count': queryset.filter(status='DRAFT').count(),
            'submitted_count': queryset.filter(status='SUBMITTED').count(),
            'matched_count': queryset.filter(is_matched=True).count(),
            'approved_count': queryset.filter(status='APPROVED').count(),
            'posted_count': queryset.filter(is_posted_to_ap=True).count(),
            'total_amount': queryset.aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'pending_match_count': queryset.filter(
                status='SUBMITTED',
                is_matched=False
            ).count(),
            'exceptions_count': queryset.filter(has_exceptions=True).count(),
            'blocked_count': queryset.filter(
                has_exceptions=True,
                exceptions_resolved=False
            ).count(),
        }
        
        serializer = VendorBillSummarySerializer(summary)
        return Response(serializer.data)


class ThreeWayMatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Three-Way Match records (read-only).
    
    Endpoints:
    - list: Get all match records
    - retrieve: Get single match record
    - resolve: Resolve match variance (POST)
    """
    
    queryset = ThreeWayMatch.objects.all().select_related(
        'vendor_bill_line', 'grn_line', 'catalog_item', 'matched_by'
    )
    serializer_class = ThreeWayMatchSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_queryset(self):
        """Filter by vendor bill or status."""
        queryset = super().get_queryset()
        
        vendor_bill_id = self.request.query_params.get('vendor_bill')
        if vendor_bill_id:
            queryset = queryset.filter(vendor_bill_id=vendor_bill_id)
        
        match_status = self.request.query_params.get('match_status')
        if match_status:
            queryset = queryset.filter(match_status=match_status)
        
        return queryset.order_by('-matched_date')
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve match variance."""
        match_record = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        
        if match_record.is_resolved:
            return Response(
                {'error': 'Match is already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            match_record.is_resolved = True
            match_record.resolved_by = request.user
            match_record.resolved_date = timezone.now()
            match_record.resolution_notes = resolution_notes
            match_record.save()
            
            serializer = self.get_serializer(match_record)
            return Response({
                'message': 'Match variance resolved',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MatchExceptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Match Exceptions.
    
    Endpoints:
    - list: Get all exceptions
    - retrieve: Get single exception
    - create: Create exception
    - update: Update exception
    - resolve: Resolve exception (POST)
    """
    
    queryset = MatchException.objects.all().select_related(
        'three_way_match__vendor_bill_line__vendor_bill',
        'resolved_by', 'approved_by'
    )
    serializer_class = MatchExceptionSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_queryset(self):
        """Filter by vendor bill or status."""
        queryset = super().get_queryset()
        
        vendor_bill_id = self.request.query_params.get('vendor_bill')
        if vendor_bill_id:
            queryset = queryset.filter(three_way_match__vendor_bill_line__vendor_bill_id=vendor_bill_id)
        
        exception_status = self.request.query_params.get('status')
        if exception_status:
            queryset = queryset.filter(resolution_status=exception_status)
        
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set created_by on creation."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve exception."""
        exception = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        resolution_action = request.data.get('resolution_action', 'OTHER')
        
        if exception.resolution_status == 'RESOLVED':
            return Response(
                {'error': 'Exception is already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            exception.resolution_status = 'RESOLVED'
            exception.resolution_action = resolution_action
            exception.resolution_notes = resolution_notes
            exception.resolved_by = request.user
            exception.resolved_date = timezone.now()
            exception.save()
            
            # Check if all exceptions are resolved for the vendor bill
            vendor_bill = exception.three_way_match.vendor_bill_line.vendor_bill
            unresolved = MatchException.objects.filter(
                three_way_match__vendor_bill_line__vendor_bill=vendor_bill,
                resolution_status='UNRESOLVED'
            ).count()
            
            if unresolved == 0:
                vendor_bill.exceptions_resolved = True
                vendor_bill.status = 'SUBMITTED'  # Move back to submitted so it can be matched again
                vendor_bill.save()
            
            serializer = self.get_serializer(exception)
            return Response({
                'message': 'Exception resolved successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MatchToleranceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Match Tolerances.
    
    Endpoints:
    - list: Get all tolerances
    - retrieve: Get single tolerance
    - create: Create tolerance
    - update: Update tolerance
    - destroy: Delete tolerance
    """
    
    queryset = MatchTolerance.objects.all().select_related(
        'supplier', 'item', 'created_by'
    )
    serializer_class = MatchToleranceSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_queryset(self):
        """Filter by level, supplier, or item."""
        queryset = super().get_queryset()
        
        tolerance_level = self.request.query_params.get('level')
        if tolerance_level:
            queryset = queryset.filter(tolerance_level=tolerance_level)
        
        supplier_id = self.request.query_params.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        
        item_id = self.request.query_params.get('item')
        if item_id:
            queryset = queryset.filter(item_id=item_id)
        
        is_active = self.request.query_params.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('tolerance_level', '-created_at')
    
    def perform_create(self, serializer):
        """Set created_by on creation."""
        serializer.save(created_by=self.request.user)

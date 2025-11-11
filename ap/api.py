# ap/api.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from decimal import Decimal

from .models import (
    Supplier, VendorContact, VendorDocument, VendorPerformanceRecord,
    VendorOnboardingChecklist, APInvoice
)
from .serializers import (
    SupplierListSerializer, SupplierDetailSerializer, SupplierCreateUpdateSerializer,
    VendorContactSerializer, VendorDocumentSerializer, VendorPerformanceRecordSerializer,
    VendorOnboardingChecklistSerializer
)


class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Supplier/Vendor management
    
    Provides CRUD operations and additional actions for:
    - Vendor onboarding
    - Performance tracking
    - Risk assessment
    - Document management
    """
    queryset = Supplier.objects.all()
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'country': ['exact', 'in'],
        'vendor_category': ['exact', 'in'],
        'is_active': ['exact'],
        'is_preferred': ['exact'],
        'is_blacklisted': ['exact'],
        'is_on_hold': ['exact'],
        'onboarding_status': ['exact', 'in'],
        'compliance_verified': ['exact'],
        'performance_score': ['gte', 'lte'],
    }
    search_fields = ['code', 'name', 'legal_name', 'email', 'vat_number', 'tax_id']
    ordering_fields = ['code', 'name', 'performance_score', 'created_at', 'updated_at']
    ordering = ['code']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return SupplierListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SupplierCreateUpdateSerializer
        return SupplierDetailSerializer
    
    def perform_create(self, serializer):
        """Set created_by when creating a vendor"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_preferred(self, request, pk=None):
        """Mark vendor as preferred"""
        vendor = self.get_object()
        vendor.is_preferred = True
        vendor.save()
        return Response({
            'status': 'success',
            'message': f'Vendor {vendor.name} marked as preferred'
        })
    
    @action(detail=True, methods=['post'])
    def remove_preferred(self, request, pk=None):
        """Remove preferred status"""
        vendor = self.get_object()
        vendor.is_preferred = False
        vendor.save()
        return Response({
            'status': 'success',
            'message': f'Preferred status removed from {vendor.name}'
        })
    
    @action(detail=True, methods=['post'])
    def put_on_hold(self, request, pk=None):
        """Put vendor on hold"""
        vendor = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response(
                {'error': 'Hold reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vendor.is_on_hold = True
        vendor.hold_reason = reason
        vendor.save()
        
        return Response({
            'status': 'success',
            'message': f'Vendor {vendor.name} put on hold'
        })
    
    @action(detail=True, methods=['post'])
    def remove_hold(self, request, pk=None):
        """Remove hold status"""
        vendor = self.get_object()
        vendor.is_on_hold = False
        vendor.hold_reason = ''
        vendor.save()
        return Response({
            'status': 'success',
            'message': f'Hold status removed from {vendor.name}'
        })
    
    @action(detail=True, methods=['post'])
    def blacklist(self, request, pk=None):
        """Blacklist a vendor"""
        vendor = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response(
                {'error': 'Blacklist reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vendor.is_blacklisted = True
        vendor.is_active = False
        vendor.blacklist_reason = reason
        vendor.save()
        
        return Response({
            'status': 'success',
            'message': f'Vendor {vendor.name} blacklisted'
        })
    
    @action(detail=True, methods=['post'])
    def remove_blacklist(self, request, pk=None):
        """Remove blacklist status"""
        vendor = self.get_object()
        vendor.is_blacklisted = False
        vendor.blacklist_reason = ''
        # Note: is_active should be manually re-enabled by admin
        vendor.save()
        return Response({
            'status': 'success',
            'message': f'Blacklist status removed from {vendor.name}. Please manually activate if needed.'
        })
    
    @action(detail=True, methods=['get'])
    def performance_summary(self, request, pk=None):
        """Get performance summary for vendor"""
        vendor = self.get_object()
        
        # Get latest performance record
        latest_performance = vendor.performance_records.order_by('-period_end').first()
        
        # Get invoice statistics
        invoice_stats = APInvoice.objects.filter(supplier=vendor).aggregate(
            total_count=Count('id'),
            posted_count=Count('id', filter=Q(is_posted=True)),
            cancelled_count=Count('id', filter=Q(is_cancelled=True)),
            total_value=Sum('total'),
        )
        
        return Response({
            'vendor_id': vendor.id,
            'vendor_name': vendor.name,
            'performance_score': vendor.performance_score,
            'quality_score': vendor.quality_score,
            'delivery_score': vendor.delivery_score,
            'price_score': vendor.price_score,
            'latest_performance_record': VendorPerformanceRecordSerializer(latest_performance).data if latest_performance else None,
            'invoice_statistics': invoice_stats,
            'is_preferred': vendor.is_preferred,
            'can_transact': vendor.can_transact(),
        })
    
    @action(detail=True, methods=['get'])
    def onboarding_progress(self, request, pk=None):
        """Get onboarding progress for vendor"""
        vendor = self.get_object()
        
        checklist_items = vendor.onboarding_checklist.all()
        total_items = checklist_items.count()
        completed_items = checklist_items.filter(is_completed=True).count()
        required_items = checklist_items.filter(is_required=True).count()
        completed_required = checklist_items.filter(is_required=True, is_completed=True).count()
        
        progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
        required_progress = (completed_required / required_items * 100) if required_items > 0 else 0
        
        # Document status
        documents = vendor.documents.all()
        total_docs = documents.count()
        verified_docs = documents.filter(is_verified=True).count()
        expired_docs = documents.filter(expiry_date__lt=timezone.now().date()).count()
        required_docs = documents.filter(is_required_for_onboarding=True).count()
        required_verified = documents.filter(is_required_for_onboarding=True, is_verified=True).count()
        
        return Response({
            'vendor_id': vendor.id,
            'vendor_name': vendor.name,
            'onboarding_status': vendor.onboarding_status,
            'onboarding_completed_date': vendor.onboarding_completed_date,
            'compliance_verified': vendor.compliance_verified,
            'checklist': {
                'total_items': total_items,
                'completed_items': completed_items,
                'required_items': required_items,
                'completed_required': completed_required,
                'progress_percentage': round(progress_percentage, 2),
                'required_progress_percentage': round(required_progress, 2),
                'items': VendorOnboardingChecklistSerializer(checklist_items, many=True).data
            },
            'documents': {
                'total_documents': total_docs,
                'verified_documents': verified_docs,
                'expired_documents': expired_docs,
                'required_documents': required_docs,
                'required_verified': required_verified,
                'documents': VendorDocumentSerializer(documents, many=True).data
            },
            'can_complete_onboarding': required_progress == 100 and required_verified == required_docs
        })
    
    @action(detail=True, methods=['post'])
    def complete_onboarding(self, request, pk=None):
        """Mark vendor onboarding as complete"""
        vendor = self.get_object()
        
        # Check if all required checklist items are completed
        required_incomplete = vendor.onboarding_checklist.filter(
            is_required=True,
            is_completed=False
        ).exists()
        
        if required_incomplete:
            return Response(
                {'error': 'All required onboarding checklist items must be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if all required documents are verified
        required_unverified = vendor.documents.filter(
            is_required_for_onboarding=True,
            is_verified=False
        ).exists()
        
        if required_unverified:
            return Response(
                {'error': 'All required onboarding documents must be verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vendor.onboarding_status = 'COMPLETED'
        vendor.onboarding_completed_date = timezone.now().date()
        vendor.compliance_verified = True
        vendor.compliance_verified_date = timezone.now().date()
        vendor.save()
        
        return Response({
            'status': 'success',
            'message': f'Onboarding completed for {vendor.name}',
            'onboarding_completed_date': vendor.onboarding_completed_date
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get overall vendor statistics"""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'total_vendors': queryset.count(),
            'active_vendors': queryset.filter(is_active=True).count(),
            'preferred_vendors': queryset.filter(is_preferred=True).count(),
            'blacklisted_vendors': queryset.filter(is_blacklisted=True).count(),
            'on_hold_vendors': queryset.filter(is_on_hold=True).count(),
            'by_onboarding_status': {
                status[0]: queryset.filter(onboarding_status=status[0]).count()
                for status in Supplier.ONBOARDING_STATUSES
            },
            'by_vendor_category': {
                cat[0]: queryset.filter(vendor_category=cat[0]).count()
                for cat in Supplier.VENDOR_CATEGORIES
            },
            'by_country': dict(
                queryset.values('country').annotate(count=Count('id')).values_list('country', 'count')
            ),
            'average_performance_score': queryset.aggregate(
                avg=Avg('performance_score')
            )['avg'],
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def expiring_documents(self, request):
        """Get vendors with expiring documents"""
        days = int(request.query_params.get('days', 30))
        cutoff_date = timezone.now().date() + timezone.timedelta(days=days)
        
        expiring_docs = VendorDocument.objects.filter(
            expiry_date__lte=cutoff_date,
            expiry_date__gte=timezone.now().date(),
            is_verified=True
        ).select_related('vendor')
        
        return Response(VendorDocumentSerializer(expiring_docs, many=True).data)


class VendorContactViewSet(viewsets.ModelViewSet):
    """ViewSet for Vendor Contacts"""
    queryset = VendorContact.objects.all()
    serializer_class = VendorContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['vendor', 'contact_type', 'is_primary', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'vendor__name']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['-is_primary', 'last_name']


class VendorDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for Vendor Documents"""
    queryset = VendorDocument.objects.all()
    serializer_class = VendorDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'vendor': ['exact'],
        'document_type': ['exact', 'in'],
        'is_verified': ['exact'],
        'is_required_for_onboarding': ['exact'],
        'expiry_date': ['gte', 'lte'],
    }
    search_fields = ['document_name', 'document_number', 'vendor__name']
    ordering_fields = ['document_type', 'issue_date', 'expiry_date', 'created_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set uploaded_by when creating a document"""
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a document"""
        document = self.get_object()
        document.is_verified = True
        document.verified_by = request.user
        document.verified_date = timezone.now().date()
        document.save()
        
        return Response({
            'status': 'success',
            'message': f'Document {document.document_name} verified'
        })
    
    @action(detail=True, methods=['post'])
    def unverify(self, request, pk=None):
        """Unverify a document"""
        document = self.get_object()
        document.is_verified = False
        document.verified_by = None
        document.verified_date = None
        document.save()
        
        return Response({
            'status': 'success',
            'message': f'Document {document.document_name} unverified'
        })


class VendorPerformanceRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for Vendor Performance Records"""
    queryset = VendorPerformanceRecord.objects.all()
    serializer_class = VendorPerformanceRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'vendor': ['exact'],
        'risk_level': ['exact', 'in'],
        'period_start': ['gte', 'lte'],
        'period_end': ['gte', 'lte'],
        'overall_score': ['gte', 'lte'],
    }
    search_fields = ['vendor__name', 'vendor__code']
    ordering_fields = ['period_end', 'overall_score', 'created_at']
    ordering = ['-period_end']
    
    def perform_create(self, serializer):
        """Set created_by and calculate scores when creating"""
        instance = serializer.save(created_by=self.request.user)
        instance.calculate_scores()
    
    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        """Recalculate performance scores"""
        record = self.get_object()
        record.calculate_scores()
        
        return Response({
            'status': 'success',
            'message': 'Performance scores recalculated',
            'data': VendorPerformanceRecordSerializer(record).data
        })


class VendorOnboardingChecklistViewSet(viewsets.ModelViewSet):
    """ViewSet for Vendor Onboarding Checklist"""
    queryset = VendorOnboardingChecklist.objects.all()
    serializer_class = VendorOnboardingChecklistSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['vendor', 'is_completed', 'is_required']
    search_fields = ['item_name', 'vendor__name']
    ordering_fields = ['priority', 'item_name', 'completed_date']
    ordering = ['priority', 'item_name']
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark checklist item as complete"""
        item = self.get_object()
        item.is_completed = True
        item.completed_date = timezone.now().date()
        item.completed_by = request.user
        item.save()
        
        return Response({
            'status': 'success',
            'message': f'Checklist item "{item.item_name}" marked as complete'
        })
    
    @action(detail=True, methods=['post'])
    def uncomplete(self, request, pk=None):
        """Mark checklist item as incomplete"""
        item = self.get_object()
        item.is_completed = False
        item.completed_date = None
        item.completed_by = None
        item.save()
        
        return Response({
            'status': 'success',
            'message': f'Checklist item "{item.item_name}" marked as incomplete'
        })

# catalog/api.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from decimal import Decimal

from .models import (
    UnitOfMeasure, CatalogCategory, CatalogItem, SupplierPriceTier,
    FrameworkAgreement, FrameworkItem, CallOffOrder, CallOffLine
)
from .serializers import (
    UnitOfMeasureSerializer, CatalogCategorySerializer,
    CatalogItemListSerializer, CatalogItemDetailSerializer, CatalogItemCreateUpdateSerializer,
    SupplierPriceTierSerializer, FrameworkAgreementListSerializer,
    FrameworkAgreementDetailSerializer, FrameworkAgreementCreateUpdateSerializer,
    FrameworkItemSerializer, CallOffOrderListSerializer,
    CallOffOrderDetailSerializer, CallOffOrderCreateUpdateSerializer,
    CallOffLineSerializer
)


class UnitOfMeasureViewSet(viewsets.ModelViewSet):
    """ViewSet for Units of Measure"""
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['uom_type', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name']
    ordering = ['code']


class CatalogCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Catalog Categories"""
    queryset = CatalogCategory.objects.all()
    serializer_class = CatalogCategorySerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['parent', 'level', 'is_active']
    search_fields = ['code', 'name', 'full_path']
    ordering_fields = ['code', 'name', 'level']
    ordering = ['code']
    
    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """Get all subcategories of a category"""
        category = self.get_object()
        subcategories = category.children.filter(is_active=True)
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree structure"""
        top_level = self.queryset.filter(parent__isnull=True, is_active=True)
        
        def build_tree(categories):
            tree = []
            for cat in categories:
                node = {
                    'id': cat.id,
                    'code': cat.code,
                    'name': cat.name,
                    'level': cat.level,
                    'children': build_tree(cat.children.filter(is_active=True))
                }
                tree.append(node)
            return tree
        
        tree = build_tree(top_level)
        return Response(tree)


class CatalogItemViewSet(viewsets.ModelViewSet):
    """ViewSet for Catalog Items"""
    queryset = CatalogItem.objects.all()
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'category': ['exact'],
        'item_type': ['exact', 'in'],
        'is_active': ['exact'],
        'is_purchasable': ['exact'],
        'is_restricted': ['exact'],
        'list_price': ['gte', 'lte'],
        'preferred_supplier': ['exact'],
    }
    search_fields = ['sku', 'item_code', 'name', 'short_description', 
                    'manufacturer', 'manufacturer_part_number', 'brand']
    ordering_fields = ['sku', 'name', 'list_price', 'created_at']
    ordering = ['sku']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CatalogItemListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CatalogItemCreateUpdateSerializer
        return CatalogItemDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def price_tiers(self, request, pk=None):
        """Get all price tiers for an item"""
        item = self.get_object()
        supplier_id = request.query_params.get('supplier')
        
        price_tiers = item.supplier_price_tiers.filter(is_active=True)
        
        if supplier_id:
            price_tiers = price_tiers.filter(supplier_id=supplier_id)
        
        # Filter for currently valid tiers
        today = timezone.now().date()
        price_tiers = price_tiers.filter(
            valid_from__lte=today
        ).filter(
            Q(valid_to__isnull=True) | Q(valid_to__gte=today)
        ).order_by('supplier', 'min_quantity')
        
        serializer = SupplierPriceTierSerializer(price_tiers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def get_effective_price(self, request, pk=None):
        """Get effective price for a given quantity and supplier"""
        item = self.get_object()
        quantity = Decimal(str(request.data.get('quantity', 1)))
        supplier_id = request.data.get('supplier_id')
        
        from ap.models import Supplier
        supplier = None
        if supplier_id:
            try:
                supplier = Supplier.objects.get(id=supplier_id)
            except Supplier.DoesNotExist:
                pass
        
        effective_price = item.get_effective_price(quantity, supplier)
        
        return Response({
            'item_sku': item.sku,
            'quantity': str(quantity),
            'supplier': supplier.name if supplier else 'Default',
            'effective_price': str(effective_price),
            'currency': item.currency.code,
            'total': str(effective_price * quantity)
        })
    
    @action(detail=False, methods=['get'])
    def search_catalog(self, request):
        """Advanced catalog search"""
        query = request.query_params.get('q', '')
        category = request.query_params.get('category')
        item_type = request.query_params.get('item_type')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        
        queryset = self.get_queryset().filter(is_active=True, is_purchasable=True)
        
        if query:
            queryset = queryset.filter(
                Q(sku__icontains=query) |
                Q(name__icontains=query) |
                Q(short_description__icontains=query) |
                Q(manufacturer__icontains=query) |
                Q(brand__icontains=query)
            )
        
        if category:
            queryset = queryset.filter(category_id=category)
        
        if item_type:
            queryset = queryset.filter(item_type=item_type)
        
        if min_price:
            queryset = queryset.filter(list_price__gte=Decimal(min_price))
        
        if max_price:
            queryset = queryset.filter(list_price__lte=Decimal(max_price))
        
        serializer = self.get_serializer(queryset[:50], many=True)  # Limit to 50 results
        return Response(serializer.data)


class SupplierPriceTierViewSet(viewsets.ModelViewSet):
    """ViewSet for Supplier Price Tiers"""
    queryset = SupplierPriceTier.objects.all()
    serializer_class = SupplierPriceTierSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['catalog_item', 'supplier', 'is_active']
    search_fields = ['catalog_item__sku', 'supplier__name']
    ordering = ['catalog_item', 'supplier', 'min_quantity']


class FrameworkAgreementViewSet(viewsets.ModelViewSet):
    """ViewSet for Framework Agreements"""
    queryset = FrameworkAgreement.objects.all()
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'agreement_type': ['exact', 'in'],
        'status': ['exact', 'in'],
        'supplier': ['exact'],
        'start_date': ['gte', 'lte'],
        'end_date': ['gte', 'lte'],
    }
    search_fields = ['agreement_number', 'title', 'supplier__name', 'department']
    ordering_fields = ['agreement_number', 'title', 'start_date', 'end_date']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FrameworkAgreementListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return FrameworkAgreementCreateUpdateSerializer
        return FrameworkAgreementDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate framework agreement"""
        framework = self.get_object()
        
        if framework.status == 'PENDING_APPROVAL':
            framework.activate(request.user)
            return Response({
                'status': 'success',
                'message': f'Framework {framework.agreement_number} activated'
            })
        
        return Response(
            {'error': 'Framework must be in PENDING_APPROVAL status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend framework agreement"""
        framework = self.get_object()
        reason = request.data.get('reason', '')
        
        if framework.status == 'ACTIVE':
            framework.suspend(reason)
            return Response({
                'status': 'success',
                'message': f'Framework {framework.agreement_number} suspended'
            })
        
        return Response(
            {'error': 'Only active frameworks can be suspended'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate framework agreement"""
        framework = self.get_object()
        reason = request.data.get('reason', '')
        
        framework.terminate(reason)
        return Response({
            'status': 'success',
            'message': f'Framework {framework.agreement_number} terminated'
        })
    
    @action(detail=True, methods=['get'])
    def utilization(self, request, pk=None):
        """Get framework utilization details"""
        framework = self.get_object()
        
        return Response({
            'agreement_number': framework.agreement_number,
            'total_contract_value': str(framework.total_contract_value) if framework.total_contract_value else None,
            'total_committed': str(framework.total_committed),
            'total_spent': str(framework.total_spent),
            'remaining_value': str(framework.get_remaining_value()) if framework.get_remaining_value() else None,
            'utilization_percent': round(framework.get_utilization_percent(), 2),
            'is_limit_warning': framework.is_limit_warning(),
            'calloff_count': framework.calloff_orders.count(),
            'active_calloff_count': framework.calloff_orders.filter(
                status__in=['APPROVED', 'SENT_TO_SUPPLIER', 'CONFIRMED', 'IN_DELIVERY']
            ).count()
        })
    
    @action(detail=False, methods=['get'])
    def active_frameworks(self, request):
        """Get all active frameworks"""
        today = timezone.now().date()
        active = self.queryset.filter(
            status='ACTIVE',
            start_date__lte=today,
            end_date__gte=today
        )
        
        serializer = self.get_serializer(active, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get frameworks expiring within specified days"""
        days = int(request.query_params.get('days', 30))
        today = timezone.now().date()
        
        from datetime import timedelta
        expiry_date = today + timedelta(days=days)
        
        expiring = self.queryset.filter(
            status='ACTIVE',
            start_date__lte=today,
            end_date__gte=today,
            end_date__lte=expiry_date
        ).order_by('end_date')
        
        serializer = self.get_serializer(expiring, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get framework statistics"""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'total_frameworks': queryset.count(),
            'by_status': {
                s[0]: queryset.filter(status=s[0]).count()
                for s in FrameworkAgreement.STATUS_CHOICES
            },
            'by_type': {
                t[0]: queryset.filter(agreement_type=t[0]).count()
                for t in FrameworkAgreement.AGREEMENT_TYPES
            },
            'active_count': queryset.filter(status='ACTIVE').count(),
            'total_value': queryset.aggregate(
                total=Sum('total_contract_value')
            )['total'] or 0,
            'total_committed': queryset.aggregate(
                total=Sum('total_committed')
            )['total'] or 0,
            'total_spent': queryset.aggregate(
                total=Sum('total_spent')
            )['total'] or 0,
        }
        
        return Response(stats)


class FrameworkItemViewSet(viewsets.ModelViewSet):
    """ViewSet for Framework Items"""
    queryset = FrameworkItem.objects.all()
    serializer_class = FrameworkItemSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['framework', 'catalog_item', 'is_active']
    search_fields = ['framework__agreement_number', 'catalog_item__sku', 'catalog_item__name']
    ordering = ['framework', 'line_number']


class CallOffOrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Call-Off Orders"""
    queryset = CallOffOrder.objects.all()
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'framework': ['exact'],
        'status': ['exact', 'in'],
        'order_date': ['gte', 'lte'],
        'requested_by': ['exact'],
        'department': ['exact'],
    }
    search_fields = ['calloff_number', 'framework__agreement_number', 'internal_reference']
    ordering_fields = ['calloff_number', 'order_date', 'total_amount']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CallOffOrderListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CallOffOrderCreateUpdateSerializer
        return CallOffOrderDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            requested_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit call-off for approval"""
        calloff = self.get_object()
        
        if calloff.submit():
            return Response({
                'status': 'success',
                'message': f'Call-off {calloff.calloff_number} submitted'
            })
        
        return Response(
            {'error': 'Call-off must be in DRAFT status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve call-off order"""
        calloff = self.get_object()
        
        if calloff.approve(request.user):
            return Response({
                'status': 'success',
                'message': f'Call-off {calloff.calloff_number} approved'
            })
        
        return Response(
            {'error': 'Call-off must be in SUBMITTED status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def send_to_supplier(self, request, pk=None):
        """Send call-off to supplier"""
        calloff = self.get_object()
        
        if calloff.send_to_supplier():
            return Response({
                'status': 'success',
                'message': f'Call-off {calloff.calloff_number} sent to supplier'
            })
        
        return Response(
            {'error': 'Call-off must be APPROVED'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark call-off as completed"""
        calloff = self.get_object()
        
        if calloff.complete():
            return Response({
                'status': 'success',
                'message': f'Call-off {calloff.calloff_number} completed'
            })
        
        return Response(
            {'error': 'Call-off must be CONFIRMED or IN_DELIVERY'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel call-off order"""
        calloff = self.get_object()
        reason = request.data.get('reason', '')
        
        if calloff.cancel(reason):
            return Response({
                'status': 'success',
                'message': f'Call-off {calloff.calloff_number} cancelled'
            })
        
        return Response(
            {'error': 'Call-off cannot be cancelled (already completed or cancelled)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        """Recalculate call-off totals"""
        calloff = self.get_object()
        total = calloff.calculate_totals()
        
        return Response({
            'status': 'success',
            'subtotal': str(calloff.subtotal),
            'tax_amount': str(calloff.tax_amount),
            'total_amount': str(calloff.total_amount)
        })
    
    @action(detail=False, methods=['get'])
    def by_framework(self, request):
        """Get call-offs for a specific framework"""
        framework_id = request.query_params.get('framework_id')
        
        if not framework_id:
            return Response(
                {'error': 'framework_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        calloffs = self.queryset.filter(framework_id=framework_id)
        serializer = self.get_serializer(calloffs, many=True)
        return Response(serializer.data)


class CallOffLineViewSet(viewsets.ModelViewSet):
    """ViewSet for Call-Off Lines"""
    queryset = CallOffLine.objects.all()
    serializer_class = CallOffLineSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['calloff', 'catalog_item', 'is_received']
    search_fields = ['calloff__calloff_number', 'catalog_item__sku', 'description']
    ordering = ['calloff', 'line_number']
    
    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """Record receipt of goods"""
        line = self.get_object()
        quantity = Decimal(str(request.data.get('quantity', 0)))
        
        if quantity <= 0:
            return Response(
                {'error': 'Quantity must be positive'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if line.quantity_received + quantity > line.quantity:
            return Response(
                {'error': 'Cannot receive more than ordered quantity'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        line.receive(quantity)
        
        return Response({
            'status': 'success',
            'message': f'Received {quantity} units',
            'quantity_received': str(line.quantity_received),
            'is_received': line.is_received
        })

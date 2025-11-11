"""
API ViewSets for Purchase Requisition management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import CostCenter, Project, PRHeader, PRLine
from .services import PRToPOConversionService, PRLineSelectionHelper
from .serializers import (
    CostCenterSerializer, ProjectSerializer,
    PRHeaderListSerializer, PRHeaderDetailSerializer,
    PRHeaderCreateUpdateSerializer, PRLineSerializer,
    PRSubmitSerializer, PRApproveSerializer,
    PRRejectSerializer, PRCancelSerializer,
    PRConvertSerializer
)


class CostCenterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Cost Center management.
    
    Endpoints:
    - GET /api/requisition/cost-centers/ - List all cost centers
    - POST /api/requisition/cost-centers/ - Create cost center
    - GET /api/requisition/cost-centers/{id}/ - Retrieve cost center
    - PUT/PATCH /api/requisition/cost-centers/{id}/ - Update cost center
    - DELETE /api/requisition/cost-centers/{id}/ - Delete cost center
    - GET /api/requisition/cost-centers/budget_summary/ - Get budget summary
    - GET /api/requisition/cost-centers/{id}/utilization/ - Get utilization
    """
    
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'manager', 'parent']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'annual_budget']
    ordering = ['code']
    
    @action(detail=False, methods=['get'])
    def budget_summary(self, request):
        """Get budget summary across all cost centers."""
        cost_centers = self.get_queryset().filter(is_active=True)
        
        summary = {
            'total_centers': cost_centers.count(),
            'total_budget': sum(cc.annual_budget for cc in cost_centers),
            'total_committed': sum(cc.get_total_committed() for cc in cost_centers),
            'total_available': sum(cc.get_available_budget() for cc in cost_centers),
            'centers_over_budget': sum(
                1 for cc in cost_centers if cc.get_available_budget() < 0
            ),
        }
        
        return Response(summary)
    
    @action(detail=True, methods=['get'])
    def utilization(self, request, pk=None):
        """Get detailed utilization for a cost center."""
        cost_center = self.get_object()
        
        # Get PRs by status
        prs = cost_center.pr_headers.all()
        
        utilization = {
            'cost_center': CostCenterSerializer(cost_center).data,
            'prs_by_status': {
                'draft': prs.filter(status='DRAFT').count(),
                'submitted': prs.filter(status='SUBMITTED').count(),
                'approved': prs.filter(status='APPROVED').count(),
                'converted': prs.filter(status='CONVERTED').count(),
            },
            'committed_amount': float(cost_center.get_total_committed()),
            'available_amount': float(cost_center.get_available_budget()),
            'utilization_pct': float(
                (cost_center.get_total_committed() / cost_center.annual_budget * 100)
                if cost_center.annual_budget else 0
            ),
        }
        
        return Response(utilization)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project management.
    
    Endpoints:
    - GET /api/requisition/projects/ - List all projects
    - POST /api/requisition/projects/ - Create project
    - GET /api/requisition/projects/{id}/ - Retrieve project
    - PUT/PATCH /api/requisition/projects/{id}/ - Update project
    - DELETE /api/requisition/projects/{id}/ - Delete project
    - GET /api/requisition/projects/active/ - Get active projects
    - GET /api/requisition/projects/{id}/utilization/ - Get utilization
    """
    
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'project_manager']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'start_date', 'budget']
    ordering = ['code']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active projects."""
        active_projects = self.get_queryset().filter(status='ACTIVE')
        serializer = self.get_serializer(active_projects, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def utilization(self, request, pk=None):
        """Get detailed utilization for a project."""
        project = self.get_object()
        
        # Get PRs by status
        prs = project.pr_headers.all()
        
        utilization = {
            'project': ProjectSerializer(project).data,
            'prs_by_status': {
                'draft': prs.filter(status='DRAFT').count(),
                'submitted': prs.filter(status='SUBMITTED').count(),
                'approved': prs.filter(status='APPROVED').count(),
                'converted': prs.filter(status='CONVERTED').count(),
            },
            'committed_amount': float(project.get_total_committed()),
            'available_amount': float(project.get_available_budget()),
            'utilization_pct': float(
                (project.get_total_committed() / project.budget * 100)
                if project.budget else 0
            ),
        }
        
        return Response(utilization)


class PRHeaderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Purchase Requisition Header management.
    
    Endpoints:
    - GET /api/requisition/pr-headers/ - List all PRs
    - POST /api/requisition/pr-headers/ - Create PR
    - GET /api/requisition/pr-headers/{id}/ - Retrieve PR
    - PUT/PATCH /api/requisition/pr-headers/{id}/ - Update PR
    - DELETE /api/requisition/pr-headers/{id}/ - Delete PR
    - POST /api/requisition/pr-headers/{id}/submit/ - Submit PR
    - POST /api/requisition/pr-headers/{id}/approve/ - Approve PR
    - POST /api/requisition/pr-headers/{id}/reject/ - Reject PR
    - POST /api/requisition/pr-headers/{id}/cancel/ - Cancel PR
    - POST /api/requisition/pr-headers/{id}/check_budget/ - Check budget
    - POST /api/requisition/pr-headers/{id}/generate_suggestions/ - Generate catalog suggestions
    - POST /api/requisition/pr-headers/{id}/convert_to_po/ - Convert to PO
    - GET /api/requisition/pr-headers/{id}/split_by_vendor/ - Get vendor split
    - GET /api/requisition/pr-headers/my_prs/ - Get current user's PRs
    - GET /api/requisition/pr-headers/pending_approval/ - Get PRs pending approval
    - GET /api/requisition/pr-headers/statistics/ - Get PR statistics
    """
    
    queryset = PRHeader.objects.all()
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'priority', 'requestor', 'cost_center', 'project',
        'budget_check_passed', 'can_split_by_vendor'
    ]
    search_fields = [
        'pr_number', 'title', 'description',
        'requestor__username', 'requestor__email'
    ]
    ordering_fields = ['pr_number', 'pr_date', 'required_date', 'total_amount']
    ordering = ['-pr_date', '-pr_number']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PRHeaderListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PRHeaderCreateUpdateSerializer
        else:
            return PRHeaderDetailSerializer
    
    def perform_create(self, serializer):
        # Use authenticated user if available, otherwise use the requestor from the data
        if self.request.user.is_authenticated:
            created_by = self.request.user
        else:
            # Fall back to the requestor specified in the data
            from django.contrib.auth.models import User
            requestor_id = serializer.validated_data.get('requestor')
            if requestor_id:
                created_by = requestor_id if isinstance(requestor_id, User) else User.objects.get(id=requestor_id.id if hasattr(requestor_id, 'id') else requestor_id)
            else:
                # Default to first superuser if no requestor specified
                created_by = User.objects.filter(is_superuser=True).first()
        
        serializer.save(created_by=created_by)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit PR for approval."""
        pr = self.get_object()
        serializer = PRSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get user - use requestor if not authenticated
            user = request.user if request.user.is_authenticated else pr.requestor
            pr.submit(user)
            return Response({
                'status': 'success',
                'message': f'PR {pr.pr_number} submitted successfully',
                'pr': PRHeaderDetailSerializer(pr).data
            })
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve PR."""
        pr = self.get_object()
        serializer = PRApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get user - use requestor if not authenticated
            user = request.user if request.user.is_authenticated else pr.requestor
            pr.approve(user)
            return Response({
                'status': 'success',
                'message': f'PR {pr.pr_number} approved successfully',
                'pr': PRHeaderDetailSerializer(pr).data
            })
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject PR."""
        pr = self.get_object()
        serializer = PRRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get user - use requestor if not authenticated
            user = request.user if request.user.is_authenticated else pr.requestor
            pr.reject(user, serializer.validated_data['reason'])
            return Response({
                'status': 'success',
                'message': f'PR {pr.pr_number} rejected',
                'pr': PRHeaderDetailSerializer(pr).data
            })
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel PR."""
        pr = self.get_object()
        serializer = PRCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get user - use requestor if not authenticated
            user = request.user if request.user.is_authenticated else pr.requestor
            pr.cancel(user, serializer.validated_data['reason'])
            return Response({
                'status': 'success',
                'message': f'PR {pr.pr_number} cancelled',
                'pr': PRHeaderDetailSerializer(pr).data
            })
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def check_budget(self, request, pk=None):
        """Perform budget check on PR."""
        pr = self.get_object()
        
        passed = pr.check_budget()
        pr.save()
        
        return Response({
            'status': 'success',
            'budget_check_passed': passed,
            'message': pr.budget_check_message,
            'checked_at': pr.budget_checked_at
        })
    
    @action(detail=True, methods=['post'])
    def generate_suggestions(self, request, pk=None):
        """Generate catalog item suggestions for PR lines."""
        pr = self.get_object()
        
        count = pr.generate_catalog_suggestions()
        
        return Response({
            'status': 'success',
            'message': f'Generated suggestions for {count} line(s)',
            'pr': PRHeaderDetailSerializer(pr).data
        })
    
    @action(detail=True, methods=['post'])
    def convert_to_po(self, request, pk=None):
        """Convert PR to PO(s)."""
        pr = self.get_object()
        serializer = PRConvertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if pr.status != 'APPROVED':
            return Response(
                {'status': 'error', 'message': 'Only approved PRs can be converted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        split_by_vendor = serializer.validated_data['split_by_vendor']
        po_type = serializer.validated_data['po_type']
        
        # Get user - use requestor if not authenticated
        user = request.user if request.user.is_authenticated else pr.requestor
        
        # Create PO from PR
        from procurement.purchase_orders.models import POHeader, POLine
        
        po = POHeader.objects.create(
            pr_header_id=pr.id,
            pr_number=pr.pr_number,
            title=pr.title,
            description=pr.description,
            currency=pr.currency,
            cost_center_code=pr.cost_center.code if pr.cost_center else '',
            cost_center_name=pr.cost_center.name if pr.cost_center else '',
            project_code=pr.project.code if pr.project else '',
            project_name=pr.project.name if pr.project else '',
            created_by=user,
            delivery_address=f"{pr.cost_center.name if pr.cost_center else 'Main Office'}",
            status='DRAFT'
        )
        
        # Copy lines from PR to PO
        for pr_line in pr.lines.all():
            POLine.objects.create(
                po_header=po,
                pr_line_id=pr_line.id,
                line_number=pr_line.line_number,
                item_description=pr_line.item_description,
                specifications=pr_line.specifications,
                catalog_item=pr_line.catalog_item,
                quantity=pr_line.quantity,
                unit_of_measure=pr_line.unit_of_measure,
                unit_price=pr_line.estimated_unit_price,  # Start with estimated price
                need_by_date=pr_line.need_by_date
            )
        
        # Recalculate PO totals now that lines are created
        po.calculate_totals()
        po.save()
        
        # Mark PR as converted
        pr.mark_converted(user)
        
        return Response({
            'status': 'success',
            'message': f'PR {pr.pr_number} converted to PO {po.po_number}',
            'po_number': po.po_number,
            'po_id': po.id,
            'pr': PRHeaderDetailSerializer(pr).data
        })
    
    @action(detail=True, methods=['get'])
    def split_by_vendor(self, request, pk=None):
        """Get PR lines split by vendor."""
        pr = self.get_object()
        
        try:
            vendor_split = pr.split_by_vendor()
            
            # Format response
            result = []
            for supplier_id, data in vendor_split.items():
                supplier = data['supplier']
                lines = data['lines']
                
                result.append({
                    'supplier': {
                        'id': supplier.id if supplier else None,
                        'name': supplier.name if supplier else 'Unassigned',
                        'code': supplier.code if supplier else None,
                    },
                    'lines': PRLineSerializer(lines, many=True).data,
                    'line_count': len(lines),
                    'total_amount': sum(line.get_line_total_with_tax() for line in lines)
                })
            
            return Response(result)
        
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def my_prs(self, request):
        """Get PRs created by current user."""
        if request.user.is_authenticated:
            # Use authenticated user
            prs = self.get_queryset().filter(requestor=request.user)
        else:
            # For non-authenticated requests, allow filtering by requestor_id parameter
            # This is for development/testing. In production, authentication should be required.
            requestor_id = request.query_params.get('requestor_id')
            if requestor_id:
                from django.contrib.auth.models import User
                try:
                    user = User.objects.get(id=requestor_id)
                    prs = self.get_queryset().filter(requestor=user)
                except User.DoesNotExist:
                    prs = self.get_queryset().none()
            else:
                # Return empty queryset if no user specified
                prs = self.get_queryset().none()
        
        serializer = PRHeaderListSerializer(prs, many=True)
        return Response({'results': serializer.data, 'count': prs.count()})
    
    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """Get PRs pending approval."""
        prs = self.get_queryset().filter(status='SUBMITTED')
        serializer = PRHeaderListSerializer(prs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get PR statistics."""
        queryset = self.get_queryset()
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(pr_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(pr_date__lte=end_date)
        
        stats = {
            'total_prs': queryset.count(),
            'by_status': {
                'draft': queryset.filter(status='DRAFT').count(),
                'submitted': queryset.filter(status='SUBMITTED').count(),
                'approved': queryset.filter(status='APPROVED').count(),
                'rejected': queryset.filter(status='REJECTED').count(),
                'converted': queryset.filter(status='CONVERTED').count(),
                'cancelled': queryset.filter(status='CANCELLED').count(),
            },
            'by_priority': {
                'low': queryset.filter(priority='LOW').count(),
                'normal': queryset.filter(priority='NORMAL').count(),
                'high': queryset.filter(priority='HIGH').count(),
                'urgent': queryset.filter(priority='URGENT').count(),
            },
            'total_value': float(
                queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            ),
            'budget_check_pass_rate': (
                queryset.filter(budget_check_passed=True).count() /
                queryset.count() * 100
            ) if queryset.count() > 0 else 0,
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def conversion_summary(self, request, pk=None):
        """
        Get conversion summary for a PR.
        
        Shows how PR lines have been converted to PO lines.
        """
        pr_header = self.get_object()
        summary = PRToPOConversionService.get_pr_conversion_summary(pr_header)
        return Response(summary)
    
    @action(detail=False, methods=['post'])
    def convert_lines_to_po(self, request):
        """
        Convert selected PR lines to a Purchase Order.
        
        Request body:
        {
            "pr_line_selections": [
                {
                    "pr_line_id": 1,
                    "quantity": 10.0,
                    "unit_price": 25.50,
                    "notes": "Optional notes"
                },
                ...
            ],
            "title": "Office Supplies Order - Q4 2024",
            "vendor_name": "ABC Supplier Ltd",
            "vendor_email": "orders@abcsupplier.com",
            "vendor_phone": "+1-555-0100",
            "delivery_date": "2025-12-01",
            "delivery_address": "123 Main St, City, Country",
            "special_instructions": "Handle with care",
            "payment_terms": "NET_30"
        }
        """
        try:
            # Get or create default user if not authenticated
            if not request.user.is_authenticated:
                from django.contrib.auth.models import User
                # Get or create a default system user for testing
                user, created = User.objects.get_or_create(
                    username='system',
                    defaults={
                        'email': 'system@erp.local',
                        'first_name': 'System',
                        'last_name': 'User',
                        'is_staff': False,
                        'is_active': True,
                    }
                )
                created_by = user
            else:
                created_by = request.user
            
            pr_line_selections = request.data.get('pr_line_selections', [])
            title = request.data.get('title', '')
            vendor_name = request.data.get('vendor_name', '')
            vendor_email = request.data.get('vendor_email', '')
            vendor_phone = request.data.get('vendor_phone', '')
            delivery_date = request.data.get('delivery_date')
            delivery_address = request.data.get('delivery_address', '')
            special_instructions = request.data.get('special_instructions', '')
            payment_terms = request.data.get('payment_terms', 'NET_30')
            
            # Validate required fields
            if not title:
                return Response(
                    {'error': 'PO Title is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create PO
            po_header = PRToPOConversionService.convert_pr_lines_to_po(
                pr_line_selections=pr_line_selections,
                title=title,
                vendor_name=vendor_name or 'To be assigned',
                vendor_email=vendor_email,
                vendor_phone=vendor_phone,
                delivery_date=delivery_date,
                delivery_address=delivery_address,
                special_instructions=special_instructions,
                payment_terms=payment_terms,
                created_by=created_by,
            )
            
            # Update PR conversion status
            for selection in pr_line_selections:
                pr_line = PRLine.objects.get(id=selection['pr_line_id'])
                PRToPOConversionService.update_pr_conversion_status(pr_line.pr_header)
            
            from procurement.purchase_orders.serializers import POHeaderDetailSerializer
            serializer = POHeaderDetailSerializer(po_header)
            
            return Response({
                'message': 'PR lines successfully converted to PO',
                'po': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Conversion failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def convertible_lines(self, request):
        """
        Get PR lines that can be converted to PO.
        
        Query params:
        - pr_header_ids: Comma-separated list of PR header IDs (optional)
        """
        pr_header_ids_str = request.query_params.get('pr_header_ids')
        pr_header_ids = None
        
        if pr_header_ids_str:
            try:
                pr_header_ids = [int(id.strip()) for id in pr_header_ids_str.split(',')]
            except ValueError:
                return Response(
                    {'error': 'Invalid pr_header_ids format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        lines_data = PRLineSelectionHelper.prepare_pr_lines_for_selection(pr_header_ids)
        
        return Response({
            'count': len(lines_data),
            'lines': lines_data
        })


class PRLineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PR Line management.
    
    Endpoints:
    - GET /api/requisition/pr-lines/ - List all PR lines
    - POST /api/requisition/pr-lines/ - Create PR line
    - GET /api/requisition/pr-lines/{id}/ - Retrieve PR line
    - PUT/PATCH /api/requisition/pr-lines/{id}/ - Update PR line
    - DELETE /api/requisition/pr-lines/{id}/ - Delete PR line
    - GET /api/requisition/pr-lines/need_catalog/ - Get lines needing catalog items
    """
    
    queryset = PRLine.objects.all()
    serializer_class = PRLineSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'pr_header', 'catalog_item', 'unit_of_measure',
        'suggested_supplier', 'quantity_converted'
    ]
    search_fields = ['item_description', 'specifications', 'notes']
    ordering_fields = ['pr_header', 'line_number', 'need_by_date']
    ordering = ['pr_header', 'line_number']
    
    @action(detail=False, methods=['get'])
    def need_catalog(self, request):
        """Get PR lines that need catalog item assignment."""
        lines = self.get_queryset().filter(
            catalog_item__isnull=True,
            pr_header__status__in=['DRAFT', 'SUBMITTED']
        )
        serializer = self.get_serializer(lines, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_pr_header(self, request):
        """
        Get PR lines grouped by PR header for conversion interface.
        
        Query params:
        - pr_header_id: PR header ID
        - status: Filter by conversion status (NOT_CONVERTED, PARTIALLY_CONVERTED, FULLY_CONVERTED)
        """
        pr_header_id = request.query_params.get('pr_header_id')
        conversion_status = request.query_params.get('status')
        
        queryset = self.get_queryset()
        
        if pr_header_id:
            queryset = queryset.filter(pr_header_id=pr_header_id)
        
        if conversion_status:
            queryset = queryset.filter(conversion_status=conversion_status)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

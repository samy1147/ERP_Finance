"""
API ViewSets for Approval and Budget Control.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    ApprovalWorkflow, ApprovalStep, ApprovalInstance,
    ApprovalStepInstance, ApprovalAction, ApprovalDelegation,
    BudgetAllocation, BudgetCheck
)
from .serializers import (
    ApprovalWorkflowSerializer, ApprovalStepSerializer,
    ApprovalInstanceSerializer, ApprovalStepInstanceSerializer,
    ApprovalActionSerializer, ApprovalDelegationSerializer,
    BudgetAllocationSerializer, BudgetCheckSerializer,
    ApproveActionSerializer, RejectActionSerializer,
    DelegateActionSerializer, BudgetCheckRequestSerializer
)


class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    """ViewSet for Approval Workflows."""
    queryset = ApprovalWorkflow.objects.all()
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'document_type', 'scope']
    search_fields = ['name', 'description']
    ordering = ['name']


class ApprovalInstanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Approval Instances.
    
    Manage document approval processes.
    """
    queryset = ApprovalInstance.objects.all()
    serializer_class = ApprovalInstanceSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'workflow', 'requested_by']
    search_fields = ['notes']
    ordering = ['-requested_at']
    
    @action(detail=False, methods=['get'])
    def my_pending(self, request):
        """Get approvals pending for current user."""
        # For non-authenticated users in development, show all pending approvals
        # In production, this should require authentication
        if not request.user.is_authenticated:
            # Show all active/pending approvals for development
            instances = self.queryset.filter(status__in=['IN_PROGRESS', 'PENDING'])
            serializer = self.get_serializer(instances, many=True)
            return Response(serializer.data)
        
        # Find step instances where user can approve
        pending_steps = ApprovalStepInstance.objects.filter(
            status='ACTIVE'
        )
        
        # Filter to steps where current user is an approver
        user_approvals = []
        for step_inst in pending_steps:
            approvers = step_inst.workflow_step.get_approvers(
                step_inst.approval_instance.content_object
            )
            if request.user in approvers:
                user_approvals.append(step_inst.approval_instance.id)
        
        instances = self.queryset.filter(id__in=user_approvals)
        serializer = self.get_serializer(instances, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel approval instance."""
        instance = self.get_object()
        reason = request.data.get('reason', 'Cancelled by user')
        
        try:
            instance.cancel(request.user, reason)
            return Response({
                'status': 'success',
                'message': 'Approval cancelled',
                'approval': self.get_serializer(instance).data
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ApprovalStepInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Approval Step Instances.
    
    Perform approve/reject actions on steps.
    """
    queryset = ApprovalStepInstance.objects.all()
    serializer_class = ApprovalStepInstanceSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'approval_instance']
    ordering = ['approval_instance', 'workflow_step__sequence']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve this step."""
        step_instance = self.get_object()
        serializer = ApproveActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        comments = serializer.validated_data.get('comments', '')
        
        # For development: use admin user if not authenticated
        from django.contrib.auth.models import User
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        try:
            step_instance.approve(user, comments)
            return Response({
                'status': 'success',
                'message': 'Step approved',
                'step': self.get_serializer(step_instance).data
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject this step."""
        step_instance = self.get_object()
        serializer = RejectActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reason = serializer.validated_data['reason']
        
        # For development: use admin user if not authenticated
        from django.contrib.auth.models import User
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        try:
            step_instance.reject(user, reason)
            return Response({
                'status': 'success',
                'message': 'Step rejected',
                'step': self.get_serializer(step_instance).data
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ApprovalDelegationViewSet(viewsets.ModelViewSet):
    """ViewSet for Approval Delegations."""
    queryset = ApprovalDelegation.objects.all()
    serializer_class = ApprovalDelegationSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active', 'from_user', 'to_user', 'workflow']
    ordering = ['-start_date']
    
    @action(detail=False, methods=['get'])
    def my_delegations(self, request):
        """Get delegations for current user."""
        delegations = self.queryset.filter(
            Q(from_user=request.user) | Q(to_user=request.user)
        )
        serializer = self.get_serializer(delegations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_now(self, request):
        """Get currently active delegations."""
        today = timezone.now().date()
        delegations = self.queryset.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
        serializer = self.get_serializer(delegations, many=True)
        return Response(serializer.data)


class BudgetAllocationViewSet(viewsets.ModelViewSet):
    """ViewSet for Budget Allocations."""
    queryset = BudgetAllocation.objects.all()
    serializer_class = BudgetAllocationSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['entity_type', 'entity_id', 'fiscal_year', 'fiscal_period']
    ordering = ['-fiscal_year', '-fiscal_period']
    
    @action(detail=True, methods=['post'])
    def check_availability(self, request, pk=None):
        """Check budget availability."""
        allocation = self.get_object()
        serializer = BudgetCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        check_type = serializer.validated_data.get('check_type', 'COMMIT')
        
        passed, message = allocation.check_availability(amount, check_type)
        
        return Response({
            'passed': passed,
            'message': message,
            'available_amount': float(allocation.get_available_amount()),
            'utilization_pct': float(allocation.get_utilization_pct())
        })
    
    @action(detail=False, methods=['get'])
    def over_budget(self, request):
        """Get allocations that are over budget."""
        allocations = [a for a in self.queryset.all() if a.is_over_budget()]
        serializer = self.get_serializer(allocations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def at_warning(self, request):
        """Get allocations at warning threshold."""
        allocations = [a for a in self.queryset.all() if a.is_at_warning_threshold()]
        serializer = self.get_serializer(allocations, many=True)
        return Response(serializer.data)


class BudgetCheckViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Budget Checks (read-only history)."""
    queryset = BudgetCheck.objects.all()
    serializer_class = BudgetCheckSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['check_type', 'passed', 'budget_allocation']
    ordering = ['-checked_at']

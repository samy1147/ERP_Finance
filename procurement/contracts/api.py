"""
Contracts API

REST API endpoints for Contracts & Compliance module.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import (
    ClauseLibrary, Contract, ContractClause,
    ContractSLA, ContractPenalty, ContractPenaltyInstance,
    ContractRenewal, ContractAttachment, ContractNote
)
from .serializers import (
    ClauseLibrarySerializer, ContractSerializer, ContractCreateSerializer,
    ContractClauseSerializer, ContractSLASerializer,
    ContractPenaltySerializer, ContractPenaltyInstanceSerializer,
    ContractRenewalSerializer, ContractAttachmentSerializer,
    ContractNoteSerializer, ContractSummarySerializer
)


class ClauseLibraryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Clause Library.
    
    Endpoints:
    - list: Get all clauses
    - retrieve: Get single clause
    - create: Create clause
    - update: Update clause
    - destroy: Delete clause
    """
    
    queryset = ClauseLibrary.objects.all()
    serializer_class = ClauseLibrarySerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_queryset(self):
        """Filter by category or active status."""
        queryset = super().get_queryset()
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(clause_category=category)
        
        is_active = self.request.query_params.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('clause_category', 'clause_code')
    
    def perform_create(self, serializer):
        """Set created_by on creation."""
        serializer.save(created_by=self.request.user)


class ContractViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contracts.
    
    Endpoints:
    - list: Get all contracts
    - retrieve: Get single contract
    - create: Create contract
    - update: Update contract
    - destroy: Delete contract
    - approve: Approve contract (POST)
    - activate: Activate contract (POST)
    - terminate: Terminate contract (POST)
    - renew: Renew contract (POST)
    - send_renewal_reminder: Send renewal reminder (POST)
    - update_status: Update contract status based on dates (POST)
    - summary: Get summary (GET)
    """
    
    queryset = Contract.objects.all().select_related(
        'currency', 'contract_owner', 'legal_reviewer',
        'approved_by', 'created_by', 'updated_by'
    ).prefetch_related('clauses', 'slas', 'penalties', 'attachments', 'notes')
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ContractCreateSerializer
        return ContractSerializer
    
    def get_queryset(self):
        """Filter by type, status, party, or expiry."""
        queryset = super().get_queryset()
        
        contract_type = self.request.query_params.get('contract_type')
        if contract_type:
            queryset = queryset.filter(contract_type=contract_type)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        approval_status = self.request.query_params.get('approval_status')
        if approval_status:
            queryset = queryset.filter(approval_status=approval_status)
        
        # Filter expiring soon
        expiring_soon = self.request.query_params.get('expiring_soon')
        if expiring_soon == 'true':
            queryset = [c for c in queryset if c.is_expiring_soon()]
        
        # Filter by owner
        owner_id = self.request.query_params.get('owner')
        if owner_id:
            queryset = queryset.filter(contract_owner_id=owner_id)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set created_by and updated_by on creation."""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update."""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve contract."""
        contract = self.get_object()
        
        if contract.approval_status not in ['PENDING', 'UNDER_REVIEW']:
            return Response(
                {'error': 'Only pending or under review contracts can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            contract.approve(request.user)
            serializer = self.get_serializer(contract)
            return Response({
                'message': 'Contract approved successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate contract."""
        contract = self.get_object()
        
        if contract.approval_status != 'APPROVED':
            return Response(
                {'error': 'Only approved contracts can be activated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            contract.activate(request.user)
            serializer = self.get_serializer(contract)
            return Response({
                'message': 'Contract activated successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate contract."""
        contract = self.get_object()
        reason = request.data.get('reason', '')
        
        if contract.is_terminated:
            return Response(
                {'error': 'Contract is already terminated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            contract.terminate(request.user, reason)
            serializer = self.get_serializer(contract)
            return Response({
                'message': 'Contract terminated successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew contract (creates new contract)."""
        contract = self.get_object()
        new_expiry_date = request.data.get('new_expiry_date')
        new_value = request.data.get('new_value')
        
        if not new_expiry_date:
            return Response(
                {'error': 'new_expiry_date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_contract = contract.renew(request.user, new_expiry_date, new_value)
            serializer = self.get_serializer(new_contract)
            return Response({
                'message': 'Contract renewed successfully',
                'old_contract_id': contract.id,
                'new_contract_id': new_contract.id,
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def send_renewal_reminder(self, request, pk=None):
        """Mark renewal reminder as sent."""
        contract = self.get_object()
        
        if contract.reminder_sent:
            return Response(
                {'error': 'Renewal reminder already sent'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            contract.reminder_sent = True
            contract.reminder_sent_date = timezone.now().date()
            contract.save()
            
            serializer = self.get_serializer(contract)
            return Response({
                'message': 'Renewal reminder marked as sent',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update contract status based on current dates."""
        contract = self.get_object()
        
        try:
            contract.update_status()
            serializer = self.get_serializer(contract)
            return Response({
                'message': 'Contract status updated',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get contracts summary for dashboard."""
        queryset = self.get_queryset()
        
        # Count SLA compliance
        sla_compliant = 0
        sla_breach = 0
        for contract in queryset:
            slas = contract.slas.all()
            sla_compliant += slas.filter(is_compliant=True).count()
            sla_breach += slas.filter(is_compliant=False).count()
        
        # Calculate total penalties
        total_penalties = ContractPenalty.objects.filter(
            contract__in=queryset
        ).aggregate(total=Sum('total_penalties_applied'))['total'] or 0
        
        summary = {
            'total_contracts': queryset.count(),
            'active_count': queryset.filter(status='ACTIVE').count(),
            'expiring_soon_count': len([c for c in queryset if c.is_expiring_soon()]),
            'expired_count': queryset.filter(status='EXPIRED').count(),
            'draft_count': queryset.filter(status='DRAFT').count(),
            'pending_approval_count': queryset.filter(
                approval_status='PENDING'
            ).count(),
            'total_value': queryset.aggregate(
                total=Sum('total_value')
            )['total'] or 0,
            'sla_compliant_count': sla_compliant,
            'sla_breach_count': sla_breach,
            'total_penalties': total_penalties,
        }
        
        serializer = ContractSummarySerializer(summary)
        return Response(serializer.data)


class ContractSLAViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contract SLAs.
    
    Endpoints:
    - list: Get all SLAs
    - retrieve: Get single SLA
    - create: Create SLA
    - update: Update SLA
    - destroy: Delete SLA
    - record_measurement: Record new measurement (POST)
    """
    
    queryset = ContractSLA.objects.all().select_related('contract')
    serializer_class = ContractSLASerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_queryset(self):
        """Filter by contract or compliance status."""
        queryset = super().get_queryset()
        
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        is_compliant = self.request.query_params.get('is_compliant')
        if is_compliant == 'true':
            queryset = queryset.filter(is_compliant=True)
        elif is_compliant == 'false':
            queryset = queryset.filter(is_compliant=False)
        
        return queryset.order_by('contract', 'sla_name')
    
    @action(detail=True, methods=['post'])
    def record_measurement(self, request, pk=None):
        """Record new SLA measurement."""
        sla = self.get_object()
        value = request.data.get('value')
        
        if value is None:
            return Response(
                {'error': 'value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            sla.record_measurement(float(value))
            serializer = self.get_serializer(sla)
            return Response({
                'message': 'Measurement recorded successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ContractPenaltyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contract Penalties.
    
    Endpoints:
    - list: Get all penalties
    - retrieve: Get single penalty
    - create: Create penalty
    - update: Update penalty
    - destroy: Delete penalty
    - apply_penalty: Apply penalty instance (POST)
    """
    
    queryset = ContractPenalty.objects.all().select_related('contract', 'related_sla')
    serializer_class = ContractPenaltySerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_queryset(self):
        """Filter by contract or penalty type."""
        queryset = super().get_queryset()
        
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        penalty_type = self.request.query_params.get('penalty_type')
        if penalty_type:
            queryset = queryset.filter(penalty_type=penalty_type)
        
        return queryset.order_by('contract', 'penalty_type')
    
    @action(detail=True, methods=['post'])
    def apply_penalty(self, request, pk=None):
        """Apply penalty instance."""
        penalty = self.get_object()
        amount = request.data.get('amount')
        notes = request.data.get('notes', '')
        
        if amount is None:
            return Response(
                {'error': 'amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            instance = penalty.apply_penalty(float(amount), notes)
            instance_serializer = ContractPenaltyInstanceSerializer(instance)
            return Response({
                'message': 'Penalty applied successfully',
                'data': instance_serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ContractRenewalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contract Renewals.
    
    Endpoints:
    - list: Get all renewals
    - retrieve: Get single renewal
    - create: Create renewal
    - update: Update renewal
    - destroy: Delete renewal
    """
    
    queryset = ContractRenewal.objects.all().select_related(
        'contract', 'decision_by', 'renewed_contract'
    )
    serializer_class = ContractRenewalSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_queryset(self):
        """Filter by contract or status."""
        queryset = super().get_queryset()
        
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')


class ContractAttachmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contract Attachments.
    
    Endpoints:
    - list: Get all attachments
    - retrieve: Get single attachment
    - create: Create attachment
    - update: Update attachment
    - destroy: Delete attachment
    """
    
    queryset = ContractAttachment.objects.all().select_related('contract', 'uploaded_by')
    serializer_class = ContractAttachmentSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_queryset(self):
        """Filter by contract or document type."""
        queryset = super().get_queryset()
        
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        document_type = self.request.query_params.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        is_latest = self.request.query_params.get('is_latest')
        if is_latest == 'true':
            queryset = queryset.filter(is_latest=True)
        
        return queryset.order_by('contract', '-version')
    
    def perform_create(self, serializer):
        """Set uploaded_by on creation."""
        serializer.save(uploaded_by=self.request.user)


class ContractNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contract Notes.
    
    Endpoints:
    - list: Get all notes
    - retrieve: Get single note
    - create: Create note
    - update: Update note
    - destroy: Delete note
    """
    
    queryset = ContractNote.objects.all().select_related('contract', 'created_by')
    serializer_class = ContractNoteSerializer
    permission_classes = [AllowAny]  # TODO: Change back to IsAuthenticated in production
    
    def get_queryset(self):
        """Filter by contract or note type."""
        queryset = super().get_queryset()
        
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        note_type = self.request.query_params.get('note_type')
        if note_type:
            queryset = queryset.filter(note_type=note_type)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set created_by on creation."""
        serializer.save(created_by=self.request.user)

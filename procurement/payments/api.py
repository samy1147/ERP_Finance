"""
Payment Integration API

REST API endpoints for Payments & Finance Integration module.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import (
    TaxJurisdiction, TaxRate, TaxComponent,
    APPaymentBatch, APPaymentLine,
    TaxPeriod, CorporateTaxAccrual,
    PaymentRequest
)
from .serializers import (
    TaxJurisdictionSerializer, TaxRateSerializer, TaxComponentSerializer,
    APPaymentBatchSerializer, APPaymentBatchCreateSerializer,
    APPaymentLineSerializer, TaxPeriodSerializer,
    CorporateTaxAccrualSerializer, PaymentSummarySerializer,
    PaymentRequestSerializer, PaymentRequestCreateSerializer,
    PaymentRequestListSerializer
)


class TaxJurisdictionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tax Jurisdictions.
    
    Endpoints:
    - list: Get all jurisdictions
    - retrieve: Get single jurisdiction
    - create: Create jurisdiction
    - update: Update jurisdiction
    - destroy: Delete jurisdiction
    """
    
    queryset = TaxJurisdiction.objects.all().prefetch_related('rates')
    serializer_class = TaxJurisdictionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by country or tax system."""
        queryset = super().get_queryset()
        
        country_code = self.request.query_params.get('country')
        if country_code:
            queryset = queryset.filter(country_code=country_code)
        
        tax_system = self.request.query_params.get('tax_system')
        if tax_system:
            queryset = queryset.filter(tax_system=tax_system)
        
        is_active = self.request.query_params.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('country_code')


class TaxRateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tax Rates.
    
    Endpoints:
    - list: Get all tax rates
    - retrieve: Get single tax rate
    - create: Create tax rate
    - update: Update tax rate
    - destroy: Delete tax rate
    """
    
    queryset = TaxRate.objects.all().select_related('jurisdiction').prefetch_related('components')
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by jurisdiction or rate type."""
        queryset = super().get_queryset()
        
        jurisdiction_id = self.request.query_params.get('jurisdiction')
        if jurisdiction_id:
            queryset = queryset.filter(jurisdiction_id=jurisdiction_id)
        
        rate_type = self.request.query_params.get('rate_type')
        if rate_type:
            queryset = queryset.filter(rate_type=rate_type)
        
        is_active = self.request.query_params.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('jurisdiction', 'rate_code')


class TaxComponentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tax Components.
    
    Endpoints:
    - list: Get all tax components
    - retrieve: Get single component
    - create: Create component
    - update: Update component
    - destroy: Delete component
    """
    
    queryset = TaxComponent.objects.all().select_related('tax_rate')
    serializer_class = TaxComponentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by tax rate."""
        queryset = super().get_queryset()
        
        tax_rate_id = self.request.query_params.get('tax_rate')
        if tax_rate_id:
            queryset = queryset.filter(tax_rate_id=tax_rate_id)
        
        return queryset.order_by('tax_rate', 'component_type')


class APPaymentBatchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AP Payment Batches.
    
    Endpoints:
    - list: Get all batches
    - retrieve: Get single batch
    - create: Create batch
    - update: Update batch
    - destroy: Delete batch
    - submit: Submit for approval (POST)
    - approve: Approve batch (POST)
    - reject: Reject batch (POST)
    - post_to_finance: Post to Finance (POST)
    - reconcile: Mark as reconciled (POST)
    - summary: Get summary (GET)
    """
    
    queryset = APPaymentBatch.objects.all().select_related(
        'bank_account', 'currency', 'journal_entry'
    ).prefetch_related('lines')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return APPaymentBatchCreateSerializer
        return APPaymentBatchSerializer
    
    def get_queryset(self):
        """Filter by status, date, or bank account."""
        queryset = super().get_queryset()
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        bank_account_id = self.request.query_params.get('bank_account')
        if bank_account_id:
            queryset = queryset.filter(bank_account_id=bank_account_id)
        
        is_reconciled = self.request.query_params.get('is_reconciled')
        if is_reconciled == 'true':
            queryset = queryset.filter(is_reconciled=True)
        elif is_reconciled == 'false':
            queryset = queryset.filter(is_reconciled=False)
        
        return queryset.order_by('-batch_date', '-created_at')
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit payment batch for approval."""
        batch = self.get_object()
        
        if batch.status != 'DRAFT':
            return Response(
                {'error': 'Only draft batches can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            batch.submit(request.user)
            serializer = self.get_serializer(batch)
            return Response({
                'message': 'Payment batch submitted successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve payment batch."""
        batch = self.get_object()
        
        if batch.status != 'SUBMITTED':
            return Response(
                {'error': 'Only submitted batches can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            batch.approve(request.user)
            serializer = self.get_serializer(batch)
            return Response({
                'message': 'Payment batch approved successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject payment batch."""
        batch = self.get_object()
        reason = request.data.get('reason', '')
        
        if batch.status in ['POSTED_TO_FINANCE', 'RECONCILED']:
            return Response(
                {'error': 'Cannot reject posted or reconciled batches'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            batch.status = 'DRAFT'
            batch.notes = f"{batch.notes}\n\nREJECTED by {request.user.username}: {reason}".strip()
            batch.save()
            
            serializer = self.get_serializer(batch)
            return Response({
                'message': 'Payment batch rejected',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def post_to_finance(self, request, pk=None):
        """Post payment batch to Finance (create journal entry)."""
        batch = self.get_object()
        
        if batch.status != 'APPROVED':
            return Response(
                {'error': 'Only approved batches can be posted to Finance'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if batch.journal_entry:
            return Response(
                {'error': 'Batch is already posted to Finance'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            journal_entry = batch.post_to_finance(request.user)
            serializer = self.get_serializer(batch)
            return Response({
                'message': 'Posted to Finance successfully',
                'journal_entry_id': journal_entry.id,
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reconcile(self, request, pk=None):
        """Mark payment batch as reconciled."""
        batch = self.get_object()
        
        if batch.status != 'POSTED_TO_FINANCE':
            return Response(
                {'error': 'Only posted batches can be reconciled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if batch.is_reconciled:
            return Response(
                {'error': 'Batch is already reconciled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            batch.reconcile()
            serializer = self.get_serializer(batch)
            return Response({
                'message': 'Payment batch reconciled successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get payment batches summary for dashboard."""
        queryset = self.get_queryset()
        
        summary = {
            'total_batches': queryset.count(),
            'draft_count': queryset.filter(status='DRAFT').count(),
            'submitted_count': queryset.filter(status='SUBMITTED').count(),
            'approved_count': queryset.filter(status='APPROVED').count(),
            'posted_count': queryset.filter(status='POSTED_TO_FINANCE').count(),
            'total_payment_amount': queryset.aggregate(
                total=Sum('total_net_payment')
            )['total'] or 0,
            'pending_approval_count': queryset.filter(status='SUBMITTED').count(),
            'pending_posting_count': queryset.filter(status='APPROVED').count(),
        }
        
        serializer = PaymentSummarySerializer(summary)
        return Response(serializer.data)


class TaxPeriodViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tax Periods.
    
    Endpoints:
    - list: Get all tax periods
    - retrieve: Get single period
    - create: Create period
    - update: Update period
    - destroy: Delete period
    - calculate_tax: Calculate tax amounts (POST)
    - close_period: Close period (POST)
    - file_return: Mark return as filed (POST)
    - record_payment: Record tax payment (POST)
    """
    
    queryset = TaxPeriod.objects.all().select_related('jurisdiction')
    serializer_class = TaxPeriodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by jurisdiction, status, or date range."""
        queryset = super().get_queryset()
        
        jurisdiction_id = self.request.query_params.get('jurisdiction')
        if jurisdiction_id:
            queryset = queryset.filter(jurisdiction_id=jurisdiction_id)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(period_start__year=year)
        
        return queryset.order_by('-period_end')
    
    @action(detail=True, methods=['post'])
    def calculate_tax(self, request, pk=None):
        """Calculate tax amounts from invoices."""
        period = self.get_object()
        
        if period.status != 'OPEN':
            return Response(
                {'error': 'Only open periods can have tax calculated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            period.calculate_tax_amounts()
            serializer = self.get_serializer(period)
            return Response({
                'message': 'Tax amounts calculated successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def close_period(self, request, pk=None):
        """Close tax period."""
        period = self.get_object()
        
        if period.status != 'OPEN':
            return Response(
                {'error': 'Only open periods can be closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            period.close_period()
            serializer = self.get_serializer(period)
            return Response({
                'message': 'Tax period closed successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def file_return(self, request, pk=None):
        """Mark tax return as filed."""
        period = self.get_object()
        filing_date = request.data.get('filing_date', timezone.now().date())
        
        if period.status != 'CLOSED':
            return Response(
                {'error': 'Only closed periods can be filed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            period.file_return(filing_date)
            serializer = self.get_serializer(period)
            return Response({
                'message': 'Tax return filed successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """Record tax payment."""
        period = self.get_object()
        payment_date = request.data.get('payment_date', timezone.now().date())
        payment_reference = request.data.get('payment_reference', '')
        user = request.user
        
        if period.status != 'FILED':
            return Response(
                {'error': 'Only filed periods can have payments recorded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            journal_entry = period.record_payment(payment_date, payment_reference, user)
            serializer = self.get_serializer(period)
            return Response({
                'message': 'Tax payment recorded successfully',
                'journal_entry_id': journal_entry.id,
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CorporateTaxAccrualViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Corporate Tax Accruals.
    
    Endpoints:
    - list: Get all accruals
    - retrieve: Get single accrual
    - create: Create accrual
    - update: Update accrual
    - destroy: Delete accrual
    - post_accrual: Post to Finance (POST)
    """
    
    queryset = CorporateTaxAccrual.objects.all().select_related('journal_entry')
    serializer_class = CorporateTaxAccrualSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by fiscal year, period, or posted status."""
        queryset = super().get_queryset()
        
        fiscal_year = self.request.query_params.get('fiscal_year')
        if fiscal_year:
            queryset = queryset.filter(fiscal_year=fiscal_year)
        
        period_month = self.request.query_params.get('period_month')
        if period_month:
            queryset = queryset.filter(period_month=period_month)
        
        period_quarter = self.request.query_params.get('period_quarter')
        if period_quarter:
            queryset = queryset.filter(period_quarter=period_quarter)
        
        is_posted = self.request.query_params.get('is_posted')
        if is_posted == 'true':
            queryset = queryset.filter(is_posted=True)
        elif is_posted == 'false':
            queryset = queryset.filter(is_posted=False)
        
        return queryset.order_by('-fiscal_year', '-period_month')
    
    @action(detail=True, methods=['post'])
    def post_accrual(self, request, pk=None):
        """Post corporate tax accrual to Finance."""
        accrual = self.get_object()
        
        if accrual.is_posted:
            return Response(
                {'error': 'Accrual is already posted to Finance'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            journal_entry = accrual.post_accrual(request.user)
            serializer = self.get_serializer(accrual)
            return Response({
                'message': 'Corporate tax accrual posted successfully',
                'journal_entry_id': journal_entry.id,
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Payment Requests.
    
    Endpoints:
    - list: Get all payment requests
    - retrieve: Get single payment request
    - create: Create payment request
    - update: Update payment request
    - destroy: Delete payment request
    - submit: Submit for approval
    - approve: Approve payment request
    - reject: Reject payment request
    - schedule: Schedule in payment batch
    - mark_paid: Mark as paid
    - cancel: Cancel payment request
    """
    
    queryset = PaymentRequest.objects.all().select_related(
        'supplier', 'vendor_bill', 'currency', 'payment_batch',
        'created_by', 'approved_by', 'updated_by'
    )
    permission_classes = [AllowAny]  # TODO: Change to IsAuthenticated in production
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PaymentRequestCreateSerializer
        elif self.action == 'list':
            return PaymentRequestListSerializer
        return PaymentRequestSerializer
    
    def get_queryset(self):
        """Filter payment requests by various criteria."""
        queryset = super().get_queryset()
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by supplier
        supplier_id = self.request.query_params.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        
        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(requested_payment_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(requested_payment_date__lte=to_date)
        
        # Filter pending approval
        pending_approval = self.request.query_params.get('pending_approval')
        if pending_approval == 'true':
            queryset = queryset.filter(status='SUBMITTED')
        
        return queryset.order_by('-requested_date', '-created_at')
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit payment request for approval."""
        payment_request = self.get_object()
        
        try:
            payment_request.submit(request.user)
            serializer = self.get_serializer(payment_request)
            return Response({
                'message': 'Payment request submitted successfully',
                'data': serializer.data
            })
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve payment request."""
        payment_request = self.get_object()
        
        try:
            payment_request.approve(request.user)
            serializer = self.get_serializer(payment_request)
            return Response({
                'message': 'Payment request approved successfully',
                'data': serializer.data
            })
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject payment request."""
        payment_request = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            payment_request.reject(request.user, reason)
            serializer = self.get_serializer(payment_request)
            return Response({
                'message': 'Payment request rejected',
                'data': serializer.data
            })
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        """Schedule payment request in a payment batch."""
        payment_request = self.get_object()
        payment_batch_id = request.data.get('payment_batch_id')
        scheduled_date = request.data.get('scheduled_date')
        
        if not payment_batch_id:
            return Response(
                {'error': 'payment_batch_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .models import APPaymentBatch
            payment_batch = APPaymentBatch.objects.get(id=payment_batch_id)
            payment_request.schedule(payment_batch, scheduled_date)
            serializer = self.get_serializer(payment_request)
            return Response({
                'message': 'Payment request scheduled successfully',
                'data': serializer.data
            })
        except APPaymentBatch.DoesNotExist:
            return Response(
                {'error': 'Payment batch not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark payment request as paid."""
        payment_request = self.get_object()
        paid_date = request.data.get('paid_date')
        reference = request.data.get('payment_reference')
        
        try:
            payment_request.mark_paid(paid_date, reference)
            serializer = self.get_serializer(payment_request)
            return Response({
                'message': 'Payment request marked as paid',
                'data': serializer.data
            })
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel payment request."""
        payment_request = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            payment_request.cancel(request.user, reason)
            serializer = self.get_serializer(payment_request)
            return Response({
                'message': 'Payment request cancelled',
                'data': serializer.data
            })
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for payment requests."""
        from django.db.models import Sum, Count, Q
        
        queryset = self.get_queryset()
        
        # Count by status
        status_counts = {
            'total': queryset.count(),
            'draft': queryset.filter(status='DRAFT').count(),
            'submitted': queryset.filter(status='SUBMITTED').count(),
            'approved': queryset.filter(status='APPROVED').count(),
            'scheduled': queryset.filter(status='SCHEDULED').count(),
            'paid': queryset.filter(status='PAID').count(),
            'rejected': queryset.filter(status='REJECTED').count(),
            'cancelled': queryset.filter(status='CANCELLED').count(),
        }
        
        # Sum by status
        status_amounts = queryset.values('status').annotate(
            total_amount=Sum('payment_amount')
        )
        
        # Pending approval
        pending_approval = queryset.filter(status='SUBMITTED').aggregate(
            count=Count('id'),
            total_amount=Sum('payment_amount')
        )
        
        # Due soon (next 7 days)
        from datetime import timedelta
        from django.utils import timezone
        due_soon_date = timezone.now().date() + timedelta(days=7)
        due_soon = queryset.filter(
            status__in=['APPROVED', 'SCHEDULED'],
            requested_payment_date__lte=due_soon_date
        ).aggregate(
            count=Count('id'),
            total_amount=Sum('payment_amount')
        )
        
        return Response({
            'status_counts': status_counts,
            'status_amounts': list(status_amounts),
            'pending_approval': pending_approval,
            'due_soon': due_soon,
        })


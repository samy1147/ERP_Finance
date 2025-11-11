"""
Period Management API Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta

from .models import FiscalYear, FiscalPeriod, PeriodStatus
from .serializers import (
    FiscalYearSerializer,
    FiscalPeriodSerializer,
    FiscalPeriodListSerializer,
    PeriodStatusSerializer,
    GeneratePeriodsSerializer,
    CreateAdjustmentPeriodSerializer
)


class FiscalYearViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Fiscal Year management.
    
    list: Get all fiscal years
    retrieve: Get a specific fiscal year
    create: Create a new fiscal year
    update: Update fiscal year
    destroy: Delete fiscal year (only if no periods exist)
    """
    queryset = FiscalYear.objects.all()
    serializer_class = FiscalYearSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['year', 'status']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def close_year(self, request, pk=None):
        """Close a fiscal year and all its periods"""
        fiscal_year = self.get_object()
        
        if fiscal_year.status == 'CLOSED':
            return Response(
                {'error': 'Fiscal year is already closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fiscal_year.close_year(user=request.user)
        
        return Response({
            'message': f'Fiscal year {fiscal_year.year} closed successfully',
            'year': FiscalYearSerializer(fiscal_year).data
        })
    
    @action(detail=True, methods=['post'])
    def open_year(self, request, pk=None):
        """Reopen a closed fiscal year"""
        fiscal_year = self.get_object()
        
        if fiscal_year.status == 'OPEN':
            return Response(
                {'error': 'Fiscal year is already open'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fiscal_year.open_year(user=request.user)
        
        return Response({
            'message': f'Fiscal year {fiscal_year.year} reopened successfully',
            'year': FiscalYearSerializer(fiscal_year).data
        })
    
    @action(detail=True, methods=['post'])
    def generate_periods(self, request, pk=None):
        """Generate periods for the fiscal year"""
        fiscal_year = self.get_object()
        period_type = request.data.get('period_type', 'MONTHLY')
        
        if period_type not in ['MONTHLY', 'QUARTERLY', 'YEARLY']:
            return Response(
                {'error': 'Invalid period_type. Must be MONTHLY, QUARTERLY, or YEARLY'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if periods already exist
        existing_periods = fiscal_year.periods.filter(period_type=period_type)
        if existing_periods.exists():
            return Response(
                {'error': f'{period_type} periods already exist for this fiscal year'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_periods = []
        
        if period_type == 'MONTHLY':
            # Generate 12 monthly periods
            current_date = fiscal_year.start_date
            for i in range(1, 13):
                # Calculate period end date
                if i < 12:
                    next_month = current_date + relativedelta(months=1)
                    end_date = next_month - relativedelta(days=1)
                else:
                    end_date = fiscal_year.end_date
                
                period = FiscalPeriod.objects.create(
                    fiscal_year=fiscal_year,
                    period_number=i,
                    period_code=f"{fiscal_year.year}-{i:02d}",
                    period_name=current_date.strftime("%B %Y"),
                    period_type='MONTHLY',
                    start_date=current_date,
                    end_date=end_date,
                    status='OPEN',
                    created_by=request.user
                )
                created_periods.append(period)
                current_date = next_month
        
        elif period_type == 'QUARTERLY':
            # Generate 4 quarterly periods
            quarters = [
                (1, 'Q1', 1, 3),
                (2, 'Q2', 4, 6),
                (3, 'Q3', 7, 9),
                (4, 'Q4', 10, 12),
            ]
            
            for q_num, q_name, start_month, end_month in quarters:
                # Calculate quarter dates
                start_date = fiscal_year.start_date + relativedelta(months=start_month-1)
                if q_num < 4:
                    end_date = fiscal_year.start_date + relativedelta(months=end_month) - relativedelta(days=1)
                else:
                    end_date = fiscal_year.end_date
                
                period = FiscalPeriod.objects.create(
                    fiscal_year=fiscal_year,
                    period_number=q_num,
                    period_code=f"{fiscal_year.year}-{q_name}",
                    period_name=f"{q_name} {fiscal_year.year}",
                    period_type='QUARTERLY',
                    start_date=start_date,
                    end_date=end_date,
                    status='OPEN',
                    created_by=request.user
                )
                created_periods.append(period)
        
        elif period_type == 'YEARLY':
            # Generate 1 yearly period
            period = FiscalPeriod.objects.create(
                fiscal_year=fiscal_year,
                period_number=1,
                period_code=f"{fiscal_year.year}",
                period_name=f"Year {fiscal_year.year}",
                period_type='YEARLY',
                start_date=fiscal_year.start_date,
                end_date=fiscal_year.end_date,
                status='OPEN',
                created_by=request.user
            )
            created_periods.append(period)
        
        return Response({
            'message': f'Successfully generated {len(created_periods)} {period_type.lower()} periods',
            'count': len(created_periods),
            'periods': FiscalPeriodListSerializer(created_periods, many=True).data
        })


class FiscalPeriodViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Fiscal Period management.
    
    list: Get all fiscal periods
    retrieve: Get a specific period
    create: Create a new period (typically for adjustment periods)
    update: Update period
    destroy: Delete period (only if no transactions exist)
    """
    queryset = FiscalPeriod.objects.select_related('fiscal_year', 'created_by')
    serializer_class = FiscalPeriodSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['fiscal_year', 'period_type', 'status', 'period_number']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FiscalPeriodListSerializer
        return FiscalPeriodSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def close_period(self, request, pk=None):
        """Close a fiscal period"""
        period = self.get_object()
        reason = request.data.get('reason', '')
        
        if period.status == 'CLOSED':
            return Response(
                {'error': 'Period is already closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        period.close_period(user=request.user, reason=reason)
        
        return Response({
            'message': f'Period {period.period_code} closed successfully',
            'period': FiscalPeriodSerializer(period).data
        })
    
    @action(detail=True, methods=['post'])
    def open_period(self, request, pk=None):
        """Open/Reopen a fiscal period"""
        period = self.get_object()
        reason = request.data.get('reason', '')
        
        if period.status == 'OPEN':
            return Response(
                {'error': 'Period is already open'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            period.open_period(user=request.user, reason=reason)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': f'Period {period.period_code} opened successfully',
            'period': FiscalPeriodSerializer(period).data
        })
    
    @action(detail=False, methods=['get'])
    def current_period(self, request):
        """Get the current open period for today's date"""
        period_type = request.query_params.get('period_type', 'MONTHLY')
        
        period = FiscalPeriod.get_current_period(period_type=period_type)
        
        if not period:
            return Response(
                {'error': f'No open {period_type.lower()} period found for current date'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(FiscalPeriodSerializer(period).data)
    
    @action(detail=False, methods=['post'])
    def validate_date(self, request):
        """Validate if a transaction can be posted on a given date"""
        transaction_date_str = request.data.get('transaction_date')
        period_id = request.data.get('period_id')
        
        if not transaction_date_str:
            return Response(
                {'error': 'transaction_date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_valid, period, error_message = FiscalPeriod.validate_transaction_date(
            transaction_date, period_id
        )
        
        if is_valid:
            return Response({
                'valid': True,
                'period': FiscalPeriodSerializer(period).data,
                'message': f'Transaction can be posted to period {period.period_code}'
            })
        else:
            return Response({
                'valid': False,
                'error': error_message,
                'period': FiscalPeriodSerializer(period).data if period else None
            })


class PeriodStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for Period Status History (read-only).
    
    list: Get all status changes
    retrieve: Get a specific status change
    """
    queryset = PeriodStatus.objects.select_related('fiscal_period', 'changed_by')
    serializer_class = PeriodStatusSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['fiscal_period', 'old_status', 'new_status']

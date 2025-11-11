"""
Period Management Serializers
"""

from rest_framework import serializers
from .models import FiscalYear, FiscalPeriod, PeriodStatus
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user display in audit fields"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class FiscalYearSerializer(serializers.ModelSerializer):
    """Serializer for Fiscal Year"""
    created_by = UserSerializer(read_only=True)
    period_count = serializers.SerializerMethodField()
    open_period_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FiscalYear
        fields = [
            'id', 'year', 'start_date', 'end_date', 'status', 'description',
            'period_count', 'open_period_count',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
    
    def get_period_count(self, obj):
        return obj.periods.count()
    
    def get_open_period_count(self, obj):
        return obj.periods.filter(status='OPEN').count()


class PeriodStatusSerializer(serializers.ModelSerializer):
    """Serializer for Period Status History"""
    changed_by = UserSerializer(read_only=True)
    period_code = serializers.CharField(source='fiscal_period.period_code', read_only=True)
    
    class Meta:
        model = PeriodStatus
        fields = [
            'id', 'fiscal_period', 'period_code', 'old_status', 'new_status',
            'changed_at', 'changed_by', 'change_reason'
        ]
        read_only_fields = ['changed_at', 'changed_by']


class FiscalPeriodSerializer(serializers.ModelSerializer):
    """Serializer for Fiscal Period"""
    created_by = UserSerializer(read_only=True)
    fiscal_year_display = serializers.CharField(source='fiscal_year.year', read_only=True)
    status_history = PeriodStatusSerializer(many=True, read_only=True)
    transaction_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FiscalPeriod
        fields = [
            'id', 'fiscal_year', 'fiscal_year_display', 'period_number', 'period_code',
            'period_name', 'period_type', 'start_date', 'end_date', 'status',
            'is_adjustment_period', 'transaction_count', 'status_history',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
    
    def get_transaction_count(self, obj):
        """
        Count transactions in this period across all modules.
        This will be populated once we add period FK to transaction models.
        """
        count = 0
        
        # Finance journal entries
        if hasattr(obj, 'journal_entries'):
            count += obj.journal_entries.count()
        
        # AR invoices
        if hasattr(obj, 'ar_invoices'):
            count += obj.ar_invoices.count()
        
        # AP invoices
        if hasattr(obj, 'ap_invoices'):
            count += obj.ap_invoices.count()
        
        # Asset depreciation schedules
        if hasattr(obj, 'depreciation_schedules'):
            count += obj.depreciation_schedules.count()
        
        return count


class FiscalPeriodListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for period lists"""
    fiscal_year_display = serializers.CharField(source='fiscal_year.year', read_only=True)
    
    class Meta:
        model = FiscalPeriod
        fields = [
            'id', 'fiscal_year', 'fiscal_year_display', 'period_number', 'period_code',
            'period_name', 'period_type', 'start_date', 'end_date', 'status',
            'is_adjustment_period'
        ]


class GeneratePeriodsSerializer(serializers.Serializer):
    """Serializer for generating periods for a fiscal year"""
    fiscal_year_id = serializers.IntegerField()
    period_type = serializers.ChoiceField(
        choices=['MONTHLY', 'QUARTERLY', 'YEARLY'],
        default='MONTHLY'
    )
    
    def validate_fiscal_year_id(self, value):
        try:
            FiscalYear.objects.get(id=value)
        except FiscalYear.DoesNotExist:
            raise serializers.ValidationError("Fiscal year not found")
        return value


class CreateAdjustmentPeriodSerializer(serializers.Serializer):
    """Serializer for creating an adjustment period"""
    fiscal_year_id = serializers.IntegerField()
    period_name = serializers.CharField(max_length=100)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    def validate_fiscal_year_id(self, value):
        try:
            FiscalYear.objects.get(id=value)
        except FiscalYear.DoesNotExist:
            raise serializers.ValidationError("Fiscal year not found")
        return value
    
    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("Start date must be before end date")
        return data

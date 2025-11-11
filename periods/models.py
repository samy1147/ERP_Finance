"""
Fiscal Period Management Models

This module defines the core models for managing fiscal periods:
1. FiscalYear - Represents a fiscal/calendar year
2. FiscalPeriod - Individual periods (monthly, quarterly, yearly, adjustment)
3. PeriodStatus - Historical tracking of period status changes
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class FiscalYear(models.Model):
    """
    Represents a fiscal year for financial reporting.
    Typically aligns with calendar year but can be customized.
    """
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]
    
    year = models.IntegerField(unique=True, help_text="Fiscal year (e.g., 2025)")
    start_date = models.DateField(help_text="First day of fiscal year")
    end_date = models.DateField(help_text="Last day of fiscal year")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    description = models.TextField(blank=True, help_text="Additional notes about this fiscal year")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_fiscal_years')
    
    class Meta:
        db_table = 'periods_fiscal_year'
        ordering = ['-year']
        verbose_name = 'Fiscal Year'
        verbose_name_plural = 'Fiscal Years'
        indexes = [
            models.Index(fields=['year']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"FY {self.year} ({self.start_date} to {self.end_date})"
    
    def clean(self):
        """Validate fiscal year data"""
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("Start date must be before end date")
            
            # Check for overlapping fiscal years
            overlapping = FiscalYear.objects.filter(
                models.Q(start_date__lte=self.end_date, end_date__gte=self.start_date)
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError(f"Fiscal year overlaps with existing year: {overlapping.first()}")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def close_year(self, user=None):
        """Close the fiscal year and all its periods"""
        self.status = 'CLOSED'
        self.save()
        
        # Close all periods in this year
        for period in self.periods.all():
            period.close_period(user=user)
    
    def open_year(self, user=None):
        """Reopen the fiscal year"""
        self.status = 'OPEN'
        self.save()


class FiscalPeriod(models.Model):
    """
    Represents a fiscal period within a fiscal year.
    Can be monthly, quarterly, yearly, or adjustment period.
    """
    
    PERIOD_TYPE_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
        ('ADJUSTMENT', 'Adjustment'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]
    
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='periods')
    period_number = models.IntegerField(help_text="Period number within fiscal year (1-12 for monthly)")
    period_code = models.CharField(max_length=20, unique=True, help_text="Unique code (e.g., 2025-01, 2025-Q1)")
    period_name = models.CharField(max_length=100, help_text="Display name (e.g., January 2025)")
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES, default='MONTHLY')
    
    start_date = models.DateField(help_text="First day of period")
    end_date = models.DateField(help_text="Last day of period")
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    is_adjustment_period = models.BooleanField(default=False, help_text="True for year-end adjustment periods")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_periods')
    
    class Meta:
        db_table = 'periods_fiscal_period'
        ordering = ['fiscal_year__year', 'period_number']
        verbose_name = 'Fiscal Period'
        verbose_name_plural = 'Fiscal Periods'
        unique_together = [('fiscal_year', 'period_number', 'period_type')]
        indexes = [
            models.Index(fields=['fiscal_year', 'period_number']),
            models.Index(fields=['period_code']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.period_code} - {self.period_name} ({self.status})"
    
    def clean(self):
        """Validate period data"""
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("Start date must be before end date")
            
            # Ensure period is within fiscal year bounds
            if self.fiscal_year:
                if self.start_date < self.fiscal_year.start_date:
                    raise ValidationError(f"Period start date must be on or after fiscal year start ({self.fiscal_year.start_date})")
                if self.end_date > self.fiscal_year.end_date:
                    raise ValidationError(f"Period end date must be on or before fiscal year end ({self.fiscal_year.end_date})")
            
            # Check for overlapping periods in same fiscal year
            overlapping = FiscalPeriod.objects.filter(
                fiscal_year=self.fiscal_year,
                period_type=self.period_type,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError(f"Period overlaps with existing period: {overlapping.first()}")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def close_period(self, user=None, reason=''):
        """Close the period and create status history"""
        if self.status == 'CLOSED':
            return
        
        old_status = self.status
        self.status = 'CLOSED'
        self.save()
        
        # Create status history record
        PeriodStatus.objects.create(
            fiscal_period=self,
            old_status=old_status,
            new_status='CLOSED',
            changed_by=user,
            change_reason=reason or f"Period closed on {timezone.now().strftime('%Y-%m-%d')}"
        )
    
    def open_period(self, user=None, reason=''):
        """Open/Reopen the period and create status history"""
        if self.status == 'OPEN':
            return
        
        # Check if fiscal year is open
        if self.fiscal_year.status == 'CLOSED':
            raise ValidationError("Cannot open period in a closed fiscal year")
        
        old_status = self.status
        self.status = 'OPEN'
        self.save()
        
        # Create status history record
        PeriodStatus.objects.create(
            fiscal_period=self,
            old_status=old_status,
            new_status='OPEN',
            changed_by=user,
            change_reason=reason or f"Period opened on {timezone.now().strftime('%Y-%m-%d')}"
        )
    
    @classmethod
    def get_current_period(cls, period_type='MONTHLY'):
        """Get the current open period for today's date"""
        today = timezone.now().date()
        try:
            return cls.objects.get(
                period_type=period_type,
                status='OPEN',
                start_date__lte=today,
                end_date__gte=today
            )
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            # Return the first one if multiple exist
            return cls.objects.filter(
                period_type=period_type,
                status='OPEN',
                start_date__lte=today,
                end_date__gte=today
            ).first()
    
    @classmethod
    def validate_transaction_date(cls, transaction_date, period_id=None):
        """
        Validate if a transaction can be posted on the given date.
        Returns (is_valid, period, error_message)
        """
        if period_id:
            try:
                period = cls.objects.get(id=period_id)
                if period.status != 'OPEN':
                    return False, period, f"Period {period.period_code} is closed"
                if not (period.start_date <= transaction_date <= period.end_date):
                    return False, period, f"Transaction date {transaction_date} is outside period range"
                return True, period, None
            except cls.DoesNotExist:
                return False, None, "Period not found"
        else:
            # Auto-detect period from transaction date
            periods = cls.objects.filter(
                start_date__lte=transaction_date,
                end_date__gte=transaction_date,
                status='OPEN'
            )
            if not periods.exists():
                return False, None, f"No open period found for date {transaction_date}"
            return True, periods.first(), None


class PeriodStatus(models.Model):
    """
    Historical tracking of period status changes.
    Provides audit trail for period open/close operations.
    """
    
    fiscal_period = models.ForeignKey(FiscalPeriod, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=10)
    new_status = models.CharField(max_length=10)
    
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='period_status_changes')
    change_reason = models.TextField(blank=True, help_text="Reason for status change")
    
    class Meta:
        db_table = 'periods_period_status'
        ordering = ['-changed_at']
        verbose_name = 'Period Status History'
        verbose_name_plural = 'Period Status Histories'
        indexes = [
            models.Index(fields=['fiscal_period', '-changed_at']),
        ]
    
    def __str__(self):
        return f"{self.fiscal_period.period_code}: {self.old_status} → {self.new_status} at {self.changed_at}"

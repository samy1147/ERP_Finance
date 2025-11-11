"""
Admin Configuration for Period Management
"""

from django.contrib import admin
from .models import FiscalYear, FiscalPeriod, PeriodStatus


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ['year', 'start_date', 'end_date', 'status', 'created_at', 'created_by']
    list_filter = ['status', 'year']
    search_fields = ['year', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('year', 'start_date', 'end_date', 'status')
        }),
        ('Additional Info', {
            'fields': ('description',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FiscalPeriod)
class FiscalPeriodAdmin(admin.ModelAdmin):
    list_display = ['period_code', 'period_name', 'fiscal_year', 'period_type', 
                    'start_date', 'end_date', 'status', 'is_adjustment_period']
    list_filter = ['fiscal_year', 'period_type', 'status', 'is_adjustment_period']
    search_fields = ['period_code', 'period_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Period Information', {
            'fields': ('fiscal_year', 'period_number', 'period_code', 'period_name', 'period_type')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('status', 'is_adjustment_period')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PeriodStatus)
class PeriodStatusAdmin(admin.ModelAdmin):
    list_display = ['fiscal_period', 'old_status', 'new_status', 'changed_at', 'changed_by']
    list_filter = ['old_status', 'new_status', 'changed_at']
    search_fields = ['fiscal_period__period_code', 'change_reason']
    readonly_fields = ['fiscal_period', 'old_status', 'new_status', 'changed_at', 'changed_by', 'change_reason']
    
    def has_add_permission(self, request):
        # Status changes should only be created through period open/close actions
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of audit trail
        return False

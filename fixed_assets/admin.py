from django.contrib import admin
from .models import (
    AssetCategory, AssetLocation, Asset, AssetTransfer,
    DepreciationSchedule, AssetMaintenance, AssetDocument, AssetConfiguration
)


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'depreciation_method', 'useful_life_years', 'is_active']
    list_filter = ['depreciation_method', 'is_active']
    search_fields = ['code', 'name']


@admin.register(AssetLocation)
class AssetLocationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'city', 'country', 'custodian', 'is_active']
    list_filter = ['is_active', 'country']
    search_fields = ['code', 'name', 'city']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_number', 'name', 'category', 'location', 'status', 'acquisition_cost', 'net_book_value']
    list_filter = ['status', 'category', 'location', 'depreciation_method']
    search_fields = ['asset_number', 'name', 'serial_number']
    readonly_fields = ['total_depreciation', 'net_book_value', 'last_depreciation_date']


@admin.register(AssetTransfer)
class AssetTransferAdmin(admin.ModelAdmin):
    list_display = ['asset', 'transfer_date', 'from_location', 'to_location', 'is_completed', 'approved_by']
    list_filter = ['is_completed', 'transfer_date']
    search_fields = ['asset__asset_number', 'asset__name']


@admin.register(DepreciationSchedule)
class DepreciationScheduleAdmin(admin.ModelAdmin):
    list_display = ['asset', 'period_date', 'depreciation_amount', 'accumulated_depreciation', 'is_posted']
    list_filter = ['is_posted', 'period_date']
    search_fields = ['asset__asset_number', 'asset__name']
    readonly_fields = ['posted_at', 'journal_entry']


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['asset', 'maintenance_date', 'maintenance_type', 'cost', 'is_capitalized']
    list_filter = ['maintenance_type', 'is_capitalized', 'maintenance_date']
    search_fields = ['asset__asset_number', 'asset__name', 'description']


@admin.register(AssetDocument)
class AssetDocumentAdmin(admin.ModelAdmin):
    list_display = ['asset', 'document_type', 'title', 'document_date', 'uploaded_by']
    list_filter = ['document_type', 'document_date']
    search_fields = ['asset__asset_number', 'asset__name', 'title']


@admin.register(AssetConfiguration)
class AssetConfigurationAdmin(admin.ModelAdmin):
    list_display = ['minimum_capitalization_amount', 'auto_generate_asset_number', 'asset_number_prefix', 'updated_at', 'updated_by']
    readonly_fields = ['updated_at', 'updated_by']
    
    def has_add_permission(self, request):
        # Only allow one configuration record
        return not AssetConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the configuration
        return False

# catalog/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    UnitOfMeasure, CatalogCategory, CatalogItem, SupplierPriceTier,
    FrameworkAgreement, FrameworkItem, CallOffOrder, CallOffLine
)


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'uom_type', 'base_uom', 'conversion_factor', 'is_active']
    list_filter = ['uom_type', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'uom_type')
        }),
        ('Conversion', {
            'fields': ('base_uom', 'conversion_factor'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(CatalogCategory)
class CatalogCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'level', 'get_full_path_display', 'is_active']
    list_filter = ['level', 'is_active']
    search_fields = ['code', 'name', 'full_path']
    ordering = ['code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'parent')
        }),
        ('UNSPSC Codes', {
            'fields': ('unspsc_segment', 'unspsc_family', 'unspsc_class', 'unspsc_commodity'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ['level', 'full_path']
    
    def get_full_path_display(self, obj):
        return obj.full_path
    get_full_path_display.short_description = 'Full Path'


class SupplierPriceTierInline(admin.TabularInline):
    model = SupplierPriceTier
    extra = 1
    fields = ['supplier', 'min_quantity', 'unit_price', 'currency', 'discount_percent', 
              'valid_from', 'valid_to', 'is_active']
    autocomplete_fields = ['supplier', 'currency']


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'item_type', 'list_price', 'currency', 
                   'unit_of_measure', 'preferred_supplier', 'is_active', 'is_purchasable']
    list_filter = ['item_type', 'category', 'is_active', 'is_purchasable', 'is_restricted']
    search_fields = ['sku', 'item_code', 'name', 'manufacturer', 'manufacturer_part_number']
    ordering = ['sku']
    
    autocomplete_fields = ['category', 'unit_of_measure', 'currency', 'preferred_supplier']
    
    fieldsets = (
        ('Identification', {
            'fields': ('sku', 'item_code', 'name', 'short_description', 'long_description')
        }),
        ('Classification', {
            'fields': ('category', 'item_type', 'unit_of_measure')
        }),
        ('Product Details', {
            'fields': ('manufacturer', 'manufacturer_part_number', 'brand', 'model_number')
        }),
        ('Specifications', {
            'fields': ('specifications', 'attributes'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('image_url', 'datasheet_url', 'additional_images'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('list_price', 'currency')
        }),
        ('Supplier', {
            'fields': ('preferred_supplier',)
        }),
        ('Procurement Settings', {
            'fields': ('minimum_order_quantity', 'order_multiple', 'lead_time_days')
        }),
        ('Tax & Accounting', {
            'fields': ('is_taxable', 'tax_category', 'gl_account_code'),
            'classes': ('collapse',)
        }),
        ('Status & Control', {
            'fields': ('is_active', 'is_purchasable', 'is_restricted', 'restriction_notes')
        }),
    )
    
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    
    inlines = [SupplierPriceTierInline]
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SupplierPriceTier)
class SupplierPriceTierAdmin(admin.ModelAdmin):
    list_display = ['catalog_item', 'supplier', 'min_quantity', 'unit_price', 'currency',
                   'discount_percent', 'valid_from', 'valid_to', 'is_valid_display', 'is_active']
    list_filter = ['is_active', 'supplier', 'valid_from']
    search_fields = ['catalog_item__sku', 'catalog_item__name', 'supplier__name']
    ordering = ['catalog_item', 'supplier', 'min_quantity']
    
    autocomplete_fields = ['catalog_item', 'supplier', 'currency']
    
    fieldsets = (
        ('Item & Supplier', {
            'fields': ('catalog_item', 'supplier')
        }),
        ('Pricing', {
            'fields': ('min_quantity', 'unit_price', 'currency', 'discount_percent')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('Delivery & Reference', {
            'fields': ('lead_time_days', 'supplier_item_code', 'supplier_quote_reference')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def is_valid_display(self, obj):
        if obj.is_valid_today():
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Expired</span>')
    is_valid_display.short_description = 'Validity Status'


class FrameworkItemInline(admin.TabularInline):
    model = FrameworkItem
    extra = 1
    fields = ['line_number', 'catalog_item', 'unit_price', 'currency', 
              'minimum_order_quantity', 'maximum_order_quantity', 
              'total_quantity_limit', 'quantity_ordered', 'is_active']
    readonly_fields = ['quantity_ordered', 'quantity_received', 'total_value_ordered']
    autocomplete_fields = ['catalog_item', 'currency']


@admin.register(FrameworkAgreement)
class FrameworkAgreementAdmin(admin.ModelAdmin):
    list_display = ['agreement_number', 'title', 'supplier', 'agreement_type', 'status',
                   'start_date', 'end_date', 'get_utilization_display', 'is_active_display']
    list_filter = ['agreement_type', 'status', 'start_date', 'end_date']
    search_fields = ['agreement_number', 'title', 'supplier__name']
    ordering = ['-start_date']
    
    autocomplete_fields = ['supplier', 'currency', 'approved_by', 'created_by']
    
    fieldsets = (
        ('Agreement Information', {
            'fields': ('agreement_number', 'title', 'description', 'agreement_type')
        }),
        ('Parties', {
            'fields': ('supplier', 'department', 'buyer_name')
        }),
        ('Validity Period', {
            'fields': ('start_date', 'end_date', 'auto_renew', 'renewal_notice_days')
        }),
        ('Financial Limits', {
            'fields': ('currency', 'total_contract_value', 'annual_value_limit', 
                      'per_order_limit', 'total_committed', 'total_spent')
        }),
        ('Terms & Conditions', {
            'fields': ('payment_terms', 'delivery_terms', 'warranty_terms', 'special_terms')
        }),
        ('Pricing', {
            'fields': ('pricing_type', 'discount_percent', 'allow_price_adjustment',
                      'price_adjustment_frequency', 'price_adjustment_method')
        }),
        ('Documents', {
            'fields': ('contract_document_url', 'attachments'),
            'classes': ('collapse',)
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_date')
        }),
        ('Termination', {
            'fields': ('termination_date', 'termination_reason'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('notify_on_expiry', 'notify_on_limit_reached', 'limit_warning_percent'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['agreement_number', 'total_committed', 'total_spent', 
                      'approved_date', 'created_by', 'created_at', 'updated_at']
    
    inlines = [FrameworkItemInline]
    
    actions = ['activate_frameworks', 'suspend_frameworks']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_utilization_display(self, obj):
        utilization = obj.get_utilization_percent()
        if utilization >= 90:
            color = 'red'
        elif utilization >= 75:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, utilization
        )
    get_utilization_display.short_description = 'Utilization'
    
    def is_active_display(self, obj):
        if obj.is_active():
            return format_html('<span style="color: green;">✓ Active</span>')
        elif obj.is_expiring_soon(30):
            return format_html('<span style="color: orange;">⚠ Expiring Soon</span>')
        return format_html('<span style="color: gray;">✗ Inactive</span>')
    is_active_display.short_description = 'Active Status'
    
    def activate_frameworks(self, request, queryset):
        count = 0
        for framework in queryset:
            if framework.status == 'PENDING_APPROVAL':
                framework.activate(request.user)
                count += 1
        self.message_user(request, f'{count} framework(s) activated successfully.')
    activate_frameworks.short_description = 'Activate selected frameworks'
    
    def suspend_frameworks(self, request, queryset):
        count = queryset.filter(status='ACTIVE').update(status='SUSPENDED')
        self.message_user(request, f'{count} framework(s) suspended successfully.')
    suspend_frameworks.short_description = 'Suspend selected frameworks'


@admin.register(FrameworkItem)
class FrameworkItemAdmin(admin.ModelAdmin):
    list_display = ['framework', 'line_number', 'catalog_item', 'unit_price', 'currency',
                   'quantity_ordered', 'get_remaining_quantity_display', 'is_active']
    list_filter = ['framework', 'is_active']
    search_fields = ['framework__agreement_number', 'catalog_item__sku', 'catalog_item__name']
    ordering = ['framework', 'line_number']
    
    autocomplete_fields = ['framework', 'catalog_item', 'currency']
    
    fieldsets = (
        ('Framework & Item', {
            'fields': ('framework', 'catalog_item', 'line_number')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'currency')
        }),
        ('Quantity Limits', {
            'fields': ('minimum_order_quantity', 'maximum_order_quantity', 'total_quantity_limit')
        }),
        ('Usage Tracking', {
            'fields': ('quantity_ordered', 'quantity_received', 'total_value_ordered')
        }),
        ('Delivery', {
            'fields': ('lead_time_days', 'delivery_location')
        }),
        ('Status', {
            'fields': ('is_active', 'notes')
        }),
    )
    
    readonly_fields = ['quantity_ordered', 'quantity_received', 'total_value_ordered']
    
    def get_remaining_quantity_display(self, obj):
        remaining = obj.get_remaining_quantity()
        if remaining is None:
            return 'Unlimited'
        if remaining <= 0:
            return format_html('<span style="color: red;">0 (Limit Reached)</span>')
        return format_html('{:.3f}', remaining)
    get_remaining_quantity_display.short_description = 'Remaining'


class CallOffLineInline(admin.TabularInline):
    model = CallOffLine
    extra = 1
    fields = ['line_number', 'catalog_item', 'framework_item', 'quantity', 
              'unit_price', 'line_total', 'requested_delivery_date', 
              'quantity_received', 'is_received']
    readonly_fields = ['line_total']
    autocomplete_fields = ['catalog_item', 'framework_item']


@admin.register(CallOffOrder)
class CallOffOrderAdmin(admin.ModelAdmin):
    list_display = ['calloff_number', 'framework', 'order_date', 'status', 
                   'total_amount', 'currency', 'requested_by', 'approved_by']
    list_filter = ['status', 'order_date', 'framework']
    search_fields = ['calloff_number', 'framework__agreement_number', 'internal_reference']
    ordering = ['-order_date', '-calloff_number']
    
    autocomplete_fields = ['framework', 'currency', 'requested_by', 
                          'approved_by', 'created_by']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('calloff_number', 'framework', 'order_date')
        }),
        ('Delivery', {
            'fields': ('requested_delivery_date', 'delivery_location', 'actual_delivery_date',
                      'delivery_notes')
        }),
        ('Requester', {
            'fields': ('requested_by', 'department', 'cost_center')
        }),
        ('Financial', {
            'fields': ('currency', 'subtotal', 'tax_amount', 'total_amount')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_date')
        }),
        ('Reference', {
            'fields': ('supplier_po_number', 'internal_reference')
        }),
        ('Notes', {
            'fields': ('notes', 'special_instructions'),
            'classes': ('collapse',)
        }),
        ('Cancellation', {
            'fields': ('cancelled_date', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['calloff_number', 'subtotal', 'tax_amount', 'total_amount',
                      'approved_date', 'cancelled_date', 'created_by', 'created_at', 'updated_at']
    
    inlines = [CallOffLineInline]
    
    actions = ['submit_calloffs', 'approve_calloffs', 'send_to_supplier']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def submit_calloffs(self, request, queryset):
        count = 0
        for calloff in queryset:
            if calloff.submit():
                count += 1
        self.message_user(request, f'{count} call-off(s) submitted successfully.')
    submit_calloffs.short_description = 'Submit selected call-offs'
    
    def approve_calloffs(self, request, queryset):
        count = 0
        for calloff in queryset:
            if calloff.approve(request.user):
                count += 1
        self.message_user(request, f'{count} call-off(s) approved successfully.')
    approve_calloffs.short_description = 'Approve selected call-offs'
    
    def send_to_supplier(self, request, queryset):
        count = 0
        for calloff in queryset:
            if calloff.send_to_supplier():
                count += 1
        self.message_user(request, f'{count} call-off(s) sent to supplier successfully.')
    send_to_supplier.short_description = 'Send to supplier'


@admin.register(CallOffLine)
class CallOffLineAdmin(admin.ModelAdmin):
    list_display = ['calloff', 'line_number', 'catalog_item', 'quantity', 
                   'unit_price', 'line_total', 'quantity_received', 'is_received']
    list_filter = ['is_received', 'calloff__status']
    search_fields = ['calloff__calloff_number', 'catalog_item__sku', 'description']
    ordering = ['calloff', 'line_number']
    
    autocomplete_fields = ['calloff', 'framework_item', 'catalog_item']
    
    fieldsets = (
        ('Call-Off', {
            'fields': ('calloff', 'framework_item', 'line_number')
        }),
        ('Item Details', {
            'fields': ('catalog_item', 'description')
        }),
        ('Quantity & Pricing', {
            'fields': ('quantity', 'unit_price', 'line_total')
        }),
        ('Delivery', {
            'fields': ('requested_delivery_date', 'actual_delivery_date', 
                      'quantity_received', 'is_received')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ['line_total']

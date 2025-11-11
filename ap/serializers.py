# ap/serializers.py
from rest_framework import serializers
from .models import (
    Supplier, VendorContact, VendorDocument, VendorPerformanceRecord, 
    VendorOnboardingChecklist, APInvoice, APPayment
)


class VendorContactSerializer(serializers.ModelSerializer):
    """Serializer for Vendor Contact"""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = VendorContact
        fields = [
            'id', 'vendor', 'first_name', 'last_name', 'full_name', 'title',
            'email', 'phone', 'mobile', 'contact_type', 'is_primary', 'is_active',
            'receives_invoices', 'receives_payments', 'receives_orders', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class VendorDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Vendor Document"""
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = VendorDocument
        fields = [
            'id', 'vendor', 'document_type', 'document_type_display', 'document_name', 
            'document_number', 'file', 'file_url', 'issue_date', 'expiry_date',
            'is_verified', 'verified_by', 'verified_date', 'is_required_for_onboarding',
            'is_submitted', 'is_expired', 'days_until_expiry', 'notes',
            'created_at', 'updated_at', 'uploaded_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_expired', 'days_until_expiry']


class VendorPerformanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for Vendor Performance Record"""
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    
    class Meta:
        model = VendorPerformanceRecord
        fields = [
            'id', 'vendor', 'vendor_name', 'period_start', 'period_end',
            'total_orders', 'on_time_deliveries', 'late_deliveries', 'avg_delivery_delay_days',
            'total_items_received', 'rejected_items', 'defect_rate',
            'price_changes', 'price_increase_count', 'avg_price_variance',
            'total_invoices', 'disputed_invoices', 'invoice_accuracy_rate',
            'delivery_score', 'quality_score', 'price_score', 'overall_score',
            'risk_level', 'risk_level_display', 'risk_notes', 'notes',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'defect_rate', 'invoice_accuracy_rate',
            'delivery_score', 'quality_score', 'price_score', 'overall_score'
        ]


class VendorOnboardingChecklistSerializer(serializers.ModelSerializer):
    """Serializer for Vendor Onboarding Checklist"""
    
    class Meta:
        model = VendorOnboardingChecklist
        fields = [
            'id', 'vendor', 'item_name', 'description', 'is_completed',
            'completed_date', 'completed_by', 'is_required', 'priority',
            'related_document', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SupplierListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    vendor_category_display = serializers.CharField(source='get_vendor_category_display', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    status = serializers.SerializerMethodField()
    can_transact = serializers.ReadOnlyField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'code', 'name', 'email', 'phone', 'country', 
            'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'currency', 'currency_code',
            'vendor_category', 'vendor_category_display', 'is_active', 'is_preferred',
            'is_blacklisted', 'is_on_hold', 'onboarding_status', 'performance_score',
            'status', 'can_transact'
        ]
    
    def get_status(self, obj):
        """Get human-readable status"""
        if obj.is_blacklisted:
            return 'BLACKLISTED'
        if obj.is_on_hold:
            return 'ON_HOLD'
        if not obj.is_active:
            return 'INACTIVE'
        return 'ACTIVE'


class SupplierDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with all fields and nested data"""
    vendor_category_display = serializers.CharField(source='get_vendor_category_display', read_only=True)
    onboarding_status_display = serializers.CharField(source='get_onboarding_status_display', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    can_transact = serializers.ReadOnlyField()
    
    # Nested relationships
    contacts = VendorContactSerializer(many=True, read_only=True)
    documents = VendorDocumentSerializer(many=True, read_only=True)
    performance_records = VendorPerformanceRecordSerializer(many=True, read_only=True)
    onboarding_checklist = VendorOnboardingChecklistSerializer(many=True, read_only=True)
    
    # Statistics
    total_invoices = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            # Basic Info
            'id', 'code', 'name', 'legal_name', 'email', 'phone', 'website',
            
            # Address
            'country', 'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            
            # Tax & Registration
            'vat_number', 'tax_id', 'trade_license_number', 'trade_license_expiry',
            
            # Financial
            'currency', 'currency_code', 'payment_terms_days', 'credit_limit',
            
            # Bank Details
            'bank_name', 'bank_account_name', 'bank_account_number', 'bank_iban',
            'bank_swift', 'bank_routing_number',
            
            # Classification & Status
            'vendor_category', 'vendor_category_display', 'is_preferred', 'is_active',
            'is_blacklisted', 'is_on_hold', 'hold_reason', 'blacklist_reason',
            
            # Onboarding
            'onboarding_status', 'onboarding_status_display', 'onboarding_completed_date',
            'compliance_verified', 'compliance_verified_date',
            
            # Performance
            'performance_score', 'quality_score', 'delivery_score', 'price_score',
            
            # Metadata
            'notes', 'created_at', 'updated_at', 'created_by', 'can_transact',
            
            # Nested relationships
            'contacts', 'documents', 'performance_records', 'onboarding_checklist',
            
            # Statistics
            'total_invoices', 'total_paid', 'outstanding_balance'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'performance_score', 'quality_score',
            'delivery_score', 'price_score', 'can_transact'
        ]
    
    def get_total_invoices(self, obj):
        """Get total number of invoices for this vendor"""
        return APInvoice.objects.filter(supplier=obj).count()
    
    def get_total_paid(self, obj):
        """Get total amount paid to this vendor"""
        from decimal import Decimal
        from django.db.models import Sum
        
        total = APPayment.objects.filter(supplier=obj).aggregate(
            total=Sum('total_amount')
        )['total']
        return total or Decimal('0.00')
    
    def get_outstanding_balance(self, obj):
        """Get outstanding balance for this vendor"""
        from decimal import Decimal
        
        balance = Decimal('0.00')
        invoices = APInvoice.objects.filter(
            supplier=obj,
            is_posted=True,
            is_cancelled=False,
            payment_status__in=['UNPAID', 'PARTIALLY_PAID']
        )
        
        for invoice in invoices:
            balance += invoice.outstanding_amount()
        
        return balance


class SupplierCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating suppliers"""
    
    class Meta:
        model = Supplier
        fields = [
            'code', 'name', 'legal_name', 'email', 'phone', 'website',
            'country', 'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'vat_number', 'tax_id', 'trade_license_number', 'trade_license_expiry',
            'currency', 'payment_terms_days', 'credit_limit',
            'bank_name', 'bank_account_name', 'bank_account_number', 'bank_iban',
            'bank_swift', 'bank_routing_number',
            'vendor_category', 'is_preferred', 'is_active',
            'is_blacklisted', 'is_on_hold', 'hold_reason', 'blacklist_reason',
            'onboarding_status', 'notes'
        ]
    
    def validate(self, data):
        """Custom validation"""
        # If blacklisting, ensure reason is provided
        if data.get('is_blacklisted') and not data.get('blacklist_reason'):
            raise serializers.ValidationError({
                'blacklist_reason': 'Blacklist reason is required when blacklisting a vendor.'
            })
        
        # If putting on hold, ensure reason is provided
        if data.get('is_on_hold') and not data.get('hold_reason'):
            raise serializers.ValidationError({
                'hold_reason': 'Hold reason is required when putting a vendor on hold.'
            })
        
        # Blacklisted vendors should be inactive
        if data.get('is_blacklisted') and data.get('is_active'):
            data['is_active'] = False
        
        return data

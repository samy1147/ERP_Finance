"""
Payment Integration Serializers

Serializers for Payments & Finance Integration module.
"""

from rest_framework import serializers
from .models import (
    TaxJurisdiction, TaxRate, TaxComponent,
    APPaymentBatch, APPaymentLine,
    TaxPeriod, CorporateTaxAccrual,
    PaymentRequest
)


class TaxComponentSerializer(serializers.ModelSerializer):
    """Serializer for tax components (GST split)."""
    
    component_type_display = serializers.CharField(source='get_component_type_display', read_only=True)
    
    class Meta:
        model = TaxComponent
        fields = [
            'id', 'tax_rate', 'component_type', 'component_type_display',
            'component_percentage', 'gl_account', 'is_active'
        ]
        read_only_fields = ['id']


class TaxRateSerializer(serializers.ModelSerializer):
    """Serializer for tax rates."""
    
    components = TaxComponentSerializer(many=True, read_only=True)
    jurisdiction_name = serializers.CharField(source='jurisdiction.country_name', read_only=True)
    rate_type_display = serializers.CharField(source='get_rate_type_display', read_only=True)
    
    class Meta:
        model = TaxRate
        fields = [
            'id', 'jurisdiction', 'jurisdiction_name',
            'rate_code', 'rate_name', 'rate_type', 'rate_type_display',
            'rate_percentage', 'is_default', 'is_active',
            'effective_from', 'effective_to',
            'tax_payable_account', 'tax_receivable_account',
            'description', 'components'
        ]
        read_only_fields = ['id']


class TaxJurisdictionSerializer(serializers.ModelSerializer):
    """Serializer for tax jurisdictions."""
    
    rates = TaxRateSerializer(many=True, read_only=True)
    tax_system_display = serializers.CharField(source='get_tax_system_display', read_only=True)
    tax_period_display = serializers.CharField(source='get_tax_period_display', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    active_rates_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TaxJurisdiction
        fields = [
            'id', 'country_code', 'country_name',
            'tax_system', 'tax_system_display',
            'standard_rate', 'tax_authority_name', 'tax_registration_number',
            'tax_period', 'tax_period_display',
            'currency', 'currency_code',
            'is_active', 'rates', 'active_rates_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_active_rates_count(self, obj):
        """Count of active tax rates."""
        return obj.rates.filter(is_active=True).count()


class APPaymentLineSerializer(serializers.ModelSerializer):
    """Serializer for payment lines."""
    
    invoice_number = serializers.CharField(source='ap_invoice.invoice_number', read_only=True)
    supplier_name = serializers.CharField(source='ap_invoice.supplier.name', read_only=True)
    
    class Meta:
        model = APPaymentLine
        fields = [
            'id', 'payment_batch', 'line_number',
            'ap_invoice', 'invoice_number', 'supplier_name',
            'payment_amount', 'withholding_tax_rate', 'withholding_tax_amount',
            'withholding_tax_account', 'discount_taken', 'net_payment_amount',
            'is_paid', 'paid_date', 'notes'
        ]
        read_only_fields = ['id', 'net_payment_amount', 'is_paid', 'paid_date']


class APPaymentBatchSerializer(serializers.ModelSerializer):
    """Serializer for payment batches."""
    
    lines = APPaymentLineSerializer(many=True, read_only=True)
    bank_account_name = serializers.CharField(source='bank_account.account_name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_summary = serializers.SerializerMethodField()
    supplier_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = APPaymentBatch
        fields = [
            'id', 'batch_number', 'batch_date', 'payment_date', 'payment_method',
            'bank_account', 'bank_account_name',
            'currency', 'currency_code',
            'status', 'status_display',
            'total_amount', 'payment_count', 
            'is_reconciled', 'reconciled_date',
            'journal_entry', 'notes',
            'created_by', 'created_at',
            'submitted_by', 'submitted_date',
            'approved_by', 'approved_date',
            'posted_to_finance_by', 'posted_to_finance_date',
            'lines', 'payment_summary', 'supplier_breakdown'
        ]
        read_only_fields = [
            'id', 'batch_number', 'total_amount', 'payment_count', 'journal_entry',
            'created_by', 'created_at', 'submitted_by', 'submitted_date',
            'approved_by', 'approved_date', 'posted_to_finance_by', 'posted_to_finance_date'
        ]
    
    def get_payment_summary(self, obj):
        """Get payment totals summary."""
        return {
            'total_amount': float(obj.total_amount or 0),
            'payment_count': obj.payment_count
        }
    
    def get_supplier_breakdown(self, obj):
        """Get supplier-wise breakdown."""
        from django.db.models import Count, Sum
        breakdown = obj.lines.values(
            'ap_invoice__supplier__name'
        ).annotate(
            count=Count('id'),
            total=Sum('net_payment_amount')
        ).order_by('-total')
        
        return [
            {
                'supplier': item['ap_invoice__supplier__name'],
                'payment_count': item['count'],
                'total_amount': float(item['total'])
            }
            for item in breakdown
        ]


class APPaymentBatchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payment batches with lines."""
    
    lines = APPaymentLineSerializer(many=True)
    
    class Meta:
        model = APPaymentBatch
        fields = [
            'batch_date', 'payment_date', 'payment_method', 'bank_account',
            'currency', 'notes', 'lines'
        ]
    
    def create(self, validated_data):
        """Create payment batch with lines."""
        lines_data = validated_data.pop('lines')
        payment_batch = APPaymentBatch.objects.create(
            created_by=self.context['request'].user,
            **validated_data
        )
        
        for line_data in lines_data:
            APPaymentLine.objects.create(
                payment_batch=payment_batch,
                **line_data
            )
        
        payment_batch.recalculate_totals()
        return payment_batch


class TaxPeriodSerializer(serializers.ModelSerializer):
    """Serializer for tax periods."""
    
    jurisdiction_name = serializers.CharField(source='jurisdiction.country_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tax_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = TaxPeriod
        fields = [
            'id', 'jurisdiction', 'jurisdiction_name',
            'period_start', 'period_end', 'period_name',
            'status', 'status_display',
            'output_tax', 'input_tax', 'net_tax_payable',
            'filing_due_date', 'filed_date', 'filed_by',
            'payment_date', 'payment_reference',
            'journal_entry', 'notes',
            'created_at', 'updated_at',
            'tax_breakdown'
        ]
        read_only_fields = [
            'id', 'output_tax', 'input_tax', 'net_tax_payable',
            'filed_by', 'journal_entry', 'created_at', 'updated_at'
        ]
    
    def get_tax_breakdown(self, obj):
        """Get tax breakdown details."""
        return {
            'output_tax': float(obj.output_tax or 0),
            'input_tax': float(obj.input_tax or 0),
            'net_payable': float(obj.net_tax_payable or 0)
        }


class CorporateTaxAccrualSerializer(serializers.ModelSerializer):
    """Serializer for corporate tax accruals."""
    
    tax_calculation = serializers.SerializerMethodField()
    
    class Meta:
        model = CorporateTaxAccrual
        fields = [
            'id', 'fiscal_year', 'period_month', 'period_quarter',
            'revenue', 'expenses', 'profit_before_tax',
            'tax_rate', 'tax_amount', 
            'cumulative_profit_before_tax', 'cumulative_tax_amount',
            'tax_expense_account', 'tax_payable_account',
            'is_posted', 'journal_entry', 'posted_by', 'posted_date',
            'created_at', 'updated_at', 'tax_calculation'
        ]
        read_only_fields = [
            'id', 'profit_before_tax', 'tax_amount',
            'cumulative_profit_before_tax', 'cumulative_tax_amount', 
            'journal_entry', 'posted_by', 'posted_date',
            'created_at', 'updated_at'
        ]
    
    def get_tax_calculation(self, obj):
        """Get tax calculation details."""
        return {
            'revenue': float(obj.revenue),
            'expenses': float(obj.expenses),
            'profit_before_tax': float(obj.profit_before_tax),
            'tax_rate': float(obj.tax_rate),
            'tax_amount': float(obj.tax_amount),
            'cumulative_ytd': float(obj.cumulative_tax_ytd)
        }


class PaymentSummarySerializer(serializers.Serializer):
    """Summary serializer for dashboard."""
    
    total_batches = serializers.IntegerField()
    draft_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    approved_count = serializers.IntegerField()
    posted_count = serializers.IntegerField()
    total_payment_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_approval_count = serializers.IntegerField()
    pending_posting_count = serializers.IntegerField()


class PaymentRequestSerializer(serializers.ModelSerializer):
    """Serializer for Payment Requests."""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    vendor_bill_number = serializers.CharField(source='vendor_bill.bill_number', read_only=True)
    payment_batch_number = serializers.CharField(source='payment_batch.batch_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = PaymentRequest
        fields = [
            'id', 'request_number', 'supplier', 'supplier_name',
            'vendor_bill', 'vendor_bill_number',
            'payment_method', 'payment_method_display',
            'requested_date', 'requested_payment_date',
            'currency', 'currency_code', 'payment_amount',
            'exchange_rate', 'base_currency_amount',
            'status', 'status_display', 'priority', 'priority_display',
            'approval_required', 'approved_by', 'approved_by_name', 'approved_date',
            'payment_batch', 'payment_batch_number', 'scheduled_date', 'paid_date',
            'payment_reference', 'purpose', 'notes', 'attachment_url',
            'created_at', 'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'request_number', 'base_currency_amount',
            'approved_by', 'approved_date', 'scheduled_date', 'paid_date',
            'created_at', 'updated_at', 'created_by'
        ]


class PaymentRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Payment Requests."""
    
    class Meta:
        model = PaymentRequest
        fields = [
            'supplier', 'vendor_bill', 'payment_method',
            'requested_payment_date', 'currency', 'payment_amount',
            'exchange_rate', 'priority', 'approval_required',
            'purpose', 'notes', 'attachment_url'
        ]
    
    def validate(self, data):
        """Validate payment request data."""
        # If vendor_bill is provided, ensure supplier matches
        if data.get('vendor_bill') and data.get('supplier'):
            if data['vendor_bill'].supplier != data['supplier']:
                raise serializers.ValidationError({
                    'supplier': 'Supplier must match the vendor bill supplier'
                })
        
        # Validate requested payment date is not in the past
        from django.utils import timezone
        if data.get('requested_payment_date'):
            if data['requested_payment_date'] < timezone.now().date():
                raise serializers.ValidationError({
                    'requested_payment_date': 'Requested payment date cannot be in the past'
                })
        
        # Validate amount is positive
        if data.get('payment_amount') and data['payment_amount'] <= 0:
            raise serializers.ValidationError({
                'payment_amount': 'Payment amount must be greater than zero'
            })
        
        return data
    
    def create(self, validated_data):
        """Create payment request with auto-generated number."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class PaymentRequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing payment requests."""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = PaymentRequest
        fields = [
            'id', 'request_number', 'supplier_name',
            'requested_payment_date', 'currency_code', 'payment_amount',
            'status', 'status_display', 'priority', 'priority_display',
            'approved_date', 'paid_date', 'created_at'
        ]


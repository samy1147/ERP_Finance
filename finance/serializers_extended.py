"""
Serializers for Payment Allocations and Invoice Approvals
"""
from rest_framework import serializers
from decimal import Decimal
from ar.models import ARPayment, ARPaymentAllocation, ARInvoice, Customer
from ap.models import APPayment, APPaymentAllocation, APInvoice, Supplier
from finance.models import InvoiceApproval
from core.models import Currency


# ============================================================================
# AR PAYMENT ALLOCATION SERIALIZERS
# ============================================================================

class ARPaymentAllocationSerializer(serializers.ModelSerializer):
    """Serializer for AR payment allocations"""
    invoice_number = serializers.CharField(source='invoice.number', read_only=True)
    invoice_total = serializers.SerializerMethodField()
    invoice_outstanding = serializers.SerializerMethodField()
    
    class Meta:
        model = ARPaymentAllocation
        fields = ['id', 'invoice', 'invoice_number', 'invoice_total', 
                 'invoice_outstanding', 'amount', 'memo', 'created_at']
        read_only_fields = ['created_at']
    
    def get_invoice_total(self, obj):
        return float(obj.invoice.calculate_total())
    
    def get_invoice_outstanding(self, obj):
        return float(obj.invoice.outstanding_amount())
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


class ARPaymentSerializer(serializers.ModelSerializer):
    """Serializer for AR payments with allocations"""
    allocations = ARPaymentAllocationSerializer(many=True, required=False)
    customer_name = serializers.SerializerMethodField()
    currency_code = serializers.SerializerMethodField()
    allocated_amount = serializers.SerializerMethodField()
    unallocated_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = ARPayment
        fields = ['id', 'customer', 'customer_name', 'reference', 'date', 
                 'total_amount', 'currency', 'currency_code', 'memo', 
                 'bank_account', 'posted_at', 'reconciled', 'reconciliation_ref',
                 'reconciled_at', 'gl_journal', 'payment_fx_rate',
                 'allocations', 'allocated_amount', 'unallocated_amount']
        read_only_fields = ['posted_at', 'reconciled_at', 'gl_journal', 
                           'allocated_amount', 'unallocated_amount']
    
    def create(self, validated_data):
        allocations_data = validated_data.pop('allocations', [])
        payment = ARPayment.objects.create(**validated_data)
        
        # Create allocations
        for allocation_data in allocations_data:
            ARPaymentAllocation.objects.create(payment=payment, **allocation_data)
        
        return payment
    
    def update(self, instance, validated_data):
        allocations_data = validated_data.pop('allocations', None)
        
        # Update payment fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update allocations if provided
        if allocations_data is not None:
            # Clear existing allocations
            instance.allocations.all().delete()
            # Create new allocations
            for allocation_data in allocations_data:
                ARPaymentAllocation.objects.create(payment=instance, **allocation_data)
        
        return instance
    
    def get_customer_name(self, obj):
        """Return customer name, handling None"""
        return obj.customer.name if obj.customer else None
    
    def get_currency_code(self, obj):
        """Return currency code, handling None"""
        return obj.currency.code if obj.currency else None
    
    def get_allocated_amount(self, obj):
        """Return total allocated amount"""
        try:
            return float(obj.allocated_amount())
        except:
            return 0.0
    
    def get_unallocated_amount(self, obj):
        """Return unallocated amount"""
        try:
            return float(obj.unallocated_amount())
        except:
            return float(obj.total_amount or 0)
    
    def validate(self, data):
        # Validate total allocation doesn't exceed payment amount
        if 'allocations' in data and 'total_amount' in data:
            total_allocated = sum(a['amount'] for a in data['allocations'])
            if total_allocated > data['total_amount']:
                raise serializers.ValidationError(
                    f"Total allocated amount ({total_allocated}) exceeds payment amount ({data['total_amount']})"
                )
        return data


# ============================================================================
# AP PAYMENT ALLOCATION SERIALIZERS
# ============================================================================

class APPaymentAllocationSerializer(serializers.ModelSerializer):
    """Serializer for AP payment allocations"""
    invoice_number = serializers.CharField(source='invoice.number', read_only=True)
    invoice_total = serializers.SerializerMethodField()
    invoice_outstanding = serializers.SerializerMethodField()
    
    class Meta:
        model = APPaymentAllocation
        fields = ['id', 'invoice', 'invoice_number', 'invoice_total', 
                 'invoice_outstanding', 'amount', 'memo', 'created_at']
        read_only_fields = ['created_at']
    
    def get_invoice_total(self, obj):
        return float(obj.invoice.calculate_total())
    
    def get_invoice_outstanding(self, obj):
        return float(obj.invoice.outstanding_amount())
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


class APPaymentSerializer(serializers.ModelSerializer):
    """Serializer for AP payments with allocations"""
    allocations = APPaymentAllocationSerializer(many=True, required=False)
    supplier_name = serializers.SerializerMethodField()
    currency_code = serializers.SerializerMethodField()
    allocated_amount = serializers.SerializerMethodField()
    unallocated_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = APPayment
        fields = ['id', 'supplier', 'supplier_name', 'reference', 'date', 
                 'total_amount', 'currency', 'currency_code', 'memo', 
                 'bank_account', 'posted_at', 'reconciled', 'reconciliation_ref',
                 'reconciled_at', 'gl_journal', 'payment_fx_rate',
                 'allocations', 'allocated_amount', 'unallocated_amount']
        read_only_fields = ['posted_at', 'reconciled_at', 'gl_journal', 
                           'allocated_amount', 'unallocated_amount']
    
    def create(self, validated_data):
        allocations_data = validated_data.pop('allocations', [])
        payment = APPayment.objects.create(**validated_data)
        
        # Create allocations
        for allocation_data in allocations_data:
            APPaymentAllocation.objects.create(payment=payment, **allocation_data)
        
        return payment
    
    def update(self, instance, validated_data):
        allocations_data = validated_data.pop('allocations', None)
        
        # Update payment fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update allocations if provided
        if allocations_data is not None:
            # Clear existing allocations
            instance.allocations.all().delete()
            # Create new allocations
            for allocation_data in allocations_data:
                APPaymentAllocation.objects.create(payment=instance, **allocation_data)
        
        return instance
    
    def get_supplier_name(self, obj):
        """Return supplier name, handling None"""
        return obj.supplier.name if obj.supplier else None
    
    def get_currency_code(self, obj):
        """Return currency code, handling None"""
        return obj.currency.code if obj.currency else None
    
    def get_allocated_amount(self, obj):
        """Return total allocated amount"""
        try:
            return float(obj.allocated_amount())
        except:
            return 0.0
    
    def get_unallocated_amount(self, obj):
        """Return unallocated amount"""
        try:
            return float(obj.unallocated_amount())
        except:
            return float(obj.total_amount or 0)
    
    def validate(self, data):
        # Validate total allocation doesn't exceed payment amount
        if 'allocations' in data and 'total_amount' in data:
            total_allocated = sum(a['amount'] for a in data['allocations'])
            if total_allocated > data['total_amount']:
                raise serializers.ValidationError(
                    f"Total allocated amount ({total_allocated}) exceeds payment amount ({data['total_amount']})"
                )
        return data


# ============================================================================
# INVOICE APPROVAL SERIALIZERS
# ============================================================================

class InvoiceApprovalSerializer(serializers.ModelSerializer):
    """Serializer for invoice approvals"""
    
    class Meta:
        model = InvoiceApproval
        fields = ['id', 'invoice_type', 'invoice_id', 'status', 
                 'submitted_by', 'submitted_at', 'approver', 'approved_at', 
                 'rejected_at', 'comments', 'approval_level']
        read_only_fields = ['submitted_at', 'approved_at', 'rejected_at']
    
    def validate(self, data):
        # Validate status transitions
        if self.instance:
            current_status = self.instance.status
            new_status = data.get('status', current_status)
            
            # Can't go from APPROVED/REJECTED back to PENDING
            if current_status in ['APPROVED', 'REJECTED'] and new_status == 'PENDING_APPROVAL':
                raise serializers.ValidationError(
                    "Cannot change status from approved/rejected back to pending"
                )
        
        # Require comments for rejection
        if data.get('status') == 'REJECTED' and not data.get('comments'):
            raise serializers.ValidationError(
                "Comments are required when rejecting an invoice"
            )
        
        return data

"""
Serializers for Payment Allocations and Invoice Approvals
"""
from rest_framework import serializers
from decimal import Decimal
from ar.models import ARPayment, ARPaymentAllocation, ARInvoice, Customer
from ap.models import APPayment, APPaymentAllocation, APInvoice, Supplier
from finance.models import InvoiceApproval, JournalLine, JournalLineSegment, JournalEntry
from core.models import Currency


# ============================================================================
# JOURNAL LINE SERIALIZERS FOR GL DISTRIBUTION DISPLAY
# ============================================================================

class JournalLineSegmentDisplaySerializer(serializers.ModelSerializer):
    """Serializer for displaying journal line segments"""
    segment_code = serializers.CharField(source='segment.code', read_only=True)
    segment_name = serializers.CharField(source='segment.alias', read_only=True)
    segment_type_name = serializers.CharField(source='segment.segment_type.segment_type', read_only=True)
    
    class Meta:
        model = JournalLineSegment
        fields = ['id', 'segment_type', 'segment_type_name', 'segment', 'segment_code', 'segment_name']


class JournalLineDisplaySerializer(serializers.ModelSerializer):
    """Serializer for displaying journal lines with segments"""
    segments = JournalLineSegmentDisplaySerializer(many=True, read_only=True)
    line_type = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    
    class Meta:
        model = JournalLine
        fields = ['id', 'debit', 'credit', 'description', 'line_type', 'amount', 'segments']
    
    def get_line_type(self, obj):
        """Return DEBIT or CREDIT based on which is non-zero"""
        if obj.debit and obj.debit > 0:
            return 'DEBIT'
        elif obj.credit and obj.credit > 0:
            return 'CREDIT'
        return 'DEBIT'
    
    def get_amount(self, obj):
        """Return the non-zero amount"""
        if obj.debit and obj.debit > 0:
            return str(obj.debit)
        elif obj.credit and obj.credit > 0:
            return str(obj.credit)
        return '0.00'


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
    """Serializer for AR payments with allocations and GL lines"""
    allocations = ARPaymentAllocationSerializer(many=True, required=False)
    gl_lines = serializers.ListField(child=serializers.DictField(), required=False, write_only=True)
    gl_lines_display = serializers.SerializerMethodField(read_only=True)
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
                 'allocations', 'allocated_amount', 'unallocated_amount', 'gl_lines', 'gl_lines_display']
        read_only_fields = ['posted_at', 'reconciled_at', 'gl_journal', 
                           'allocated_amount', 'unallocated_amount', 'gl_lines_display']
    
    def get_gl_lines_display(self, obj):
        """Return GL lines from the associated journal entry"""
        if obj.gl_journal:
            lines = obj.gl_journal.lines.all()
            return JournalLineDisplaySerializer(lines, many=True).data
        return []
    
    def create(self, validated_data):
        allocations_data = validated_data.pop('allocations', [])
        gl_lines_data = validated_data.pop('gl_lines', [])
        payment = ARPayment.objects.create(**validated_data)
        
        # Create allocations
        for allocation_data in allocations_data:
            ARPaymentAllocation.objects.create(payment=payment, **allocation_data)
        
        # Create GL lines if provided
        if gl_lines_data and payment.gl_journal:
            self._create_gl_lines(payment.gl_journal, gl_lines_data)
        
        return payment
    
    def _create_gl_lines(self, journal_entry, gl_lines_data):
        """Create journal lines with segments from GL distribution"""
        for line_data in gl_lines_data:
            # Convert DEBIT/CREDIT to debit/credit amounts
            amount = Decimal(str(line_data.get('amount', 0)))
            line_type = line_data.get('line_type', '').upper()
            
            debit = amount if line_type == 'DEBIT' else Decimal('0')
            credit = amount if line_type == 'CREDIT' else Decimal('0')
            
            # Create journal line
            journal_line = JournalLine.objects.create(
                journal_entry=journal_entry,
                debit=debit,
                credit=credit,
                description=line_data.get('description', '')
            )
            
            # Create segments
            segments = line_data.get('segments', {})
            for segment_type, segment_id in segments.items():
                if segment_id:
                    JournalLineSegment.objects.create(
                        journal_line=journal_line,
                        segment_type=segment_type,
                        segment_id=segment_id
                    )
    
    def update(self, instance, validated_data):
        allocations_data = validated_data.pop('allocations', None)
        gl_lines_data = validated_data.pop('gl_lines', None)
        
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
        
        # Update GL lines if provided
        if gl_lines_data is not None and instance.gl_journal:
            # Clear existing journal lines
            instance.gl_journal.lines.all().delete()
            # Create new GL lines
            self._create_gl_lines(instance.gl_journal, gl_lines_data)
        
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
        
        # Validate GL lines balance if provided
        if 'gl_lines' in data:
            total_debit = Decimal('0')
            total_credit = Decimal('0')
            
            for line in data['gl_lines']:
                amount = Decimal(str(line.get('amount', 0)))
                line_type = line.get('line_type', '').upper()
                
                if line_type == 'DEBIT':
                    total_debit += amount
                elif line_type == 'CREDIT':
                    total_credit += amount
            
            if total_debit != total_credit:
                raise serializers.ValidationError(
                    f"GL lines must balance: Debits ({total_debit}) ≠ Credits ({total_credit})"
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
    """Serializer for AP payments with allocations and GL lines"""
    allocations = APPaymentAllocationSerializer(many=True, required=False)
    gl_lines = serializers.ListField(child=serializers.DictField(), required=False, write_only=True)
    gl_lines_display = serializers.SerializerMethodField(read_only=True)
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
                 'allocations', 'allocated_amount', 'unallocated_amount', 'gl_lines', 'gl_lines_display']
        read_only_fields = ['posted_at', 'reconciled_at', 'gl_journal', 
                           'allocated_amount', 'unallocated_amount', 'gl_lines_display']
    
    def get_gl_lines_display(self, obj):
        """Return GL lines from the associated journal entry"""
        if obj.gl_journal:
            lines = obj.gl_journal.lines.all()
            return JournalLineDisplaySerializer(lines, many=True).data
        return []
    
    def create(self, validated_data):
        allocations_data = validated_data.pop('allocations', [])
        gl_lines_data = validated_data.pop('gl_lines', [])
        payment = APPayment.objects.create(**validated_data)
        
        # Create allocations
        for allocation_data in allocations_data:
            APPaymentAllocation.objects.create(payment=payment, **allocation_data)
        
        # Create GL lines if provided
        if gl_lines_data and payment.gl_journal:
            self._create_gl_lines(payment.gl_journal, gl_lines_data)
        
        return payment
    
    def _create_gl_lines(self, journal_entry, gl_lines_data):
        """Create journal lines with segments from GL distribution"""
        for line_data in gl_lines_data:
            # Convert DEBIT/CREDIT to debit/credit amounts
            amount = Decimal(str(line_data.get('amount', 0)))
            line_type = line_data.get('line_type', '').upper()
            
            debit = amount if line_type == 'DEBIT' else Decimal('0')
            credit = amount if line_type == 'CREDIT' else Decimal('0')
            
            # Create journal line
            journal_line = JournalLine.objects.create(
                journal_entry=journal_entry,
                debit=debit,
                credit=credit,
                description=line_data.get('description', '')
            )
            
            # Create segments
            segments = line_data.get('segments', {})
            for segment_type, segment_id in segments.items():
                if segment_id:
                    JournalLineSegment.objects.create(
                        journal_line=journal_line,
                        segment_type=segment_type,
                        segment_id=segment_id
                    )
    
    def update(self, instance, validated_data):
        allocations_data = validated_data.pop('allocations', None)
        gl_lines_data = validated_data.pop('gl_lines', None)
        
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
        
        # Update GL lines if provided
        if gl_lines_data is not None and instance.gl_journal:
            # Clear existing journal lines
            instance.gl_journal.lines.all().delete()
            # Create new GL lines
            self._create_gl_lines(instance.gl_journal, gl_lines_data)
        
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
        
        # Validate GL lines balance if provided
        if 'gl_lines' in data:
            total_debit = Decimal('0')
            total_credit = Decimal('0')
            
            for line in data['gl_lines']:
                amount = Decimal(str(line.get('amount', 0)))
                line_type = line.get('line_type', '').upper()
                
                if line_type == 'DEBIT':
                    total_debit += amount
                elif line_type == 'CREDIT':
                    total_credit += amount
            
            if total_debit != total_credit:
                raise serializers.ValidationError(
                    f"GL lines must balance: Debits ({total_debit}) ≠ Credits ({total_credit})"
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

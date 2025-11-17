"""
Serializers for Payment Allocations and Invoice Approvals
"""
from rest_framework import serializers
from decimal import Decimal
from ar.models import ARPayment, ARPaymentAllocation, ARInvoice, Customer
from ap.models import APPayment, APPaymentAllocation, APInvoice, Supplier
from finance.models import InvoiceApproval, JournalLine, JournalLineSegment, JournalEntry
from core.models import Currency
from segment.models import XX_Segment, XX_SegmentType


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
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.alias', read_only=True)
    
    class Meta:
        model = JournalLine
        fields = ['id', 'account', 'account_code', 'account_name', 'debit', 'credit', 'line_type', 'amount', 'segments']
    
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
# PAYMENT DISTRIBUTION SERIALIZERS (Dynamic Segments)
# ============================================================================

class PaymentDistributionSegmentSerializer(serializers.Serializer):
    """Nested serializer for segments within a payment distribution line"""
    segment_type = serializers.IntegerField()
    segment_type_name = serializers.CharField(read_only=True)
    segment = serializers.IntegerField()
    segment_code = serializers.CharField(read_only=True)
    segment_name = serializers.CharField(read_only=True)
    
    def validate(self, data):
        """Validate segment exists and is a child type"""
        segment_type_id = data.get('segment_type')
        segment_id = data.get('segment')
        
        # Validate segment exists and is child type
        try:
            segment = XX_Segment.objects.get(pk=segment_id)
            if segment.node_type != 'child':  # Fixed: lowercase 'child'
                raise serializers.ValidationError(
                    f"Segment {segment.code} must be a child type (detail level)"
                )
            
            # Validate segment belongs to the specified segment type
            if segment.segment_type_id != segment_type_id:
                raise serializers.ValidationError(
                    f"Segment {segment.code} does not belong to segment type {segment_type_id}"
                )
        except XX_Segment.DoesNotExist:
            raise serializers.ValidationError(f"Segment {segment_id} does not exist")
        
        return data


class PaymentDistributionSerializer(serializers.Serializer):
    """Serializer for payment distribution lines with dynamic multi-segment support"""
    id = serializers.IntegerField(read_only=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)
    line_type = serializers.ChoiceField(choices=['DEBIT', 'CREDIT'])
    segments = PaymentDistributionSegmentSerializer(many=True)
    
    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate_segments(self, segments):
        """Validate that at least one segment is provided"""
        if not segments or len(segments) == 0:
            raise serializers.ValidationError("At least one segment must be provided")
        
        # Validate each segment belongs to its segment type
        for seg in segments:
            segment_type_id = seg.get('segment_type')
            segment_id = seg.get('segment')
            
            try:
                segment = XX_Segment.objects.get(pk=segment_id)
                if segment.segment_type_id != segment_type_id:
                    raise serializers.ValidationError(
                        f"Segment {segment.code} does not belong to segment type {segment_type_id}"
                    )
            except XX_Segment.DoesNotExist:
                raise serializers.ValidationError(f"Segment {segment_id} does not exist")
        
        return segments


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
    """Serializer for AR payments with allocations and dynamic segment distributions"""
    allocations = ARPaymentAllocationSerializer(many=True, required=False)
    distributions = PaymentDistributionSerializer(many=True, required=False)  # NEW: Dynamic segments
    gl_lines = serializers.ListField(child=serializers.DictField(), required=False, write_only=True)  # OLD: Deprecated
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
                 'allocations', 'allocated_amount', 'unallocated_amount', 
                 'distributions', 'gl_lines', 'gl_lines_display']  # Added distributions
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
        distributions_data = validated_data.pop('distributions', [])  # NEW format
        gl_lines_data = validated_data.pop('gl_lines', [])  # OLD format (deprecated)
        
        payment = ARPayment.objects.create(**validated_data)
        
        # Create allocations
        for allocation_data in allocations_data:
            ARPaymentAllocation.objects.create(payment=payment, **allocation_data)
        
        # Create GL distributions if provided (prefer new format)
        if distributions_data and payment.gl_journal:
            self._create_distributions(payment.gl_journal, distributions_data)
        elif gl_lines_data and payment.gl_journal:
            # Fallback to old format for backward compatibility
            print(f"WARNING: Using deprecated gl_lines format. Please migrate to distributions.")
            self._create_gl_lines_old(payment.gl_journal, gl_lines_data)
        
        return payment
    
    def _create_distributions(self, journal_entry, distributions_data):
        """Create journal lines with dynamic segments from NEW distribution format"""
        for dist_data in distributions_data:
            amount = Decimal(str(dist_data['amount']))
            line_type = dist_data.get('line_type', '').upper()
            
            debit = amount if line_type == 'DEBIT' else Decimal('0')
            credit = amount if line_type == 'CREDIT' else Decimal('0')
            
            # Create journal line
            journal_line = JournalLine.objects.create(
                journal_entry=journal_entry,
                debit=debit,
                credit=credit,
                description=dist_data.get('description', '')
            )
            
            # Create segments from array format
            for segment_data in dist_data.get('segments', []):
                JournalLineSegment.objects.create(
                    journal_line=journal_line,
                    segment_type_id=segment_data['segment_type'],
                    segment_id=segment_data['segment']
                )
    
    def _create_gl_lines(self, journal_entry, gl_lines_data):
        """DEPRECATED: Create journal lines with segments from OLD dictionary format"""
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
        distributions_data = validated_data.pop('distributions', None)  # NEW format
        gl_lines_data = validated_data.pop('gl_lines', None)  # OLD format
        
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
        
        # Update GL distributions if provided (prefer new format)
        if distributions_data is not None and instance.gl_journal:
            instance.gl_journal.lines.all().delete()
            self._create_distributions(instance.gl_journal, distributions_data)
        elif gl_lines_data is not None and instance.gl_journal:
            # Clear existing journal lines
            instance.gl_journal.lines.all().delete()
            # Create new GL lines using old format
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
        
        # Validate distributions balance if provided (NEW format - preferred)
        if 'distributions' in data:
            total_debit = Decimal('0')
            total_credit = Decimal('0')
            
            for dist in data['distributions']:
                amount = Decimal(str(dist['amount']))
                line_type = dist.get('line_type', '').upper()
                
                if line_type == 'DEBIT':
                    total_debit += amount
                elif line_type == 'CREDIT':
                    total_credit += amount
            
            if total_debit != total_credit:
                raise serializers.ValidationError(
                    f"Distributions must balance: Debits ({total_debit}) ≠ Credits ({total_credit})"
                )
        
        # Validate GL lines balance if provided (OLD format - deprecated)
        elif 'gl_lines' in data:
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
    invoice_number = serializers.SerializerMethodField()
    invoice_total = serializers.SerializerMethodField()
    invoice_outstanding = serializers.SerializerMethodField()
    
    class Meta:
        model = APPaymentAllocation
        fields = ['id', 'invoice', 'invoice_number', 'invoice_total', 
                 'invoice_outstanding', 'amount', 'memo', 'created_at']
        read_only_fields = ['created_at']
    
    def get_invoice_number(self, obj):
        """Get invoice number, safely handling None"""
        # Check the FK _id field directly to avoid triggering RelatedObjectDoesNotExist
        if obj.invoice_id is None:
            return None
        try:
            return obj.invoice.number
        except APInvoice.DoesNotExist:
            return None
    
    def get_invoice_total(self, obj):
        """Get invoice total, safely handling None"""
        if obj.invoice_id is None:
            return 0.0
        try:
            return float(obj.invoice.calculate_total())
        except APInvoice.DoesNotExist:
            return 0.0
    
    def get_invoice_outstanding(self, obj):
        """Get invoice outstanding amount, safely handling None"""
        if obj.invoice_id is None:
            return 0.0
        try:
            return float(obj.invoice.outstanding_amount())
        except APInvoice.DoesNotExist:
            return 0.0
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


class APPaymentSerializer(serializers.ModelSerializer):
    """Serializer for AP payments with allocations and dynamic segment distributions"""
    allocations = APPaymentAllocationSerializer(many=True, required=False)
    distributions = PaymentDistributionSerializer(many=True, required=False)  # NEW: Dynamic segments
    gl_lines = serializers.ListField(child=serializers.DictField(), required=False, write_only=True)  # OLD: Deprecated
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
                 'allocations', 'allocated_amount', 'unallocated_amount', 
                 'distributions', 'gl_lines', 'gl_lines_display']  # Added distributions
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
        distributions_data = validated_data.pop('distributions', [])  # NEW format
        gl_lines_data = validated_data.pop('gl_lines', [])  # OLD format (deprecated)
        
        payment = APPayment.objects.create(**validated_data)
        
        # Create allocations
        for allocation_data in allocations_data:
            APPaymentAllocation.objects.create(payment=payment, **allocation_data)
        
        # Create GL distributions if provided (prefer new format)
        if distributions_data and payment.gl_journal:
            self._create_distributions(payment.gl_journal, distributions_data)
        elif gl_lines_data and payment.gl_journal:
            # Fallback to old format for backward compatibility
            print(f"WARNING: Using deprecated gl_lines format. Please migrate to distributions.")
            self._create_gl_lines_old(payment.gl_journal, gl_lines_data)
        
        return payment
    
    def _create_distributions(self, journal_entry, distributions_data):
        """Create journal lines with dynamic segments from NEW distribution format"""
        for dist_data in distributions_data:
            amount = Decimal(str(dist_data['amount']))
            line_type = dist_data.get('line_type', '').upper()
            
            debit = amount if line_type == 'DEBIT' else Decimal('0')
            credit = amount if line_type == 'CREDIT' else Decimal('0')
            
            # Create journal line
            journal_line = JournalLine.objects.create(
                journal_entry=journal_entry,
                debit=debit,
                credit=credit,
                description=dist_data.get('description', '')
            )
            
            # Create segments from array format
            for segment_data in dist_data.get('segments', []):
                JournalLineSegment.objects.create(
                    journal_line=journal_line,
                    segment_type_id=segment_data['segment_type'],
                    segment_id=segment_data['segment']
                )
    
    def _create_gl_lines_old(self, journal_entry, gl_lines_data):
        """DEPRECATED: Create journal lines with segments from OLD dictionary format"""
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
        distributions_data = validated_data.pop('distributions', None)  # NEW format
        gl_lines_data = validated_data.pop('gl_lines', None)  # OLD format
        
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
        
        # Update GL distributions if provided (prefer new format)
        if distributions_data is not None and instance.gl_journal:
            instance.gl_journal.lines.all().delete()
            self._create_distributions(instance.gl_journal, distributions_data)
        elif gl_lines_data is not None and instance.gl_journal:
            # Clear existing journal lines
            instance.gl_journal.lines.all().delete()
            # Create new GL lines using old format
            self._create_gl_lines_old(instance.gl_journal, gl_lines_data)
        
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
        
        # Validate distributions balance if provided (NEW format - preferred)
        if 'distributions' in data:
            total_debit = Decimal('0')
            total_credit = Decimal('0')
            
            for dist in data['distributions']:
                amount = Decimal(str(dist['amount']))
                line_type = dist.get('line_type', '').upper()
                
                if line_type == 'DEBIT':
                    total_debit += amount
                elif line_type == 'CREDIT':
                    total_credit += amount
            
            if total_debit != total_credit:
                raise serializers.ValidationError(
                    f"Distributions must balance: Debits ({total_debit}) ≠ Credits ({total_credit})"
                )
        
        # Validate GL lines balance if provided (OLD format - deprecated)
        elif 'gl_lines' in data:
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

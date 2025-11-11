"""
Contracts Serializers

Serializers for Contracts & Compliance module.
"""

from rest_framework import serializers
from .models import (
    ClauseLibrary, Contract, ContractClause,
    ContractSLA, ContractPenalty, ContractPenaltyInstance,
    ContractRenewal, ContractAttachment, ContractNote
)
from django.contrib.contenttypes.models import ContentType


class ClauseLibrarySerializer(serializers.ModelSerializer):
    """Serializer for clause library."""
    
    clause_category_display = serializers.CharField(source='get_clause_category_display', read_only=True)
    
    class Meta:
        model = ClauseLibrary
        fields = [
            'id', 'clause_code', 'clause_title',
            'clause_category', 'clause_category_display',
            'clause_text', 'placeholders',
            'version', 'is_active',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ContractClauseSerializer(serializers.ModelSerializer):
    """Serializer for contract clauses."""
    
    library_clause_title = serializers.CharField(source='library_clause.clause_title', read_only=True, allow_null=True)
    
    class Meta:
        model = ContractClause
        fields = [
            'id', 'contract', 'library_clause', 'library_clause_title',
            'clause_number', 'clause_title', 'clause_text',
            'is_critical', 'is_negotiable'
        ]
        read_only_fields = ['id']


class ContractSLASerializer(serializers.ModelSerializer):
    """Serializer for contract SLAs."""
    
    measurement_type_display = serializers.CharField(source='get_measurement_type_display', read_only=True)
    compliance_status = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractSLA
        fields = [
            'id', 'contract', 'sla_name',
            'measurement_type', 'measurement_type_display',
            'target_value', 'minimum_value', 'measurement_unit',
            'current_value', 'is_compliant', 'breach_count',
            'has_penalty', 'compliance_status'
        ]
        read_only_fields = ['id', 'breach_count']
    
    def get_compliance_status(self, obj):
        """Get compliance status details."""
        return {
            'is_compliant': obj.is_compliant,
            'breach_count': obj.breach_count,
            'current_value': float(obj.current_value) if obj.current_value else None,
            'target_value': float(obj.target_value),
            'minimum_value': float(obj.minimum_value) if obj.minimum_value else None
        }


class ContractPenaltySerializer(serializers.ModelSerializer):
    """Serializer for contract penalties."""
    
    penalty_type_display = serializers.CharField(source='get_penalty_type_display', read_only=True)
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    related_sla_name = serializers.CharField(source='related_sla.sla_name', read_only=True, allow_null=True)
    
    class Meta:
        model = ContractPenalty
        fields = [
            'id', 'contract', 'penalty_type', 'penalty_type_display',
            'trigger_type', 'trigger_type_display',
            'related_sla', 'related_sla_name',
            'penalty_amount', 'penalty_percentage',
            'max_penalty_amount', 'max_penalty_percentage',
            'total_penalties_applied', 'penalty_count',
            'description'
        ]
        read_only_fields = ['id', 'total_penalties_applied', 'penalty_count']


class ContractPenaltyInstanceSerializer(serializers.ModelSerializer):
    """Serializer for penalty instances."""
    
    penalty_description = serializers.CharField(source='penalty.description', read_only=True)
    
    class Meta:
        model = ContractPenaltyInstance
        fields = [
            'id', 'penalty', 'penalty_description',
            'applied_date', 'penalty_amount',
            'invoice_reference', 'notes'
        ]
        read_only_fields = ['id']


class ContractRenewalSerializer(serializers.ModelSerializer):
    """Serializer for contract renewals."""
    
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    renewed_contract_number = serializers.CharField(source='renewed_contract.contract_number', read_only=True, allow_null=True)
    
    class Meta:
        model = ContractRenewal
        fields = [
            'id', 'contract', 'contract_number',
            'status', 'status_display',
            'proposed_expiry_date', 'proposed_value',
            'decision_date', 'decision_by', 'decision_notes',
            'renewed_contract', 'renewed_contract_number',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ContractAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for contract attachments."""
    
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractAttachment
        fields = [
            'id', 'contract', 'document_type', 'document_type_display',
            'file', 'file_url', 'document_name', 'file_size', 'file_type',
            'version', 'is_latest', 'description',
            'uploaded_by', 'uploaded_at'
        ]
        read_only_fields = ['id', 'file_size', 'file_type', 'uploaded_by', 'uploaded_at']
    
    def get_file_url(self, obj):
        """Get file URL."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class ContractNoteSerializer(serializers.ModelSerializer):
    """Serializer for contract notes."""
    
    note_type_display = serializers.CharField(source='get_note_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = ContractNote
        fields = [
            'id', 'contract', 'note_type', 'note_type_display',
            'note_text', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for contracts."""
    
    clauses = ContractClauseSerializer(many=True, read_only=True)
    slas = ContractSLASerializer(many=True, read_only=True)
    penalties = ContractPenaltySerializer(many=True, read_only=True)
    attachments = ContractAttachmentSerializer(many=True, read_only=True)
    notes_list = ContractNoteSerializer(source='notes', many=True, read_only=True)
    
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    party_name = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    is_expiring_soon = serializers.SerializerMethodField()
    
    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number', 'contract_type', 'contract_type_display',
            'contract_title', 'status', 'status_display',
            'party_content_type', 'party_object_id', 'party_name',
            'contract_date', 'effective_date', 'expiry_date', 'term_months',
            'currency', 'currency_code', 'total_value', 'annual_value',
            'auto_renewal', 'renewal_notice_days',
            'renewed_from', 'is_terminated', 'termination_date', 'termination_reason',
            'contract_owner', 'legal_reviewer',
            'approval_status', 'approval_status_display',
            'approved_by', 'approved_date',
            'original_document', 'reminder_sent', 'reminder_sent_date',
            'description', 'internal_notes',
            'days_until_expiry', 'is_expiring_soon',
            'clauses', 'slas', 'penalties', 'attachments', 'notes_list',
            'created_by', 'created_at', 'updated_by', 'updated_at'
        ]
        read_only_fields = [
            'id', 'contract_number', 'annual_value',
            'approved_by', 'approved_date', 'reminder_sent', 'reminder_sent_date',
            'created_by', 'created_at', 'updated_by', 'updated_at'
        ]
    
    def get_party_name(self, obj):
        """Get party name from polymorphic relationship."""
        if obj.party:
            return str(obj.party)
        return None
    
    def get_days_until_expiry(self, obj):
        """Get days until expiry."""
        return obj.get_days_until_expiry()
    
    def get_is_expiring_soon(self, obj):
        """Check if contract is expiring soon."""
        return obj.is_expiring_soon()


class ContractCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contracts."""
    
    class Meta:
        model = Contract
        fields = [
            'contract_type', 'contract_title',
            'party_content_type', 'party_object_id',
            'contract_date', 'effective_date', 'expiry_date', 'term_months',
            'currency', 'total_value',
            'auto_renewal', 'renewal_notice_days',
            'contract_owner', 'legal_reviewer',
            'original_document', 'description', 'internal_notes'
        ]
    
    def create(self, validated_data):
        """Create contract with generated number."""
        contract = Contract.objects.create(
            created_by=self.context['request'].user,
            updated_by=self.context['request'].user,
            **validated_data
        )
        return contract


class ContractSummarySerializer(serializers.Serializer):
    """Summary serializer for dashboard."""
    
    total_contracts = serializers.IntegerField()
    active_count = serializers.IntegerField()
    expiring_soon_count = serializers.IntegerField()
    expired_count = serializers.IntegerField()
    draft_count = serializers.IntegerField()
    pending_approval_count = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    sla_compliant_count = serializers.IntegerField()
    sla_breach_count = serializers.IntegerField()
    total_penalties = serializers.DecimalField(max_digits=15, decimal_places=2)

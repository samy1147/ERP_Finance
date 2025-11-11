"""
Serializers for Approval and Budget Control API.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    ApprovalWorkflow, ApprovalStep, ApprovalInstance,
    ApprovalStepInstance, ApprovalAction, ApprovalDelegation,
    BudgetAllocation, BudgetCheck
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ApprovalStepSerializer(serializers.ModelSerializer):
    approvers_details = UserSerializer(source='approvers', many=True, read_only=True)
    
    class Meta:
        model = ApprovalStep
        fields = [
            'id', 'workflow', 'sequence', 'name', 'description',
            'amount_threshold', 'approver_type',
            'approvers', 'approvers_details', 'approver_group', 'role_name',
            'is_active', 'is_mandatory', 'require_all_approvers',
            'sla_hours', 'created_at', 'updated_at'
        ]


class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    steps = ApprovalStepSerializer(many=True, read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = ApprovalWorkflow
        fields = [
            'id', 'name', 'description', 'document_type', 'scope',
            'is_active', 'allow_parallel_approval', 'require_all_approvers',
            'auto_approve_below_threshold', 'min_approval_threshold',
            'steps', 'created_at', 'created_by', 'created_by_details',
            'updated_at'
        ]


class ApprovalActionSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    delegated_to_details = UserSerializer(source='delegated_to', read_only=True)
    
    class Meta:
        model = ApprovalAction
        fields = [
            'id', 'step_instance', 'user', 'user_details',
            'action', 'comments', 'delegated_to', 'delegated_to_details',
            'created_at'
        ]


class ApprovalStepInstanceSerializer(serializers.ModelSerializer):
    workflow_step_details = ApprovalStepSerializer(source='workflow_step', read_only=True)
    actions = ApprovalActionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ApprovalStepInstance
        fields = [
            'id', 'approval_instance', 'workflow_step', 'workflow_step_details',
            'status', 'activated_at', 'due_at', 'completed_at',
            'notes', 'actions'
        ]


class ApprovalInstanceSerializer(serializers.ModelSerializer):
    workflow_details = ApprovalWorkflowSerializer(source='workflow', read_only=True)
    requested_by_details = UserSerializer(source='requested_by', read_only=True)
    step_instances = ApprovalStepInstanceSerializer(many=True, read_only=True)
    
    class Meta:
        model = ApprovalInstance
        fields = [
            'id', 'workflow', 'workflow_details',
            'content_type', 'object_id',
            'amount', 'requested_by', 'requested_by_details',
            'requested_at', 'status', 'completed_at',
            'notes', 'step_instances'
        ]


class ApprovalDelegationSerializer(serializers.ModelSerializer):
    from_user_details = UserSerializer(source='from_user', read_only=True)
    to_user_details = UserSerializer(source='to_user', read_only=True)
    is_currently_active = serializers.SerializerMethodField()
    
    class Meta:
        model = ApprovalDelegation
        fields = [
            'id', 'from_user', 'from_user_details',
            'to_user', 'to_user_details',
            'start_date', 'end_date', 'workflow', 'amount_limit',
            'reason', 'is_active', 'is_currently_active',
            'created_at'
        ]
    
    def get_is_currently_active(self, obj):
        return obj.is_valid_now()


class BudgetAllocationSerializer(serializers.ModelSerializer):
    available_amount = serializers.SerializerMethodField()
    utilization_pct = serializers.SerializerMethodField()
    is_over_budget = serializers.SerializerMethodField()
    is_at_warning = serializers.SerializerMethodField()
    
    class Meta:
        model = BudgetAllocation
        fields = [
            'id', 'entity_type', 'entity_id',
            'fiscal_year', 'fiscal_period',
            'allocated_amount', 'pre_committed_amount',
            'committed_amount', 'actual_amount',
            'available_amount', 'utilization_pct',
            'is_over_budget', 'is_at_warning',
            'allow_overrun', 'warning_threshold_pct',
            'created_at', 'updated_at'
        ]
    
    def get_available_amount(self, obj):
        return float(obj.get_available_amount())
    
    def get_utilization_pct(self, obj):
        return float(obj.get_utilization_pct())
    
    def get_is_over_budget(self, obj):
        return obj.is_over_budget()
    
    def get_is_at_warning(self, obj):
        return obj.is_at_warning_threshold()


class BudgetCheckSerializer(serializers.ModelSerializer):
    budget_allocation_details = BudgetAllocationSerializer(source='budget_allocation', read_only=True)
    checked_by_details = UserSerializer(source='checked_by', read_only=True)
    
    class Meta:
        model = BudgetCheck
        fields = [
            'id', 'content_type', 'object_id',
            'budget_allocation', 'budget_allocation_details',
            'check_type', 'amount', 'passed', 'message',
            'checked_by', 'checked_by_details', 'checked_at'
        ]


# Action serializers
class ApproveActionSerializer(serializers.Serializer):
    comments = serializers.CharField(required=False, allow_blank=True)


class RejectActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)


class DelegateActionSerializer(serializers.Serializer):
    delegate_to = serializers.IntegerField(required=True)
    comments = serializers.CharField(required=False, allow_blank=True)


class BudgetCheckRequestSerializer(serializers.Serializer):
    entity_type = serializers.ChoiceField(choices=['COST_CENTER', 'PROJECT'])
    entity_id = serializers.IntegerField()
    fiscal_year = serializers.IntegerField()
    fiscal_period = serializers.IntegerField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    check_type = serializers.ChoiceField(
        choices=['PRE_COMMIT', 'COMMIT', 'ACTUAL'],
        default='COMMIT'
    )

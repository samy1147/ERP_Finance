"""
Approval and Budget Control models for ERP Finance system.

Features:
- Approval workflows with role/amount thresholds
- Multi-step approval (line-level or header-level)
- Budget integration (pre-commit, commit, actuals)
- Delegation and out-of-office routing
- Approval history and audit trail
"""

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import json


class ApprovalWorkflow(models.Model):
    """
    Approval Workflow Definition.
    
    Defines the approval process for different document types.
    """
    
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Document type this workflow applies to
    # e.g., 'requisition.PRHeader', 'po.POHeader'
    document_type = models.CharField(
        max_length=100,
        help_text="Model path (e.g., 'requisition.PRHeader')"
    )
    
    # Workflow scope
    SCOPE_CHOICES = [
        ('HEADER', 'Header Level'),
        ('LINE', 'Line Item Level'),
        ('BOTH', 'Both Header and Line'),
    ]
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='HEADER'
    )
    
    # Active flag
    is_active = models.BooleanField(default=True)
    
    # Workflow options
    allow_parallel_approval = models.BooleanField(
        default=False,
        help_text="Allow multiple approvers to approve simultaneously"
    )
    require_all_approvers = models.BooleanField(
        default=True,
        help_text="Require all approvers in a step or just one"
    )
    auto_approve_below_threshold = models.BooleanField(
        default=False,
        help_text="Auto-approve if amount is below all thresholds"
    )
    min_approval_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Minimum amount requiring approval"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_workflows'
    )
    
    class Meta:
        db_table = 'approval_approvalworkflow'
        ordering = ['name']
        verbose_name = 'Approval Workflow'
        verbose_name_plural = 'Approval Workflows'
    
    def __str__(self):
        return f"{self.name} ({self.document_type})"
    
    def get_steps_for_amount(self, amount):
        """Get required approval steps for given amount."""
        return self.steps.filter(
            is_active=True,
            amount_threshold__lte=amount
        ).order_by('sequence')
    
    def initiate_approval(self, document, amount, requested_by):
        """
        Initiate approval process for a document.
        
        Returns the created ApprovalInstance.
        """
        # Check if auto-approve
        if self.auto_approve_below_threshold and amount < self.min_approval_threshold:
            return None  # Auto-approved
        
        # Get required steps
        steps = self.get_steps_for_amount(amount)
        
        if not steps.exists():
            return None  # No approval required
        
        # Create approval instance
        content_type = ContentType.objects.get_for_model(document)
        instance = ApprovalInstance.objects.create(
            workflow=self,
            content_type=content_type,
            object_id=document.pk,
            amount=amount,
            requested_by=requested_by,
            status='PENDING'
        )
        
        # Create step instances
        for step in steps:
            ApprovalStepInstance.objects.create(
                approval_instance=instance,
                workflow_step=step,
                status='PENDING'
            )
        
        # Activate first step
        first_step = instance.step_instances.first()
        if first_step:
            first_step.activate()
        
        return instance


class ApprovalStep(models.Model):
    """
    Individual step in an approval workflow.
    
    Defines who can approve and under what conditions.
    """
    
    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    
    sequence = models.PositiveIntegerField(
        help_text="Order in which this step is executed"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Amount threshold for this step
    amount_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Minimum amount that triggers this step"
    )
    
    # Approvers (can use role or specific users)
    APPROVER_TYPE_CHOICES = [
        ('USER', 'Specific Users'),
        ('GROUP', 'User Group'),
        ('ROLE', 'Role-based'),
        ('MANAGER', 'Requestor\'s Manager'),
        ('COST_CENTER_MANAGER', 'Cost Center Manager'),
        ('PROJECT_MANAGER', 'Project Manager'),
    ]
    approver_type = models.CharField(
        max_length=30,
        choices=APPROVER_TYPE_CHOICES,
        default='USER'
    )
    
    # Specific approvers (for USER type)
    approvers = models.ManyToManyField(
        User,
        blank=True,
        related_name='approval_steps'
    )
    
    # Approver group (for GROUP type)
    approver_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_steps'
    )
    
    # Role name (for ROLE type)
    role_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Role name for role-based approval"
    )
    
    # Step options
    is_active = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(
        default=True,
        help_text="Whether this step must be completed"
    )
    require_all_approvers = models.BooleanField(
        default=False,
        help_text="Require all approvers or just one"
    )
    
    # Time limits
    sla_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="SLA in hours for this approval step"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'approval_approvalstep'
        ordering = ['workflow', 'sequence']
        verbose_name = 'Approval Step'
        verbose_name_plural = 'Approval Steps'
        unique_together = [['workflow', 'sequence']]
    
    def __str__(self):
        return f"{self.workflow.name} - Step {self.sequence}: {self.name}"
    
    def get_approvers(self, document=None):
        """
        Get list of users who can approve this step.
        
        Args:
            document: The document being approved (needed for dynamic approvers)
        
        Returns:
            QuerySet of Users
        """
        if self.approver_type == 'USER':
            return self.approvers.all()
        
        elif self.approver_type == 'GROUP':
            if self.approver_group:
                return self.approver_group.user_set.all()
            return User.objects.none()
        
        elif self.approver_type == 'MANAGER':
            # Get requestor's manager
            if document and hasattr(document, 'requestor'):
                # Assume User model has a manager field (or use employee profile)
                if hasattr(document.requestor, 'manager'):
                    return User.objects.filter(id=document.requestor.manager.id)
            return User.objects.none()
        
        elif self.approver_type == 'COST_CENTER_MANAGER':
            if document and hasattr(document, 'cost_center'):
                if document.cost_center and document.cost_center.manager:
                    return User.objects.filter(id=document.cost_center.manager.id)
            return User.objects.none()
        
        elif self.approver_type == 'PROJECT_MANAGER':
            if document and hasattr(document, 'project'):
                if document.project and document.project.project_manager:
                    return User.objects.filter(id=document.project.project_manager.id)
            return User.objects.none()
        
        # TODO: Implement ROLE type with custom role system
        return User.objects.none()


class ApprovalInstance(models.Model):
    """
    Instance of an approval process for a specific document.
    
    Tracks the overall approval status.
    """
    
    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.PROTECT,
        related_name='instances'
    )
    
    # Generic foreign key to the document being approved
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Approval details
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount being approved"
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='approval_requests'
    )
    requested_at = models.DateTimeField(default=timezone.now)
    
    # Status
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'approval_approvalinstance'
        ordering = ['-requested_at']
        verbose_name = 'Approval Instance'
        verbose_name_plural = 'Approval Instances'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status', 'requested_at']),
        ]
    
    def __str__(self):
        return f"Approval {self.id} for {self.content_object} - {self.status}"
    
    def check_and_update_status(self):
        """Check step statuses and update overall status."""
        steps = self.step_instances.all()
        
        # Check if any step is rejected
        if steps.filter(status='REJECTED').exists():
            self.status = 'REJECTED'
            self.completed_at = timezone.now()
            self.save()
            return
        
        # Check if all mandatory steps are approved
        mandatory_steps = steps.filter(workflow_step__is_mandatory=True)
        if mandatory_steps.filter(status='APPROVED').count() == mandatory_steps.count():
            self.status = 'APPROVED'
            self.completed_at = timezone.now()
            self.save()
            
            # Update document status
            if hasattr(self.content_object, 'on_approved'):
                self.content_object.on_approved()
            
            return
        
        # Otherwise, in progress
        if self.status == 'PENDING':
            self.status = 'IN_PROGRESS'
            self.save()
    
    def cancel(self, user, reason):
        """Cancel the approval process."""
        self.status = 'CANCELLED'
        self.completed_at = timezone.now()
        self.notes = f"Cancelled by {user}: {reason}"
        self.save()
        
        # Cancel all pending steps
        self.step_instances.filter(status='PENDING').update(
            status='CANCELLED',
            completed_at=timezone.now()
        )


class ApprovalStepInstance(models.Model):
    """
    Instance of an approval step for a specific approval.
    
    Tracks individual step execution and approvers.
    """
    
    approval_instance = models.ForeignKey(
        ApprovalInstance,
        on_delete=models.CASCADE,
        related_name='step_instances'
    )
    workflow_step = models.ForeignKey(
        ApprovalStep,
        on_delete=models.PROTECT,
        related_name='instances'
    )
    
    # Status
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('SKIPPED', 'Skipped'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Timing
    activated_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'approval_approvalstepinstance'
        ordering = ['approval_instance', 'workflow_step__sequence']
        verbose_name = 'Approval Step Instance'
        verbose_name_plural = 'Approval Step Instances'
    
    def __str__(self):
        return f"{self.approval_instance.id} - {self.workflow_step.name} - {self.status}"
    
    def activate(self):
        """Activate this step for approval."""
        self.status = 'ACTIVE'
        self.activated_at = timezone.now()
        
        # Calculate due date
        if self.workflow_step.sla_hours:
            from datetime import timedelta
            self.due_at = self.activated_at + timedelta(hours=self.workflow_step.sla_hours)
        
        self.save()
        
        # TODO: Send notifications to approvers
    
    def approve(self, user, comments=''):
        """Approve this step."""
        # Record the approval action
        ApprovalAction.objects.create(
            step_instance=self,
            user=user,
            action='APPROVED',
            comments=comments
        )
        
        # Check if we have enough approvals
        required_count = 1
        if self.workflow_step.require_all_approvers:
            required_count = self.workflow_step.get_approvers(
                self.approval_instance.content_object
            ).count()
        
        approval_count = self.actions.filter(action='APPROVED').count()
        
        if approval_count >= required_count:
            self.status = 'APPROVED'
            self.completed_at = timezone.now()
            self.save()
            
            # Update approval instance and activate next step
            self.approval_instance.check_and_update_status()
            self._activate_next_step()
    
    def reject(self, user, reason):
        """Reject this step."""
        ApprovalAction.objects.create(
            step_instance=self,
            user=user,
            action='REJECTED',
            comments=reason
        )
        
        self.status = 'REJECTED'
        self.completed_at = timezone.now()
        self.save()
        
        # Update approval instance
        self.approval_instance.check_and_update_status()
    
    def _activate_next_step(self):
        """Activate the next step in sequence."""
        next_step = self.approval_instance.step_instances.filter(
            workflow_step__sequence__gt=self.workflow_step.sequence,
            status='PENDING'
        ).order_by('workflow_step__sequence').first()
        
        if next_step:
            next_step.activate()


class ApprovalAction(models.Model):
    """
    Individual approval action (approve/reject) by a user.
    
    Records who approved/rejected and when.
    """
    
    step_instance = models.ForeignKey(
        ApprovalStepInstance,
        on_delete=models.CASCADE,
        related_name='actions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='approval_actions'
    )
    
    ACTION_CHOICES = [
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('DELEGATED', 'Delegated'),
        ('RETURNED', 'Returned for Revision'),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True)
    
    # Delegation
    delegated_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegated_approvals'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'approval_approvalaction'
        ordering = ['-created_at']
        verbose_name = 'Approval Action'
        verbose_name_plural = 'Approval Actions'
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"


class ApprovalDelegation(models.Model):
    """
    Approval delegation for out-of-office or temporary reassignment.
    
    Allows users to delegate their approval authority to another user.
    """
    
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='delegations_given'
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='delegations_received'
    )
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Scope
    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='delegations',
        help_text="Leave blank to delegate all workflows"
    )
    
    # Optional: Amount limit
    amount_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum amount delegate can approve"
    )
    
    reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'approval_approvaldelegation'
        ordering = ['-start_date']
        verbose_name = 'Approval Delegation'
        verbose_name_plural = 'Approval Delegations'
    
    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.start_date} to {self.end_date})"
    
    def is_valid_now(self):
        """Check if delegation is currently valid."""
        today = timezone.now().date()
        return (
            self.is_active and
            self.start_date <= today <= self.end_date
        )
    
    @classmethod
    def get_delegate_for_user(cls, user, workflow=None, amount=None):
        """
        Get the delegate for a user if one exists.
        
        Returns the delegate User or None.
        """
        today = timezone.now().date()
        
        query = cls.objects.filter(
            from_user=user,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
        
        if workflow:
            query = query.filter(Q(workflow=workflow) | Q(workflow__isnull=True))
        
        if amount:
            query = query.filter(Q(amount_limit__gte=amount) | Q(amount_limit__isnull=True))
        
        delegation = query.first()
        return delegation.to_user if delegation else None


class BudgetAllocation(models.Model):
    """
    Budget allocation for cost centers and projects.
    
    Tracks budget amounts and consumption over time.
    """
    
    # Budget reference
    ENTITY_TYPE_CHOICES = [
        ('COST_CENTER', 'Cost Center'),
        ('PROJECT', 'Project'),
    ]
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES
    )
    entity_id = models.PositiveIntegerField()
    
    # Fiscal period
    fiscal_year = models.PositiveIntegerField()
    fiscal_period = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Leave blank for annual budget"
    )
    
    # Amounts
    allocated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total allocated budget"
    )
    
    # Consumed amounts (cached for performance)
    pre_committed_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="PRs submitted but not approved"
    )
    committed_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Approved PRs and open POs"
    )
    actual_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Actual spending (AP invoices)"
    )
    
    # Budget control settings
    allow_overrun = models.BooleanField(
        default=False,
        help_text="Allow spending beyond allocated budget"
    )
    warning_threshold_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('80.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Warning threshold percentage"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'approval_budgetallocation'
        ordering = ['-fiscal_year', '-fiscal_period']
        verbose_name = 'Budget Allocation'
        verbose_name_plural = 'Budget Allocations'
        unique_together = [['entity_type', 'entity_id', 'fiscal_year', 'fiscal_period']]
        indexes = [
            models.Index(fields=['entity_type', 'entity_id', 'fiscal_year']),
        ]
    
    def __str__(self):
        period = f"P{self.fiscal_period}" if self.fiscal_period else "Annual"
        return f"{self.entity_type} {self.entity_id} - FY{self.fiscal_year} {period}"
    
    def get_available_amount(self):
        """Calculate available budget."""
        return self.allocated_amount - self.committed_amount - self.actual_amount
    
    def get_utilization_pct(self):
        """Calculate budget utilization percentage."""
        if self.allocated_amount == 0:
            return Decimal('0.00')
        
        consumed = self.committed_amount + self.actual_amount
        return (consumed / self.allocated_amount * 100).quantize(Decimal('0.01'))
    
    def is_over_budget(self):
        """Check if over budget."""
        return self.get_available_amount() < 0
    
    def is_at_warning_threshold(self):
        """Check if at warning threshold."""
        return self.get_utilization_pct() >= self.warning_threshold_pct
    
    def check_availability(self, amount, check_type='COMMIT'):
        """
        Check if amount is available in budget.
        
        Args:
            amount: Amount to check
            check_type: 'PRE_COMMIT', 'COMMIT', or 'ACTUAL'
        
        Returns:
            (bool, str): (passed, message)
        """
        available = self.get_available_amount()
        
        if check_type == 'PRE_COMMIT':
            available -= self.pre_committed_amount
        
        if available >= amount:
            return True, "Budget available"
        
        if self.allow_overrun:
            return True, f"Warning: Budget overrun (Available: {available}, Required: {amount})"
        
        return False, f"Insufficient budget (Available: {available}, Required: {amount})"


class BudgetCheck(models.Model):
    """
    Budget check record for documents.
    
    Records budget check results and history.
    """
    
    # Document reference
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Budget allocation
    budget_allocation = models.ForeignKey(
        BudgetAllocation,
        on_delete=models.PROTECT,
        related_name='checks'
    )
    
    # Check details
    CHECK_TYPE_CHOICES = [
        ('PRE_COMMIT', 'Pre-Commitment'),
        ('COMMIT', 'Commitment'),
        ('ACTUAL', 'Actual'),
    ]
    check_type = models.CharField(
        max_length=20,
        choices=CHECK_TYPE_CHOICES
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Result
    passed = models.BooleanField()
    message = models.TextField()
    
    checked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='budget_checks_performed'
    )
    checked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'approval_budgetcheck'
        ordering = ['-checked_at']
        verbose_name = 'Budget Check'
        verbose_name_plural = 'Budget Checks'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['passed', 'checked_at']),
        ]
    
    def __str__(self):
        return f"Budget Check {self.id} - {self.check_type} - {'Passed' if self.passed else 'Failed'}"

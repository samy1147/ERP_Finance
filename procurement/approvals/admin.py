"""
Admin interfaces for Approval and Budget Control.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Sum, Count
from .models import (
    ApprovalWorkflow, ApprovalStep, ApprovalInstance,
    ApprovalStepInstance, ApprovalAction, ApprovalDelegation,
    BudgetAllocation, BudgetCheck
)


class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 1
    fields = [
        'sequence', 'name', 'amount_threshold',
        'approver_type', 'is_mandatory', 'sla_hours'
    ]
    ordering = ['sequence']


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'document_type', 'scope', 'is_active',
        'get_steps_count', 'min_approval_threshold'
    ]
    list_filter = ['is_active', 'scope', 'document_type']
    search_fields = ['name', 'description', 'document_type']
    readonly_fields = ['created_at', 'updated_at', 'get_workflow_summary']
    
    inlines = [ApprovalStepInline]
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'description', 'document_type', 'scope']
        }),
        ('Workflow Options', {
            'fields': [
                'is_active', 'allow_parallel_approval',
                'require_all_approvers', 'auto_approve_below_threshold',
                'min_approval_threshold'
            ]
        }),
        ('Summary', {
            'fields': ['get_workflow_summary'],
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': ['created_at', 'created_by', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_steps_count(self, obj):
        return obj.steps.filter(is_active=True).count()
    get_steps_count.short_description = 'Active Steps'
    
    def get_workflow_summary(self, obj):
        if not obj.pk:
            return "Save to see summary"
        
        steps = obj.steps.filter(is_active=True).order_by('sequence')
        
        summary_html = '<table style="width:100%; border-collapse: collapse;">'
        summary_html += '<tr style="background: #f0f0f0;"><th>Seq</th><th>Name</th><th>Threshold</th><th>Approver Type</th><th>SLA (hrs)</th></tr>'
        
        for step in steps:
            summary_html += f'<tr><td>{step.sequence}</td><td>{step.name}</td><td>{step.amount_threshold}</td><td>{step.get_approver_type_display()}</td><td>{step.sla_hours or "-"}</td></tr>'
        
        summary_html += '</table>'
        
        return format_html(summary_html)
    get_workflow_summary.short_description = 'Workflow Summary'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = [
        'workflow', 'sequence', 'name', 'amount_threshold',
        'approver_type', 'is_mandatory', 'is_active', 'sla_hours'
    ]
    list_filter = ['workflow', 'approver_type', 'is_mandatory', 'is_active']
    search_fields = ['name', 'description', 'workflow__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Step Information', {
            'fields': ['workflow', 'sequence', 'name', 'description']
        }),
        ('Threshold', {
            'fields': ['amount_threshold']
        }),
        ('Approvers', {
            'fields': [
                'approver_type', 'approvers', 'approver_group', 'role_name'
            ]
        }),
        ('Options', {
            'fields': [
                'is_active', 'is_mandatory',
                'require_all_approvers', 'sla_hours'
            ]
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    filter_horizontal = ['approvers']


class ApprovalStepInstanceInline(admin.TabularInline):
    model = ApprovalStepInstance
    extra = 0
    fields = [
        'workflow_step', 'status', 'activated_at',
        'due_at', 'completed_at'
    ]
    readonly_fields = ['workflow_step', 'activated_at', 'due_at', 'completed_at']
    can_delete = False


@admin.register(ApprovalInstance)
class ApprovalInstanceAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'workflow', 'get_status_colored', 'amount',
        'requested_by', 'requested_at', 'get_document_link'
    ]
    list_filter = ['status', 'workflow', 'requested_at']
    search_fields = ['id', 'requested_by__username', 'notes']
    readonly_fields = [
        'workflow', 'content_type', 'object_id',
        'amount', 'requested_by', 'requested_at',
        'completed_at', 'get_document_link', 'get_approval_timeline'
    ]
    
    date_hierarchy = 'requested_at'
    inlines = [ApprovalStepInstanceInline]
    
    fieldsets = [
        ('Approval Information', {
            'fields': [
                'workflow', 'status', 'amount',
                'requested_by', 'requested_at'
            ]
        }),
        ('Document', {
            'fields': ['content_type', 'object_id', 'get_document_link']
        }),
        ('Timeline', {
            'fields': ['get_approval_timeline']
        }),
        ('Completion', {
            'fields': ['completed_at']
        }),
        ('Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['action_cancel']
    
    def get_status_colored(self, obj):
        colors = {
            'PENDING': 'gray',
            'IN_PROGRESS': 'blue',
            'APPROVED': 'green',
            'REJECTED': 'red',
            'CANCELLED': 'orange',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    
    def get_document_link(self, obj):
        if obj.content_object:
            return format_html(
                '<a href="#">{}</a>',
                str(obj.content_object)
            )
        return "N/A"
    get_document_link.short_description = 'Document'
    
    def get_approval_timeline(self, obj):
        if not obj.pk:
            return "Save to see timeline"
        
        timeline_html = '<table style="width:100%; border-collapse: collapse;">'
        timeline_html += '<tr style="background: #f0f0f0;"><th>Step</th><th>Status</th><th>Activated</th><th>Completed</th><th>Actions</th></tr>'
        
        for step_inst in obj.step_instances.all():
            actions_count = step_inst.actions.count()
            status_color = {
                'PENDING': 'gray',
                'ACTIVE': 'blue',
                'APPROVED': 'green',
                'REJECTED': 'red',
                'CANCELLED': 'orange',
                'SKIPPED': 'gray'
            }.get(step_inst.status, 'black')
            
            timeline_html += f'<tr>'
            timeline_html += f'<td>{step_inst.workflow_step.name}</td>'
            timeline_html += f'<td><span style="color: {status_color};">{step_inst.get_status_display()}</span></td>'
            timeline_html += f'<td>{step_inst.activated_at.strftime("%Y-%m-%d %H:%M") if step_inst.activated_at else "-"}</td>'
            timeline_html += f'<td>{step_inst.completed_at.strftime("%Y-%m-%d %H:%M") if step_inst.completed_at else "-"}</td>'
            timeline_html += f'<td>{actions_count}</td>'
            timeline_html += f'</tr>'
        
        timeline_html += '</table>'
        
        return format_html(timeline_html)
    get_approval_timeline.short_description = 'Approval Timeline'
    
    def action_cancel(self, request, queryset):
        cancelled_count = 0
        for approval in queryset.filter(status__in=['PENDING', 'IN_PROGRESS']):
            approval.cancel(request.user, "Cancelled from admin interface")
            cancelled_count += 1
        
        self.message_user(request, f"Cancelled {cancelled_count} approval(s)")
    action_cancel.short_description = "Cancel selected approvals"


@admin.register(ApprovalStepInstance)
class ApprovalStepInstanceAdmin(admin.ModelAdmin):
    list_display = [
        'approval_instance', 'workflow_step', 'get_status_colored',
        'activated_at', 'due_at', 'completed_at', 'get_is_overdue'
    ]
    list_filter = ['status', 'activated_at', 'workflow_step__workflow']
    search_fields = ['approval_instance__id', 'workflow_step__name']
    readonly_fields = [
        'approval_instance', 'workflow_step',
        'activated_at', 'due_at', 'completed_at',
        'get_actions_summary'
    ]
    
    fieldsets = [
        ('Step Information', {
            'fields': ['approval_instance', 'workflow_step', 'status']
        }),
        ('Timing', {
            'fields': ['activated_at', 'due_at', 'completed_at']
        }),
        ('Actions', {
            'fields': ['get_actions_summary']
        }),
        ('Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
    ]
    
    def get_status_colored(self, obj):
        colors = {
            'PENDING': 'gray',
            'ACTIVE': 'blue',
            'APPROVED': 'green',
            'REJECTED': 'red',
            'CANCELLED': 'orange',
            'SKIPPED': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    
    def get_is_overdue(self, obj):
        if obj.due_at and obj.status == 'ACTIVE':
            if timezone.now() > obj.due_at:
                return format_html('<span style="color: red; font-weight: bold;">OVERDUE</span>')
        return '-'
    get_is_overdue.short_description = 'Overdue'
    
    def get_actions_summary(self, obj):
        if not obj.pk:
            return "Save to see actions"
        
        actions = obj.actions.all()
        
        if not actions:
            return "No actions yet"
        
        summary_html = '<table style="width:100%; border-collapse: collapse;">'
        summary_html += '<tr style="background: #f0f0f0;"><th>User</th><th>Action</th><th>Comments</th><th>Date</th></tr>'
        
        for action in actions:
            summary_html += f'<tr>'
            summary_html += f'<td>{action.user}</td>'
            summary_html += f'<td>{action.get_action_display()}</td>'
            summary_html += f'<td>{action.comments[:50]}</td>'
            summary_html += f'<td>{action.created_at.strftime("%Y-%m-%d %H:%M")}</td>'
            summary_html += f'</tr>'
        
        summary_html += '</table>'
        
        return format_html(summary_html)
    get_actions_summary.short_description = 'Actions Summary'


@admin.register(ApprovalAction)
class ApprovalActionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_approval_id', 'get_step_name',
        'user', 'action', 'created_at'
    ]
    list_filter = ['action', 'created_at', 'user']
    search_fields = [
        'step_instance__approval_instance__id',
        'user__username', 'comments'
    ]
    readonly_fields = [
        'step_instance', 'user', 'action',
        'comments', 'delegated_to', 'created_at'
    ]
    
    fieldsets = [
        ('Action Information', {
            'fields': [
                'step_instance', 'user', 'action', 'comments'
            ]
        }),
        ('Delegation', {
            'fields': ['delegated_to']
        }),
        ('Timestamp', {
            'fields': ['created_at']
        }),
    ]
    
    def get_approval_id(self, obj):
        return obj.step_instance.approval_instance.id
    get_approval_id.short_description = 'Approval ID'
    
    def get_step_name(self, obj):
        return obj.step_instance.workflow_step.name
    get_step_name.short_description = 'Step'


@admin.register(ApprovalDelegation)
class ApprovalDelegationAdmin(admin.ModelAdmin):
    list_display = [
        'from_user', 'to_user', 'start_date', 'end_date',
        'workflow', 'amount_limit', 'get_is_active_display'
    ]
    list_filter = ['is_active', 'start_date', 'end_date', 'workflow']
    search_fields = [
        'from_user__username', 'to_user__username',
        'reason'
    ]
    readonly_fields = ['created_at']
    
    date_hierarchy = 'start_date'
    
    fieldsets = [
        ('Delegation', {
            'fields': ['from_user', 'to_user', 'start_date', 'end_date']
        }),
        ('Scope', {
            'fields': ['workflow', 'amount_limit']
        }),
        ('Details', {
            'fields': ['reason', 'is_active']
        }),
        ('Timestamp', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['action_activate', 'action_deactivate']
    
    def get_is_active_display(self, obj):
        is_valid = obj.is_valid_now()
        if is_valid:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        else:
            return format_html('<span style="color: gray;">Inactive</span>')
    get_is_active_display.short_description = 'Currently Active'
    
    def action_activate(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} delegation(s)")
    action_activate.short_description = "Activate selected delegations"
    
    def action_deactivate(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} delegation(s)")
    action_deactivate.short_description = "Deactivate selected delegations"


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = [
        'entity_type', 'entity_id', 'fiscal_year', 'fiscal_period',
        'allocated_amount', 'get_utilization_display',
        'get_available_display', 'get_status_display'
    ]
    list_filter = [
        'entity_type', 'fiscal_year', 'fiscal_period',
        'allow_overrun'
    ]
    search_fields = ['entity_id']
    readonly_fields = [
        'pre_committed_amount', 'committed_amount', 'actual_amount',
        'created_at', 'updated_at', 'get_budget_summary'
    ]
    
    fieldsets = [
        ('Budget Reference', {
            'fields': ['entity_type', 'entity_id', 'fiscal_year', 'fiscal_period']
        }),
        ('Budget Amounts', {
            'fields': [
                'allocated_amount', 'pre_committed_amount',
                'committed_amount', 'actual_amount'
            ]
        }),
        ('Budget Control', {
            'fields': ['allow_overrun', 'warning_threshold_pct']
        }),
        ('Summary', {
            'fields': ['get_budget_summary']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_utilization_display(self, obj):
        pct = obj.get_utilization_pct()
        color = 'green' if pct < obj.warning_threshold_pct else 'orange' if pct < 100 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, pct
        )
    get_utilization_display.short_description = 'Utilization'
    
    def get_available_display(self, obj):
        available = obj.get_available_amount()
        color = 'green' if available > 0 else 'red'
        return format_html(
            '<span style="color: {};">{:,.2f}</span>',
            color, available
        )
    get_available_display.short_description = 'Available'
    
    def get_status_display(self, obj):
        if obj.is_over_budget():
            return format_html('<span style="color: red; font-weight: bold;">OVER BUDGET</span>')
        elif obj.is_at_warning_threshold():
            return format_html('<span style="color: orange; font-weight: bold;">WARNING</span>')
        else:
            return format_html('<span style="color: green;">OK</span>')
    get_status_display.short_description = 'Status'
    
    def get_budget_summary(self, obj):
        if not obj.pk:
            return "Save to see summary"
        
        available = obj.get_available_amount()
        utilization = obj.get_utilization_pct()
        
        return format_html(
            '<div style="font-family: monospace;">'
            '<strong>Allocated:</strong> {:,.2f}<br>'
            '<strong>Pre-Committed:</strong> {:,.2f}<br>'
            '<strong>Committed:</strong> {:,.2f}<br>'
            '<strong>Actual:</strong> {:,.2f}<br>'
            '<strong>Available:</strong> <span style="color: {};">{:,.2f}</span><br>'
            '<strong>Utilization:</strong> {:.1f}%<br>'
            '</div>',
            obj.allocated_amount,
            obj.pre_committed_amount,
            obj.committed_amount,
            obj.actual_amount,
            'green' if available > 0 else 'red',
            available,
            utilization
        )
    get_budget_summary.short_description = 'Budget Summary'


@admin.register(BudgetCheck)
class BudgetCheckAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'check_type', 'amount', 'get_passed_display',
        'budget_allocation', 'checked_by', 'checked_at'
    ]
    list_filter = ['check_type', 'passed', 'checked_at']
    search_fields = ['id', 'message', 'checked_by__username']
    readonly_fields = [
        'content_type', 'object_id', 'budget_allocation',
        'check_type', 'amount', 'passed', 'message',
        'checked_by', 'checked_at'
    ]
    
    date_hierarchy = 'checked_at'
    
    fieldsets = [
        ('Document', {
            'fields': ['content_type', 'object_id']
        }),
        ('Check Details', {
            'fields': [
                'budget_allocation', 'check_type',
                'amount', 'passed', 'message'
            ]
        }),
        ('Audit', {
            'fields': ['checked_by', 'checked_at']
        }),
    ]
    
    def get_passed_display(self, obj):
        if obj.passed:
            return format_html('<span style="color: green; font-weight: bold;">✓ PASSED</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ FAILED</span>')
    get_passed_display.short_description = 'Result'

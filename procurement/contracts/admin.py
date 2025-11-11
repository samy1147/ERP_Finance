"""
Contracts & Compliance Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    ClauseLibrary, Contract, ContractClause,
    ContractSLA, ContractPenalty, ContractPenaltyInstance,
    ContractRenewal, ContractAttachment, ContractNote
)


@admin.register(ClauseLibrary)
class ClauseLibraryAdmin(admin.ModelAdmin):
    list_display = [
        'clause_code', 'clause_title', 'get_category_colored',
        'version', 'is_active'
    ]
    list_filter = ['clause_category', 'is_active']
    search_fields = ['clause_code', 'clause_title', 'clause_text']
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at']
    
    fieldsets = (
        ('Clause Identification', {
            'fields': (
                'clause_code', 'clause_title', 'clause_category'
            )
        }),
        ('Clause Content', {
            'fields': (
                'clause_text', 'placeholders'
            )
        }),
        ('Metadata', {
            'fields': (
                'description', 'notes', 'version', 'is_active'
            )
        }),
        ('Audit Trail', {
            'fields': (
                'created_by', 'created_at', 'updated_by', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_category_colored(self, obj):
        """Color-coded category"""
        colors = {
            'GENERAL': 'blue',
            'PAYMENT': 'green',
            'DELIVERY': 'orange',
            'WARRANTY': 'purple',
            'LIABILITY': 'red',
            'CONFIDENTIALITY': 'darkblue',
            'TERMINATION': 'darkred',
            'DISPUTE': 'brown',
            'COMPLIANCE': 'teal',
            'SLA': 'darkgreen',
            'IP': 'indigo',
            'DATA_PROTECTION': 'navy',
            'FORCE_MAJEURE': 'gray',
            'OTHER': 'black',
        }
        color = colors.get(obj.clause_category, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_clause_category_display()
        )
    get_category_colored.short_description = 'Category'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class ContractClauseInline(admin.TabularInline):
    model = ContractClause
    extra = 0
    fields = [
        'clause_number', 'library_clause', 'clause_title',
        'is_critical', 'is_negotiable'
    ]


class ContractSLAInline(admin.TabularInline):
    model = ContractSLA
    extra = 0
    fields = [
        'sla_name', 'measurement_type', 'target_value',
        'current_value', 'is_compliant', 'is_active'
    ]
    readonly_fields = ['is_compliant']


class ContractPenaltyInline(admin.TabularInline):
    model = ContractPenalty
    extra = 0
    fields = [
        'penalty_type', 'trigger_type', 'description',
        'penalty_amount', 'total_penalties_applied', 'is_active'
    ]
    readonly_fields = ['total_penalties_applied']


class ContractAttachmentInline(admin.TabularInline):
    model = ContractAttachment
    extra = 0
    fields = [
        'document_type', 'document_name', 'file',
        'version', 'is_latest', 'uploaded_at'
    ]
    readonly_fields = ['uploaded_at']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        'contract_number', 'contract_title', 'get_contract_type_colored',
        'get_party_name', 'effective_date', 'expiry_date',
        'get_status_colored', 'total_value', 'get_expiry_alert'
    ]
    list_filter = [
        'contract_type', 'status', 'is_renewable', 'auto_renewal',
        'is_terminated', 'approval_status'
    ]
    search_fields = [
        'contract_number', 'contract_title',
        'description'
    ]
    readonly_fields = [
        'contract_number', 'annual_value', 'status',
        'is_terminated', 'termination_date', 'terminated_by',
        'approval_status', 'approved_by', 'approved_date',
        'reminder_sent', 'reminder_sent_date',
        'created_by', 'created_at', 'updated_by', 'updated_at',
        'get_contract_summary', 'get_sla_summary',
        'get_penalty_summary', 'get_days_remaining'
    ]
    
    fieldsets = (
        ('Contract Information', {
            'fields': (
                'contract_number', 'contract_title', 'contract_type',
                'status', 'description'
            )
        }),
        ('Party Information', {
            'fields': (
                'party_content_type', 'party_object_id'
            )
        }),
        ('Dates', {
            'fields': (
                'contract_date', 'effective_date', 'expiry_date',
                'get_days_remaining'
            )
        }),
        ('Financial Details', {
            'fields': (
                'currency', 'total_value', 'annual_value'
            )
        }),
        ('Term & Renewal', {
            'fields': (
                'term_months', 'is_renewable', 'auto_renewal',
                'renewal_notice_days', 'renewed_from'
            )
        }),
        ('Termination', {
            'fields': (
                'is_terminated', 'termination_date',
                'termination_reason', 'terminated_by'
            )
        }),
        ('Responsible Parties', {
            'fields': (
                'contract_owner', 'legal_reviewer'
            )
        }),
        ('Approval', {
            'fields': (
                'approval_status', 'approved_by', 'approved_date'
            )
        }),
        ('Document', {
            'fields': ('original_document',)
        }),
        ('Reminders', {
            'fields': (
                'reminder_sent', 'reminder_sent_date'
            )
        }),
        ('Summary', {
            'fields': (
                'get_contract_summary', 'get_sla_summary',
                'get_penalty_summary'
            )
        }),
        ('Notes', {
            'fields': ('internal_notes',)
        }),
        ('Audit Trail', {
            'fields': (
                'created_by', 'created_at', 'updated_by', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        ContractClauseInline, ContractSLAInline,
        ContractPenaltyInline, ContractAttachmentInline
    ]
    
    actions = [
        'action_approve', 'action_activate', 'action_terminate',
        'action_send_renewal_reminder'
    ]
    
    def get_contract_type_colored(self, obj):
        """Color-coded contract type"""
        colors = {
            'PURCHASE': 'blue',
            'SALES': 'green',
            'SERVICE': 'purple',
            'MASTER': 'darkblue',
            'FRAMEWORK': 'teal',
            'NDA': 'orange',
            'SLA': 'darkgreen',
            'LICENSE': 'indigo',
            'OTHER': 'gray',
        }
        color = colors.get(obj.contract_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_contract_type_display()
        )
    get_contract_type_colored.short_description = 'Type'
    
    def get_party_name(self, obj):
        """Get party name"""
        if obj.party:
            return obj.party.name if hasattr(obj.party, 'name') else str(obj.party)
        return 'N/A'
    get_party_name.short_description = 'Party'
    
    def get_status_colored(self, obj):
        """Color-coded status"""
        colors = {
            'DRAFT': 'gray',
            'UNDER_REVIEW': 'blue',
            'PENDING_APPROVAL': 'orange',
            'APPROVED': 'green',
            'ACTIVE': 'darkgreen',
            'EXPIRING_SOON': 'darkorange',
            'EXPIRED': 'red',
            'TERMINATED': 'darkred',
            'RENEWED': 'teal',
            'CANCELLED': 'darkgray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    
    def get_expiry_alert(self, obj):
        """Expiry alert indicator"""
        days_remaining = obj.get_days_until_expiry()
        
        if obj.status == 'EXPIRED':
            return format_html('<span style="color: red;">✗ Expired</span>')
        elif days_remaining <= obj.renewal_notice_days and days_remaining > 0:
            return format_html(
                '<span style="color: orange;">⚠ {} days</span>',
                days_remaining
            )
        elif days_remaining > 0:
            return format_html(
                '<span style="color: green;">{} days</span>',
                days_remaining
            )
        else:
            return format_html('<span style="color: gray;">N/A</span>')
    get_expiry_alert.short_description = 'Expiry'
    
    def get_days_remaining(self, obj):
        """Days remaining display"""
        days = obj.get_days_until_expiry()
        if days > 0:
            html = f"""
            <div style="padding: 10px; background: {'#fff3cd' if days <= obj.renewal_notice_days else '#d4edda'}; border-radius: 5px;">
                <strong>Days Until Expiry:</strong> {days} days<br>
                <strong>Expiry Date:</strong> {obj.expiry_date.strftime('%Y-%m-%d')}<br>
                <strong>Renewal Notice Period:</strong> {obj.renewal_notice_days} days<br>
                <span style="color: {'orange' if days <= obj.renewal_notice_days else 'green'}; font-weight: bold;">
                    {'⚠ RENEWAL NOTICE PERIOD' if days <= obj.renewal_notice_days else '✓ ACTIVE'}
                </span>
            </div>
            """
        else:
            html = """
            <div style="padding: 10px; background: #f8d7da; border-radius: 5px;">
                <span style="color: red; font-weight: bold;">✗ CONTRACT EXPIRED</span>
            </div>
            """
        return format_html(html)
    get_days_remaining.short_description = 'Days Remaining'
    
    def get_contract_summary(self, obj):
        """Contract summary"""
        if not obj.pk:
            return "Save contract to see summary"
        
        html = f"""
        <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
            <strong>Contract Summary:</strong><br>
            Type: {obj.get_contract_type_display()}<br>
            Status: {obj.get_status_display()}<br>
            Party: {self.get_party_name(obj)}<br>
            Total Value: {obj.total_value:,.2f} {obj.currency.code}<br>
            Annual Value: {obj.annual_value:,.2f} {obj.currency.code}<br>
            Term: {obj.term_months} months<br>
            Auto-Renewal: {'Yes' if obj.auto_renewal else 'No'}<br>
            Clauses: {obj.clauses.count()}<br>
            SLAs: {obj.slas.count()}<br>
            Penalties: {obj.penalties.count()}<br>
            Attachments: {obj.attachments.count()}
        </div>
        """
        return format_html(html)
    get_contract_summary.short_description = 'Contract Summary'
    
    def get_sla_summary(self, obj):
        """SLA summary"""
        if not obj.pk:
            return "Save contract to see SLAs"
        
        slas = obj.slas.all()
        if not slas.exists():
            return "No SLAs defined"
        
        compliant = slas.filter(is_compliant=True).count()
        breached = slas.filter(is_compliant=False).count()
        
        html = f"""
        <div style="padding: 10px; background: #e3f2fd; border-radius: 5px;">
            <strong>SLA Summary:</strong><br>
            Total SLAs: {slas.count()}<br>
            Compliant: <span style="color: green;">{compliant}</span><br>
            Breached: <span style="color: red;">{breached}</span>
        </div>
        """
        return format_html(html)
    get_sla_summary.short_description = 'SLA Summary'
    
    def get_penalty_summary(self, obj):
        """Penalty summary"""
        if not obj.pk:
            return "Save contract to see penalties"
        
        penalties = obj.penalties.all()
        if not penalties.exists():
            return "No penalties defined"
        
        total_penalties = sum(p.total_penalties_applied for p in penalties)
        
        html = f"""
        <div style="padding: 10px; background: #fff3cd; border-radius: 5px;">
            <strong>Penalty Summary:</strong><br>
            Total Penalties Applied: <span style="color: red;">{total_penalties:,.2f} {obj.currency.code}</span><br>
            Penalty Count: {sum(p.penalty_count for p in penalties)}
        </div>
        """
        return format_html(html)
    get_penalty_summary.short_description = 'Penalty Summary'
    
    def action_approve(self, request, queryset):
        """Approve contracts"""
        count = 0
        for contract in queryset:
            try:
                contract.approve(request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f"Error approving {contract.contract_number}: {e}", level='error')
        
        self.message_user(request, f"Approved {count} contracts")
    action_approve.short_description = "Approve selected contracts"
    
    def action_activate(self, request, queryset):
        """Activate contracts"""
        count = 0
        for contract in queryset:
            try:
                contract.activate(request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f"Error activating {contract.contract_number}: {e}", level='error')
        
        self.message_user(request, f"Activated {count} contracts")
    action_activate.short_description = "Activate selected contracts"
    
    def action_terminate(self, request, queryset):
        """Terminate contracts"""
        count = 0
        for contract in queryset:
            try:
                contract.terminate(request.user, "Terminated via admin action")
                count += 1
            except Exception as e:
                self.message_user(request, f"Error terminating {contract.contract_number}: {e}", level='error')
        
        self.message_user(request, f"Terminated {count} contracts")
    action_terminate.short_description = "Terminate selected contracts"
    
    def action_send_renewal_reminder(self, request, queryset):
        """Send renewal reminders"""
        count = 0
        for contract in queryset:
            if contract.is_expiring_soon() and not contract.reminder_sent:
                # Would send email/notification here
                contract.reminder_sent = True
                contract.reminder_sent_date = timezone.now().date()
                contract.save()
                count += 1
        
        self.message_user(request, f"Sent renewal reminders for {count} contracts")
    action_send_renewal_reminder.short_description = "Send renewal reminders"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContractSLA)
class ContractSLAAdmin(admin.ModelAdmin):
    list_display = [
        'contract', 'sla_name', 'measurement_type',
        'target_value', 'current_value', 'get_compliance_status',
        'breach_count', 'is_active'
    ]
    list_filter = ['measurement_type', 'is_compliant', 'is_active', 'has_penalty']
    search_fields = ['sla_name', 'contract__contract_number']
    readonly_fields = ['is_compliant', 'breach_count', 'last_measured_date']
    
    def get_compliance_status(self, obj):
        """Compliance status indicator"""
        if obj.is_compliant:
            return format_html('<span style="color: green;">✓ Compliant</span>')
        else:
            return format_html(
                '<span style="color: red;">✗ Breached ({} times)</span>',
                obj.breach_count
            )
    get_compliance_status.short_description = 'Compliance'


@admin.register(ContractPenalty)
class ContractPenaltyAdmin(admin.ModelAdmin):
    list_display = [
        'contract', 'get_penalty_type_colored', 'trigger_type',
        'penalty_amount', 'total_penalties_applied', 'penalty_count',
        'is_active'
    ]
    list_filter = ['penalty_type', 'trigger_type', 'is_active']
    search_fields = ['contract__contract_number', 'description']
    readonly_fields = ['total_penalties_applied', 'penalty_count']
    
    def get_penalty_type_colored(self, obj):
        """Color-coded penalty type"""
        colors = {
            'PENALTY': 'red',
            'LIQUIDATED_DAMAGES': 'darkred',
            'INCENTIVE': 'green',
            'DISCOUNT': 'blue',
        }
        color = colors.get(obj.penalty_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_penalty_type_display()
        )
    get_penalty_type_colored.short_description = 'Type'


@admin.register(ContractRenewal)
class ContractRenewalAdmin(admin.ModelAdmin):
    list_display = [
        'contract', 'renewal_date', 'proposed_expiry_date',
        'proposed_value', 'get_status_colored', 'decision_date',
        'renewed_contract'
    ]
    list_filter = ['status']
    search_fields = ['contract__contract_number']
    readonly_fields = [
        'renewed_contract', 'created_by', 'created_at', 'updated_at'
    ]
    
    def get_status_colored(self, obj):
        """Color-coded status"""
        colors = {
            'PENDING': 'orange',
            'UNDER_NEGOTIATION': 'blue',
            'APPROVED': 'green',
            'RENEWED': 'darkgreen',
            'NOT_RENEWED': 'red',
            'CANCELLED': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContractAttachment)
class ContractAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'contract', 'document_name', 'get_document_type_colored',
        'version', 'is_latest', 'file_size', 'uploaded_at'
    ]
    list_filter = ['document_type', 'is_latest']
    search_fields = ['contract__contract_number', 'document_name']
    readonly_fields = ['file_size', 'file_type', 'uploaded_by', 'uploaded_at']
    
    def get_document_type_colored(self, obj):
        """Color-coded document type"""
        colors = {
            'CONTRACT': 'darkblue',
            'AMENDMENT': 'orange',
            'EXHIBIT': 'purple',
            'CORRESPONDENCE': 'blue',
            'INVOICE': 'green',
            'REPORT': 'teal',
            'CERTIFICATE': 'darkgreen',
            'OTHER': 'gray',
        }
        color = colors.get(obj.document_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_document_type_display()
        )
    get_document_type_colored.short_description = 'Type'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContractNote)
class ContractNoteAdmin(admin.ModelAdmin):
    list_display = [
        'contract', 'note_type', 'get_note_preview',
        'created_by', 'created_at'
    ]
    list_filter = ['note_type', 'created_at']
    search_fields = ['contract__contract_number', 'note_text']
    readonly_fields = ['created_by', 'created_at']
    
    def get_note_preview(self, obj):
        """Note preview"""
        preview = obj.note_text[:100]
        if len(obj.note_text) > 100:
            preview += '...'
        return preview
    get_note_preview.short_description = 'Note Preview'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

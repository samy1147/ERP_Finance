# procurement/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    RFxEvent, RFxItem, SupplierInvitation, SupplierQuote, SupplierQuoteLine,
    RFxAward, RFxAwardLine, AuctionBid
)


# ==================== INLINE ADMINS ====================

class RFxItemInline(admin.TabularInline):
    model = RFxItem
    extra = 1
    fields = ('line_number', 'item_code', 'description', 'quantity', 'unit_of_measure', 
              'estimated_unit_price', 'is_mandatory')
    ordering = ['line_number']


class SupplierInvitationInline(admin.TabularInline):
    model = SupplierInvitation
    extra = 0
    fields = ('supplier', 'status', 'invited_date', 'responded_date')
    readonly_fields = ('invited_date', 'responded_date')
    autocomplete_fields = ('supplier',)


class SupplierQuoteLineInline(admin.TabularInline):
    model = SupplierQuoteLine
    extra = 0
    fields = ('rfx_item', 'is_quoted', 'quantity', 'unit_price', 'brand_offered', 
              'delivery_lead_time_days', 'meets_specifications')
    readonly_fields = ('rfx_item',)


class RFxAwardLineInline(admin.TabularInline):
    model = RFxAwardLine
    extra = 0
    fields = ('rfx_item', 'quantity_awarded', 'unit_price', 'line_total', 'delivery_date')
    readonly_fields = ('line_total',)


class AuctionBidInline(admin.TabularInline):
    model = AuctionBid
    extra = 0
    fields = ('supplier', 'bid_number', 'bid_amount', 'bid_time', 'is_current_best', 'rank')
    readonly_fields = ('bid_time', 'is_current_best', 'rank')
    can_delete = False
    ordering = ['-bid_time']


# ==================== MAIN ADMINS ====================

@admin.register(RFxEvent)
class RFxEventAdmin(admin.ModelAdmin):
    list_display = (
        'rfx_number', 'title', 'event_type', 'status_display', 
        'submission_due_date', 'response_count', 'is_overdue_display',
        'is_auction'
    )
    list_filter = ('event_type', 'status', 'is_auction', 'is_confidential', 'created_at')
    search_fields = ('rfx_number', 'title', 'description', 'category', 'department')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    autocomplete_fields = ('currency', 'created_by', 'published_by', 'awarded_by')
    
    inlines = [RFxItemInline, SupplierInvitationInline, AuctionBidInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                ('rfx_number', 'event_type'),
                'title',
                'description',
                ('department', 'category'),
            )
        }),
        ('Status & Timeline', {
            'fields': (
                'status',
                ('publish_date', 'published_by'),
                ('submission_start_date', 'submission_due_date'),
                ('evaluation_due_date', 'award_date'),
            )
        }),
        ('Terms & Conditions', {
            'fields': (
                ('currency', 'payment_terms_days'),
                ('delivery_terms', 'delivery_location'),
                'delivery_date_required',
            )
        }),
        ('Technical Requirements', {
            'fields': (
                'technical_specifications',
                'quality_requirements',
                'compliance_requirements',
            ),
            'classes': ('collapse',)
        }),
        ('Evaluation Criteria', {
            'fields': (
                'evaluation_method',
                ('price_weight', 'technical_weight'),
            )
        }),
        ('Configuration', {
            'fields': (
                ('allow_partial_quotes', 'allow_alternate_quotes'),
                ('require_samples', 'is_confidential'),
            )
        }),
        ('Auction Settings', {
            'fields': (
                'is_auction',
                ('auction_start_date', 'auction_end_date'),
                ('auction_extension_minutes', 'auction_minimum_decrement'),
            ),
            'classes': ('collapse',)
        }),
        ('Award Information', {
            'fields': (
                'award_justification',
                ('total_awarded_value', 'awarded_by'),
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                ('created_by', 'created_at'),
                'updated_at',
                'notes',
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'publish_date', 'award_date')
    
    def status_display(self, obj):
        colors = {
            'DRAFT': 'gray',
            'PUBLISHED': 'blue',
            'IN_PROGRESS': 'green',
            'CLOSED': 'orange',
            'AWARDED': 'darkgreen',
            'CANCELLED': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def response_count(self, obj):
        count = obj.get_response_count()
        invited = obj.get_invited_count()
        if invited > 0:
            percentage = (count / invited) * 100
            color = 'green' if percentage >= 50 else 'orange' if percentage >= 25 else 'red'
            return format_html(
                '<span style="color: {};">{} / {} ({:.0f}%)</span>',
                color, count, invited, percentage
            )
        return f"{count} / {invited}"
    response_count.short_description = 'Responses'
    
    def is_overdue_display(self, obj):
        if obj.is_overdue():
            return format_html('<span style="color: red;">⚠ OVERDUE</span>')
        return '-'
    is_overdue_display.short_description = 'Overdue'
    
    actions = ['publish_rfx', 'close_rfx', 'cancel_rfx']
    
    def publish_rfx(self, request, queryset):
        count = 0
        for rfx in queryset.filter(status='DRAFT'):
            if rfx.publish(request.user):
                count += 1
        self.message_user(request, f'{count} RFx event(s) published.')
    publish_rfx.short_description = "Publish selected RFx events"
    
    def close_rfx(self, request, queryset):
        count = 0
        for rfx in queryset:
            if rfx.close():
                count += 1
        self.message_user(request, f'{count} RFx event(s) closed.')
    close_rfx.short_description = "Close selected RFx events"
    
    def cancel_rfx(self, request, queryset):
        updated = queryset.update(status='CANCELLED')
        self.message_user(request, f'{updated} RFx event(s) cancelled.')
    cancel_rfx.short_description = "Cancel selected RFx events"


@admin.register(RFxItem)
class RFxItemAdmin(admin.ModelAdmin):
    list_display = (
        'rfx_event', 'line_number', 'item_code', 'description_short',
        'quantity', 'unit_of_measure', 'estimated_unit_price', 'quote_count'
    )
    list_filter = ('is_mandatory', 'unit_of_measure', 'rfx_event__event_type')
    search_fields = ('item_code', 'description', 'rfx_event__rfx_number', 'part_number')
    autocomplete_fields = ('rfx_event',)
    ordering = ('rfx_event', 'line_number')
    
    fieldsets = (
        ('RFx & Line Info', {
            'fields': (
                'rfx_event',
                ('line_number', 'item_code'),
            )
        }),
        ('Description', {
            'fields': (
                'description',
                ('quantity', 'unit_of_measure'),
            )
        }),
        ('Technical Details', {
            'fields': (
                'technical_specifications',
                ('brand_preference', 'part_number'),
            )
        }),
        ('Pricing', {
            'fields': (
                ('estimated_unit_price', 'target_unit_price'),
            )
        }),
        ('Requirements', {
            'fields': (
                ('is_mandatory', 'delivery_date_required'),
                'attachment_url',
            )
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def quote_count(self, obj):
        count = obj.get_quote_count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    quote_count.short_description = 'Quotes'


@admin.register(SupplierInvitation)
class SupplierInvitationAdmin(admin.ModelAdmin):
    list_display = (
        'rfx_event', 'supplier', 'status_display', 'invited_date',
        'sent_date', 'viewed_date', 'responded_date'
    )
    list_filter = ('status', 'invited_date', 'sent_date')
    search_fields = ('rfx_event__rfx_number', 'supplier__name', 'supplier__code')
    autocomplete_fields = ('rfx_event', 'supplier', 'invited_by')
    date_hierarchy = 'invited_date'
    ordering = ('-invited_date',)
    
    fieldsets = (
        ('Invitation Details', {
            'fields': (
                ('rfx_event', 'supplier'),
                'status',
                'invitation_message',
            )
        }),
        ('Timeline', {
            'fields': (
                'invited_date',
                'sent_date',
                'viewed_date',
                'responded_date',
            )
        }),
        ('Decline Information', {
            'fields': ('decline_reason',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('invited_by',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('invited_date', 'sent_date', 'viewed_date', 'responded_date')
    
    def status_display(self, obj):
        colors = {
            'PENDING': 'gray',
            'SENT': 'blue',
            'VIEWED': 'orange',
            'RESPONDED': 'green',
            'DECLINED': 'red'
        }
        color = colors.get(obj.status, 'black')
        icon = {
            'PENDING': '⏸',
            'SENT': '📧',
            'VIEWED': '👁',
            'RESPONDED': '✓',
            'DECLINED': '✗'
        }.get(obj.status, '')
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    actions = ['mark_as_sent']
    
    def mark_as_sent(self, request, queryset):
        count = 0
        for invitation in queryset.filter(status='PENDING'):
            invitation.mark_as_sent()
            count += 1
        self.message_user(request, f'{count} invitation(s) marked as sent.')
    mark_as_sent.short_description = "Mark selected as sent"


@admin.register(SupplierQuote)
class SupplierQuoteAdmin(admin.ModelAdmin):
    list_display = (
        'quote_number', 'rfx_event', 'supplier', 'status_display',
        'total_amount', 'overall_score_display', 'submitted_date'
    )
    list_filter = ('status', 'submitted_date', 'rfx_event__event_type', 'is_auction_bid')
    search_fields = ('quote_number', 'rfx_event__rfx_number', 'supplier__name', 'supplier__code')
    autocomplete_fields = ('rfx_event', 'supplier', 'invitation', 'currency')
    date_hierarchy = 'submitted_date'
    ordering = ('-submitted_date',)
    
    inlines = [SupplierQuoteLineInline]
    
    fieldsets = (
        ('Quote Information', {
            'fields': (
                ('quote_number', 'quote_version'),
                ('rfx_event', 'supplier'),
                'invitation',
                'status',
            )
        }),
        ('Submission', {
            'fields': (
                ('submitted_date', 'submitted_by'),
            )
        }),
        ('Commercial Terms', {
            'fields': (
                ('currency', 'payment_terms_days'),
                ('delivery_terms', 'delivery_lead_time_days'),
            )
        }),
        ('Pricing', {
            'fields': (
                ('subtotal', 'tax_amount'),
                ('shipping_cost', 'other_charges'),
                'discount_amount',
                'total_amount',
            )
        }),
        ('Technical Response', {
            'fields': (
                'technical_proposal',
                'certifications',
                'references',
            ),
            'classes': ('collapse',)
        }),
        ('Evaluation', {
            'fields': (
                ('price_score', 'technical_score', 'overall_score'),
                'evaluator_comments',
            )
        }),
        ('Auction', {
            'fields': (
                ('is_auction_bid', 'auction_bid_time'),
                'previous_bid_amount',
            ),
            'classes': ('collapse',)
        }),
        ('Attachments & Notes', {
            'fields': (
                'attachment_files',
                'notes',
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('submitted_date', 'created_at', 'updated_at')
    
    def status_display(self, obj):
        colors = {
            'DRAFT': 'gray',
            'SUBMITTED': 'blue',
            'WITHDRAWN': 'orange',
            'ACCEPTED': 'green',
            'REJECTED': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def overall_score_display(self, obj):
        if obj.overall_score:
            score = float(obj.overall_score)
            color = 'green' if score >= 80 else 'orange' if score >= 60 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
                color, score
            )
        return '-'
    overall_score_display.short_description = 'Score'
    
    actions = ['calculate_totals', 'calculate_scores', 'accept_quotes', 'reject_quotes']
    
    def calculate_totals(self, request, queryset):
        for quote in queryset:
            quote.calculate_totals()
        self.message_user(request, f'{queryset.count()} quote(s) totals recalculated.')
    calculate_totals.short_description = "Recalculate quote totals"
    
    def calculate_scores(self, request, queryset):
        for quote in queryset:
            quote.calculate_scores()
        self.message_user(request, f'{queryset.count()} quote(s) scores recalculated.')
    calculate_scores.short_description = "Recalculate evaluation scores"
    
    def accept_quotes(self, request, queryset):
        updated = queryset.update(status='ACCEPTED')
        self.message_user(request, f'{updated} quote(s) accepted.')
    accept_quotes.short_description = "Accept selected quotes"
    
    def reject_quotes(self, request, queryset):
        updated = queryset.update(status='REJECTED')
        self.message_user(request, f'{updated} quote(s) rejected.')
    reject_quotes.short_description = "Reject selected quotes"


@admin.register(SupplierQuoteLine)
class SupplierQuoteLineAdmin(admin.ModelAdmin):
    list_display = (
        'quote', 'rfx_item_display', 'is_quoted', 'quantity',
        'unit_price', 'line_total_display', 'meets_specifications'
    )
    list_filter = ('is_quoted', 'meets_specifications', 'is_alternate')
    search_fields = ('quote__quote_number', 'quote__supplier__name', 'item_description')
    autocomplete_fields = ('quote', 'rfx_item')
    
    fieldsets = (
        ('Quote & Item', {
            'fields': (
                ('quote', 'rfx_item'),
                'is_quoted',
            )
        }),
        ('Quote Details', {
            'fields': (
                ('quantity', 'unit_price'),
                ('delivery_lead_time_days', 'delivery_date_offered'),
            )
        }),
        ('Item Details', {
            'fields': (
                'item_description',
                ('brand_offered', 'part_number_offered'),
                'is_alternate',
            )
        }),
        ('Technical Compliance', {
            'fields': (
                'meets_specifications',
                'specification_notes',
            )
        }),
        ('Evaluation', {
            'fields': (
                'technical_score',
                'evaluator_notes',
            ),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def rfx_item_display(self, obj):
        return f"Line {obj.rfx_item.line_number}: {obj.rfx_item.description[:30]}"
    rfx_item_display.short_description = 'RFx Item'
    
    def line_total_display(self, obj):
        total = obj.get_line_total()
        return format_html('<strong>{:.2f}</strong>', total)
    line_total_display.short_description = 'Line Total'


@admin.register(RFxAward)
class RFxAwardAdmin(admin.ModelAdmin):
    list_display = (
        'award_number', 'rfx_event', 'supplier', 'status_display',
        'award_amount', 'award_date', 'po_number'
    )
    list_filter = ('status', 'award_date', 'approved_date')
    search_fields = ('award_number', 'rfx_event__rfx_number', 'supplier__name', 'po_number')
    autocomplete_fields = ('rfx_event', 'supplier', 'quote', 'currency', 
                          'approved_by', 'po_created_by', 'created_by')
    date_hierarchy = 'award_date'
    ordering = ('-award_date',)
    
    inlines = [RFxAwardLineInline]
    
    fieldsets = (
        ('Award Information', {
            'fields': (
                ('award_number', 'status'),
                ('rfx_event', 'supplier'),
                'quote',
                ('award_date', 'award_amount', 'currency'),
            )
        }),
        ('Justification', {
            'fields': (
                'justification',
                'evaluation_summary',
            )
        }),
        ('Approval', {
            'fields': (
                ('approved_by', 'approved_date'),
            )
        }),
        ('Purchase Order', {
            'fields': (
                ('po_number', 'po_created_date'),
                'po_created_by',
            )
        }),
        ('Metadata', {
            'fields': (
                ('created_at', 'created_by'),
                'notes',
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'approved_date', 'po_created_date')
    
    def status_display(self, obj):
        colors = {
            'PENDING': 'orange',
            'APPROVED': 'green',
            'PO_CREATED': 'darkgreen',
            'CANCELLED': 'red'
        }
        color = colors.get(obj.status, 'black')
        icon = {
            'PENDING': '⏳',
            'APPROVED': '✓',
            'PO_CREATED': '📄',
            'CANCELLED': '✗'
        }.get(obj.status, '')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    actions = ['approve_awards']
    
    def approve_awards(self, request, queryset):
        count = 0
        for award in queryset.filter(status='PENDING'):
            if award.approve(request.user):
                count += 1
        self.message_user(request, f'{count} award(s) approved.')
    approve_awards.short_description = "Approve selected awards"


@admin.register(AuctionBid)
class AuctionBidAdmin(admin.ModelAdmin):
    list_display = (
        'rfx_event', 'supplier', 'bid_number', 'bid_amount',
        'bid_time', 'is_current_best_display', 'rank'
    )
    list_filter = ('is_valid', 'is_current_best', 'caused_extension', 'bid_time')
    search_fields = ('rfx_event__rfx_number', 'supplier__name')
    autocomplete_fields = ('rfx_event', 'supplier')
    date_hierarchy = 'bid_time'
    ordering = ('rfx_event', '-bid_time')
    
    fieldsets = (
        ('Bid Information', {
            'fields': (
                ('rfx_event', 'supplier'),
                ('bid_number', 'bid_amount'),
                'bid_time',
            )
        }),
        ('Status', {
            'fields': (
                ('is_valid', 'is_current_best'),
                'rank',
                'caused_extension',
            )
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('bid_time',)
    
    def is_current_best_display(self, obj):
        if obj.is_current_best:
            return format_html('<span style="color: green; font-weight: bold;">🏆 BEST</span>')
        return '-'
    is_current_best_display.short_description = 'Best Bid'


# Register autocomplete for searchable fields
@admin.register(RFxAwardLine)
class RFxAwardLineAdmin(admin.ModelAdmin):
    list_display = ('award', 'rfx_item', 'quantity_awarded', 'unit_price', 'line_total')
    list_filter = ('award__status',)
    search_fields = ('award__award_number', 'rfx_item__description')
    autocomplete_fields = ('award', 'rfx_item', 'quote_line')

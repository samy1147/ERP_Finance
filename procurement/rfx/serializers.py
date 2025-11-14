# procurement/serializers.py
from rest_framework import serializers
from .models import (
    RFxEvent, RFxItem, SupplierInvitation, SupplierQuote, SupplierQuoteLine,
    RFxAward, RFxAwardLine, AuctionBid
)
from ap.models import Supplier


class RFxItemSerializer(serializers.ModelSerializer):
    """Serializer for RFx Items"""
    quote_count = serializers.SerializerMethodField()
    best_quote_price = serializers.SerializerMethodField()
    
    class Meta:
        model = RFxItem
        fields = [
            'id', 'rfx_event', 'line_number', 'item_code', 'description',
            'quantity', 'unit_of_measure', 'technical_specifications',
            'brand_preference', 'part_number', 'estimated_unit_price',
            'target_unit_price', 'is_mandatory', 'delivery_date_required',
            'attachment_url', 'notes', 'created_at',
            'quote_count', 'best_quote_price'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_quote_count(self, obj):
        return obj.get_quote_count()
    
    def get_best_quote_price(self, obj):
        best_quote = obj.get_best_quote()
        return best_quote.unit_price if best_quote else None


class SupplierInvitationSerializer(serializers.ModelSerializer):
    """Serializer for Supplier Invitations"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.username', read_only=True)
    
    class Meta:
        model = SupplierInvitation
        fields = [
            'id', 'rfx_event', 'supplier', 'supplier_name', 'status',
            'invited_date', 'sent_date', 'viewed_date', 'responded_date',
            'invitation_message', 'decline_reason',
            'invited_by', 'invited_by_name'
        ]
        read_only_fields = ['id', 'invited_date', 'sent_date', 'viewed_date', 'responded_date']


class SupplierQuoteLineSerializer(serializers.ModelSerializer):
    """Serializer for Quote Line Items"""
    rfx_item_description = serializers.CharField(source='rfx_item.description', read_only=True)
    line_total = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierQuoteLine
        fields = [
            'id', 'quote', 'rfx_item', 'rfx_item_description', 'is_quoted',
            'quantity', 'unit_price', 'item_description', 'brand_offered',
            'part_number_offered', 'is_alternate', 'delivery_lead_time_days',
            'delivery_date_offered', 'meets_specifications', 'specification_notes',
            'technical_score', 'evaluator_notes', 'notes', 'line_total'
        ]
    
    def get_line_total(self, obj):
        return obj.get_line_total()


class SupplierQuoteSerializer(serializers.ModelSerializer):
    """Serializer for Supplier Quotes"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    rfx_number = serializers.CharField(source='rfx_event.rfx_number', read_only=True)
    rfx_title = serializers.CharField(source='rfx_event.title', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    quote_lines = SupplierQuoteLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = SupplierQuote
        fields = [
            'id', 'rfx_event', 'rfx_number', 'rfx_title', 'supplier', 'supplier_name',
            'invitation', 'quote_number', 'quote_version', 'status',
            'submitted_date', 'submitted_by', 'currency', 'currency_code',
            'payment_terms_days', 'delivery_terms', 'delivery_lead_time_days',
            'subtotal', 'tax_amount', 'shipping_cost', 'other_charges',
            'discount_amount', 'total_amount', 'technical_proposal',
            'certifications', 'references', 'price_score', 'technical_score',
            'overall_score', 'evaluator_comments', 'is_auction_bid',
            'auction_bid_time', 'previous_bid_amount', 'attachment_files',
            'notes', 'created_at', 'updated_at', 'quote_lines'
        ]
        read_only_fields = ['id', 'submitted_date', 'created_at', 'updated_at']


class RFxEventListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    response_count = serializers.SerializerMethodField()
    invited_count = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = RFxEvent
        fields = [
            'id', 'rfx_number', 'title', 'event_type', 'event_type_display',
            'status', 'status_display', 'submission_due_date', 'currency', 'currency_code',
            'is_auction', 'response_count', 'invited_count', 'is_open', 'is_overdue',
            'created_at'
        ]
    
    def get_response_count(self, obj):
        return obj.get_response_count()
    
    def get_invited_count(self, obj):
        return obj.get_invited_count()
    
    def get_is_open(self, obj):
        return obj.is_open_for_submission()
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()


class RFxEventDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with all fields and nested data"""
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    evaluation_method_display = serializers.CharField(source='get_evaluation_method_display', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    
    # Nested relationships
    items = RFxItemSerializer(many=True, read_only=True)
    invitations = SupplierInvitationSerializer(many=True, read_only=True)
    quotes = SupplierQuoteSerializer(many=True, read_only=True)
    
    # Statistics
    response_count = serializers.SerializerMethodField()
    invited_count = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = RFxEvent
        fields = [
            'id', 'rfx_number', 'title', 'event_type', 'event_type_display',
            'description', 'status', 'status_display', 'publish_date',
            'submission_start_date', 'submission_due_date', 'evaluation_due_date',
            'award_date', 'currency', 'currency_code', 'payment_terms_days',
            'delivery_terms', 'delivery_location', 'delivery_date_required',
            'technical_specifications', 'quality_requirements', 'compliance_requirements',
            'evaluation_method', 'evaluation_method_display', 'price_weight',
            'technical_weight', 'allow_partial_quotes', 'allow_alternate_quotes',
            'require_samples', 'is_confidential', 'is_auction', 'auction_start_date',
            'auction_end_date', 'auction_extension_minutes', 'auction_minimum_decrement',
            'award_justification', 'total_awarded_value', 'created_by',
            'created_at', 'updated_at', 'published_by', 'awarded_by',
            'department', 'category', 'notes',
            'items', 'invitations', 'quotes',
            'response_count', 'invited_count', 'is_open', 'is_overdue'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'publish_date', 'award_date']
    
    def get_response_count(self, obj):
        return obj.get_response_count()
    
    def get_invited_count(self, obj):
        return obj.get_invited_count()
    
    def get_is_open(self, obj):
        return obj.is_open_for_submission()
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()


class RFxEventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating RFx events"""
    
    class Meta:
        model = RFxEvent
        fields = [
            'rfx_number', 'title', 'event_type', 'description', 'status',
            'submission_start_date', 'submission_due_date', 'evaluation_due_date',
            'currency', 'payment_terms_days', 'delivery_terms', 'delivery_location',
            'delivery_date_required', 'technical_specifications', 'quality_requirements',
            'compliance_requirements', 'evaluation_method', 'price_weight',
            'technical_weight', 'allow_partial_quotes', 'allow_alternate_quotes',
            'require_samples', 'is_confidential', 'is_auction', 'auction_start_date',
            'auction_end_date', 'auction_extension_minutes', 'auction_minimum_decrement',
            'department', 'category', 'notes'
        ]
    
    def validate(self, data):
        """Custom validation"""
        # Validate weights sum to 100
        price_weight = data.get('price_weight', 70)
        tech_weight = data.get('technical_weight', 30)
        if price_weight + tech_weight != 100:
            raise serializers.ValidationError({
                'price_weight': 'Price weight and technical weight must sum to 100%'
            })
        
        # Validate dates
        if data.get('submission_start_date') and data.get('submission_due_date'):
            if data['submission_start_date'] >= data['submission_due_date']:
                raise serializers.ValidationError({
                    'submission_due_date': 'Submission due date must be after start date'
                })
        
        # Validate auction dates
        if data.get('is_auction'):
            if not data.get('auction_start_date') or not data.get('auction_end_date'):
                raise serializers.ValidationError({
                    'is_auction': 'Auction start and end dates are required for auction events'
                })
            if data['auction_start_date'] >= data['auction_end_date']:
                raise serializers.ValidationError({
                    'auction_end_date': 'Auction end date must be after start date'
                })
        
        return data


class RFxAwardLineSerializer(serializers.ModelSerializer):
    """Serializer for Award Line Items"""
    rfx_item_description = serializers.CharField(source='rfx_item.description', read_only=True)
    
    class Meta:
        model = RFxAwardLine
        fields = [
            'id', 'award', 'rfx_item', 'rfx_item_description', 'quote_line',
            'quantity_awarded', 'unit_price', 'line_total', 'delivery_date', 'notes'
        ]
        read_only_fields = ['id', 'line_total']


class RFxAwardSerializer(serializers.ModelSerializer):
    """Serializer for RFx Awards"""
    rfx_number = serializers.CharField(source='rfx_event.rfx_number', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    award_lines = RFxAwardLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = RFxAward
        fields = [
            'id', 'rfx_event', 'rfx_number', 'supplier', 'supplier_name',
            'quote', 'award_number', 'status', 'status_display', 'award_date',
            'award_amount', 'currency', 'currency_code', 'justification',
            'evaluation_summary', 'approved_by', 'approved_date',
            'po_number', 'po_created_date', 'po_created_by',
            'created_at', 'created_by', 'notes', 'award_lines'
        ]
        read_only_fields = ['id', 'created_at', 'approved_date', 'po_created_date']


class AuctionBidSerializer(serializers.ModelSerializer):
    """Serializer for Auction Bids"""
    rfx_number = serializers.CharField(source='rfx_event.rfx_number', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = AuctionBid
        fields = [
            'id', 'rfx_event', 'rfx_number', 'supplier', 'supplier_name',
            'bid_number', 'bid_amount', 'bid_time', 'is_valid',
            'is_current_best', 'rank', 'caused_extension', 'notes'
        ]
        read_only_fields = ['id', 'bid_time']


class QuoteComparisonSerializer(serializers.Serializer):
    """Serializer for side-by-side quote comparison"""
    rfx_event_id = serializers.IntegerField()
    rfx_number = serializers.CharField()
    rfx_title = serializers.CharField()
    item_count = serializers.IntegerField()
    quote_count = serializers.IntegerField()
    
    items = serializers.ListField()
    quotes = serializers.ListField()
    comparison_matrix = serializers.DictField()
    
    best_price_supplier = serializers.CharField(allow_null=True)
    best_technical_supplier = serializers.CharField(allow_null=True)
    best_overall_supplier = serializers.CharField(allow_null=True)

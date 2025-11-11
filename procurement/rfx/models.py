"""
Procurement Models - Sourcing / RFx
RFQ/RFP Events, Quotes, Awards, Auctions
"""
from django.db import models
from django.utils import timezone
from decimal import Decimal
from ap.models import Supplier


class RFxEvent(models.Model):
    """
    Request for Quote (RFQ) / Request for Proposal (RFP) Event
    Central entity for sourcing activities
    """
    EVENT_TYPES = [
        ('RFQ', 'Request for Quote'),
        ('RFP', 'Request for Proposal'),
        ('RFI', 'Request for Information'),
        ('ITB', 'Invitation to Bid'),
    ]
    
    EVENT_STATUSES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('IN_PROGRESS', 'In Progress'),
        ('CLOSED', 'Closed'),
        ('AWARDED', 'Awarded'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    EVALUATION_METHODS = [
        ('LOWEST_PRICE', 'Lowest Price'),
        ('BEST_VALUE', 'Best Value (Price + Quality)'),
        ('TECHNICAL_ONLY', 'Technical Evaluation Only'),
        ('TWO_ENVELOPE', 'Two Envelope (Technical then Price)'),
    ]
    
    # Basic Information
    rfx_number = models.CharField(max_length=50, unique=True, help_text="RFx reference number")
    title = models.CharField(max_length=255, help_text="RFx title/subject")
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES, default='RFQ')
    description = models.TextField(help_text="Detailed description of requirements")
    
    # Status & Timeline
    status = models.CharField(max_length=20, choices=EVENT_STATUSES, default='DRAFT')
    publish_date = models.DateTimeField(null=True, blank=True, help_text="Date when RFx is published to suppliers")
    submission_start_date = models.DateTimeField(help_text="When suppliers can start submitting")
    submission_due_date = models.DateTimeField(help_text="Quote submission deadline")
    evaluation_due_date = models.DateTimeField(null=True, blank=True, help_text="Internal evaluation deadline")
    award_date = models.DateTimeField(null=True, blank=True, help_text="Date of award decision")
    
    # Terms & Conditions
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, help_text="Currency for this RFx")
    payment_terms_days = models.IntegerField(default=30, help_text="Payment terms in days")
    delivery_terms = models.CharField(max_length=100, blank=True, help_text="Delivery terms (e.g., FOB, CIF)")
    delivery_location = models.CharField(max_length=255, blank=True, help_text="Delivery location/address")
    delivery_date_required = models.DateField(null=True, blank=True, help_text="Required delivery date")
    
    # Technical Requirements
    technical_specifications = models.TextField(blank=True, help_text="Technical specifications document")
    quality_requirements = models.TextField(blank=True, help_text="Quality standards required")
    compliance_requirements = models.TextField(blank=True, help_text="Compliance/regulatory requirements")
    
    # Evaluation Criteria
    evaluation_method = models.CharField(max_length=20, choices=EVALUATION_METHODS, default='LOWEST_PRICE')
    price_weight = models.DecimalField(max_digits=5, decimal_places=2, default=70, help_text="Weight % for price (0-100)")
    technical_weight = models.DecimalField(max_digits=5, decimal_places=2, default=30, help_text="Weight % for technical (0-100)")
    
    # Configuration
    allow_partial_quotes = models.BooleanField(default=True, help_text="Allow suppliers to quote on partial items")
    allow_alternate_quotes = models.BooleanField(default=False, help_text="Allow alternate/substitute items")
    require_samples = models.BooleanField(default=False, help_text="Require physical samples")
    is_confidential = models.BooleanField(default=False, help_text="Confidential RFx")
    
    # Auction Settings (Optional)
    is_auction = models.BooleanField(default=False, help_text="Enable reverse auction")
    auction_start_date = models.DateTimeField(null=True, blank=True)
    auction_end_date = models.DateTimeField(null=True, blank=True)
    auction_extension_minutes = models.IntegerField(default=5, help_text="Auto-extend auction by X minutes on last-minute bids")
    auction_minimum_decrement = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Minimum price decrement for bids")
    
    # Award Information
    awarded_to = models.ManyToManyField(Supplier, through='RFxAward', related_name='awarded_rfx_events')
    award_justification = models.TextField(blank=True, help_text="Justification for award decision")
    total_awarded_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='rfx_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='rfx_published')
    awarded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='rfx_awarded')
    
    # Department/Category
    department = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'procurement_rfx_event'
        ordering = ['-created_at']
        verbose_name = 'RFx Event'
        verbose_name_plural = 'RFx Events'
    
    def __str__(self):
        return f"{self.rfx_number} - {self.title}"
    
    def is_open_for_submission(self):
        """Check if RFx is currently open for supplier submissions"""
        now = timezone.now()
        return (
            self.status == 'PUBLISHED' and
            self.submission_start_date <= now <= self.submission_due_date
        )
    
    def is_overdue(self):
        """Check if submission deadline has passed"""
        return timezone.now() > self.submission_due_date and self.status not in ['CLOSED', 'AWARDED', 'CANCELLED']
    
    def get_response_count(self):
        """Get number of supplier responses received"""
        return self.quotes.filter(status='SUBMITTED').count()
    
    def get_invited_count(self):
        """Get number of invited suppliers"""
        return self.invitations.count()
    
    def publish(self, user):
        """Publish the RFx event to invited suppliers"""
        if self.status == 'DRAFT':
            self.status = 'PUBLISHED'
            self.publish_date = timezone.now()
            self.published_by = user
            self.save()
            return True
        return False
    
    def close(self):
        """Close the RFx event (after deadline)"""
        if self.status in ['PUBLISHED', 'IN_PROGRESS']:
            self.status = 'CLOSED'
            self.save()
            return True
        return False


class RFxItem(models.Model):
    """Line items/requirements for an RFx event"""
    rfx_event = models.ForeignKey(RFxEvent, on_delete=models.CASCADE, related_name='items')
    
    line_number = models.IntegerField(help_text="Line item number")
    item_code = models.CharField(max_length=50, blank=True, help_text="Item/SKU code")
    description = models.TextField(help_text="Item description/specifications")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, help_text="Quantity required")
    unit_of_measure = models.CharField(max_length=20, default='EA', help_text="Unit of measure (EA, KG, M, etc.)")
    
    # Technical Details
    technical_specifications = models.TextField(blank=True)
    brand_preference = models.CharField(max_length=100, blank=True, help_text="Preferred brand (if any)")
    part_number = models.CharField(max_length=100, blank=True, help_text="Manufacturer part number")
    
    # Estimated/Target Values
    estimated_unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Estimated unit price")
    target_unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Target/budget unit price")
    
    # Requirements
    is_mandatory = models.BooleanField(default=True, help_text="Mandatory item (cannot be excluded)")
    delivery_date_required = models.DateField(null=True, blank=True, help_text="Required delivery date for this item")
    
    # Attachments
    attachment_url = models.URLField(blank=True, help_text="Link to drawings/specs")
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'procurement_rfx_item'
        ordering = ['rfx_event', 'line_number']
        unique_together = ['rfx_event', 'line_number']
    
    def __str__(self):
        return f"{self.rfx_event.rfx_number} - Line {self.line_number}: {self.description[:50]}"
    
    def get_best_quote(self):
        """Get the best (lowest) quote for this item"""
        quotes = self.quote_lines.filter(
            quote__status='SUBMITTED'
        ).order_by('unit_price')
        return quotes.first() if quotes.exists() else None
    
    def get_quote_count(self):
        """Get number of quotes received for this item"""
        return self.quote_lines.filter(quote__status='SUBMITTED').count()


class SupplierInvitation(models.Model):
    """Invitation sent to suppliers for an RFx event"""
    INVITATION_STATUSES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('VIEWED', 'Viewed'),
        ('RESPONDED', 'Responded'),
        ('DECLINED', 'Declined'),
    ]
    
    rfx_event = models.ForeignKey(RFxEvent, on_delete=models.CASCADE, related_name='invitations')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='rfx_invitations')
    
    status = models.CharField(max_length=20, choices=INVITATION_STATUSES, default='PENDING')
    invited_date = models.DateTimeField(auto_now_add=True)
    sent_date = models.DateTimeField(null=True, blank=True)
    viewed_date = models.DateTimeField(null=True, blank=True)
    responded_date = models.DateTimeField(null=True, blank=True)
    
    invitation_message = models.TextField(blank=True, help_text="Custom message to supplier")
    decline_reason = models.TextField(blank=True, help_text="Reason if supplier declined")
    
    invited_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'procurement_supplier_invitation'
        unique_together = ['rfx_event', 'supplier']
        ordering = ['-invited_date']
    
    def __str__(self):
        return f"{self.rfx_event.rfx_number} - {self.supplier.name}"
    
    def mark_as_sent(self):
        """Mark invitation as sent"""
        self.status = 'SENT'
        self.sent_date = timezone.now()
        self.save()
    
    def mark_as_viewed(self):
        """Mark invitation as viewed by supplier"""
        if self.status == 'SENT':
            self.status = 'VIEWED'
            self.viewed_date = timezone.now()
            self.save()
    
    def mark_as_responded(self):
        """Mark invitation as responded"""
        self.status = 'RESPONDED'
        self.responded_date = timezone.now()
        self.save()


class SupplierQuote(models.Model):
    """Supplier's response/quote for an RFx event"""
    QUOTE_STATUSES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('WITHDRAWN', 'Withdrawn'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    
    rfx_event = models.ForeignKey(RFxEvent, on_delete=models.CASCADE, related_name='quotes')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='quotes')
    invitation = models.OneToOneField(SupplierInvitation, on_delete=models.SET_NULL, null=True, blank=True, related_name='quote')
    
    quote_number = models.CharField(max_length=50, unique=True, help_text="Quote reference number")
    quote_version = models.IntegerField(default=1, help_text="Version number (if revisions allowed)")
    status = models.CharField(max_length=20, choices=QUOTE_STATUSES, default='DRAFT')
    
    # Submission Details
    submitted_date = models.DateTimeField(null=True, blank=True)
    submitted_by = models.CharField(max_length=100, blank=True, help_text="Supplier contact who submitted")
    
    # Commercial Terms
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    payment_terms_days = models.IntegerField(help_text="Offered payment terms in days")
    delivery_terms = models.CharField(max_length=100, blank=True)
    delivery_lead_time_days = models.IntegerField(help_text="Delivery lead time in days")
    
    # Pricing
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    # Technical Response
    technical_proposal = models.TextField(blank=True, help_text="Technical proposal/response")
    certifications = models.TextField(blank=True, help_text="Relevant certifications")
    references = models.TextField(blank=True, help_text="Client references")
    
    # Evaluation Scores
    price_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Price evaluation score (0-100)")
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Technical evaluation score (0-100)")
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Overall weighted score")
    evaluator_comments = models.TextField(blank=True, help_text="Internal evaluation comments")
    
    # Auction (if applicable)
    is_auction_bid = models.BooleanField(default=False)
    auction_bid_time = models.DateTimeField(null=True, blank=True)
    previous_bid_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    # Attachments
    attachment_files = models.TextField(blank=True, help_text="JSON list of attachment file URLs")
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'procurement_supplier_quote'
        ordering = ['-submitted_date']
        unique_together = ['rfx_event', 'supplier', 'quote_version']
    
    def __str__(self):
        return f"{self.quote_number} - {self.supplier.name}"
    
    def submit(self):
        """Submit the quote"""
        if self.status == 'DRAFT':
            self.status = 'SUBMITTED'
            self.submitted_date = timezone.now()
            self.save()
            
            # Update invitation status
            if self.invitation:
                self.invitation.mark_as_responded()
            
            return True
        return False
    
    def calculate_totals(self):
        """Calculate quote totals from line items"""
        line_total = Decimal('0.00')
        
        for line in self.quote_lines.all():
            if line.unit_price and line.quantity:
                line_total += line.unit_price * line.quantity
        
        self.subtotal = line_total
        self.total_amount = (
            line_total + 
            (self.tax_amount or Decimal('0')) + 
            self.shipping_cost + 
            self.other_charges - 
            self.discount_amount
        )
        self.save()
        
        return self.total_amount
    
    def calculate_scores(self):
        """Calculate evaluation scores"""
        if not self.rfx_event:
            return
        
        # Price Score (inverse - lower price = higher score)
        all_quotes = SupplierQuote.objects.filter(
            rfx_event=self.rfx_event,
            status='SUBMITTED',
            total_amount__isnull=False
        ).order_by('total_amount')
        
        if all_quotes.exists() and self.total_amount:
            lowest_price = all_quotes.first().total_amount
            if lowest_price and lowest_price > 0:
                # Price score: 100 for lowest, scaled down for higher prices
                self.price_score = min(Decimal('100'), (lowest_price / self.total_amount) * 100)
        
        # Overall score (weighted)
        if self.price_score and self.technical_score:
            price_weight = self.rfx_event.price_weight / 100
            tech_weight = self.rfx_event.technical_weight / 100
            self.overall_score = (self.price_score * price_weight) + (self.technical_score * tech_weight)
        elif self.price_score:
            self.overall_score = self.price_score
        elif self.technical_score:
            self.overall_score = self.technical_score
        
        self.save()


class SupplierQuoteLine(models.Model):
    """Line items in a supplier's quote"""
    quote = models.ForeignKey(SupplierQuote, on_delete=models.CASCADE, related_name='quote_lines')
    rfx_item = models.ForeignKey(RFxItem, on_delete=models.CASCADE, related_name='quote_lines')
    
    # Quote Details
    is_quoted = models.BooleanField(default=True, help_text="Supplier is quoting this item")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, help_text="Quoted quantity")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Unit price")
    
    # Item Details (can differ from RFx if alternates allowed)
    item_description = models.TextField(blank=True, help_text="Supplier's item description")
    brand_offered = models.CharField(max_length=100, blank=True)
    part_number_offered = models.CharField(max_length=100, blank=True)
    is_alternate = models.BooleanField(default=False, help_text="Alternate/substitute item")
    
    # Lead Time
    delivery_lead_time_days = models.IntegerField(null=True, blank=True, help_text="Lead time for this item")
    delivery_date_offered = models.DateField(null=True, blank=True)
    
    # Technical Compliance
    meets_specifications = models.BooleanField(default=True)
    specification_notes = models.TextField(blank=True, help_text="Notes on spec compliance")
    
    # Evaluation
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    evaluator_notes = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'procurement_supplier_quote_line'
        unique_together = ['quote', 'rfx_item']
        ordering = ['rfx_item__line_number']
    
    def __str__(self):
        return f"{self.quote.quote_number} - Line {self.rfx_item.line_number}"
    
    def get_line_total(self):
        """Calculate line total"""
        if self.unit_price and self.quantity:
            return self.unit_price * self.quantity
        return Decimal('0.00')


class RFxAward(models.Model):
    """Award decision for an RFx event (can be split among multiple suppliers)"""
    AWARD_STATUSES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('PO_CREATED', 'PO Created'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    rfx_event = models.ForeignKey(RFxEvent, on_delete=models.CASCADE, related_name='awards')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    quote = models.ForeignKey(SupplierQuote, on_delete=models.SET_NULL, null=True, blank=True)
    
    award_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=AWARD_STATUSES, default='PENDING')
    
    # Award Details
    award_date = models.DateTimeField(default=timezone.now)
    award_amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    
    # Justification
    justification = models.TextField(help_text="Justification for awarding to this supplier")
    evaluation_summary = models.TextField(blank=True, help_text="Summary of evaluation")
    
    # Approval
    approved_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='awards_approved')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # PO Creation
    po_number = models.CharField(max_length=50, blank=True, help_text="Purchase Order number created from this award")
    po_created_date = models.DateTimeField(null=True, blank=True)
    po_created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_created')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='awards_created')
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'procurement_rfx_award'
        ordering = ['-award_date']
    
    def __str__(self):
        return f"{self.award_number} - {self.supplier.name}"
    
    def approve(self, user):
        """Approve the award"""
        if self.status == 'PENDING':
            self.status = 'APPROVED'
            self.approved_by = user
            self.approved_date = timezone.now()
            self.save()
            return True
        return False


class RFxAwardLine(models.Model):
    """Line items awarded to a supplier"""
    award = models.ForeignKey(RFxAward, on_delete=models.CASCADE, related_name='award_lines')
    rfx_item = models.ForeignKey(RFxItem, on_delete=models.CASCADE)
    quote_line = models.ForeignKey(SupplierQuoteLine, on_delete=models.SET_NULL, null=True, blank=True)
    
    quantity_awarded = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)
    
    delivery_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'procurement_rfx_award_line'
        unique_together = ['award', 'rfx_item']
    
    def __str__(self):
        return f"{self.award.award_number} - Line {self.rfx_item.line_number}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate line total
        if self.quantity_awarded and self.unit_price:
            self.line_total = self.quantity_awarded * self.unit_price
        super().save(*args, **kwargs)


class AuctionBid(models.Model):
    """Real-time auction bids for reverse auctions"""
    rfx_event = models.ForeignKey(RFxEvent, on_delete=models.CASCADE, related_name='auction_bids')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='auction_bids')
    
    bid_number = models.IntegerField(help_text="Sequential bid number for this auction")
    bid_amount = models.DecimalField(max_digits=14, decimal_places=2, help_text="Total bid amount")
    bid_time = models.DateTimeField(default=timezone.now)
    
    is_valid = models.BooleanField(default=True, help_text="Bid meets all requirements")
    is_current_best = models.BooleanField(default=False, help_text="Currently the best (lowest) bid")
    
    rank = models.IntegerField(null=True, blank=True, help_text="Current rank among all bids")
    
    # Auto-extension tracking
    caused_extension = models.BooleanField(default=False, help_text="This bid caused auction extension")
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'procurement_auction_bid'
        ordering = ['rfx_event', 'bid_time']
        unique_together = ['rfx_event', 'supplier', 'bid_number']
    
    def __str__(self):
        return f"{self.rfx_event.rfx_number} - Bid #{self.bid_number} by {self.supplier.name}"

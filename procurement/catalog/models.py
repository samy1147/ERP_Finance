# catalog/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class UnitOfMeasure(models.Model):
    """
    Unit of Measure (UoM) master data
    Examples: PCS, KG, M, L, BOX, CASE, etc.
    """
    code = models.CharField(max_length=10, unique=True, help_text="UoM code (e.g., PCS, KG)")
    name = models.CharField(max_length=50, help_text="Full name (e.g., Pieces, Kilograms)")
    description = models.TextField(blank=True, null=True)
    
    # UoM Type
    UOM_TYPES = [
        ('QUANTITY', 'Quantity'),
        ('WEIGHT', 'Weight'),
        ('LENGTH', 'Length'),
        ('AREA', 'Area'),
        ('VOLUME', 'Volume'),
        ('TIME', 'Time'),
        ('TEMPERATURE', 'Temperature'),
        ('OTHER', 'Other'),
    ]
    uom_type = models.CharField(max_length=20, choices=UOM_TYPES, default='QUANTITY')
    
    # Conversion (optional - for future use)
    base_uom = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                  help_text="Base UoM for conversion")
    conversion_factor = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True,
                                           help_text="Multiply by this to convert to base UoM")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Unit of Measure'
        verbose_name_plural = 'Units of Measure'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class CatalogCategory(models.Model):
    """
    Hierarchical catalog categories (UNSPSC-style)
    Example: IT Equipment > Computers > Laptops
    """
    code = models.CharField(max_length=20, unique=True, help_text="Category code (e.g., UNSPSC)")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Hierarchical structure
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='children')
    level = models.IntegerField(default=0, help_text="0=top level, 1=sub, etc.")
    full_path = models.CharField(max_length=500, blank=True, help_text="Full category path")
    
    # UNSPSC codes (optional)
    unspsc_segment = models.CharField(max_length=2, blank=True, help_text="UNSPSC Segment (2 digits)")
    unspsc_family = models.CharField(max_length=2, blank=True, help_text="UNSPSC Family (2 digits)")
    unspsc_class = models.CharField(max_length=2, blank=True, help_text="UNSPSC Class (2 digits)")
    unspsc_commodity = models.CharField(max_length=2, blank=True, help_text="UNSPSC Commodity (2 digits)")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Catalog Category'
        verbose_name_plural = 'Catalog Categories'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Calculate level and full path
        if self.parent:
            self.level = self.parent.level + 1
            self.full_path = f"{self.parent.full_path} > {self.name}"
        else:
            self.level = 0
            self.full_path = self.name
        super().save(*args, **kwargs)
    
    def get_full_code(self):
        """Get full UNSPSC code if available"""
        if all([self.unspsc_segment, self.unspsc_family, self.unspsc_class, self.unspsc_commodity]):
            return f"{self.unspsc_segment}{self.unspsc_family}{self.unspsc_class}{self.unspsc_commodity}"
        return self.code


class CatalogItem(models.Model):
    """
    Master catalog of items/services available for procurement
    """
    # Identification
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    item_code = models.CharField(max_length=50, db_index=True, help_text="Internal item code")
    name = models.CharField(max_length=200)
    short_description = models.CharField(max_length=500, blank=True)
    long_description = models.TextField(blank=True)
    
    # Classification
    category = models.ForeignKey(CatalogCategory, on_delete=models.PROTECT, related_name='items')
    
    ITEM_TYPES = [
        ('GOODS', 'Goods'),
        ('SERVICE', 'Service'),
        ('SOFTWARE', 'Software'),
        ('SUBSCRIPTION', 'Subscription'),
        ('CONSUMABLE', 'Consumable'),
        ('ASSET', 'Asset'),
    ]
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='GOODS')
    
    # Measurement
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    
    # Product Details
    manufacturer = models.CharField(max_length=100, blank=True)
    manufacturer_part_number = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    
    # Specifications
    specifications = models.JSONField(default=dict, blank=True,
                                     help_text="Technical specifications as JSON")
    attributes = models.JSONField(default=dict, blank=True,
                                 help_text="Custom attributes as JSON")
    
    # Images & Documents
    image_url = models.URLField(max_length=500, blank=True)
    datasheet_url = models.URLField(max_length=500, blank=True)
    additional_images = models.JSONField(default=list, blank=True,
                                        help_text="List of image URLs")
    
    # Pricing (base/list price)
    list_price = models.DecimalField(max_digits=15, decimal_places=2, 
                                     validators=[MinValueValidator(Decimal('0.00'))])
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    
    # Supplier Information
    preferred_supplier = models.ForeignKey('ap.Supplier', on_delete=models.SET_NULL, 
                                          null=True, blank=True,
                                          related_name='preferred_catalog_items')
    
    # Procurement Settings
    minimum_order_quantity = models.DecimalField(max_digits=15, decimal_places=3, 
                                                 default=Decimal('1.000'))
    order_multiple = models.DecimalField(max_digits=15, decimal_places=3, 
                                        default=Decimal('1.000'),
                                        help_text="Order must be in multiples of this")
    lead_time_days = models.IntegerField(default=0, help_text="Standard lead time in days")
    
    # Tax & Accounting
    is_taxable = models.BooleanField(default=True)
    tax_category = models.CharField(max_length=50, blank=True)
    gl_account_code = models.CharField(max_length=50, blank=True, 
                                       help_text="Default GL account for this item")
    
    # Status & Control
    is_active = models.BooleanField(default=True)
    is_purchasable = models.BooleanField(default=True)
    is_restricted = models.BooleanField(default=False, 
                                       help_text="Requires special approval")
    restriction_notes = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  related_name='created_catalog_items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sku']
        verbose_name = 'Catalog Item'
        verbose_name_plural = 'Catalog Items'
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['item_code']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    def get_effective_price(self, quantity=1, supplier=None):
        """
        Get effective price considering price tiers
        """
        # Check for supplier-specific price tiers
        if supplier:
            price_tiers = self.supplier_price_tiers.filter(
                supplier=supplier,
                is_active=True,
                valid_from__lte=timezone.now().date()
            ).filter(
                models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=timezone.now().date())
            ).filter(
                min_quantity__lte=quantity
            ).order_by('-min_quantity').first()
            
            if price_tiers:
                return price_tiers.unit_price
        
        return self.list_price


class SupplierPriceTier(models.Model):
    """
    Supplier-specific pricing with quantity breaks
    Supports volume discounts and special pricing agreements
    """
    catalog_item = models.ForeignKey(CatalogItem, on_delete=models.CASCADE,
                                    related_name='supplier_price_tiers')
    supplier = models.ForeignKey('ap.Supplier', on_delete=models.CASCADE,
                                related_name='price_tiers')
    
    # Pricing
    min_quantity = models.DecimalField(max_digits=15, decimal_places=3,
                                      validators=[MinValueValidator(Decimal('0.001'))],
                                      help_text="Minimum quantity for this price tier")
    unit_price = models.DecimalField(max_digits=15, decimal_places=2,
                                    validators=[MinValueValidator(Decimal('0.00'))])
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    
    # Discounts
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'),
                                          validators=[MinValueValidator(Decimal('0.00')),
                                                     MaxValueValidator(Decimal('100.00'))])
    
    # Validity
    valid_from = models.DateField(default=timezone.now)
    valid_to = models.DateField(null=True, blank=True)
    
    # Delivery
    lead_time_days = models.IntegerField(default=0)
    
    # Reference
    supplier_item_code = models.CharField(max_length=50, blank=True)
    supplier_quote_reference = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['catalog_item', 'supplier', 'min_quantity']
        verbose_name = 'Supplier Price Tier'
        verbose_name_plural = 'Supplier Price Tiers'
        unique_together = [['catalog_item', 'supplier', 'min_quantity', 'valid_from']]
    
    def __str__(self):
        return f"{self.catalog_item.sku} - {self.supplier.name} - Qty {self.min_quantity}+"
    
    def is_valid_today(self):
        """Check if price tier is currently valid"""
        today = timezone.now().date()
        if self.valid_from > today:
            return False
        if self.valid_to and self.valid_to < today:
            return False
        return self.is_active


class FrameworkAgreement(models.Model):
    """
    Blanket/Framework agreements with suppliers
    Master contract for recurring purchases with pre-negotiated terms
    """
    # Agreement Identification
    agreement_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    AGREEMENT_TYPES = [
        ('BLANKET', 'Blanket Purchase Agreement'),
        ('FRAMEWORK', 'Framework Agreement'),
        ('CONTRACT', 'Master Service Agreement'),
        ('RATE_CARD', 'Rate Card Agreement'),
    ]
    agreement_type = models.CharField(max_length=20, choices=AGREEMENT_TYPES, default='FRAMEWORK')
    
    # Parties
    supplier = models.ForeignKey('ap.Supplier', on_delete=models.PROTECT,
                                related_name='framework_agreements')
    department = models.CharField(max_length=100, blank=True)
    buyer_name = models.CharField(max_length=100, blank=True)
    
    # Validity Period
    start_date = models.DateField()
    end_date = models.DateField()
    auto_renew = models.BooleanField(default=False)
    renewal_notice_days = models.IntegerField(default=30,
                                             help_text="Days before expiry to trigger renewal notice")
    
    # Financial Limits
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    total_contract_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                              help_text="Total agreement value limit")
    annual_value_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                            help_text="Annual spending limit")
    per_order_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                         help_text="Maximum value per call-off order")
    
    # Usage Tracking
    total_committed = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'),
                                         help_text="Total amount committed via call-offs")
    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'),
                                     help_text="Total amount actually spent")
    
    # Terms & Conditions
    payment_terms = models.CharField(max_length=100, blank=True)
    delivery_terms = models.CharField(max_length=100, blank=True)
    warranty_terms = models.TextField(blank=True)
    special_terms = models.TextField(blank=True)
    
    # Pricing
    PRICING_TYPES = [
        ('FIXED', 'Fixed Prices'),
        ('TIERED', 'Volume Tiered'),
        ('DISCOUNT', 'Discount from List'),
        ('RATE_CARD', 'Rate Card'),
        ('MARKET', 'Market Based'),
    ]
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPES, default='FIXED')
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'),
                                          help_text="Overall discount % from catalog prices")
    
    # Price Adjustment
    allow_price_adjustment = models.BooleanField(default=False)
    price_adjustment_frequency = models.CharField(max_length=20, blank=True,
                                                 help_text="e.g., Quarterly, Annual")
    price_adjustment_method = models.CharField(max_length=100, blank=True,
                                              help_text="e.g., CPI-based, Fixed %")
    
    # Documents
    contract_document_url = models.URLField(max_length=500, blank=True)
    attachments = models.JSONField(default=list, blank=True,
                                  help_text="List of attachment URLs")
    
    # Approval & Status
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('EXPIRED', 'Expired'),
        ('TERMINATED', 'Terminated'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_frameworks')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)
    
    # Notifications
    notify_on_expiry = models.BooleanField(default=True)
    notify_on_limit_reached = models.BooleanField(default=True)
    limit_warning_percent = models.IntegerField(default=80,
                                               validators=[MinValueValidator(0), MaxValueValidator(100)],
                                               help_text="Warn when % of limit is reached")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  related_name='created_frameworks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Framework Agreement'
        verbose_name_plural = 'Framework Agreements'
    
    def __str__(self):
        return f"{self.agreement_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.agreement_number:
            self.agreement_number = self.generate_agreement_number()
        super().save(*args, **kwargs)
    
    def generate_agreement_number(self):
        """Generate unique agreement number"""
        from django.db.models import Max
        today = timezone.now().date()
        prefix = f"FA-{today.strftime('%Y%m%d')}"
        
        last_agreement = FrameworkAgreement.objects.filter(
            agreement_number__startswith=prefix
        ).aggregate(Max('agreement_number'))
        
        if last_agreement['agreement_number__max']:
            last_num = int(last_agreement['agreement_number__max'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:03d}"
    
    def is_active(self):
        """Check if agreement is currently active"""
        if self.status != 'ACTIVE':
            return False
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
    
    def is_expiring_soon(self, days=30):
        """Check if agreement expires within specified days"""
        if not self.is_active():
            return False
        days_until_expiry = (self.end_date - timezone.now().date()).days
        return 0 <= days_until_expiry <= days
    
    def get_remaining_value(self):
        """Calculate remaining contract value"""
        if not self.total_contract_value:
            return None
        return self.total_contract_value - self.total_committed
    
    def get_utilization_percent(self):
        """Calculate % of contract value utilized"""
        if not self.total_contract_value or self.total_contract_value == 0:
            return 0
        return (self.total_committed / self.total_contract_value) * 100
    
    def is_limit_warning(self):
        """Check if limit warning threshold reached"""
        utilization = self.get_utilization_percent()
        return utilization >= self.limit_warning_percent
    
    def activate(self, approved_by):
        """Activate the framework agreement"""
        self.status = 'ACTIVE'
        self.approved_by = approved_by
        self.approved_date = timezone.now()
        self.save()
    
    def suspend(self, reason=''):
        """Suspend the framework agreement"""
        self.status = 'SUSPENDED'
        if reason:
            self.special_terms += f"\n[SUSPENDED: {reason}]"
        self.save()
    
    def terminate(self, reason=''):
        """Terminate the framework agreement"""
        self.status = 'TERMINATED'
        self.termination_date = timezone.now().date()
        self.termination_reason = reason
        self.save()


class FrameworkItem(models.Model):
    """
    Items/services covered under a framework agreement
    Links catalog items to framework with specific terms
    """
    framework = models.ForeignKey(FrameworkAgreement, on_delete=models.CASCADE,
                                 related_name='framework_items')
    catalog_item = models.ForeignKey(CatalogItem, on_delete=models.PROTECT,
                                    related_name='framework_items')
    
    # Item-specific terms
    line_number = models.IntegerField(help_text="Line number in framework")
    
    # Pricing
    unit_price = models.DecimalField(max_digits=15, decimal_places=2,
                                    validators=[MinValueValidator(Decimal('0.00'))])
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    
    # Quantity Limits
    minimum_order_quantity = models.DecimalField(max_digits=15, decimal_places=3,
                                                null=True, blank=True)
    maximum_order_quantity = models.DecimalField(max_digits=15, decimal_places=3,
                                                null=True, blank=True)
    total_quantity_limit = models.DecimalField(max_digits=15, decimal_places=3,
                                              null=True, blank=True,
                                              help_text="Total quantity allowed under framework")
    
    # Usage Tracking
    quantity_ordered = models.DecimalField(max_digits=15, decimal_places=3,
                                          default=Decimal('0.000'))
    quantity_received = models.DecimalField(max_digits=15, decimal_places=3,
                                           default=Decimal('0.000'))
    total_value_ordered = models.DecimalField(max_digits=15, decimal_places=2,
                                             default=Decimal('0.00'))
    
    # Delivery
    lead_time_days = models.IntegerField(default=0)
    delivery_location = models.CharField(max_length=200, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['framework', 'line_number']
        verbose_name = 'Framework Item'
        verbose_name_plural = 'Framework Items'
        unique_together = [['framework', 'catalog_item']]
    
    def __str__(self):
        return f"{self.framework.agreement_number} - {self.catalog_item.sku}"
    
    def get_remaining_quantity(self):
        """Calculate remaining quantity available"""
        if not self.total_quantity_limit:
            return None
        return self.total_quantity_limit - self.quantity_ordered
    
    def is_quantity_available(self, quantity):
        """Check if requested quantity is available"""
        if not self.total_quantity_limit:
            return True
        remaining = self.get_remaining_quantity()
        return remaining >= quantity


class CallOffOrder(models.Model):
    """
    Call-off purchase orders against framework agreements
    Individual releases from blanket/framework agreements
    """
    # Order Identification
    calloff_number = models.CharField(max_length=50, unique=True)
    framework = models.ForeignKey(FrameworkAgreement, on_delete=models.PROTECT,
                                 related_name='calloff_orders')
    
    # Order Details
    order_date = models.DateField(default=timezone.now)
    requested_delivery_date = models.DateField()
    delivery_location = models.CharField(max_length=200)
    
    # Requester
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='calloff_requests')
    department = models.CharField(max_length=100, blank=True)
    cost_center = models.CharField(max_length=50, blank=True)
    
    # Financial
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Status
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('SENT_TO_SUPPLIER', 'Sent to Supplier'),
        ('CONFIRMED', 'Confirmed by Supplier'),
        ('IN_DELIVERY', 'In Delivery'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Approval
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_calloffs')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Delivery
    actual_delivery_date = models.DateField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    
    # Reference
    supplier_po_number = models.CharField(max_length=50, blank=True,
                                         help_text="Supplier's PO confirmation number")
    internal_reference = models.CharField(max_length=50, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Cancellation
    cancelled_date = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  related_name='created_calloffs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date', '-calloff_number']
        verbose_name = 'Call-Off Order'
        verbose_name_plural = 'Call-Off Orders'
    
    def __str__(self):
        return f"{self.calloff_number} - {self.framework.agreement_number}"
    
    def save(self, *args, **kwargs):
        if not self.calloff_number:
            self.calloff_number = self.generate_calloff_number()
        super().save(*args, **kwargs)
    
    def generate_calloff_number(self):
        """Generate unique call-off number"""
        from django.db.models import Max
        today = timezone.now().date()
        prefix = f"CO-{today.strftime('%Y%m%d')}"
        
        last_calloff = CallOffOrder.objects.filter(
            calloff_number__startswith=prefix
        ).aggregate(Max('calloff_number'))
        
        if last_calloff['calloff_number__max']:
            last_num = int(last_calloff['calloff_number__max'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:03d}"
    
    def calculate_totals(self):
        """Calculate order totals from lines"""
        lines = self.lines.all()
        self.subtotal = sum(line.get_line_total() for line in lines)
        # Tax calculation would go here
        self.total_amount = self.subtotal + self.tax_amount
        self.save()
        return self.total_amount
    
    def submit(self):
        """Submit call-off for approval"""
        if self.status == 'DRAFT':
            self.status = 'SUBMITTED'
            self.save()
            return True
        return False
    
    def approve(self, approved_by):
        """Approve call-off order"""
        if self.status == 'SUBMITTED':
            self.status = 'APPROVED'
            self.approved_by = approved_by
            self.approved_date = timezone.now()
            self.save()
            
            # Update framework commitment
            self.framework.total_committed += self.total_amount
            self.framework.save()
            
            return True
        return False
    
    def send_to_supplier(self):
        """Mark as sent to supplier"""
        if self.status == 'APPROVED':
            self.status = 'SENT_TO_SUPPLIER'
            self.save()
            return True
        return False
    
    def complete(self):
        """Mark call-off as completed"""
        if self.status in ['CONFIRMED', 'IN_DELIVERY']:
            self.status = 'COMPLETED'
            self.actual_delivery_date = timezone.now().date()
            
            # Update framework spent amount
            self.framework.total_spent += self.total_amount
            self.framework.save()
            
            self.save()
            return True
        return False
    
    def cancel(self, reason=''):
        """Cancel call-off order"""
        if self.status not in ['COMPLETED', 'CANCELLED']:
            old_status = self.status
            self.status = 'CANCELLED'
            self.cancelled_date = timezone.now()
            self.cancellation_reason = reason
            self.save()
            
            # Reverse framework commitment if was approved
            if old_status in ['APPROVED', 'SENT_TO_SUPPLIER', 'CONFIRMED', 'IN_DELIVERY']:
                self.framework.total_committed -= self.total_amount
                self.framework.save()
            
            return True
        return False


class CallOffLine(models.Model):
    """
    Line items in a call-off order
    """
    calloff = models.ForeignKey(CallOffOrder, on_delete=models.CASCADE,
                               related_name='lines')
    framework_item = models.ForeignKey(FrameworkItem, on_delete=models.PROTECT,
                                      related_name='calloff_lines')
    
    line_number = models.IntegerField()
    
    # Item Details
    catalog_item = models.ForeignKey(CatalogItem, on_delete=models.PROTECT)
    description = models.CharField(max_length=200)
    
    # Quantity & Pricing
    quantity = models.DecimalField(max_digits=15, decimal_places=3,
                                  validators=[MinValueValidator(Decimal('0.001'))])
    unit_price = models.DecimalField(max_digits=15, decimal_places=2,
                                    validators=[MinValueValidator(Decimal('0.00'))])
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Delivery
    requested_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    quantity_received = models.DecimalField(max_digits=15, decimal_places=3,
                                           default=Decimal('0.000'))
    
    # Status
    is_received = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['calloff', 'line_number']
        verbose_name = 'Call-Off Line'
        verbose_name_plural = 'Call-Off Lines'
        unique_together = [['calloff', 'line_number']]
    
    def __str__(self):
        return f"{self.calloff.calloff_number} - Line {self.line_number}"
    
    def save(self, *args, **kwargs):
        # Calculate line total
        self.line_total = self.get_line_total()
        super().save(*args, **kwargs)
    
    def get_line_total(self):
        """Calculate line total"""
        return self.quantity * self.unit_price
    
    def receive(self, quantity):
        """Record receipt of goods"""
        self.quantity_received += quantity
        if self.quantity_received >= self.quantity:
            self.is_received = True
            self.actual_delivery_date = timezone.now().date()
        
        # Update framework item usage
        self.framework_item.quantity_received += quantity
        self.framework_item.save()
        
        self.save()

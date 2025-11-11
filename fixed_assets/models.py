"""
Asset Management Models

Handles:
- Asset registers, categories, and locations
- Capitalization, transfers, and disposals
- Depreciation calculations and posting
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import Currency
from segment.models import XX_Segment


# Country choices (matching core.models TaxRate)
COUNTRY_CHOICES = [
    ("AE", "United Arab Emirates"),
    ("SA", "Saudi Arabia"),
    ("EG", "Egypt"),
    ("IN", "India"),
]


class AssetCategory(models.Model):
    """Asset categories for classification"""
    DEPRECIATION_METHODS = [
        ('STRAIGHT_LINE', 'Straight Line'),
        ('DECLINING_BALANCE', 'Declining Balance'),
        ('UNITS_OF_PRODUCTION', 'Units of Production'),
        ('SUM_OF_YEARS', 'Sum of Years Digits'),
    ]
    
    code = models.CharField(max_length=20, unique=True, help_text="Category code (e.g., COMP, FURN)")
    name = models.CharField(max_length=100, help_text="Category name")
    description = models.TextField(blank=True)
    
    # Category classification
    major = models.CharField(max_length=100, blank=True, help_text="Major category classification")
    minor = models.CharField(max_length=100, blank=True, help_text="Minor category classification")
    
    # Default depreciation settings
    depreciation_method = models.CharField(max_length=20, choices=DEPRECIATION_METHODS, default='STRAIGHT_LINE')
    useful_life_years = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                            help_text="Default useful life in years")
    min_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'),
                                    validators=[MinValueValidator(Decimal('0.00'))],
                                    help_text="Minimum value for capitalization")
    
    # GL Account mappings
    asset_account = models.ForeignKey(XX_Segment, on_delete=models.PROTECT, related_name='asset_categories_asset',
                                      null=True, blank=True, help_text="Default asset GL account")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_asset_categories')
    
    class Meta:
        db_table = 'assets_category'
        verbose_name = 'Asset Category'
        verbose_name_plural = 'Asset Categories'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class AssetLocation(models.Model):
    """Physical locations where assets are kept"""
    code = models.CharField(max_length=20, unique=True, help_text="Location code")
    name = models.CharField(max_length=100, help_text="Location name")
    description = models.TextField(blank=True)
    
    # Address details
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, blank=True)
    
    # Location hierarchy
    parent_location = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='sub_locations')
    
    # Custodian/Responsible person
    custodian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='asset_locations_custodian')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assets_location'
        verbose_name = 'Asset Location'
        verbose_name_plural = 'Asset Locations'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Asset(models.Model):
    """Main asset register"""
    STATUS_CHOICES = [
        ('CIP', 'cip'),
        ('CAPITALIZED', 'capitalized'),
        ('RETIRED', 'Retired'),
    ]
    
    # Asset identification
    asset_number = models.CharField(max_length=50, unique=True, help_text="Unique asset number")
    name = models.CharField(max_length=255, help_text="Asset name/description")
    description = models.TextField(blank=True)
    serial_number = models.CharField(max_length=100, blank=True, help_text="Serial/VIN number")
    
    # Classification
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name='assets')
    location = models.ForeignKey(AssetLocation, on_delete=models.PROTECT, related_name='assets')
    
    # Financial details
    acquisition_date = models.DateField(help_text="Date asset was acquired")
    acquisition_cost = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)],
                                          help_text="Original acquisition cost")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='assets')
    
    # Depreciation parameters
    depreciation_method = models.CharField(max_length=20, choices=AssetCategory.DEPRECIATION_METHODS)
    useful_life_years = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)])
    salvage_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'),
                                       validators=[MinValueValidator(0)])
    depreciation_start_date = models.DateField(help_text="Date to start calculating depreciation")
    
    # Current status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    capitalization_date = models.DateField(null=True, blank=True, help_text="Date asset was capitalized")
    
    # GL Account assignments (can override category defaults)
    asset_account = models.ForeignKey(XX_Segment, on_delete=models.PROTECT, related_name='assets_asset',
                                     help_text="Asset GL account")
    accumulated_depreciation_account = models.ForeignKey(XX_Segment, on_delete=models.PROTECT,
                                                         related_name='assets_accum_dep',
                                                         help_text="Accumulated depreciation account")
    depreciation_expense_account = models.ForeignKey(XX_Segment, on_delete=models.PROTECT,
                                                     related_name='assets_dep_exp',
                                                     help_text="Depreciation expense account")
    
    # Computed values (cached for performance)
    total_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_book_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    last_depreciation_date = models.DateField(null=True, blank=True)
    
    # Disposal information
    disposal_date = models.DateField(null=True, blank=True)
    disposal_method = models.CharField(max_length=50, blank=True, choices=[
        ('SALE', 'Sale'),
        ('SCRAP', 'Scrap'),
        ('DONATION', 'Donation'),
        ('TRADE_IN', 'Trade-In'),
        ('OTHER', 'Other'),
    ])
    disposal_proceeds = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    disposal_notes = models.TextField(blank=True)
    
    # References
    purchase_order = models.CharField(max_length=50, blank=True)
    supplier = models.ForeignKey('ap.Supplier', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='assets_supplied')
    
    # Source tracking - to prevent duplicate asset creation
    SOURCE_CHOICES = [
        ('MANUAL', 'Manual Entry'),
        ('AP_INVOICE', 'AP Invoice'),
        ('GRN', 'Goods Receipt Note'),
        ('PO', 'Purchase Order'),
    ]
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='MANUAL',
                                   help_text="Source of asset creation")
    ap_invoice = models.ForeignKey('ap.APInvoice', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_assets',
                                   help_text="AP Invoice that created this asset (if applicable)")
    ap_invoice_line = models.IntegerField(null=True, blank=True,
                                          help_text="Line number in AP Invoice")
    grn = models.ForeignKey('receiving.GoodsReceipt', on_delete=models.SET_NULL, null=True, blank=True,
                           related_name='created_assets',
                           help_text="GRN that created this asset (if applicable)")
    grn_line = models.ForeignKey('receiving.GRNLine', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='created_asset',
                                 help_text="GRN Line that created this asset")
    
    # Journal entries
    capitalization_journal = models.ForeignKey('finance.JournalEntry', on_delete=models.SET_NULL, 
                                              null=True, blank=True, related_name='capitalized_assets')
    disposal_journal = models.ForeignKey('finance.JournalEntry', on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='disposed_assets')
    
    # Tracking
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_assets')
    
    class Meta:
        db_table = 'assets_asset'
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        ordering = ['-acquisition_date', 'asset_number']
        indexes = [
            models.Index(fields=['asset_number']),
            models.Index(fields=['status']),
            models.Index(fields=['category', 'location']),
        ]
    
    def __str__(self):
        return f"{self.asset_number} - {self.name}"
    
    def calculate_depreciable_amount(self):
        """Calculate the amount to be depreciated"""
        return self.acquisition_cost - self.salvage_value
    
    def update_net_book_value(self):
        """Update the net book value"""
        self.net_book_value = self.acquisition_cost - self.total_depreciation
        return self.net_book_value
    
    @classmethod
    def check_source_already_converted(cls, source_type, ap_invoice_id=None, ap_invoice_line=None, 
                                       grn_line_id=None):
        """
        Check if a source (AP Invoice line or GRN line) has already been converted to an asset.
        
        Args:
            source_type: 'AP_INVOICE' or 'GRN'
            ap_invoice_id: ID of AP Invoice (if source_type is AP_INVOICE)
            ap_invoice_line: Line number in AP Invoice
            grn_line_id: ID of GRN Line (if source_type is GRN)
        
        Returns:
            dict with 'exists' boolean and 'asset' if it exists
        """
        if source_type == 'AP_INVOICE' and ap_invoice_id and ap_invoice_line is not None:
            existing = cls.objects.filter(
                source_type='AP_INVOICE',
                ap_invoice_id=ap_invoice_id,
                ap_invoice_line=ap_invoice_line
            ).first()
            
            if existing:
                return {
                    'exists': True,
                    'asset': existing,
                    'message': f'This AP Invoice line has already been converted to asset: {existing.asset_number}'
                }
        
        elif source_type == 'GRN' and grn_line_id:
            existing = cls.objects.filter(
                source_type='GRN',
                grn_line_id=grn_line_id
            ).first()
            
            if existing:
                return {
                    'exists': True,
                    'asset': existing,
                    'message': f'This GRN line has already been converted to asset: {existing.asset_number}'
                }
        
        return {'exists': False, 'asset': None, 'message': None}


class AssetTransfer(models.Model):
    """Track asset transfers between locations"""
    APPROVAL_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='transfers')
    
    transfer_date = models.DateField()
    from_location = models.ForeignKey(AssetLocation, on_delete=models.PROTECT, related_name='transfers_from')
    to_location = models.ForeignKey(AssetLocation, on_delete=models.PROTECT, related_name='transfers_to')
    
    reason = models.TextField(help_text="Reason for transfer")
    notes = models.TextField(blank=True)
    
    # Approval workflow
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='PENDING')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='asset_transfers_requested')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='asset_transfers_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assets_transfer'
        verbose_name = 'Asset Transfer'
        verbose_name_plural = 'Asset Transfers'
        ordering = ['-transfer_date']
    
    def __str__(self):
        return f"{self.asset.asset_number}: {self.from_location.code} → {self.to_location.code} on {self.transfer_date}"


class DepreciationSchedule(models.Model):
    """Monthly depreciation schedule entries"""
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='depreciation_schedules')
    
    period_date = models.DateField(help_text="Month/period for this depreciation")
    period = models.ForeignKey('periods.FiscalPeriod', on_delete=models.PROTECT, null=True, blank=True, related_name='depreciation_schedules', help_text="Fiscal period for this depreciation")
    depreciation_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Running totals
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2)
    net_book_value = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Posting information
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)
    journal_entry = models.ForeignKey('finance.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='depreciation_entries')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_depreciation_schedules')
    
    class Meta:
        db_table = 'assets_depreciation_schedule'
        verbose_name = 'Depreciation Schedule'
        verbose_name_plural = 'Depreciation Schedules'
        ordering = ['asset', 'period_date']
        unique_together = ['asset', 'period_date']
        indexes = [
            models.Index(fields=['period_date', 'is_posted']),
        ]
    
    def __str__(self):
        return f"{self.asset.asset_number} - {self.period_date.strftime('%Y-%m')}: {self.depreciation_amount}"


class AssetMaintenance(models.Model):
    """Track asset maintenance and repairs"""
    MAINTENANCE_TYPES = [
        ('PREVENTIVE', 'Preventive Maintenance'),
        ('CORRECTIVE', 'Corrective Maintenance'),
        ('REPAIR', 'Repair'),
        ('INSPECTION', 'Inspection'),
        ('UPGRADE', 'Upgrade'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_records')
    
    maintenance_date = models.DateField()
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    description = models.TextField(help_text="Description of maintenance performed")
    
    # Cost tracking
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='asset_maintenance')
    is_capitalized = models.BooleanField(default=False, help_text="Should this cost be capitalized to asset?")
    
    # Vendor information
    vendor_name = models.CharField(max_length=255, blank=True)
    vendor_invoice = models.CharField(max_length=100, blank=True)
    
    # Downtime tracking
    downtime_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                        help_text="Hours asset was unavailable")
    
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='maintenance_performed')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assets_maintenance'
        verbose_name = 'Asset Maintenance'
        verbose_name_plural = 'Asset Maintenance Records'
        ordering = ['-maintenance_date']
    
    def __str__(self):
        return f"{self.asset.asset_number} - {self.maintenance_type} on {self.maintenance_date}"


class AssetDocument(models.Model):
    """Store asset-related documents"""
    DOCUMENT_TYPES = [
        ('INVOICE', 'Purchase Invoice'),
        ('WARRANTY', 'Warranty Document'),
        ('MANUAL', 'User Manual'),
        ('CERTIFICATE', 'Certificate'),
        ('PHOTO', 'Photo'),
        ('INSURANCE', 'Insurance Document'),
        ('OTHER', 'Other'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='documents')
    
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    file = models.FileField(upload_to='asset_documents/%Y/%m/', blank=True, null=True)
    file_url = models.URLField(blank=True, help_text="External URL if document is stored elsewhere")
    
    document_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='uploaded_asset_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assets_document'
        verbose_name = 'Asset Document'
        verbose_name_plural = 'Asset Documents'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.asset.asset_number} - {self.title}"


class AssetConfiguration(models.Model):
    """Configuration settings for asset management"""
    # Singleton pattern - only one record should exist
    singleton_id = models.BooleanField(default=True, unique=True, 
                                      help_text="Ensures only one configuration record exists")
    
    # Capitalization threshold
    minimum_capitalization_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('1000.00'),
        validators=[MinValueValidator(0)],
        help_text="Minimum amount for an asset to be capitalized (items below this are expensed)"
    )
    base_currency = models.ForeignKey(
        Currency, 
        on_delete=models.PROTECT, 
        related_name='asset_config_base_currency',
        null=True,
        blank=True,
        help_text="Base currency for the minimum capitalization amount"
    )
    
    # Auto-numbering settings
    auto_generate_asset_number = models.BooleanField(default=True, 
                                                     help_text="Automatically generate asset numbers")
    asset_number_prefix = models.CharField(max_length=10, default='ASSET-',
                                          help_text="Prefix for auto-generated asset numbers")
    next_asset_number = models.IntegerField(default=1,
                                           help_text="Next sequential number for asset numbering")
    
    # Depreciation settings
    auto_calculate_depreciation = models.BooleanField(default=True,
                                                      help_text="Automatically calculate depreciation monthly")
    depreciation_posting_day = models.IntegerField(default=1, 
                                                   validators=[MinValueValidator(1)],
                                                   help_text="Day of month to post depreciation (1-28)")
    
    # Approval settings
    require_capitalization_approval = models.BooleanField(default=False,
                                                         help_text="Require approval before capitalizing assets")
    require_disposal_approval = models.BooleanField(default=True,
                                                    help_text="Require approval before disposing assets")
    
    # Audit fields
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='updated_asset_configs')
    
    class Meta:
        db_table = 'assets_configuration'
        verbose_name = 'Asset Configuration'
        verbose_name_plural = 'Asset Configuration'
    
    def __str__(self):
        return f"Asset Configuration (Min Amount: {self.minimum_capitalization_amount})"
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration"""
        config, created = cls.objects.get_or_create(singleton_id=True)
        return config
    
    def save(self, *args, **kwargs):
        """Override save to ensure singleton pattern"""
        self.singleton_id = True
        super().save(*args, **kwargs)


class AssetRetirement(models.Model):
    """Track asset retirements/disposals"""
    RETIREMENT_TYPES = [
        ('SALE', 'Sale'),
        ('SCRAP', 'Scrap'),
        ('DONATION', 'Donation'),
        ('TRADE_IN', 'Trade-In'),
        ('LOSS', 'Loss/Theft'),
        ('TRANSFER_OUT', 'Transfer Out'),
        ('OTHER', 'Other'),
    ]
    
    APPROVAL_STATUS = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='retirements')
    
    retirement_date = models.DateField(help_text="Date of retirement")
    retirement_type = models.CharField(max_length=20, choices=RETIREMENT_TYPES)
    
    # Financial details
    net_book_value_at_retirement = models.DecimalField(max_digits=15, decimal_places=2,
                                                       help_text="NBV at retirement date")
    disposal_proceeds = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'),
                                           help_text="Proceeds from disposal")
    disposal_costs = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'),
                                        help_text="Costs incurred for disposal")
    gain_loss = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'),
                                    help_text="Gain or loss on disposal")
    
    # Buyer/recipient information
    buyer_recipient = models.CharField(max_length=255, blank=True, help_text="Who received the asset")
    sale_invoice_number = models.CharField(max_length=100, blank=True)
    
    reason = models.TextField(help_text="Reason for retirement")
    notes = models.TextField(blank=True)
    
    # Approval workflow
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='DRAFT')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='retirement_submissions')
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='retirement_approvals')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # GL Posting
    is_posted = models.BooleanField(default=False)
    journal_entry = models.ForeignKey('finance.JournalEntry', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='asset_retirements')
    posted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_retirements')
    
    class Meta:
        db_table = 'assets_retirement'
        verbose_name = 'Asset Retirement'
        verbose_name_plural = 'Asset Retirements'
        ordering = ['-retirement_date']
    
    def __str__(self):
        return f"{self.asset.asset_number} - {self.retirement_type} on {self.retirement_date}"
    
    def calculate_gain_loss(self):
        """Calculate gain or loss on disposal"""
        net_proceeds = self.disposal_proceeds - self.disposal_costs
        self.gain_loss = net_proceeds - self.net_book_value_at_retirement
        return self.gain_loss


class AssetAdjustment(models.Model):
    """Track adjustments to asset cost or depreciation"""
    ADJUSTMENT_TYPES = [
        ('COST', 'Cost Adjustment'),
        ('USEFUL_LIFE', 'Useful Life Adjustment'),
        ('DEPRECIATION', 'Manual Depreciation Adjustment'),
        ('RECATEGORIZE', 'Recategorization'),
    ]
    
    APPROVAL_STATUS = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='adjustments')
    
    adjustment_date = models.DateField()
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    
    # Cost adjustments
    old_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    new_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    cost_difference = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Useful life adjustments
    old_useful_life = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    new_useful_life = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Manual depreciation adjustments
    depreciation_adjustment_amount = models.DecimalField(max_digits=15, decimal_places=2, 
                                                        null=True, blank=True,
                                                        help_text="Amount to adjust depreciation by")
    
    # Recategorization
    old_category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='adjustments_from')
    new_category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='adjustments_to')
    
    reason = models.TextField(help_text="Reason for adjustment")
    notes = models.TextField(blank=True)
    
    # Approval workflow
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='DRAFT')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='adjustment_submissions')
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='adjustment_approvals')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # GL Posting (if applicable)
    is_posted = models.BooleanField(default=False)
    journal_entry = models.ForeignKey('finance.JournalEntry', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='asset_adjustments')
    posted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_adjustments')
    
    class Meta:
        db_table = 'assets_adjustment'
        verbose_name = 'Asset Adjustment'
        verbose_name_plural = 'Asset Adjustments'
        ordering = ['-adjustment_date']
    
    def __str__(self):
        return f"{self.asset.asset_number} - {self.adjustment_type} on {self.adjustment_date}"


class AssetApproval(models.Model):
    """Track approval requests for asset operations"""
    OPERATION_TYPES = [
        ('CAPITALIZE', 'Capitalization'),
        ('RETIRE', 'Retirement'),
        ('ADJUST', 'Adjustment'),
        ('TRANSFER', 'Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='approval_requests')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    
    # Related records (polymorphic relationship)
    retirement = models.ForeignKey(AssetRetirement, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='approval_requests')
    adjustment = models.ForeignKey(AssetAdjustment, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='approval_requests')
    transfer = models.ForeignKey(AssetTransfer, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='approval_requests')
    
    # Approval details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='asset_approval_requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    request_notes = models.TextField(blank=True)
    
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='asset_approval_reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assets_approval'
        verbose_name = 'Asset Approval'
        verbose_name_plural = 'Asset Approvals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'operation_type']),
        ]
    
    def __str__(self):
        return f"{self.operation_type} - {self.asset.asset_number} ({self.status})"

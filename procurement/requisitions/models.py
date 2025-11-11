"""
Purchase Requisition (PR) models for ERP Finance system.

Features:
- PR header with cost center, project, business justification
- PR lines with need-by dates, catalog item references
- State machine: Draft → Submitted → Approved → Converted
- Auto-catalog suggestion based on item descriptions
- Split by vendor capability for PO conversion
- Budget check integration (pre-commit validation)
- Approval workflow integration
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import date
from decimal import Decimal


class CostCenter(models.Model):
    """
    Cost Centers for departmental budgeting and expense tracking.
    """
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_cost_centers'
    )
    is_active = models.BooleanField(default=True)
    
    # Budget tracking
    annual_budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'requisition_costcenter'
        ordering = ['code']
        verbose_name = 'Cost Center'
        verbose_name_plural = 'Cost Centers'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_total_committed(self):
        """Calculate total committed amount (approved PRs + open POs)."""
        from django.db.models import Sum, Q
        
        # PRs that are approved but not yet converted
        pr_total = self.pr_headers.filter(
            status__in=['APPROVED']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Open POs
        # TODO: Add PO model integration when implemented
        # po_total = self.po_headers.filter(
        #     status__in=['APPROVED', 'DISPATCHED', 'PARTIALLY_RECEIVED']
        # ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        return pr_total
    
    def get_available_budget(self):
        """Calculate available budget (annual - committed - actual)."""
        committed = self.get_total_committed()
        # TODO: Add actual spending from AP invoices
        actual = Decimal('0.00')
        return self.annual_budget - committed - actual


class Project(models.Model):
    """
    Projects for capital expenditures and project-based purchasing.
    """
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    project_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_projects'
    )
    
    # Budget and dates
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('PLANNING', 'Planning'),
        ('ACTIVE', 'Active'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANNING'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'requisition_project'
        ordering = ['code']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_total_committed(self):
        """Calculate total committed amount for this project."""
        from django.db.models import Sum
        
        pr_total = self.pr_headers.filter(
            status__in=['APPROVED']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        return pr_total
    
    def get_available_budget(self):
        """Calculate available budget."""
        committed = self.get_total_committed()
        actual = Decimal('0.00')  # TODO: Add actual spending
        return self.budget - committed - actual


class PRHeader(models.Model):
    """
    Purchase Requisition Header.
    
    Represents a request to purchase goods or services.
    Follows state machine: Draft → Submitted → Approved → Converted
    """
    
    # Document identification
    pr_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        editable=False
    )
    
    # Dates
    pr_date = models.DateField(default=date.today)
    required_date = models.DateField(
        help_text="Date by which items are needed"
    )
    
    # Requestor and organization
    requestor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='purchase_requisitions'
    )
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.PROTECT,
        related_name='pr_headers',
        null=True,
        blank=True
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name='pr_headers',
        null=True,
        blank=True,
        help_text="For capital expenditures or project-based purchasing"
    )
    
    # Purpose and justification
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    business_justification = models.TextField(
        blank=True,
        help_text="Explain why this purchase is necessary"
    )
    
    # Priority
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='NORMAL'
    )
    
    # PR Type (Categorized Goods, Uncategorized Goods, or Services)
    PR_TYPE_CHOICES = [
        ('CATEGORIZED_GOODS', 'Categorized Goods'),
        ('UNCATEGORIZED_GOODS', 'Uncategorized Goods'),
        ('SERVICES', 'Services'),
    ]
    pr_type = models.CharField(
        max_length=30,
        choices=PR_TYPE_CHOICES,
        default='UNCATEGORIZED_GOODS',
        help_text="Type of purchase requisition: Categorized Goods, Uncategorized Goods, or Services"
    )
    
    # State machine
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CONVERTED', 'Converted to PO'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )
    
    # Workflow tracking
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_prs'
    )
    
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_prs'
    )
    
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_prs'
    )
    rejection_reason = models.TextField(blank=True)
    
    converted_at = models.DateTimeField(null=True, blank=True)
    converted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_prs'
    )
    
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_prs'
    )
    cancellation_reason = models.TextField(blank=True)
    
    # Financial totals
    currency = models.ForeignKey(
        'core.Currency',
        on_delete=models.PROTECT,
        related_name='pr_headers'
    )
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Budget check
    budget_check_passed = models.BooleanField(default=False)
    budget_check_message = models.TextField(blank=True)
    budget_checked_at = models.DateTimeField(null=True, blank=True)
    
    # Auto-catalog suggestion
    catalog_suggestions_generated = models.BooleanField(default=False)
    
    # Vendor split capability
    can_split_by_vendor = models.BooleanField(
        default=True,
        help_text="Allow splitting this PR into multiple POs by vendor"
    )
    
    # Notes
    internal_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_prs'
    )
    
    class Meta:
        db_table = 'requisition_prheader'
        ordering = ['-pr_date', '-pr_number']
        verbose_name = 'Purchase Requisition'
        verbose_name_plural = 'Purchase Requisitions'
        indexes = [
            models.Index(fields=['status', 'pr_date']),
            models.Index(fields=['cost_center', 'status']),
            models.Index(fields=['project', 'status']),
        ]
    
    def __str__(self):
        return f"PR-{self.pr_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Generate PR number if new
        if not self.pr_number:
            self.pr_number = self._generate_pr_number()
        
        # Recalculate totals
        self.recalculate_totals()
        
        super().save(*args, **kwargs)
    
    def _generate_pr_number(self):
        """Generate unique PR number: PR-YYYYMM-NNNN"""
        from django.db.models import Max
        import re
        
        today = timezone.now()
        prefix = f"PR-{today.strftime('%Y%m')}"
        
        # Get the last PR number for this month
        last_pr = PRHeader.objects.filter(
            pr_number__startswith=prefix
        ).aggregate(Max('pr_number'))['pr_number__max']
        
        if last_pr:
            # Extract the sequence number
            match = re.search(r'-(\d+)$', last_pr)
            if match:
                sequence = int(match.group(1)) + 1
            else:
                sequence = 1
        else:
            sequence = 1
        
        return f"{prefix}-{sequence:04d}"
    
    def recalculate_totals(self):
        """Recalculate financial totals from lines."""
        from django.db.models import Sum
        
        # Skip if this is a new unsaved PR
        if not self.pk:
            return
        
        lines = self.lines.all()
        
        self.subtotal = sum(
            line.get_line_total() for line in lines
        ) or Decimal('0.00')
        
        self.tax_amount = sum(
            line.tax_amount for line in lines
        ) or Decimal('0.00')
        
        self.total_amount = self.subtotal + self.tax_amount
    
    def submit(self, user):
        """Submit PR for approval."""
        if self.status != 'DRAFT':
            raise ValueError("Only draft PRs can be submitted")
        
        if not self.lines.exists():
            raise ValueError("Cannot submit PR without line items")
        
        # Perform budget check
        self.check_budget()
        
        self.status = 'SUBMITTED'
        self.submitted_at = timezone.now()
        self.submitted_by = user
        self.save()
        
        # Trigger approval workflow
        from procurement.approvals.models import ApprovalWorkflow
        
        # Find active workflow for PRHeader
        workflow = ApprovalWorkflow.objects.filter(
            document_type='requisitions.PRHeader',
            is_active=True
        ).first()
        
        if workflow:
            # Calculate total amount in base currency
            total_amount = self.total_amount
            
            # Initiate approval process
            workflow.initiate_approval(
                document=self,
                amount=total_amount,
                requested_by=user
            )
        
        return True
    
    def approve(self, user):
        """Approve PR."""
        if self.status != 'SUBMITTED':
            raise ValueError("Only submitted PRs can be approved")
        
        # Re-check budget
        if not self.budget_check_passed:
            self.check_budget()
            if not self.budget_check_passed:
                raise ValueError(f"Budget check failed: {self.budget_check_message}")
        
        self.status = 'APPROVED'
        self.approved_at = timezone.now()
        self.approved_by = user
        self.save()
        
        return True
    
    def on_approved(self):
        """Callback when approval workflow completes successfully."""
        # Get the user who approved (from the approval workflow)
        from django.contrib.auth.models import User
        approver = User.objects.get(id=2)  # Default to admin in dev mode
        
        if self.status == 'SUBMITTED':
            self.status = 'APPROVED'
            self.approved_at = timezone.now()
            self.approved_by = approver
            self.save()
    
    def reject(self, user, reason):
        """Reject PR."""
        if self.status != 'SUBMITTED':
            raise ValueError("Only submitted PRs can be rejected")
        
        self.status = 'REJECTED'
        self.rejected_at = timezone.now()
        self.rejected_by = user
        self.rejection_reason = reason
        self.save()
        
        return True
    
    def cancel(self, user, reason):
        """Cancel PR."""
        if self.status in ['CONVERTED', 'CANCELLED']:
            raise ValueError(f"Cannot cancel PR with status {self.status}")
        
        self.status = 'CANCELLED'
        self.cancelled_at = timezone.now()
        self.cancelled_by = user
        self.cancellation_reason = reason
        self.save()
        
        return True
    
    def mark_converted(self, user):
        """Mark PR as converted to PO."""
        if self.status != 'APPROVED':
            raise ValueError("Only approved PRs can be converted")
        
        self.status = 'CONVERTED'
        self.converted_at = timezone.now()
        self.converted_by = user
        self.save()
        
        return True
    
    def check_budget(self):
        """
        Check if budget is available for this PR.
        
        Sets budget_check_passed and budget_check_message.
        """
        messages = []
        passed = True
        
        # Check cost center budget
        if self.cost_center:
            available = self.cost_center.get_available_budget()
            if available < self.total_amount:
                passed = False
                messages.append(
                    f"Cost center {self.cost_center.code} has insufficient budget. "
                    f"Required: {self.total_amount}, Available: {available}"
                )
        
        # Check project budget
        if self.project:
            available = self.project.get_available_budget()
            if available < self.total_amount:
                passed = False
                messages.append(
                    f"Project {self.project.code} has insufficient budget. "
                    f"Required: {self.total_amount}, Available: {available}"
                )
        
        if passed:
            messages.append("Budget check passed")
        
        self.budget_check_passed = passed
        self.budget_check_message = "\n".join(messages)
        self.budget_checked_at = timezone.now()
        
        return passed
    
    def generate_catalog_suggestions(self):
        """
        Generate catalog item suggestions for lines without catalog items.
        
        Uses text matching on item descriptions to suggest catalog items.
        """
        from procurement.catalog.models import CatalogItem
        from django.db.models import Q
        
        suggestions_count = 0
        
        for line in self.lines.filter(catalog_item__isnull=True):
            if not line.item_description:
                continue
            
            # Simple text search in catalog
            # TODO: Implement more sophisticated matching (ML, fuzzy search)
            keywords = line.item_description.lower().split()[:5]  # First 5 words
            
            query = Q()
            for keyword in keywords:
                if len(keyword) > 3:  # Skip short words
                    query |= Q(name__icontains=keyword)
                    query |= Q(description__icontains=keyword)
            
            if query:
                suggestions = CatalogItem.objects.filter(
                    query,
                    is_active=True
                ).distinct()[:5]
                
                if suggestions.exists():
                    # Store suggestions in line
                    line.suggested_catalog_items = [
                        {
                            'id': item.id,
                            'name': item.name,
                            'sku': item.sku,
                            'unit_price': str(item.list_price),
                        }
                        for item in suggestions
                    ]
                    line.save()
                    suggestions_count += 1
        
        self.catalog_suggestions_generated = True
        self.save()
        
        return suggestions_count
    
    def split_by_vendor(self):
        """
        Split PR lines by vendor for PO conversion.
        
        Returns a dict mapping suppliers to their line items.
        """
        if not self.can_split_by_vendor:
            raise ValueError("This PR cannot be split by vendor")
        
        vendor_lines = {}
        
        for line in self.lines.all():
            supplier = line.suggested_supplier
            if not supplier:
                # Lines without supplier go to None key
                supplier_key = None
            else:
                supplier_key = supplier.id
            
            if supplier_key not in vendor_lines:
                vendor_lines[supplier_key] = {
                    'supplier': supplier,
                    'lines': []
                }
            
            vendor_lines[supplier_key]['lines'].append(line)
        
        return vendor_lines


class PRLine(models.Model):
    """
    Purchase Requisition Line Item.
    
    Represents individual items or services requested in a PR.
    """
    
    pr_header = models.ForeignKey(
        PRHeader,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    
    line_number = models.PositiveIntegerField()
    
    # Item identification
    item_description = models.CharField(max_length=500)
    specifications = models.TextField(
        blank=True,
        help_text="Detailed specifications or requirements"
    )
    
    # Catalog reference
    catalog_item = models.ForeignKey(
        'catalog.CatalogItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pr_lines'
    )
    
    # Item Categorization Status
    ITEM_TYPE_CHOICES = [
        ('CATEGORIZED', 'Categorized - Linked to Catalog'),
        ('NON_CATEGORIZED', 'Non-Categorized - Free Text'),
    ]
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        default='NON_CATEGORIZED',
        help_text="Whether item is linked to catalog or is free text"
    )
    
    # Auto-catalog suggestions (JSON field)
    suggested_catalog_items = models.JSONField(
        default=list,
        blank=True,
        help_text="AI/system-suggested catalog items"
    )
    
    # Quantity and unit
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    unit_of_measure = models.ForeignKey(
        'catalog.UnitOfMeasure',
        on_delete=models.PROTECT,
        related_name='pr_lines'
    )
    
    # Pricing
    estimated_unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000')
    )
    
    # Tax
    tax_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Tax code (e.g., VAT-STANDARD, GST-5)"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tax rate in percentage"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Dates
    need_by_date = models.DateField(
        help_text="Date by which this item is needed"
    )
    
    # Suggested supplier (for split by vendor)
    suggested_supplier = models.ForeignKey(
        'ap.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suggested_pr_lines'
    )
    
    # Account coding
    gl_account = models.CharField(
        max_length=50,
        blank=True,
        help_text="GL account code for this expense"
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Conversion tracking
    conversion_status = models.CharField(
        max_length=20,
        choices=[
            ('NOT_CONVERTED', 'Not Converted'),
            ('PARTIALLY_CONVERTED', 'Partially Converted'),
            ('FULLY_CONVERTED', 'Fully Converted'),
        ],
        default='NOT_CONVERTED',
        help_text="Track conversion status of this PR line"
    )
    quantity_converted = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Quantity already converted to PO"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'requisition_prline'
        ordering = ['pr_header', 'line_number']
        verbose_name = 'PR Line'
        verbose_name_plural = 'PR Lines'
        unique_together = [['pr_header', 'line_number']]
        indexes = [
            models.Index(fields=['catalog_item']),
            models.Index(fields=['suggested_supplier']),
        ]
    
    def __str__(self):
        return f"{self.pr_header.pr_number} - Line {self.line_number}"
    
    def save(self, *args, **kwargs):
        # Auto-assign line number if new
        if not self.line_number:
            last_line = PRLine.objects.filter(
                pr_header=self.pr_header
            ).order_by('-line_number').first()
            
            self.line_number = (last_line.line_number + 10) if last_line else 10
        
        # Auto-set item_type based on catalog_item presence
        if self.catalog_item:
            self.item_type = 'CATEGORIZED'
        else:
            self.item_type = 'NON_CATEGORIZED'
        
        # Calculate tax amount
        line_total = self.get_line_total()
        self.tax_amount = (line_total * self.tax_rate / Decimal('100')).quantize(
            Decimal('0.01')
        )
        
        super().save(*args, **kwargs)
        
        # Update header totals
        if self.pr_header_id:
            self.pr_header.recalculate_totals()
            self.pr_header.save()
    
    def delete(self, *args, **kwargs):
        pr_header = self.pr_header
        super().delete(*args, **kwargs)
        
        # Update header totals after deletion
        pr_header.recalculate_totals()
        pr_header.save()
    
    def get_line_total(self):
        """Calculate line total (quantity × unit price)."""
        return (self.quantity * self.estimated_unit_price).quantize(
            Decimal('0.01')
        )
    
    def get_line_total_with_tax(self):
        """Calculate line total including tax."""
        return self.get_line_total() + self.tax_amount
    
    @property
    def quantity_remaining(self):
        """Calculate quantity not yet converted to PO."""
        return self.quantity - self.quantity_converted
    
    @property
    def is_fully_converted(self):
        """Check if this line is fully converted to PO."""
        return self.quantity_converted >= self.quantity
    
    def update_conversion_status(self):
        """Update conversion status based on quantity converted."""
        if self.quantity_converted <= 0:
            self.conversion_status = 'NOT_CONVERTED'
        elif self.quantity_converted >= self.quantity:
            self.conversion_status = 'FULLY_CONVERTED'
        else:
            self.conversion_status = 'PARTIALLY_CONVERTED'
        self.save()


class PRToPOLineMapping(models.Model):
    """
    Many-to-Many mapping between PR Lines and PO Lines.
    
    This model tracks the relationship between Purchase Requisition lines
    and Purchase Order lines, enabling:
    - One PR line to be split into multiple PO lines (different vendors/deliveries)
    - Multiple PR lines to be consolidated into one PO line
    - Partial conversion tracking (quantity from each PR line used in each PO line)
    """
    
    # Source PR Line
    pr_line = models.ForeignKey(
        PRLine,
        on_delete=models.PROTECT,
        related_name='po_line_mappings',
        help_text="Source PR line"
    )
    
    # Target PO Line
    po_line = models.ForeignKey(
        'purchase_orders.POLine',
        on_delete=models.CASCADE,
        related_name='pr_line_mappings',
        help_text="Target PO line"
    )
    
    # Quantity from PR line used in this PO line
    quantity_converted = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text="Quantity from PR line converted to this PO line"
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pr_to_po_mappings_created'
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Notes about this conversion (e.g., split reason)"
    )
    
    class Meta:
        db_table = 'requisition_pr_to_po_line_mapping'
        ordering = ['pr_line', 'po_line']
        verbose_name = 'PR to PO Line Mapping'
        verbose_name_plural = 'PR to PO Line Mappings'
        indexes = [
            models.Index(fields=['pr_line']),
            models.Index(fields=['po_line']),
        ]
    
    def __str__(self):
        return f"{self.pr_line.pr_header.pr_number}-L{self.pr_line.line_number} → {self.po_line.po_header.po_number}-L{self.po_line.line_number}"
    
    def save(self, *args, **kwargs):
        # Validate quantity
        if self.quantity_converted > self.pr_line.quantity_remaining:
            raise ValueError(
                f"Cannot convert {self.quantity_converted} units. "
                f"Only {self.pr_line.quantity_remaining} units remaining on PR line."
            )
        
        super().save(*args, **kwargs)
        
        # Update PR line conversion tracking
        self._update_pr_line_conversion()
    
    def delete(self, *args, **kwargs):
        pr_line = self.pr_line
        super().delete(*args, **kwargs)
        
        # Recalculate PR line conversion status
        self._update_pr_line_conversion(pr_line=pr_line)
    
    def _update_pr_line_conversion(self, pr_line=None):
        """Update the source PR line's conversion status."""
        if pr_line is None:
            pr_line = self.pr_line
        
        # Sum all quantities converted from this PR line
        from django.db.models import Sum
        total_converted = PRToPOLineMapping.objects.filter(
            pr_line=pr_line
        ).aggregate(total=Sum('quantity_converted'))['total'] or Decimal('0.0000')
        
        pr_line.quantity_converted = total_converted
        pr_line.update_conversion_status()

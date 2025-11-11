from django.db import models
from django.db.utils import OperationalError
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords


class XX_SegmentType(models.Model):
    """
    Defines segment types for this client installation.
    Examples: Entity (Cost Center), Account, Project, Line Item, etc.
    Configured during client setup.
    """
    segment_id = models.IntegerField(primary_key=True, help_text="Unique segment identifier")
    segment_name = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Display name (e.g., 'Entity', 'Account', 'Project')"
    )
    segment_type = models.CharField(
        max_length=50,
        help_text="Technical type (e.g., 'cost_center', 'account', 'project')"
    )
    is_required = models.BooleanField(
        default=True,
        help_text="Whether this segment is required in transactions"
    )
    has_hierarchy = models.BooleanField(
        default=False,
        help_text="Whether this segment supports parent-child relationships"
    )
    length = models.IntegerField(
        default=50,
        help_text="Fixed code length for this segment (all codes must be this length)"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Order for displaying in UI (lower = first)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of what this segment represents"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this segment is currently active"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "XX_SEGMENT_TYPE_XX"
        verbose_name = "Segment Type"
        verbose_name_plural = "Segment Types"
        ordering = ['display_order', 'segment_id']
    
    def __str__(self):
        return f"{self.segment_name}"
    
    def is_used_in_transactions(self):
        """
        Check if this segment type is used in any transactions.
        Returns tuple: (is_used: bool, usage_details: list)
        """
        usage = []
        
        # Check if segment type has any segment values
        segment_count = self.values.count()
        if segment_count > 0:
            # Check if any of those segments are used in journal line segments
            from finance.models import JournalLineSegment
            used_in_journal = JournalLineSegment.objects.filter(segment_type=self).exists()
            if used_in_journal:
                count = JournalLineSegment.objects.filter(segment_type=self).count()
                usage.append(f"Used in {count} journal line segment(s)")
        
        return (len(usage) > 0, usage)
    
    def delete(self, *args, **kwargs):
        """
        Prevent deletion if segment type is used in transactions.
        Suggest marking as inactive instead.
        """
        is_used, usage_details = self.is_used_in_transactions()
        
        if is_used:
            error_msg = (
                f"Cannot delete segment type '{self.segment_name}' because it is used in transactions:\n"
                + "\n".join(f"  - {detail}" for detail in usage_details)
                + "\n\nInstead of deleting, consider marking it as inactive by setting is_active=False."
            )
            raise ValidationError(error_msg)
        
        # Check if it has any segment values (even if not used in transactions)
        segment_count = self.values.count()
        if segment_count > 0:
            error_msg = (
                f"Cannot delete segment type '{self.segment_name}' because it has {segment_count} segment value(s).\n"
                "Please delete or reassign all segment values first, or mark this segment type as inactive."
            )
            raise ValidationError(error_msg)
        
        super().delete(*args, **kwargs)


class XX_Segment(models.Model):
    """
    Generic segment value model that replaces XX_Entity, XX_Account, XX_Project.
    All segment values (regardless of type) are stored here.
    """
    id = models.AutoField(primary_key=True)
    segment_type = models.ForeignKey(
        XX_SegmentType,
        on_delete=models.CASCADE,
        related_name='values',
        help_text="Which segment type this value belongs to"
    )
    code = models.CharField(
        max_length=50,
        help_text="The actual segment code/value"
    )
    parent_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Parent segment code for hierarchical segments"
    )
    alias = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Display name / description"
    )
    node_type = models.CharField(
        max_length=20,
        choices=[
            ('parent', 'Parent'),
            ('sub_parent', 'Sub-Parent'),
            ('child', 'Child')
        ],
        default='child',
        help_text="Node type in hierarchy: parent (root), sub_parent (intermediate), or child (leaf)"
    )
    level = models.IntegerField(
        default=0,
        help_text="Hierarchy level (0 = root)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this segment value is active"
    )
    
    # Financial data (optional, for segments that need envelopes/limits)
    envelope_amount = models.DecimalField(
        max_digits=30,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Envelope/budget limit for this segment (if applicable)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "XX_SEGMENT_XX"
        verbose_name = "Segment Value"
        verbose_name_plural = "Segment Values"
        unique_together = ("segment_type", "code")
        indexes = [
            models.Index(fields=["segment_type", "code"]),
            models.Index(fields=["segment_type", "parent_code"]),
            models.Index(fields=["code"]),
        ]
    
    def __str__(self):
        return f"{self.segment_type.segment_name}: {self.code} ({self.alias or 'No alias'})"
    
    @property
    def name(self):
        """Compatibility property for old Account model"""
        return self.alias or self.code
    
    @property
    def type(self):
        """Compatibility property for old Account model"""
        return self.segment_type.segment_type if self.segment_type else None
    
    @property
    def parent(self):
        """Get parent segment object if exists"""
        if self.parent_code:
            try:
                return XX_Segment.objects.get(
                    segment_type=self.segment_type,
                    code=self.parent_code
                )
            except XX_Segment.DoesNotExist:
                return None
        return None
    
    @property
    def full_path(self):
        """Get full hierarchical path"""
        path = [self.code]
        current = self
        while current.parent_code:
            try:
                current = XX_Segment.objects.get(
                    segment_type=current.segment_type,
                    code=current.parent_code
                )
                path.insert(0, current.code)
            except XX_Segment.DoesNotExist:
                break
        return " > ".join(path)
    
    @property
    def hierarchy_level(self):
        """Get numeric hierarchy level"""
        return self.level
    
    def get_all_children(self):
        """Get all descendant codes recursively"""
        children = list(XX_Segment.objects.filter(
            segment_type=self.segment_type,
            parent_code=self.code
        ).values_list('code', flat=True))
        
        descendants = []
        for child_code in children:
            descendants.append(child_code)
            try:
                child = XX_Segment.objects.get(
                    segment_type=self.segment_type,
                    code=child_code
                )
                descendants.extend(child.get_all_children())
            except XX_Segment.DoesNotExist:
                continue
        
        return descendants
    
    def is_used_in_transactions(self):
        """
        Check if this segment is used in any transactions.
        Returns tuple: (is_used: bool, usage_details: list)
        """
        usage = []
        
        # Check in JournalLine (account field)
        try:
            from finance.models import JournalLine, JournalLineSegment
            journal_line_count = JournalLine.objects.filter(account=self).count()
            if journal_line_count > 0:
                usage.append(f"Used as account in {journal_line_count} journal line(s)")
            
            # Check in JournalLineSegment (segment field)
            journal_segment_count = JournalLineSegment.objects.filter(segment=self).count()
            if journal_segment_count > 0:
                usage.append(f"Used in {journal_segment_count} journal line segment assignment(s)")
        except (ImportError, OperationalError):
            # Tables might not exist yet
            pass
        
        # Check in InvoiceLine (if table exists)
        try:
            from finance.models import InvoiceLine
            invoice_line_count = InvoiceLine.objects.filter(account=self).count()
            if invoice_line_count > 0:
                usage.append(f"Used in {invoice_line_count} invoice line(s)")
        except (ImportError, OperationalError):
            # Table might not exist
            pass
        
        # Check in procurement payment models (if they exist)
        try:
            from procurement.payments.models import (
                TaxConfiguration, PaymentLine, 
                WithholdingTaxConfig, TaxPaymentLine
            )
            
            tax_config_payable = TaxConfiguration.objects.filter(tax_payable_account=self).count()
            tax_config_receivable = TaxConfiguration.objects.filter(tax_receivable_account=self).count()
            if tax_config_payable > 0:
                usage.append(f"Used as tax payable account in {tax_config_payable} tax configuration(s)")
            if tax_config_receivable > 0:
                usage.append(f"Used as tax receivable account in {tax_config_receivable} tax configuration(s)")
            
            payment_line_count = PaymentLine.objects.filter(gl_account=self).count()
            if payment_line_count > 0:
                usage.append(f"Used in {payment_line_count} payment line(s)")
            
            withholding_config = WithholdingTaxConfig.objects.filter(withholding_tax_account=self).count()
            if withholding_config > 0:
                usage.append(f"Used in {withholding_config} withholding tax configuration(s)")
            
            tax_payment_expense = TaxPaymentLine.objects.filter(tax_expense_account=self).count()
            tax_payment_payable = TaxPaymentLine.objects.filter(tax_payable_account=self).count()
            if tax_payment_expense > 0:
                usage.append(f"Used as tax expense account in {tax_payment_expense} tax payment(s)")
            if tax_payment_payable > 0:
                usage.append(f"Used as tax payable account in {tax_payment_payable} tax payment(s)")
        except (ImportError, OperationalError):
            # Procurement app might not be installed or tables might not exist
            pass
        
        return (len(usage) > 0, usage)
    
    def delete(self, *args, **kwargs):
        """
        Prevent deletion if segment is used in any transactions.
        Suggest marking as inactive instead.
        """
        is_used, usage_details = self.is_used_in_transactions()
        
        if is_used:
            error_msg = (
                f"Cannot delete segment '{self.code} - {self.alias}' because it is used in transactions:\n"
                + "\n".join(f"  - {detail}" for detail in usage_details)
                + "\n\nInstead of deleting, mark it as inactive by setting is_active=False."
            )
            raise ValidationError(error_msg)
        
        # Also check if this segment has children
        children_count = XX_Segment.objects.filter(
            segment_type=self.segment_type,
            parent_code=self.code
        ).count()
        
        if children_count > 0:
            error_msg = (
                f"Cannot delete segment '{self.code} - {self.alias}' because it has {children_count} child segment(s).\n"
                "Please delete or reassign all child segments first, or mark this segment as inactive."
            )
            raise ValidationError(error_msg)
        
        super().delete(*args, **kwargs)

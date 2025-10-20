"""
AP (Accounts Payable) Models
Supplier, APInvoice, APItem, APPayment
"""
from django.db import models
from core.models import Currency, TaxRate

TAX_COUNTRIES = [("AE","UAE"),("SA","KSA"),("EG","Egypt"),("IN","India")]
TAX_CATS = [("STANDARD","Standard"),("ZERO","Zero"),("EXEMPT","Exempt"),("RC","Reverse Charge")]


class Supplier(models.Model):
    """Supplier master data"""
    code = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Unique supplier code")
    name = models.CharField(max_length=128)
    email = models.EmailField(blank=True)
    country = models.CharField(max_length=2, default="AE", help_text="ISO 2-letter country code")
    currency = models.ForeignKey("core.Currency", on_delete=models.PROTECT, null=True, blank=True,
                                 help_text="Supplier's default currency",
                                 related_name="ap_suppliers")
    vat_number = models.CharField(max_length=50, blank=True, help_text="VAT/Tax registration number")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['code']
        db_table = 'ap_supplier'  # NEW table name
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class APInvoice(models.Model):
    """Accounts Payable Invoice"""
    # Payment status choices
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    PAYMENT_STATUSES = [
        (UNPAID, "Unpaid"),
        (PARTIALLY_PAID, "Partially Paid"),
        (PAID, "Paid"),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    number = models.CharField(max_length=32, unique=True)
    date = models.DateField()
    due_date = models.DateField()
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="ap_invoices")
    country = models.CharField(max_length=2, choices=TAX_COUNTRIES, default="AE",help_text="Tax country for this invoice (defaults to supplier country)")
    
    # Approval workflow
    APPROVAL_STATUSES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUSES,
        default='DRAFT',
        help_text="Approval workflow status"
    )
    
    # Posting status - separates draft/posted state
    is_posted = models.BooleanField(default=False, help_text="Whether invoice is posted to GL")
    posted_at = models.DateTimeField(null=True, blank=True)
    
    # Payment status - separates payment state
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUSES, 
        default=UNPAID,
        help_text="Payment status of the invoice"
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Cancellation flag
    is_cancelled = models.BooleanField(default=False, help_text="Whether invoice is cancelled")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    gl_journal = models.OneToOneField(
        "finance.JournalEntry", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="ap_source_new")  # Changed related_name to avoid conflict
    
    # FX tracking fields
    exchange_rate = models.DecimalField(
        max_digits=18, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Exchange rate used when posting (invoice currency to base currency)"
    )
    base_currency_total = models.DecimalField(
        max_digits=14, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Total amount in base currency"
    )
    
    # Stored total fields
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Invoice subtotal (before tax)"
    )
    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total tax amount"
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Invoice total (subtotal + tax)"
    )
    
    class Meta:
        db_table = 'ap_apinvoice'  # NEW table name
    
    def save(self, *args, **kwargs):
        # Auto-set country from supplier if not explicitly set
        if not self.country and self.supplier and self.supplier.country:
            self.country = self.supplier.country
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"AP-{self.number}"
    
    def calculate_and_save_totals(self):
        """Calculate invoice totals from items and save to database"""
        from decimal import Decimal
        
        subtotal_amt = Decimal('0.00')
        tax_amt = Decimal('0.00')
        
        for item in self.items.all():
            line_subtotal = item.quantity * item.unit_price
            line_tax = Decimal('0.00')
            if item.tax_rate:
                line_tax = line_subtotal * (item.tax_rate.rate / 100)
            subtotal_amt += line_subtotal
            tax_amt += line_tax
        
        self.subtotal = subtotal_amt
        self.tax_amount = tax_amt
        self.total = subtotal_amt + tax_amt
        self.save(update_fields=['subtotal', 'tax_amount', 'total'])
        
        return {
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'total': self.total
        }
    
    def calculate_total(self):
        """Calculate invoice total from items (backward compatibility)"""
        from decimal import Decimal
        
        total = Decimal('0.00')
        for item in self.items.all():
            subtotal = item.quantity * item.unit_price
            tax_amount = Decimal('0.00')
            if item.tax_rate:
                tax_amount = subtotal * (item.tax_rate.rate / 100)
            total += subtotal + tax_amount
        return total
    
    def paid_amount(self):
        """Return total amount paid via allocations (converted to invoice currency)"""
        from decimal import Decimal
        
        paid = Decimal('0.00')
        for alloc in self.payment_allocations.all():
            alloc_amount = alloc.amount
            
            # Check if payment currency differs from invoice currency
            if alloc.payment and alloc.payment.currency_id != self.currency_id:
                # Convert payment amount to invoice currency
                if alloc.current_exchange_rate and alloc.current_exchange_rate != Decimal("0"):
                    # Payment amount in invoice currency = payment amount / exchange rate
                    # (exchange rate is FROM invoice TO payment, so divide to go back)
                    alloc_amount = alloc.amount / alloc.current_exchange_rate
                else:
                    # No exchange rate available, try to fetch on the fly
                    try:
                        from finance.fx_services import get_exchange_rate
                        rate = get_exchange_rate(
                            from_currency=alloc.payment.currency,
                            to_currency=self.currency,
                            rate_date=alloc.payment.date,
                            rate_type="SPOT"
                        )
                        # Payment currency to invoice currency
                        alloc_amount = alloc.amount * rate
                    except:
                        pass  # Keep original amount if conversion fails
            
            paid += alloc_amount
        
        return paid
    
    def outstanding_amount(self):
        """Return unpaid balance (in invoice currency)"""
        return self.calculate_total() - self.paid_amount()


class APItem(models.Model):
    """AP Invoice Line Item"""
    invoice = models.ForeignKey(APInvoice, related_name="items", on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.ForeignKey(TaxRate, null=True, blank=True, on_delete=models.SET_NULL, related_name="ap_items")
    tax_country  = models.CharField(max_length=2, choices=TAX_COUNTRIES, null=True, blank=True)
    tax_category = models.CharField(max_length=16, choices=TAX_CATS, null=True, blank=True)
    
    class Meta:
        db_table = 'ap_apitem'  # NEW table name
    
    def __str__(self):
        return f"{self.invoice.number} - {self.description[:30]}"


class APPayment(models.Model):
    """AP Payment - can be allocated to multiple invoices"""
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, blank=True, help_text="Supplier receiving the payment")
    reference = models.CharField(max_length=64, unique=True, null=True, blank=True, help_text="Payment reference number")
    date = models.DateField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text="Total payment amount")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="ap_payments_currency", null=True, blank=True, help_text="Payment currency (currency paid)")
    memo = models.CharField(max_length=255, blank=True, help_text="Payment memo/notes")
    bank_account = models.ForeignKey("finance.BankAccount", null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="ap_payments")
    posted_at = models.DateTimeField(null=True, blank=True)
    reconciled = models.BooleanField(default=False)
    reconciliation_ref = models.CharField(max_length=64, blank=True)
    reconciled_at = models.DateField(null=True, blank=True)
    gl_journal = models.ForeignKey("finance.JournalEntry", null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="ap_payment_source_new")
    payment_fx_rate = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    
    # FX gain/loss tracking fields
    invoice_currency = models.ForeignKey(
        Currency, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name="ap_payments_invoice_currency",
        help_text="Currency of the invoice(s) being paid - for FX tracking"
    )
    exchange_rate = models.DecimalField(
        max_digits=18, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Exchange rate from invoice currency to payment currency (for FX gain/loss)"
    )
    
    # Legacy support - keep for backward compatibility but make optional
    invoice = models.ForeignKey(APInvoice, related_name="payments_legacy", on_delete=models.PROTECT, 
                                null=True, blank=True, help_text="DEPRECATED: Use allocations instead")
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                 help_text="DEPRECATED: Use total_amount instead")
    
    class Meta:
        db_table = 'ap_appayment'
        ordering = ['-date', '-id']
    
    def __str__(self):
        return f"Payment {self.reference or 'N/A'} - {self.total_amount or 0}"
    
    def allocated_amount(self):
        """Return sum of all allocations"""
        from decimal import Decimal
        return self.allocations.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    
    def unallocated_amount(self):
        """Return unallocated amount"""
        from decimal import Decimal
        total = self.total_amount if self.total_amount is not None else Decimal('0.00')
        return total - self.allocated_amount()
    
    def update_exchange_rate_from_allocations(self):
        """
        Update invoice_currency and exchange_rate based on allocated invoices.
        If all allocations are to invoices in the same currency (different from payment currency),
        fetch and store the exchange rate for FX gain/loss calculations.
        """
        from decimal import Decimal
        
        allocations = self.allocations.all()
        if not allocations.exists():
            return
        
        # Get all unique invoice currencies from allocations
        invoice_currencies = set(
            alloc.invoice.currency for alloc in allocations if alloc.invoice
        )
        
        # If all invoices are in the same currency and it's different from payment currency
        if len(invoice_currencies) == 1:
            inv_currency = invoice_currencies.pop()
            
            if self.currency and inv_currency.id != self.currency.id:
                # Different currencies - fetch exchange rate
                self.invoice_currency = inv_currency
                
                try:
                    from finance.fx_services import get_exchange_rate
                    self.exchange_rate = get_exchange_rate(
                        from_currency=inv_currency,
                        to_currency=self.currency,
                        rate_date=self.date,
                        rate_type="SPOT"
                    )
                    self.save(update_fields=['invoice_currency', 'exchange_rate'])
                    print(f"Payment {self.reference}: Set exchange rate {inv_currency.code} -> {self.currency.code} = {self.exchange_rate}")
                except Exception as e:
                    print(f"Warning: Could not fetch exchange rate for payment {self.reference}: {e}")
            else:
                # Same currency - no FX rate needed
                self.invoice_currency = inv_currency
                self.exchange_rate = Decimal('1.000000')
                self.save(update_fields=['invoice_currency', 'exchange_rate'])


class APPaymentAllocation(models.Model):
    """Allocation of AP payment to specific invoices"""
    payment = models.ForeignKey(APPayment, related_name="allocations", on_delete=models.CASCADE)
    invoice = models.ForeignKey(APInvoice, related_name="payment_allocations", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=14, decimal_places=2, help_text="Amount allocated to this invoice")
    memo = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Currency tracking fields
    invoice_currency = models.ForeignKey(
        Currency, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name="ap_payment_allocations_invoice_currency",
        help_text="Currency of the invoice (copied from invoice at allocation time)"
    )
    current_exchange_rate = models.DecimalField(
        max_digits=18, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Exchange rate from invoice currency to payment currency at allocation time"
    )
    
    class Meta:
        db_table = 'ap_appaymentallocation'
        unique_together = [['payment', 'invoice']]
    
    def __str__(self):
        return f"{self.payment.reference} -> {self.invoice.number}: {self.amount}"
    
    def save(self, *args, **kwargs):
        """Auto-populate invoice_currency and current_exchange_rate on save"""
        if self.invoice and not self.invoice_currency:
            # Get invoice currency
            self.invoice_currency = self.invoice.currency
            
            # Calculate exchange rate if payment and invoice currencies differ
            if self.payment and self.payment.currency and self.invoice.currency:
                from_currency = self.invoice.currency
                to_currency = self.payment.currency
                
                # Only fetch exchange rate if currencies are different
                if from_currency.id != to_currency.id:
                    try:
                        from finance.fx_services import get_exchange_rate
                        self.current_exchange_rate = get_exchange_rate(
                            from_currency=from_currency,
                            to_currency=to_currency,
                            rate_date=self.payment.date,
                            rate_type="SPOT"
                        )
                    except Exception as e:
                        print(f"Warning: Could not fetch exchange rate: {e}")
                        self.current_exchange_rate = None
                else:
                    # Same currency, rate is 1.0
                    from decimal import Decimal
                    self.current_exchange_rate = Decimal('1.000000')
        
        super().save(*args, **kwargs)

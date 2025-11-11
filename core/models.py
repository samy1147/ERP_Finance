from django.db import models
from simple_history.models import HistoricalRecords

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=64)
    symbol = models.CharField(max_length=8, default="$")
    is_base = models.BooleanField(default=False, help_text="Is this the base/home currency?")
    history = HistoricalRecords()
    
    class Meta:
        verbose_name_plural = "Currencies"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class TaxRate(models.Model):
    COUNTRY_CHOICES = [
        ("AE", "United Arab Emirates"),
        ("SA", "Saudi Arabia"),
        ("EG", "Egypt"),
        ("IN", "India"),
    ]
    CATEGORY_CHOICES = [
        ("STANDARD", "Standard"),
        ("ZERO", "Zero Rated"),
        ("EXEMPT", "Exempt"),
        ("RC", "Reverse Charge"),
    ]

    name = models.CharField(max_length=64)
    rate = models.DecimalField(max_digits=6, decimal_places=3, help_text="Percent (e.g. 5 = 5%)")
    # NEW:
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default="AE")
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES, default="STANDARD")
    code = models.CharField(max_length=16, blank=True, help_text="Display code (e.g., VAT5, GST18)")
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Is this rate currently active?")
    history = HistoricalRecords()
  
    class Meta:
        indexes = [
           models.Index(fields=["country", "category", "code", "effective_from", "effective_to"]),
          ]
        ordering = ['country', '-effective_from']
        unique_together = (("country", "category", "code", "effective_from"), )
    def __str__(self):
        return f"{self.country}-{self.category} {self.rate}%"


class ExchangeRate(models.Model):
    """
    Exchange rate table for multi-currency support.
    Stores exchange rates between currencies for specific dates.
    """
    RATE_TYPE_CHOICES = [
        ("SPOT", "Spot Rate"),
        ("AVERAGE", "Average Rate"),
        ("FIXED", "Fixed Rate"),
        ("CLOSING", "Period Closing Rate"),
    ]
    
    from_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="rates_from")
    to_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="rates_to")
    rate_date = models.DateField(db_index=True, help_text="Date this rate is effective")
    rate = models.DecimalField(max_digits=18, decimal_places=6, help_text="Exchange rate (1 from_currency = rate * to_currency)")
    rate_type = models.CharField(max_length=16, choices=RATE_TYPE_CHOICES, default="SPOT")
    source = models.CharField(max_length=128, blank=True, help_text="Source of rate (e.g., Central Bank, Manual)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-rate_date', 'from_currency', 'to_currency']
        indexes = [
            models.Index(fields=['from_currency', 'to_currency', '-rate_date']),
            models.Index(fields=['rate_date', 'is_active']),
        ]
        unique_together = [('from_currency', 'to_currency', 'rate_date', 'rate_type')]
    
    def __str__(self):
        return f"{self.from_currency.code}/{self.to_currency.code} = {self.rate} on {self.rate_date}"


class FXGainLossAccount(models.Model):
    """
    Configuration for FX gain/loss GL accounts.
    Defines which accounts to use for realized and unrealized FX gains and losses.
    """
    account = models.OneToOneField('segment.XX_Segment', on_delete=models.PROTECT, related_name='fx_config')
    gain_loss_type = models.CharField(
        max_length=16,
        choices=[
            ("REALIZED_GAIN", "Realized FX Gain"),
            ("REALIZED_LOSS", "Realized FX Loss"),
            ("UNREALIZED_GAIN", "Unrealized FX Gain"),
            ("UNREALIZED_LOSS", "Unrealized FX Loss"),
        ],
        unique=True
    )
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name = "FX Gain/Loss Account"
        verbose_name_plural = "FX Gain/Loss Accounts"
    
    def __str__(self):
        return f"{self.gain_loss_type}: {self.account.code} - {self.account.name}"


"""
FX (Foreign Exchange) Service Functions
Handles currency conversion, exchange rate lookups, and FX gain/loss calculations
"""

from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from datetime import date, datetime
from typing import Optional, Tuple
from django.core.exceptions import ValidationError

from core.models import Currency, ExchangeRate, FXGainLossAccount
from .models import JournalEntry, JournalLine
from segment.models import XX_Segment
from segment.utils import SegmentHelper


def get_base_currency() -> Currency:
    """
    Get the base/home currency for the company.
    Returns the currency marked with is_base=True.
    """
    try:
        return Currency.objects.get(is_base=True)
    except Currency.DoesNotExist:
        raise ValidationError("No base currency configured. Please set a currency as is_base=True.")
    except Currency.MultipleObjectsReturned:
        raise ValidationError("Multiple base currencies found. Only one currency should have is_base=True.")


def get_exchange_rate(
    from_currency: Currency,
    to_currency: Currency,
    rate_date: date,
    rate_type: str = "SPOT"
) -> Decimal:
    """
    Get the exchange rate for converting from one currency to another on a specific date.
    
    Args:
        from_currency: Source currency
        to_currency: Target currency
        rate_date: Date for which to get the rate
        rate_type: Type of rate (SPOT, AVERAGE, CLOSING, etc.)
    
    Returns:
        Exchange rate as Decimal
    
    Raises:
        ValidationError: If no rate is found
    """
    # If currencies are the same, rate is 1
    if from_currency.id == to_currency.id:
        return Decimal('1.000000')
    
    # Try to get the exact date rate
    try:
        rate_obj = ExchangeRate.objects.filter(
            from_currency=from_currency,
            to_currency=to_currency,
            rate_date=rate_date,
            rate_type=rate_type,
            is_active=True
        ).latest('rate_date')
        return rate_obj.rate
    except ExchangeRate.DoesNotExist:
        pass
    
    # Try to get the most recent rate before the date
    try:
        rate_obj = ExchangeRate.objects.filter(
            from_currency=from_currency,
            to_currency=to_currency,
            rate_date__lte=rate_date,
            rate_type=rate_type,
            is_active=True
        ).latest('rate_date')
        return rate_obj.rate
    except ExchangeRate.DoesNotExist:
        pass
    
    # Try inverse rate (to/from) and calculate reciprocal
    try:
        rate_obj = ExchangeRate.objects.filter(
            from_currency=to_currency,
            to_currency=from_currency,
            rate_date__lte=rate_date,
            rate_type=rate_type,
            is_active=True
        ).latest('rate_date')
        # Inverse the rate
        return Decimal('1.000000') / rate_obj.rate
    except ExchangeRate.DoesNotExist:
        raise ValidationError(
            f"No exchange rate found for {from_currency.code}/{to_currency.code} "
            f"on or before {rate_date} (type: {rate_type})"
        )


def convert_amount(
    amount: Decimal,
    from_currency: Currency,
    to_currency: Currency,
    rate_date: date,
    rate_type: str = "SPOT"
) -> Decimal:
    """
    Convert an amount from one currency to another.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency
        to_currency: Target currency
        rate_date: Date for exchange rate lookup
        rate_type: Type of rate to use
    
    Returns:
        Converted amount rounded to 2 decimal places
    """
    rate = get_exchange_rate(from_currency, to_currency, rate_date, rate_type)
    converted = (amount * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return converted


def calculate_fx_gain_loss(
    original_amount: Decimal,
    original_currency: Currency,
    original_rate: Decimal,
    settlement_amount: Decimal,
    settlement_currency: Currency,
    settlement_rate: Decimal
) -> Tuple[Decimal, str]:
    """
    Calculate realized FX gain or loss on a transaction.
    
    Args:
        original_amount: Original transaction amount in original currency
        original_currency: Original transaction currency
        original_rate: Exchange rate used at original transaction time
        settlement_amount: Settlement amount in settlement currency
        settlement_currency: Settlement currency
        settlement_rate: Exchange rate at settlement time
    
    Returns:
        Tuple of (gain_loss_amount, gain_or_loss_type)
        gain_or_loss_type is either "REALIZED_GAIN" or "REALIZED_LOSS"
    """
    base_currency = get_base_currency()
    
    # Convert original amount to base currency at original rate
    if original_currency.id == base_currency.id:
        original_base_amount = original_amount
    else:
        original_base_amount = original_amount * original_rate
    
    # Convert settlement amount to base currency at settlement rate
    if settlement_currency.id == base_currency.id:
        settlement_base_amount = settlement_amount
    else:
        settlement_base_amount = settlement_amount * settlement_rate
    
    # Calculate difference
    difference = settlement_base_amount - original_base_amount
    
    # Round to 2 decimal places
    difference = difference.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Determine if it's a gain or loss
    if difference > 0:
        return (difference, "REALIZED_GAIN")
    elif difference < 0:
        return (abs(difference), "REALIZED_LOSS")
    else:
        return (Decimal('0.00'), "REALIZED_GAIN")  # No gain/loss


def get_fx_account(gain_loss_type: str) -> XX_Segment:
    """
    Get the GL account configured for a specific FX gain/loss type.
    
    Args:
        gain_loss_type: Type of gain/loss (REALIZED_GAIN, REALIZED_LOSS, etc.)
    
    Returns:
        Account object
    
    Raises:
        ValidationError: If no account is configured
    """
    try:
        fx_config = FXGainLossAccount.objects.get(
            gain_loss_type=gain_loss_type,
            is_active=True
        )
        return fx_config.account
    except FXGainLossAccount.DoesNotExist:
        raise ValidationError(
            f"No FX gain/loss account configured for {gain_loss_type}. "
            f"Please configure in FXGainLossAccount model."
        )


@transaction.atomic
def post_fx_gain_loss(
    journal_entry: JournalEntry,
    gain_loss_amount: Decimal,
    gain_loss_type: str,
    contra_account: XX_Segment,
    memo: str = ""
) -> None:
    """
    Post FX gain or loss journal lines to an existing journal entry.
    
    Args:
        journal_entry: JournalEntry to add lines to
        gain_loss_amount: Absolute amount of gain or loss
        gain_loss_type: REALIZED_GAIN, REALIZED_LOSS, UNREALIZED_GAIN, or UNREALIZED_LOSS
        contra_account: The account to post against (usually AR/AP account)
        memo: Optional memo for the line items
    """
    if gain_loss_amount == 0:
        return  # No gain/loss to post
    
    fx_account = get_fx_account(gain_loss_type)
    
    if "GAIN" in gain_loss_type:
        # Gain: Credit FX Gain account, Debit contra account
        JournalLine.objects.create(
            entry=journal_entry,
            account=fx_account,
            debit=Decimal('0.00'),
            credit=gain_loss_amount
        )
        JournalLine.objects.create(
            entry=journal_entry,
            account=contra_account,
            debit=gain_loss_amount,
            credit=Decimal('0.00')
        )
    else:
        # Loss: Debit FX Loss account, Credit contra account
        JournalLine.objects.create(
            entry=journal_entry,
            account=fx_account,
            debit=gain_loss_amount,
            credit=Decimal('0.00')
        )
        JournalLine.objects.create(
            entry=journal_entry,
            account=contra_account,
            debit=Decimal('0.00'),
            credit=gain_loss_amount
        )


def create_exchange_rate(
    from_currency_code: str,
    to_currency_code: str,
    rate: Decimal,
    rate_date: date,
    rate_type: str = "SPOT",
    source: str = ""
) -> ExchangeRate:
    """
    Create or update an exchange rate.
    
    Args:
        from_currency_code: Source currency code (e.g., 'USD')
        to_currency_code: Target currency code (e.g., 'AED')
        rate: Exchange rate
        rate_date: Effective date
        rate_type: Type of rate
        source: Source of the rate
    
    Returns:
        ExchangeRate object
    """
    from_currency = Currency.objects.get(code=from_currency_code)
    to_currency = Currency.objects.get(code=to_currency_code)
    
    rate_obj, created = ExchangeRate.objects.update_or_create(
        from_currency=from_currency,
        to_currency=to_currency,
        rate_date=rate_date,
        rate_type=rate_type,
        defaults={
            'rate': rate,
            'source': source,
            'is_active': True
        }
    )
    
    return rate_obj


@transaction.atomic
def revalue_open_balances(
    as_of_date: date,
    account_code: str,
    revaluation_currency: Optional[Currency] = None
) -> JournalEntry:
    """
    Revalue open AR/AP balances for unrealized FX gain/loss.
    This should be run at period end to recognize unrealized FX on open balances.
    
    Args:
        as_of_date: Date to revalue as of
        account_code: AR or AP account code to revalue
        revaluation_currency: Currency to revalue to (defaults to base currency)
    
    Returns:
        JournalEntry with the revaluation
    
    Note: This is a placeholder for more complex revaluation logic
    that would need to track individual AR/AP items and their original rates.
    """
    if revaluation_currency is None:
        revaluation_currency = get_base_currency()
    
    # This would need more complex logic to:
    # 1. Get all open AR/AP invoices
    # 2. Calculate their original booked amount in base currency
    # 3. Revalue them at current rate
    # 4. Post the difference as unrealized gain/loss
    
    # Placeholder implementation
    account = SegmentHelper.get_account_by_code(account_code)
    je = JournalEntry.objects.create(
        date=as_of_date,
        currency=revaluation_currency,
        memo=f"Unrealized FX revaluation for {account_code}",
        posted=False
    )
    
    # Would add journal lines here based on revaluation calculation
    
    return je

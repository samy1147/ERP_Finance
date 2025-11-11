import pytest
from decimal import Decimal
from django.utils import timezone

@pytest.fixture
def base_data(db):
    """Create minimal base data independent of seed_erp to keep tests hermetic."""
    from core.models import Currency, TaxRate
    from finance.models import BankAccount
    from segment.utils import SegmentHelper
    # Currency
    aed, _ = Currency.objects.get_or_create(code="AED", defaults={"name":"UAE Dirham","symbol":"د.إ","is_base":True})
    # Accounts (match services.DEFAULT_ACCOUNTS keys)
    account_defs = [
        ("1000","Cash at Bank","AS"),
        ("1100","Accounts Receivable","AS"),
        ("2000","Accounts Payable","LI"),
        ("2100","VAT Output (Payable)","LI"),
        ("2110","VAT Input (Recoverable)","AS"),
        ("4000","Revenue","IN"),
        ("5000","Expense","EX"),
        ("2400","Corporate Tax Payable","LI"),
        ("6900","Corporate Tax Expense","EX"),
        ("7150","FX Gain","IN"),
        ("8150","FX Loss","EX"),
    ]
    for code, name, typ in account_defs:
        SegmentHelper.get_account_segments().get_or_create(code=code, defaults={"name":name, "type":typ, "is_active":True})
    # Bank
    bank, _ = BankSegmentHelper.get_account_segments().get_or_create(name="Main Bank", defaults={"account_code":"1000", "currency":aed, "active":True})
    # VAT (AE 5%)
    TaxRate.objects.get_or_create(
        country="AE", category="STANDARD", code="VAT5", effective_from=timezone.now().date().replace(year=2018, month=1, day=1),
        defaults={"name":"VAT 5%", "rate":Decimal("5.000"), "is_active":True}
    )
    return {"currency": aed, "bank": bank}
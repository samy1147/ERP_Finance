import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

@pytest.mark.django_db
def test_ar_aging_buckets(base_data):
    from ar.models import Customer, ARInvoice, ARItem
    from core.models import TaxRate
    from finance.services import gl_post_from_ar_balanced, build_ar_aging

    today = timezone.now().date()
    cust = Customer.objects.create(code="C004", name="Delta LLC", currency=base_data["currency"])
    vat5 = TaxRate.objects.get(country="AE", code="VAT5")

    # Create 4 invoices with different due dates; all posted
    def make_inv(num, days_ago):
        inv = ARInvoice.objects.create(
            customer=cust, number=f"INV-AGE-{num}",
            date=today - timedelta(days=days_ago+5),  # created before due
            due_date=today - timedelta(days=days_ago),
            currency=base_data["currency"],
        )
        ARItem.objects.create(invoice=inv, description="Item", quantity=1, unit_price=Decimal("100.00"),
                              tax_rate=vat5, tax_country="AE", tax_category="STANDARD")
        gl_post_from_ar_balanced(inv)
        return inv

    inv_current = make_inv(1, -1)   # due tomorrow -> current
    inv_10      = make_inv(2, 10)   # 10 days overdue -> 1–30
    inv_45      = make_inv(3, 45)   # 45 days overdue -> 31–60
    inv_100     = make_inv(4, 100)  # >90

    rep = build_ar_aging(as_of=today, b1=30, b2=30, b3=30)
    buckets = {r["bucket"] for r in rep["invoices"]}
    assert "Current" in buckets
    assert "1–30" in buckets
    assert "31–60" in buckets
    assert ">90" in buckets
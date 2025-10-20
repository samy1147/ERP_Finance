import pytest
from decimal import Decimal
from django.utils import timezone

@pytest.mark.django_db
def test_vat_rounding_edges(base_data):
    from ar.models import Customer, ARInvoice, ARItem
    from core.models import TaxRate
    from finance.services import ar_totals, q2

    cust = Customer.objects.create(code="C002", name="Beta Co", currency=base_data["currency"])
    inv = ARInvoice.objects.create(
        customer=cust, number="INV-ROUND",
        date=timezone.now().date(), due_date=timezone.now().date(),
        currency=base_data["currency"],
    )
    vat5 = TaxRate.objects.get(country="AE", code="VAT5")
    # Two tiny prices to hit rounding points: 0.10 and 0.20 at 5% VAT
    ARItem.objects.create(invoice=inv, description="Tiny A", quantity=1, unit_price=Decimal("0.10"),
                          tax_rate=vat5, tax_country="AE", tax_category="STANDARD")
    ARItem.objects.create(invoice=inv, description="Tiny B", quantity=1, unit_price=Decimal("0.20"),
                          tax_rate=vat5, tax_country="AE", tax_category="STANDARD")

    totals = ar_totals(inv)
    # Expected: net=0.30, tax=0.02 (0.10*5% -> 0.005 => 0.01; 0.20*5% -> 0.01), gross=0.32
    assert totals["subtotal"] == q2(Decimal("0.30"))
    assert totals["tax"] == q2(Decimal("0.02"))
    assert totals["total"] == q2(Decimal("0.32"))
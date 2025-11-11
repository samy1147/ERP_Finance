import pytest
from decimal import Decimal
from django.utils import timezone

@pytest.mark.django_db
def test_ar_invoice_post_gl_idempotent(base_data):
    from ar.models import Customer, ARInvoice, ARItem
    from core.models import TaxRate
    from finance.models import JournalEntry, JournalLine
    from segment.models import XX_Segment
from segment.utils import SegmentHelper
    from finance.services import gl_post_from_ar_balanced, ar_totals

    # Customer & invoice
    cust = Customer.objects.create(code="C001", name="Acme LLC", currency=base_data["currency"])
    inv = ARInvoice.objects.create(
        customer=cust, number="INV-001",
        date=timezone.now().date(), due_date=timezone.now().date(),
        currency=base_data["currency"],
    )
    vat5 = TaxRate.objects.get(country="AE", code="VAT5")
    ARItem.objects.create(invoice=inv, description="Service A", quantity=1, unit_price=Decimal("100.00"),
                          tax_rate=vat5, tax_country="AE", tax_category="STANDARD")

    # First post
    je1, created1 = gl_post_from_ar_balanced(inv)
    assert created1 is True
    assert je1.posted

    # Second post — should be idempotent
    je2, created2 = gl_post_from_ar_balanced(inv)
    assert created2 is False
    assert je1.id == je2.id
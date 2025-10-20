import pytest
from decimal import Decimal
from django.utils import timezone

@pytest.mark.django_db
def test_ar_payments_partial_and_close_with_fx(base_data):
    from ar.models import Customer, ARInvoice, ARItem, ARPayment
    from core.models import TaxRate
    from finance.models import BankAccount, JournalEntry, Account, JournalLine
    from finance.services import gl_post_from_ar_balanced, post_ar_payment, reverse_journal, ar_totals, q2

    cust = Customer.objects.create(code="C003", name="Gamma Inc", currency=base_data["currency"])
    inv = ARInvoice.objects.create(
        customer=cust, number="INV-PAY",
        date=timezone.now().date(), due_date=timezone.now().date(),
        currency=base_data["currency"],
    )
    vat5 = TaxRate.objects.get(country="AE", code="VAT5")
    ARItem.objects.create(invoice=inv, description="Consulting", quantity=1, unit_price=Decimal("100.00"),
                          tax_rate=vat5, tax_country="AE", tax_category="STANDARD")
    je, created = gl_post_from_ar_balanced(inv)
    assert created is True

    # Partial payment 60.00
    p1 = ARPayment.objects.create(invoice=inv, date=timezone.now().date(), amount=Decimal("60.00"),
                                  bank_account=base_data["bank"])
    je1, already_posted1, closed1 = post_ar_payment(p1)
    assert closed1 is False

    # Update: change p1 amount to 70.00 -> reverse and repost
    reverse_journal(je1)
    p1.gl_journal = None
    p1.amount = Decimal("70.00")
    p1.save(update_fields=["gl_journal", "amount"])
    je2, already_posted2, closed2 = post_ar_payment(p1)
    assert je2.id != je1.id

    # Second payment with FX rate (should post FX gain/loss if configured)
    p2 = ARPayment.objects.create(invoice=inv, date=timezone.now().date(), amount=Decimal("35.00"),
                                  bank_account=base_data["bank"], payment_fx_rate=Decimal("1.050000"))
    je3, already_posted3, closed3 = post_ar_payment(p2)
    assert closed3 is False  # 70 + 35 = 105? Not yet, because VAT makes gross 105; remaining 105-70-35=0 => closed next
    totals_after = ar_totals(inv)
    assert totals_after["balance"] == q2(Decimal("0.00"))
    # After balance zero, invoice should be PAID
    inv.refresh_from_db()
    assert inv.status == "PAID"
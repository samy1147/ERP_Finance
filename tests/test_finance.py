import datetime as dt
import pytest
from core.models import Currency, TaxRate
from finance.models import JournalEntry, JournalLine
from segment.models import XX_Segment
from segment.utils import SegmentHelper
from ar.models import Customer, ARInvoice, ARItem, ARPayment
from finance.services import post_entry, ar_totals

@pytest.mark.django_db
def test_post_entry_balanced():
    cur = Currency.objects.create(code="USD", name="US Dollar")
    cash = Account.objects.create(code="1000", name="Cash", type="AS")
    rev  = Account.objects.create(code="4000", name="Revenue", type="IN")
    je = JournalEntry.objects.create(date=dt.date.today(), currency=cur, memo="sale")
    JournalLine.objects.create(entry=je, account=cash, debit=100, credit=0)
    JournalLine.objects.create(entry=je, account=rev, debit=0, credit=100)
    post_entry(je)
    je.refresh_from_db()
    assert je.posted is True

@pytest.mark.django_db
def test_ar_totals_with_tax_and_payment():
    cur = Currency.objects.create(code="USD", name="US Dollar")
    vat = TaxRate.objects.create(name="VAT", rate=10)
    cust = Customer.objects.create(name="Acme", email="a@a.com")
    inv = ARInvoice.objects.create(customer=cust, number="INV1", date=dt.date.today(), due_date=dt.date.today(), currency=cur)
    ARItem.objects.create(invoice=inv, description="A", quantity=2, unit_price=50, tax_rate=vat)  # 2*50=100 +10% = 110
    ARItem.objects.create(invoice=inv, description="B", quantity=1, unit_price=100)              # 100
    ARPayment.objects.create(invoice=inv, date=dt.date.today(), amount=60)
    totals = ar_totals(inv)
    assert float(totals["total"]) == pytest.approx(210.0)
    assert float(totals["paid"]) == pytest.approx(60.0)
    assert float(totals["balance"]) == pytest.approx(150.0)

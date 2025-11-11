# tests/test_invoice_post_reverse.py
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.db import connection, IntegrityError
from django.db import transaction

from finance.models import Invoice, InvoiceLine, InvoiceStatus, TaxCode
from segment.models import XX_Segment
from segment.utils import SegmentHelper
from finance.services import post_invoice, reverse_posted_invoice

def _get_any_customer_id():
    """
    Try to fetch any CRM customer id to satisfy the FK.
    If none exists, tests that require a customer will be skipped.
    """
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT id FROM crm_customer LIMIT 1;")
            row = cur.fetchone()
            if row:
                return row[0]
    except Exception:
        return None
    return None

class InvoiceBaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer_id = _get_any_customer_id()
        cls.acc = Account.objects.create(code="4000", name="Revenue")
        cls.tax = TaxCode.objects.create(code="VAT5", rate=Decimal("0.05"))

    def setUp(self):
        if self.customer_id is None:
            self.skipTest("No crm_customer rows found; skipping invoice tests pending CRM fixture.")

    def _draft_invoice_with_line(self, invoice_no="INV-001"):
        inv = Invoice.objects.create(customer_id=self.customer_id, invoice_no=invoice_no, currency="AED")
        InvoiceLine.objects.create(
            invoice=inv, description="Line 1", account=self.acc, tax_code=self.tax,
            quantity=1, unit_price=Decimal("100.00"),
        )
        inv.recompute_totals()
        inv.save()
        return inv

    def test_post_happy_path(self):
        inv = self._draft_invoice_with_line("INV-HP-001")
        posted = post_invoice(inv.id)
        self.assertEqual(posted.status, InvoiceStatus.POSTED)
        self.assertGreater(posted.total_gross, 0)

    def test_block_post_no_lines(self):
        inv = Invoice.objects.create(customer_id=self.customer_id, invoice_no="INV-NL-001", currency="AED")
        with self.assertRaises(ValidationError):
            post_invoice(inv.id)

    def test_block_post_missing_account_or_tax(self):
        inv = Invoice.objects.create(customer_id=self.customer_id, invoice_no="INV-MISS-001", currency="AED")
        # Missing tax
        InvoiceLine.objects.create(invoice=inv, account=self.acc, tax_code=None, quantity=1, unit_price=10)
        with self.assertRaises(ValidationError):
            post_invoice(inv.id)

    def test_reversal_idempotent_and_totals(self):
        inv = self._draft_invoice_with_line("INV-REV-001")
        # capture original totals before reversal
        original_net = inv.total_net
        original_tax = inv.total_tax
        original_gross = inv.total_gross

        post_invoice(inv.id)
        rev1 = reverse_posted_invoice(inv.id)
        rev2 = reverse_posted_invoice(inv.id)
        self.assertEqual(rev1.id, rev2.id)
        inv.refresh_from_db()
        self.assertEqual(inv.status, InvoiceStatus.REVERSED)
        self.assertTrue(rev1.lines.count() > 0)
        # totals of reversal should be negatives of original
        self.assertEqual(Decimal(rev1.total_net), Decimal(-original_net))
        self.assertEqual(Decimal(rev1.total_tax), Decimal(-original_tax))
        self.assertEqual(Decimal(rev1.total_gross), Decimal(-original_gross))

class InvoiceTriggersTest(TransactionTestCase):
    reset_sequences = True

    @classmethod
    def setUpTestData(cls):
        cls.customer_id = _get_any_customer_id()
        cls.acc = Account.objects.create(code="4001", name="Services")
        cls.tax = TaxCode.objects.create(code="VAT15", rate=Decimal("0.15"))

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Trigger checks require PostgreSQL.")
        if self.customer_id is None:
            self.skipTest("No crm_customer rows found; skipping trigger tests pending CRM fixture.")

    def _posted_invoice(self, invoice_no="INV-TRG-1"):
        inv = Invoice.objects.create(customer_id=self.customer_id, invoice_no=invoice_no, currency="AED")
        InvoiceLine.objects.create(invoice=inv, account=self.acc, tax_code=self.tax, quantity=2, unit_price=50)
        inv = post_invoice(inv.id)
        return inv

    def test_trigger_blocks_edit_after_posted(self):
        inv = self._posted_invoice("INV-TRG-EDIT")
        inv.customer_id = 999  # try to change after POSTED
        with self.assertRaises(IntegrityError):
            inv.save()  # trigger should raise

    def test_trigger_validates_posting_transition(self):
        # Build invoice with a bad line (missing tax), then try to post via raw status change
        inv = Invoice.objects.create(customer_id=self.customer_id, invoice_no="INV-TRG-BAD", currency="AED")
        InvoiceLine.objects.create(invoice=inv, account=self.acc, tax_code=None, quantity=1, unit_price=10)

        # Bypass service layer to hit trigger
        inv.status = InvoiceStatus.POSTED
        with self.assertRaises(IntegrityError):
            inv.save(update_fields=["status"])

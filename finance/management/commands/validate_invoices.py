# apps/finance/management/commands/validate_invoices.py

import csv

import sys

from decimal import Decimal

from django.core.management.base import BaseCommand

from django.db import transaction

from finance.models import Invoice, InvoiceStatus
 
class Command(BaseCommand):

    help = "Scan all invoices and report violations (lines, accounts/tax, totals). Optionally fix drifted totals on DRAFT."
 
    def add_arguments(self, parser):

        parser.add_argument("--output", type=str, default="-", help="CSV file path or '-' for stdout")

        parser.add_argument("--fix-totals", action="store_true", help="For DRAFT invoices only, recompute & save totals")

        parser.add_argument("--limit", type=int, default=None, help="Limit number of invoices scanned")
 
    def handle(self, *args, **opts):

        qs = Invoice.objects.all().prefetch_related("lines")

        if opts["limit"]:

            qs = qs.order_by("id")[:opts["limit"]]
 
        rows = []

        invalid_count = 0
 
        for inv in qs:

            inv.recompute_totals()

            has_lines = inv.has_lines()

            missing_acct_tax = inv.any_line_missing_account_or_tax()

            zero_totals = inv.is_zero_totals()
 
            issues = []

            if inv.status in (InvoiceStatus.POSTED, InvoiceStatus.REVERSED):

                # strict for posted/reversed

                if not has_lines:

                    issues.append("NO_LINES")

                if missing_acct_tax:

                    issues.append("MISSING_ACCOUNT_OR_TAX")

                if zero_totals:

                    issues.append("ZERO_TOTALS")

            else:

                # DRAFT can have issues, but we can fix totals drift

                pass
 
            # totals drift between header & line sums

            drift = []

            sum_net = sum((l.amount_net or Decimal("0")) for l in inv.lines.all()) if has_lines else Decimal("0")

            sum_tax = sum((l.tax_amount or Decimal("0")) for l in inv.lines.all()) if has_lines else Decimal("0")

            sum_gross = sum((l.amount_gross or Decimal("0")) for l in inv.lines.all()) if has_lines else Decimal("0")

            if Decimal(inv.total_net or 0) != sum_net:

                drift.append("NET_DRIFT")

            if Decimal(inv.total_tax or 0) != sum_tax:

                drift.append("TAX_DRIFT")

            if Decimal(inv.total_gross or 0) != sum_gross:

                drift.append("GROSS_DRIFT")
 
            if drift:

                issues.extend(drift)
 
            if inv.status == InvoiceStatus.DRAFT and opts["fix-totals"] and has_lines:

                with transaction.atomic():

                    inv.total_net = sum_net

                    inv.total_tax = sum_tax

                    inv.total_gross = sum_gross

                    inv.save(update_fields=["total_net", "total_tax", "total_gross", "updated_at"])
 
            if issues:

                invalid_count += 1

                rows.append({

                    "invoice_id": inv.id,

                    "invoice_no": inv.invoice_no,

                    "status": inv.status,

                    "issues": "|".join(issues),

                    "lines": inv.lines.count(),

                    "total_net": str(inv.total_net),

                    "total_tax": str(inv.total_tax),

                    "total_gross": str(inv.total_gross),

                })
 
        # Output CSV - elegant single block approach
        fp = sys.stdout if opts["output"] == "-" else open(opts["output"], "w", newline="", encoding="utf-8")
        try:
            writer = csv.DictWriter(fp, fieldnames=[
                "invoice_id", "invoice_no", "status", "issues", "lines", "total_net", "total_tax", "total_gross"
            ])
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        finally:
            # Only close if it's a file (not stdout)
            if fp is not sys.stdout:
                fp.close()
 
        if invalid_count:
            self.stderr.write(self.style.ERROR(f"Found {invalid_count} invalid invoices"))
            # Non-zero exit to surface in CI
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("All invoices are valid"))

 

from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.conf import settings
from django.db.models import Sum, F, Q
from .models import Invoice, InvoiceLine, InvoiceStatus, JournalEntry, JournalLine, BankAccount,CorporateTaxRule,CorporateTaxFiling
from segment.models import XX_Segment
from segment.utils import SegmentHelper
from ar.models import ARInvoice, ARPayment
from ap.models import APInvoice, APPayment
from django.utils import timezone
from django.db import transaction
from datetime import datetime, date
from decimal import Decimal
from core.models import TaxRate
from django.core.exceptions import ValidationError

# Helper function to get account segments by code
def get_account_by_code(code: str) -> XX_Segment:
    """Get account segment by code"""
    return SegmentHelper.get_account_by_code(code)


def build_trial_balance(date_from=None, date_to=None):
    """
    Returns list of dicts: [{code, name, debit, credit}], with final TOTAL row.
    Filters by JournalEntry.date in [date_from, date_to], posted only.
    """
    qs = JournalLine.objects.select_related("entry", "account").filter(entry__posted=True)
    if date_from:
        qs = qs.filter(entry__date__gte=date_from)
    if date_to:
        qs = qs.filter(entry__date__lte=date_to)

    rows = {}
    for jl in qs:
        code = jl.account.code
        if code not in rows:
            rows[code] = {"code": code, "name": jl.account.name, "debit": Decimal("0.00"), "credit": Decimal("0.00")}
        rows[code]["debit"] += Decimal(jl.debit or 0)
        rows[code]["credit"] += Decimal(jl.credit or 0)

    data = []
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    for code in sorted(rows):
        r = rows[code]
        r["debit"] = q2(r["debit"])
        r["credit"] = q2(r["credit"])
        total_debit += r["debit"]
        total_credit += r["credit"]
        data.append(r)

    data.append({"code": "TOTAL", "name": "", "debit": q2(total_debit), "credit": q2(total_credit)})
    return data


def _aging_bucket(days_overdue, b1=30, b2=30, b3=30):
    if days_overdue <= 0:
        return "Current"
    if 1 <= days_overdue <= b1:
        return f"1–{b1}"
    if b1 < days_overdue <= b1 + b2:
        return f"{b1+1}–{b1+b2}"
    if b1 + b2 < days_overdue <= b1 + b2 + b3:
        return f"{b1+b2+1}–{b1+b2+b3}"
    return f">{b1+b2+b3}"


def _ar_balance(inv: ARInvoice):
    t = ar_totals(inv)
    return q2(t["balance"])

def _ap_balance(inv: APInvoice):
    t = ap_totals(inv)
    return q2(t["balance"])




def build_ar_aging(as_of=None, b1=30, b2=30, b3=30):
    """
    Returns dict:
      {
        "as_of": ISO, "buckets": ["Current","1–30","31–60","61–90",">90"],
        "invoices": [... per invoice ...],
        "summary": {"Current": ..., "1–30": ..., ... , "TOTAL": ...}
      }
    """
    as_of = as_of or timezone.now().date()
    buckets = ["Current", f"1–{b1}", f"{b1+1}–{b1+b2}", f"{b1+b2+1}–{b1+b2+b3}", f">{b1+b2+b3}"]
    rows = []
    sums = {k: Decimal("0.00") for k in buckets}
    total = Decimal("0.00")

    for inv in ARInvoice.objects.select_related("customer").all():
        bal = _ar_balance(inv)
        if bal <= 0:
            continue
        days = (as_of - inv.due_date).days if inv.due_date else 0
        bucket = _aging_bucket(days, b1, b2, b3)
        row = {
            "invoice_id": inv.id,
            "number": inv.number,
            "customer": getattr(inv.customer, "name", ""),
            "date": inv.date.isoformat() if inv.date else None,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "days_overdue": max(days, 0),
            "balance": float(bal),
            "bucket": bucket,
        }
        rows.append(row)
        sums[bucket] += bal
        total += bal

    summary = {k: float(q2(v)) for k, v in sums.items()}
    summary["TOTAL"] = float(q2(total))
    return {"as_of": as_of.isoformat(), "buckets": buckets, "invoices": rows, "summary": summary}

def build_ap_aging(as_of=None, b1=30, b2=30, b3=30):
    as_of = as_of or timezone.now().date()
    buckets = ["Current", f"1–{b1}", f"{b1+1}–{b1+b2}", f"{b1+b2+1}–{b1+b2+b3}", f">{b1+b2+b3}"]
    rows = []
    sums = {k: Decimal("0.00") for k in buckets}
    total = Decimal("0.00")

    for inv in APInvoice.objects.select_related("supplier").all():
        bal = _ap_balance(inv)
        if bal <= 0:
            continue
        days = (as_of - inv.due_date).days if inv.due_date else 0
        bucket = _aging_bucket(days, b1, b2, b3)
        row = {
            "invoice_id": inv.id,
            "number": inv.number,
            "supplier": getattr(inv.supplier, "name", ""),
            "date": inv.date.isoformat() if inv.date else None,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "days_overdue": max(days, 0),
            "balance": float(bal),
            "bucket": bucket,
        }
        rows.append(row)
        sums[bucket] += bal
        total += bal

    summary = {k: float(q2(v)) for k, v in sums.items()}
    summary["TOTAL"] = float(q2(total))
    return {"as_of": as_of.isoformat(), "buckets": buckets, "invoices": rows, "summary": summary}


def _bank_account_to_gl_account(payment_bank: BankAccount | None) -> XX_Segment:
    """
    If BankAccount has a mapped GL code, use it, else fall back to FINANCE_ACCOUNTS['BANK'].
    """
    code = (payment_bank.account_code or ACCOUNT_CODES["BANK"]) if payment_bank else ACCOUNT_CODES["BANK"]
    try:
        return get_account_by_code(code)
    except XX_Segment.DoesNotExist:
        raise ValueError(f"Bank GL account '{code}' not found. Seed an Account with code={code} "
                         f"or set bank_account.account_code accordingly.")

def q2(x: Decimal) -> Decimal:
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def amount_with_tax(qty, price, rate):
    subtotal = Decimal(qty) * Decimal(price)
    tax = subtotal * (Decimal(rate) / Decimal("100")) if rate else Decimal("0")
    return q2(subtotal), q2(tax), q2(subtotal + tax)

def ar_totals(invoice: ARInvoice) -> dict:
   subtotal = Decimal("0"); tax = Decimal("0"); total = Decimal("0")
   for i in invoice.items.all():
       r = line_rate(i, invoice.date)
       s, t, tot = amount_with_tax(i.quantity, i.unit_price, r)
       subtotal += s; tax += t; total += tot
   
   # Get paid amount from payment allocations (reverse relation: payment_allocations)
   # Convert payment amounts to invoice currency if needed
   paid = Decimal("0")
   for alloc in invoice.payment_allocations.all():
       alloc_amount = alloc.amount
       
       # Check if payment currency differs from invoice currency
       if alloc.payment and alloc.payment.currency_id != invoice.currency_id:
           # Convert payment amount to invoice currency
           if alloc.current_exchange_rate and alloc.current_exchange_rate != Decimal("0"):
               # Payment amount in invoice currency = payment amount / exchange rate
               # (exchange rate is FROM invoice TO payment, so divide to go back)
               alloc_amount = alloc.amount / alloc.current_exchange_rate
           else:
               # No exchange rate available, use payment amount as-is (might be incorrect)
               # Try to fetch rate on the fly
               try:
                   from finance.fx_services import get_exchange_rate
                   rate = get_exchange_rate(
                       from_currency=alloc.payment.currency,
                       to_currency=invoice.currency,
                       rate_date=alloc.payment.date,
                       rate_type="SPOT"
                   )
                   # Payment currency to invoice currency
                   alloc_amount = alloc.amount * rate
               except:
                   pass  # Keep original amount if conversion fails
       
       paid += alloc_amount
   
   return {"subtotal": q2(subtotal), "tax": q2(tax), "total": q2(total), "paid": q2(paid), "balance": q2(total - paid)}
def ap_totals(invoice: APInvoice) -> dict:
   subtotal = Decimal("0"); tax = Decimal("0"); total = Decimal("0")
   for i in invoice.items.all():
       r = line_rate(i, invoice.date)
       s, t, tot = amount_with_tax(i.quantity, i.unit_price, r)
       subtotal += s; tax += t; total += tot
   
   # Get paid amount from payment allocations (reverse relation: payment_allocations)
   # Convert payment amounts to invoice currency if needed
   paid = Decimal("0")
   for alloc in invoice.payment_allocations.all():
       alloc_amount = alloc.amount
       
       # Check if payment currency differs from invoice currency
       if alloc.payment and alloc.payment.currency_id != invoice.currency_id:
           # Convert payment amount to invoice currency
           if alloc.current_exchange_rate and alloc.current_exchange_rate != Decimal("0"):
               # Payment amount in invoice currency = payment amount / exchange rate
               # (exchange rate is FROM invoice TO payment, so divide to go back)
               alloc_amount = alloc.amount / alloc.current_exchange_rate
           else:
               # No exchange rate available, use payment amount as-is (might be incorrect)
               # Try to fetch rate on the fly
               try:
                   from finance.fx_services import get_exchange_rate
                   rate = get_exchange_rate(
                       from_currency=alloc.payment.currency,
                       to_currency=invoice.currency,
                       rate_date=alloc.payment.date,
                       rate_type="SPOT"
                   )
                   # Payment currency to invoice currency
                   alloc_amount = alloc.amount * rate
               except:
                   pass  # Keep original amount if conversion fails
       
       paid += alloc_amount
   
   return {"subtotal": q2(subtotal), "tax": q2(tax), "total": q2(total), "paid": q2(paid), "balance": q2(total - paid)}
def post_entry(entry: JournalEntry):
    td = sum((l.debit for l in entry.lines.all()), start=Decimal("0"))
    tc = sum((l.credit for l in entry.lines.all()), start=Decimal("0"))
    if q2(td) != q2(tc):
        raise ValueError("Unbalanced journal")
    entry.posted = True; entry.save(update_fields=["posted"]); return entry


DEFAULT_ACCOUNTS = {
    # Control / Balances
    "BANK": "1000",
    "AR": "1100",
    "AP": "2000",

    # Indirect tax (VAT)
    "VAT_OUT": "2100",          # Output VAT (payable) – credited on AR posting
    "VAT_IN": "2110",           # Input VAT (recoverable) – debited on AP posting

    # P&L
    "REV": "4000",
    "EXP": "5000",

    # Corporate tax
    "TAX_CORP_PAYABLE": "2220", # Liability - Corporate Tax Payable
    "TAX_CORP_EXP": "6900",     # Expense

    # FX revaluation (optional)
    "FX_GAIN": "7150",
    "FX_LOSS": "8150",
}
ACCOUNT_CODES = getattr(settings, "FINANCE_ACCOUNTS", DEFAULT_ACCOUNTS)


def _create_journal_entry(**kwargs):
    allowed = {f.name for f in JournalEntry._meta.get_fields()
               if getattr(f, "concrete", False) and not getattr(f, "many_to_many", False)}
    payload = {k: v for k, v in kwargs.items() if k in allowed}
    return JournalEntry.objects.create(**payload)


def _acct(key: str) -> XX_Segment:
    """Get account by key, with helpful error message if not found"""
    code = ACCOUNT_CODES.get(key)
    if not code:
        raise ValueError(f"Account key '{key}' not configured in FINANCE_ACCOUNTS")
    
    try:
        return get_account_by_code(code)
    except XX_Segment.DoesNotExist:
        raise ValueError(
            f"Account '{code}' (for {key}) does not exist in Chart of Accounts. "
            f"Please create this account before posting invoices."
        )

@transaction.atomic
def gl_post_from_ar_balanced(invoice: ARInvoice):
    """
    Idempotent: if invoice already posted, return existing JE.
    Else create a balanced JE, attach to invoice, mark posted.
    Automatically converts to base currency if invoice is in foreign currency.
    Returns: (journal_entry, created: bool)
    """
    from finance.fx_services import get_base_currency, get_exchange_rate, convert_amount
    
    # lock invoice row to avoid race
    inv = ARInvoice.objects.select_for_update().get(pk=invoice.pk)

    if inv.gl_journal_id:
        return inv.gl_journal, False

    # Check if invoice has items
    item_count = inv.items.count()
    if item_count == 0:
        raise ValueError(f"Cannot post invoice {inv.number} to GL: Invoice has no line items")

    # Calculate and save totals to database before posting
    inv.calculate_and_save_totals()
    
    # Calculate totals in invoice currency FIRST
    # Tax is calculated on invoice currency amounts
    totals = ar_totals(inv)
    subtotal = totals["subtotal"]
    tax = totals["tax"]
    invoice_total = q2(subtotal + tax)
    
    # Validate totals are not zero
    if invoice_total == Decimal("0.00"):
        raise ValueError(f"Cannot post invoice {inv.number} to GL: Total amount is zero")

    # Get base currency
    base_currency = get_base_currency()
    
    # Determine if currency conversion is needed
    needs_conversion = inv.currency.id != base_currency.id
    
    if needs_conversion:
        # Get exchange rate for invoice date
        exchange_rate = get_exchange_rate(
            from_currency=inv.currency,
            to_currency=base_currency,
            rate_date=inv.date,
            rate_type="SPOT"
        )
        
        # Convert AFTER tax calculation: Total (with tax) → Base Currency
        # This ensures tax is calculated in invoice currency first
        total_base = convert_amount(invoice_total, inv.currency, base_currency, inv.date)
        
        # For GL breakdown, convert subtotal and tax separately
        subtotal_base = convert_amount(subtotal, inv.currency, base_currency, inv.date)
        tax_base = q2(total_base - subtotal_base)  # Derive tax_base to ensure balance
        
        # Store exchange rate and base currency total
        inv.exchange_rate = exchange_rate
        inv.base_currency_total = total_base
        memo = f"AR Post {inv.number} ({inv.currency.code}→{base_currency.code} @ {exchange_rate})"
    else:
        # Same currency - no conversion needed
        exchange_rate = Decimal('1.000000')
        subtotal_base = subtotal
        tax_base = tax
        total_base = invoice_total
        inv.exchange_rate = exchange_rate
        inv.base_currency_total = total_base
        memo = f"AR Post {inv.number}"

    # Create journal entry in BASE CURRENCY
    je = _create_journal_entry(
        organization=getattr(inv, "organization", None),
        date=inv.date,
        currency=base_currency,  # Always post in base currency
        memo=memo,
    )
    
    # Check if invoice has custom GL distribution lines
    has_gl_lines = hasattr(inv, 'gl_lines') and inv.gl_lines.exists()
    
    if not has_gl_lines:
        raise ValueError(f"Cannot post invoice {inv.number}: GL distribution lines are required")
    
    # Use GL distribution lines
    for gl_line in inv.gl_lines.all():
        # Convert to base currency if needed
        line_amount = convert_amount(gl_line.amount, inv.currency, base_currency, inv.date) if needs_conversion else gl_line.amount
        
        if gl_line.line_type == 'DEBIT':
            JournalLine.objects.create(entry=je, account=gl_line.account, debit=line_amount)
        else:
            JournalLine.objects.create(entry=je, account=gl_line.account, credit=line_amount)

    post_entry(je)

    # mark invoice posted
    inv.gl_journal = je
    if hasattr(inv, "is_posted"):
        # AR/AP invoices use new field structure
        inv.is_posted = True
        inv.save(update_fields=["gl_journal", "posted_at", "is_posted", "exchange_rate", "base_currency_total", "subtotal", "tax_amount", "total"])
    elif hasattr(inv, "status"):
        # Legacy invoice models
        inv.status = getattr(inv, "POSTED", getattr(inv, "status", "POSTED"))
        inv.save(update_fields=["gl_journal", "posted_at", "status", "exchange_rate", "base_currency_total", "subtotal", "tax_amount", "total"])
    inv.posted_at = timezone.now()

    return je, True


@transaction.atomic
def gl_post_from_ap_balanced(invoice: APInvoice):
    """
    Idempotent: if invoice already posted, return existing JE.
    Else create a balanced JE, attach to invoice, mark posted.
    Automatically converts to base currency if invoice is in foreign currency.
    Returns: (journal_entry, created: bool)
    """
    from finance.fx_services import get_base_currency, get_exchange_rate, convert_amount
    
    inv = APInvoice.objects.select_for_update().get(pk=invoice.pk)

    if inv.gl_journal_id:
        return inv.gl_journal, False

    # Check if invoice has items
    item_count = inv.items.count()
    if item_count == 0:
        raise ValueError(f"Cannot post invoice {inv.number} to GL: Invoice has no line items")

    # Calculate and save totals to database before posting
    inv.calculate_and_save_totals()
    
    # Calculate totals in invoice currency FIRST
    # Tax is calculated on invoice currency amounts
    totals = ap_totals(inv)
    subtotal = totals["subtotal"]
    tax = totals["tax"]
    invoice_total = q2(subtotal + tax)
    
    # Validate totals are not zero
    if invoice_total == Decimal("0.00"):
        raise ValueError(f"Cannot post invoice {inv.number} to GL: Total amount is zero")

    # Get base currency
    base_currency = get_base_currency()
    
    # Determine if currency conversion is needed
    needs_conversion = inv.currency.id != base_currency.id
    
    if needs_conversion:
        # Get exchange rate for invoice date
        exchange_rate = get_exchange_rate(
            from_currency=inv.currency,
            to_currency=base_currency,
            rate_date=inv.date,
            rate_type="SPOT"
        )
        
        # Convert AFTER tax calculation: Total (with tax) → Base Currency
        # This ensures tax is calculated in invoice currency first
        total_base = convert_amount(invoice_total, inv.currency, base_currency, inv.date)
        
        # For GL breakdown, convert subtotal and tax separately
        subtotal_base = convert_amount(subtotal, inv.currency, base_currency, inv.date)
        tax_base = q2(total_base - subtotal_base)  # Derive tax_base to ensure balance
        
        # Store exchange rate and base currency total
        inv.exchange_rate = exchange_rate
        inv.base_currency_total = total_base
        memo = f"AP Post {inv.number} ({inv.currency.code}→{base_currency.code} @ {exchange_rate})"
    else:
        # Same currency - no conversion needed
        exchange_rate = Decimal('1.000000')
        subtotal_base = subtotal
        tax_base = tax
        total_base = invoice_total
        inv.exchange_rate = exchange_rate
        inv.base_currency_total = total_base
        memo = f"AP Post {inv.number}"

    # Create journal entry in BASE CURRENCY
    je = _create_journal_entry(
        organization=getattr(inv, "organization", None),
        date=inv.date,
        currency=base_currency,  # Always post in base currency
        memo=memo,
    )
    
    # Check if invoice has custom GL distribution lines
    has_gl_lines = hasattr(inv, 'gl_lines') and inv.gl_lines.exists()
    
    if not has_gl_lines:
        raise ValueError(f"Cannot post invoice {inv.number}: GL distribution lines are required")
    
    # Use GL distribution lines
    for gl_line in inv.gl_lines.all():
        # Convert to base currency if needed
        line_amount = convert_amount(gl_line.amount, inv.currency, base_currency, inv.date) if needs_conversion else gl_line.amount
        
        if gl_line.line_type == 'DEBIT':
            JournalLine.objects.create(entry=je, account=gl_line.account, debit=line_amount)
        else:
            JournalLine.objects.create(entry=je, account=gl_line.account, credit=line_amount)

    post_entry(je)

    inv.gl_journal = je
    inv.posted_at = timezone.now()
    if hasattr(inv, "is_posted"):
        # AR/AP invoices use new field structure
        inv.is_posted = True
        inv.save(update_fields=["gl_journal", "posted_at", "is_posted", "exchange_rate", "base_currency_total", "subtotal", "tax_amount", "total"])
    elif hasattr(inv, "status"):
        # Legacy invoice models
        inv.status = getattr(inv, "POSTED", getattr(inv, "status", "POSTED"))
        inv.save(update_fields=["gl_journal", "posted_at", "status", "exchange_rate", "base_currency_total", "subtotal", "tax_amount", "total"])

    return je, True
# NEW: safe creator that strips unknown kwargs (like 'organization')
@transaction.atomic
def post_ar_payment(payment):
    """
    Post AR payment to GL with multi-currency and FX gain/loss support.
    Handles both old single-invoice and new multi-allocation payment systems.
    """
    from finance.fx_services import get_base_currency, convert_amount
    
    ar_account = get_account_by_code(ACCOUNT_CODES['AR'])
    
    # Get bank account from payment.bank_account
    if payment.bank_account and payment.bank_account.account_code:
        bank_account = get_account_by_code(payment.bank_account.account_code)
    else:
        bank_account = get_account_by_code(ACCOUNT_CODES['BANK'])
    
    # FX accounts for gain/loss
    try:
        fx_gain_account = get_account_by_code(ACCOUNT_CODES.get('FX_GAIN', '9999'))
        fx_loss_account = get_account_by_code(ACCOUNT_CODES.get('FX_LOSS', '9998'))
        fx_accounts_available = True
    except XX_Segment.DoesNotExist:
        fx_accounts_available = False
        print("Warning: FX Gain/Loss accounts not configured")
    
    # Get base currency for journal entry
    base_currency = get_base_currency()
    payment_currency = payment.currency or base_currency
    
    # Update FX tracking fields if not already set
    if not payment.invoice_currency and payment.allocations.exists():
        payment.update_exchange_rate_from_allocations()
        payment.refresh_from_db()
    
    # Create journal entry in base currency
    entry = JournalEntry.objects.create(
        date=payment.date,
        currency=base_currency,
        memo=f"AR Payment {payment.reference or f'#{payment.id}'}",
        posted=True
    )

    # Calculate amounts in base currency
    total_ar_reduction = Decimal("0")  # Amount to reduce AR (in base currency)
    total_bank_received = Decimal("0")  # Amount received in bank (in base currency)
    total_fx_impact = Decimal("0")  # Total FX gain/loss
    
    # Process allocations (new system)
    if payment.allocations.exists():
        for allocation in payment.allocations.all():
            invoice = allocation.invoice
            allocation_amount = allocation.amount
            
            # Get invoice exchange rate (rate when invoice was posted)
            invoice_rate = invoice.exchange_rate or Decimal('1.0')
            
            # Get payment exchange rate (rate when payment was received)
            if payment.invoice_currency and payment.exchange_rate and payment.currency:
                if payment.invoice_currency.id != payment.currency.id:
                    payment_rate = payment.exchange_rate
                else:
                    payment_rate = Decimal('1.0')
            else:
                payment_rate = Decimal('1.0')
            
            # Convert allocation amount to base currency using invoice rate
            # (this is the AR value we're reducing)
            if invoice.currency.id != base_currency.id:
                ar_reduction_base = convert_amount(
                    allocation_amount / invoice_rate if invoice_rate else allocation_amount,
                    invoice.currency,
                    base_currency,
                    payment.date
                )
            else:
                ar_reduction_base = allocation_amount
            
            # Convert cash received to base currency using payment rate
            if payment_currency.id != base_currency.id:
                bank_received_base = convert_amount(
                    allocation_amount,
                    payment_currency,
                    base_currency,
                    payment.date
                )
            else:
                bank_received_base = allocation_amount
            
            total_ar_reduction += ar_reduction_base
            total_bank_received += bank_received_base
            
            # FX impact for this allocation (if rates differ)
            if invoice_rate and payment_rate and invoice_rate != payment_rate:
                # Calculate FX gain/loss in payment currency
                amount_in_invoice_curr = allocation_amount / payment_rate if payment_rate else allocation_amount
                fx_diff_payment_curr = amount_in_invoice_curr * (payment_rate - invoice_rate)
                
                # Convert FX difference to base currency
                if payment_currency.id != base_currency.id:
                    fx_impact = convert_amount(
                        fx_diff_payment_curr,
                        payment_currency,
                        base_currency,
                        payment.date
                    )
                else:
                    fx_impact = fx_diff_payment_curr
                
                total_fx_impact += fx_impact
    
    # Fallback to old single-invoice system
    elif payment.invoice:
        invoice = payment.invoice
        payment_amount = payment.amount or payment.total_amount or Decimal("0")
        
        # Convert using invoice rate
        if invoice.currency.id != base_currency.id:
            ar_reduction_base = convert_amount(
                payment_amount,
                invoice.currency,
                base_currency,
                payment.date
            )
        else:
            ar_reduction_base = payment_amount
        
        # Convert using payment rate
        if payment_currency.id != base_currency.id:
            bank_received_base = convert_amount(
                payment_amount,
                payment_currency,
                base_currency,
                payment.date
            )
        else:
            bank_received_base = payment_amount
        
        total_ar_reduction = ar_reduction_base
        total_bank_received = bank_received_base
        total_fx_impact = bank_received_base - ar_reduction_base
    
    # Post journal lines in base currency
    # Debit: Bank (cash received)
    JournalLine.objects.create(
        entry=entry,
        account=bank_account,
        debit=q2(total_bank_received),
        credit=Decimal("0")
    )

    # Credit: AR (reduce receivable)
    JournalLine.objects.create(
        entry=entry,
        account=ar_account,
        debit=Decimal("0"),
        credit=q2(total_ar_reduction)
    )
    
    # Post FX gain or loss
    if total_fx_impact != 0 and fx_accounts_available:
        if total_fx_impact > 0:
            # FX Gain: received more than AR reduction (currency strengthened)
            JournalLine.objects.create(
                entry=entry,
                account=fx_gain_account,
                debit=Decimal("0"),
                credit=q2(abs(total_fx_impact))
            )
            print(f"AR Payment {payment.reference}: FX Gain {abs(total_fx_impact)} {base_currency.code}")
        else:
            # FX Loss: received less than AR reduction (currency weakened)
            JournalLine.objects.create(
                entry=entry,
                account=fx_loss_account,
                debit=q2(abs(total_fx_impact)),
                credit=Decimal("0")
            )
            print(f"AR Payment {payment.reference}: FX Loss {abs(total_fx_impact)} {base_currency.code}")

    payment.gl_journal = entry
    payment.posted_at = timezone.now()
    payment.save()
    
    # Update invoice payment status for all allocated invoices
    invoice_closed_list = []
    if payment.allocations.exists():
        for allocation in payment.allocations.all():
            invoice = allocation.invoice
            totals = ar_totals(invoice)
            invoice_closed = (totals['balance'] == 0)
            
            if invoice_closed:
                invoice.payment_status = "PAID"
                invoice.paid_at = timezone.now()
                invoice.save(update_fields=['payment_status', 'paid_at'])
                invoice_closed_list.append(invoice.number)
            elif totals['paid'] > 0:
                invoice.payment_status = "PARTIALLY_PAID"
                invoice.save(update_fields=['payment_status'])
    elif payment.invoice:
        # Old system - single invoice
        invoice = payment.invoice
        totals = ar_totals(invoice)
        invoice_closed = (totals['balance'] == 0)
        
        if invoice_closed:
            invoice.payment_status = "PAID"
            invoice.paid_at = timezone.now()
            invoice.save(update_fields=['payment_status', 'paid_at'])
            invoice_closed_list.append(invoice.number)
        elif totals['paid'] > 0:
            invoice.payment_status = "PARTIALLY_PAID"
            invoice.save(update_fields=['payment_status'])
    
    return entry, False, invoice_closed_list


@transaction.atomic
def post_ap_payment(payment: APPayment):
    """
    Post AP payment to GL with multi-currency and FX gain/loss support.
    Handles both old single-invoice and new multi-allocation payment systems.
    """
    from finance.fx_services import get_base_currency, convert_amount
    
    ap_account = get_account_by_code(ACCOUNT_CODES['AP'])
    
    # Get bank account from payment.bank_account
    if payment.bank_account and payment.bank_account.account_code:
        bank_account = get_account_by_code(payment.bank_account.account_code)
    else:
        bank_account = get_account_by_code(ACCOUNT_CODES['BANK'])
    
    # FX accounts for gain/loss
    try:
        fx_gain_account = get_account_by_code(ACCOUNT_CODES.get('FX_GAIN', '9999'))
        fx_loss_account = get_account_by_code(ACCOUNT_CODES.get('FX_LOSS', '9998'))
        fx_accounts_available = True
    except XX_Segment.DoesNotExist:
        fx_accounts_available = False
        print("Warning: FX Gain/Loss accounts not configured")
    
    # Get base currency for journal entry
    base_currency = get_base_currency()
    payment_currency = payment.currency or base_currency
    
    # Update FX tracking fields if not already set
    if not payment.invoice_currency and payment.allocations.exists():
        payment.update_exchange_rate_from_allocations()
        payment.refresh_from_db()
    
    # Create journal entry in base currency
    entry = JournalEntry.objects.create(
        date=payment.date,
        currency=base_currency,
        memo=f"AP Payment {payment.reference or f'#{payment.id}'}",
        posted=True
    )

    # Calculate amounts in base currency
    total_ap_reduction = Decimal("0")  # Amount to reduce AP (in base currency)
    total_bank_paid = Decimal("0")  # Amount paid from bank (in base currency)
    total_fx_impact = Decimal("0")  # Total FX gain/loss
    
    # Process allocations (new system)
    if payment.allocations.exists():
        for allocation in payment.allocations.all():
            invoice = allocation.invoice
            allocation_amount = allocation.amount
            
            # Get invoice exchange rate (rate when invoice was posted)
            invoice_rate = invoice.exchange_rate or Decimal('1.0')
            
            # Get payment exchange rate (rate when payment was made)
            if payment.invoice_currency and payment.exchange_rate and payment.currency:
                if payment.invoice_currency.id != payment.currency.id:
                    payment_rate = payment.exchange_rate
                else:
                    payment_rate = Decimal('1.0')
            else:
                payment_rate = Decimal('1.0')
            
            # Convert allocation amount to base currency using invoice rate
            # (this is the AP value we're reducing)
            if invoice.currency.id != base_currency.id:
                ap_reduction_base = convert_amount(
                    allocation_amount / invoice_rate if invoice_rate else allocation_amount,
                    invoice.currency,
                    base_currency,
                    payment.date
                )
            else:
                ap_reduction_base = allocation_amount
            
            # Convert cash paid to base currency using payment rate
            if payment_currency.id != base_currency.id:
                bank_paid_base = convert_amount(
                    allocation_amount,
                    payment_currency,
                    base_currency,
                    payment.date
                )
            else:
                bank_paid_base = allocation_amount
            
            total_ap_reduction += ap_reduction_base
            total_bank_paid += bank_paid_base
            
            # FX impact for this allocation (if rates differ)
            if invoice_rate and payment_rate and invoice_rate != payment_rate:
                # Calculate FX gain/loss in payment currency
                amount_in_invoice_curr = allocation_amount / payment_rate if payment_rate else allocation_amount
                fx_diff_payment_curr = amount_in_invoice_curr * (payment_rate - invoice_rate)
                
                # Convert FX difference to base currency
                if payment_currency.id != base_currency.id:
                    fx_impact = convert_amount(
                        fx_diff_payment_curr,
                        payment_currency,
                        base_currency,
                        payment.date
                    )
                else:
                    fx_impact = fx_diff_payment_curr
                
                total_fx_impact += fx_impact
    
    # Fallback to old single-invoice system
    elif payment.invoice:
        invoice = payment.invoice
        payment_amount = payment.amount or payment.total_amount or Decimal("0")
        
        # Convert using invoice rate
        if invoice.currency.id != base_currency.id:
            ap_reduction_base = convert_amount(
                payment_amount,
                invoice.currency,
                base_currency,
                payment.date
            )
        else:
            ap_reduction_base = payment_amount
        
        # Convert using payment rate
        if payment_currency.id != base_currency.id:
            bank_paid_base = convert_amount(
                payment_amount,
                payment_currency,
                base_currency,
                payment.date
            )
        else:
            bank_paid_base = payment_amount
        
        total_ap_reduction = ap_reduction_base
        total_bank_paid = bank_paid_base
        total_fx_impact = bank_paid_base - ap_reduction_base
    
    # Post journal lines in base currency
    # Debit: AP (reduce liability)
    JournalLine.objects.create(
        entry=entry,
        account=ap_account,
        debit=q2(total_ap_reduction),
        credit=Decimal("0")
    )
    
    # Credit: Bank (reduce cash)
    JournalLine.objects.create(
        entry=entry,
        account=bank_account,
        debit=Decimal("0"),
        credit=q2(total_bank_paid)
    )
    
    # Post FX gain or loss
    # For AP: If we paid LESS than liability reduction = FX Gain
    #         If we paid MORE than liability reduction = FX Loss
    if total_fx_impact != 0 and fx_accounts_available:
        if total_fx_impact > 0:
            # FX Loss: paid more cash than AP reduction (currency weakened)
            JournalLine.objects.create(
                entry=entry,
                account=fx_loss_account,
                debit=q2(abs(total_fx_impact)),
                credit=Decimal("0")
            )
            print(f"AP Payment {payment.reference}: FX Loss {abs(total_fx_impact)} {base_currency.code}")
        else:
            # FX Gain: paid less cash than AP reduction (currency strengthened)
            JournalLine.objects.create(
                entry=entry,
                account=fx_gain_account,
                debit=Decimal("0"),
                credit=q2(abs(total_fx_impact))
            )
            print(f"AP Payment {payment.reference}: FX Gain {abs(total_fx_impact)} {base_currency.code}")

    payment.gl_journal = entry
    payment.posted_at = timezone.now()
    payment.save()
    
    # Update invoice payment status for all allocated invoices
    invoice_closed_list = []
    if payment.allocations.exists():
        for allocation in payment.allocations.all():
            invoice = allocation.invoice
            totals = ap_totals(invoice)
            invoice_closed = (totals['balance'] == 0)
            
            if invoice_closed:
                invoice.payment_status = "PAID"
                invoice.paid_at = timezone.now()
                invoice.save(update_fields=['payment_status', 'paid_at'])
                invoice_closed_list.append(invoice.number)
            elif totals['paid'] > 0:
                invoice.payment_status = "PARTIALLY_PAID"
                invoice.save(update_fields=['payment_status'])
    elif payment.invoice:
        # Old system - single invoice
        invoice = payment.invoice
        totals = ap_totals(invoice)
        invoice_closed = (totals['balance'] == 0)
        
        if invoice_closed:
            invoice.payment_status = "PAID"
            invoice.paid_at = timezone.now()
            invoice.save(update_fields=['payment_status', 'paid_at'])
            invoice_closed_list.append(invoice.number)
        elif totals['paid'] > 0:
            invoice.payment_status = "PARTIALLY_PAID"
            invoice.save(update_fields=['payment_status'])
    
    return entry, False, invoice_closed_list


def reverse_journal(entry: JournalEntry) -> JournalEntry:
    reversed_entry = JournalEntry.objects.create(
        date=timezone.now().date(),
        currency=entry.currency,
        memo=f"Reversal of Journal #{entry.id}",
        posted=True
    )

    for line in entry.lines.all():
        JournalLine.objects.create(
            entry=reversed_entry,
            account=line.account,
            debit=line.credit,
            credit=line.debit
        )

    return reversed_entry


def _acct_code_or_raise(key: str) -> XX_Segment:
    code = ACCOUNT_CODES[key]
    try:
        return get_account_by_code(code)
    except XX_Segment.DoesNotExist:
        raise ValueError(f"Account {key} with code '{code}' not found. Seed it or override FINANCE_ACCOUNTS.")

# ---- VAT preset seeding ----

PRESET_VAT = {
    "AE": [("STANDARD","VAT 5%","VAT5", Decimal("5.0")),
           ("ZERO","VAT 0%","VAT0", Decimal("0.0")),
           ("EXEMPT","VAT Exempt","VATX", Decimal("0.0"))],
    "SA": [("STANDARD","VAT 15%","VAT15", Decimal("15.0")),
           ("ZERO","VAT 0%","VAT0", Decimal("0.0")),
           ("EXEMPT","VAT Exempt","VATX", Decimal("0.0"))],
    "EG": [("STANDARD","VAT 14%","VAT14", Decimal("14.0")),
           ("ZERO","VAT 0%","VAT0", Decimal("0.0")),
           ("EXEMPT","VAT Exempt","VATX", Decimal("0.0"))],
    "IN": [("STANDARD","GST 18%","GST18", Decimal("18.0")),
           ("ZERO","GST 0%","GST0", Decimal("0.0")),
           ("EXEMPT","GST Exempt","GSTX", Decimal("0.0"))],
}

@transaction.atomic
def seed_vat_presets(effective_from: date | None = None):
    created = []
    for cc, items in PRESET_VAT.items():
        for category, name, code, rate in items:
            obj, was_new = TaxRate.objects.get_or_create(
                country=cc, category=category, code=code,
                defaults={"name": name, "rate": rate, "effective_from": effective_from}
            )
            if was_new: created.append(obj.id)
    return created

def _has_field(model, name:str) -> bool:
   return any(f.name == name for f in model._meta.get_fields())
def _with_org_filter(lines_qs, org_id):
   if org_id and _has_field(JournalEntry, "organization"):
       return lines_qs.filter(entry__organization_id=org_id)
   return lines_qs

# ---- Corporate tax accrual ----
@transaction.atomic
def accrue_corporate_tax(country: str, date_from: date, date_to: date, org_id: int | None = None):
    """
    Compute profit (INCOME - EXPENSE) from posted journals in [date_from, date_to],
    apply CorporateTaxRule for 'country', and post accrual:
      DR TAX_CORP_EXP, CR TAX_CORP_PAYABLE
    Returns created JournalEntry and computed amounts.
    """
    rule = CorporateTaxRule.objects.filter(country=country, active=True).order_by("-id").first()
    if not rule:
        raise ValueError(f"No active CorporateTaxRule configured for country={country}")

    # Sum posted JournalLines in period by account type
    lines = JournalLine.objects.select_related("entry","account") \
          .filter(entry__posted=True, entry__date__gte=date_from, entry__date__lte=date_to)
    lines = _with_org_filter(lines, org_id)
    income = Decimal("0"); expense = Decimal("0")
    for ln in lines:
       acc_type = ln.account.type.upper()
       if acc_type in ("INCOME", "IN"): income += (Decimal(ln.credit) - Decimal(ln.debit))
       elif acc_type in ("EXPENSE", "EX"): expense += (Decimal(ln.debit) - Decimal(ln.credit))
    profit = q2(income - expense)
    
    if profit <= 0:
        return None, {"profit": float(profit), "tax_base": 0.0, "tax": 0.0}
    
    # Threshold handling: tax only on profit above threshold if provided
    tax_base = profit
    if rule.threshold is not None and profit > rule.threshold:
        tax_base = q2(profit - rule.threshold)
    elif rule.threshold:
        # profit below threshold
        return None, {"profit": float(profit), "tax_base": 0.0, "tax": 0.0}
    
    tax = q2(tax_base * (rule.rate / Decimal("100")))
    
    if tax == 0:
        return None, {"profit": float(profit), "tax_base": float(tax_base), "tax": 0.0}
    
    # Get default currency (use first available, or None if field doesn't exist)
    currency = None
    if _has_field(JournalEntry, "currency"):
        from core.models import Currency
        currency = Currency.objects.first()  # Use first available currency
    
    # Create accrual JE
    je = _create_journal_entry(
        organization=org_id if _has_field(JournalEntry,"organization") else None,
        date=date_to, currency=currency,
        memo=f"Corporate tax accrual {country} {date_from}..{date_to} on profit {profit}",
   )
    JournalLine.objects.create(entry=je, account=_acct("TAX_CORP_EXP"), debit=tax, credit=Decimal("0"))
    JournalLine.objects.create(entry=je, account=_acct("TAX_CORP_PAYABLE"), debit=Decimal("0"), credit=tax)
    post_entry(je)
    
    return je, {"profit": float(profit), "tax_base": float(tax_base), "tax": float(tax)}

def resolve_tax_rate_for_date(country:str, category:str, as_of:date) -> Decimal:
   """
   Pick the rate whose [effective_from .. effective_to] encompasses 'as_of'.
   If multiple, pick the most recent effective_from.
   """
   qs = TaxRate.objects.filter(country=country, category=category)
   if as_of:
       qs = qs.filter(
           Q(effective_from__isnull=True) | Q(effective_from__lte=as_of),
       ).filter(
           Q(effective_to__isnull=True) | Q(effective_to__gte=as_of),
       )
   tr = qs.order_by("-effective_from", "-id").first()
   return Decimal(tr.rate) if tr else Decimal("0.0")
def line_rate(item, inv_date) -> Decimal:
   """
   Priority: explicit TaxRate FK > (tax_country+tax_category periodized) > 0%
   """
   if item.tax_rate:
       return Decimal(item.tax_rate.rate)
   if getattr(item, "tax_country", None) and getattr(item, "tax_category", None):
       return resolve_tax_rate_for_date(item.tax_country, item.tax_category, inv_date)
   return Decimal("0.0")


def _get_or_block_existing_filing(country, df, dt, org_id, *, allow_override=False):
   existing = CorporateTaxFiling.objects.filter(country=country, period_start=df, period_end=dt, organization_id=org_id).first()
   if existing:
       if existing.status == "FILED" and not allow_override:
           raise ValueError("Corporate tax period is FILED/locked; override not allowed.")
       if existing.status == "ACCRUED" and existing.accrual_journal_id and not allow_override:
           # idempotent: just return existing accrual
           return existing, False
       return existing, True
   return None, True
@transaction.atomic
def accrue_corporate_tax_with_filing(country:str, date_from:date, date_to:date, org_id:int|None=None, *, allow_override=False):
   filing, can_create = _get_or_block_existing_filing(country, date_from, date_to, org_id, allow_override=allow_override)
   if filing and not can_create and filing.accrual_journal_id:
       # idempotent: return existing accrual
       je = filing.accrual_journal
       return filing, je, {"reuse": True}
   je, meta = accrue_corporate_tax(country, date_from, date_to, org_id)
   if je is None:
       return None, None, meta  # nothing to accrue
   if not filing:
       filing = CorporateTaxFiling.objects.create(country=country, period_start=date_from, period_end=date_to, organization_id=org_id)
   filing.accrual_journal = je
   filing.status = "ACCRUED"
   filing.save(update_fields=["accrual_journal","status"])
   return filing, je, meta
@transaction.atomic
def reverse_corporate_tax_filing(filing_id:int):
   f = CorporateTaxFiling.objects.select_for_update().get(pk=filing_id)
   if f.status == "FILED":
       raise ValueError("Cannot reverse a FILED/locked corporate tax accrual. Unfile/override required.")
   if not f.accrual_journal_id:
       raise ValueError("No accrual journal to reverse.")
   rev = reverse_journal(f.accrual_journal)
   f.reversal_journal = rev
   f.status = "REVERSED"
   f.save(update_fields=["reversal_journal","status"])
   return rev
@transaction.atomic
def file_corporate_tax(filing_id:int):
   f = CorporateTaxFiling.objects.select_for_update().get(pk=filing_id)
   if f.status != "ACCRUED":
       raise ValueError("Only ACCRUED filings can be marked FILED.")
   f.status = "FILED"
   f.filed_at = timezone.now()
   f.save(update_fields=["status","filed_at"])
   return f


def validate_ready_to_post(inv: Invoice):
    # Always compute current totals from lines
    inv.recompute_totals()

    if not inv.has_lines():
        raise ValidationError("Cannot post invoice: it has no lines.")

    if inv.any_line_missing_account_or_tax():
        raise ValidationError("Cannot post invoice: one or more lines missing account or tax code.")

    if inv.is_zero_totals():
        raise ValidationError("Cannot post invoice: totals are zero.")

    # Optional: disallow negative gross (toggle as needed)
    if inv.total_gross < 0:
        raise ValidationError("Cannot post invoice: total gross cannot be negative.")

def post_invoice(invoice_id: int) -> Invoice:
    with transaction.atomic():
        inv = Invoice.objects.select_for_update().get(pk=invoice_id)

        if inv.status == InvoiceStatus.POSTED:
            return inv  # idempotent: already posted

        if inv.status != InvoiceStatus.DRAFT:
            raise ValidationError(f"Only DRAFT invoices can be posted (current: {inv.status}).")

        validate_ready_to_post(inv)

        # Lock & persist
        inv.status = InvoiceStatus.POSTED
        inv.posted_at = timezone.now()
        inv.save()

        # (Optional) create Journal Entries here, if your JE module exists
        # create_journal_for_invoice(inv)

        return inv
def reverse_posted_invoice(original_id: int) -> Invoice:
    with transaction.atomic():
        orig = Invoice.objects.select_for_update().get(pk=original_id)
        if orig.status != InvoiceStatus.POSTED:
            raise ValidationError("Only POSTED invoices can be reversed.")

        # Idempotency: if it already has a reversal, return it
        existing = orig.reversals.order_by("created_at").first()
        if existing:
            return existing

        # Create reversing invoice (negative amounts)
        rev = Invoice.objects.create(
            customer=orig.customer,
            invoice_no=f"{orig.invoice_no}-REV",
            currency=orig.currency,
            status=InvoiceStatus.POSTED,  # Post immediately (common pattern) or keep DRAFT if you want approval
            posted_at=timezone.now(),
            reversal_ref=orig,
        )

        # Mirror lines with negative signs
        bulk = []
        for line in orig.lines.all():
            bulk.append(InvoiceLine(
                invoice=rev,
                description=f"REV of {line.description}",
                account=line.account,
                tax_code=line.tax_code,
                quantity=-line.quantity,
                unit_price=line.unit_price,  # qty negative is enough
            ))
        InvoiceLine.objects.bulk_create(bulk)

        # Recompute totals & save
        rev.recompute_totals()
        rev.save()

        # Mark original as REVERSED (read-only remains in effect)
        orig.status = InvoiceStatus.REVERSED
        orig.save(update_fields=["status", "updated_at"])

        # (Optional) create reversing Journal Entries here
        # create_reversing_journal_for_invoice(rev, original=orig)

        return rev
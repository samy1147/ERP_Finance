"""
Auto-generation of GL distributions with dynamic segment assignments.
"""
from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db import transaction
from segment.models import XX_Segment, XX_SegmentType
from finance.models import SegmentAssignmentRule, JournalEntry, JournalLine, JournalLineSegment
from ar.models import ARInvoice
from ap.models import APInvoice
import logging

logger = logging.getLogger(__name__)


def get_segment_rule(account_segment, customer=None, supplier=None):
    """
    Get the most specific segment assignment rule for given context.
    
    Priority:
    1. Customer/Supplier + Account specific
    2. Account specific (default)
    
    Args:
        account_segment: XX_Segment instance for the account
        customer: Customer instance (optional)
        supplier: Supplier instance (optional)
    
    Returns:
        SegmentAssignmentRule instance or None
    """
    rules = SegmentAssignmentRule.objects.filter(
        is_active=True,
        account_segment=account_segment
    ).order_by('priority')
    
    # Try customer-specific first
    if customer:
        rule = rules.filter(customer=customer).first()
        if rule:
            return rule
    
    # Try supplier-specific
    if supplier:
        rule = rules.filter(supplier=supplier).first()
        if rule:
            return rule
    
    # Fall back to default (no customer/supplier)
    rule = rules.filter(customer__isnull=True, supplier__isnull=True).first()
    return rule


def get_default_segments_for_account(account_code: str, customer=None, supplier=None) -> List[Dict[str, int]]:
    """
    Get default segment assignments for an account using rules.
    
    Args:
        account_code: Account segment code (e.g., '1200', '4000')
        customer: Customer instance (optional)
        supplier: Supplier instance (optional)
    
    Returns:
        List of {'segment_type': int, 'segment': int} dicts
    """
    try:
        # Get account segment
        account_segment = XX_Segment.objects.get(code=account_code, node_type='child')
    except XX_Segment.DoesNotExist:
        logger.error(f"Account segment {account_code} not found")
        raise ValueError(f"Account segment {account_code} does not exist")
    
    # Get rule
    rule = get_segment_rule(account_segment, customer=customer, supplier=supplier)
    
    if rule:
        # Use rule assignments
        assignments = rule.get_segment_assignments()
        return [
            {'segment_type': seg_type_id, 'segment': seg_id}
            for seg_type_id, seg_id in assignments.items()
        ]
    else:
        # No rule found - use just the account
        logger.warning(f"No segment rule found for account {account_code}, using account only")
        return [
            {
                'segment_type': account_segment.segment_type_id,
                'segment': account_segment.id
            }
        ]


def auto_generate_ar_invoice_distributions(invoice: ARInvoice) -> List[Dict[str, Any]]:
    """
    Auto-generate GL distributions for AR invoice.
    
    Standard AR entry:
    - DEBIT: Accounts Receivable (asset - increases)
    - CREDIT: Revenue (income - increases)
    
    Args:
        invoice: ARInvoice instance
    
    Returns:
        List of distribution dicts with amounts, line_type, description, segments
    """
    distributions = []
    
    # DEBIT: Accounts Receivable
    ar_segments = get_default_segments_for_account(
        account_code='1200',  # AR Control Account
        customer=invoice.customer
    )
    
    distributions.append({
        'amount': str(invoice.total),
        'line_type': 'DEBIT',
        'description': f'AR Invoice {invoice.number} - {invoice.customer.name}',
        'segments': ar_segments
    })
    
    # CREDIT: Revenue (one line per item or single line)
    if invoice.items.exists():
        # Create one credit line per invoice item
        for item in invoice.items.all():
            revenue_segments = get_default_segments_for_account(
                account_code='4000',  # Revenue Account
                customer=invoice.customer
            )
            
            # Calculate line total: quantity * unit_price
            line_total = item.quantity * item.unit_price
            
            distributions.append({
                'amount': str(line_total),
                'line_type': 'CREDIT',
                'description': item.description or 'Revenue',
                'segments': revenue_segments
            })
    else:
        # Single credit line for total
        revenue_segments = get_default_segments_for_account(
            account_code='4000',  # Revenue Account
            customer=invoice.customer
        )
        
        distributions.append({
            'amount': str(invoice.total),
            'line_type': 'CREDIT',
            'description': f'Revenue - Invoice {invoice.number}',
            'segments': revenue_segments
        })
    
    logger.info(f"Generated {len(distributions)} distributions for AR Invoice {invoice.number}")
    return distributions


def auto_generate_ap_invoice_distributions(invoice: APInvoice) -> List[Dict[str, Any]]:
    """
    Auto-generate GL distributions for AP invoice.
    
    Standard AP entry:
    - DEBIT: Expense (expense - increases)
    - CREDIT: Accounts Payable (liability - increases)
    
    Args:
        invoice: APInvoice instance
    
    Returns:
        List of distribution dicts with amounts, line_type, description, segments
    """
    distributions = []
    
    # DEBIT: Expense (one line per item or single line)
    if invoice.items.exists():
        # Create one debit line per invoice item
        for item in invoice.items.all():
            expense_segments = get_default_segments_for_account(
                account_code='5000',  # Expense Account
                supplier=invoice.supplier
            )
            
            # Calculate line total: quantity * unit_price
            line_total = item.quantity * item.unit_price
            
            distributions.append({
                'amount': str(line_total),
                'line_type': 'DEBIT',
                'description': item.description or 'Expense',
                'segments': expense_segments
            })
    else:
        # Single debit line for total
        expense_segments = get_default_segments_for_account(
            account_code='5000',  # Expense Account
            supplier=invoice.supplier
        )
        
        distributions.append({
            'amount': str(invoice.total),
            'line_type': 'DEBIT',
            'description': f'Expense - Invoice {invoice.number}',
            'segments': expense_segments
        })
    
    # CREDIT: Accounts Payable
    ap_segments = get_default_segments_for_account(
        account_code='2100',  # AP Control Account
        supplier=invoice.supplier
    )
    
    distributions.append({
        'amount': str(invoice.total),
        'line_type': 'CREDIT',
        'description': f'AP Invoice {invoice.number} - {invoice.supplier.name}',
        'segments': ap_segments
    })
    
    logger.info(f"Generated {len(distributions)} distributions for AP Invoice {invoice.number}")
    return distributions


@transaction.atomic
def create_journal_entry_from_distributions(
    distributions: List[Dict[str, Any]],
    date,
    description: str,
    currency,
    **kwargs
) -> JournalEntry:
    """
    Create a journal entry with lines and segments from distributions.
    
    Args:
        distributions: List of dicts with amount, line_type, description, segments
        date: Entry date
        description: Entry description
        currency: Currency instance
        **kwargs: Additional JournalEntry fields
    
    Returns:
        JournalEntry instance
    """
    # Create journal entry
    journal_entry = JournalEntry.objects.create(
        date=date,
        currency=currency,
        memo=description,
        posted=False,
        **kwargs
    )
    
    # Create journal lines with segments
    for dist in distributions:
        amount = Decimal(str(dist['amount']))
        line_type = dist.get('line_type', '').upper()
        
        debit = amount if line_type == 'DEBIT' else Decimal('0')
        credit = amount if line_type == 'CREDIT' else Decimal('0')
        
        # Get account segment (first segment in list should be account)
        segments_data = dist.get('segments', [])
        if not segments_data:
            raise ValueError(f"Distribution must have at least one segment (account)")
        
        # Find account segment
        account_segment_id = None
        for seg in segments_data:
            seg_type = XX_SegmentType.objects.get(pk=seg['segment_type'])
            if seg_type.segment_name.lower() == 'account':
                account_segment_id = seg['segment']
                break
        
        if not account_segment_id:
            raise ValueError(f"Distribution must include an account segment")
        
        account_segment = XX_Segment.objects.get(pk=account_segment_id)
        
        # Create journal line
        journal_line = JournalLine.objects.create(
            entry=journal_entry,
            account=account_segment,
            debit=debit,
            credit=credit
        )
        
        # Create segment assignments
        for seg_data in segments_data:
            JournalLineSegment.objects.create(
                journal_line=journal_line,
                segment_type_id=seg_data['segment_type'],
                segment_id=seg_data['segment']
            )
        
        logger.debug(f"Created journal line: {line_type} {amount} - {dist.get('description', '')}")
    
    logger.info(f"Created journal entry #{journal_entry.id} with {len(distributions)} lines")
    return journal_entry


def validate_distributions_balance(distributions: List[Dict[str, Any]]) -> bool:
    """
    Validate that distributions balance (debits = credits).
    
    Args:
        distributions: List of distribution dicts
    
    Returns:
        True if balanced
    
    Raises:
        ValueError if not balanced
    """
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    
    for dist in distributions:
        amount = Decimal(str(dist['amount']))
        line_type = dist.get('line_type', '').upper()
        
        if line_type == 'DEBIT':
            total_debit += amount
        elif line_type == 'CREDIT':
            total_credit += amount
    
    if total_debit != total_credit:
        raise ValueError(
            f"Distributions do not balance: Debits ({total_debit}) ≠ Credits ({total_credit})"
        )
    
    return True

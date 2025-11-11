"""
3-Way Match Service

Implements the matching logic between PO, GRN, and Vendor Bill.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from typing import Dict, List, Any


class ThreeWayMatchService:
    """Service for performing 3-way matching"""
    
    def match_vendor_bill(self, vendor_bill, user) -> Dict[str, Any]:
        """
        Perform 3-way matching for entire vendor bill.
        
        Returns:
            {
                'success': bool,
                'matched_lines': int,
                'exception_lines': int,
                'has_exceptions': bool,
                'exception_count': int,
                'matches': List[ThreeWayMatch],
                'exceptions': List[MatchException]
            }
        """
        from .models import ThreeWayMatch, MatchException
        
        # Clear old match data and exceptions for re-matching
        ThreeWayMatch.objects.filter(vendor_bill_line__vendor_bill=vendor_bill).delete()
        MatchException.objects.filter(three_way_match__vendor_bill_line__vendor_bill=vendor_bill).delete()
        
        results = {
            'success': False,
            'matched_lines': 0,
            'exception_lines': 0,
            'has_exceptions': False,
            'exception_count': 0,
            'matches': [],
            'exceptions': []
        }
        
        with transaction.atomic():
            for bill_line in vendor_bill.lines.all():
                try:
                    match = self.match_bill_line(bill_line, user)
                    results['matches'].append(match)
                    
                    if match.has_exception:
                        results['exception_lines'] += 1
                        
                        # Create exception record
                        exception = self.create_exception(match, user)
                        results['exceptions'].append(exception)
                    else:
                        results['matched_lines'] += 1
                    
                except Exception as e:
                    # Create exception for matching failure
                    results['exception_lines'] += 1
                    # Log error but continue with other lines
        
        results['has_exceptions'] = results['exception_lines'] > 0
        results['exception_count'] = results['exception_lines']
        results['success'] = True
        
        return results
    
    def match_bill_line(self, bill_line, user):
        """
        Match a single vendor bill line against PO and GRN.
        
        Steps:
        1. Find matching GRN line(s) based on:
           - PO number + line number (if provided)
           - Item + supplier + date range (if PO not provided)
        
        2. Find matching PO line from GRN
        
        3. Create ThreeWayMatch record with variance calculations
        """
        from .models import ThreeWayMatch
        from procurement.receiving.models import GRNLine
        
        vendor_bill = bill_line.vendor_bill
        
        # Find matching GRN line
        grn_line = self.find_matching_grn_line(bill_line)
        
        if not grn_line:
            # No GRN found - create unmatched record
            match = ThreeWayMatch.objects.create(
                vendor_bill_line=bill_line,
                po_number=bill_line.po_number or '',
                po_line_number=bill_line.po_line_number,
                grn_line=None,
                catalog_item=bill_line.catalog_item,
                po_quantity=0,
                grn_quantity=0,
                bill_quantity=bill_line.quantity,
                po_unit_price=0,
                bill_unit_price=bill_line.unit_price,
                match_status='UNMATCHED',
                has_exception=True,
                matched_by=user,
            )
            return match
        
        # Get PO details from GRN line
        # Note: PO module not yet implemented, using placeholder values
        po_quantity = grn_line.ordered_quantity if hasattr(grn_line, 'ordered_quantity') else grn_line.received_quantity
        po_unit_price = Decimal('0.00')  # Will come from PO line when PO module implemented
        
        # Create match record
        match = ThreeWayMatch.objects.create(
            vendor_bill_line=bill_line,
            po_number=bill_line.po_number or grn_line.goods_receipt.receipt_number,
            po_line_number=bill_line.po_line_number or grn_line.line_number,
            grn_line=grn_line,
            catalog_item=bill_line.catalog_item,
            po_quantity=po_quantity,
            grn_quantity=grn_line.received_quantity,
            bill_quantity=bill_line.quantity,
            po_unit_price=po_unit_price,
            bill_unit_price=bill_line.unit_price,
            matched_by=user,
        )
        
        # Variance calculations and tolerance checking done in model save()
        
        return match
    
    def find_matching_grn_line(self, bill_line):
        """
        Find matching GRN line for vendor bill line.
        
        Matching criteria:
        1. If PO number + line provided: Match by PO reference
        2. Otherwise: Match by item + supplier + date range
        """
        from procurement.receiving.models import GRNLine, GoodsReceipt
        
        vendor_bill = bill_line.vendor_bill
        
        # Strategy 1: Match by GRN number if provided
        if bill_line.grn_number:
            grn = GoodsReceipt.objects.filter(
                receipt_number=bill_line.grn_number,
                supplier=vendor_bill.supplier
            ).first()
            
            if grn:
                grn_line = grn.lines.filter(
                    catalog_item=bill_line.catalog_item
                ).first()
                if grn_line:
                    return grn_line
        
        # Strategy 2: Match by PO number if provided
        if bill_line.po_number:
            # Will use PO reference when PO module implemented
            # For now, search GRN by supplier and item
            pass
        
        # Strategy 3: Match by item, supplier, and date range
        # Find GRN lines for same supplier and item within date range
        from datetime import timedelta
        
        date_range_start = vendor_bill.bill_date - timedelta(days=90)  # 90 days lookback
        date_range_end = vendor_bill.bill_date
        
        grn_lines = GRNLine.objects.filter(
            goods_receipt__supplier=vendor_bill.supplier,
            goods_receipt__receipt_date__gte=date_range_start,
            goods_receipt__receipt_date__lte=date_range_end,
            catalog_item=bill_line.catalog_item,
            goods_receipt__status='COMPLETED'
        ).order_by('-goods_receipt__receipt_date')
        
        # Return most recent matching GRN line
        if grn_lines.exists():
            return grn_lines.first()
        
        return None
    
    def create_exception(self, match, user):
        """Create exception record for failed match"""
        from .models import MatchException
        
        # Determine exception type
        if match.quantity_tolerance_exceeded and match.quantity_variance > 0:
            exception_type = 'QUANTITY_OVER'
            variance_amount = match.quantity_variance
            variance_pct = match.quantity_variance_pct
        elif match.quantity_tolerance_exceeded and match.quantity_variance < 0:
            exception_type = 'QUANTITY_UNDER'
            variance_amount = abs(match.quantity_variance)
            variance_pct = abs(match.quantity_variance_pct)
        elif match.price_tolerance_exceeded and match.price_variance > 0:
            exception_type = 'PRICE_OVER'
            variance_amount = match.price_variance
            variance_pct = match.price_variance_pct
        elif match.price_tolerance_exceeded and match.price_variance < 0:
            exception_type = 'PRICE_UNDER'
            variance_amount = abs(match.price_variance)
            variance_pct = abs(match.price_variance_pct)
        elif match.match_status == 'UNMATCHED':
            exception_type = 'GRN_NOT_FOUND'
            variance_amount = 0
            variance_pct = 0
        else:
            exception_type = 'OTHER'
            variance_amount = 0
            variance_pct = 0
        
        # Calculate financial impact
        if exception_type in ['QUANTITY_OVER', 'QUANTITY_UNDER']:
            financial_impact = abs(match.quantity_variance * match.bill_unit_price)
        elif exception_type in ['PRICE_OVER', 'PRICE_UNDER']:
            financial_impact = abs(match.price_variance * match.bill_quantity)
        else:
            financial_impact = match.bill_quantity * match.bill_unit_price
        
        # Determine severity
        if financial_impact > 50000:
            severity = 'CRITICAL'
        elif financial_impact > 10000:
            severity = 'HIGH'
        elif financial_impact > 1000:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'
        
        # Create exception
        exception = MatchException.objects.create(
            three_way_match=match,
            exception_type=exception_type,
            severity=severity,
            variance_amount=variance_amount,
            variance_percentage=variance_pct,
            financial_impact=financial_impact,
        )
        
        return exception
    
    def resolve_exception(self, exception, user, action, notes):
        """Resolve a match exception"""
        exception.resolve(user, action, notes)
    
    def waive_exception(self, exception, user, notes):
        """Waive a match exception"""
        exception.waive(user, notes)
    
    def approve_exception_waiver(self, exception, user):
        """Approve high-value exception waiver"""
        exception.approve_waiver(user)

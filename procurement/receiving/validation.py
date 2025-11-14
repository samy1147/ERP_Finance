"""
Receiving Validation Service

Validates GRN (Goods Receipt Note) amounts and quantities against PO limits.
Ensures received amounts don't exceed purchase order amounts.
"""

from decimal import Decimal
from typing import Dict, List, Tuple
from django.db.models import Sum, Q


class GRNValidationService:
    """Service for validating GRN amounts against PO limits."""
    
    @staticmethod
    def validate_grn_against_po(po_header, grn_lines: List[Dict]) -> Dict:
        """
        Validate GRN lines against PO limits.
        
        Args:
            po_header: POHeader instance
            grn_lines: List of dicts with keys: po_line_id, received_quantity, unit_price
            
        Returns:
            Dict with validation results:
            {
                'is_valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'line_validations': List[Dict]
            }
        """
        from procurement.purchase_orders.models import POLine
        from procurement.receiving.models import GRNLine
        
        errors = []
        warnings = []
        line_validations = []
        
        if not po_header:
            return {
                'is_valid': False,
                'errors': ['No PO reference provided'],
                'warnings': [],
                'line_validations': []
            }
        
        # Get all PO lines
        po_lines = {pl.id: pl for pl in po_header.lines.all()}
        
        for grn_line in grn_lines:
            try:
                po_line_id = grn_line.get('po_line_id') or grn_line.get('po_line_reference')
                
                # Convert quantities to Decimal, handling None, empty strings, etc.
                recv_qty_raw = grn_line.get('received_quantity', 0)
                if recv_qty_raw is None or recv_qty_raw == '':
                    recv_qty_raw = 0
                received_qty = Decimal(str(recv_qty_raw))
                
                unit_price_raw = grn_line.get('unit_price', 0)
                if unit_price_raw is None or unit_price_raw == '':
                    unit_price_raw = 0
                unit_price = Decimal(str(unit_price_raw))
                
            except (ValueError, TypeError, ArithmeticError) as e:
                line_validations.append({
                    'line': grn_line.get('line_number', 'Unknown'),
                    'valid': False,
                    'errors': [f'Invalid numeric value: {str(e)}'],
                    'warnings': []
                })
                errors.append(f"Line {grn_line.get('line_number', 'Unknown')}: Invalid numeric value")
                continue
            
            if not po_line_id:
                line_validations.append({
                    'line': grn_line.get('line_number', 'Unknown'),
                    'valid': False,
                    'errors': ['No PO line reference provided'],
                    'warnings': []
                })
                errors.append(f"Line {grn_line.get('line_number', 'Unknown')}: No PO line reference")
                continue
            
            po_line = po_lines.get(int(po_line_id))
            if not po_line:
                line_validations.append({
                    'line': grn_line.get('line_number', 'Unknown'),
                    'valid': False,
                    'errors': [f'PO line {po_line_id} not found'],
                    'warnings': []
                })
                errors.append(f"Line {grn_line.get('line_number', 'Unknown')}: PO line not found")
                continue
            
            # Get previously received quantity for this PO line
            previous_receipts = GRNLine.objects.filter(
                po_line_reference=po_line_id,
                goods_receipt__status__in=['DRAFT', 'SUBMITTED', 'COMPLETED']
            ).exclude(
                goods_receipt_id=grn_line.get('goods_receipt_id')  # Exclude current GRN if editing
            ).aggregate(
                total_received=Sum('received_quantity')
            )
            
            previously_received = previous_receipts['total_received'] or Decimal('0')
            total_to_receive = previously_received + received_qty
            ordered_qty = po_line.quantity
            
            line_errors = []
            line_warnings = []
            
            # Validate quantity
            if total_to_receive > ordered_qty:
                over_qty = total_to_receive - ordered_qty
                line_errors.append(
                    f"Receiving {received_qty} exceeds PO quantity. "
                    f"Ordered: {ordered_qty}, Previously received: {previously_received}, "
                    f"Over by: {over_qty}"
                )
                errors.append(
                    f"Line {grn_line.get('line_number', 'Unknown')} ({po_line.item_description}): "
                    f"Over-receipt by {over_qty}"
                )
            elif total_to_receive == ordered_qty:
                line_warnings.append(f"This receipt will complete the PO line (all {ordered_qty} units received)")
            
            # Validate unit price (with tolerance)
            po_unit_price = po_line.unit_price
            
            # Only validate price if it was provided in the GRN line
            # (price might be fetched from PO later in the process)
            if unit_price and unit_price > 0:
                price_variance_pct = abs((unit_price - po_unit_price) / po_unit_price * 100) if po_unit_price else 0
                
                # 5% tolerance for price variance
                if price_variance_pct > 5:
                    line_errors.append(
                        f"Unit price {unit_price} differs from PO price {po_unit_price} "
                        f"by {price_variance_pct:.1f}% (exceeds 5% tolerance)"
                    )
                    errors.append(
                        f"Line {grn_line.get('line_number', 'Unknown')} ({po_line.item_description}): "
                        f"Price variance {price_variance_pct:.1f}%"
                    )
                elif price_variance_pct > 0:
                    line_warnings.append(
                        f"Unit price {unit_price} differs from PO price {po_unit_price} "
                        f"by {price_variance_pct:.1f}%"
                    )
            
            # Calculate line amount
            line_amount = received_qty * unit_price if unit_price else Decimal('0')
            po_line_amount = ordered_qty * po_unit_price
            
            # Calculate price variance for reporting (even if not validated)
            price_variance = unit_price - po_unit_price if unit_price else Decimal('0')
            price_variance_pct = abs(price_variance / po_unit_price * 100) if (po_unit_price and unit_price) else Decimal('0')
            
            line_validations.append({
                'line': grn_line.get('line_number', 'Unknown'),
                'item_description': po_line.item_description,
                'valid': len(line_errors) == 0,
                'errors': line_errors,
                'warnings': line_warnings,
                'quantities': {
                    'ordered': float(ordered_qty),
                    'previously_received': float(previously_received),
                    'current_receipt': float(received_qty),
                    'total_received': float(total_to_receive),
                    'remaining': float(ordered_qty - total_to_receive)
                },
                'prices': {
                    'po_unit_price': float(po_unit_price),
                    'receipt_unit_price': float(unit_price) if unit_price else 0.0,
                    'variance_pct': float(price_variance_pct)
                },
                'amounts': {
                    'line_amount': float(line_amount),
                    'po_line_amount': float(po_line_amount)
                }
            })
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'line_validations': line_validations
        }
    
    @staticmethod
    def get_po_receiving_status(po_header) -> Dict:
        """
        Get receiving status for a PO.
        
        Returns:
            Dict with receiving status information
        """
        from procurement.receiving.models import GRNLine
        from django.db.models import Sum
        
        lines_status = []
        total_lines = 0
        fully_received_lines = 0
        partially_received_lines = 0
        not_received_lines = 0
        
        for po_line in po_header.lines.all():
            total_lines += 1
            
            # Get received quantity for this PO line
            receipts = GRNLine.objects.filter(
                po_line_reference=po_line.id,
                goods_receipt__status__in=['SUBMITTED', 'COMPLETED']
            ).aggregate(
                total_received=Sum('received_quantity')
            )
            
            received_qty = receipts['total_received'] or Decimal('0')
            ordered_qty = po_line.quantity
            remaining_qty = ordered_qty - received_qty
            
            if received_qty == 0:
                status = 'NOT_RECEIVED'
                not_received_lines += 1
            elif received_qty >= ordered_qty:
                status = 'FULLY_RECEIVED'
                fully_received_lines += 1
            else:
                status = 'PARTIALLY_RECEIVED'
                partially_received_lines += 1
            
            lines_status.append({
                'line_number': po_line.line_number,
                'item_description': po_line.item_description,
                'ordered_quantity': float(ordered_qty),
                'received_quantity': float(received_qty),
                'remaining_quantity': float(remaining_qty),
                'status': status,
                'percent_received': float(received_qty / ordered_qty * 100) if ordered_qty else 0
            })
        
        # Overall PO receiving status
        if fully_received_lines == total_lines:
            overall_status = 'FULLY_RECEIVED'
        elif not_received_lines == total_lines:
            overall_status = 'NOT_RECEIVED'
        else:
            overall_status = 'PARTIALLY_RECEIVED'
        
        return {
            'po_number': po_header.po_number,
            'overall_status': overall_status,
            'total_lines': total_lines,
            'fully_received_lines': fully_received_lines,
            'partially_received_lines': partially_received_lines,
            'not_received_lines': not_received_lines,
            'lines_status': lines_status
        }

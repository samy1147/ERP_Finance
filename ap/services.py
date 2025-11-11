"""
AP (Accounts Payable) Services
3-Way Match and Invoice Validation Services
"""
from decimal import Decimal
from django.utils import timezone
from django.db import transaction


class ThreeWayMatchService:
    """
    Service for performing 3-way match on AP Invoices.
    Compares: PO → GRN → Invoice
    
    Validates:
    - Quantity match (Invoice qty <= GRN received qty)
    - Price match (Invoice price vs PO price within tolerance)
    - Total amount match
    """
    
    # Default tolerances (can be overridden)
    DEFAULT_QUANTITY_TOLERANCE = Decimal('5.0')  # 5% tolerance
    DEFAULT_PRICE_TOLERANCE = Decimal('2.0')     # 2% tolerance
    DEFAULT_AMOUNT_TOLERANCE = Decimal('5.0')    # 5% tolerance
    
    def __init__(self, invoice):
        """
        Initialize 3-way match service for an invoice.
        
        Args:
            invoice: APInvoice instance
        """
        self.invoice = invoice
        self.variances = []
        self.total_variance = Decimal('0.00')
        
    def perform_match(self):
        """
        Perform 3-way match validation.
        
        Returns:
            dict: {
                'status': 'MATCHED' | 'VARIANCE' | 'FAILED',
                'variances': list of variance details,
                'total_variance_amount': Decimal,
                'notes': str
            }
        """
        # Check if 3-way match is applicable
        if not self.invoice.goods_receipt:
            return {
                'status': 'NOT_REQUIRED',
                'variances': [],
                'total_variance_amount': Decimal('0.00'),
                'notes': 'No GRN linked - 3-way match not required'
            }
        
        if not self.invoice.po_header:
            return {
                'status': 'FAILED',
                'variances': ['No PO linked to invoice'],
                'total_variance_amount': Decimal('0.00'),
                'notes': 'PO reference required for 3-way match'
            }
        
        # Get related data
        grn = self.invoice.goods_receipt
        po = self.invoice.po_header
        
        # Match invoice lines against GRN and PO
        self._match_lines(grn, po)
        
        # Determine overall status
        if len(self.variances) == 0:
            status = 'MATCHED'
            notes = 'All items matched successfully within tolerance'
        elif self.total_variance > Decimal('100.00'):  # Significant variance
            status = 'FAILED'
            notes = f'Significant variances detected. Total variance: {self.total_variance}'
        else:
            status = 'VARIANCE'
            notes = f'Minor variances detected. Total variance: {self.total_variance}'
        
        return {
            'status': status,
            'variances': self.variances,
            'total_variance_amount': self.total_variance,
            'notes': notes
        }
    
    def _match_lines(self, grn, po):
        """
        Match invoice lines against GRN and PO lines.
        
        Args:
            grn: GoodsReceipt instance
            po: POHeader instance
        """
        invoice_items = self.invoice.items.all()
        grn_lines = grn.lines.all()
        po_lines = po.lines.all()
        
        # Create lookup dictionaries
        grn_lines_dict = {line.po_line_reference: line for line in grn_lines if line.po_line_reference}
        po_lines_dict = {str(line.id): line for line in po_lines}
        
        for invoice_item in invoice_items:
            # Try to match with GRN/PO
            # Assumption: invoice item description matches GRN item description
            matched_grn_line = self._find_matching_grn_line(invoice_item, grn_lines)
            
            if not matched_grn_line:
                self.variances.append({
                    'item': invoice_item.description,
                    'type': 'NO_MATCH',
                    'message': f'Invoice item "{invoice_item.description}" not found in GRN'
                })
                continue
            
            # Get corresponding PO line
            po_line = po_lines_dict.get(str(matched_grn_line.po_line_reference))
            
            if not po_line:
                self.variances.append({
                    'item': invoice_item.description,
                    'type': 'NO_PO_LINE',
                    'message': f'No PO line found for GRN line reference {matched_grn_line.po_line_reference}'
                })
                continue
            
            # Validate quantity
            self._validate_quantity(invoice_item, matched_grn_line, po_line)
            
            # Validate price
            self._validate_price(invoice_item, matched_grn_line, po_line)
            
            # Validate line total
            self._validate_line_total(invoice_item, matched_grn_line, po_line)
    
    def _find_matching_grn_line(self, invoice_item, grn_lines):
        """Find GRN line matching the invoice item."""
        # Match by description (simple approach)
        for grn_line in grn_lines:
            if grn_line.item_description.lower().strip() == invoice_item.description.lower().strip():
                return grn_line
        return None
    
    def _validate_quantity(self, invoice_item, grn_line, po_line):
        """Validate invoice quantity against GRN received quantity."""
        invoice_qty = Decimal(str(invoice_item.quantity))
        grn_qty = grn_line.received_quantity
        po_qty = po_line.quantity
        
        # Invoice qty should not exceed GRN received qty
        if invoice_qty > grn_qty:
            variance_qty = invoice_qty - grn_qty
            self.variances.append({
                'item': invoice_item.description,
                'type': 'QUANTITY_OVER',
                'message': f'Invoice qty ({invoice_qty}) exceeds GRN received qty ({grn_qty})',
                'invoice_qty': float(invoice_qty),
                'grn_qty': float(grn_qty),
                'variance_qty': float(variance_qty)
            })
        
        # Check tolerance
        tolerance = self.DEFAULT_QUANTITY_TOLERANCE
        variance_pct = abs((invoice_qty - grn_qty) / grn_qty * 100) if grn_qty > 0 else Decimal('0')
        
        if variance_pct > tolerance:
            self.variances.append({
                'item': invoice_item.description,
                'type': 'QUANTITY_VARIANCE',
                'message': f'Quantity variance {variance_pct:.2f}% exceeds tolerance {tolerance}%',
                'invoice_qty': float(invoice_qty),
                'grn_qty': float(grn_qty),
                'variance_pct': float(variance_pct)
            })
    
    def _validate_price(self, invoice_item, grn_line, po_line):
        """Validate invoice unit price against PO unit price."""
        invoice_price = Decimal(str(invoice_item.unit_price))
        po_price = po_line.unit_price
        
        # Check if prices match within tolerance
        tolerance = self.DEFAULT_PRICE_TOLERANCE
        variance_pct = abs((invoice_price - po_price) / po_price * 100) if po_price > 0 else Decimal('0')
        
        if variance_pct > tolerance:
            variance_amount = abs(invoice_price - po_price) * Decimal(str(invoice_item.quantity))
            self.total_variance += variance_amount
            
            self.variances.append({
                'item': invoice_item.description,
                'type': 'PRICE_VARIANCE',
                'message': f'Price variance {variance_pct:.2f}% exceeds tolerance {tolerance}%',
                'invoice_price': float(invoice_price),
                'po_price': float(po_price),
                'variance_pct': float(variance_pct),
                'variance_amount': float(variance_amount)
            })
    
    def _validate_line_total(self, invoice_item, grn_line, po_line):
        """Validate invoice line total."""
        invoice_qty = Decimal(str(invoice_item.quantity))
        invoice_price = Decimal(str(invoice_item.unit_price))
        invoice_total = invoice_qty * invoice_price
        
        # Expected total based on GRN qty and PO price
        expected_total = grn_line.received_quantity * po_line.unit_price
        
        # Check tolerance
        tolerance = self.DEFAULT_AMOUNT_TOLERANCE
        if expected_total > 0:
            variance_pct = abs((invoice_total - expected_total) / expected_total * 100)
        else:
            variance_pct = Decimal('0')
        
        if variance_pct > tolerance:
            variance_amount = abs(invoice_total - expected_total)
            self.total_variance += variance_amount
            
            self.variances.append({
                'item': invoice_item.description,
                'type': 'AMOUNT_VARIANCE',
                'message': f'Line total variance {variance_pct:.2f}% exceeds tolerance {tolerance}%',
                'invoice_total': float(invoice_total),
                'expected_total': float(expected_total),
                'variance_pct': float(variance_pct),
                'variance_amount': float(variance_amount)
            })
    
    @transaction.atomic
    def update_invoice_match_status(self):
        """
        Perform match and update invoice with results.
        """
        result = self.perform_match()
        
        # Update invoice
        self.invoice.three_way_match_status = result['status']
        self.invoice.match_variance_amount = result['total_variance_amount']
        self.invoice.match_variance_notes = f"{result['notes']}\n\nVariances:\n" + \
                                           '\n'.join([v.get('message', str(v)) for v in result['variances']])
        self.invoice.match_performed_at = timezone.now()
        self.invoice.save()
        
        return result


def perform_three_way_match(invoice):
    """
    Convenience function to perform 3-way match on an invoice.
    
    Args:
        invoice: APInvoice instance
        
    Returns:
        dict: Match result
    """
    service = ThreeWayMatchService(invoice)
    return service.update_invoice_match_status()

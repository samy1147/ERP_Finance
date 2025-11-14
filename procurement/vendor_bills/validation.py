"""
3-Way Match Validation Service

Validates vendor bills against PO and GRN with comprehensive variance detection.
Implements strict 3-way matching: PO ↔ GRN ↔ AP Invoice
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.db.models import Sum


class ThreeWayMatchValidator:
    """Service for 3-way match validation between PO, GRN, and AP Invoice."""
    
    # Tolerance thresholds
    QUANTITY_TOLERANCE_PCT = Decimal('2.0')  # 2% tolerance for quantity variance
    PRICE_TOLERANCE_PCT = Decimal('5.0')     # 5% tolerance for price variance
    AMOUNT_TOLERANCE = Decimal('10.00')      # $10 tolerance for amount variance
    
    @staticmethod
    def validate_vendor_bill_against_grn(grn_header, bill_lines: List[Dict]) -> Dict:
        """
        Validate vendor bill lines against GRN (Goods Receipt Note).
        
        Args:
            grn_header: GoodsReceipt instance
            bill_lines: List of dicts with keys: grn_line_id, quantity, unit_price, line_total
            
        Returns:
            Dict with validation results:
            {
                'is_valid': bool,
                'can_proceed': bool,  # Can proceed with warnings but not with errors
                'errors': List[str],
                'warnings': List[str],
                'variances': List[Dict],
                'line_validations': List[Dict]
            }
        """
        from procurement.receiving.models import GRNLine
        
        errors = []
        warnings = []
        variances = []
        line_validations = []
        blocking_issues = 0
        
        if not grn_header:
            return {
                'is_valid': False,
                'can_proceed': False,
                'errors': ['No GRN reference provided'],
                'warnings': [],
                'variances': [],
                'line_validations': []
            }
        
        # Get all GRN lines
        grn_lines = {gl.id: gl for gl in grn_header.lines.all()}
        
        for bill_line in bill_lines:
            grn_line_id = bill_line.get('grn_line_id') or bill_line.get('grn_line_reference')
            bill_qty = Decimal(str(bill_line.get('quantity', 0)))
            bill_unit_price = Decimal(str(bill_line.get('unit_price', 0)))
            bill_line_total = Decimal(str(bill_line.get('line_total', bill_qty * bill_unit_price)))
            
            if not grn_line_id:
                line_validations.append({
                    'line': bill_line.get('line_number', 'Unknown'),
                    'valid': False,
                    'errors': ['No GRN line reference provided'],
                    'warnings': [],
                    'variances': []
                })
                errors.append(f"Line {bill_line.get('line_number', 'Unknown')}: No GRN line reference")
                blocking_issues += 1
                continue
            
            grn_line = grn_lines.get(int(grn_line_id))
            if not grn_line:
                line_validations.append({
                    'line': bill_line.get('line_number', 'Unknown'),
                    'valid': False,
                    'errors': [f'GRN line {grn_line_id} not found'],
                    'warnings': [],
                    'variances': []
                })
                errors.append(f"Line {bill_line.get('line_number', 'Unknown')}: GRN line not found")
                blocking_issues += 1
                continue
            
            line_errors = []
            line_warnings = []
            line_variances = []
            
            # === QUANTITY VARIANCE ===
            grn_qty = grn_line.received_quantity
            qty_variance = bill_qty - grn_qty
            qty_variance_pct = abs(qty_variance / grn_qty * 100) if grn_qty else 0
            
            if bill_qty > grn_qty:
                if qty_variance_pct > ThreeWayMatchValidator.QUANTITY_TOLERANCE_PCT:
                    line_errors.append(
                        f"Invoice quantity {bill_qty} exceeds received quantity {grn_qty} "
                        f"by {qty_variance} ({qty_variance_pct:.1f}%, tolerance: {ThreeWayMatchValidator.QUANTITY_TOLERANCE_PCT}%)"
                    )
                    errors.append(
                        f"Line {bill_line.get('line_number', 'Unknown')} ({grn_line.item_description}): "
                        f"Over-billed by {qty_variance} units"
                    )
                    blocking_issues += 1
                    line_variances.append({
                        'type': 'QUANTITY_OVER',
                        'severity': 'ERROR',
                        'expected': float(grn_qty),
                        'actual': float(bill_qty),
                        'variance': float(qty_variance),
                        'variance_pct': float(qty_variance_pct),
                        'message': f"Invoiced quantity exceeds received quantity"
                    })
                else:
                    line_warnings.append(
                        f"Invoice quantity {bill_qty} exceeds received quantity {grn_qty} "
                        f"by {qty_variance} (within {ThreeWayMatchValidator.QUANTITY_TOLERANCE_PCT}% tolerance)"
                    )
                    line_variances.append({
                        'type': 'QUANTITY_OVER',
                        'severity': 'WARNING',
                        'expected': float(grn_qty),
                        'actual': float(bill_qty),
                        'variance': float(qty_variance),
                        'variance_pct': float(qty_variance_pct),
                        'message': f"Minor over-billing within tolerance"
                    })
            elif bill_qty < grn_qty:
                line_warnings.append(
                    f"Invoice quantity {bill_qty} is less than received quantity {grn_qty} "
                    f"by {abs(qty_variance)}"
                )
                line_variances.append({
                    'type': 'QUANTITY_UNDER',
                    'severity': 'WARNING',
                    'expected': float(grn_qty),
                    'actual': float(bill_qty),
                    'variance': float(qty_variance),
                    'variance_pct': float(qty_variance_pct),
                    'message': f"Invoiced less than received (partial billing)"
                })
            
            # === UNIT PRICE VARIANCE ===
            grn_unit_price = grn_line.unit_price
            price_variance = bill_unit_price - grn_unit_price
            price_variance_pct = abs(price_variance / grn_unit_price * 100) if grn_unit_price else 0
            
            if price_variance_pct > ThreeWayMatchValidator.PRICE_TOLERANCE_PCT:
                line_errors.append(
                    f"Invoice unit price {bill_unit_price} differs from GRN price {grn_unit_price} "
                    f"by {price_variance_pct:.1f}% (exceeds {ThreeWayMatchValidator.PRICE_TOLERANCE_PCT}% tolerance)"
                )
                errors.append(
                    f"Line {bill_line.get('line_number', 'Unknown')} ({grn_line.item_description}): "
                    f"Price variance {price_variance_pct:.1f}%"
                )
                blocking_issues += 1
                line_variances.append({
                    'type': 'PRICE_VARIANCE',
                    'severity': 'ERROR',
                    'expected': float(grn_unit_price),
                    'actual': float(bill_unit_price),
                    'variance': float(price_variance),
                    'variance_pct': float(price_variance_pct),
                    'message': f"Unit price variance exceeds tolerance"
                })
            elif price_variance_pct > 0:
                line_warnings.append(
                    f"Invoice unit price {bill_unit_price} differs from GRN price {grn_unit_price} "
                    f"by {price_variance_pct:.1f}% (within tolerance)"
                )
                line_variances.append({
                    'type': 'PRICE_VARIANCE',
                    'severity': 'WARNING',
                    'expected': float(grn_unit_price),
                    'actual': float(bill_unit_price),
                    'variance': float(price_variance),
                    'variance_pct': float(price_variance_pct),
                    'message': f"Minor price variance within tolerance"
                })
            
            # === AMOUNT VARIANCE ===
            grn_line_total = grn_qty * grn_unit_price
            amount_variance = bill_line_total - grn_line_total
            amount_variance_pct = abs(amount_variance / grn_line_total * 100) if grn_line_total else 0
            
            if abs(amount_variance) > ThreeWayMatchValidator.AMOUNT_TOLERANCE:
                line_variances.append({
                    'type': 'AMOUNT_VARIANCE',
                    'severity': 'WARNING',
                    'expected': float(grn_line_total),
                    'actual': float(bill_line_total),
                    'variance': float(amount_variance),
                    'variance_pct': float(amount_variance_pct),
                    'message': f"Line total variance: {amount_variance}"
                })
            
            line_validations.append({
                'line': bill_line.get('line_number', 'Unknown'),
                'item_description': grn_line.item_description,
                'valid': len(line_errors) == 0,
                'errors': line_errors,
                'warnings': line_warnings,
                'variances': line_variances,
                'quantities': {
                    'grn_received': float(grn_qty),
                    'invoice_quantity': float(bill_qty),
                    'variance': float(qty_variance)
                },
                'prices': {
                    'grn_unit_price': float(grn_unit_price),
                    'invoice_unit_price': float(bill_unit_price),
                    'variance': float(price_variance),
                    'variance_pct': float(price_variance_pct)
                },
                'amounts': {
                    'grn_line_total': float(grn_line_total),
                    'invoice_line_total': float(bill_line_total),
                    'variance': float(amount_variance)
                }
            })
            
            variances.extend(line_variances)
        
        return {
            'is_valid': len(errors) == 0,
            'can_proceed': blocking_issues == 0,  # Can proceed if only warnings
            'errors': errors,
            'warnings': warnings,
            'variances': variances,
            'line_validations': line_validations,
            'summary': {
                'total_lines': len(bill_lines),
                'valid_lines': sum(1 for lv in line_validations if lv['valid']),
                'lines_with_errors': sum(1 for lv in line_validations if not lv['valid']),
                'lines_with_warnings': sum(1 for lv in line_validations if lv['warnings']),
                'blocking_issues': blocking_issues,
                'total_variances': len(variances)
            }
        }
    
    @staticmethod
    def validate_full_3way_match(po_header, grn_header, bill_lines: List[Dict]) -> Dict:
        """
        Perform complete 3-way match validation: PO ↔ GRN ↔ Invoice.
        
        Args:
            po_header: POHeader instance
            grn_header: GoodsReceipt instance
            bill_lines: List of vendor bill line dicts
            
        Returns:
            Dict with comprehensive validation results
        """
        from procurement.purchase_orders.models import POLine
        from procurement.receiving.models import GRNLine
        
        errors = []
        warnings = []
        variances = []
        
        if not po_header:
            return {
                'is_valid': False,
                'can_proceed': False,
                'errors': ['No PO reference provided for 3-way match'],
                'warnings': [],
                'variances': [],
                'line_validations': []
            }
        
        if not grn_header:
            return {
                'is_valid': False,
                'can_proceed': False,
                'errors': ['No GRN reference provided for 3-way match'],
                'warnings': [],
                'variances': [],
                'line_validations': []
            }
        
        # Validate GRN belongs to PO
        if grn_header.po_header_id != po_header.id:
            return {
                'is_valid': False,
                'can_proceed': False,
                'errors': [f'GRN {grn_header.grn_number} is not linked to PO {po_header.po_number}'],
                'warnings': [],
                'variances': [],
                'line_validations': []
            }
        
        # First validate against GRN
        grn_validation = ThreeWayMatchValidator.validate_vendor_bill_against_grn(
            grn_header, bill_lines
        )
        
        # Add PO-level validations
        po_lines = {pl.id: pl for pl in po_header.lines.all()}
        grn_lines = {gl.id: gl for gl in grn_header.lines.all()}
        
        line_validations = grn_validation['line_validations']
        
        # Enhance validations with PO data
        for i, bill_line in enumerate(bill_lines):
            grn_line_id = bill_line.get('grn_line_id') or bill_line.get('grn_line_reference')
            if not grn_line_id:
                continue
            
            grn_line = grn_lines.get(int(grn_line_id))
            if not grn_line or not grn_line.po_line_reference:
                continue
            
            po_line = po_lines.get(int(grn_line.po_line_reference))
            if not po_line:
                continue
            
            # Compare invoice against original PO
            bill_qty = Decimal(str(bill_line.get('quantity', 0)))
            bill_unit_price = Decimal(str(bill_line.get('unit_price', 0)))
            
            po_qty = po_line.quantity
            po_unit_price = po_line.unit_price
            
            # Check if invoice quantity exceeds PO quantity
            if bill_qty > po_qty:
                variances.append({
                    'type': 'PO_QUANTITY_EXCEEDED',
                    'severity': 'ERROR',
                    'line': bill_line.get('line_number', 'Unknown'),
                    'po_quantity': float(po_qty),
                    'invoice_quantity': float(bill_qty),
                    'message': f"Invoice quantity {bill_qty} exceeds PO quantity {po_qty}"
                })
            
            # Check PO price vs invoice price
            po_price_variance_pct = abs((bill_unit_price - po_unit_price) / po_unit_price * 100) if po_unit_price else 0
            if po_price_variance_pct > ThreeWayMatchValidator.PRICE_TOLERANCE_PCT:
                variances.append({
                    'type': 'PO_PRICE_VARIANCE',
                    'severity': 'WARNING',
                    'line': bill_line.get('line_number', 'Unknown'),
                    'po_unit_price': float(po_unit_price),
                    'invoice_unit_price': float(bill_unit_price),
                    'variance_pct': float(po_price_variance_pct),
                    'message': f"Invoice price differs from PO price by {po_price_variance_pct:.1f}%"
                })
            
            # Add PO reference to line validation
            if i < len(line_validations):
                line_validations[i]['po_reference'] = {
                    'po_number': po_header.po_number,
                    'po_line_number': po_line.line_number,
                    'po_quantity': float(po_qty),
                    'po_unit_price': float(po_unit_price),
                    'po_line_total': float(po_qty * po_unit_price)
                }
        
        return {
            'is_valid': grn_validation['is_valid'] and len([v for v in variances if v['severity'] == 'ERROR']) == 0,
            'can_proceed': grn_validation['can_proceed'],
            'errors': grn_validation['errors'] + [v['message'] for v in variances if v['severity'] == 'ERROR'],
            'warnings': grn_validation['warnings'] + [v['message'] for v in variances if v['severity'] == 'WARNING'],
            'variances': grn_validation['variances'] + variances,
            'line_validations': line_validations,
            'summary': {
                **grn_validation['summary'],
                'po_variances': len([v for v in variances if v['type'].startswith('PO_')])
            },
            'match_status': {
                'po_number': po_header.po_number,
                'grn_number': grn_header.grn_number,
                'match_type': '3-WAY',
                'all_documents_matched': True
            }
        }

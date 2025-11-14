"""
PR to PO Conversion Services.

This module handles the conversion of Purchase Requisitions to Purchase Orders,
supporting:
- Selection of specific PR lines to convert
- Consolidation of multiple PR lines into one PO
- Splitting of PR lines across multiple POs
- Many-to-many relationship tracking
"""

from decimal import Decimal
from typing import List, Dict, Optional
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone

from .models import PRHeader, PRLine, PRToPOLineMapping
from procurement.purchase_orders.models import POHeader, POLine


class PRToPOConversionService:
    """
    Service for converting Purchase Requisitions to Purchase Orders.
    
    Supports flexible conversion patterns:
    - One PR → One PO (simple conversion)
    - One PR → Multiple POs (split by vendor/delivery)
    - Multiple PRs → One PO (consolidation)
    - Partial PR line conversion
    """
    
    @staticmethod
    @transaction.atomic
    def convert_pr_lines_to_po(
        pr_line_selections: List[Dict],
        title: str = '',
        vendor_name: str = '',
        vendor_email: str = '',
        vendor_phone: str = '',
        delivery_date: Optional[str] = None,
        delivery_address: str = '',
        special_instructions: str = '',
        created_by: User = None,
        **kwargs
    ) -> POHeader:
        """
        Convert selected PR lines to a Purchase Order.
        
        Args:
            pr_line_selections: List of dicts with:
                - pr_line_id: ID of PR line
                - quantity: Quantity to convert (can be partial)
                - unit_price: Price per unit
                - notes: Optional notes about this conversion
            title: PO title (if not provided, auto-generated)
            vendor_name: Vendor/Supplier name (optional, can be set later)
            vendor_email: Vendor email
            vendor_phone: Vendor phone
            delivery_date: Expected delivery date
            delivery_address: Delivery address
            special_instructions: Special instructions for vendor
            created_by: User creating the PO
            **kwargs: Additional PO header fields
        
        Returns:
            Created POHeader instance
        
        Raises:
            ValueError: If validation fails
        """
        
        if not pr_line_selections:
            raise ValueError("No PR lines selected for conversion")
        
        if not title:
            raise ValueError("PO Title is required")
        
        # Validate all PR lines and load them
        pr_lines_data = []
        pr_headers = set()
        total_amount = Decimal('0.00')
        currency = None
        
        for selection in pr_line_selections:
            pr_line_id = selection.get('pr_line_id')
            quantity = Decimal(str(selection.get('quantity', 0)))
            unit_price = Decimal(str(selection.get('unit_price', 0)))
            
            if not pr_line_id:
                raise ValueError("pr_line_id is required for each selection")
            
            if quantity <= 0:
                raise ValueError(f"Invalid quantity {quantity} for PR line {pr_line_id}")
            
            try:
                pr_line = PRLine.objects.select_related('pr_header', 'unit_of_measure').get(id=pr_line_id)
            except PRLine.DoesNotExist:
                raise ValueError(f"PR Line {pr_line_id} not found")
            
            # Validate PR header is approved
            if pr_line.pr_header.status != 'APPROVED':
                raise ValueError(
                    f"PR {pr_line.pr_header.pr_number} is not approved. "
                    f"Only approved PRs can be converted to PO."
                )
            
            # Validate quantity available
            if quantity > pr_line.quantity_remaining:
                raise ValueError(
                    f"Cannot convert {quantity} units from PR line {pr_line_id}. "
                    f"Only {pr_line.quantity_remaining} units remaining."
                )
            
            # Track PR headers
            pr_headers.add(pr_line.pr_header)
            
            # Track currency (all lines must have same currency)
            if currency is None:
                currency = pr_line.pr_header.currency
            elif currency != pr_line.pr_header.currency:
                raise ValueError("All PR lines must have the same currency")
            
            # Calculate line total
            line_total = quantity * unit_price
            total_amount += line_total
            
            pr_lines_data.append({
                'pr_line': pr_line,
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': line_total,
                'notes': selection.get('notes', ''),
            })
        
        # Generate title if not provided
        if not title:
            title = f"PO from {len(pr_headers)} PR(s)"
        
        # Determine PO Type from PRs
        # Priority: SERVICES > CATEGORIZED_GOODS > UNCATEGORIZED_GOODS
        # If any PR is SERVICES, the entire PO is SERVICES
        # If any PR is CATEGORIZED_GOODS (and no SERVICES), PO is CATEGORIZED_GOODS
        # Otherwise, PO is UNCATEGORIZED_GOODS
        pr_types = {pr.pr_type for pr in pr_headers}
        if 'SERVICES' in pr_types:
            po_type = 'SERVICES'
        elif 'CATEGORIZED_GOODS' in pr_types:
            po_type = 'CATEGORIZED_GOODS'
        else:
            po_type = 'UNCATEGORIZED_GOODS'
        
        # Create PO Header
        po_header = POHeader(
            title=title,
            po_type=po_type,  # Copy from PR type
            vendor_name=vendor_name,
            vendor_email=vendor_email,
            vendor_phone=vendor_phone,
            delivery_date=delivery_date,
            delivery_address=delivery_address,
            special_instructions=special_instructions,
            currency=currency,
            subtotal=total_amount,
            total_amount=total_amount,
            description=f"Created from PR(s): {', '.join(pr.pr_number for pr in pr_headers)}",
            created_by=created_by,
            status='DRAFT',
            **kwargs
        )
        po_header.save()
        
        # Link source PR headers
        po_header.source_pr_headers.set(pr_headers)
        
        # Create PO Lines and Mappings
        line_number = 10
        for line_data in pr_lines_data:
            pr_line = line_data['pr_line']
            quantity = line_data['quantity']
            unit_price = line_data['unit_price']
            
            # Create PO Line
            po_line = POLine(
                po_header=po_header,
                line_number=line_number,
                item_description=pr_line.item_description,
                specifications=pr_line.specifications,
                catalog_item=pr_line.catalog_item,
                item_type=pr_line.item_type,  # Copy item categorization status from PR
                quantity=quantity,
                unit_of_measure=pr_line.unit_of_measure,
                unit_price=unit_price,
                line_total=line_data['line_total'],
                need_by_date=pr_line.need_by_date,
                notes=line_data['notes'],
            )
            po_line.save()
            
            # Create mapping between PR line and PO line
            mapping = PRToPOLineMapping(
                pr_line=pr_line,
                po_line=po_line,
                quantity_converted=quantity,
                created_by=created_by,
                notes=line_data['notes']
            )
            mapping.save()
            
            line_number += 10
        
        # Recalculate PO totals
        po_header.calculate_totals()
        po_header.save()
        
        return po_header
    
    @staticmethod
    def get_convertible_pr_lines(pr_header_ids: Optional[List[int]] = None) -> List[PRLine]:
        """
        Get PR lines that can be converted to PO.
        
        Args:
            pr_header_ids: Optional list of PR header IDs to filter
        
        Returns:
            QuerySet of PR lines that can be converted
        """
        from django.db.models import Q
        
        queryset = PRLine.objects.select_related(
            'pr_header', 'pr_header__requestor', 'pr_header__cost_center',
            'catalog_item', 'unit_of_measure'
        ).filter(
            pr_header__status='APPROVED',
            conversion_status__in=['NOT_CONVERTED', 'PARTIALLY_CONVERTED']
        )
        
        if pr_header_ids:
            queryset = queryset.filter(pr_header_id__in=pr_header_ids)
        
        return queryset.order_by('pr_header__pr_number', 'line_number')
    
    @staticmethod
    def get_pr_conversion_summary(pr_header: PRHeader) -> Dict:
        """
        Get conversion summary for a PR.
        
        Args:
            pr_header: PRHeader instance
        
        Returns:
            Dict with conversion statistics
        """
        lines = pr_header.lines.all()
        total_lines = lines.count()
        
        not_converted = lines.filter(conversion_status='NOT_CONVERTED').count()
        partially_converted = lines.filter(conversion_status='PARTIALLY_CONVERTED').count()
        fully_converted = lines.filter(conversion_status='FULLY_CONVERTED').count()
        
        # Get all POs created from this PR
        pos = POHeader.objects.filter(source_pr_headers=pr_header).distinct()
        
        return {
            'pr_number': pr_header.pr_number,
            'pr_status': pr_header.status,
            'total_lines': total_lines,
            'not_converted': not_converted,
            'partially_converted': partially_converted,
            'fully_converted': fully_converted,
            'conversion_percentage': (fully_converted / total_lines * 100) if total_lines > 0 else 0,
            'related_pos': [
                {
                    'po_number': po.po_number,
                    'vendor': po.vendor_name,
                    'total_amount': str(po.total_amount),
                    'status': po.status,
                }
                for po in pos
            ]
        }
    
    @staticmethod
    def consolidate_pr_lines_by_vendor(pr_lines: List[PRLine]) -> Dict[str, List[PRLine]]:
        """
        Group PR lines by suggested supplier for consolidated PO creation.
        
        Args:
            pr_lines: List of PRLine instances
        
        Returns:
            Dict mapping vendor names to lists of PR lines
        """
        vendor_groups = {}
        
        for pr_line in pr_lines:
            vendor_key = pr_line.suggested_supplier.name if pr_line.suggested_supplier else 'NO_VENDOR'
            
            if vendor_key not in vendor_groups:
                vendor_groups[vendor_key] = []
            
            vendor_groups[vendor_key].append(pr_line)
        
        return vendor_groups
    
    @staticmethod
    @transaction.atomic
    def update_pr_conversion_status(pr_header: PRHeader):
        """
        Update PR header status based on line conversion status.
        
        If all lines are fully converted, mark PR as CONVERTED.
        
        Args:
            pr_header: PRHeader instance
        """
        lines = pr_header.lines.all()
        
        if not lines.exists():
            return
        
        # Check if all lines are fully converted
        all_converted = all(
            line.conversion_status == 'FULLY_CONVERTED'
            for line in lines
        )
        
        if all_converted and pr_header.status == 'APPROVED':
            pr_header.status = 'CONVERTED'
            pr_header.converted_at = timezone.now()
            pr_header.save()


class PRLineSelectionHelper:
    """
    Helper class for PR line selection interface.
    """
    
    @staticmethod
    def prepare_pr_lines_for_selection(pr_header_ids: List[int] = None) -> List[Dict]:
        """
        Prepare PR lines data for selection UI.
        
        Args:
            pr_header_ids: List of PR header IDs (optional - if None, gets all approved PRs)
        
        Returns:
            List of dicts with PR line data ready for selection
        """
        pr_lines = PRToPOConversionService.get_convertible_pr_lines(pr_header_ids)
        
        result = []
        for pr_line in pr_lines:
            # Get requester name (with error handling for missing users)
            try:
                requester = pr_line.pr_header.requestor
                requester_name = f"{requester.first_name} {requester.last_name}".strip() or requester.username
            except Exception:
                # If requestor doesn't exist, use a default
                requester_name = "Unknown User"
            
            # Get cost center
            cost_center = (
                f"{pr_line.pr_header.cost_center.code} - {pr_line.pr_header.cost_center.name}"
                if pr_line.pr_header.cost_center
                else None
            )
            
            result.append({
                'pr_line_id': pr_line.id,
                'pr_number': pr_line.pr_header.pr_number,
                'pr_header_id': pr_line.pr_header.id,
                'pr_line_number': pr_line.line_number,
                'item_description': pr_line.item_description,
                'specifications': pr_line.specifications,
                'quantity_requested': str(pr_line.quantity),
                'quantity_converted': str(pr_line.quantity_converted),
                'quantity_remaining': str(pr_line.quantity_remaining),
                'unit_of_measure': pr_line.unit_of_measure.name,
                'estimated_unit_price': str(pr_line.estimated_unit_price),
                'need_by_date': pr_line.need_by_date.isoformat() if pr_line.need_by_date else None,
                'suggested_supplier': pr_line.suggested_supplier.name if pr_line.suggested_supplier else None,
                'conversion_status': pr_line.conversion_status,
                'catalog_item': pr_line.catalog_item.name if pr_line.catalog_item else None,
                'requester_name': requester_name,
                'cost_center': cost_center,
            })
        
        return result

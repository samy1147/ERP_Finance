"""
Procurement Analytics Service

Service for calculating procurement metrics and generating reports.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import (
    Sum, Avg, Count, Q, F, ExpressionWrapper,
    DecimalField, DurationField, Case, When, Value
)
from django.db.models.functions import TruncMonth, TruncWeek, Coalesce
from django.utils import timezone


class ProcurementAnalytics:
    """Main analytics service for procurement metrics."""
    
    def __init__(self, start_date=None, end_date=None):
        """
        Initialize analytics service with date range.
        
        Args:
            start_date: Start date for analysis (default: 30 days ago)
            end_date: End date for analysis (default: today)
        """
        self.end_date = end_date or timezone.now().date()
        self.start_date = start_date or (self.end_date - timedelta(days=30))
    
    def get_po_cycle_time_metrics(self):
        """
        Calculate PO cycle time metrics (based on PR and GRN).
        
        Returns average time from:
        - Requisition to GRN
        - GRN processing time
        - Overall cycle time
        """
        from procurement.requisitions.models import PRHeader
        from procurement.receiving.models import GoodsReceipt
        
        prs = PRHeader.objects.filter(
            pr_date__range=[self.start_date, self.end_date]
        ).exclude(status='DRAFT')
        
        metrics = {
            'total_prs': prs.count(),
            'avg_approval_time_days': None,
            'avg_fulfillment_time_days': None,
            'avg_total_cycle_days': None,
            'fastest_approval_days': None,
            'slowest_approval_days': None,
        }
        
        if not prs.exists():
            return metrics
        
        # Calculate approval time (PR creation to approval)
        approved_prs = prs.filter(
            approval_date__isnull=False
        ).annotate(
            approval_duration=ExpressionWrapper(
                F('approval_date') - F('pr_date'),
                output_field=DurationField()
            )
        )
        
        if approved_prs.exists():
            approval_times = [
                pr.approval_duration.total_seconds() / 86400  # Convert to days
                for pr in approved_prs
                if pr.approval_duration
            ]
            if approval_times:
                metrics['avg_approval_time_days'] = round(sum(approval_times) / len(approval_times), 2)
                metrics['fastest_approval_days'] = round(min(approval_times), 2)
                metrics['slowest_approval_days'] = round(max(approval_times), 2)
        
        # Calculate fulfillment time (PR to GRN)
        grns = GoodsReceipt.objects.filter(
            created_at__gte=self.start_date,
            status__in=['COMPLETED', 'QUALITY_APPROVED']
        )
        
        if grns.exists():
            fulfillment_times = []
            for grn in grns:
                if grn.received_date:
                    days = (grn.received_date - grn.created_at.date()).days
                    if days >= 0:
                        fulfillment_times.append(days)
            
            if fulfillment_times:
                metrics['avg_fulfillment_time_days'] = round(sum(fulfillment_times) / len(fulfillment_times), 2)
        
        # Overall cycle time
        if metrics['avg_approval_time_days'] and metrics['avg_fulfillment_time_days']:
            metrics['avg_total_cycle_days'] = round(
                metrics['avg_approval_time_days'] + metrics['avg_fulfillment_time_days'], 2
            )
        
        return metrics
    
    def get_on_time_delivery_metrics(self):
        """
        Calculate on-time delivery metrics.
        
        Returns:
        - Total deliveries
        - On-time deliveries
        - Late deliveries
        - On-time delivery percentage
        - Average delay days
        """
        from procurement.receiving.models import GoodsReceipt
        
        grns = GoodsReceipt.objects.filter(
            received_date__range=[self.start_date, self.end_date],
            status__in=['COMPLETED', 'QUALITY_APPROVED']
        )
        
        metrics = {
            'total_deliveries': grns.count(),
            'on_time_count': 0,
            'late_count': 0,
            'on_time_percentage': 0,
            'avg_delay_days': 0,
            'by_supplier': []
        }
        
        if not grns.exists():
            return metrics
        
        delays = []
        supplier_stats = {}
        
        for grn in grns:
            if grn.expected_delivery_date and grn.received_date:
                delay_days = (grn.received_date - grn.expected_delivery_date).days
                delays.append(delay_days)
                
                if delay_days <= 0:
                    metrics['on_time_count'] += 1
                else:
                    metrics['late_count'] += 1
                
                # Track by supplier if available
                if hasattr(grn, 'supplier') and grn.supplier:
                    supplier_id = grn.supplier.id
                    if supplier_id not in supplier_stats:
                        supplier_stats[supplier_id] = {
                            'supplier_id': supplier_id,
                            'supplier_name': grn.supplier.name,
                            'total': 0,
                            'on_time': 0,
                            'late': 0
                        }
                    
                    supplier_stats[supplier_id]['total'] += 1
                    if delay_days <= 0:
                        supplier_stats[supplier_id]['on_time'] += 1
                    else:
                        supplier_stats[supplier_id]['late'] += 1
        
        if metrics['total_deliveries'] > 0:
            metrics['on_time_percentage'] = round(
                (metrics['on_time_count'] / metrics['total_deliveries']) * 100, 2
            )
        
        if delays:
            late_delays = [d for d in delays if d > 0]
            if late_delays:
                metrics['avg_delay_days'] = round(sum(late_delays) / len(late_delays), 2)
        
        # Calculate supplier performance
        for supplier_id, stats in supplier_stats.items():
            stats['on_time_percentage'] = round(
                (stats['on_time'] / stats['total']) * 100, 2
            ) if stats['total'] > 0 else 0
        
        metrics['by_supplier'] = sorted(
            supplier_stats.values(),
            key=lambda x: x['on_time_percentage'],
            reverse=True
        )
        
        return metrics
    
    def get_price_variance_metrics(self):
        """
        Calculate price variance metrics comparing:
        - Vendor bill prices vs PO prices
        - Current PO prices vs historical average
        
        Returns variance statistics and top variances
        """
        from procurement.vendor_bills.models import VendorBill, VendorBillLine
        
        vendor_bills = VendorBill.objects.filter(
            invoice_date__range=[self.start_date, self.end_date]
        ).prefetch_related('lines')
        
        metrics = {
            'total_bills_analyzed': vendor_bills.count(),
            'total_variance_amount': Decimal('0'),
            'avg_variance_percentage': Decimal('0'),
            'favorable_variances': 0,
            'unfavorable_variances': 0,
            'top_variances': []
        }
        
        if not vendor_bills.exists():
            return metrics
        
        variances = []
        total_variance = Decimal('0')
        
        for bill in vendor_bills:
            for line in bill.lines.filter(po_line__isnull=False):
                po_price = line.po_line.unit_price
                bill_price = line.unit_price
                quantity = line.quantity_billed
                
                variance_amount = (bill_price - po_price) * quantity
                variance_pct = ((bill_price - po_price) / po_price * 100) if po_price else Decimal('0')
                
                total_variance += variance_amount
                
                if variance_amount < 0:
                    metrics['favorable_variances'] += 1
                elif variance_amount > 0:
                    metrics['unfavorable_variances'] += 1
                
                variances.append({
                    'bill_number': bill.bill_number,
                    'supplier': bill.supplier.name,
                    'item': line.po_line.item.name if line.po_line.item else line.description,
                    'po_price': float(po_price),
                    'bill_price': float(bill_price),
                    'quantity': float(quantity),
                    'variance_amount': float(variance_amount),
                    'variance_percentage': float(variance_pct)
                })
        
        metrics['total_variance_amount'] = float(total_variance)
        
        if variances:
            avg_pct = sum(abs(v['variance_percentage']) for v in variances) / len(variances)
            metrics['avg_variance_percentage'] = round(avg_pct, 2)
            
            # Top 10 variances by absolute amount
            metrics['top_variances'] = sorted(
                variances,
                key=lambda x: abs(x['variance_amount']),
                reverse=True
            )[:10]
        
        return metrics
    
    def get_spend_analysis(self, group_by='supplier'):
        """
        Analyze spend by different dimensions.
        
        Args:
            group_by: One of 'supplier', 'category', 'cost_center', 'month'
        
        Returns spend breakdown with totals and percentages
        """
        from procurement.vendor_bills.models import VendorBill
        
        bills = VendorBill.objects.filter(
            invoice_date__range=[self.start_date, self.end_date],
            status__in=['APPROVED', 'POSTED_TO_AP']
        )
        
        total_spend = bills.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        
        if group_by == 'supplier':
            spend_data = bills.values(
                'supplier__id', 'supplier__name'
            ).annotate(
                spend=Sum('total_amount'),
                bill_count=Count('id')
            ).order_by('-spend')
            
            result = []
            for item in spend_data:
                percentage = (item['spend'] / total_spend * 100) if total_spend else 0
                result.append({
                    'supplier_id': item['supplier__id'],
                    'supplier_name': item['supplier__name'],
                    'total_spend': float(item['spend']),
                    'bill_count': item['bill_count'],
                    'percentage': round(float(percentage), 2)
                })
            
            return {
                'total_spend': float(total_spend),
                'breakdown': result,
                'top_10': result[:10]
            }
        
        elif group_by == 'month':
            spend_data = bills.annotate(
                month=TruncMonth('invoice_date')
            ).values('month').annotate(
                spend=Sum('total_amount'),
                bill_count=Count('id')
            ).order_by('month')
            
            result = []
            for item in spend_data:
                result.append({
                    'month': item['month'].strftime('%Y-%m'),
                    'total_spend': float(item['spend']),
                    'bill_count': item['bill_count']
                })
            
            return {
                'total_spend': float(total_spend),
                'breakdown': result
            }
        
        elif group_by == 'category':
            # Group by item category from PO lines
            from procurement.vendor_bills.models import VendorBillLine
            
            lines = VendorBillLine.objects.filter(
                vendor_bill__in=bills,
                po_line__item__category__isnull=False
            ).values(
                'po_line__item__category__id',
                'po_line__item__category__name'
            ).annotate(
                spend=Sum('total_amount')
            ).order_by('-spend')
            
            result = []
            category_total = sum(item['spend'] for item in lines)
            
            for item in lines:
                percentage = (item['spend'] / category_total * 100) if category_total else 0
                result.append({
                    'category_id': item['po_line__item__category__id'],
                    'category_name': item['po_line__item__category__name'],
                    'total_spend': float(item['spend']),
                    'percentage': round(float(percentage), 2)
                })
            
            return {
                'total_spend': float(category_total),
                'breakdown': result,
                'top_10': result[:10]
            }
        
        return {'total_spend': float(total_spend), 'breakdown': []}
    
    def get_exceptions_and_blocked_invoices(self):
        """
        Get current exceptions and blocked invoices report.
        
        Returns:
        - Total exceptions by type and severity
        - Blocked vendor bills
        - Resolution time statistics
        """
        from procurement.vendor_bills.models import MatchException, VendorBill
        
        exceptions = MatchException.objects.filter(
            created_at__gte=self.start_date
        )
        
        metrics = {
            'total_exceptions': exceptions.count(),
            'open_exceptions': exceptions.filter(status='OPEN').count(),
            'in_review': exceptions.filter(status='IN_REVIEW').count(),
            'resolved': exceptions.filter(status='RESOLVED').count(),
            'blocked_bills': 0,
            'by_type': [],
            'by_severity': [],
            'resolution_stats': {},
            'top_blocking_exceptions': []
        }
        
        # Group by exception type
        by_type = exceptions.values('exception_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        metrics['by_type'] = [
            {
                'type': item['exception_type'],
                'count': item['count']
            }
            for item in by_type
        ]
        
        # Group by severity
        by_severity = exceptions.values('severity').annotate(
            count=Count('id')
        ).order_by('-count')
        
        metrics['by_severity'] = [
            {
                'severity': item['severity'],
                'count': item['count']
            }
            for item in by_severity
        ]
        
        # Blocked vendor bills
        blocked_bills = VendorBill.objects.filter(
            has_exceptions=True,
            exceptions_resolved=False
        )
        
        metrics['blocked_bills'] = blocked_bills.count()
        
        # Top blocking exceptions
        blocking_exceptions = exceptions.filter(
            blocks_posting=True,
            status__in=['OPEN', 'IN_REVIEW']
        ).select_related('vendor_bill', 'vendor_bill__supplier')
        
        metrics['top_blocking_exceptions'] = [
            {
                'id': exc.id,
                'vendor_bill': exc.vendor_bill.bill_number,
                'supplier': exc.vendor_bill.supplier.name,
                'type': exc.exception_type,
                'severity': exc.severity,
                'description': exc.description,
                'created_at': exc.created_at.strftime('%Y-%m-%d'),
                'age_days': (timezone.now().date() - exc.created_at.date()).days
            }
            for exc in blocking_exceptions[:20]
        ]
        
        # Resolution time statistics
        resolved_exceptions = exceptions.filter(
            status='RESOLVED',
            resolved_date__isnull=False
        )
        
        if resolved_exceptions.exists():
            resolution_times = []
            for exc in resolved_exceptions:
                days = (exc.resolved_date - exc.created_at.date()).days
                resolution_times.append(days)
            
            metrics['resolution_stats'] = {
                'avg_resolution_days': round(sum(resolution_times) / len(resolution_times), 2),
                'min_resolution_days': min(resolution_times),
                'max_resolution_days': max(resolution_times)
            }
        
        return metrics
    
    def get_dashboard_kpis(self):
        """
        Get comprehensive KPIs for procurement dashboard.
        
        Returns all key metrics in one call.
        """
        cycle_time = self.get_po_cycle_time_metrics()
        on_time_delivery = self.get_on_time_delivery_metrics()
        price_variance = self.get_price_variance_metrics()
        spend = self.get_spend_analysis(group_by='supplier')
        exceptions = self.get_exceptions_and_blocked_invoices()
        
        return {
            'period': {
                'start_date': self.start_date.strftime('%Y-%m-%d'),
                'end_date': self.end_date.strftime('%Y-%m-%d')
            },
            'cycle_time': cycle_time,
            'on_time_delivery': on_time_delivery,
            'price_variance': price_variance,
            'spend_summary': {
                'total_spend': spend['total_spend'],
                'top_suppliers': spend['top_10']
            },
            'exceptions': exceptions
        }

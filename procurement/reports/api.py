"""
Procurement Reports API

REST API endpoints for procurement reporting and analytics.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from datetime import datetime, timedelta
from django.utils import timezone

from .analytics import ProcurementAnalytics
from .export_utils import CSVExporter, ExcelExporter, prepare_export_data
from procurement.vendor_bills.models import VendorBill, MatchException
from procurement.requisitions.models import PRHeader
from procurement.receiving.models import GoodsReceipt


class POCycleTimeReportAPI(APIView):
    """
    API endpoint for PO cycle time analysis.
    
    GET /api/reports/po-cycle-time/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&format=json|csv|xlsx
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get PO cycle time metrics."""
        # Parse date parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        export_format = request.query_params.get('format', 'json')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get analytics
        analytics = ProcurementAnalytics(start_date, end_date)
        data = analytics.get_po_cycle_time_metrics()
        
        # Export if requested
        if export_format == 'csv':
            return CSVExporter.export_to_response(
                [data], 
                'po_cycle_time'
            )
        elif export_format == 'xlsx':
            return ExcelExporter.export_to_response(
                [data],
                'po_cycle_time',
                title='PO Cycle Time Analysis'
            )
        
        return Response(data)


class OnTimeDeliveryReportAPI(APIView):
    """
    API endpoint for on-time delivery analysis.
    
    GET /api/reports/on-time-delivery/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&format=json|csv|xlsx
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get on-time delivery metrics."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        export_format = request.query_params.get('format', 'json')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics = ProcurementAnalytics(start_date, end_date)
        data = analytics.get_on_time_delivery_metrics()
        
        if export_format == 'csv':
            # Export supplier breakdown
            return CSVExporter.export_to_response(
                data.get('by_supplier', []),
                'on_time_delivery_by_supplier'
            )
        elif export_format == 'xlsx':
            # Multi-sheet export
            sheets = [
                ('Summary', [data], None, 'On-Time Delivery Summary'),
                ('By Supplier', data.get('by_supplier', []), None, 'Supplier Performance')
            ]
            return ExcelExporter.export_multi_sheet(
                sheets,
                'on_time_delivery_report'
            )
        
        return Response(data)


class PriceVarianceReportAPI(APIView):
    """
    API endpoint for price variance analysis.
    
    GET /api/reports/price-variance/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&format=json|csv|xlsx
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get price variance metrics."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        export_format = request.query_params.get('format', 'json')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics = ProcurementAnalytics(start_date, end_date)
        data = analytics.get_price_variance_metrics()
        
        if export_format == 'csv':
            return CSVExporter.export_to_response(
                data.get('top_variances', []),
                'price_variances'
            )
        elif export_format == 'xlsx':
            return ExcelExporter.export_to_response(
                data.get('top_variances', []),
                'price_variances',
                title='Top Price Variances'
            )
        
        return Response(data)


class SpendAnalysisReportAPI(APIView):
    """
    API endpoint for spend analysis.
    
    GET /api/reports/spend-analysis/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&group_by=supplier|category|month&format=json|csv|xlsx
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get spend analysis."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_by = request.query_params.get('group_by', 'supplier')
        export_format = request.query_params.get('format', 'json')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics = ProcurementAnalytics(start_date, end_date)
        data = analytics.get_spend_analysis(group_by=group_by)
        
        if export_format == 'csv':
            return CSVExporter.export_to_response(
                data.get('breakdown', []),
                f'spend_by_{group_by}'
            )
        elif export_format == 'xlsx':
            return ExcelExporter.export_to_response(
                data.get('breakdown', []),
                f'spend_by_{group_by}',
                title=f'Spend Analysis by {group_by.title()}'
            )
        
        return Response(data)


class ExceptionsReportAPI(APIView):
    """
    API endpoint for exceptions and blocked invoices.
    
    GET /api/reports/exceptions/?start_date=YYYY-MM-DD&format=json|csv|xlsx
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get exceptions report."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        export_format = request.query_params.get('format', 'json')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics = ProcurementAnalytics(start_date, end_date)
        data = analytics.get_exceptions_and_blocked_invoices()
        
        if export_format == 'csv':
            return CSVExporter.export_to_response(
                data.get('top_blocking_exceptions', []),
                'blocking_exceptions'
            )
        elif export_format == 'xlsx':
            sheets = [
                ('Exceptions by Type', data.get('by_type', []), None, 'Exceptions by Type'),
                ('Exceptions by Severity', data.get('by_severity', []), None, 'Exceptions by Severity'),
                ('Blocking Exceptions', data.get('top_blocking_exceptions', []), None, 'Top Blocking Exceptions')
            ]
            return ExcelExporter.export_multi_sheet(
                sheets,
                'exceptions_report'
            )
        
        return Response(data)


class DashboardKPIsAPI(APIView):
    """
    API endpoint for comprehensive dashboard KPIs.
    
    GET /api/reports/dashboard/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all dashboard KPIs."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics = ProcurementAnalytics(start_date, end_date)
        data = analytics.get_dashboard_kpis()
        
        return Response(data)


class VendorBillExportAPI(APIView):
    """
    API endpoint for exporting vendor bills.
    
    GET /api/reports/vendor-bills/export/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&status=APPROVED&format=csv|xlsx
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Export vendor bills."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        status_filter = request.query_params.get('status')
        supplier_id = request.query_params.get('supplier')
        export_format = request.query_params.get('format', 'xlsx')
        
        # Build queryset
        queryset = VendorBill.objects.all().select_related('supplier', 'currency')
        
        if start_date:
            queryset = queryset.filter(invoice_date__gte=datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            queryset = queryset.filter(invoice_date__lte=datetime.strptime(end_date, '%Y-%m-%d').date())
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        
        # Prepare data
        fields = [
            ('bill_number', 'Bill Number'),
            ('supplier.name', 'Supplier'),
            ('invoice_number', 'Invoice Number'),
            ('invoice_date', 'Invoice Date'),
            ('due_date', 'Due Date'),
            ('currency.code', 'Currency'),
            ('total_amount', 'Total Amount'),
            ('status', 'Status'),
            ('match_status', 'Match Status'),
            ('is_posted_to_ap', 'Posted to AP'),
        ]
        
        data = prepare_export_data(queryset, fields)
        
        if export_format == 'csv':
            return CSVExporter.export_to_response(data, 'vendor_bills')
        else:
            return ExcelExporter.export_to_response(
                data,
                'vendor_bills',
                title='Vendor Bills Report'
            )


class PurchaseRequisitionExportAPI(APIView):
    """
    API endpoint for exporting purchase requisitions.
    
    GET /api/reports/purchase-requisitions/export/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&status=APPROVED&format=csv|xlsx
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Export purchase requisitions."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        status_filter = request.query_params.get('status')
        department = request.query_params.get('department')
        export_format = request.query_params.get('format', 'xlsx')
        
        # Build queryset
        queryset = PRHeader.objects.all().select_related('requested_by')
        
        if start_date:
            queryset = queryset.filter(pr_date__gte=datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            queryset = queryset.filter(pr_date__lte=datetime.strptime(end_date, '%Y-%m-%d').date())
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if department:
            queryset = queryset.filter(department=department)
        
        # Prepare data
        fields = [
            ('pr_number', 'PR Number'),
            ('pr_date', 'PR Date'),
            ('requested_by.username', 'Requested By'),
            ('department', 'Department'),
            ('status', 'Status'),
            ('priority', 'Priority'),
            ('required_date', 'Required Date'),
        ]
        
        data = prepare_export_data(queryset, fields)
        
        if export_format == 'csv':
            return CSVExporter.export_to_response(data, 'purchase_requisitions')
        else:
            return ExcelExporter.export_to_response(
                data,
                'purchase_requisitions',
                title='Purchase Requisitions Report'
            )


class GRNExportAPI(APIView):
    """
    API endpoint for exporting GRNs.
    
    GET /api/reports/grns/export/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&status=COMPLETED&format=csv|xlsx
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Export GRNs."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        status_filter = request.query_params.get('status')
        export_format = request.query_params.get('format', 'xlsx')
        
        # Build queryset
        queryset = GoodsReceipt.objects.all().select_related('received_by')
        
        if start_date:
            queryset = queryset.filter(received_date__gte=datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            queryset = queryset.filter(received_date__lte=datetime.strptime(end_date, '%Y-%m-%d').date())
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Prepare data
        fields = [
            ('grn_number', 'GRN Number'),
            ('received_date', 'Received Date'),
            ('status', 'Status'),
            ('quality_status', 'Quality Status'),
            ('received_by.username', 'Received By'),
        ]
        
        data = prepare_export_data(queryset, fields)
        
        if export_format == 'csv':
            return CSVExporter.export_to_response(data, 'grns')
        else:
            return ExcelExporter.export_to_response(
                data,
                'grns',
                title='Goods Receipt Notes Report'
            )

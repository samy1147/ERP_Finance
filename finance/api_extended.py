"""
Extended API for Payment Allocations and Invoice Approvals
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from decimal import Decimal

from ar.models import ARPayment, ARPaymentAllocation, ARInvoice, Customer
from ap.models import APPayment, APPaymentAllocation, APInvoice, Supplier
from finance.models import InvoiceApproval
from finance.serializers_extended import (
    ARPaymentSerializer, ARPaymentAllocationSerializer,
    APPaymentSerializer, APPaymentAllocationSerializer,
    InvoiceApprovalSerializer
)
from drf_spectacular.utils import extend_schema, extend_schema_view


# ============================================================================
# AR PAYMENT ALLOCATION VIEWSETS
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List all AR payments with allocations"),
    retrieve=extend_schema(description="Get AR payment details with allocations"),
    create=extend_schema(description="Create AR payment with allocations"),
    update=extend_schema(description="Update AR payment and allocations"),
    partial_update=extend_schema(description="Partially update AR payment"),
)
class ARPaymentViewSet(viewsets.ModelViewSet):
    """AR Payment ViewSet with allocation support"""
    queryset = ARPayment.objects.all().prefetch_related('allocations', 'allocations__invoice')
    serializer_class = ARPaymentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by reconciliation status
        reconciled = self.request.query_params.get('reconciled')
        if reconciled is not None:
            queryset = queryset.filter(reconciled=reconciled.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        """Post AR payment to GL"""
        payment = self.get_object()
        
        if payment.posted_at:
            return Response(
                {'error': 'Payment already posted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implement GL posting logic
        # For now, just mark as posted
        payment.posted_at = timezone.now()
        payment.save()
        
        return Response(self.get_serializer(payment).data)
    
    @action(detail=True, methods=['post'])
    def reconcile(self, request, pk=None):
        """Mark payment as reconciled"""
        payment = self.get_object()
        reconciliation_ref = request.data.get('reconciliation_ref', '')
        
        payment.reconciled = True
        payment.reconciled_at = timezone.now().date()
        if reconciliation_ref:
            payment.reconciliation_ref = reconciliation_ref
        payment.save()
        
        return Response(self.get_serializer(payment).data)
    
    @action(detail=False, methods=['get'])
    def outstanding(self, request):
        """Get AR payments with unallocated amounts"""
        payments = self.get_queryset().filter(posted_at__isnull=False)
        outstanding = []
        
        for payment in payments:
            unallocated = payment.unallocated_amount()
            if unallocated > 0:
                serializer = self.get_serializer(payment)
                data = serializer.data
                data['unallocated_amount'] = float(unallocated)
                outstanding.append(data)
        
        return Response(outstanding)


# ============================================================================
# AP PAYMENT ALLOCATION VIEWSETS
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List all AP payments with allocations"),
    retrieve=extend_schema(description="Get AP payment details with allocations"),
    create=extend_schema(description="Create AP payment with allocations"),
    update=extend_schema(description="Update AP payment and allocations"),
    partial_update=extend_schema(description="Partially update AP payment"),
)
class APPaymentViewSet(viewsets.ModelViewSet):
    """AP Payment ViewSet with allocation support"""
    queryset = APPayment.objects.all().prefetch_related('allocations', 'allocations__invoice')
    serializer_class = APPaymentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by supplier
        supplier_id = self.request.query_params.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        
        # Filter by reconciliation status
        reconciled = self.request.query_params.get('reconciled')
        if reconciled is not None:
            queryset = queryset.filter(reconciled=reconciled.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        """Post AP payment to GL"""
        payment = self.get_object()
        
        if payment.posted_at:
            return Response(
                {'error': 'Payment already posted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implement GL posting logic
        # For now, just mark as posted
        payment.posted_at = timezone.now()
        payment.save()
        
        return Response(self.get_serializer(payment).data)
    
    @action(detail=True, methods=['post'])
    def reconcile(self, request, pk=None):
        """Mark payment as reconciled"""
        payment = self.get_object()
        reconciliation_ref = request.data.get('reconciliation_ref', '')
        
        payment.reconciled = True
        payment.reconciled_at = timezone.now().date()
        if reconciliation_ref:
            payment.reconciliation_ref = reconciliation_ref
        payment.save()
        
        return Response(self.get_serializer(payment).data)
    
    @action(detail=False, methods=['get'])
    def outstanding(self, request):
        """Get AP payments with unallocated amounts"""
        payments = self.get_queryset().filter(posted_at__isnull=False)
        outstanding = []
        
        for payment in payments:
            unallocated = payment.unallocated_amount()
            if unallocated > 0:
                serializer = self.get_serializer(payment)
                data = serializer.data
                data['unallocated_amount'] = float(unallocated)
                outstanding.append(data)
        
        return Response(outstanding)


# ============================================================================
# INVOICE APPROVAL VIEWSETS
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List all invoice approvals"),
    retrieve=extend_schema(description="Get invoice approval details"),
    create=extend_schema(description="Submit invoice for approval"),
)
class InvoiceApprovalViewSet(viewsets.ModelViewSet):
    """Invoice Approval ViewSet"""
    queryset = InvoiceApproval.objects.all()
    serializer_class = InvoiceApprovalSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by invoice type
        invoice_type = self.request.query_params.get('invoice_type')
        if invoice_type:
            queryset = queryset.filter(invoice_type=invoice_type)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an invoice"""
        approval = self.get_object()
        
        if approval.status != 'PENDING_APPROVAL':
            return Response(
                {'error': 'Only pending approvals can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as approved
        approval.status = 'APPROVED'
        approval.approver = request.data.get('approver', 'System')
        approval.approved_at = timezone.now()
        approval.comments = request.data.get('comments', '')
        approval.save()
        
        # Update invoice approval_status
        if approval.invoice_type == 'AR':
            try:
                invoice = ARInvoice.objects.get(id=approval.invoice_id)
                invoice.approval_status = 'APPROVED'
                invoice.save()
            except ARInvoice.DoesNotExist:
                pass
        elif approval.invoice_type == 'AP':
            try:
                invoice = APInvoice.objects.get(id=approval.invoice_id)
                invoice.approval_status = 'APPROVED'
                invoice.save()
            except APInvoice.DoesNotExist:
                pass
        
        return Response(self.get_serializer(approval).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an invoice"""
        approval = self.get_object()
        
        if approval.status != 'PENDING_APPROVAL':
            return Response(
                {'error': 'Only pending approvals can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comments = request.data.get('comments', '')
        if not comments:
            return Response(
                {'error': 'Comments are required for rejection'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as rejected
        approval.status = 'REJECTED'
        approval.approver = request.data.get('approver', 'System')
        approval.rejected_at = timezone.now()
        approval.comments = comments
        approval.save()
        
        # Update invoice approval_status
        if approval.invoice_type == 'AR':
            try:
                invoice = ARInvoice.objects.get(id=approval.invoice_id)
                invoice.approval_status = 'REJECTED'
                invoice.save()
            except ARInvoice.DoesNotExist:
                pass
        elif approval.invoice_type == 'AP':
            try:
                invoice = APInvoice.objects.get(id=approval.invoice_id)
                invoice.approval_status = 'REJECTED'
                invoice.save()
            except APInvoice.DoesNotExist:
                pass
        
        return Response(self.get_serializer(approval).data)


# ============================================================================
# HELPER APIS
# ============================================================================

class OutstandingInvoicesAPI(APIView):
    """Get outstanding invoices for a customer or supplier"""
    
    def get(self, request):
        customer_id = request.query_params.get('customer')
        supplier_id = request.query_params.get('supplier')
        
        invoices = []
        
        if customer_id:
            ar_invoices = ARInvoice.objects.filter(
                customer_id=customer_id,
                is_posted=True,
                is_cancelled=False
            ).prefetch_related('items', 'payment_allocations')
            
            for inv in ar_invoices:
                outstanding = inv.outstanding_amount()
                if outstanding > 0:
                    invoices.append({
                        'id': inv.id,
                        'number': inv.number,
                        'date': inv.date,
                        'due_date': inv.due_date,
                        'total': float(inv.calculate_total()),
                        'paid': float(inv.paid_amount()),
                        'outstanding': float(outstanding),
                        'currency': inv.currency.code,
                        'currency_id': inv.currency.id
                    })
        
        elif supplier_id:
            ap_invoices = APInvoice.objects.filter(
                supplier_id=supplier_id,
                is_posted=True,
                is_cancelled=False
            ).prefetch_related('items', 'payment_allocations')
            
            for inv in ap_invoices:
                outstanding = inv.outstanding_amount()
                if outstanding > 0:
                    invoices.append({
                        'id': inv.id,
                        'number': inv.number,
                        'date': inv.date,
                        'due_date': inv.due_date,
                        'total': float(inv.calculate_total()),
                        'paid': float(inv.paid_amount()),
                        'outstanding': float(outstanding),
                        'currency': inv.currency.code,
                        'currency_id': inv.currency.id
                    })
        
        return Response(invoices)

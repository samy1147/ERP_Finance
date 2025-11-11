"""
CRM API ViewSets

Customer Management:
- CustomerViewSet available at /api/customers/

Supplier/Vendor Management:
- SupplierViewSet available at /api/ap/vendors/ (in ap module)
  Full vendor management with onboarding, performance tracking, and risk assessment
"""

from rest_framework import viewsets
from ar.models import Customer
from ap.models import Supplier
from .serializers import CustomerSerializer, SupplierSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing customers (AR)
    
    Available at: /api/customers/
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_fields = ['code', 'name', 'email', 'is_active']
    search_fields = ['code', 'name', 'email']
    ordering_fields = ['code', 'name']
    ordering = ['code']


class SupplierViewSet(viewsets.ModelViewSet):
    """
    INTERNAL USE ONLY - Not registered in main router
    
    For Supplier/Vendor management, use the full-featured endpoint:
    /api/ap/vendors/ (ap.api.SupplierViewSet)
    
    That endpoint provides:
    - Complete vendor CRUD
    - Performance tracking
    - Onboarding workflows
    - Risk assessment
    - Document management
    - Custom actions (mark_preferred, put_on_hold, blacklist, etc.)
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_fields = ['code', 'name', 'email', 'is_active']
    search_fields = ['code', 'name', 'email']
    ordering_fields = ['code', 'name']
    ordering = ['code']

from rest_framework import viewsets
from ar.models import Customer
from ap.models import Supplier
from .serializers import CustomerSerializer, SupplierSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing customers (AR)
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_fields = ['code', 'name', 'email', 'is_active']
    search_fields = ['code', 'name', 'email']
    ordering_fields = ['code', 'name']
    ordering = ['code']


class SupplierViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing suppliers (AP)
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_fields = ['code', 'name', 'email', 'is_active']
    search_fields = ['code', 'name', 'email']
    ordering_fields = ['code', 'name']
    ordering = ['code']

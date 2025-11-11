# procurement/urls.py
"""
Main procurement module URL router
Routes requests to all procurement submodules
"""
from django.urls import path, include

urlpatterns = [
    # RFx & Sourcing Events
    path('rfx/', include('procurement.rfx.urls')),
    
    # Vendor Bills & Invoice Management
    path('vendor-bills/', include('procurement.vendor_bills.urls')),
    
    # Contracts Management
    path('contracts/', include('procurement.contracts.urls')),
    
    # Payment Integration
    path('payments/', include('procurement.payments.urls')),
    
    # Purchase Orders
    path('purchase-orders/', include('procurement.purchase_orders.urls')),
    
    # Purchase Requisitions
    path('requisitions/', include('procurement.requisitions.urls')),
    
    # Receiving & Goods Receipt
    path('receiving/', include('procurement.receiving.urls')),
    
    # Approval Workflows
    path('approvals/', include('procurement.approvals.urls')),
    
    # Product Catalog
    path('catalog/', include('procurement.catalog.urls')),
    
    # Analytics & Reports
    path('reports/', include('procurement.reports.urls')),
]

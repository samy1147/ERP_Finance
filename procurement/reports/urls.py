"""
Procurement Reports URLs

API Endpoints for procurement reporting and analytics.
"""

from django.urls import path
from .api import (
    POCycleTimeReportAPI,
    OnTimeDeliveryReportAPI,
    PriceVarianceReportAPI,
    SpendAnalysisReportAPI,
    ExceptionsReportAPI,
    DashboardKPIsAPI,
    VendorBillExportAPI,
    PurchaseRequisitionExportAPI,
    GRNExportAPI
)

urlpatterns = [
    # Analytics endpoints
    path('po-cycle-time/', POCycleTimeReportAPI.as_view(), name='po-cycle-time'),
    path('on-time-delivery/', OnTimeDeliveryReportAPI.as_view(), name='on-time-delivery'),
    path('price-variance/', PriceVarianceReportAPI.as_view(), name='price-variance'),
    path('spend-analysis/', SpendAnalysisReportAPI.as_view(), name='spend-analysis'),
    path('exceptions/', ExceptionsReportAPI.as_view(), name='exceptions'),
    path('dashboard/', DashboardKPIsAPI.as_view(), name='dashboard'),
    
    # Export endpoints
    path('vendor-bills/export/', VendorBillExportAPI.as_view(), name='vendor-bills-export'),
    path('purchase-requisitions/export/', PurchaseRequisitionExportAPI.as_view(), name='purchase-requisitions-export'),
    path('grns/export/', GRNExportAPI.as_view(), name='grns-export'),
]

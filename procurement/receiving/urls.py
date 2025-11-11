"""
URL configuration for Receiving API - Placeholder for full implementation.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    WarehouseViewSet, GoodsReceiptViewSet, GRNLineViewSet,
    QualityInspectionViewSet, NonConformanceViewSet,
    ReturnToVendorViewSet, RTVLineViewSet
)

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'receipts', GoodsReceiptViewSet, basename='goods-receipt')
router.register(r'grn-lines', GRNLineViewSet, basename='grn-line')
router.register(r'inspections', QualityInspectionViewSet, basename='quality-inspection')
router.register(r'non-conformances', NonConformanceViewSet, basename='non-conformance')
router.register(r'returns', ReturnToVendorViewSet, basename='return-to-vendor')
router.register(r'rtv-lines', RTVLineViewSet, basename='rtv-line')

urlpatterns = [
    path('', include(router.urls)),
]

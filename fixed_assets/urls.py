"""
Asset Management URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    AssetCategoryViewSet, AssetLocationViewSet, AssetViewSet,
    AssetTransferViewSet, DepreciationScheduleViewSet,
    AssetMaintenanceViewSet, AssetDocumentViewSet, AssetConfigurationViewSet,
    AssetRetirementViewSet, AssetAdjustmentViewSet, AssetApprovalViewSet
)

router = DefaultRouter()
router.register(r'categories', AssetCategoryViewSet, basename='assetcategory')
router.register(r'locations', AssetLocationViewSet, basename='assetlocation')
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'transfers', AssetTransferViewSet, basename='assettransfer')
router.register(r'retirements', AssetRetirementViewSet, basename='assetretirement')
router.register(r'adjustments', AssetAdjustmentViewSet, basename='assetadjustment')
router.register(r'approvals', AssetApprovalViewSet, basename='assetapproval')
router.register(r'depreciation', DepreciationScheduleViewSet, basename='depreciation')
router.register(r'maintenance', AssetMaintenanceViewSet, basename='assetmaintenance')
router.register(r'documents', AssetDocumentViewSet, basename='assetdocument')
router.register(r'configuration', AssetConfigurationViewSet, basename='assetconfiguration')

urlpatterns = [
    path('', include(router.urls)),
]

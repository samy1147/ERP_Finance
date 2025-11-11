# ap/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    SupplierViewSet,
    VendorContactViewSet,
    VendorDocumentViewSet,
    VendorPerformanceRecordViewSet,
    VendorOnboardingChecklistViewSet
)

app_name = 'ap'

router = DefaultRouter()
router.register(r'vendors', SupplierViewSet, basename='vendor')
router.register(r'vendor-contacts', VendorContactViewSet, basename='vendor-contact')
router.register(r'vendor-documents', VendorDocumentViewSet, basename='vendor-document')
router.register(r'vendor-performance', VendorPerformanceRecordViewSet, basename='vendor-performance')
router.register(r'vendor-onboarding', VendorOnboardingChecklistViewSet, basename='vendor-onboarding')

urlpatterns = [
    path('', include(router.urls)),
]

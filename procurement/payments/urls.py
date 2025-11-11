"""
Payments & Finance Integration URLs

API Endpoints:
- /api/payment-batches/ - AP payment batch CRUD and workflow
- /api/payment-requests/ - Payment request management
- /api/tax-jurisdictions/ - Tax jurisdiction configuration
- /api/tax-rates/ - Tax rate management
- /api/tax-periods/ - Tax period management
- /api/corporate-tax/ - Corporate tax accruals
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    APPaymentBatchViewSet, TaxJurisdictionViewSet,
    TaxRateViewSet, TaxComponentViewSet,
    TaxPeriodViewSet, CorporateTaxAccrualViewSet,
    PaymentRequestViewSet
)

router = DefaultRouter()
router.register('batches', APPaymentBatchViewSet, basename='batch')
router.register('requests', PaymentRequestViewSet, basename='request')
router.register('jurisdictions', TaxJurisdictionViewSet, basename='jurisdiction')
router.register('rates', TaxRateViewSet, basename='rate')
router.register('components', TaxComponentViewSet, basename='component')
router.register('tax-periods', TaxPeriodViewSet, basename='tax-period')
router.register('tax-accruals', CorporateTaxAccrualViewSet, basename='accrual')

urlpatterns = [
    path('', include(router.urls)),
]

"""
Vendor Bill & 3-Way Match URLs

API Endpoints:
- /api/vendor-bills/ - Vendor bill CRUD and workflow
- /api/three-way-match/ - 3-way matching operations
- /api/match-exceptions/ - Exception management
- /api/match-tolerances/ - Tolerance configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    VendorBillViewSet, ThreeWayMatchViewSet,
    MatchExceptionViewSet, MatchToleranceViewSet
)

router = DefaultRouter()
router.register('bills', VendorBillViewSet, basename='vendor-bill')
router.register('matches', ThreeWayMatchViewSet, basename='match')
router.register('exceptions', MatchExceptionViewSet, basename='exception')
router.register('tolerances', MatchToleranceViewSet, basename='tolerance')

urlpatterns = [
    path('', include(router.urls)),
]

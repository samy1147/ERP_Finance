"""
URL Configuration for Periods API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import FiscalYearViewSet, FiscalPeriodViewSet, PeriodStatusViewSet

router = DefaultRouter()
router.register(r'fiscal-years', FiscalYearViewSet, basename='fiscal-year')
router.register(r'fiscal-periods', FiscalPeriodViewSet, basename='fiscal-period')
router.register(r'period-status', PeriodStatusViewSet, basename='period-status')

urlpatterns = [
    path('', include(router.urls)),
]

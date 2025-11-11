# procurement/purchase_orders/urls.py
"""
Purchase Orders URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import POHeaderViewSet, POLineViewSet

router = DefaultRouter()
router.register(r'', POHeaderViewSet, basename='po-header')
router.register(r'lines', POLineViewSet, basename='po-line')

urlpatterns = [
    path('', include(router.urls)),
]

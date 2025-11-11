"""
URL configuration for Purchase Requisition API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    CostCenterViewSet, ProjectViewSet,
    PRHeaderViewSet, PRLineViewSet
)

router = DefaultRouter()
router.register(r'cost-centers', CostCenterViewSet, basename='cost-center')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'pr-headers', PRHeaderViewSet, basename='pr-header')
router.register(r'pr-lines', PRLineViewSet, basename='pr-line')

urlpatterns = [
    path('', include(router.urls)),
]

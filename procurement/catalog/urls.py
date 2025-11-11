# catalog/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    UnitOfMeasureViewSet, CatalogCategoryViewSet, CatalogItemViewSet,
    SupplierPriceTierViewSet, FrameworkAgreementViewSet, FrameworkItemViewSet,
    CallOffOrderViewSet, CallOffLineViewSet
)

router = DefaultRouter()
router.register(r'units-of-measure', UnitOfMeasureViewSet, basename='unit-of-measure')
router.register(r'categories', CatalogCategoryViewSet, basename='catalog-category')
router.register(r'items', CatalogItemViewSet, basename='catalog-item')
router.register(r'price-tiers', SupplierPriceTierViewSet, basename='supplier-price-tier')
router.register(r'framework-agreements', FrameworkAgreementViewSet, basename='framework-agreement')
router.register(r'framework-items', FrameworkItemViewSet, basename='framework-item')
router.register(r'calloff-orders', CallOffOrderViewSet, basename='calloff-order')
router.register(r'calloff-lines', CallOffLineViewSet, basename='calloff-line')

urlpatterns = [
    path('', include(router.urls)),
]

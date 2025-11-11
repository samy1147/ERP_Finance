from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import SegmentTypeViewSet, SegmentViewSet, AccountViewSet

router = DefaultRouter()
router.register(r'types', SegmentTypeViewSet, basename='segment-type')
router.register(r'values', SegmentViewSet, basename='segment-value')
router.register(r'accounts', AccountViewSet, basename='account')

urlpatterns = [
    path('', include(router.urls)),
]


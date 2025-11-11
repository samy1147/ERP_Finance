# procurement/rfx/urls.py
"""
RFx URLs - RFx Events, Sourcing, Supplier Management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    RFxEventViewSet, RFxItemViewSet, SupplierInvitationViewSet,
    SupplierQuoteViewSet, SupplierQuoteLineViewSet, RFxAwardViewSet,
    AuctionBidViewSet
)

router = DefaultRouter()
router.register(r'rfx-events', RFxEventViewSet, basename='rfx-event')
router.register(r'rfx-items', RFxItemViewSet, basename='rfx-item')
router.register(r'supplier-invitations', SupplierInvitationViewSet, basename='supplier-invitation')
router.register(r'supplier-quotes', SupplierQuoteViewSet, basename='supplier-quote')
router.register(r'supplier-quote-lines', SupplierQuoteLineViewSet, basename='supplier-quote-line')
router.register(r'rfx-awards', RFxAwardViewSet, basename='rfx-award')
router.register(r'auction-bids', AuctionBidViewSet, basename='auction-bid')

urlpatterns = [
    path('', include(router.urls)),
]

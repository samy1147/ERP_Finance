"""
Contracts & Compliance URLs

API Endpoints:
- /api/contracts/ - Contract CRUD and workflow
- /api/clause-library/ - Clause library management
- /api/contract-renewals/ - Renewal tracking
- /api/contract-slas/ - SLA management
- /api/contract-penalties/ - Penalty tracking
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    ContractViewSet, ClauseLibraryViewSet,
    ContractSLAViewSet, ContractPenaltyViewSet,
    ContractRenewalViewSet, ContractAttachmentViewSet,
    ContractNoteViewSet
)

router = DefaultRouter()
router.register('contracts', ContractViewSet, basename='contract')
router.register('clauses', ClauseLibraryViewSet, basename='clause')
router.register('slas', ContractSLAViewSet, basename='sla')
router.register('penalties', ContractPenaltyViewSet, basename='penalty')
router.register('renewals', ContractRenewalViewSet, basename='renewal')
router.register('attachments', ContractAttachmentViewSet, basename='attachment')
router.register('notes', ContractNoteViewSet, basename='note')

urlpatterns = [
    path('', include(router.urls)),
]

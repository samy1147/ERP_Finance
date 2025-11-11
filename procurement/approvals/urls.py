"""
URL configuration for Approval API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    ApprovalWorkflowViewSet, ApprovalInstanceViewSet,
    ApprovalStepInstanceViewSet, ApprovalDelegationViewSet,
    BudgetAllocationViewSet, BudgetCheckViewSet
)

router = DefaultRouter()
router.register(r'workflows', ApprovalWorkflowViewSet, basename='approval-workflow')
router.register(r'instances', ApprovalInstanceViewSet, basename='approval-instance')
router.register(r'steps', ApprovalStepInstanceViewSet, basename='approval-step')
router.register(r'delegations', ApprovalDelegationViewSet, basename='approval-delegation')
router.register(r'budgets', BudgetAllocationViewSet, basename='budget-allocation')
router.register(r'budget-checks', BudgetCheckViewSet, basename='budget-check')

urlpatterns = [
    path('', include(router.urls)),
]

from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from finance.api import (AccountViewSet, CorporateTaxReverse, JournalEntryViewSet, JournalLineViewSet, ARInvoiceViewSet, ARPaymentViewSet,APInvoiceViewSet, APPaymentViewSet, CurrencyViewSet, GetCSRFToken)
from finance.api import BankAccountViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from finance.api import TrialBalanceReport, ARAgingReport, APAgingReport
from rest_framework.urlpatterns import format_suffix_patterns
from finance.api import SeedVATPresets, ListTaxRates, CorporateTaxAccrual,CorporateTaxFile,CorporateTaxBreakdown,CorporateTaxFilingDetail
from finance.api import ExchangeRateViewSet, CurrencyConvertView, CreateExchangeRateView, FXGainLossAccountViewSet, BaseCurrencyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from crm.api import CustomerViewSet, SupplierViewSet

# Import new extended APIs
from finance.api_extended import (
    ARPaymentViewSet as ARPaymentExtendedViewSet,
    APPaymentViewSet as APPaymentExtendedViewSet,
    InvoiceApprovalViewSet, OutstandingInvoicesAPI
)

router = routers.DefaultRouter()
router.register(r"currencies", CurrencyViewSet)
router.register(r"accounts", AccountViewSet)
router.register(r"journals", JournalEntryViewSet)
router.register(r"journal-lines", JournalLineViewSet)
router.register(r"ar/invoices", ARInvoiceViewSet)
router.register(r"ar/payments", ARPaymentExtendedViewSet, basename="ar-payments")  # Extended version with allocations
router.register(r"ap/invoices", APInvoiceViewSet)
router.register(r"ap/payments", APPaymentExtendedViewSet, basename="ap-payments")  # Extended version with allocations
router.register(r"bank-accounts", BankAccountViewSet)
router.register(r"customers", CustomerViewSet)
router.register(r"suppliers", SupplierViewSet)
router.register(r"fx/rates", ExchangeRateViewSet, basename="exchangerate")
router.register(r"fx/accounts", FXGainLossAccountViewSet, basename="fxgainlossaccount")
router.register(r"invoice-approvals", InvoiceApprovalViewSet, basename="invoice-approvals")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/csrf/", GetCSRFToken.as_view(), name="csrf"),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/reports/trial-balance/", TrialBalanceReport.as_view()),
    path("api/reports/ar-aging/", ARAgingReport.as_view()),
    path("api/reports/ap-aging/", APAgingReport.as_view()),
    path("api/tax/seed-presets/", SeedVATPresets.as_view()),
    path("api/tax/rates/", ListTaxRates.as_view()),
    path("api/tax/corporate-accrual/", CorporateTaxAccrual.as_view()),
    path("api/tax/corporate-file/<int:filing_id>/",    CorporateTaxFile.as_view()),
    path("api/tax/corporate-filing/<int:filing_id>/",  CorporateTaxFilingDetail.as_view()),
    path("api/tax/corporate-reverse/<int:filing_id>/", CorporateTaxReverse.as_view()),
    path("api/tax/corporate-breakdown/",               CorporateTaxBreakdown.as_view()),
    path("api/fx/convert/", CurrencyConvertView.as_view(), name="fx-convert"),
    path("api/fx/create-rate/", CreateExchangeRateView.as_view(), name="fx-create-rate"),
    path("api/fx/base-currency/", BaseCurrencyView.as_view(), name="fx-base-currency"),
    path("api/outstanding-invoices/", OutstandingInvoicesAPI.as_view(), name="outstanding-invoices"),
]
#urlpatterns = format_suffix_patterns(urlpatterns)





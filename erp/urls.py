from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from finance.api import (CorporateTaxReverse, JournalEntryViewSet, JournalLineViewSet, ARInvoiceViewSet, ARPaymentViewSet,APInvoiceViewSet, APPaymentViewSet, CurrencyViewSet, GetCSRFToken)
from finance.api import BankAccountViewSet
from segment.api import AccountViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from finance.api import TrialBalanceReport, ARAgingReport, APAgingReport
from rest_framework.urlpatterns import format_suffix_patterns
from finance.api import SeedVATPresets, ListTaxRates, TaxRateDetail, CorporateTaxAccrual,CorporateTaxFile,CorporateTaxBreakdown,CorporateTaxFilingDetail
from finance.api import ExchangeRateViewSet, CurrencyConvertView, CreateExchangeRateView, FXGainLossAccountViewSet, BaseCurrencyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from crm.api import CustomerViewSet
# Note: SupplierViewSet is available at /api/ap/vendors/ with full vendor management features

# Import new extended APIs
from finance.api_extended import (
    ARPaymentViewSet as ARPaymentExtendedViewSet,
    APPaymentViewSet as APPaymentExtendedViewSet,
    InvoiceApprovalViewSet, OutstandingInvoicesAPI
)

# Import attachment API
from procurement.attachments.views import AttachmentViewSet

router = routers.DefaultRouter()
router.register(r"currencies", CurrencyViewSet)
router.register(r"accounts", AccountViewSet, basename='account')
router.register(r"journals", JournalEntryViewSet)
router.register(r"journal-lines", JournalLineViewSet)
router.register(r"ar/invoices", ARInvoiceViewSet)
router.register(r"ar/payments", ARPaymentExtendedViewSet, basename="ar-payments")  # Extended version with allocations
router.register(r"ap/invoices", APInvoiceViewSet)
router.register(r"ap/payments", APPaymentExtendedViewSet, basename="ap-payments")  # Extended version with allocations
router.register(r"bank-accounts", BankAccountViewSet)
router.register(r"customers", CustomerViewSet)
# Suppliers available at /api/ap/vendors/ (full-featured vendor management)
router.register(r"fx/rates", ExchangeRateViewSet, basename="exchangerate")
router.register(r"fx/accounts", FXGainLossAccountViewSet, basename="fxgainlossaccount")
router.register(r"invoice-approvals", InvoiceApprovalViewSet, basename="invoice-approvals")

# Import inventory API viewsets
from inventory.api import (
    InventoryBalanceViewSet, StockMovementViewSet,
    StockAdjustmentViewSet, StockTransferViewSet
)

# Register inventory endpoints
router.register(r"inventory/balances", InventoryBalanceViewSet, basename="inventory-balances")
router.register(r"inventory/movements", StockMovementViewSet, basename="stock-movements")
router.register(r"inventory/adjustments", StockAdjustmentViewSet, basename="stock-adjustments")
router.register(r"inventory/transfers", StockTransferViewSet, basename="stock-transfers")

# Register attachment endpoints
router.register(r"procurement/attachments", AttachmentViewSet, basename="attachments")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/csrf/", GetCSRFToken.as_view(), name="csrf"),
    path("api/", include(router.urls)),
    path("api/segment/", include("segment.urls")),  # Chart of Accounts & Segments
    path("api/periods/", include("periods.urls")),  # Fiscal Period Management
    path("api/ap/", include("ap.urls")),  # Vendor Management endpoints
    path("api/fixed-assets/", include("fixed_assets.urls")),  # Fixed Asset Management endpoints
    
    # Procurement Module - All endpoints under /api/procurement/
    path("api/procurement/", include("procurement.urls")),  # Main procurement router
    
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/reports/trial-balance/", TrialBalanceReport.as_view()),
    path("api/reports/ar-aging/", ARAgingReport.as_view()),
    path("api/reports/ap-aging/", APAgingReport.as_view()),
    path("api/tax/seed-presets/", SeedVATPresets.as_view()),
    path("api/tax/rates/", ListTaxRates.as_view()),
    path("api/tax/rates/<int:pk>/", TaxRateDetail.as_view()),
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

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)






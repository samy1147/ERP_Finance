import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env("DEBUG", default=True)
SECRET_KEY = env("SECRET_KEY", default="dev-secret")

# Get URLs from environment variables
BACKEND_URL = env("BACKEND_URL", default="http://localhost:8007")
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

ALLOWED_HOSTS = ["*"]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",  # NEW: Enable CORS for frontend
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "simple_history",
    "core",
    "segment",  # Chart of Accounts & Segments - MUST come before finance
    "periods",  # Fiscal Periods Management - MUST come before finance
    "finance.apps.FinanceConfig",
    "crm",
    "ar",  # Accounts Receivable
    "ap",  # Accounts Payable
    "fixed_assets",  # Fixed Asset Management
    
    # Procurement Module - All submodules organized under procurement/
    "procurement",  # Main procurement app
    "procurement.rfx",  # RFx & Sourcing Events
    "procurement.vendor_bills",  # Vendor Bills & 3-Way Match
    "procurement.contracts",  # Contracts & Compliance
    "procurement.payments",  # Payment Integration
    "procurement.purchase_orders",  # Purchase Orders (PO)
    "procurement.requisitions",  # Purchase Requisitions (PR)
    "procurement.receiving",  # Receiving & Goods Receipt (GRN)
    "procurement.approvals",  # Approval Workflows
    "procurement.catalog",  # Product Catalog
    "procurement.reports",  # Analytics & Reports
    "procurement.attachments",  # File Attachments
    "inventory",  # Inventory & Warehouse Management
]

# Silence admin checks that fail due to lazy model loading
SILENCED_SYSTEM_CHECKS = ['admin.E038']

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # NEW: CORS middleware (must be before CommonMiddleware)
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "erp.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "erp.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []
STATIC_URL = "static/"

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

}

SPECTACULAR_SETTINGS = {
    "TITLE": "Finance ERP API",
    "DESCRIPTION": "Finance module (GL, AR/AP)",
    "VERSION": "0.1.0",
    "SERVERS": [{"url": f"{BACKEND_URL}/api"}],
    "COMPONENT_SPLIT_REQUEST": True,
}

# CORS Settings - Allow all origins (public API access)
CORS_ALLOW_ALL_ORIGINS = True

# CSRF Trusted Origins - Required for Django 4.0+
CSRF_TRUSTED_ORIGINS = [
    FRONTEND_URL,  # Use environment variable
    BACKEND_URL,   # Backend URL
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:8007",
    "http://127.0.0.1:8007",
]

# CSRF Cookie Settings - For cross-origin requests
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read the cookie
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS

# Allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

# Allow specific headers
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Media Files Configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Maximum file upload size (10MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB in bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB in bytes


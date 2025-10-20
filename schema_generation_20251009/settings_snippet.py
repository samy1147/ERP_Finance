# Install: pip install drf-spectacular
INSTALLED_APPS += [
    "drf_spectacular",
    # Optional: offline Swagger/Redoc assets
    # "drf_spectacular_sidecar",
]

REST_FRAMEWORK.update({
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
})

SPECTACULAR_SETTINGS = {
    "TITLE": "Mini ERP Finance API",
    "DESCRIPTION": "Auto-generated schema for GL posting, payments, reports",
    "VERSION": "1.0.0",
    "SERVERS": [{"url": "http://localhost:8000/api"}],
    "COMPONENT_SPLIT_REQUEST": True,
}
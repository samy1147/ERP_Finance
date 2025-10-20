# Schema Generation Bundle — 2025-10-09

This bundle enables **auto OpenAPI schema generation** using **drf-spectacular** and annotates your endpoints for better docs.

## Files
- **api.py** — your `api.py` with `@extend_schema` annotations for:
  - `ARInvoiceViewSet.post_gl` and `APInvoiceViewSet.post_gl` (with response examples)
  - `ARPaymentViewSet.create` and `APPaymentViewSet.create` (with request and response examples)
  - `JournalEntryViewSet.export`, `TrialBalanceReport`, `ARAgingReport`, `APAgingReport`
- **urls_snippet.py** — code to add schema endpoints (`/api/schema/`, `/api/docs/`, `/api/redoc/`)
- **settings_snippet.py** — `INSTALLED_APPS`, `REST_FRAMEWORK.DEFAULT_SCHEMA_CLASS`, `SPECTACULAR_SETTINGS`

## Install
```bash
pip install drf-spectacular
# Optional if you want to serve Swagger/Redoc assets locally:
# pip install "drf-spectacular[sidecar]"
```

## Wire up
1. Copy the **api.py** from this bundle over your project `api.py` (or merge the `@extend_schema` parts).
2. In your project **settings.py** add the snippet from `settings_snippet.py`.
3. In your main **urls.py**, add the `schema_urlpatterns` from `urls_snippet.py`:
   ```python
   from django.urls import include, path
   from schema.urls_snippet import schema_urlpatterns  # or paste directly

   urlpatterns = [
       # ... existing routes ...
       *schema_urlpatterns,
   ]
   ```

## Use
- Visit **/api/docs/** for Swagger UI or **/api/redoc/** for ReDoc.
- **/api/schema/** returns the raw OpenAPI JSON.

> Tip: Combine this with the provided `docs/openapi.yaml` as a reference — the runtime schema is generated from your code, and the annotations here are aligned with those examples.
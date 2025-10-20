# Docs & Tests Package — 2025-10-09

This folder gives you **OpenAPI examples** for GL posting & payments, plus **pytest** tests covering idempotency, rounding, payments, and AR aging.

## Structure
- `docs/openapi.yaml` — Minimal OpenAPI with **examples** for:
  - `POST /ar/invoices/{id}/post-gl/`
  - `POST /ap/invoices/{id}/post-gl/`
  - `POST /ar/payments/`
  - `POST /ap/payments/`
- `docs/openapi_examples.md` — cURL/HTTP examples matching the YAML.
- `tests/` — pytest tests:
  - `test_idempotency.py` — idempotent AR post-to-GL
  - `test_rounding.py` — edge rounding on VAT calc
  - `test_payments.py` — partial/update/FX payment flow and invoice close
  - `test_aging.py` — AR aging buckets sanity check
  - `conftest.py` — isolated base data (currencies, CoA, bank, VAT5)

## Running the tests
1. Ensure `pytest` and `pytest-django` are installed:
   ```bash
   pip install pytest pytest-django
   ```
2. Set `DJANGO_SETTINGS_MODULE` to your project's settings (e.g., `myproj.settings`) **or** add it in `pytest.ini`.
3. Run:
   ```bash
   pytest -q
   ```

### Notes
- Tests create their **own minimal base data** (accounts, AED, VAT5) so they do not depend on your `seed_erp` command.
- Account codes in tests match the canonical map used in `services.py`:
  `BANK=1000`, `AR=1100`, `AP=2000`, `VAT_OUT=2100`, `VAT_IN=2110`, `REV=4000`, `EXP=5000`, `TAX_CORP_PAYABLE=2400`, `TAX_CORP_EXP=6900`, `FX_GAIN=7150`, `FX_LOSS=8150`.
- If your project uses different app labels or paths, update imports at the top of the tests accordingly.
# OpenAPI Examples — Post GL & Payments

Below are quick HTTP examples that match the OpenAPI (`docs/openapi.yaml`). Adjust base URLs & IDs for your environment.

## Post AR invoice to GL (idempotent)
```bash
curl -X POST http://localhost:8000/api/ar/invoices/123/post-gl/   -H "Authorization: Bearer <token>"
```

## Post AP invoice to GL (idempotent)
```bash
curl -X POST http://localhost:8000/api/ap/invoices/456/post-gl/   -H "Authorization: Bearer <token>"
```

## Create AR payment (auto-posts to GL)
```bash
curl -X POST http://localhost:8000/api/ar/payments/   -H "Content-Type: application/json" -H "Authorization: Bearer <token>"   -d '{
    "invoice": 123,
    "date": "2025-10-02",
    "amount": 105.00,
    "bank_account": 1
  }'
```

### AR payment with FX (gain/loss lines if FX accounts seeded)
```bash
curl -X POST http://localhost:8000/api/ar/payments/   -H "Content-Type: application/json" -H "Authorization: Bearer <token>"   -d '{
    "invoice": 123,
    "date": "2025-10-02",
    "amount": 100.00,
    "bank_account": 1,
    "payment_fx_rate": 1.050000
  }'
```

## Create AP payment
```bash
curl -X POST http://localhost:8000/api/ap/payments/   -H "Content-Type: application/json" -H "Authorization: Bearer <token>"   -d '{
    "invoice": 456,
    "date": "2025-10-02",
    "amount": 115.00,
    "bank_account": 1
  }'
```
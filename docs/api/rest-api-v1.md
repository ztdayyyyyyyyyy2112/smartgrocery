# SmartGrocery REST API v1

Base URL (local): `http://localhost:8000/api/v1`

This is the contract between:

- Next.js frontend (`apps/web`)
- FastAPI (`services/api`)
- Intelligence service (`services/intelligence`) via backend job/forecast endpoints

Do not change path names, required fields, or status enums without a group review.
Implementation comes in later backend PRs. This PR only freezes the contract.

## 1. Conventions

### 1.1 Headers

| Header | Required | Notes |
|---|---|---|
| `Authorization` | protected routes | `Bearer <jwt>` |
| `Content-Type` | JSON bodies | `application/json` |
| `Idempotency-Key` | `POST /orders` | UUID or opaque string, unique per customer |

### 1.2 Error body

```json
{
  "error": {
    "code": "STOCK_INSUFFICIENT",
    "message": "Not enough sellable quantity for SKU MILK-1L",
    "details": { "product_id": "...", "requested": 3, "available": 1 }
  }
}
```

Stable `code` values: `VALIDATION_ERROR`, `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `IDEMPOTENCY_CONFLICT`, `STOCK_INSUFFICIENT`, `BATCH_EXPIRED`, `JOB_FAILED`.

### 1.3 Pagination

List endpoints accept `page` (default 1) and `page_size` (default 20, max 100) and return:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

### 1.4 Money and quantity

- Money: string decimal in JSON, e.g. `"45000.00"`, currency `VND`.
- Quantity: string decimal, e.g. `"1.500"`.

## 2. Auth

### `POST /auth/register`

Body: `{ "email", "password", "full_name" }`

Creates a `customer`. Returns tokens + user public profile.

### `POST /auth/login`

Body: `{ "email", "password" }`

Returns:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user": { "id": "...", "email": "...", "full_name": "...", "role": "customer" }
}
```

### `POST /auth/refresh`

Body: `{ "refresh_token" }` → new access token (and rotated refresh token).

### `GET /auth/me`

Returns the current user.

## 3. Catalog

### `GET /categories`

Public. Items: `{ id, slug, name, image_url }`.

### `GET /products`

Public. Query: `q`, `category_id`, `page`, `page_size`.

Each item includes availability for the default store:

```json
{
  "id": "...",
  "sku": "APL-FUJI-01",
  "name": "Fuji Apple",
  "unit": "kg",
  "selling_price": "39000.00",
  "image_url": "...",
  "category": { "id": "...", "slug": "fruits", "name": "Fruits" },
  "available_qty": "12.000",
  "is_active": true
}
```

### `GET /products/{product_id}`

Public product detail. Same fields plus `description`, `is_perishable`.

## 4. Cart and checkout

The MVP cart may live in the frontend. Checkout is the source of truth.

### `POST /orders`

Customer only. Header `Idempotency-Key` required.

Body:

```json
{
  "store_id": "...",
  "items": [
    { "product_id": "...", "quantity": "2" }
  ]
}
```

Server must, in one transaction:

1. Lock candidate batches with FEFO.
2. Reject if any line `requested > available`.
3. Create `orders`, `order_items`, `stock_reservations`.
4. Increase `quantity_reserved`.
5. Persist idempotency record.

Success `201` returns the order. Replay of the same key returns `200` and the original order.

### `GET /orders`

Customer: own orders. Merchant/admin: all orders in the store (`status` filter allowed).

### `GET /orders/{order_id}`

Includes items and reservation summary.

### `POST /orders/{order_id}/cancel`

Customer may cancel `pending`/`confirmed` if not fulfilled.
Merchant may cancel with reason. Releases reservations.

### `POST /orders/{order_id}/fulfil`

Merchant/admin. Decrements `quantity_on_hand` and `quantity_reserved` on reserved batches.

## 5. Inventory

Merchant/admin.

### `GET /inventory`

Query: `store_id`, `product_id`, `low_stock_only`.

Item:

```json
{
  "store_id": "...",
  "product_id": "...",
  "sku": "...",
  "name": "...",
  "on_hand": "20.000",
  "reserved": "3.000",
  "available": "17.000",
  "nearest_expiry": "2026-11-04",
  "alerts": ["LOW_STOCK", "EXPIRY_WARNING"]
}
```

### `GET /inventory/batches`

Query: `store_id`, `product_id`, `status`.

### `POST /inventory/batches/{batch_id}/quarantine`

Sets `status = quarantined`. Remaining sellable qty becomes 0.

## 6. Suppliers and procurement

Merchant/admin.

### `GET|POST /suppliers`

### `GET|PATCH /suppliers/{supplier_id}`

### `GET|PUT /suppliers/{supplier_id}/products`

Catalog of what a supplier can provide, with `unit_cost` and `min_order_qty`.

### `POST /purchase-orders`

Body: `{ store_id, supplier_id, items: [{ product_id, quantity, unit_cost }], notes }`

Status starts as `draft` or `pending_approval` (implementation may start at `pending_approval`).

### `GET /purchase-orders` and `GET /purchase-orders/{id}`

### `POST /purchase-orders/{id}/approve`

`draft|pending_approval` → `approved`. Sets `approved_by`.

### `POST /purchase-orders/{id}/send`

`approved` → `sent`.

### `POST /purchase-orders/{id}/receive`

Body:

```json
{
  "items": [
    {
      "product_id": "...",
      "quantity": "10",
      "lot_code": "LOT-20261101",
      "expiry_date": "2026-11-20",
      "unit_cost": "12000.00"
    }
  ]
}
```

Creates `goods_receipts` + `inventory_batches` and updates PO status to `partially_received` or `received`.

### `POST /purchase-orders/{id}/cancel`

Allowed before any receipt.

## 7. Forecasting and recommendations

Merchant/admin read models. Intelligence service writes through job APIs, not directly from the browser.

### `GET /forecasts`

Query: `store_id`, `product_id`, `from`, `to`, `model_name`.

Item grain: store–SKU–day for a 7-day horizon.

```json
{
  "store_id": "...",
  "product_id": "...",
  "target_date": "2026-11-01",
  "predicted_qty": "24.000",
  "model_name": "lightgbm",
  "model_version": "2026-10-30"
}
```

### `GET /recommendations`

Query: `status`, `store_id`.

```json
{
  "id": "...",
  "product_id": "...",
  "suggested_qty": "40.000",
  "safety_stock": "12.000",
  "reorder_point": "18.000",
  "meu_score": "0.812000",
  "reason": "Predicted 7-day demand exceeds available stock after safety stock",
  "status": "pending"
}
```

### `POST /recommendations/{id}/approve`

Optional body `{ "convert_to_po": true, "supplier_id": "..." }`.
If `convert_to_po` is true, creates a purchase order and sets `status = converted`.

### `POST /recommendations/{id}/reject`

### `POST /jobs/forecasts`

Starts a forecast job. Returns `{ "job_id", "status": "queued" }`.

### `GET /jobs/{job_id}`

Job status for UI polling until WebSocket exists.

## 8. Intelligence service contract

FastAPI owns HTTP to the frontend. The intelligence service is an internal Python package/worker.

Backend → intelligence input:

```json
{
  "store_id": "...",
  "as_of": "2026-10-28",
  "horizon_days": 7,
  "sales": [
    { "product_id": "...", "date": "2026-10-01", "qty": "10.000" }
  ],
  "inventory": [
    { "product_id": "...", "available": "8.000", "on_hand": "10.000" }
  ]
}
```

Intelligence → backend output:

```json
{
  "model_name": "lightgbm",
  "model_version": "2026-10-30",
  "forecasts": [
    { "product_id": "...", "target_date": "2026-10-29", "predicted_qty": "11.000" }
  ],
  "recommendations": [
    {
      "product_id": "...",
      "suggested_qty": "20.000",
      "safety_stock": "6.000",
      "reorder_point": "14.000",
      "meu_score": "0.74",
      "reason": "..."
    }
  ]
}
```

If inference fails, backend stores `job_status = failed` and does not invent forecast numbers. Fallback model selection is owned by the intelligence service (`seasonal_naive` then `lightgbm`).

## 9. Rule engine (backend)

Rules run inside FastAPI on inventory and checkout, not in the ML service.

| Code | When | Effect |
|---|---|---|
| `FEFO_ALLOCATION` | checkout | allocate earliest expiry first |
| `DO_NOT_SELL_EXPIRED` | checkout / catalog | exclude expired batches from `available` |
| `EXPIRY_WARNING` | inventory read | alert when expiry within N days (default 3) |
| `LOW_STOCK_ALERT` | inventory read | alert when `available` < reorder point if present, else < configured threshold |

## 10. Health

### `GET /health`

`{ "status": "ok" }` — public, used by Docker later.

OpenAPI/Swagger will be generated from FastAPI once `feat/be-fastapi-setup` lands. This markdown remains the human contract.

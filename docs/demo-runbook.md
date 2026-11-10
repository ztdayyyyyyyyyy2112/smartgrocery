# SmartGrocery demo runbook

## Start

Use Docker Desktop/Compose. From the repository root:

```powershell
docker compose up -d --build
docker compose exec api python scripts/seed.py
python scripts/demo_smoke.py
```

The first build trains the AI model from reproducible synthetic data and may take several minutes. `docker compose ps` should show PostgreSQL, Redis, intelligence, API, worker, beat and web. Open the web app at `http://localhost:3000`.

## Click path

1. Choose store `S001`. Log in as `customer@smartgrocery.example.com` / `DemoPass123!`. Add `SKU005` to cart, check the red cart count, enter recipient/phone/address, and check out. Order history should show the store and delivery details.
2. Log out and log in as `merchant@smartgrocery.example.com` / `DemoPass123!`. This merchant belongs to `S001`. Dashboard Orders shows delivery details; Inventory shows `SKU005` with less available stock due to reservation. Orders can fulfil the order to decrease physical stock.
3. Go to Forecasting and run the 7-day job. Wait for `succeeded`. Forecast rows should be visible; their history cutoff is 09/11/2026.
4. Go to Recommendations, approve the pending `SKU005` recommendation and create a PO. Go to Procurement, approve → send → receive the PO. Inventory should increase.

The automated smoke test performs the same API sequence and prints `DEMO PASS`. It uses synthetic sales history and a local demo catalog; it does not process payments. `docker compose down` stops services while keeping data. `docker compose down -v` intentionally removes the demo database and Redis data.

## If a step fails

- `docker compose ps` / `docker compose logs api worker intelligence web` show service failures.
- If login fails, rerun `docker compose exec api python scripts/seed.py` and use the documented demo credentials.
- If a forecast job fails, check its error on the Forecasting page, then `docker compose logs worker intelligence`. Confirm `intelligence` is healthy and `FORECAST_AUTORUN=true` for API.
- If the model is absent, rebuild `intelligence`: `docker compose build intelligence` then `docker compose up -d intelligence`.
- If browser API calls fail, use `http://localhost:3000` (not a different origin), check `http://localhost:8000/health`, and rebuild web if `NEXT_PUBLIC_API_URL` changed.

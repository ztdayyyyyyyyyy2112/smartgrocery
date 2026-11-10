# SmartGrocery

SmartGrocery is a grocery commerce prototype with a Next.js storefront and merchant dashboard, a FastAPI business API, PostgreSQL inventory and procurement records, Redis/Celery event delivery, and a standalone intelligence service for synthetic-data demand forecasting and replenishment recommendations.

## Current status

The demo integrates the Next.js storefront and merchant dashboard with the FastAPI business API, PostgreSQL, Redis/Celery, and the standalone intelligence service. The canonical demo catalog uses `S001`–`S003` and `SKU001`–`SKU032`; database UUIDs remain internal. Forecasts use synthetic historical sales ending 09/11/2026 and live inventory from the backend. This is an academic demo, not a production commerce or payment system.

Track the acceptance checklist in [release readiness #46](https://github.com/ztdayyyyyyyyyy2112/smartgrocery/issues/46). The `v1.0.0` tag records an earlier **backend milestone**, not a full-product release.

## Repository layout

- `apps/web` — Next.js storefront and merchant dashboard shell.
- `services/api` — FastAPI, Alembic migrations, Celery worker and seed script.
- `services/intelligence` — synthetic data, forecasting, replenishment optimization and standalone inference API.
- `tests/api` — backend tests; `tests/intelligence` — intelligence tests.
- `docs/architecture` and `docs/api` — design and API contracts.
- `docs/release-evidence.md` — results recorded by the backend team.
- `database/demo` — tracked shared Store–SKU catalog for both sides of the demo.
- `scripts/demo_smoke.py` — automated checkout-to-receiving acceptance check.

## Run the complete demo with Docker Compose

Install Docker Desktop with Compose. From the repository root in PowerShell:

```powershell
docker compose up -d --build
docker compose exec api python scripts/seed.py
python scripts/demo_smoke.py
```

Open http://localhost:3000. AI Swagger is at http://localhost:8001/docs and business API Swagger at http://localhost:8000/docs. First build trains the model from synthetic data and may take several minutes. Demo accounts: `customer@smartgrocery.example.com` and `merchant@smartgrocery.example.com`, password `DemoPass123!` (change with `SG_DEMO_PASSWORD` when seeding manually). Keep these credentials local; do not deploy the demo seed publicly.

Manual click path: customer login → add `SKU005` to cart → checkout at `S001` → merchant login → Inventory → Forecasting (run job; wait for succeeded) → Recommendations (approve and create PO) → Procurement (approve, send, receive) → Inventory (observe increase). Merchant may fulfil the customer order from Orders. `docs/demo-runbook.md` records expected results and troubleshooting.

Stop with `docker compose down`; add `-v` only when intentionally deleting the demo database.

## Run services separately

Prerequisites: Python 3.11, Node.js 22, npm, and Docker Compose (or local PostgreSQL and Redis). Commands below use PowerShell from the repository root.

1. Create local configuration and start the two infrastructure services:

   ```powershell
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   docker compose up -d postgres redis
   ```

2. Install, migrate, seed and start the API:

   ```powershell
   Set-Location services/api
   py -3.11 -m venv .venv
   & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   & .\.venv\Scripts\python.exe -m alembic upgrade head
   & .\.venv\Scripts\python.exe scripts/seed.py
   & .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
   ```

   Open http://localhost:8000/health and http://localhost:8000/docs. The sample credentials in `.env.example` are for local development only.

3. In a second terminal, start the frontend:

   ```powershell
   Set-Location apps/web
   npm ci
   npm run dev
   ```

   Open http://localhost:3000. The storefront calls the API at `NEXT_PUBLIC_API_URL`.

4. For event processing, run these optional commands in separate terminals from `services/api` using its virtual environment:

   ```powershell
   & .\.venv\Scripts\python.exe -m celery -A app.worker.celery_app worker --loglevel=info --pool=solo
   & .\.venv\Scripts\python.exe -m celery -A app.worker.celery_app beat --loglevel=info
   ```

5. To run the intelligence service independently, open another terminal from the repository root:

   ```powershell
   Set-Location services/intelligence
   py -3.11 -m venv .venv
   & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   & .\.venv\Scripts\python.exe scripts/run_pipeline.py --regenerate-data
   & .\.venv\Scripts\python.exe -m uvicorn src.inference.api:app --port 8001
   ```

   Open http://localhost:8001/docs. Set `FORECAST_AUTORUN=true`, keep a Celery worker running, and rerun `scripts/seed.py` after migrating the database.

## Checks

From the repository root, after the API dependencies, PostgreSQL and Redis are available:

```powershell
& .\services\api\.venv\Scripts\python.exe -m pytest -q
Set-Location apps/web
npm run lint
npm run build
```

CI runs web, backend, AI and the Docker Compose demo smoke check. See [backend release evidence](docs/release-evidence.md) for older backend-only results.

After running the intelligence pipeline, check its tests with `& .\services\intelligence\.venv\Scripts\python.exe -m pytest tests/intelligence -q` from the repository root. The intelligence suite passed 46 tests locally on 10 November 2026. CI regenerates the synthetic data and model before running this suite.

## Collaboration

Create a task branch from the latest `develop`, open a pull request into `develop`, and include test results. Merge only when CI and the task's acceptance criteria pass; reviewer invitations are optional. Promote `develop` to `main` through the [draft release PR](https://github.com/ztdayyyyyyyyyy2112/smartgrocery/pull/47) only after the acceptance checklist is complete. Keep `.env`, real credentials, raw datasets and generated model files out of Git.

# SmartGrocery

SmartGrocery is a grocery commerce prototype with a Next.js storefront and merchant dashboard, a FastAPI business API, PostgreSQL inventory and procurement records, and Redis/Celery event delivery. The planned intelligence service will provide demand forecasts and replenishment recommendations.

## Current status

The backend includes authentication, catalog, orders, inventory batches, purchase orders, forecast job APIs, outbox processing and tests. The frontend is a visual shell: catalog data is mocked, and login, cart, checkout and several dashboard views are placeholders. `services/intelligence` does not yet contain a runnable forecasting pipeline. The backend integration test posts a prepared forecast result; it does not run model inference. This repository is a prototype in progress, not a complete end-to-end release.

Track the acceptance checklist in [release readiness #46](https://github.com/ztdayyyyyyyyyy2112/smartgrocery/issues/46). The `v1.0.0` tag records an earlier **backend milestone**, not a full-product release.

## Repository layout

- `apps/web` — Next.js storefront and merchant dashboard shell.
- `services/api` — FastAPI, Alembic migrations, Celery worker and seed script.
- `services/intelligence` — reserved for the forecasting and decision pipeline.
- `tests/api` — backend tests.
- `docs/architecture` and `docs/api` — design and API contracts.
- `docs/release-evidence.md` — results recorded by the backend team.

## Run locally

Prerequisites: Python 3.12, Node.js 22, npm, and Docker Compose (or local PostgreSQL and Redis). Commands below use PowerShell from the repository root.

1. Create local configuration and start the two infrastructure services:

   ```powershell
   Copy-Item .env.example .env
   docker compose up -d postgres redis
   ```

2. Install, migrate, seed and start the API:

   ```powershell
   Set-Location services/api
   py -3.12 -m venv .venv
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

   Open http://localhost:3000. The pages render, but the storefront is not connected to the API yet.

4. For event processing, run these optional commands in separate terminals from `services/api` using its virtual environment:

   ```powershell
   & .\.venv\Scripts\python.exe -m celery -A app.worker.celery_app worker --loglevel=info --pool=solo
   & .\.venv\Scripts\python.exe -m celery -A app.worker.celery_app beat --loglevel=info
   ```

## Checks

From the repository root, after the API dependencies, PostgreSQL and Redis are available:

```powershell
& .\services\api\.venv\Scripts\python.exe -m pytest -q
Set-Location apps/web
npm run lint
npm run build
```

The CI workflow runs these checks for pull requests. See [backend release evidence](docs/release-evidence.md) for recorded backend results. A clean-run result for the entire product is still required.

## Collaboration

Create a task branch from the latest `develop`, open a pull request into `develop`, include test results, and ask another team member to review. Promote `develop` to `main` through the [draft release PR](https://github.com/ztdayyyyyyyyyy2112/smartgrocery/pull/47) only after the acceptance checklist is complete. Keep `.env`, real credentials, raw datasets and generated model files out of Git.

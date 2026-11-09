# SmartGrocery API

FastAPI business service on port 8000. For the full repository layout and current product status, start with the [root README](../../README.md). This service requires PostgreSQL; Redis is required for the worker and realtime event test.

## Local setup

Run these PowerShell commands from the repository root:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres redis
Set-Location services/api
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m alembic upgrade head
& .\.venv\Scripts\python.exe scripts/seed.py
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/health, http://localhost:8000/docs or http://localhost:8000/openapi.json. The local seed creates demo products and inventory; it does not supply historical sales for model training.

If Docker is unavailable, start local PostgreSQL and Redis services matching the values in `.env`, then run the same migrations and seed commands. See the [backend runbook](../../docs/backend-runbook.md) for the Windows PostgreSQL service path.

## Tests

From the repository root, with PostgreSQL and Redis running:

```powershell
& .\services\api\.venv\Scripts\python.exe -m pytest -q
```

Use a separate test database by setting `DATABASE_URL` in the terminal before running migrations, seed and tests. The CI workflow does this automatically.

## Optional event worker

In separate terminals opened at `services/api`:

```powershell
& .\.venv\Scripts\python.exe -m celery -A app.worker.celery_app worker --loglevel=info --pool=solo
& .\.venv\Scripts\python.exe -m celery -A app.worker.celery_app beat --loglevel=info
```

Load probe commands and recorded results are in [release evidence](../../docs/release-evidence.md). The forecast job API accepts intelligence results, but model inference is still a separate team deliverable.

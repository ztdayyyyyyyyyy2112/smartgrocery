# SmartGrocery Backend Runbook

This runbook starts the FastAPI backend with local PostgreSQL and optional Redis/Celery.
Run commands from PowerShell unless noted otherwise.

## 1. Prerequisites

- PostgreSQL 18 service installed and running.
- Python virtual environment at `services/api/.venv`.
- Docker Desktop only if Redis is needed.

Check PostgreSQL:

```powershell
Get-Service postgresql-x64-18
Start-Service postgresql-x64-18 # only when it is stopped
```

## 2. Python environment

```powershell
cd F:\smartgrocery\smartgrocery\services\api
python -m venv .venv # skip when .venv already exists
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The default `.env` points to the local `smartgrocery` database. Never commit `.env`.

## 3. Database migration and seed

```powershell
& .\.venv\Scripts\python.exe -m alembic upgrade head
& .\.venv\Scripts\python.exe scripts/seed.py
```

For clean-database verification, use a separate database and set `DATABASE_URL`
only in the current PowerShell session.

## 4. Start FastAPI

```powershell
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Open:

- Health: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json

Expected health response includes `status=ok` and `database=connected`.

## 5. Run tests

In a second terminal:

```powershell
cd F:\smartgrocery\smartgrocery
& .\services\api\.venv\Scripts\python.exe -m pytest -q
```

The latest verified suite has 29 passing tests. Non-blocking Starlette/pytest
warnings may appear.

## 6. Optional Redis and Celery

Start Redis with Docker:

```powershell
docker start smartgrocery-redis
# or, on first run:
docker run -d --name smartgrocery-redis -p 6379:6379 redis:7
docker exec -it smartgrocery-redis redis-cli ping
```

Start the Windows-compatible Celery worker:

```powershell
cd F:\smartgrocery\smartgrocery\services\api
$env:CELERY_BROKER_URL="redis://localhost:6379/0"
$env:CELERY_RESULT_BACKEND="redis://localhost:6379/1"
& .\.venv\Scripts\python.exe -m celery -A app.worker.celery_app worker --loglevel=INFO --pool=solo
```

Verify from another terminal:

```powershell
& .\.venv\Scripts\python.exe -m celery -A app.worker.celery_app inspect ping
& .\.venv\Scripts\python.exe -m celery -A app.worker.celery_app call app.worker.run_outbox_batch
```

## 7. WebSocket and load probe

- WebSocket URL: `ws://127.0.0.1:8000/ws/events`.
- Use browser DevTools or the automated `tests/api/test_realtime.py`; do not paste
  `ws://` directly into the browser address bar.

Load probe from the repository root:

```powershell
& .\services\api\.venv\Scripts\python.exe services/api/scripts/load_test.py --requests 50 --concurrency 10
```

## 8. Troubleshooting

- `python.exe not recognized`: change directory to `services/api` or use the absolute virtualenv path.
- `database does not exist`: create the database and check `DATABASE_URL`.
- Docker/WSL errors: use the local PostgreSQL service; Docker is optional for the API.
- `rg not recognized`: use PowerShell `Select-String` instead.
- Never reset the development database to fix a test; use a separate test database.
## Final handoff verification — 2026-11-06

From the repository root, the final verification commands are:

```powershell
cd services/api
& .\.venv\Scripts\python.exe -m alembic upgrade head
cd ../..
& .\services\api\.venv\Scripts\python.exe -m pytest -q
```

Expected result: `38 passed`. Redis must be running for the realtime integration test.

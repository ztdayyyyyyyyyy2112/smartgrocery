# Backend release evidence

## Environment

- FastAPI backend: `services/api`
- PostgreSQL: local PostgreSQL 18 service (`smartgrocery` database)
- Docker: optional; not required for local verification
- API docs: `/docs` and `/openapi.json`

## Reproduction commands

```powershell
cd F:\smartgrocery\smartgrocery\services\api
& .\.venv\Scripts\python.exe -m alembic upgrade head
cd ..\..
& .\services\api\.venv\Scripts\python.exe -m pytest -q
```

## Verified evidence

- Alembic migrations through forecast jobs completed successfully.
- Full backend suite: `24 passed` on the hardening branch.
- Integration flow verified: checkout → inventory → forecast job → recommendation → purchase order → receiving.
- Concurrency verified: two simultaneous checkouts against one unit produce one `201` and one `409 STOCK_INSUFFICIENT`.
- RBAC verified for unauthenticated and customer access to merchant-only endpoints.

## Known non-blocking warnings

- Starlette AnyIO deprecation warning.
- Pytest cache path warning on the Windows workspace.

## Clean database verification — 2026-11-05

Database: `smartgrocery_test` (new empty PostgreSQL database owned by `smartgrocery`).

Commands executed:

```powershell
$env:DATABASE_URL="postgresql+psycopg://smartgrocery:smartgrocery@localhost:5432/smartgrocery_test"
cd services/api
& .\.venv\Scripts\python.exe -m alembic upgrade head
& .\.venv\Scripts\python.exe scripts/seed.py
cd ../..
& .\services/api\.venv\Scripts\python.exe -m pytest -q
```

Results:

- Migrations `0001_extensions` through `0006_forecast_jobs`: passed.
- Seed: completed successfully.
- Full test suite: `24 passed, 1 warning`.
- Existing development database was not reset or modified.

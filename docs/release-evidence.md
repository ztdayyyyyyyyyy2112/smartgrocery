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

## Celery/Redis verification — 2026-11-05

- Redis 7 container `smartgrocery-redis` started on `localhost:6379`.
- `redis-cli ping` returned `PONG`.
- Celery worker `v5.5.3` connected to broker/result backend successfully.
- Worker task `app.worker.run_outbox_batch` completed: `{'published': 12, 'failed': 0}`.

## Schema backup readiness — 2026-11-05

- `pg_dump.exe` and `pg_restore.exe` are installed under PostgreSQL 18.
- Reproducible schema-only and custom-format backup commands are documented in `docs/schema-backup.md`.
- Backup artifacts must remain outside Git and use approved secure storage.
## Business endpoint load test — 2026-11-06

Endpoint: `GET /api/v1/products` on local PostgreSQL-backed API.

| Requests | Concurrency | Success | Throughput | p50 | p95 | p99 | Max |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 10 | 50/50 | 108.81 RPS | 54.96 ms | 203.83 ms | 221.95 ms | 221.95 ms |
| 100 | 20 | 100/100 | 142.14 RPS | 113.62 ms | 260.32 ms | 295.74 ms | 295.74 ms |
| 200 | 40 | 200/200 | 192.93 RPS | 179.90 ms | 341.55 ms | 377.51 ms | 377.55 ms |

All requests succeeded. These local measurements are evidence for development validation, not a production capacity guarantee.

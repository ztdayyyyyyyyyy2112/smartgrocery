# SmartGrocery API

FastAPI backend. Run this service on port 8000.

## 1. Python environment

From `services/api`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Database

Copy the repo-root `.env.example` to `.env`.

Create a PostgreSQL database that matches `DATABASE_URL`:

- user: `smartgrocery`
- password: `smartgrocery`
- database: `smartgrocery`
- port: `5432`

If you use Docker Desktop instead of a local install:

```powershell
docker compose up -d postgres
```

Apply migrations:

```powershell
cd services/api
alembic upgrade head
```

Seed deterministic catalog/inventory data:

```powershell
python scripts/seed.py
```

Run the backend test suite from the repository root:

```powershell
cd ../..
..\services\api\.venv\Scripts\python.exe -m pytest -q
```

## 3. Run the API

```powershell
cd services/api
uvicorn app.main:app --reload --port 8000
```

Open:

- Health: http://localhost:8000/health
- Swagger: http://localhost:8000/docs

Smoke checks:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/api/v1/categories
Invoke-RestMethod http://localhost:8000/api/v1/products
```

The API uses PostgreSQL through `DATABASE_URL`. Docker is optional; if Docker
Desktop/WSL is unavailable, start the local PostgreSQL Windows service and run
the same migrations against it.

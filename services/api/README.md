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

## 3. Run the API

```powershell
cd services/api
uvicorn app.main:app --reload --port 8000
```

Open:

- Health: http://localhost:8000/health
- Swagger: http://localhost:8000/docs

# smartgrocery
Intelligent E-Commerce Platform with Knowledge-Based Reasoning, Demand Forecasting and Replenishment Planning

## Backend (FastAPI)

See `services/api/README.md`. Short version:

1. Copy `.env.example` to `.env`
2. Create PostgreSQL database `smartgrocery` (user/password `smartgrocery`)
3. `cd services/api` then `python -m venv .venv` and `pip install -r requirements.txt`
4. `alembic upgrade head`
5. `uvicorn app.main:app --reload --port 8000`
6. Open http://localhost:8000/docs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import database_is_connected

app = FastAPI(
    title="SmartGrocery API",
    version="0.1.0",
    description="Backend for catalog, orders, inventory, and procurement.",
)

# The Next.js app runs on port 3000 during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict[str, str]:
    connected = database_is_connected()
    return {
        "status": "ok" if connected else "degraded",
        "database": "connected" if connected else "disconnected",
    }

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import database_is_connected
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.orders import router as orders_router
from app.api.inventory import router as inventory_router
from app.api.procurement import router as procurement_router
from app.api.forecast import router as forecast_router
from app.realtime import manager

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
app.include_router(auth_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(procurement_router, prefix="/api/v1")
app.include_router(forecast_router, prefix="/api/v1")


@app.websocket("/ws/events")
async def events_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict[str, str]:
    connected = database_is_connected()
    return {
        "status": "ok" if connected else "degraded",
        "database": "connected" if connected else "disconnected",
    }

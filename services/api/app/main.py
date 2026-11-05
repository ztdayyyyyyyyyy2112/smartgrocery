import asyncio
import json

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from uuid import uuid4
import jwt
from redis import asyncio as redis_asyncio
from app.core.config import get_settings
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import database_is_connected
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.orders import router as orders_router
from app.api.inventory import router as inventory_router
from app.api.procurement import router as procurement_router
from app.api.forecast import router as forecast_router
from app.realtime import manager
from app.event_publisher import EVENTS_CHANNEL

app = FastAPI(
    title="SmartGrocery API",
    version="0.1.0",
    description="Backend for catalog, orders, inventory, and procurement.",
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except IntegrityError:
        response = JSONResponse(status_code=409, content={"detail": "Database constraint violated"})
    except OperationalError:
        response = JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable"})
    except Exception:
        response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
    response.headers["X-Request-ID"] = request_id
    return response

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
    token = websocket.query_params.get("access_token")
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    try:
        payload = jwt.decode(token, get_settings().jwt_secret_key.get_secret_value(), algorithms=["HS256"])
        if payload.get("type") != "access" or payload.get("role") not in {"merchant", "admin"}:
            raise ValueError("invalid websocket role")
    except (jwt.PyJWTError, ValueError):
        await websocket.close(code=1008, reason="Invalid authentication")
        return
    await manager.connect(websocket)
    redis_client = redis_asyncio.from_url(get_settings().celery_broker_url, decode_responses=True)
    subscriber = redis_client.pubsub()
    await subscriber.subscribe(EVENTS_CHANNEL)
    async def forward_events() -> None:
        while True:
            message = await subscriber.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                try:
                    await websocket.send_json(json.loads(message["data"]))
                except (TypeError, json.JSONDecodeError):
                    continue

    event_task = asyncio.create_task(forward_events())
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)
    finally:
        event_task.cancel()
        await subscriber.aclose()
        await redis_client.aclose()


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict[str, str]:
    connected = database_is_connected()
    return {
        "status": "ok" if connected else "degraded",
        "database": "connected" if connected else "disconnected",
    }

from fastapi.testclient import TestClient
from datetime import timedelta
from uuid import uuid4
from threading import Thread
from time import sleep
from redis import Redis

from app.main import app
from app.db.session import SessionLocal
from app.models import User, UserRole
from app.security import create_token, hash_password
from app.core.config import get_settings
from sqlalchemy import select
from app.models import Store


def test_events_websocket_accepts_connection() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "merchant@smartgrocery.example.com"))
        token = create_token(user, token_type="access", expires_delta=timedelta(minutes=15))
    with client.websocket_connect(f"/ws/events?access_token={token}") as websocket:
        websocket.send_text("ping")


def test_events_websocket_requires_authentication() -> None:
    client = TestClient(app)
    try:
        with client.websocket_connect("/ws/events"):
            raise AssertionError("unauthenticated websocket should be rejected")
    except Exception as exc:
        assert "1008" in str(exc) or exc.__class__.__name__ == "WebSocketDisconnect"


def test_events_websocket_receives_redis_event() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "merchant@smartgrocery.example.com"))
        store_id = str(db.scalar(select(Store.id).where(Store.merchant_id == user.id)))
        token = create_token(user, token_type="access", expires_delta=timedelta(minutes=15))

    def publish() -> None:
        sleep(0.2)
        Redis.from_url(get_settings().celery_broker_url).publish(
            "smartgrocery:events",
            '{"event_type":"test.realtime","payload":{"message":"hello","store_id":"' + store_id + '"}}',
        )

    with client.websocket_connect(f"/ws/events?access_token={token}") as websocket:
        Thread(target=publish, daemon=True).start()
        assert websocket.receive_json() == {"event_type": "test.realtime", "payload": {"message": "hello", "store_id": store_id}}

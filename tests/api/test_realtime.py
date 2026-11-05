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


def test_events_websocket_accepts_connection() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        user = User(email=f"ws-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="WS Merchant", role=UserRole.MERCHANT)
        db.add(user)
        db.commit()
        db.refresh(user)
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
        user = User(email=f"ws-event-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="WS Event", role=UserRole.MERCHANT)
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_token(user, token_type="access", expires_delta=timedelta(minutes=15))

    def publish() -> None:
        sleep(0.2)
        Redis.from_url("redis://localhost:6379/0").publish(
            "smartgrocery:events",
            '{"event_type":"test.realtime","payload":{"message":"hello"}}',
        )

    with client.websocket_connect(f"/ws/events?access_token={token}") as websocket:
        Thread(target=publish, daemon=True).start()
        assert websocket.receive_json() == {"event_type": "test.realtime", "payload": {"message": "hello"}}

from fastapi.testclient import TestClient

from app.main import app


def test_events_websocket_accepts_connection() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws/events") as websocket:
        websocket.send_text("ping")

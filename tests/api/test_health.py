from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_json_status() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["database"] in {"connected", "disconnected"}

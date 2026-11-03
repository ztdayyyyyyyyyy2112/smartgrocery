from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.db.session import SessionLocal
from app.models import User, UserRole

client = TestClient(app)
STORE_ID = "00000000-0000-0000-0000-000000000001"
MILK_ID = "00000000-0000-0000-0000-000000001002"


def _token() -> str:
    email = f"order-{uuid4().hex}@example.com"
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "full_name": "Order Test"})
    assert response.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login.json()["access_token"]


def test_checkout_reserves_stock_and_replays_idempotently() -> None:
    headers = {"Authorization": f"Bearer {_token()}", "Idempotency-Key": f"test-{uuid4().hex}"}
    payload = {"store_id": STORE_ID, "items": [{"product_id": MILK_ID, "quantity": "2"}]}
    first = client.post("/api/v1/orders", json=payload, headers=headers)
    assert first.status_code == 201
    second = client.post("/api/v1/orders", json=payload, headers=headers)
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]

    conflict = client.post("/api/v1/orders", json={**payload, "items": [{"product_id": MILK_ID, "quantity": "3"}]}, headers=headers)
    assert conflict.status_code == 409


def test_checkout_rejects_insufficient_stock() -> None:
    headers = {"Authorization": f"Bearer {_token()}", "Idempotency-Key": f"test-{uuid4().hex}"}
    response = client.post("/api/v1/orders", json={"store_id": STORE_ID, "items": [{"product_id": MILK_ID, "quantity": "9999"}]}, headers=headers)
    assert response.status_code == 409


def test_cancel_releases_reservation() -> None:
    headers = {"Authorization": f"Bearer {_token()}", "Idempotency-Key": f"test-{uuid4().hex}"}
    response = client.post("/api/v1/orders", json={"store_id": STORE_ID, "items": [{"product_id": MILK_ID, "quantity": "1"}]}, headers=headers)
    assert response.status_code == 201
    order_id = response.json()["id"]
    cancelled = client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_merchant_can_fulfil_order() -> None:
    token = _token()
    login_user = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    with SessionLocal.begin() as db:
        user = db.scalar(select(User).where(User.id == login_user["id"]))
        user.role = UserRole.MERCHANT
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": f"test-{uuid4().hex}"}
    created = client.post("/api/v1/orders", json={"store_id": STORE_ID, "items": [{"product_id": MILK_ID, "quantity": "1"}]}, headers=headers)
    assert created.status_code == 201
    fulfilled = client.post(f"/api/v1/orders/{created.json()['id']}/fulfil", headers={"Authorization": f"Bearer {token}"})
    assert fulfilled.status_code == 200
    assert fulfilled.json()["status"] == "fulfilled"


def test_merchant_can_read_inventory_alerts() -> None:
    token = _token()
    user_data = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    with SessionLocal.begin() as db:
        user = db.scalar(select(User).where(User.id == user_data["id"]))
        user.role = UserRole.MERCHANT
    response = client.get("/api/v1/inventory", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert "available" in response.json()[0]

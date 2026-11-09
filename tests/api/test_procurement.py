from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models import User, UserRole

client = TestClient(app)
STORE_ID = "00000000-0000-0000-0000-000000000001"
PRODUCT_ID = "00000000-0000-0000-0000-000000001003"


def merchant_token() -> str:
    email = f"procurement-{uuid4().hex}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "full_name": "Procurement Test"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    token = login.json()["access_token"]
    user_id = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["id"]
    with SessionLocal.begin() as db:
        db.scalar(select(User).where(User.id == user_id)).role = UserRole.MERCHANT
    return token


def test_purchase_order_lifecycle_and_receiving() -> None:
    headers = {"Authorization": f"Bearer {merchant_token()}"}
    supplier = client.post("/api/v1/suppliers", json={"name": f"Supplier {uuid4().hex[:6]}", "lead_time_days": 2}, headers=headers)
    assert supplier.status_code == 201
    po = client.post("/api/v1/purchase-orders", json={"store_id": STORE_ID, "supplier_id": supplier.json()["id"], "items": [{"product_id": PRODUCT_ID, "quantity": "4", "unit_cost": "12000"}]}, headers=headers)
    assert po.status_code == 201
    po_id = po.json()["id"]
    assert client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=headers).json()["status"] == "approved"
    assert client.post(f"/api/v1/purchase-orders/{po_id}/send", headers=headers).json()["status"] == "sent"
    received = client.post(f"/api/v1/purchase-orders/{po_id}/receive", json={"items": [{"product_id": PRODUCT_ID, "quantity": "4", "lot_code": f"LOT-{uuid4().hex}", "expiry_date": (date.today() + timedelta(days=30)).isoformat(), "unit_cost": "12000"}]}, headers=headers)
    assert received.status_code == 200
    assert received.json()["status"] == "received"


def test_supplier_product_and_partial_receiving() -> None:
    headers = {"Authorization": f"Bearer {merchant_token()}"}
    supplier = client.post("/api/v1/suppliers", json={"name": f"Partial Supplier {uuid4().hex[:6]}"}, headers=headers).json()
    supplier_product = client.put(f"/api/v1/suppliers/{supplier['id']}/products", json={"product_id": PRODUCT_ID, "unit_cost": "11000", "min_order_qty": "2"}, headers=headers)
    assert supplier_product.status_code == 200
    assert len(client.get(f"/api/v1/suppliers/{supplier['id']}/products", headers=headers).json()) == 1
    po = client.post("/api/v1/purchase-orders", json={"store_id": STORE_ID, "supplier_id": supplier["id"], "items": [{"product_id": PRODUCT_ID, "quantity": "5", "unit_cost": "11000"}]}, headers=headers).json()
    po_id = po["id"]
    client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=headers)
    client.post(f"/api/v1/purchase-orders/{po_id}/send", headers=headers)
    partial = client.post(f"/api/v1/purchase-orders/{po_id}/receive", json={"items": [{"product_id": PRODUCT_ID, "quantity": "2", "lot_code": f"PARTIAL-{uuid4().hex}", "unit_cost": "11000"}]}, headers=headers)
    assert partial.status_code == 200
    assert partial.json()["status"] == "partially_received"


def test_cancel_purchase_order() -> None:
    headers = {"Authorization": f"Bearer {merchant_token()}"}
    supplier = client.post("/api/v1/suppliers", json={"name": f"Cancel Supplier {uuid4().hex[:6]}"}, headers=headers).json()
    po = client.post("/api/v1/purchase-orders", json={"store_id": STORE_ID, "supplier_id": supplier["id"], "items": [{"product_id": PRODUCT_ID, "quantity": "1", "unit_cost": "10000"}]}, headers=headers).json()
    cancelled = client.post(f"/api/v1/purchase-orders/{po['id']}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_customer_cannot_access_procurement() -> None:
    email = f"customer-procurement-{uuid4().hex}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "full_name": "Customer"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    response = client.get("/api/v1/suppliers", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_purchase_order_invalid_transition_is_rejected() -> None:
    headers = {"Authorization": f"Bearer {merchant_token()}"}
    supplier = client.post("/api/v1/suppliers", json={"name": f"State Supplier {uuid4().hex[:6]}"}, headers=headers).json()
    po = client.post("/api/v1/purchase-orders", json={"store_id": STORE_ID, "supplier_id": supplier["id"], "items": [{"product_id": PRODUCT_ID, "quantity": "1", "unit_cost": "10000"}]}, headers=headers).json()
    invalid_send = client.post(f"/api/v1/purchase-orders/{po['id']}/send", headers=headers)
    assert invalid_send.status_code == 409

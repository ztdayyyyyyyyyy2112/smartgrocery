from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models import Product, Store


def _customer(client: TestClient) -> dict:
    email = f"cart-{uuid4().hex}@example.com"
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "password123",
        "full_name": "Cart Customer", "phone": "0900000000", "default_address": "1 Demo Street", "privacy_consent": True})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_cart_is_persisted_per_customer_and_cleared_on_checkout() -> None:
    with SessionLocal() as db:
        store = db.scalar(select(Store).where(Store.code == "S001"))
        product = db.scalar(select(Product).where(Product.sku == "SKU001"))
        store_id, product_id = str(store.id), str(product.id)
    with TestClient(app) as client:
        first = _customer(client)
        second = _customer(client)
        payload = {"store_id": store_id, "items": [{"product_id": product_id, "quantity": 1}]}
        saved = client.put("/api/v1/cart", headers=first, json=payload)
        assert saved.status_code == 200, saved.text
        assert len(client.get("/api/v1/cart", headers=first).json()["items"]) == 1
        assert client.get("/api/v1/cart", headers=second).json()["items"] == []
        order = client.post("/api/v1/orders", headers={**first, "Idempotency-Key": str(uuid4())},
            json={"store_id": store_id, "items": payload["items"]})
        assert order.status_code == 201, order.text
        assert client.get("/api/v1/cart", headers=first).json()["items"] == []


def test_cart_rejects_unavailable_quantity_at_selected_store() -> None:
    with SessionLocal() as db:
        store = db.scalar(select(Store).where(Store.code == "S002"))
        product = db.scalar(select(Product).where(Product.sku == "SKU001"))
        store_id, product_id = str(store.id), str(product.id)
    with TestClient(app) as client:
        headers = _customer(client)
        response = client.put("/api/v1/cart", headers=headers, json={"store_id": store_id,
            "items": [{"product_id": product_id, "quantity": 999}]})
        assert response.status_code == 409

from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models import Product, Store, Supplier, SupplierProduct, User, UserRole
from app.security import create_token, hash_password

client = TestClient(app)


def test_checkout_to_forecast_to_receiving_flow() -> None:
    store_id, product_id = _catalog_ids()
    merchant_token = _merchant_token()
    customer_token = _customer_token()

    checkout = client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {customer_token}", "Idempotency-Key": f"e2e-{uuid4().hex}"},
        json={"store_id": str(store_id), "items": [{"product_id": str(product_id), "quantity": "1"}]},
    )
    assert checkout.status_code == 201
    inventory = client.get("/api/v1/inventory", headers={"Authorization": f"Bearer {merchant_token}"})
    assert inventory.status_code == 200

    job = client.post("/api/v1/jobs/forecasts", headers={"Authorization": f"Bearer {merchant_token}"}, json={"store_id": str(store_id)}).json()
    supplier_id = _supplier_id(product_id)
    result = client.post(
        f"/api/v1/jobs/{job['job_id']}/result",
        headers={"Authorization": f"Bearer {merchant_token}"},
        json={"status": "succeeded", "model_name": "seasonal_naive", "model_version": "e2e", "forecasts": [{"product_id": str(product_id), "target_date": "2026-11-10", "predicted_qty": 10}], "recommendations": [{"product_id": str(product_id), "suggested_qty": 2, "safety_stock": 1, "reorder_point": 2, "meu_score": 0.8, "reason": "E2E replenishment"}]},
    )
    assert result.status_code == 200
    recommendations = client.get("/api/v1/recommendations", headers={"Authorization": f"Bearer {merchant_token}"}).json()
    recommendation = next(item for item in recommendations if item["reason"] == "E2E replenishment")
    approved = client.post(f"/api/v1/recommendations/{recommendation['id']}/approve", headers={"Authorization": f"Bearer {merchant_token}"}, json={"convert_to_po": True, "supplier_id": str(supplier_id)})
    assert approved.status_code == 200
    po_id = approved.json()["purchase_order_id"]
    assert client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers={"Authorization": f"Bearer {merchant_token}"}).status_code == 200
    assert client.post(f"/api/v1/purchase-orders/{po_id}/send", headers={"Authorization": f"Bearer {merchant_token}"}).status_code == 200
    received = client.post(f"/api/v1/purchase-orders/{po_id}/receive", headers={"Authorization": f"Bearer {merchant_token}"}, json={"items": [{"product_id": str(product_id), "quantity": "2", "lot_code": f"E2E-{uuid4().hex}", "unit_cost": "12000"}]})
    assert received.status_code == 200
    assert received.json()["status"] == "received"


def _catalog_ids():
    with SessionLocal() as db:
        store = db.scalar(select(Store).limit(1))
        product = db.scalar(select(Product).limit(1))
        assert store is not None and product is not None
        return store.id, product.id


def _merchant_token() -> str:
    with SessionLocal() as db:
        user = User(email=f"e2e-merchant-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="E2E Merchant", role=UserRole.MERCHANT)
        db.add(user)
        db.commit()
        db.refresh(user)
        return create_token(user, token_type="access", expires_delta=timedelta(minutes=15))


def _customer_token() -> str:
    with SessionLocal() as db:
        user = User(email=f"e2e-customer-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="E2E Customer", role=UserRole.CUSTOMER)
        db.add(user)
        db.commit()
        db.refresh(user)
        return create_token(user, token_type="access", expires_delta=timedelta(minutes=15))


def _supplier_id(product_id):
    with SessionLocal() as db:
        supplier = Supplier(name=f"E2E Supplier {uuid4().hex[:6]}")
        db.add(supplier)
        db.flush()
        db.add(SupplierProduct(supplier_id=supplier.id, product_id=product_id, unit_cost=12000))
        db.commit()
        return supplier.id

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models import InventoryBatch, Product, Store, User, UserRole
from app.security import create_token, hash_password

client = TestClient(app)


def test_expired_batch_is_not_available_in_catalog() -> None:
    with SessionLocal() as db:
        store = db.scalar(select(Store).limit(1))
        product = Product(sku=f"EXPIRED-{uuid4().hex[:8]}", name="Expired Edge SKU", unit="unit", selling_price=Decimal("1000"), is_perishable=True)
        db.add(product)
        db.flush()
        db.add(InventoryBatch(store_id=store.id, product_id=product.id, lot_code=f"EX-{uuid4().hex}", quantity_on_hand=10, expiry_date=date.today() - timedelta(days=1)))
        db.commit()
        product_id = product.id
    response = client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    assert Decimal(response.json()["available_qty"]) == Decimal("0")


def test_sparse_sku_without_inventory_returns_zero_available() -> None:
    with SessionLocal() as db:
        product = Product(sku=f"SPARSE-{uuid4().hex[:8]}", name="Sparse Edge SKU", unit="unit", selling_price=Decimal("1000"), is_perishable=False)
        db.add(product)
        db.commit()
        product_id = product.id
    response = client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    assert Decimal(response.json()["available_qty"]) == Decimal("0")


def test_zero_demand_forecast_is_stored_without_fake_recommendation() -> None:
    with SessionLocal() as db:
        store = db.scalar(select(Store).limit(1))
        product = db.scalar(select(Product).limit(1))
        assert store is not None and product is not None
        store_id, product_id = store.id, product.id
        user = User(email=f"edge-forecast-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="Edge Merchant", role=UserRole.MERCHANT)
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_token(user, token_type="access", expires_delta=timedelta(minutes=15))
    headers = {"Authorization": f"Bearer {token}"}
    job_id = client.post("/api/v1/jobs/forecasts", headers=headers, json={"store_id": str(store_id)}).json()["job_id"]
    response = client.post(f"/api/v1/jobs/{job_id}/result", headers=headers, json={"status": "succeeded", "model_name": "seasonal_naive", "model_version": "edge", "forecasts": [{"product_id": str(product_id), "target_date": str(date.today()), "predicted_qty": 0}], "recommendations": []})
    assert response.status_code == 200
    assert response.json()["recommendation_count"] == 0

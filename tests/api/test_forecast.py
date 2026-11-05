from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models import ReplenishmentRecommendation, RecommendationStatus, Store, Supplier, SupplierProduct, User, UserRole
from app.security import create_token, hash_password

client = TestClient(app)


def test_forecast_job_requires_merchant_role() -> None:
    email = f"forecast-customer-{uuid4()}@example.com"
    register = client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "full_name": "Forecast Customer"})
    assert register.status_code == 201
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    store_id = str(_store_id())
    response = client.post("/api/v1/jobs/forecasts", headers={"Authorization": f"Bearer {token}"}, json={"store_id": store_id})
    assert response.status_code == 403


def test_merchant_can_queue_and_poll_forecast_job() -> None:
    with SessionLocal() as db:
        merchant = User(email=f"forecast-merchant-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="Forecast Merchant", role=UserRole.MERCHANT)
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        token = create_token(merchant, token_type="access", expires_delta=__import__("datetime").timedelta(minutes=15))
    response = client.post("/api/v1/jobs/forecasts", headers={"Authorization": f"Bearer {token}"}, json={"store_id": str(_store_id()), "horizon_days": 7})
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert response.json()["status"] == "queued"
    poll = client.get(f"/api/v1/jobs/{job_id}", headers={"Authorization": f"Bearer {token}"})
    assert poll.status_code == 200
    assert poll.json()["status"] == "queued"


def test_forecast_job_result_success_and_failure() -> None:
    with SessionLocal() as db:
        merchant = User(email=f"forecast-result-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="Forecast Result", role=UserRole.MERCHANT)
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        token = create_token(merchant, token_type="access", expires_delta=__import__("datetime").timedelta(minutes=15))
    headers = {"Authorization": f"Bearer {token}"}
    store_id = str(_store_id())
    product_id = _product_id()
    success_job = client.post("/api/v1/jobs/forecasts", headers=headers, json={"store_id": store_id}).json()["job_id"]
    result = client.post(f"/api/v1/jobs/{success_job}/result", headers=headers, json={"status": "succeeded", "model_name": "seasonal_naive", "model_version": "test", "forecasts": [{"product_id": product_id, "target_date": "2026-11-06", "predicted_qty": 10}], "recommendations": []})
    assert result.status_code == 200
    assert result.json()["status"] == "succeeded"
    failed_job = client.post("/api/v1/jobs/forecasts", headers=headers, json={"store_id": store_id}).json()["job_id"]
    failed = client.post(f"/api/v1/jobs/{failed_job}/result", headers=headers, json={"status": "failed", "error_message": "inference unavailable"})
    assert failed.status_code == 200
    assert failed.json()["status"] == "failed"


def test_recommendation_can_convert_to_purchase_order() -> None:
    with SessionLocal() as db:
        merchant = User(email=f"forecast-convert-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="Forecast Convert", role=UserRole.MERCHANT)
        db.add(merchant)
        db.flush()
        store_id = _store_id()
        product_id = _product_id()
        supplier = Supplier(name=f"Forecast Supplier {uuid4().hex[:6]}")
        db.add(supplier)
        db.flush()
        db.add(SupplierProduct(supplier_id=supplier.id, product_id=product_id, unit_cost=12000))
        from app.models import ForecastJob
        job = ForecastJob(store_id=store_id, created_by=merchant.id, horizon_days=7, as_of="2026-11-05")
        db.add(job)
        db.flush()
        recommendation = ReplenishmentRecommendation(job_id=job.id, store_id=store_id, product_id=product_id, suggested_qty=5, safety_stock=1, reorder_point=2, reason="test", status=RecommendationStatus.PENDING)
        db.add(recommendation)
        db.commit()
        token = create_token(merchant, token_type="access", expires_delta=__import__("datetime").timedelta(minutes=15))
        recommendation_id = str(recommendation.id)
        supplier_id = str(supplier.id)
    response = client.post(f"/api/v1/recommendations/{recommendation_id}/approve", headers={"Authorization": f"Bearer {token}"}, json={"convert_to_po": True, "supplier_id": supplier_id})
    assert response.status_code == 200
    assert response.json()["status"] == "converted"
    assert response.json()["purchase_order_id"]


def _store_id():
    with SessionLocal() as db:
        store = db.scalar(select(Store).limit(1))
        assert store is not None
        return store.id


def _product_id():
    from app.models import Product
    with SessionLocal() as db:
        product = db.scalar(select(Product).limit(1))
        assert product is not None
        return str(product.id)

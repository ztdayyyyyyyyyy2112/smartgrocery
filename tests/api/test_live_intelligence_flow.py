"""Exercise the real backend job/PO path with a deterministic AI response."""
from datetime import date, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models import (DemandForecast, ForecastJob, ForecastJobStatus, Product,
                        ReplenishmentRecommendation, Store, Supplier, User)
from app.security import create_token
from app.worker import run_forecast_job


def test_ai_job_to_purchase_order_receiving(monkeypatch):
    with SessionLocal() as db:
        store = db.scalar(select(Store).where(Store.code == "S001"))
        product = db.scalar(select(Product).where(Product.sku == "SKU005"))
        supplier = db.scalar(select(Supplier).where(Supplier.name == "SmartGrocery Demo Supplier"))
        merchant = db.scalar(select(User).where(User.email == "merchant@smartgrocery.example.com"))
        customer = db.scalar(select(User).where(User.email == "customer@smartgrocery.example.com"))
        assert all([store, product, supplier, merchant, customer])
        store_id, product_id, supplier_id = store.id, product.id, supplier.id
        merchant_token = create_token(merchant, token_type="access", expires_delta=timedelta(minutes=15))
        customer_token = create_token(customer, token_type="access", expires_delta=timedelta(minutes=15))

    client = TestClient(app)
    customer_headers = {"Authorization": f"Bearer {customer_token}", "Idempotency-Key": f"ai-demo-{uuid4()}"}
    checkout = client.post("/api/v1/orders", headers=customer_headers,
                           json={"store_id": str(store_id), "items": [{"product_id": str(product_id), "quantity": 1}]})
    assert checkout.status_code == 201, checkout.text
    merchant_headers = {"Authorization": f"Bearer {merchant_token}"}
    job_response = client.post("/api/v1/jobs/forecasts", headers=merchant_headers,
                               json={"store_id": str(store_id), "horizon_days": 7})
    assert job_response.status_code == 202, job_response.text
    job_id = job_response.json()["job_id"]
    as_of = date.today() - timedelta(days=1)

    def fake_ai(requests):
        target = next(item for item in requests if item["sku_id"] == "SKU005")
        assert target["store_id"] == "S001"
        assert target["inventory"]["reserved"] >= 1
        return [{"store_id": "S001", "sku_id": "SKU005", "as_of_date": as_of.isoformat(),
                 "model_version": "test-lightgbm", "status": "REORDER_RECOMMENDED",
                 "forecast": [{"date": (as_of + timedelta(days=i)).isoformat(),
                               "predicted_demand": 3} for i in range(1, 8)],
                 "suggested_order_qty": 10, "safety_stock": 2, "reorder_point": 8,
                 "explanation": "Low inventory after checkout"}]

    monkeypatch.setattr("app.intelligence.fetch_batch", fake_ai)
    result = run_forecast_job.run(job_id)
    assert result["status"] == "succeeded", result
    with SessionLocal() as db:
        job = db.get(ForecastJob, UUID(job_id))
        assert job.status == ForecastJobStatus.SUCCEEDED
        assert job.as_of == as_of
        assert len(db.scalars(select(DemandForecast).where(DemandForecast.job_id == job.id)).all()) == 7
        rec = db.scalar(select(ReplenishmentRecommendation).where(ReplenishmentRecommendation.job_id == job.id))
        assert rec.product_id == product_id
        rec_id = rec.id

    approved = client.post(f"/api/v1/recommendations/{rec_id}/approve", headers=merchant_headers,
                           json={"convert_to_po": True, "supplier_id": str(supplier_id)})
    assert approved.status_code == 200, approved.text
    po_id = approved.json()["purchase_order_id"]
    assert client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=merchant_headers).status_code == 200
    assert client.post(f"/api/v1/purchase-orders/{po_id}/send", headers=merchant_headers).status_code == 200
    received = client.post(f"/api/v1/purchase-orders/{po_id}/receive", headers=merchant_headers,
                           json={"items": [{"product_id": str(product_id), "quantity": 10,
                                            "unit_cost": 10000, "lot_code": f"AI-{uuid4()}"}]})
    assert received.status_code == 200, received.text
    stock = client.get(f"/api/v1/inventory?store_id={store_id}&product_id={product_id}", headers=merchant_headers)
    assert stock.status_code == 200
    assert float(stock.json()[0]["on_hand"]) >= 12

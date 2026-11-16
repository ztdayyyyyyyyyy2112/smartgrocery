"""Smoke test the full HTTP/worker/AI procurement demo after docker compose up."""
import json
import time
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://localhost:8000/api/v1"


def call(path, method="GET", body=None, token=None, idempotency=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if idempotency:
        headers["Idempotency-Key"] = idempotency
    request = Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                      headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {exc.read().decode()}") from exc


def main():
    for attempt in range(20):
        try:
            with urlopen("http://localhost:3000", timeout=5) as response:
                assert response.status == 200 and b"SmartGrocery" in response.read()
            break
        except Exception:
            if attempt == 19:
                raise RuntimeError("Web app did not become available on localhost:3000")
            time.sleep(1)
    password = "DemoPass123!"
    customer = call("/auth/login", "POST", {"email": "customer@smartgrocery.example.com", "password": password})["access_token"]
    merchant = call("/auth/login", "POST", {"email": "merchant@smartgrocery.example.com", "password": password})["access_token"]
    store = next(item for item in call("/stores") if item["code"] == "S001")
    product = next(item for item in call("/products?page_size=100")["items"] if item["sku"] == "SKU005")
    stock_before = next(item for item in call(f"/inventory?store_id={store['id']}", token=merchant) if item["sku"] == "SKU005")
    order = call("/orders", "POST", {"store_id": store["id"], "recipient_name": "Demo Customer",
                 "delivery_phone": "0900000000", "delivery_address": "1 Demo Street, Ho Chi Minh City",
                 "items": [{"product_id": product["id"], "quantity": 1}]},
                 customer, str(uuid.uuid4()))
    assert order["status"] == "confirmed"
    stock_reserved = next(item for item in call(f"/inventory?store_id={store['id']}", token=merchant) if item["sku"] == "SKU005")
    assert float(stock_reserved["available"]) < float(stock_before["available"])
    job = call("/jobs/forecasts", "POST", {"store_id": store["id"], "horizon_days": 7}, merchant)
    for _ in range(90):
        state = call(f"/jobs/{job['job_id']}", token=merchant)
        if state["status"] in {"succeeded", "failed"}:
            break
        time.sleep(2)
    assert state["status"] == "succeeded", state
    forecast = call(f"/forecasts?store_id={store['id']}&product_id={product['id']}", token=merchant)
    assert len(forecast) >= 7
    recommendation = next(item for item in call(f"/recommendations?store_id={store['id']}", token=merchant)
                          if item["status"] == "pending")
    replenishment_before = next(item for item in call(f"/inventory?store_id={store['id']}", token=merchant)
                                if item["product_id"] == recommendation["product_id"])
    supplier = next(item for item in call("/suppliers", token=merchant) if item["name"] == "SmartGrocery Demo Supplier")
    po_id = call(f"/recommendations/{recommendation['id']}/approve", "POST",
                 {"convert_to_po": True, "supplier_id": supplier["id"]}, merchant)["purchase_order_id"]
    call(f"/purchase-orders/{po_id}/approve", "POST", token=merchant)
    call(f"/purchase-orders/{po_id}/send", "POST", token=merchant)
    po = call(f"/purchase-orders/{po_id}", token=merchant)
    line = po["items"][0]
    receipt = call(f"/purchase-orders/{po_id}/receive", "POST", {"items": [{"product_id": line["product_id"],
                   "quantity": line["quantity_ordered"], "unit_cost": line["unit_cost"],
                   "lot_code": f"SMOKE-{uuid.uuid4().hex}"}]}, merchant)
    assert receipt["status"] == "received"
    replenishment_after = next(item for item in call(f"/inventory?store_id={store['id']}", token=merchant)
                               if item["product_id"] == recommendation["product_id"])
    assert float(replenishment_after["on_hand"]) > float(replenishment_before["on_hand"])
    print("DEMO PASS: checkout -> reserved stock -> AI job -> recommendation -> PO -> receiving -> increased stock")


if __name__ == "__main__":
    main()

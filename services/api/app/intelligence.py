"""Bridge the business catalog and stock records to the standalone AI service."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (InventoryBatch, Product, PurchaseOrder, PurchaseOrderItem,
                        PurchaseOrderStatus, Store)


def build_batch(db: Session, store: Store, horizon: int) -> tuple[list[dict], dict[str, UUID]]:
    today = date.today()
    stock: dict[str, dict] = defaultdict(lambda: {"on_hand": Decimal(0), "reserved": Decimal(0)})
    products: dict[str, UUID] = {}
    rows = db.execute(select(InventoryBatch, Product).join(Product, Product.id == InventoryBatch.product_id)
                      .where(InventoryBatch.store_id == store.id)).all()
    for batch, product in rows:
        # The AI dataset has historical observations only for its canonical SKU set.
        if not product.sku.startswith("SKU") or not product.sku[3:].isdigit():
            continue
        products[product.sku] = product.id
        if batch.status.value == "available" and (batch.expiry_date is None or batch.expiry_date >= today):
            stock[product.sku]["on_hand"] += batch.quantity_on_hand
            stock[product.sku]["reserved"] += batch.quantity_reserved
    on_order: dict[UUID, Decimal] = defaultdict(lambda: Decimal(0))
    for item in db.scalars(select(PurchaseOrderItem).join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.purchase_order_id)
                           .where(PurchaseOrder.store_id == store.id,
                                  PurchaseOrder.status.in_([PurchaseOrderStatus.SENT,
                                                            PurchaseOrderStatus.PARTIALLY_RECEIVED]))).all():
        on_order[item.product_id] += item.quantity_ordered - item.quantity_received
    requests = []
    for sku, product_id in sorted(products.items()):
        values = stock[sku]
        requests.append({"store_id": store.code, "sku_id": sku, "forecast_horizon": horizon,
                         "inventory": {"on_hand": float(values["on_hand"]),
                                       "reserved": float(values["reserved"]),
                                       "on_order": float(on_order[product_id])}})
    return requests, products


def fetch_batch(items: list[dict]) -> list[dict]:
    if not items:
        raise ValueError("No AI catalog products in this store")
    with httpx.Client(base_url=get_settings().intelligence_url, timeout=90) as client:
        response = client.post("/forecast/replenishment/batch", json={"items": items})
        response.raise_for_status()
        result = response.json()
    if result.get("count") != len(items) or len(result.get("items", [])) != len(items):
        raise ValueError("AI batch response count mismatch")
    failures = [item for item in result["items"] if not item.get("ok")]
    if failures:
        raise ValueError(f"AI returned {len(failures)} failed Store/SKU results: "
                         f"{failures[0].get('error_code', 'UNKNOWN')}")
    return [item["result"] for item in result["items"]]


def to_forecast_result(results: list[dict], product_ids: dict[str, UUID], store_code: str) -> tuple[date, dict]:
    """Validate AI identities/dates and prepare the existing backend result contract."""
    if not results:
        raise ValueError("AI returned no forecasts")
    as_of = date.fromisoformat(results[0]["as_of_date"])
    model_versions = {item["model_version"] for item in results}
    if len(model_versions) != 1:
        raise ValueError("Mixed AI model versions in one job")
    forecasts, recommendations = [], []
    for item in results:
        sku = item["sku_id"]
        if item.get("store_id") != store_code or sku not in product_ids or date.fromisoformat(item["as_of_date"]) != as_of:
            raise ValueError("AI Store/SKU or as_of does not match this job")
        product_id = product_ids[sku]
        for point in item["forecast"]:
            if point["predicted_demand"] is None:
                continue
            forecasts.append({"product_id": product_id, "target_date": point["date"],
                              "predicted_qty": point["predicted_demand"]})
        if item["status"] == "REORDER_RECOMMENDED" and (item.get("suggested_order_qty") or 0) > 0:
            recommendations.append({"product_id": product_id, "suggested_qty": item["suggested_order_qty"],
                                    "safety_stock": item["safety_stock"], "reorder_point": item["reorder_point"],
                                    "meu_score": None, "reason": item["explanation"]})
    return as_of, {"status": "succeeded", "model_name": "smartgrocery-intelligence",
                   "model_version": next(iter(model_versions)), "forecasts": forecasts,
                   "recommendations": recommendations}

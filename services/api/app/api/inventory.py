from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import InventoryBatch, Product, Store, UserRole
from app.rules.inventory import inventory_alerts
from app.security import require_roles

router = APIRouter(prefix="/inventory", tags=["inventory"])


class InventoryResponse(BaseModel):
    store_id: UUID
    product_id: UUID
    sku: str
    name: str
    on_hand: Decimal
    reserved: Decimal
    available: Decimal
    nearest_expiry: date | None
    alerts: list[str]


@router.get("", response_model=list[InventoryResponse])
def inventory(
    store_id: UUID | None = None,
    product_id: UUID | None = None,
    low_stock_only: bool = False,
    low_stock_threshold: Decimal = Query(default=Decimal("5"), ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.MERCHANT, UserRole.ADMIN)),
) -> list[InventoryResponse]:
    stmt = select(InventoryBatch, Product).join(Product, Product.id == InventoryBatch.product_id).join(Store, Store.id == InventoryBatch.store_id)
    if store_id:
        stmt = stmt.where(InventoryBatch.store_id == store_id)
    if product_id:
        stmt = stmt.where(InventoryBatch.product_id == product_id)
    grouped: dict[tuple[UUID, UUID], dict] = {}
    for batch, product in db.execute(stmt).all():
        key = (batch.store_id, batch.product_id)
        row = grouped.setdefault(key, {"store_id": batch.store_id, "product_id": batch.product_id, "sku": product.sku, "name": product.name, "on_hand": Decimal("0"), "reserved": Decimal("0"), "nearest_expiry": None})
        sellable = batch.status.value == "available" and (batch.expiry_date is None or batch.expiry_date >= date.today())
        if sellable:
            row["on_hand"] += batch.quantity_on_hand
            row["reserved"] += batch.quantity_reserved
            if batch.expiry_date and (row["nearest_expiry"] is None or batch.expiry_date < row["nearest_expiry"]):
                row["nearest_expiry"] = batch.expiry_date
    result = []
    for row in grouped.values():
        row["available"] = row["on_hand"] - row["reserved"]
        row["alerts"] = inventory_alerts(available=row["available"], nearest_expiry=row["nearest_expiry"], low_stock_threshold=low_stock_threshold)
        if not low_stock_only or "LOW_STOCK_ALERT" in row["alerts"]:
            result.append(InventoryResponse(**row))
    return result

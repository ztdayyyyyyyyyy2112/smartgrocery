from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.events import enqueue_event
from app.models import GoodsReceipt, InventoryBatch, Product, PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus, StockEventType, StockLedgerEntry, Supplier, SupplierProduct, UserRole
from app.security import require_roles

router = APIRouter(tags=["procurement"])
merchant_admin = require_roles(UserRole.MERCHANT, UserRole.ADMIN)


class SupplierRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_email: str | None = None
    contact_phone: str | None = None
    lead_time_days: int = Field(default=2, ge=0)


class SupplierResponse(BaseModel):
    id: UUID
    name: str
    contact_email: str | None
    contact_phone: str | None
    lead_time_days: int
    is_active: bool

    model_config = {"from_attributes": True}


class POItemRequest(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)


class PORequest(BaseModel):
    store_id: UUID
    supplier_id: UUID
    items: list[POItemRequest] = Field(min_length=1)
    notes: str | None = None


class ReceiveItemRequest(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    lot_code: str = Field(min_length=1)
    expiry_date: date | None = None
    unit_cost: Decimal = Field(ge=0)


class ReceiveRequest(BaseModel):
    items: list[ReceiveItemRequest] = Field(min_length=1)


class SupplierProductRequest(BaseModel):
    product_id: UUID
    supplier_sku: str | None = None
    unit_cost: Decimal = Field(ge=0)
    min_order_qty: Decimal = Field(default=Decimal("1"), gt=0)


@router.get("/suppliers", response_model=list[SupplierResponse])
def list_suppliers(db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> list[SupplierResponse]:
    return list(db.scalars(select(Supplier).where(Supplier.is_active.is_(True)).order_by(Supplier.name)).all())


@router.post("/suppliers", status_code=201, response_model=SupplierResponse)
def create_supplier(payload: SupplierRequest, db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> SupplierResponse:
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/suppliers/{supplier_id}/products")
def upsert_supplier_product(supplier_id: UUID, payload: SupplierProductRequest, db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> dict:
    if db.get(Supplier, supplier_id) is None or db.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=404, detail="Supplier or product not found")
    item = db.get(SupplierProduct, (supplier_id, payload.product_id))
    if item is None:
        item = SupplierProduct(supplier_id=supplier_id, **payload.model_dump())
        db.add(item)
    else:
        item.supplier_sku = payload.supplier_sku
        item.unit_cost = payload.unit_cost
        item.min_order_qty = payload.min_order_qty
    db.commit()
    return {"supplier_id": str(supplier_id), "product_id": str(payload.product_id), "unit_cost": str(item.unit_cost), "min_order_qty": str(item.min_order_qty)}


@router.get("/suppliers/{supplier_id}/products")
def list_supplier_products(supplier_id: UUID, db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> list[dict]:
    if db.get(Supplier, supplier_id) is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    items = db.scalars(select(SupplierProduct).where(SupplierProduct.supplier_id == supplier_id)).all()
    return [{"supplier_id": str(item.supplier_id), "product_id": str(item.product_id), "supplier_sku": item.supplier_sku, "unit_cost": str(item.unit_cost), "min_order_qty": str(item.min_order_qty)} for item in items]


@router.post("/purchase-orders", status_code=201)
def create_purchase_order(payload: PORequest, db: Session = Depends(get_db), user=Depends(merchant_admin)) -> dict:
    db.rollback()
    with db.begin():
        if db.get(Supplier, payload.supplier_id) is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        po = PurchaseOrder(store_id=payload.store_id, supplier_id=payload.supplier_id, created_by=user.id, status=PurchaseOrderStatus.PENDING_APPROVAL, notes=payload.notes)
        db.add(po)
        db.flush()
        for item in payload.items:
            if db.get(Product, item.product_id) is None:
                raise HTTPException(status_code=404, detail="Product not found")
            db.add(PurchaseOrderItem(purchase_order_id=po.id, product_id=item.product_id, quantity_ordered=item.quantity, unit_cost=item.unit_cost))
        response = {"id": str(po.id), "status": po.status.value, "store_id": str(po.store_id), "supplier_id": str(po.supplier_id)}
        enqueue_event(db, event_type="purchase_order.created", aggregate_type="purchase_order", aggregate_id=po.id, payload=response)
        return response


@router.get("/purchase-orders")
def list_purchase_orders(db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> list[dict]:
    orders = db.scalars(select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())).all()
    return [{"id": str(po.id), "status": po.status.value, "store_id": str(po.store_id), "supplier_id": str(po.supplier_id)} for po in orders]


@router.get("/purchase-orders/{po_id}")
def get_purchase_order(po_id: UUID, db: Session = Depends(get_db), _user=Depends(merchant_admin)) -> dict:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    items = db.scalars(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po_id)).all()
    return {"id": str(po.id), "status": po.status.value, "store_id": str(po.store_id),
            "supplier_id": str(po.supplier_id), "items": [
                {"product_id": str(item.product_id), "quantity_ordered": str(item.quantity_ordered),
                 "quantity_received": str(item.quantity_received), "unit_cost": str(item.unit_cost)}
                for item in items]}


def _transition(po_id: UUID, expected: PurchaseOrderStatus, target: PurchaseOrderStatus, db: Session, user, *, approval: bool = False) -> dict:
    db.rollback()
    with db.begin():
        po = db.scalar(select(PurchaseOrder).where(PurchaseOrder.id == po_id).with_for_update())
        if po is None:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        if po.status != expected:
            raise HTTPException(status_code=409, detail="Invalid purchase order state")
        po.status = target
        if approval:
            po.approved_by = user.id
        response = {"id": str(po.id), "status": po.status.value}
        enqueue_event(db, event_type=f"purchase_order.{target.value}", aggregate_type="purchase_order", aggregate_id=po.id, payload=response)
        return response


@router.post("/purchase-orders/{po_id}/approve")
def approve_purchase_order(po_id: UUID, db: Session = Depends(get_db), user=Depends(merchant_admin)) -> dict:
    return _transition(po_id, PurchaseOrderStatus.PENDING_APPROVAL, PurchaseOrderStatus.APPROVED, db, user, approval=True)


@router.post("/purchase-orders/{po_id}/send")
def send_purchase_order(po_id: UUID, db: Session = Depends(get_db), user=Depends(merchant_admin)) -> dict:
    return _transition(po_id, PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.SENT, db, user)


@router.post("/purchase-orders/{po_id}/cancel")
def cancel_purchase_order(po_id: UUID, db: Session = Depends(get_db), user=Depends(merchant_admin)) -> dict:
    db.rollback()
    with db.begin():
        po = db.scalar(select(PurchaseOrder).where(PurchaseOrder.id == po_id).with_for_update())
        if po is None:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        if po.status not in {PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.PENDING_APPROVAL, PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.SENT}:
            raise HTTPException(status_code=409, detail="Purchase order cannot be cancelled")
        po.status = PurchaseOrderStatus.CANCELLED
        response = {"id": str(po.id), "status": po.status.value}
        enqueue_event(db, event_type="purchase_order.cancelled", aggregate_type="purchase_order", aggregate_id=po.id, payload=response)
        return response


@router.post("/purchase-orders/{po_id}/receive")
def receive_purchase_order(po_id: UUID, payload: ReceiveRequest, db: Session = Depends(get_db), user=Depends(merchant_admin)) -> dict:
    db.rollback()
    with db.begin():
        po = db.scalar(select(PurchaseOrder).where(PurchaseOrder.id == po_id).with_for_update())
        if po is None:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        if po.status not in {PurchaseOrderStatus.SENT, PurchaseOrderStatus.PARTIALLY_RECEIVED}:
            raise HTTPException(status_code=409, detail="Purchase order is not receivable")
        items = {item.product_id: item for item in db.scalars(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po.id).with_for_update()).all()}
        receipt = GoodsReceipt(purchase_order_id=po.id, received_by=user.id)
        db.add(receipt)
        db.flush()
        for received in payload.items:
            item = items.get(received.product_id)
            if item is None or item.quantity_received + received.quantity > item.quantity_ordered:
                raise HTTPException(status_code=409, detail="Received quantity exceeds purchase order")
            item.quantity_received += received.quantity
            batch = InventoryBatch(store_id=po.store_id, product_id=received.product_id, lot_code=received.lot_code, quantity_on_hand=received.quantity, expiry_date=received.expiry_date, unit_cost=received.unit_cost)
            db.add(batch)
            db.flush()
            db.add(StockLedgerEntry(store_id=po.store_id, product_id=received.product_id, batch_id=batch.id, event_type=StockEventType.RECEIVE, quantity_delta=received.quantity, reference_type="purchase_order", reference_id=po.id, created_by=user.id))
        po.status = PurchaseOrderStatus.RECEIVED if all(item.quantity_received == item.quantity_ordered for item in items.values()) else PurchaseOrderStatus.PARTIALLY_RECEIVED
        response = {"id": str(po.id), "status": po.status.value, "receipt_id": str(receipt.id)}
        enqueue_event(db, event_type="purchase_order.received", aggregate_type="purchase_order", aggregate_id=po.id, payload=response)
        return response

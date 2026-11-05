import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.events import enqueue_event
from app.models import IdempotencyKey, InventoryBatch, Order, OrderItem, OrderStatus, Product, StockEventType, StockLedgerEntry, StockReservation, UserRole
from app.security import current_user, require_roles

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderLineRequest(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)


class CreateOrderRequest(BaseModel):
    store_id: UUID
    items: list[OrderLineRequest] = Field(min_length=1)


def _order_body(order: Order, items: list[OrderItem]) -> dict:
    return {
        "id": str(order.id),
        "store_id": str(order.store_id),
        "customer_id": str(order.customer_id),
        "status": order.status.value,
        "subtotal": str(order.subtotal),
        "total": str(order.total),
        "currency": order.currency,
        "items": [{"product_id": str(item.product_id), "quantity": str(item.quantity), "unit_price": str(item.unit_price), "line_total": str(item.line_total)} for item in items],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(payload: CreateOrderRequest, idempotency_key: str = Header(..., alias="Idempotency-Key"), db: Session = Depends(get_db), user=Depends(current_user)) -> dict:
    request_hash = hashlib.sha256(json.dumps(payload.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
    existing = db.get(IdempotencyKey, idempotency_key)
    if existing:
        if existing.user_id != user.id or existing.request_hash != request_hash:
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT")
        return existing.response_body
    db.rollback()

    try:
        with db.begin():
            product_ids = [line.product_id for line in payload.items]
            if len(product_ids) != len(set(product_ids)):
                raise HTTPException(status_code=422, detail="Duplicate product_id is not allowed")
            products = {product.id: product for product in db.scalars(select(Product).where(Product.id.in_(product_ids), Product.is_active.is_(True))).all()}
            if len(products) != len(set(product_ids)):
                raise HTTPException(status_code=404, detail="Product not found")

            allocations: list[tuple[OrderLineRequest, Product, list[tuple[InventoryBatch, Decimal]]]] = []
            for line in payload.items:
                batches = list(db.scalars(select(InventoryBatch).where(
                    InventoryBatch.store_id == payload.store_id,
                    InventoryBatch.product_id == line.product_id,
                    InventoryBatch.status == "available",
                    or_(InventoryBatch.expiry_date.is_(None), InventoryBatch.expiry_date >= func.current_date()),
                    InventoryBatch.quantity_on_hand > InventoryBatch.quantity_reserved,
                ).order_by(InventoryBatch.expiry_date.asc().nulls_last(), InventoryBatch.received_at.asc()).with_for_update()).all())
                remaining = line.quantity
                selected = []
                for batch in batches:
                    available = batch.quantity_on_hand - batch.quantity_reserved
                    amount = min(remaining, available)
                    if amount > 0:
                        selected.append((batch, amount))
                        remaining -= amount
                    if remaining <= 0:
                        break
                if remaining > 0:
                    raise HTTPException(status_code=409, detail="STOCK_INSUFFICIENT")
                allocations.append((line, products[line.product_id], selected))

            subtotal = sum((line.quantity * product.selling_price for line, product, _ in allocations), Decimal("0"))
            order = Order(store_id=payload.store_id, customer_id=user.id, status=OrderStatus.CONFIRMED, subtotal=subtotal, total=subtotal, idempotency_key=idempotency_key)
            db.add(order)
            db.flush()
            order_items = []
            for line, product, selected in allocations:
                item = OrderItem(order_id=order.id, product_id=product.id, quantity=line.quantity, unit_price=product.selling_price, line_total=line.quantity * product.selling_price)
                db.add(item)
                db.flush()
                order_items.append(item)
                for batch, amount in selected:
                    batch.quantity_reserved += amount
                    db.add(StockReservation(order_item_id=item.id, batch_id=batch.id, quantity=amount))
                    db.add(StockLedgerEntry(store_id=payload.store_id, product_id=product.id, batch_id=batch.id, event_type=StockEventType.RESERVE, quantity_delta=amount, reference_type="order", reference_id=order.id, created_by=user.id))
            response = _order_body(order, order_items)
            enqueue_event(db, event_type="order.confirmed", aggregate_type="order", aggregate_id=order.id, payload=response)
            db.add(IdempotencyKey(key=idempotency_key, user_id=user.id, request_hash=request_hash, response_code=201, response_body=response, expires_at=datetime.now(timezone.utc) + timedelta(days=7)))
            return response
    except HTTPException:
        raise


def _locked_order(order_id: UUID, db: Session) -> tuple[Order, list[OrderItem]]:
    order = db.scalar(select(Order).where(Order.id == order_id).with_for_update())
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    items = list(db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all())
    return order, items


@router.post("/{order_id}/cancel")
def cancel_order(order_id: UUID, db: Session = Depends(get_db), user=Depends(current_user)) -> dict:
    db.rollback()
    with db.begin():
        order, items = _locked_order(order_id, db)
        if order.customer_id != user.id and user.role.value not in {"merchant", "admin"}:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status not in {OrderStatus.PENDING, OrderStatus.CONFIRMED}:
            raise HTTPException(status_code=409, detail="Order cannot be cancelled")
        for item in items:
            reservations = list(db.scalars(select(StockReservation).where(StockReservation.order_item_id == item.id).with_for_update()).all())
            for reservation in reservations:
                batch = db.scalar(select(InventoryBatch).where(InventoryBatch.id == reservation.batch_id).with_for_update())
                batch.quantity_reserved -= reservation.quantity
                db.add(StockLedgerEntry(store_id=order.store_id, product_id=item.product_id, batch_id=batch.id, event_type=StockEventType.RELEASE, quantity_delta=-reservation.quantity, reference_type="order", reference_id=order.id, created_by=user.id))
        order.status = OrderStatus.CANCELLED
        order.cancelled_reason = "cancelled by user"
        response = _order_body(order, items)
        enqueue_event(db, event_type="order.cancelled", aggregate_type="order", aggregate_id=order.id, payload=response)
        return response


@router.post("/{order_id}/fulfil")
def fulfil_order(order_id: UUID, db: Session = Depends(get_db), user=Depends(require_roles(UserRole.MERCHANT, UserRole.ADMIN))) -> dict:
    db.rollback()
    with db.begin():
        order, items = _locked_order(order_id, db)
        if order.status != OrderStatus.CONFIRMED:
            raise HTTPException(status_code=409, detail="Order cannot be fulfilled")
        for item in items:
            reservations = list(db.scalars(select(StockReservation).where(StockReservation.order_item_id == item.id).with_for_update()).all())
            for reservation in reservations:
                batch = db.scalar(select(InventoryBatch).where(InventoryBatch.id == reservation.batch_id).with_for_update())
                batch.quantity_on_hand -= reservation.quantity
                batch.quantity_reserved -= reservation.quantity
                if batch.quantity_on_hand == 0:
                    batch.status = "depleted"
                db.add(StockLedgerEntry(store_id=order.store_id, product_id=item.product_id, batch_id=batch.id, event_type=StockEventType.FULFIL, quantity_delta=-reservation.quantity, reference_type="order", reference_id=order.id, created_by=user.id))
        order.status = OrderStatus.FULFILLED
        response = _order_body(order, items)
        enqueue_event(db, event_type="order.fulfilled", aggregate_type="order", aggregate_id=order.id, payload=response)
        return response

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.catalog import _product_query, _to_product_response
from app.db.session import get_db
from app.models import Product, ShoppingCartItem, Store, UserRole
from app.security import require_roles

router = APIRouter(prefix="/cart", tags=["cart"])
customer_only = require_roles(UserRole.CUSTOMER)


class CartLine(BaseModel):
    product_id: UUID
    quantity: int = Field(ge=1, le=999)


class ReplaceCart(BaseModel):
    store_id: UUID
    items: list[CartLine] = Field(max_length=100)


def _cart_body(db: Session, user_id: UUID) -> dict:
    lines = list(db.scalars(select(ShoppingCartItem).where(ShoppingCartItem.user_id == user_id).order_by(ShoppingCartItem.product_id)).all())
    if not lines:
        return {"store_id": None, "items": []}
    store_id = lines[0].store_id
    rows = db.execute(_product_query(None, None, store_id).where(Product.id.in_([line.product_id for line in lines]))).all()
    products = {product.id: _to_product_response(product, available).model_dump(mode="json") for product, available in rows}
    return {"store_id": str(store_id), "items": [{"product": products[line.product_id], "quantity": line.quantity} for line in lines if line.product_id in products]}


@router.get("")
def get_cart(db: Session = Depends(get_db), user=Depends(customer_only)) -> dict:
    return _cart_body(db, user.id)


@router.put("")
def replace_cart(payload: ReplaceCart, db: Session = Depends(get_db), user=Depends(customer_only)) -> dict:
    if len({line.product_id for line in payload.items}) != len(payload.items):
        raise HTTPException(status_code=422, detail="Duplicate product")
    store = db.get(Store, payload.store_id)
    if store is None or not store.is_active:
        raise HTTPException(status_code=404, detail="Store not found")
    if payload.items:
        rows = db.execute(_product_query(None, None, payload.store_id).where(Product.id.in_([line.product_id for line in payload.items]))).all()
        availability = {product.id: available for product, available in rows}
        if any(line.product_id not in availability or line.quantity > availability[line.product_id] for line in payload.items):
            raise HTTPException(status_code=409, detail="Product unavailable at selected store")
    db.execute(delete(ShoppingCartItem).where(ShoppingCartItem.user_id == user.id))
    db.add_all(ShoppingCartItem(user_id=user.id, store_id=payload.store_id, product_id=line.product_id, quantity=line.quantity) for line in payload.items)
    db.commit()
    return _cart_body(db, user.id)

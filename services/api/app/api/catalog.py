from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Category, InventoryBatch, Product, Store

router = APIRouter(tags=["catalog"])


@router.get("/stores")
def stores(db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": str(store.id), "code": store.code, "name": store.name}
            for store in db.scalars(select(Store).where(Store.is_active.is_(True)).order_by(Store.code)).all()]


class CategoryResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    image_url: str | None


class ProductResponse(BaseModel):
    id: UUID
    sku: str
    name: str
    unit: str
    selling_price: Decimal
    image_url: str | None
    description: str | None = None
    is_perishable: bool = True
    available_qty: Decimal
    is_active: bool


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    page: int
    page_size: int
    total: int


@router.get("/categories", response_model=list[CategoryResponse])
def categories(db: Session = Depends(get_db)) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)).all())


def _product_query(q: str | None, category_id: UUID | None, store_id: UUID | None = None):
    available = func.coalesce(func.sum(InventoryBatch.quantity_on_hand - InventoryBatch.quantity_reserved), 0)
    stmt = select(Product, available.label("available_qty")).outerjoin(InventoryBatch, (InventoryBatch.product_id == Product.id) & (InventoryBatch.status == "available") & or_(InventoryBatch.expiry_date.is_(None), InventoryBatch.expiry_date >= func.current_date())).where(Product.is_active.is_(True)).group_by(Product.id)
    if store_id:
        stmt = stmt.where(InventoryBatch.store_id == store_id)
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%") | Product.sku.ilike(f"%{q}%"))
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    return stmt


def _to_product_response(product: Product, available_qty: Decimal) -> ProductResponse:
    return ProductResponse.model_validate({**product.__dict__, "available_qty": available_qty})


@router.get("/products", response_model=ProductListResponse)
def products(q: str | None = Query(default=None), category_id: UUID | None = None, store_id: UUID | None = None, page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)) -> ProductListResponse:
    stmt = _product_query(q, category_id, store_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(Product.name).offset((page - 1) * page_size).limit(page_size)).all()
    return ProductListResponse(items=[_to_product_response(product, qty) for product, qty in rows], page=page, page_size=page_size, total=total)


@router.get("/products/{product_id}", response_model=ProductResponse)
def product_detail(product_id: UUID, store_id: UUID | None = None, db: Session = Depends(get_db)) -> ProductResponse:
    row = db.execute(_product_query(None, None, store_id).where(Product.id == product_id)).first()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_product_response(*row)

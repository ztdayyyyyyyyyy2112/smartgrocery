from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Store, User, UserRole


def merchant_store_id(db: Session, user: User) -> UUID | None:
    if user.role == UserRole.ADMIN:
        return None
    store_id = db.scalar(select(Store.id).where(Store.merchant_id == user.id, Store.is_active.is_(True)))
    if store_id is None:
        raise HTTPException(status_code=403, detail="No store assigned to merchant")
    return store_id


def ensure_store_access(db: Session, user: User, store_id: UUID) -> None:
    owned = merchant_store_id(db, user)
    if owned is not None and owned != store_id:
        raise HTTPException(status_code=404, detail="Store resource not found")

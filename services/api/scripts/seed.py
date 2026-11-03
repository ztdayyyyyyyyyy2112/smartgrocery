"""Seed deterministic local catalog and inventory data.

Run from services/api with the project virtualenv:
    python scripts/seed.py
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Category, InventoryBatch, Product, Store

STORE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
CATEGORY_IDS = {
    "fruits": uuid.UUID("00000000-0000-0000-0000-000000000101"),
    "dairy-eggs": uuid.UUID("00000000-0000-0000-0000-000000000102"),
    "vegetables": uuid.UUID("00000000-0000-0000-0000-000000000103"),
}
PRODUCT_IDS = {
    "APL-FUJI-01": uuid.UUID("00000000-0000-0000-0000-000000001001"),
    "MILK-1L-01": uuid.UUID("00000000-0000-0000-0000-000000001002"),
    "VEG-CARROT-01": uuid.UUID("00000000-0000-0000-0000-000000001003"),
}


def seed() -> None:
    with SessionLocal.begin() as db:
        store = db.scalar(select(Store).where(Store.code == "SG-HCM-01"))
        if store is None:
            store = Store(id=STORE_ID, code="SG-HCM-01", name="SmartGrocery HCM Demo", address="Ho Chi Minh City")
            db.add(store)

        categories = [
            ("fruits", "Fruits"),
            ("dairy-eggs", "Dairy & Eggs"),
            ("vegetables", "Vegetables"),
        ]
        for slug, name in categories:
            if db.scalar(select(Category).where(Category.slug == slug)) is None:
                db.add(Category(id=CATEGORY_IDS[slug], slug=slug, name=name))

        products = [
            ("APL-FUJI-01", "Fuji Apple", "kg", Decimal("39000.00"), "fruits", True, 14),
            ("MILK-1L-01", "Fresh Milk 1L", "bottle", Decimal("32000.00"), "dairy-eggs", True, 10),
            ("VEG-CARROT-01", "Carrot", "kg", Decimal("25000.00"), "vegetables", True, 10),
        ]
        for sku, name, unit, price, category, perishable, shelf_life in products:
            if db.scalar(select(Product).where(Product.sku == sku)) is None:
                db.add(Product(
                    id=PRODUCT_IDS[sku], sku=sku, name=name, unit=unit,
                    selling_price=price, category_id=CATEGORY_IDS[category],
                    is_perishable=perishable, default_shelf_life_days=shelf_life,
                ))

        db.flush()
        batches = [
            ("APL-FUJI-01", "LOT-APL-20261029", Decimal("30.000"), date(2026, 11, 12), Decimal("25000.00")),
            ("MILK-1L-01", "LOT-MILK-20261029", Decimal("50.000"), date(2026, 11, 8), Decimal("21000.00")),
            ("VEG-CARROT-01", "LOT-CARROT-20261029", Decimal("25.000"), date(2026, 11, 15), Decimal("14000.00")),
        ]
        for sku, lot_code, quantity, expiry, unit_cost in batches:
            exists = db.scalar(select(InventoryBatch).where(
                InventoryBatch.store_id == STORE_ID,
                InventoryBatch.product_id == PRODUCT_IDS[sku],
                InventoryBatch.lot_code == lot_code,
            ))
            if exists is None:
                db.add(InventoryBatch(
                    store_id=STORE_ID, product_id=PRODUCT_IDS[sku], lot_code=lot_code,
                    quantity_on_hand=quantity, expiry_date=expiry, unit_cost=unit_cost,
                    received_at=datetime.now(timezone.utc),
                ))


if __name__ == "__main__":
    seed()
    print("Seed completed: store, categories, products, and inventory batches.")

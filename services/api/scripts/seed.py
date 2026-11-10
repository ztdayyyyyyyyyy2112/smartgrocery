"""Seed deterministic local catalog and inventory data.

Run from services/api with the project virtualenv:
    python scripts/seed.py
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import csv
import os
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Category, InventoryBatch, Product, Store, Supplier, SupplierProduct, User, UserRole
from app.security import hash_password

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
DEMO_DATA = Path(__file__).resolve().parents[3] / "database" / "demo"
DEMO_NAMESPACE = uuid.UUID("de513333-f8a6-4658-b965-ecfb49f90c57")


def _rows(name: str) -> list[dict[str, str]]:
    with (DEMO_DATA / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _demo_id(kind: str, code: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, f"{kind}:{code}")


def seed_intelligence_catalog(db) -> None:
    """Add the AI Store/SKU catalog without replacing the original backend seed."""
    stores = {row["store_id"]: row for row in _rows("stores.csv")}
    products = {row["sku_id"]: row for row in _rows("products.csv")}
    categories_by_slug = {item.slug: item for item in db.scalars(select(Category)).all()}
    for code, row in stores.items():
        if db.scalar(select(Store).where(Store.code == code)) is None:
            db.add(Store(id=_demo_id("store", code), code=code, name=row["store_name"], address=row["address"]))
    for sku, row in products.items():
        slug = row["category"]
        category = categories_by_slug.get(slug)
        if category is None:
            category = Category(id=_demo_id("category", slug), slug=slug, name=slug.replace("_", " ").title())
            db.add(category)
            categories_by_slug[slug] = category
        if db.scalar(select(Product).where(Product.sku == sku)) is None:
            db.add(Product(id=_demo_id("product", sku), sku=sku, name=row["product_name"], unit="item",
                           selling_price=Decimal(row["unit_price"]), category_id=category.id,
                           is_perishable=int(row["shelf_life_days"]) <= 30,
                           default_shelf_life_days=int(row["shelf_life_days"])))
    supplier = db.get(Supplier, _demo_id("supplier", "AI-DEMO"))
    if supplier is None:
        supplier = Supplier(id=_demo_id("supplier", "AI-DEMO"), name="SmartGrocery Demo Supplier", lead_time_days=2)
        db.add(supplier)
    db.flush()
    today = date.today()
    linked_products = set(db.scalars(select(SupplierProduct.product_id).where(
        SupplierProduct.supplier_id == supplier.id)).all())
    for row in _rows("store_assortment.csv"):
        store_code, sku = row["store_id"], row["sku_id"]
        if store_code not in stores or sku not in products:
            raise ValueError(f"Unknown Store/SKU in demo assortment: {store_code}/{sku}")
        store_id, product_id = _demo_id("store", store_code), _demo_id("product", sku)
        lot = f"DEMO-{store_code}-{sku}"
        exists = db.scalar(select(InventoryBatch).where(InventoryBatch.store_id == store_id,
                            InventoryBatch.product_id == product_id, InventoryBatch.lot_code == lot))
        if exists is None:
            quantity = Decimal("2") if store_code == "S001" and sku == "SKU005" else Decimal("15")
            shelf_life = int(products[sku]["shelf_life_days"])
            db.add(InventoryBatch(store_id=store_id, product_id=product_id, lot_code=lot,
                                  quantity_on_hand=quantity, expiry_date=today + timedelta(days=max(shelf_life, 2)),
                                  unit_cost=Decimal(products[sku]["purchase_cost"])))
        if product_id not in linked_products:
            db.add(SupplierProduct(supplier_id=supplier.id, product_id=product_id, supplier_sku=sku,
                                   unit_cost=Decimal(products[sku]["purchase_cost"]),
                                   min_order_qty=Decimal(products[sku]["moq"])))
            linked_products.add(product_id)
    password = os.getenv("SG_DEMO_PASSWORD", "DemoPass123!")
    for email, role in (("merchant@smartgrocery.example.com", UserRole.MERCHANT),
                        ("customer@smartgrocery.example.com", UserRole.CUSTOMER)):
        if db.scalar(select(User).where(User.email == email)) is None:
            db.add(User(id=_demo_id("user", email), email=email, full_name=f"Demo {role.value.title()}",
                        password_hash=hash_password(password), role=role))


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
        today = date.today()
        batches = [
            ("APL-FUJI-01", "LOT-APL-20261029", Decimal("30.000"), today + timedelta(days=14), Decimal("25000.00")),
            ("MILK-1L-01", "LOT-MILK-20261029", Decimal("50.000"), today + timedelta(days=10), Decimal("21000.00")),
            ("VEG-CARROT-01", "LOT-CARROT-20261029", Decimal("25.000"), today + timedelta(days=10), Decimal("14000.00")),
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
        seed_intelligence_catalog(db)


if __name__ == "__main__":
    seed()
    print("Seed completed: legacy and AI demo catalog, inventory, supplier, and demo users.")

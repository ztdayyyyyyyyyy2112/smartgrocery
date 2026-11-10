from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models import InventoryBatch, Product, Store, User, UserRole
from app.security import create_token, hash_password

client = TestClient(app)


def test_concurrent_checkout_cannot_oversell_single_unit() -> None:
    with SessionLocal() as db:
        store = db.query(Store).first()
        assert store is not None
        product = Product(sku=f"CONC-{uuid4().hex[:10]}", name="Concurrency SKU", unit="unit", selling_price=Decimal("1000"), is_perishable=False)
        db.add(product)
        db.flush()
        db.add(InventoryBatch(store_id=store.id, product_id=product.id, lot_code=f"CONC-{uuid4().hex}", quantity_on_hand=Decimal("1"), quantity_reserved=Decimal("0")))
        users = [User(email=f"concurrency-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="Concurrency User", role=UserRole.CUSTOMER) for _ in range(2)]
        db.add_all(users)
        db.commit()
        store_id, product_id = str(store.id), str(product.id)
        tokens = [create_token(user, token_type="access", expires_delta=timedelta(minutes=15)) for user in users]

    def checkout(index: int):
        return client.post("/api/v1/orders", headers={"Authorization": f"Bearer {tokens[index]}", "Idempotency-Key": f"concurrency-{uuid4().hex}"}, json={"store_id": store_id, "items": [{"product_id": product_id, "quantity": "1"}]})

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(checkout, [0, 1]))
    assert sorted(response.status_code for response in responses) == [201, 409]


def test_merchant_only_endpoints_enforce_auth_and_role() -> None:
    assert client.get("/api/v1/inventory").status_code == 401
    assert client.get("/api/v1/forecasts").status_code == 401
    with SessionLocal() as db:
        customer = User(email=f"rbac-customer-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="RBAC Customer", role=UserRole.CUSTOMER)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        token = create_token(customer, token_type="access", expires_delta=timedelta(minutes=15))
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/inventory", headers=headers).status_code == 403
    assert client.get("/api/v1/forecasts", headers=headers).status_code == 403
    assert client.get("/api/v1/suppliers", headers=headers).status_code == 403


def test_rbac_matrix_covers_merchant_success_inactive_and_not_found() -> None:
    with SessionLocal() as db:
        merchant = User(email=f"rbac-merchant-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="RBAC Merchant", role=UserRole.MERCHANT)
        inactive = User(email=f"rbac-inactive-{uuid4()}@example.com", password_hash=hash_password("password123"), full_name="RBAC Inactive", role=UserRole.MERCHANT, is_active=False)
        db.add_all([merchant, inactive])
        db.commit()
        db.refresh(merchant)
        db.refresh(inactive)
        merchant_token = create_token(merchant, token_type="access", expires_delta=timedelta(minutes=15))
        inactive_token = create_token(inactive, token_type="access", expires_delta=timedelta(minutes=15))

    assert client.get("/api/v1/inventory", headers={"Authorization": f"Bearer {merchant_token}"}).status_code == 200
    assert client.get("/api/v1/inventory", headers={"Authorization": f"Bearer {inactive_token}"}).status_code == 401
    assert client.get(f"/api/v1/products/{uuid4()}").status_code == 404

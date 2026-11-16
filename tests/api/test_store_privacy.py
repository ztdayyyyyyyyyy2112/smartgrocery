from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models import Store, User, UserRole
from app.security import create_token, hash_password


def test_browser_session_uses_http_only_cookies_and_requires_origin() -> None:
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", headers={"Origin": "http://localhost:3000", "X-SG-Browser-Session": "1"},
                            json={"email": "customer@smartgrocery.example.com", "password": "DemoPass123!"})
        assert login.status_code == 200
        assert "access_token" not in login.json()
        assert "HttpOnly" in login.headers["set-cookie"]
        assert client.get("/api/v1/auth/me").status_code == 200
        assert client.post("/api/v1/auth/logout", headers={"Origin": "https://other.example"}).status_code == 403
        assert client.post("/api/v1/auth/logout", headers={"Origin": "http://localhost:3000"}).status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 401


def test_merchant_cannot_read_or_mutate_another_store() -> None:
    with SessionLocal.begin() as db:
        store = db.scalar(select(Store).where(Store.code == "S002"))
        merchant = User(email=f"other-merchant-{uuid4().hex}@example.com", full_name="Other Merchant",
                        password_hash=hash_password("password123"), role=UserRole.MERCHANT)
        db.add(merchant)
        db.flush()
        store.merchant_id = merchant.id
        owned_store_id = str(store.id)
        token = create_token(merchant, token_type="access", expires_delta=timedelta(minutes=15))
    headers = {"Authorization": f"Bearer {token}"}
    with TestClient(app) as client:
        inventory = client.get("/api/v1/inventory", headers=headers)
        assert inventory.status_code == 200
        assert all(item["store_id"] == owned_store_id for item in inventory.json())
        assert client.get("/api/v1/orders", headers=headers).status_code == 200
        assert client.post("/api/v1/jobs/forecasts", headers=headers,
                           json={"store_id": "00000000-0000-0000-0000-000000000001"}).status_code == 404

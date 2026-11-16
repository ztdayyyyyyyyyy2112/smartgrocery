from fastapi.testclient import TestClient
from sqlalchemy import select
from uuid import uuid4

from app.main import app
from app.db.session import SessionLocal
from app.models import User

client = TestClient(app)


def test_catalog_pagination_and_detail() -> None:
    response = client.get("/api/v1/products?page=1&page_size=2")
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] >= 3
    assert len(body["items"]) == 2

    product_id = body["items"][0]["id"]
    detail = client.get(f"/api/v1/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == product_id
    assert client.get("/api/v1/products/00000000-0000-0000-0000-000000000099").status_code == 404


def test_register_login_and_invalid_auth() -> None:
    email = f"catalog-auth-{uuid4().hex}@example.com"
    register = client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "full_name": "Auth Test", "phone": "0900000000", "default_address": "1 Demo Street", "privacy_consent": True})
    assert register.status_code in {201, 409}
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    refresh_token = login.json()["refresh_token"]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"}).status_code == 401
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != refresh_token
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token}).status_code == 401


def test_inactive_user_cannot_login() -> None:
    email = f"inactive-auth-{uuid4().hex}@example.com"
    register = client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "full_name": "Inactive Test", "phone": "0900000000", "default_address": "1 Demo Street", "privacy_consent": True})
    assert register.status_code in {201, 409}
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        user.is_active = False
        db.commit()
    assert client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).status_code == 401

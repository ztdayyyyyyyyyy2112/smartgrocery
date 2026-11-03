from fastapi.testclient import TestClient

from app.main import app

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
    email = "catalog-auth-test@example.com"
    register = client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "full_name": "Auth Test"})
    assert register.status_code in {201, 409}
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"}).status_code == 401

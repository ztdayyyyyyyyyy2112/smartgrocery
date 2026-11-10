"""Test HTTP API (cần fastapi + httpx). Tự skip nếu môi trường chưa cài."""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="module")
def client(service):
    from src.inference import api
    return TestClient(api.app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["model_loaded"] is True


def test_replenishment_endpoint(client):
    body = {"store_id": "S001", "sku_id": "SKU005", "inventory": {"on_hand": 20, "on_order": 0, "reserved": 2}}
    r = client.post("/forecast/replenishment", json=body)
    assert r.status_code == 200
    assert len(r.json()["forecast"]) == 7


def test_unknown_sku_404(client):
    body = {"store_id": "S001", "sku_id": "SKU999", "inventory": {"on_hand": 1}}
    r = client.post("/forecast/replenishment", json=body)
    assert r.status_code == 404 and r.json()["error_code"] == "UNKNOWN_SKU"


def test_validation_422(client):
    r = client.post("/forecast/replenishment", json={"store_id": "S001"})
    assert r.status_code == 422


def test_batch(client):
    items = [{"store_id": "S001", "sku_id": "SKU005", "inventory": {"on_hand": 20}},
             {"store_id": "S001", "sku_id": "SKU999", "inventory": {"on_hand": 1}}]
    r = client.post("/forecast/replenishment/batch", json={"items": items})
    assert r.status_code == 200
    assert [i["ok"] for i in r.json()["items"]] == [True, False]

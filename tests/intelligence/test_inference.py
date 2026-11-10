import json
import math

import pytest
from pydantic import ValidationError

from src.inference.schemas import ReplenishmentRequest, ReplenishmentResponse
from src.inference.service import IntelligenceService, ServiceError


def _req(**kw):
    base = {"store_id": "S001", "sku_id": "SKU005", "inventory": {"on_hand": 20, "on_order": 0, "reserved": 2}}
    base.update(kw)
    return base


def _no_nan(obj):
    if isinstance(obj, float):
        assert math.isfinite(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _no_nan(v)
    elif isinstance(obj, list):
        for v in obj:
            _no_nan(v)


def test_reorder_response_matches_contract(service):
    r = service.replenishment(_req())
    ReplenishmentResponse(**r)                                # validate theo schema
    assert r["status"] == "REORDER_RECOMMENDED"
    assert len(r["forecast"]) == 7
    assert r["inventory_position"] == 18
    assert r["requires_approval"] is True
    assert r["suggested_order_qty"] >= 0
    _no_nan(r)
    json.dumps(r)                                             # serialize được


def test_no_reorder_when_stock_high(service):
    r = service.replenishment(_req(inventory={"on_hand": 5000, "on_order": 0, "reserved": 0}))
    assert r["status"] == "NO_REORDER_NEEDED" and r["suggested_order_qty"] == 0


def test_horizon_insufficient(service):
    r = service.replenishment(_req(sku_id="SKU004"))          # lead time 10 ngày
    assert r["status"] == "HORIZON_INSUFFICIENT" and r["suggested_order_qty"] is None


def test_negative_inventory_position(service):
    r = service.replenishment(_req(inventory={"on_hand": 1, "on_order": 0, "reserved": 10}))
    assert r["status"] == "INVENTORY_DATA_CHECK"


def test_meu_missing_costs_falls_back_to_rop(service):
    r = service.replenishment(_req(costs={"selling_price": 34000}))
    assert "MEU_INPUT_MISSING" in r["warnings"]
    assert r["suggested_order_qty"] == r["rop_order_qty"]


def test_forecast_horizon_param(service):
    r = service.replenishment(_req(forecast_horizon=3))
    assert len(r["forecast"]) == 3


def test_unknown_sku(service):
    with pytest.raises(ServiceError) as e:
        service.replenishment(_req(sku_id="SKU999"))
    assert e.value.code == "UNKNOWN_SKU" and e.value.http_status == 404


def test_unknown_series(service):
    with pytest.raises(ServiceError) as e:
        service.replenishment(_req(store_id="S003", sku_id="SKU004"))   # S003 không bán SKU004
    assert e.value.code == "UNKNOWN_SERIES"


def test_input_validation():
    with pytest.raises(ValidationError):
        ReplenishmentRequest(**_req(inventory={"on_hand": -1}))
    with pytest.raises(ValidationError):
        ReplenishmentRequest(**_req(forecast_horizon=10))
    assert ReplenishmentRequest(**_req(sku_id=" sku005 ")).sku_id == "SKU005"


def test_model_unavailable_fallback(tmp_path, monkeypatch):
    import src.inference.service as svc_mod
    monkeypatch.setattr(svc_mod, "BUNDLE_PATH", tmp_path / "missing.joblib")
    s = IntelligenceService()
    assert s.health()["status"] == "degraded"
    r = s.replenishment(_req())
    assert "MODEL_UNAVAILABLE" in r["warnings"]
    assert r["model_version"] == "seasonal-naive-fallback"
    assert all(p["predicted_demand"] is not None for p in r["forecast"])


def test_refresh_job_degraded_keeps_running(tmp_path):
    from src.jobs.refresh_forecasts import run_refresh
    st = run_refresh(bundle_path=tmp_path / "missing.joblib")
    assert st["status"] == "DEGRADED" and st["n_series"] > 0
    st2 = run_refresh()                                       # khôi phục forecast chuẩn
    assert st2["status"] == "SUCCESS"

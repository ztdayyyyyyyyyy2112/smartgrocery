import json

import numpy as np
import pandas as pd

from src.models.train_lightgbm import BUNDLE_PATH, METADATA_PATH, load_bundle
from src.utils import config


def test_artifact_loads_with_7_horizons(service):
    b = load_bundle(BUNDLE_PATH)
    assert sorted(b["models"]) == list(range(1, 8))
    meta = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    assert meta["model_version"] == b["model_version"]
    assert meta["features"] == b["features"]


def test_latest_forecast_shape_and_values(service):
    fc = pd.read_csv(config.FORECAST_DIR / "latest_forecast.csv")
    assert (fc.groupby(["store_id", "sku_id"]).size() == 7).all()
    assert fc["predicted_sales"].notna().all()
    assert np.isfinite(fc["predicted_sales"]).all()
    assert (fc["predicted_sales"] >= 0).all()


def test_lightgbm_beats_seasonal_naive():
    p = config.EVAL_DIR / "model_comparison.csv"
    m = pd.read_csv(p).set_index("model")
    assert m.loc["LightGBM", "WAPE"] < m.loc["Seasonal Naive", "WAPE"]


def test_forecast_reproducible(service):
    a = service.forecast("S001", "SKU005")
    from src.inference.service import IntelligenceService
    b = IntelligenceService().forecast("S001", "SKU005")
    assert [x["predicted_demand"] for x in a["forecast"]] == [x["predicted_demand"] for x in b["forecast"]]


def test_new_sku_flagged(service):
    f = service.forecast("S002", "SKU032")
    assert f["status"] == "INSUFFICIENT_HISTORY" and f["confidence"] == "LOW"
    assert f["method"] == "rule_mean_fallback"

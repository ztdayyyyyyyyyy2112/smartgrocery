"""Huấn luyện LightGBM theo chiến lược Direct: 7 model, mỗi model một horizon t+1..t+7."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from src.features.build_features import (CATEGORICAL, FEATURES, build_origin_features,
                                         build_training_frame, to_model_matrix)
from src.models.gbm_backend import GBMRegressor, backend_name
from src.models.seasonal_naive import moving_average_28, seasonal_naive
from src.utils import config

BUNDLE_PATH = config.MODEL_DIR / "forecast_model_bundle.joblib"
METADATA_PATH = config.MODEL_DIR / "model_metadata.json"


def model_version() -> str:
    b = backend_name()
    return f"lightgbm-direct-v{config.MODEL_SEMVER}" if b == "lightgbm" else f"histgb-direct-v{config.MODEL_SEMVER}"


def categories_from_master(products: pd.DataFrame, stores: pd.DataFrame) -> dict[str, list[str]]:
    return {"store_id": sorted(stores["store_id"].astype(str)),
            "sku_id": sorted(products["sku_id"].astype(str)),
            "category": sorted(products["category"].astype(str).unique())}


def prepare_frames(panel: pd.DataFrame, promotions: pd.DataFrame, holidays: pd.DataFrame,
                   products: pd.DataFrame) -> tuple[pd.DataFrame, dict[int, pd.DataFrame]]:
    origin = build_origin_features(panel)
    frames = {}
    for h in range(1, config.HORIZON + 1):
        f = build_training_frame(origin, h, promotions, holidays, products)
        f["pred_seasonal_naive"] = seasonal_naive(f)
        f["pred_ma28"] = moving_average_28(f)
        frames[h] = f
    return origin, frames


def train_one(frame: pd.DataFrame, categories: dict, train_mask, valid_mask=None, n_estimators=None) -> GBMRegressor:
    tr = frame[train_mask & (frame["y_ok"] == 1)]
    X_tr, y_tr = to_model_matrix(tr, categories), tr["y"].to_numpy(float)
    if valid_mask is not None:
        va = frame[valid_mask & (frame["y_ok"] == 1)]
        X_va, y_va = to_model_matrix(va, categories), va["y"].to_numpy(float)
        return GBMRegressor().fit(X_tr, y_tr, X_va, y_va)
    return GBMRegressor(n_estimators=n_estimators).fit(X_tr, y_tr)


def train_final(frames: dict[int, pd.DataFrame], categories: dict, n_iter: dict[int, int],
                train_end: pd.Timestamp, logger=None) -> dict:
    """Huấn luyện model cuối trên toàn bộ dữ liệu có target <= train_end, số cây lấy từ backtest."""
    models = {}
    for h, f in frames.items():
        mask = f["target_date"] <= train_end
        models[h] = train_one(f, categories, mask, n_estimators=n_iter[h])
        if logger:
            logger.info("final model h=%d trained: rows=%d trees=%d", h, int((mask & (f.y_ok == 1)).sum()), n_iter[h])
    bundle = {
        "models": models,
        "features": FEATURES,
        "categorical": CATEGORICAL,
        "categories": categories,
        "backend": backend_name(),
        "model_version": model_version(),
        "horizon": config.HORIZON,
        "n_estimators": n_iter,
        "train_end_date": str(pd.Timestamp(train_end).date()),
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return bundle


def save_bundle(bundle: dict, extra_meta: dict | None = None) -> None:
    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, BUNDLE_PATH, compress=3)
    meta = {k: v for k, v in bundle.items() if k != "models"}
    meta["n_estimators"] = {str(k): int(v) for k, v in meta["n_estimators"].items()}
    meta.update(extra_meta or {})
    METADATA_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def load_bundle(path=BUNDLE_PATH) -> dict:
    bundle = joblib.load(path)
    missing = {h for h in range(1, config.HORIZON + 1)} - set(bundle["models"])
    if missing:
        raise ValueError(f"Bundle thiếu model cho horizon {sorted(missing)}")
    return bundle


def predict_frame(bundle: dict, frame: pd.DataFrame, h: int) -> np.ndarray:
    X = to_model_matrix(frame, bundle["categories"])
    return bundle["models"][h].predict(X)

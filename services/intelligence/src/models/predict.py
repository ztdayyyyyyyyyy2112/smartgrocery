"""Tạo dự báo 7 ngày cho mọi Store–SKU tại ngày as-of (mục 8.1).

Quy tắc confidence / fallback:
  * history < MIN_HISTORY_DAYS_ANY (7 ngày quan sát) -> INSUFFICIENT_HISTORY:
        dùng rule fallback = trung bình các ngày đã quan sát (không stockout), confidence LOW.
  * history < MIN_HISTORY_DAYS_MODEL (28)            -> dùng model, confidence LOW.
  * còn lại: theo WAPE backtest của chuỗi: <=35% HIGH, <=60% MEDIUM, >60% LOW.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.features.build_features import build_inference_frame
from src.models.seasonal_naive import seasonal_naive
from src.models.train_lightgbm import predict_frame
from src.utils import config


def confidence_from(history_obs: int, wape: float | None) -> str:
    if history_obs < config.MIN_HISTORY_DAYS_MODEL:
        return "LOW"
    if wape is None or np.isnan(wape):
        return "MEDIUM"
    return "HIGH" if wape <= 35 else ("MEDIUM" if wape <= 60 else "LOW")


def forecast_all(bundle: dict | None, origin: pd.DataFrame, panel: pd.DataFrame, as_of: pd.Timestamp,
                 promotions: pd.DataFrame, holidays: pd.DataFrame, products: pd.DataFrame,
                 resid: pd.DataFrame | None = None) -> pd.DataFrame:
    as_of = pd.Timestamp(as_of)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    hist = panel[panel["date"] <= as_of]
    ok_hist = hist[(hist["is_missing"] == 0) & (hist["is_stockout"] == 0)]
    obs = ok_hist.groupby(["store_id", "sku_id"])["sales"].agg(history_obs="count", hist_mean="mean").reset_index()

    rows = []
    for h in range(1, config.HORIZON + 1):
        fr = build_inference_frame(origin, as_of, h, promotions, holidays, products)
        fr["baseline_seasonal_naive"] = seasonal_naive(fr)
        if bundle is not None:
            fr["predicted_sales"] = predict_frame(bundle, fr, h)
            fr["method"] = "model"
        else:  # MODEL_UNAVAILABLE -> baseline đã kiểm chứng
            fr["predicted_sales"] = fr["baseline_seasonal_naive"]
            fr["method"] = "seasonal_naive_fallback"
        rows.append(fr[["store_id", "sku_id", "category", "date", "target_date", "horizon",
                        "predicted_sales", "baseline_seasonal_naive", "method"]])
    out = pd.concat(rows, ignore_index=True).merge(obs, on=["store_id", "sku_id"], how="left")
    out["history_obs"] = out["history_obs"].fillna(0).astype(int)

    insufficient = out["history_obs"] < config.MIN_HISTORY_DAYS_ANY
    out.loc[insufficient, "predicted_sales"] = out.loc[insufficient, "hist_mean"]
    out.loc[insufficient, "method"] = "rule_mean_fallback"
    still_nan = out["predicted_sales"].isna()
    out.loc[still_nan, "method"] = "unavailable"

    if resid is not None:
        out = out.merge(resid[["store_id", "sku_id", "wape_backtest"]], on=["store_id", "sku_id"], how="left")
    else:
        out["wape_backtest"] = np.nan
    out["confidence"] = [confidence_from(o, w) for o, w in zip(out["history_obs"], out["wape_backtest"])]
    out["status"] = np.where(insufficient, "INSUFFICIENT_HISTORY", "OK")
    out["predicted_sales"] = out["predicted_sales"].clip(lower=0).round(3)
    out["model_version"] = bundle["model_version"] if bundle else "seasonal-naive-fallback"
    out["generated_at"] = generated_at
    out = out.rename(columns={"date": "as_of_date", "target_date": "forecast_date"})
    cols = ["as_of_date", "forecast_date", "store_id", "sku_id", "category", "horizon", "predicted_sales",
            "baseline_seasonal_naive", "method", "status", "confidence", "history_obs", "wape_backtest",
            "model_version", "generated_at"]
    return out[cols].sort_values(["store_id", "sku_id", "horizon"]).reset_index(drop=True)

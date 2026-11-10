"""Metrics: WAPE, RMSE, MAE, Bias (mục 8.2–8.3)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_metrics(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true, y_pred = y_true[mask], y_pred[mask]
    n = int(len(y_true))
    if n == 0:
        return {"n": 0, "WAPE": None, "RMSE": None, "MAE": None, "Bias_pct": None}
    err = y_pred - y_true
    denom = float(np.sum(np.abs(y_true)))
    return {
        "n": n,
        "WAPE": float(np.sum(np.abs(err)) / denom * 100) if denom != 0 else None,  # tổng actual = 0 -> N/A
        "RMSE": float(np.sqrt(np.mean(err ** 2))),
        "MAE": float(np.mean(np.abs(err))),
        "Bias_pct": float(np.sum(err) / denom * 100) if denom != 0 else None,
    }


def metrics_table(df: pd.DataFrame, pred_cols: dict[str, str], by: list[str] | None = None) -> pd.DataFrame:
    """df có cột y và các cột dự báo. pred_cols = {tên model: tên cột}."""
    rows = []
    groups = [((), df)] if not by else df.groupby(by)
    for key, g in groups:
        key = key if isinstance(key, tuple) else (key,)
        for name, col in pred_cols.items():
            m = calculate_metrics(g["y"], g[col])
            rows.append({**dict(zip(by or [], key)), "model": name, **m})
    return pd.DataFrame(rows)

"""Rolling-origin backtesting (mục 8.5).

Với mỗi cutoff C:
  * train : các dòng có target_date <  C - VALID_DAYS
  * valid : target_date trong [C - VALID_DAYS, C)  -> chỉ dùng cho early stopping
  * test  : origin t trong [C - 1, C - 1 + TEST_DAYS)  -> target luôn >= C
Model được huấn luyện lại ở mỗi fold, không bao giờ thấy target của tập test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.models.train_lightgbm import predict_frame, train_one
from src.utils import config

KEEP = ["store_id", "sku_id", "category", "date", "target_date", "horizon", "y", "y_ok",
        "history_days", "zero_share_28", "t_is_promo", "pred_seasonal_naive", "pred_ma28"]


def run_backtest(frames: dict[int, pd.DataFrame], categories: dict, logger=None) -> tuple[pd.DataFrame, dict]:
    preds, best_iters = [], {h: [] for h in frames}
    for fold, cutoff in enumerate(config.BACKTEST_CUTOFFS, start=1):
        C = pd.Timestamp(cutoff)
        v0 = C - pd.Timedelta(days=config.VALID_DAYS)
        t0, t1 = C - pd.Timedelta(days=1), C - pd.Timedelta(days=1) + pd.Timedelta(days=config.BACKTEST_TEST_DAYS)
        for h, f in frames.items():
            train_mask = f["target_date"] < v0
            valid_mask = (f["target_date"] >= v0) & (f["target_date"] < C)
            model = train_one(f, categories, train_mask, valid_mask)
            best_iters[h].append(model.best_iteration)
            test = f[(f["date"] >= t0) & (f["date"] < t1) & f["y"].notna()].copy()
            bundle = {"models": {h: model}, "categories": categories}
            test["pred_lightgbm"] = predict_frame(bundle, test, h)
            test["fold"] = fold
            test["cutoff"] = C
            preds.append(test[KEEP + ["pred_lightgbm", "fold", "cutoff"]])
            if logger:
                ok = test[test.y_ok == 1]
                wape = np.abs(ok.pred_lightgbm - ok.y).sum() / max(ok.y.abs().sum(), 1e-9) * 100
                logger.info("fold %d cutoff %s h=%d trees=%d test_rows=%d WAPE=%.2f%%",
                            fold, cutoff, h, model.best_iteration, len(ok), wape)
    bt = pd.concat(preds, ignore_index=True)
    n_iter = {h: int(np.median(v)) for h, v in best_iters.items()}
    return bt, n_iter


def residual_stats(bt: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Độ lệch chuẩn sai số dự báo theo Store–SKU (dùng cho Safety Stock) + WAPE (dùng cho confidence).

    sigma_daily ước lượng từ residual backtest thay vì độ lệch chuẩn doanh số thô (mục 9.4).
    Chuỗi < 20 điểm residual -> dùng sigma theo category nhân tỉ lệ mức bán (shrink)."""
    ok = bt[bt["y_ok"] == 1].copy()
    ok["resid"] = ok["y"] - ok["pred_lightgbm"]
    g = ok.groupby(["store_id", "sku_id"])
    s = g.agg(n_resid=("resid", "size"), sigma_daily=("resid", "std"), mean_actual=("y", "mean"),
              abs_err=("resid", lambda r: np.abs(r).sum()), sum_actual=("y", "sum")).reset_index()
    s["wape_backtest"] = np.where(s["sum_actual"] > 0, s["abs_err"] / s["sum_actual"] * 100, np.nan)
    s = s.merge(products[["sku_id", "category"]], on="sku_id", how="left")
    cat_cv = (s[s.n_resid >= 20].assign(cv=lambda d: d.sigma_daily / d.mean_actual.clip(lower=0.1))
              .groupby("category")["cv"].median())
    fallback = s["category"].map(cat_cv).fillna(1.0) * s["mean_actual"].clip(lower=0.5)
    s["sigma_source"] = np.where(s["n_resid"] >= 20, "backtest_residual", "category_cv_fallback")
    s["sigma_daily"] = np.where(s["n_resid"] >= 20, s["sigma_daily"], fallback)
    s["sigma_daily"] = s["sigma_daily"].fillna(fallback).clip(lower=0.5)
    return s.drop(columns=["abs_err", "sum_actual"])

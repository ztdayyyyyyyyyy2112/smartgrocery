"""Lớp bọc Gradient Boosting: ưu tiên LightGBM.

Nếu môi trường chưa cài được lightgbm, tự động dùng
sklearn.ensemble.HistGradientBoostingRegressor (cùng họ thuật toán: GBDT dạng histogram,
hỗ trợ categorical và giá trị NaN). Backend thực tế được ghi vào metadata
(`backend`) và model_version để không nhầm lẫn khi báo cáo.

Cả hai dùng objective Poisson (phù hợp số lượng bán không âm, nhiều số 0)
và early stopping trên tập validation chia THEO THỜI GIAN (không random).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.config import RANDOM_STATE

try:  # pragma: no cover - phụ thuộc môi trường
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except Exception:  # noqa: BLE001
    lgb = None
    HAS_LIGHTGBM = False

LGBM_PARAMS = dict(objective="poisson", learning_rate=0.05, num_leaves=31, min_child_samples=20,
                   subsample=0.8, subsample_freq=1, colsample_bytree=0.9, reg_lambda=1.0,
                   n_estimators=2000, random_state=RANDOM_STATE, verbose=-1)
HGB_PARAMS = dict(loss="poisson", learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=20,
                  l2_regularization=1.0, categorical_features="from_dtype", early_stopping=False,
                  random_state=RANDOM_STATE)


def backend_name() -> str:
    return "lightgbm" if HAS_LIGHTGBM else "sklearn-histgb"


class GBMRegressor:
    def __init__(self, n_estimators: int | None = None):
        self.backend = backend_name()
        self.fixed_n = n_estimators
        self.model = None
        self.best_iteration: int | None = None

    # ---- training ----
    def fit(self, X: pd.DataFrame, y: np.ndarray, X_val: pd.DataFrame | None = None,
            y_val: np.ndarray | None = None, patience: int = 100) -> "GBMRegressor":
        if self.backend == "lightgbm":
            params = dict(LGBM_PARAMS)
            if self.fixed_n:
                params["n_estimators"] = self.fixed_n
            self.model = lgb.LGBMRegressor(**params)
            if X_val is not None and not self.fixed_n:
                self.model.fit(X, y, eval_set=[(X_val, y_val)], eval_metric="l1",
                               callbacks=[lgb.early_stopping(patience, verbose=False)])
                self.best_iteration = int(self.model.best_iteration_ or params["n_estimators"])
            else:
                self.model.fit(X, y)
                self.best_iteration = params["n_estimators"]
            return self

        from sklearn.ensemble import HistGradientBoostingRegressor
        if self.fixed_n or X_val is None:
            n = self.fixed_n or 400
            self.model = HistGradientBoostingRegressor(max_iter=n, **HGB_PARAMS).fit(X, y)
            self.best_iteration = n
            return self
        # Early stopping theo thời gian: tăng dần số cây (warm_start), đo MAE trên validation
        step, max_iter = 50, 1500
        m = HistGradientBoostingRegressor(max_iter=step, warm_start=True, **HGB_PARAMS)
        best, best_n, bad = np.inf, step, 0
        n = step
        while n <= max_iter:
            m.set_params(max_iter=n)
            m.fit(X, y)
            mae = float(np.mean(np.abs(m.predict(X_val) - y_val)))
            if mae < best - 1e-6:
                best, best_n, bad = mae, n, 0
            else:
                bad += 1
                if bad * step >= patience:
                    break
            n += step
        self.model = HistGradientBoostingRegressor(max_iter=best_n, **HGB_PARAMS).fit(X, y)
        self.best_iteration = best_n
        return self

    # ---- inference ----
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("Model chưa được huấn luyện/nạp")
        p = self.model.predict(X)
        return np.clip(np.nan_to_num(p, nan=0.0, posinf=0.0, neginf=0.0), 0, None)

    def feature_importance(self, X_val: pd.DataFrame | None = None, y_val: np.ndarray | None = None) -> pd.Series:
        cols = list(X_val.columns) if X_val is not None else None
        if self.backend == "lightgbm":
            imp = self.model.booster_.feature_importance(importance_type="gain")
            return pd.Series(imp, index=self.model.booster_.feature_name()).sort_values(ascending=False)
        from sklearn.inspection import permutation_importance
        idx = np.random.default_rng(RANDOM_STATE).choice(len(X_val), min(6000, len(X_val)), replace=False)
        r = permutation_importance(self.model, X_val.iloc[idx], y_val[idx], n_repeats=3,
                                   random_state=RANDOM_STATE, scoring="neg_mean_absolute_error")
        return pd.Series(r.importances_mean, index=cols).sort_values(ascending=False)

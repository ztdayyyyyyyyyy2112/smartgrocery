"""Feature engineering cho dự báo Direct 7 horizon.

Quy ước thời gian (chống data leakage):
  * Origin t = cuối ngày t. Tại origin, đã biết doanh số đến hết ngày t (lag_0 = sales(t)).
  * Dự báo ngày t+h (h = 1..7). Mọi feature lịch sử chỉ dùng dữ liệu <= t.
  * Feature của NGÀY MỤC TIÊU chỉ gồm thông tin biết trước: lịch, ngày lễ,
    khuyến mãi đã lên kế hoạch (promotions.csv).
  * Same-weekday lag: sales(t+h-7) = lag_(7-h) tại origin -> luôn <= t vì h <= 7.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.data.aggregate_daily import add_promotions

KEYS = ["store_id", "sku_id"]
MAX_LAG = 27  # lag_0 .. lag_27

ORIGIN_FEATURES = (
    [f"lag_{k}" for k in (0, 1, 2, 3, 6, 13)]
    + ["roll_mean_7", "roll_mean_14", "roll_mean_28", "roll_std_7", "roll_std_28",
       "ewm_mean_7", "zero_share_28", "stockout_days_7", "missing_days_7", "history_days",
       "promo_days_7"]
)
TARGET_FEATURES = [
    "t_dow", "t_dom", "t_month", "t_weekofyear", "t_is_weekend", "t_is_holiday", "t_holiday_eve",
    "t_tet_window", "t_is_payday", "t_discount_pct", "t_is_promo",
    "sw_lag_1", "sw_lag_2", "sw_lag_4", "sw_mean",
]
STATIC_FEATURES = ["store_id", "sku_id", "category", "log_unit_price"]
CATEGORICAL = ["store_id", "sku_id", "category"]
FEATURES = STATIC_FEATURES + ORIGIN_FEATURES + TARGET_FEATURES


def build_origin_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Tính feature tại mỗi origin (mỗi dòng của panel). Panel phải liên tục theo ngày trong từng chuỗi."""
    df = panel.sort_values(KEYS + ["date"]).reset_index(drop=True)
    g = df.groupby(KEYS, sort=False)["sales"]
    lags = {f"lag_{k}": g.shift(k) for k in range(0, MAX_LAG + 1)}
    df = pd.concat([df, pd.DataFrame(lags)], axis=1)

    def roll(fn, w, minp):
        return g.transform(lambda s: getattr(s.rolling(w, min_periods=minp), fn)())

    df["roll_mean_7"] = roll("mean", 7, 3)
    df["roll_mean_14"] = roll("mean", 14, 5)
    df["roll_mean_28"] = roll("mean", 28, 7)
    df["roll_std_7"] = roll("std", 7, 3)
    df["roll_std_28"] = roll("std", 28, 7)
    df["ewm_mean_7"] = g.transform(lambda s: s.ewm(halflife=7, ignore_na=True).mean())
    zero = (df["sales"] == 0).astype(float).where(df["sales"].notna())
    df["zero_share_28"] = zero.groupby([df[k] for k in KEYS]).transform(
        lambda s: s.rolling(28, min_periods=7).mean())
    for col, out in (("is_stockout", "stockout_days_7"), ("is_missing", "missing_days_7"),
                     ("is_promo", "promo_days_7")):
        df[out] = df.groupby(KEYS, sort=False)[col].transform(lambda s: s.rolling(7, min_periods=1).sum())
    df["history_days"] = df.groupby(KEYS, sort=False).cumcount() + 1
    return df


def date_features(dates: pd.Series, holidays: pd.DataFrame) -> pd.DataFrame:
    d = pd.to_datetime(dates)
    hol = set(holidays["date"])
    public = holidays.loc[holidays["holiday_type"] == "public", "date"]
    eve = set()
    for x in public:
        eve |= {x - pd.Timedelta(days=1), x - pd.Timedelta(days=2)}
    tet = holidays.loc[holidays["holiday_name"].astype(str).str.contains("mùng 1", na=False), "date"].sort_values().values
    out = pd.DataFrame(index=d.index)
    out["t_dow"] = d.dt.dayofweek
    out["t_dom"] = d.dt.day
    out["t_month"] = d.dt.month
    out["t_weekofyear"] = d.dt.isocalendar().week.astype(int).values
    out["t_is_weekend"] = (out["t_dow"] >= 5).astype(int)
    out["t_is_holiday"] = d.isin(hol).astype(int)
    out["t_holiday_eve"] = d.isin(eve).astype(int)
    out["t_is_payday"] = d.dt.day.isin([1, 2, 3, 4, 5, 15, 16]).astype(int)
    if len(tet):
        dv = d.values.astype("datetime64[D]")
        diffs = (dv[:, None] - tet.astype("datetime64[D]")[None, :]).astype(int)
        nearest = diffs[np.arange(len(dv)), np.abs(diffs).argmin(axis=1)]
        out["t_tet_window"] = np.where((nearest >= -21) & (nearest <= 14), nearest, np.nan)
    else:
        out["t_tet_window"] = np.nan
    return out


def _add_target_features(base: pd.DataFrame, h: int, promotions: pd.DataFrame, holidays: pd.DataFrame,
                         products: pd.DataFrame) -> pd.DataFrame:
    out = base.copy()
    out["horizon"] = h
    out["target_date"] = out["date"] + pd.Timedelta(days=h)
    df_dates = date_features(out["target_date"], holidays)
    out = pd.concat([out, df_dates], axis=1)
    promo = add_promotions(out[KEYS + ["target_date"]].rename(columns={"target_date": "date"}), promotions)
    out["t_discount_pct"] = promo["discount_pct"].values
    out["t_is_promo"] = promo["is_promo"].values
    out["sw_lag_1"] = out[f"lag_{7 - h}"]
    out["sw_lag_2"] = out[f"lag_{14 - h}"]
    out["sw_lag_4"] = out[f"lag_{28 - h}"]
    out["sw_mean"] = out[["sw_lag_1", "sw_lag_2", "sw_lag_4"]].mean(axis=1)
    if "log_unit_price" not in out:
        out = out.merge(products[["sku_id"]].assign(log_unit_price=np.log(products["unit_price"])),
                        on="sku_id", how="left")
    return out


def build_training_frame(origin: pd.DataFrame, h: int, promotions: pd.DataFrame, holidays: pd.DataFrame,
                         products: pd.DataFrame) -> pd.DataFrame:
    """Frame cho horizon h: feature tại origin t + target = sales(t+h).

    y_ok = 1 nếu target quan sát được và không bị stockout (censored)."""
    g = origin.groupby(KEYS, sort=False)
    base = origin.copy()
    base["y"] = g["sales"].shift(-h)
    tgt_missing = g["is_missing"].shift(-h)
    tgt_stockout = g["is_stockout"].shift(-h)
    base["y_ok"] = (base["y"].notna() & (tgt_missing == 0) & (tgt_stockout == 0)).astype(int)
    return _add_target_features(base, h, promotions, holidays, products)


def build_inference_frame(origin: pd.DataFrame, as_of: pd.Timestamp, h: int, promotions: pd.DataFrame,
                          holidays: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    base = origin[origin["date"] == pd.Timestamp(as_of)].copy()
    return _add_target_features(base, h, promotions, holidays, products)


def to_model_matrix(frame: pd.DataFrame, categories: dict[str, list[str]]) -> pd.DataFrame:
    """Chọn đúng thứ tự FEATURES và ép categorical với danh mục cố định (nhất quán train/inference)."""
    X = frame[FEATURES].copy()
    for c in CATEGORICAL:
        X[c] = pd.Categorical(X[c].astype(str), categories=categories[c])
    for c in X.columns:
        if c not in CATEGORICAL:
            X[c] = X[c].astype(float)
    return X

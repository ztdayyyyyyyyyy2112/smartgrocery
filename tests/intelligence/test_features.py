import numpy as np
import pandas as pd

from src.features.build_features import FEATURES, build_origin_features, date_features


def test_lag_and_rolling_use_only_past(tiny_panel):
    o = build_origin_features(tiny_panel)
    r = o.iloc[40]
    assert r["lag_0"] == tiny_panel.loc[40, "sales"]
    assert r["lag_1"] == tiny_panel.loc[39, "sales"]
    assert np.isclose(r["roll_mean_7"], tiny_panel.loc[34:40, "sales"].mean())


def test_no_future_leakage(tiny_panel):
    """Thay đổi dữ liệu SAU origin không được làm thay đổi feature tại origin."""
    base = build_origin_features(tiny_panel)
    future_changed = tiny_panel.copy()
    future_changed.loc[45:, "sales"] = 999.0
    changed = build_origin_features(future_changed)
    cols = [c for c in base.columns if c.startswith(("lag_", "roll_", "ewm_", "zero_share", "stockout_days"))]
    pd.testing.assert_frame_equal(base.loc[:44, cols], changed.loc[:44, cols])


def test_same_weekday_lag_mapping(tiny_panel):
    from src.features.build_features import _add_target_features
    o = build_origin_features(tiny_panel)
    hol = pd.DataFrame({"date": pd.to_datetime([]), "holiday_name": [], "holiday_type": []})
    promos = pd.DataFrame(columns=["store_id", "sku_id", "start_date", "end_date", "discount_pct"])
    prods = pd.DataFrame({"sku_id": ["SKU001"], "unit_price": [12000]})
    for h in range(1, 8):
        f = _add_target_features(o, h, promos, hol, prods)
        i = 50
        target_minus_7 = tiny_panel.loc[i + h - 7, "sales"]
        assert f.loc[i, "sw_lag_1"] == target_minus_7      # sales(t+h-7), luôn <= t


def test_tet_window_feature():
    hol = pd.DataFrame({"date": pd.to_datetime(["2026-02-17"]), "holiday_name": ["Tết Nguyên đán mùng 1"],
                        "holiday_type": ["tet"]})
    f = date_features(pd.Series(pd.to_datetime(["2026-02-10", "2026-02-17", "2026-06-01"])), hol)
    assert f["t_tet_window"].tolist()[:2] == [-7, 0]
    assert np.isnan(f["t_tet_window"].iloc[2])
    assert f["t_is_holiday"].tolist() == [0, 1, 0]


def test_feature_list_unique():
    assert len(FEATURES) == len(set(FEATURES))

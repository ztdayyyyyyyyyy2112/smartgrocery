import numpy as np
import pandas as pd

from src.evaluation.metrics import calculate_metrics
from src.models.seasonal_naive import seasonal_naive, seasonal_naive_7d_from_history


def test_seasonal_naive_fallback_two_weeks():
    f = pd.DataFrame({"sw_lag_1": [5.0, np.nan, np.nan], "sw_lag_2": [9.0, 7.0, np.nan]})
    out = seasonal_naive(f)
    assert out[0] == 5 and out[1] == 7 and np.isnan(out[2])


def test_seasonal_naive_future_uses_calendar_not_last_rows():
    d = pd.date_range("2026-10-01", "2026-10-21", freq="D")
    h = pd.DataFrame({"date": d, "sales": np.arange(len(d), dtype=float)})
    h.loc[h.date == "2026-10-15", "sales"] = np.nan          # ngày missing
    fc = seasonal_naive_7d_from_history(h, pd.Timestamp("2026-10-21"))
    assert len(fc) == 7
    # t+1 = 22/10; 15/10 missing -> lùi thêm 1 tuần về 08/10 (giá trị = index 7)
    assert fc[0] == 7.0
    assert fc[1] == 15.0                                     # 23/10 -> 16/10 (index 15)



def test_metrics_values():
    m = calculate_metrics([10, 0, 5], [8, 1, 5])
    assert np.isclose(m["MAE"], 1.0)
    assert np.isclose(m["WAPE"], 3 / 15 * 100)
    assert np.isclose(m["RMSE"], np.sqrt((4 + 1 + 0) / 3))


def test_wape_undefined_when_actual_zero():
    assert calculate_metrics([0, 0], [1, 2])["WAPE"] is None

"""Seasonal Naive baseline: Forecast(t+h) = Actual(t+h-7).

Thực hiện riêng trong từng chuỗi Store–SKU (đã đảm bảo qua lag tại origin).
Nếu ngày cùng thứ tuần trước bị missing (đóng cửa/lỗi POS) -> dùng cùng thứ 2 tuần trước.
Nếu vẫn thiếu -> NaN (insufficient_history), KHÔNG bịa giá trị.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def seasonal_naive(frame: pd.DataFrame) -> np.ndarray:
    pred = frame["sw_lag_1"].to_numpy(dtype=float)
    fb = frame["sw_lag_2"].to_numpy(dtype=float)
    return np.where(np.isnan(pred), fb, pred)


def moving_average_28(frame: pd.DataFrame) -> np.ndarray:
    """Baseline tham khảo bổ sung: trung bình 28 ngày gần nhất."""
    return frame["roll_mean_28"].to_numpy(dtype=float)


def seasonal_naive_7d_from_history(history: pd.DataFrame, as_of: pd.Timestamp) -> list[float | None]:
    """Dự báo 7 ngày tương lai cho MỘT chuỗi Store–SKU từ lịch sử (dùng cho fallback inference).

    history: cột date, sales (NaN = missing). Lấy theo NGÀY LỊCH, không lấy 7 dòng cuối,
    để không sai khi lịch sử có ngày bị thiếu."""
    s = history.set_index("date")["sales"]
    out: list[float | None] = []
    for h in range(1, 8):
        target = pd.Timestamp(as_of) + pd.Timedelta(days=h)
        v = None
        for weeks in (1, 2):
            d = target - pd.Timedelta(days=7 * weeks)
            if d in s.index and pd.notna(s.loc[d]):
                v = float(s.loc[d])
                break
        out.append(v)
    return out

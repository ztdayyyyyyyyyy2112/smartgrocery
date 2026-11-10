"""Safety Stock = z × sigma_daily × sqrt(Lead Time)   (mục 9.4)

Giả định: lead time cố định, sai số dự báo hằng ngày độc lập, xấp xỉ phân phối chuẩn.
sigma_daily lấy từ residual backtest (src/evaluation/backtest.residual_stats).
"""
from __future__ import annotations

import math
from statistics import NormalDist


def z_from_service_level(service_level: float) -> float:
    if not 0 < service_level < 1:
        raise ValueError("service_level phải trong khoảng (0, 1)")
    return NormalDist().inv_cdf(service_level)


def safety_stock(sigma_daily: float, lead_time_days: int, service_level: float) -> float:
    if lead_time_days < 1:
        raise ValueError("lead_time_days phải >= 1")
    if sigma_daily < 0 or math.isnan(sigma_daily):
        raise ValueError("sigma_daily không hợp lệ")
    return z_from_service_level(service_level) * sigma_daily * math.sqrt(lead_time_days)

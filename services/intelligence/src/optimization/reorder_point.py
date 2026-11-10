"""Inventory Position, Reorder Point và lượng đặt cơ bản (mục 9.3, 9.5, 9.6).

  Inventory Position = On Hand + On Order - Reserved
  ROP = Expected Demand During Lead Time + Safety Stock
  Nếu IP <= ROP: qty = ROP - IP, sau đó áp dụng MOQ và làm tròn lên theo pack_size.
"""
from __future__ import annotations

import math


class HorizonInsufficientError(ValueError):
    """Lead time dài hơn số ngày dự báo hiện có -> không tự ý ngoại suy."""


def inventory_position(on_hand: float, on_order: float, reserved: float) -> float:
    if min(on_hand, on_order, reserved) < 0:
        raise ValueError("on_hand/on_order/reserved không được âm")
    return on_hand + on_order - reserved


def lead_time_demand(daily_forecast: list[float], lead_time_days: int) -> float:
    if lead_time_days > len(daily_forecast):
        raise HorizonInsufficientError(
            f"lead_time_days={lead_time_days} > forecast horizon={len(daily_forecast)}")
    return float(sum(daily_forecast[:lead_time_days]))


def reorder_point(lt_demand: float, ss: float) -> float:
    return lt_demand + ss


def round_to_pack(qty: float, pack_size: int = 1, moq: int = 0) -> int:
    """Áp dụng MOQ rồi làm tròn LÊN theo quy cách đóng gói. qty <= 0 -> 0."""
    if qty <= 0:
        return 0
    pack_size = max(int(pack_size or 1), 1)
    q = max(qty, moq or 0)
    return int(math.ceil(q / pack_size - 1e-9) * pack_size)


def basic_order_qty(ip: float, rop: float, pack_size: int = 1, moq: int = 0) -> int:
    if ip > rop:
        return 0
    return round_to_pack(rop - ip, pack_size, moq)

"""Maximum Expected Utility (mục 10) — chọn lượng đặt q có utility kỳ vọng lớn nhất.

  EU(q) = Σ_s p(s) · U(q, s)
  available = IP + q ; sold = min(D_s, available)
  leftover  = max(available - D_s, 0) ; shortage = max(D_s - available, 0)
  U = price·sold − cost·q + salvage·leftover − holding·leftover − waste·leftover − penalty·shortage

Hàng dư cuối kỳ vẫn nằm trong kho để bán chu kỳ sau nên giữ lại giá trị tồn kho
(salvage mặc định = purchase_cost). Chi phí thực của 1 đơn vị dư = holding + waste
(waste > 0 cho hàng tươi sống dễ hỏng). Nhờ vậy MEU đặt nhiều hơn cho hàng hạn dài,
ít hơn cho hàng tươi — đúng bản chất newsvendor.

Kịch bản nhu cầu: tổng nhu cầu trong protection period P = lead time + review period,
mean = Σ forecast[1..P], std = sigma_daily·sqrt(P). Rời rạc hóa phân phối chuẩn thành
5 kịch bản (phân vị 10/30/50/70/90%, mỗi kịch bản p = 0.2) — xác suất suy ra từ
residual backtest, không phải con số tự đặt.

Các hệ số chi phí là GIẢ ĐỊNH DEMO (từ products.csv tổng hợp) trừ khi Backend truyền vào.
Thiếu bất kỳ hệ số nào -> MEU không chạy (MEU_INPUT_MISSING).
"""
from __future__ import annotations

import math
from statistics import NormalDist

from src.optimization.reorder_point import round_to_pack

REQUIRED_COSTS = ("selling_price", "purchase_cost", "holding_cost_per_unit",
                  "stockout_penalty_per_unit", "waste_cost_per_unit")
SCENARIO_QUANTILES = [(0.1, "very_low"), (0.3, "low"), (0.5, "base"), (0.7, "high"), (0.9, "very_high")]


class MEUInputMissingError(ValueError):
    pass


def demand_scenarios(mean: float, std: float) -> list[dict]:
    nd = NormalDist()
    p = 1 / len(SCENARIO_QUANTILES)
    return [{"label": lab, "probability": p, "demand": max(0.0, mean + nd.inv_cdf(q) * std)}
            for q, lab in SCENARIO_QUANTILES]


def utility(q: float, demand: float, ip: float, c: dict) -> float:
    available = max(ip, 0) + q
    sold = min(demand, available)
    leftover = max(available - demand, 0.0)
    shortage = max(demand - available, 0.0)
    salvage = c.get("salvage_value_per_unit")
    salvage = c["purchase_cost"] if salvage is None else salvage
    return (c["selling_price"] * sold - c["purchase_cost"] * q + salvage * leftover
            - c["holding_cost_per_unit"] * leftover - c["waste_cost_per_unit"] * leftover
            - c["stockout_penalty_per_unit"] * shortage)


def expected_utility(q: float, scenarios: list[dict], ip: float, costs: dict) -> float:
    return sum(s["probability"] * utility(q, s["demand"], ip, costs) for s in scenarios)


def optimize_order_qty(daily_forecast: list[float], sigma_daily: float, ip: float, lead_time_days: int,
                       review_period_days: int, costs: dict | None, pack_size: int = 1, moq: int = 0,
                       reference_qty: int | None = None) -> dict:
    if not costs or any(costs.get(k) is None for k in REQUIRED_COSTS):
        missing = [k for k in REQUIRED_COSTS if not costs or costs.get(k) is None]
        raise MEUInputMissingError(f"Thiếu tham số chi phí cho MEU: {missing}")
    P = min(lead_time_days + review_period_days, len(daily_forecast))
    mean = float(sum(daily_forecast[:P]))
    std = float(sigma_daily) * math.sqrt(P)
    scen = demand_scenarios(mean, std)

    pack = max(int(pack_size or 1), 1)
    first = round_to_pack(1, pack, moq)
    upper = max(first, round_to_pack(mean + 3 * std - ip, pack, moq), 3 * (reference_qty or 0))
    candidates = [0] + list(range(first, upper + pack, pack))[:300]
    evals = [(q, expected_utility(q, scen, ip, costs)) for q in candidates]
    best_q, best_eu = max(evals, key=lambda t: (round(t[1], 6), -t[0]))
    top = sorted(evals, key=lambda t: -t[1])[:5]
    return {
        "recommended_qty": int(best_q),
        "expected_utility": round(best_eu, 2),
        "expected_utility_no_order": round(evals[0][1], 2),
        "expected_utility_reference_qty": (round(expected_utility(reference_qty, scen, ip, costs), 2)
                                           if reference_qty is not None else None),
        "protection_period_days": P,
        "scenarios": [{**s, "demand": round(s["demand"], 2)} for s in scen],
        "top_candidates": [{"order_qty": int(q), "expected_utility": round(e, 2)} for q, e in top],
        "n_candidates": len(candidates),
    }

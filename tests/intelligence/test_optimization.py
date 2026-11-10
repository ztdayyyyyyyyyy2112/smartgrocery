import math

import pytest

from src.optimization.meu import MEUInputMissingError, demand_scenarios, optimize_order_qty
from src.optimization.reorder_point import (HorizonInsufficientError, basic_order_qty, inventory_position,
                                            lead_time_demand, round_to_pack)
from src.optimization.safety_stock import safety_stock, z_from_service_level

COSTS = {"selling_price": 10, "purchase_cost": 7, "holding_cost_per_unit": 0.1,
         "stockout_penalty_per_unit": 1, "waste_cost_per_unit": 0}


def test_inventory_position_guide_example():
    assert inventory_position(30, 5, 3) == 32               # ví dụ mục 9.7


def test_rop_qty_and_pack_rounding_guide_example():
    assert basic_order_qty(32, 40) == 8
    assert basic_order_qty(32, 40, pack_size=6) == 12         # làm tròn lên theo pack 6


def test_no_order_when_ip_above_rop():
    assert basic_order_qty(50, 40, 6, 12) == 0


def test_moq_applied():
    assert round_to_pack(3, pack_size=5, moq=20) == 20
    assert round_to_pack(0, 5, 20) == 0


def test_safety_stock_formula():
    assert math.isclose(z_from_service_level(0.95), 1.6449, rel_tol=1e-3)
    assert math.isclose(safety_stock(4, 4, 0.95), 1.6449 * 4 * 2, rel_tol=1e-3)
    with pytest.raises(ValueError):
        safety_stock(4, 0, 0.95)


def test_lead_time_beyond_horizon_raises():
    with pytest.raises(HorizonInsufficientError):
        lead_time_demand([1] * 7, 10)


def test_meu_requires_costs():
    with pytest.raises(MEUInputMissingError):
        optimize_order_qty([10] * 7, 3, 5, 2, 1, {"selling_price": 10}, 1, 0)


def test_meu_scenarios_probabilities_sum_to_one():
    s = demand_scenarios(50, 10)
    assert math.isclose(sum(x["probability"] for x in s), 1.0)
    assert all(x["demand"] >= 0 for x in s)


def test_meu_perishable_orders_less_than_long_life():
    long_life = optimize_order_qty([10] * 7, 3, 0, 2, 1, COSTS, 1, 0)
    perishable = optimize_order_qty([10] * 7, 3, 0, 2, 1, {**COSTS, "waste_cost_per_unit": 6}, 1, 0)
    assert perishable["recommended_qty"] < long_life["recommended_qty"]
    assert long_life["recommended_qty"] % 1 == 0


def test_meu_respects_pack_and_moq():
    r = optimize_order_qty([10] * 7, 3, 0, 2, 1, COSTS, pack_size=12, moq=24)
    assert r["recommended_qty"] == 0 or (r["recommended_qty"] >= 24 and r["recommended_qty"] % 12 == 0)

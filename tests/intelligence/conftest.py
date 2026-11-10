"""Cấu hình pytest cho phần AI. Chạy từ gốc repo: pytest tests/intelligence -q"""
import sys
from pathlib import Path

import pandas as pd
import pytest

SERVICE = Path(__file__).resolve().parents[2] / "services" / "intelligence"
sys.path.insert(0, str(SERVICE))

from src.utils import config  # noqa: E402


def _need(path):
    if not Path(path).exists():
        pytest.skip(f"Thiếu {path}. Chạy trước: python scripts/run_pipeline.py")


@pytest.fixture(scope="session")
def panel():
    _need(config.DAILY_SALES)
    return pd.read_csv(config.DAILY_SALES, parse_dates=["date"], dtype={"store_id": str, "sku_id": str})


@pytest.fixture(scope="session")
def products():
    from src.data.load_data import load_products
    return load_products()


@pytest.fixture(scope="session")
def service():
    from src.models.train_lightgbm import BUNDLE_PATH
    _need(BUNDLE_PATH)
    from src.inference.service import IntelligenceService
    return IntelligenceService()


@pytest.fixture
def tiny_panel():
    """Panel nhỏ 1 chuỗi, 60 ngày, có 1 ngày missing và 1 ngày stockout."""
    d = pd.date_range("2026-01-01", periods=60, freq="D")
    sales = [float(10 + (i % 7)) for i in range(60)]
    df = pd.DataFrame({"date": d, "store_id": "S001", "sku_id": "SKU001", "sales": sales,
                       "is_missing": 0, "is_stockout": 0, "is_promo": 0, "discount_pct": 0.0,
                       "category": "fresh_produce"})
    df.loc[20, ["sales", "is_missing"]] = [float("nan"), 1]
    df.loc[30, "is_stockout"] = 1
    return df

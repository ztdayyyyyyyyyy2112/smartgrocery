"""Đọc dữ liệu gốc (data/raw) với kiểu dữ liệu nhất quán."""
from __future__ import annotations

import pandas as pd

from src.utils import config


def load_raw_transactions(path=config.RAW_TRANSACTIONS) -> pd.DataFrame:
    # Đọc tất cả dạng chuỗi trước để tự kiểm soát việc ép kiểu ở bước cleaning
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])


def load_products(path=config.RAW_PRODUCTS) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"sku_id": str})
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    return df


def load_stores(path=config.RAW_STORES) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str)


def load_assortment(path=config.RAW_ASSORTMENT) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, parse_dates=["listed_from"])


def load_store_calendar(path=config.RAW_STORE_CALENDAR) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"store_id": str, "status": str}, parse_dates=["date"])


def load_holidays(path=config.RAW_HOLIDAYS) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"])


def load_promotions(path=config.RAW_PROMOTIONS) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"store_id": str, "sku_id": str},
                       parse_dates=["start_date", "end_date"])


def load_inventory(path=config.RAW_INVENTORY) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"store_id": str, "sku_id": str}, parse_dates=["date"])

"""Làm sạch giao dịch POS.

Quy tắc (đã ghi trong docs/data_dictionary.md):
  1. Chuẩn hóa tên cột -> date, store_id, sku_id, quantity_sold, unit_price, transaction_type.
  2. Chuẩn hóa mã: strip khoảng trắng, viết hoa (sku001 -> SKU001).
  3. Loại dòng có ngày không parse được hoặc thiếu store_id/sku_id (không tự đoán mã).
  4. Loại trùng theo transaction_id (KHÔNG loại trùng theo date/store/sku vì một ngày
     có nhiều giao dịch hợp lệ).
  5. Bài toán dự báo GROSS demand: tách giao dịch RETURN (số âm) ra khỏi demand,
     giữ thống kê để báo cáo. Không đổi số âm thành dương.
  6. Dòng có số lượng >= BULK_ORDER_QTY coi là đơn sỉ B2B -> loại khỏi demand B2C, ghi log.
  7. Loại SKU/store không có trong master data.
"""
from __future__ import annotations

import pandas as pd

from src.utils import config

RENAME = {
    "Date": "date", "Store": "store_id", "Product": "sku_id", "Quantity": "quantity_sold",
    "UnitPrice": "unit_price", "TransactionType": "transaction_type",
}


def clean_transactions(raw: pd.DataFrame, valid_skus: set[str], valid_stores: set[str]) -> tuple[pd.DataFrame, dict]:
    df = raw.rename(columns=RENAME).copy()
    report: dict = {"raw_rows": int(len(df))}

    df["store_id"] = df["store_id"].astype("string").str.strip().str.upper()
    df["sku_id"] = df["sku_id"].astype("string").str.strip().str.upper()
    df["transaction_type"] = df["transaction_type"].astype("string").str.strip().str.upper()
    df["datetime"] = pd.to_datetime(df["date"], errors="coerce", format="%Y-%m-%d %H:%M:%S")
    df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    report["invalid_date_rows"] = int(df["datetime"].isna().sum())
    report["missing_sku_rows"] = int(df["sku_id"].isna().sum())
    report["missing_store_rows"] = int(df["store_id"].isna().sum())
    report["invalid_quantity_rows"] = int(df["quantity_sold"].isna().sum())
    df = df.dropna(subset=["datetime", "store_id", "sku_id", "quantity_sold"])

    unknown = ~df["sku_id"].isin(valid_skus) | ~df["store_id"].isin(valid_stores)
    report["unknown_sku_or_store_rows"] = int(unknown.sum())
    df = df[~unknown]

    report["duplicate_transaction_rows"] = int(df.duplicated(subset=["transaction_id"]).sum())
    df = df.drop_duplicates(subset=["transaction_id"], keep="first")

    is_return = (df["transaction_type"] == "RETURN") | (df["quantity_sold"] < 0)
    report["return_rows"] = int(is_return.sum())
    report["return_units"] = float(-df.loc[is_return, "quantity_sold"].sum())
    df = df[~is_return]

    bulk = df["quantity_sold"] >= config.BULK_ORDER_QTY
    report["bulk_b2b_rows"] = int(bulk.sum())
    report["bulk_b2b_units"] = float(df.loc[bulk, "quantity_sold"].sum())
    df = df[~bulk]

    df["date"] = df["datetime"].dt.normalize()
    df = df[["transaction_id", "datetime", "date", "store_id", "sku_id",
             "quantity_sold", "unit_price"]].sort_values(["store_id", "sku_id", "datetime"])
    report["clean_rows"] = int(len(df))
    return df.reset_index(drop=True), report

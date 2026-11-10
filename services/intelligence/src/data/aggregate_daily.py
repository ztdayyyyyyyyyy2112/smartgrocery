"""Tổng hợp giao dịch sạch thành panel Store–SKU–Day.

Phân biệt 3 trạng thái (mục 5.6 hướng dẫn):
  * zero-sales : cửa hàng MỞ CỬA, SKU ĐANG KINH DOANH, không có giao dịch -> sales = 0
  * missing    : cửa hàng đóng cửa / sự cố POS -> sales = NaN, is_missing = 1 (KHÔNG điền 0)
  * stockout   : tồn kho cuối ngày = 0 -> doanh số bị chặn (censored), is_stockout = 1.
                 Ngày stockout không dùng làm target khi train/đánh giá.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def aggregate_store_sku_day(clean: pd.DataFrame, assortment: pd.DataFrame, store_calendar: pd.DataFrame,
                            inventory: pd.DataFrame, promotions: pd.DataFrame, products: pd.DataFrame,
                            end_date: pd.Timestamp | None = None) -> pd.DataFrame:
    end_date = pd.Timestamp(end_date or store_calendar["date"].max())

    daily = (clean.assign(revenue=clean["quantity_sold"] * clean["unit_price"])
             .groupby(["date", "store_id", "sku_id"], as_index=False)
             .agg(sales=("quantity_sold", "sum"), n_transactions=("transaction_id", "count"),
                  revenue=("revenue", "sum")))
    daily["avg_unit_price"] = daily["revenue"] / daily["sales"].where(daily["sales"] > 0)

    # Khung lịch đầy đủ cho mỗi Store–SKU từ ngày bắt đầu kinh doanh
    frames = []
    for r in assortment.itertuples(index=False):
        d = pd.date_range(r.listed_from, end_date, freq="D")
        frames.append(pd.DataFrame({"date": d, "store_id": r.store_id, "sku_id": r.sku_id}))
    panel = pd.concat(frames, ignore_index=True)

    panel = panel.merge(store_calendar.rename(columns={"status": "store_status"}),
                        on=["store_id", "date"], how="left")
    panel["store_status"] = panel["store_status"].fillna("unknown")
    panel = panel.merge(daily, on=["date", "store_id", "sku_id"], how="left")

    is_open = panel["store_status"].eq("open")
    panel["is_missing"] = (~is_open).astype(int)
    # zero-sales chỉ khi có căn cứ: cửa hàng mở và SKU đang được kinh doanh
    panel["sales"] = np.where(is_open, panel["sales"].fillna(0.0), np.nan)
    panel["n_transactions"] = np.where(is_open, panel["n_transactions"].fillna(0), np.nan)

    inv = inventory[["date", "store_id", "sku_id", "closing_stock"]]
    panel = panel.merge(inv, on=["date", "store_id", "sku_id"], how="left")
    panel["is_stockout"] = ((panel["closing_stock"] == 0) & is_open).astype(int)

    panel = add_promotions(panel, promotions)
    panel = panel.merge(products[["sku_id", "category"]], on="sku_id", how="left")
    panel = panel.drop(columns=["revenue"]).sort_values(["store_id", "sku_id", "date"]).reset_index(drop=True)
    return panel


def add_promotions(frame: pd.DataFrame, promotions: pd.DataFrame) -> pd.DataFrame:
    """Gắn discount_pct theo ngày (khuyến mãi là kế hoạch đã biết trước -> dùng được cho tương lai)."""
    rows = []
    for p in promotions.itertuples(index=False):
        for d in pd.date_range(p.start_date, p.end_date, freq="D"):
            rows.append((p.store_id, p.sku_id, d, p.discount_pct))
    promo_daily = (pd.DataFrame(rows, columns=["store_id", "sku_id", "date", "discount_pct"])
                   .groupby(["store_id", "sku_id", "date"], as_index=False)["discount_pct"].max())
    out = frame.drop(columns=[c for c in ("discount_pct", "is_promo") if c in frame], errors="ignore")
    out = out.merge(promo_daily, on=["store_id", "sku_id", "date"], how="left")
    out["discount_pct"] = out["discount_pct"].fillna(0.0)
    out["is_promo"] = (out["discount_pct"] > 0).astype(int)
    return out


def validate_daily(panel: pd.DataFrame) -> dict:
    """Kiểm tra mục 5.7. Raise AssertionError nếu vi phạm."""
    assert panel["date"].notna().all(), "date null"
    assert panel["store_id"].notna().all(), "store_id null"
    assert panel["sku_id"].notna().all(), "sku_id null"
    assert not panel.duplicated(["date", "store_id", "sku_id"]).any(), "duplicate Store-SKU-Day key"
    assert (panel["sales"].dropna() >= 0).all(), "negative sales after cleaning"
    assert panel.loc[panel["is_missing"] == 1, "sales"].isna().all(), "missing day was filled with a value"
    return {
        "panel_rows": int(len(panel)),
        "series": int(panel.groupby(["store_id", "sku_id"]).ngroups),
        "date_min": str(panel["date"].min().date()),
        "date_max": str(panel["date"].max().date()),
        "missing_days": int(panel["is_missing"].sum()),
        "zero_sales_days": int((panel["sales"] == 0).sum()),
        "stockout_days": int(panel["is_stockout"].sum()),
        "promo_days": int(panel["is_promo"].sum()),
    }

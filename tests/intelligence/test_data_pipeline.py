import pandas as pd

from src.data.clean_data import clean_transactions
from src.data.aggregate_daily import validate_daily


def _raw():
    return pd.DataFrame({
        "transaction_id": ["T1", "T1", "T2", "T3", "T4", "T5", "T6", "T7"],
        "Date": ["2026-01-01 10:00:00", "2026-01-01 10:00:00", "2026-01-01 11:00:00", "N/A",
                 "2026-01-02 09:00:00", "2026-01-02 09:30:00", "2026-01-02 10:00:00", "2026-01-02 11:00:00"],
        "Store": ["S001"] * 8,
        "Product": ["SKU001", "SKU001", " sku001 ", "SKU001", None, "SKU001", "SKU001", "SKU001"],
        "Quantity": ["2", "2", "3", "1", "1", "-1", "250", "4"],
        "UnitPrice": ["1000"] * 8,
        "TransactionType": ["SALE", "SALE", "SALE", "SALE", "SALE", "RETURN", "SALE", "SALE"],
    })


def test_cleaning_rules():
    clean, rep = clean_transactions(_raw(), {"SKU001"}, {"S001"})
    assert rep["duplicate_transaction_rows"] == 1          # T1 trùng transaction_id
    assert rep["invalid_date_rows"] == 1                    # "N/A"
    assert rep["missing_sku_rows"] == 1
    assert rep["return_rows"] == 1 and rep["return_units"] == 1
    assert rep["bulk_b2b_rows"] == 1                        # 250 >= BULK_ORDER_QTY
    assert set(clean["sku_id"]) == {"SKU001"}               # " sku001 " đã chuẩn hóa
    assert (clean["quantity_sold"] > 0).all()
    assert clean["quantity_sold"].sum() == 2 + 3 + 4


def test_same_day_multiple_transactions_not_deduplicated():
    clean, _ = clean_transactions(_raw(), {"SKU001"}, {"S001"})
    assert (clean["date"] == "2026-01-01").sum() == 2       # T1 + T2 cùng ngày đều giữ


def test_panel_integrity(panel):
    summary = validate_daily(panel)
    assert summary["series"] >= 90
    assert not panel.duplicated(["date", "store_id", "sku_id"]).any()


def test_missing_days_not_filled_with_zero(panel):
    closed = panel[panel["store_status"] != "open"]
    assert len(closed) > 0
    assert closed["sales"].isna().all()
    # Lỗi POS S002 10–12/03/2026 phải là missing, không phải zero-sales
    outage = panel[(panel.store_id == "S002") & (panel.date.between("2026-03-10", "2026-03-12"))]
    assert outage["sales"].isna().all() and (outage["is_missing"] == 1).all()


def test_zero_sales_only_on_open_days(panel):
    zeros = panel[panel["sales"] == 0]
    assert (zeros["store_status"] == "open").all()


def test_series_start_at_listing_date(panel):
    new = panel[panel.sku_id == "SKU032"]
    assert new["date"].min() == pd.Timestamp("2026-11-05")

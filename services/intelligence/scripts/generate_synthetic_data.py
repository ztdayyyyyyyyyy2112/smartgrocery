"""Sinh bộ dữ liệu bán lẻ tổng hợp (synthetic) cho SmartGrocery.

LÝ DO DÙNG DỮ LIỆU TỔNG HỢP (xem docs/dataset_source.md):
  - Đồ án cần đủ các trường mà dataset công khai thường thiếu cùng lúc:
    tồn kho theo ngày (để đánh dấu stockout), lead time, MOQ, pack size,
    giá vốn, hạn sử dụng, lịch đóng cửa (phân biệt zero-sales và missing).
  - Dữ liệu được sinh có kiểm soát, seed cố định -> tái lập 100%.
  - Mô phỏng hành vi siêu thị mini tại TP.HCM: chu kỳ tuần, Tết Nguyên đán,
    ngày lễ, ngày lương, khuyến mãi, tăng giá, hết hàng do nhà cung cấp giao trễ,
    SKU bán thưa, SKU mới, sự cố POS, giao dịch trả hàng, dòng trùng, lỗi nhập liệu.

Đây KHÔNG phải dữ liệu thật của cửa hàng nào. Mọi số liệu chi phí là giả định demo.

Chạy:  python scripts/generate_synthetic_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import config  # noqa: E402

SEED = 42
START = pd.Timestamp("2024-11-01")
END = pd.Timestamp("2026-11-09")          # ngày dữ liệu cuối cùng (as-of)
FUTURE_END = pd.Timestamp("2026-11-30")   # khuyến mãi đã lên kế hoạch đến hết tháng 11

TET = {2025: pd.Timestamp("2025-01-29"), 2026: pd.Timestamp("2026-02-17")}

STORES = pd.DataFrame([
    ("S001", "SmartGrocery Quận 1", "Quận 1, TP.HCM", 1.15),
    ("S002", "SmartGrocery Thủ Đức", "TP. Thủ Đức, TP.HCM", 1.00),
    ("S003", "SmartGrocery Bình Thạnh", "Quận Bình Thạnh, TP.HCM", 0.85),
], columns=["store_id", "store_name", "address", "_factor"])

# sku, name, category, base_daily, price, cost, pack, moq, lead_time, shelf_life, launch
P = [
    ("SKU001", "Rau muống 500g", "fresh_produce", 26, 12000, 8000, 10, 20, 1, 3, None),
    ("SKU002", "Cà chua 1kg", "fresh_produce", 16, 35000, 24000, 10, 20, 1, 7, None),
    ("SKU003", "Chuối 1kg", "fresh_produce", 14, 30000, 21000, 10, 10, 2, 6, None),
    ("SKU004", "Táo nhập khẩu 1kg", "fresh_produce", 3, 180000, 128000, 6, 12, 10, 30, None),
    ("SKU005", "Sữa tươi tiệt trùng 1L", "dairy", 22, 34000, 26500, 12, 24, 2, 30, None),
    ("SKU006", "Sữa chua lốc 4 hộp", "dairy", 18, 28000, 21000, 12, 24, 2, 20, None),
    ("SKU007", "Phô mai lát 10 miếng", "dairy", 2.5, 75000, 56000, 6, 6, 3, 60, None),
    ("SKU008", "Thịt heo ba rọi 500g", "meat_seafood", 12, 85000, 66000, 5, 10, 1, 3, None),
    ("SKU009", "Ức gà phi lê 500g", "meat_seafood", 9, 55000, 42000, 5, 10, 1, 3, None),
    ("SKU010", "Cá basa phi lê 500g", "meat_seafood", 6, 60000, 45000, 5, 10, 2, 4, None),
    ("SKU011", "Trứng gà hộp 10 quả", "eggs", 20, 38000, 30000, 10, 20, 2, 21, None),
    ("SKU012", "Bánh mì sandwich 400g", "bakery", 11, 25000, 17000, 10, 10, 1, 4, None),
    ("SKU013", "Gạo thơm 5kg", "rice_grains", 6, 165000, 135000, 4, 8, 3, 365, None),
    ("SKU014", "Mì gói tôm chua cay", "instant_food", 45, 4500, 3400, 30, 60, 3, 180, None),
    ("SKU015", "Phở ăn liền", "instant_food", 12, 9000, 6800, 24, 48, 3, 180, None),
    ("SKU016", "Nước suối 500ml", "beverages", 40, 6000, 3900, 24, 48, 2, 365, None),
    ("SKU017", "Nước ngọt lon 330ml", "beverages", 30, 11000, 8000, 24, 48, 2, 270, None),
    ("SKU018", "Trà xanh chai 455ml", "beverages", 24, 10000, 7200, 24, 48, 2, 270, None),
    ("SKU019", "Cà phê hòa tan hộp 18 gói", "beverages", 5, 62000, 47000, 12, 12, 4, 365, None),
    ("SKU020", "Bia lon 330ml lốc 6", "beverages", 8, 105000, 86000, 4, 8, 3, 270, None),
    ("SKU021", "Snack khoai tây 50g", "snacks", 14, 12000, 8500, 20, 40, 3, 180, None),
    ("SKU022", "Bánh quy hộp 300g", "snacks", 4, 69000, 50000, 12, 12, 5, 270, None),
    ("SKU023", "Nước mắm 500ml", "condiments", 6, 42000, 31000, 12, 12, 4, 540, None),
    ("SKU024", "Dầu ăn 1L", "condiments", 7, 52000, 41000, 12, 12, 4, 540, None),
    ("SKU025", "Đường trắng 1kg", "condiments", 4, 26000, 20000, 10, 10, 4, 720, None),
    ("SKU026", "Nước rửa chén 750ml", "household", 5, 36000, 26000, 12, 12, 5, 900, None),
    ("SKU027", "Bột giặt 3kg", "household", 3, 145000, 112000, 4, 4, 5, 900, None),
    ("SKU028", "Giấy vệ sinh lốc 10 cuộn", "household", 6, 78000, 59000, 6, 6, 5, 900, None),
    ("SKU029", "Kem đánh răng 180g", "personal_care", 3, 39000, 28000, 12, 12, 5, 720, None),
    ("SKU030", "Dầu gội 650ml", "personal_care", 1.2, 135000, 98000, 6, 6, 5, 900, None),
    ("SKU031", "Kim chi cải thảo 500g", "fresh_produce", 5, 45000, 31000, 10, 10, 2, 21, "2026-09-14"),
    ("SKU032", "Nước ép trái cây 1L", "beverages", 6, 48000, 34000, 12, 12, 3, 90, "2026-11-05"),
]
PRODUCTS = pd.DataFrame(P, columns=[
    "sku_id", "product_name", "category", "_base", "unit_price", "purchase_cost",
    "pack_size", "moq", "lead_time_days", "shelf_life_days", "launch_date"])
PRODUCTS["launch_date"] = PRODUCTS["launch_date"].astype(object).where(PRODUCTS["launch_date"].notna(), None)

# Hệ số thứ trong tuần (Mon..Sun)
DOW = {
    "default": [0.92, 0.90, 0.93, 0.97, 1.05, 1.20, 1.13],
    "beverages": [0.88, 0.86, 0.90, 0.95, 1.08, 1.27, 1.16],
    "bakery": [1.04, 1.00, 1.00, 1.00, 1.00, 0.98, 0.98],
    "household": [0.85, 0.85, 0.90, 0.95, 1.05, 1.30, 1.20],
}
TET_SENSITIVE = {"snacks": 2.6, "beverages": 1.8, "condiments": 1.7, "meat_seafood": 1.6,
                 "rice_grains": 1.5, "fresh_produce": 1.4, "eggs": 1.3, "dairy": 1.2,
                 "household": 1.4, "personal_care": 1.2, "instant_food": 1.1, "bakery": 1.0}
PROMO_CATS = {"beverages", "snacks", "instant_food", "dairy", "household", "personal_care", "condiments"}
PERISHABLE = {"fresh_produce", "meat_seafood", "bakery"}


def holidays_table() -> pd.DataFrame:
    rows = []
    for y in (2024, 2025, 2026, 2027):
        rows += [(f"{y}-01-01", "Tết Dương lịch", "public"),
                 (f"{y}-04-30", "Ngày Giải phóng miền Nam", "public"),
                 (f"{y}-05-01", "Quốc tế Lao động", "public"),
                 (f"{y}-09-02", "Quốc khánh", "public")]
    for y, d in TET.items():
        for k in range(-1, 4):
            rows.append(((d + pd.Timedelta(days=k)).strftime("%Y-%m-%d"),
                         "Giao thừa" if k == -1 else f"Tết Nguyên đán mùng {k + 1}", "tet"))
    # Giỗ Tổ Hùng Vương (âm lịch 10/3)
    rows += [("2025-04-07", "Giỗ Tổ Hùng Vương", "public"), ("2026-04-26", "Giỗ Tổ Hùng Vương", "public")]
    df = pd.DataFrame(rows, columns=["date", "holiday_name", "holiday_type"])
    df["date"] = pd.to_datetime(df["date"])
    return df[(df.date >= START) & (df.date <= pd.Timestamp("2027-12-31"))].sort_values("date").reset_index(drop=True)


def store_calendar(dates: pd.DatetimeIndex) -> pd.DataFrame:
    rows = []
    closed = set()
    for d in TET.values():
        closed |= {d, d + pd.Timedelta(days=1)}          # đóng cửa mùng 1–2
    reno = set(pd.date_range("2025-08-04", "2025-08-06"))  # S003 sửa chữa
    outage = set(pd.date_range("2026-03-10", "2026-03-12"))  # S002 lỗi POS (mở cửa nhưng mất dữ liệu)
    for s in STORES.store_id:
        for d in dates:
            st = "open"
            if d in closed:
                st = "closed_holiday"
            elif s == "S003" and d in reno:
                st = "closed_renovation"
            elif s == "S002" and d in outage:
                st = "pos_outage"
            rows.append((s, d, st))
    return pd.DataFrame(rows, columns=["store_id", "date", "status"])


def assortment() -> pd.DataFrame:
    rows = []
    for s in STORES.store_id:
        for _, p in PRODUCTS.iterrows():
            if s == "S003" and p.sku_id == "SKU004":
                continue  # S003 không kinh doanh táo nhập khẩu
            listed = p.launch_date if isinstance(p.launch_date, str) else START.strftime("%Y-%m-%d")
            if s == "S003" and p.sku_id == "SKU031":
                listed = "2026-10-01"  # S003 nhận SKU mới muộn hơn
            rows.append((s, p.sku_id, listed))
    df = pd.DataFrame(rows, columns=["store_id", "sku_id", "listed_from"])
    df["listed_from"] = pd.to_datetime(df["listed_from"])
    return df


def promotions(rng: np.random.Generator, asso: pd.DataFrame) -> pd.DataFrame:
    rows, pid = [], 1
    for _, a in asso.iterrows():
        cat = PRODUCTS.set_index("sku_id").loc[a.sku_id, "category"]
        if cat not in PROMO_CATS:
            continue
        d = max(a.listed_from, START) + pd.Timedelta(days=int(rng.integers(5, 40)))
        while d < FUTURE_END:
            length = int(rng.choice([3, 5, 7, 7, 10]))
            disc = float(rng.choice([0.10, 0.15, 0.20, 0.25, 0.30]))
            rows.append((f"PR{pid:05d}", a.store_id, a.sku_id, d, d + pd.Timedelta(days=length - 1), disc))
            pid += 1
            d = d + pd.Timedelta(days=length + int(rng.integers(30, 75)))
    df = pd.DataFrame(rows, columns=["promo_id", "store_id", "sku_id", "start_date", "end_date", "discount_pct"])
    # Đảm bảo có vài khuyến mãi trong tuần dự báo (10–16/11/2026) để demo
    extra = [("S001", "SKU017", "2026-11-12", "2026-11-16", 0.20),
             ("S002", "SKU014", "2026-11-13", "2026-11-15", 0.15),
             ("S001", "SKU006", "2026-11-11", "2026-11-14", 0.25)]
    for s, k, a_, b_, disc in extra:
        df = df[~((df.store_id == s) & (df.sku_id == k) & (df.end_date >= a_) & (df.start_date <= b_))]
        df.loc[len(df)] = (f"PR{pid:05d}", s, k, pd.Timestamp(a_), pd.Timestamp(b_), disc)
        pid += 1
    return df.sort_values(["store_id", "sku_id", "start_date"]).reset_index(drop=True)


def demand_multiplier(dates: pd.DatetimeIndex, cat: str) -> np.ndarray:
    dow = np.array(DOW.get(cat, DOW["default"]))[dates.dayofweek]
    doy = dates.dayofyear.values
    if cat == "beverages":
        season = 1 + 0.15 * np.sin(2 * np.pi * (doy - 60) / 365)   # nóng tháng 3–5
    elif cat == "fresh_produce":
        season = 1 + 0.06 * np.sin(2 * np.pi * (doy - 200) / 365)
    else:
        season = 1 + 0.03 * np.sin(2 * np.pi * doy / 365)
    payday = np.where(np.isin(dates.day, [1, 2, 3, 4, 5, 15, 16]), 1.05, 1.0)
    trend = 1 + 0.08 * (dates - START).days.values / 365
    tet = np.ones(len(dates))
    peak = TET_SENSITIVE.get(cat, 1.2)
    for d in TET.values():
        delta = (dates - d).days.values
        pre = (delta >= -14) & (delta <= -1)
        tet[pre] = 1 + (peak - 1) * (15 + delta[pre]) / 14          # tăng dần đến giao thừa
        tet[(delta >= 2) & (delta <= 7)] = 0.65                       # sau Tết giảm
    hol = np.ones(len(dates))
    for md in ["04-30", "05-01", "09-02", "01-01"]:
        for y in (2025, 2026):
            dd = pd.Timestamp(f"{y}-{md}")
            delta = (dates - dd).days.values
            hol[(delta >= -2) & (delta <= 0)] *= 1.15
    return dow * season * payday * trend * tet * hol


def simulate(rng: np.random.Generator):
    dates = pd.date_range(START, END, freq="D")
    cal = store_calendar(dates)
    asso = assortment()
    promos = promotions(rng, asso)
    cal_idx = cal.set_index(["store_id", "date"])["status"]

    daily_rows, inv_rows = [], []
    for _, a in asso.iterrows():
        p = PRODUCTS.set_index("sku_id").loc[a.sku_id]
        sf = STORES.set_index("store_id").loc[a.store_id, "_factor"]
        d_idx = dates[dates >= a.listed_from]
        if len(d_idx) == 0:
            continue
        mult = demand_multiplier(d_idx, p.category)
        # Khuyến mãi
        pr = promos[(promos.store_id == a.store_id) & (promos.sku_id == a.sku_id)]
        disc = np.zeros(len(d_idx))
        post = np.ones(len(d_idx))
        for _, r in pr.iterrows():
            m = (d_idx >= r.start_date) & (d_idx <= r.end_date)
            disc[m] = r.discount_pct
            if p.category not in PERISHABLE:
                m2 = (d_idx > r.end_date) & (d_idx <= r.end_date + pd.Timedelta(days=3))
                post[m2] = 0.88                                     # hiệu ứng tích trữ sau KM
        promo_uplift = np.exp(2.6 * disc)
        price_step = np.where(d_idx >= pd.Timestamp("2025-07-01"), 1.04, 1.0)   # tăng giá 4%
        price = np.round(p.unit_price * price_step * (1 - disc), -2)
        elastic = np.where(d_idx >= pd.Timestamp("2025-07-01"), 0.97, 1.0)
        # SKU mới: tăng dần nhận biết trong 30 ngày đầu
        age = (d_idx - a.listed_from).days.values
        ramp = np.clip(0.4 + 0.6 * age / 30, 0.4, 1.0) if isinstance(p.launch_date, str) else 1.0
        mu = p._base * sf * mult * promo_uplift * post * elastic * ramp
        # Negative binomial: SKU thưa có phân tán lớn hơn
        k = 2.0 if p._base < 4 else 6.0
        demand = rng.negative_binomial(k, k / (k + mu))

        # Mô phỏng tồn kho (s, S) có giao trễ ngẫu nhiên -> stockout
        L = int(p.lead_time_days)
        mean_d = p._base * sf
        s_lvl = mean_d * (L + 1) * 1.15
        S_lvl = mean_d * (L + 6)
        stock = S_lvl
        pipeline = {}  # ngày nhận -> số lượng
        on_order = 0.0
        for i, d in enumerate(d_idx):
            status = cal_idx.loc[(a.store_id, d)]
            if d in pipeline:
                q = pipeline.pop(d)
                stock += q
                on_order -= q
            if status in ("closed_holiday", "closed_renovation"):
                continue
            sold = int(min(demand[i], np.floor(stock)))
            stock -= sold
            if stock + on_order <= s_lvl:
                q = max(S_lvl - stock - on_order, p.moq)
                q = np.ceil(q / p.pack_size) * p.pack_size
                delay = L + (int(rng.integers(2, 5)) if rng.random() < 0.06 else 0)
                arr = d + pd.Timedelta(days=delay)
                pipeline[arr] = pipeline.get(arr, 0) + q
                on_order += q
            inv_rows.append((d, a.store_id, a.sku_id, int(stock)))
            if status == "pos_outage":
                continue  # bán thật nhưng POS không ghi nhận -> missing
            daily_rows.append((d, a.store_id, a.sku_id, sold, price[i]))

    daily = pd.DataFrame(daily_rows, columns=["date", "store_id", "sku_id", "qty", "price"])
    inv = pd.DataFrame(inv_rows, columns=["date", "store_id", "sku_id", "closing_stock"])
    return dates, cal, asso, promos, daily, inv


def explode_to_transactions(rng: np.random.Generator, daily: pd.DataFrame) -> pd.DataFrame:
    """Tách doanh số ngày thành các dòng giao dịch POS (nhiều hóa đơn/ngày)."""
    d = daily[daily.qty > 0].reset_index(drop=True)
    n_lines = np.minimum(d.qty.values, 1 + rng.poisson(d.qty.values / 5.0))
    rep = np.repeat(np.arange(len(d)), n_lines)
    out = d.loc[rep, ["date", "store_id", "sku_id", "price"]].reset_index(drop=True)
    qty = np.empty(len(out), dtype=int)
    pos = 0
    for q, n in zip(d.qty.values, n_lines):
        qty[pos:pos + n] = rng.multinomial(q - n, np.ones(n) / n) + 1  # mỗi dòng >= 1
        pos += n
    out["Quantity"] = qty
    secs = rng.integers(7 * 3600, 22 * 3600, len(out))
    out["ts"] = out["date"] + pd.to_timedelta(secs, unit="s")
    out = out.sort_values(["store_id", "ts"]).reset_index(drop=True)
    out["seq"] = out.groupby(["store_id", "date"]).cumcount() + 1
    out["transaction_id"] = (out.store_id + "-" + out.date.dt.strftime("%Y%m%d") + "-"
                             + out.seq.astype(str).str.zfill(4))
    out["TransactionType"] = "SALE"
    return out


def inject_quality_issues(rng: np.random.Generator, tx: pd.DataFrame) -> pd.DataFrame:
    tx = tx.copy()
    n = len(tx)
    # 1) Trả hàng (~0.4%): dòng RETURN số lượng âm, cùng ngày hoặc vài ngày sau
    ridx = rng.choice(n, int(n * 0.004), replace=False)
    ret = tx.loc[ridx].copy()
    ret["Quantity"] = -np.minimum(ret["Quantity"], rng.integers(1, 3, len(ret)))
    ret["ts"] = ret["ts"] + pd.to_timedelta(rng.integers(0, 3, len(ret)), unit="D")
    ret["transaction_id"] = ret["transaction_id"] + "-R"
    ret["TransactionType"] = "RETURN"
    # 2) Đơn sỉ B2B bất thường
    bulk = tx.sample(3, random_state=SEED).copy()
    bulk["Quantity"] = [240, 180, 300]
    bulk["transaction_id"] = bulk["transaction_id"] + "-B2B"
    tx = pd.concat([tx, ret, bulk], ignore_index=True)
    # 3) Dòng trùng hoàn toàn (~0.3%) do đồng bộ POS lỗi
    dup = tx.sample(frac=0.003, random_state=SEED)
    tx = pd.concat([tx, dup], ignore_index=True)
    # Định dạng xuất
    tx["Date"] = tx["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
    tx["Store"] = tx["store_id"]
    tx["Product"] = tx["sku_id"]
    tx["UnitPrice"] = tx["price"].astype(int)
    # 4) Mã SKU viết thường / có khoảng trắng
    m = rng.choice(len(tx), 400, replace=False)
    tx.loc[m[:200], "Product"] = tx.loc[m[:200], "Product"].str.lower()
    tx.loc[m[200:], "Product"] = " " + tx.loc[m[200:], "Product"] + " "
    # 5) Ngày lỗi & thiếu mã SKU
    bad = rng.choice(len(tx), 60, replace=False)
    tx.loc[bad[:30], "Date"] = rng.choice(["N/A", "2025-13-45 10:00:00", ""], 30)
    tx.loc[bad[30:], "Product"] = np.nan
    tx = tx.sample(frac=1.0, random_state=SEED).reset_index(drop=True)  # POS export không sắp xếp
    return tx[["transaction_id", "Date", "Store", "Product", "Quantity", "UnitPrice", "TransactionType"]]


def main() -> None:
    rng = np.random.default_rng(SEED)
    config.ensure_dirs()
    dates, cal, asso, promos, daily, inv = simulate(rng)
    tx = explode_to_transactions(rng, daily)
    tx = inject_quality_issues(rng, tx)

    STORES.drop(columns="_factor").to_csv(config.RAW_STORES, index=False)
    PRODUCTS.drop(columns="_base").to_csv(config.RAW_PRODUCTS, index=False)
    asso.to_csv(config.RAW_ASSORTMENT, index=False, date_format="%Y-%m-%d")
    cal.to_csv(config.RAW_STORE_CALENDAR, index=False, date_format="%Y-%m-%d")
    holidays_table().to_csv(config.RAW_HOLIDAYS, index=False, date_format="%Y-%m-%d")
    promos.to_csv(config.RAW_PROMOTIONS, index=False, date_format="%Y-%m-%d")
    inv.to_csv(config.RAW_INVENTORY, index=False, date_format="%Y-%m-%d", compression="gzip")
    tx.to_csv(config.RAW_TRANSACTIONS, index=False, compression="gzip")

    print(f"Transactions: {len(tx):,} rows | Stores: {len(STORES)} | SKUs: {len(PRODUCTS)}")
    print(f"Period: {START.date()} -> {END.date()} ({len(dates)} days)")
    print(f"Promotions: {len(promos)} | Inventory rows: {len(inv):,}")
    print(f"Stockout days (closing_stock==0): {(inv.closing_stock == 0).mean():.2%}")


if __name__ == "__main__":
    main()

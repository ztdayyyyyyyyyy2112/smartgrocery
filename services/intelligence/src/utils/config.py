"""Cấu hình tập trung cho SmartGrocery Intelligence.

Mọi đường dẫn đều tính tương đối từ thư mục services/intelligence/ để
chạy được trên Windows/Linux/macOS mà không cần sửa code.
Có thể ghi đè bằng biến môi trường (xem .env.example).
"""
from __future__ import annotations

import os
from pathlib import Path

# services/intelligence/
SERVICE_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = Path(os.getenv("SG_DATA_DIR", SERVICE_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

ARTIFACTS_DIR = Path(os.getenv("SG_ARTIFACTS_DIR", SERVICE_ROOT / "artifacts"))
MODEL_DIR = ARTIFACTS_DIR / "models"
EVAL_DIR = ARTIFACTS_DIR / "evaluation"
FORECAST_DIR = ARTIFACTS_DIR / "forecasts"
LOG_DIR = ARTIFACTS_DIR / "logs"

# Thư mục docs/ ở gốc repository (dùng để xuất metrics & biểu đồ cho báo cáo)
REPO_ROOT = SERVICE_ROOT.parents[1]
DOCS_EVAL_DIR = REPO_ROOT / "docs" / "evaluation"

# ---- File dữ liệu ----
RAW_TRANSACTIONS = RAW_DIR / "pos_transactions.csv.gz"
RAW_PRODUCTS = RAW_DIR / "products.csv"
RAW_STORES = RAW_DIR / "stores.csv"
RAW_ASSORTMENT = RAW_DIR / "store_assortment.csv"
RAW_STORE_CALENDAR = RAW_DIR / "store_calendar.csv"
RAW_HOLIDAYS = RAW_DIR / "holidays_vn.csv"
RAW_PROMOTIONS = RAW_DIR / "promotions.csv"
RAW_INVENTORY = RAW_DIR / "inventory_daily.csv.gz"

CLEAN_TRANSACTIONS = PROCESSED_DIR / "transactions_clean.csv.gz"
DAILY_SALES = PROCESSED_DIR / "daily_sales.csv.gz"           # Store–SKU–Day panel
DATA_QUALITY_REPORT = PROCESSED_DIR / "data_quality_report.json"

# ---- Model ----
MODEL_NAME = "lightgbm"
MODEL_SEMVER = "1.0.0"
HORIZON = 7                     # dự báo t+1 .. t+7 (Direct strategy: 7 model)
RANDOM_STATE = 42

# Backtest: 4 fold rolling-origin, mỗi fold 28 ngày origin
BACKTEST_CUTOFFS = ["2026-08-01", "2026-08-29", "2026-09-26", "2026-10-24"]
BACKTEST_TEST_DAYS = 28
VALID_DAYS = 28                 # validation (early stopping) ngay trước cutoff

# Ngưỡng nghiệp vụ
MIN_HISTORY_DAYS_MODEL = 28     # < 28 ngày quan sát -> LOW confidence
MIN_HISTORY_DAYS_ANY = 7        # < 7 ngày -> INSUFFICIENT_HISTORY (rule fallback)
BULK_ORDER_QTY = 100            # 1 dòng giao dịch >= 100 đơn vị = đơn sỉ B2B, loại khỏi demand B2C
DEFAULT_SERVICE_LEVEL = 0.95
DEFAULT_REVIEW_PERIOD_DAYS = 1
FORECAST_STALE_HOURS = 36       # forecast precomputed quá 36h -> tính lại on-the-fly

API_HOST = os.getenv("SG_AI_HOST", "0.0.0.0")
API_PORT = int(os.getenv("SG_AI_PORT", "8001"))


def ensure_dirs() -> None:
    for d in (RAW_DIR, PROCESSED_DIR, MODEL_DIR, EVAL_DIR, FORECAST_DIR, LOG_DIR, DOCS_EVAL_DIR):
        d.mkdir(parents=True, exist_ok=True)

"""Scheduled forecast refresh (03–05/11): tạo lại forecast 7 ngày cho mọi Store–SKU.

  * Ghi artifacts/forecasts/latest_forecast.csv (ghi file tạm rồi replace -> không hỏng file cũ khi lỗi)
    và bản lưu trữ forecast_<as_of>.csv.
  * Ghi artifacts/forecasts/job_status.json: started/finished, status SUCCESS | DEGRADED | FAILED,
    số chuỗi thành công / fallback / thất bại, model_version.
  * Model không load được -> chạy seasonal naive fallback, status DEGRADED (không dừng job).
  * Lỗi khác -> status FAILED, GIỮ NGUYÊN latest_forecast.csv cũ.

Chạy 1 lần:          python -m src.jobs.refresh_forecasts
Lặp mỗi N giờ (demo): python -m src.jobs.refresh_forecasts --every-hours 24
Tích hợp Celery beat (Backend): gọi src.jobs.refresh_forecasts.run_refresh() trong task.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone

import pandas as pd

from src.data import load_data as L
from src.features.build_features import build_origin_features
from src.models.predict import forecast_all
from src.models.train_lightgbm import BUNDLE_PATH, load_bundle
from src.utils import config
from src.utils.logging_config import get_logger

log = get_logger("intelligence.job", "refresh_job.log")
STATUS_PATH = config.FORECAST_DIR / "job_status.json"
LATEST_PATH = config.FORECAST_DIR / "latest_forecast.csv"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_refresh(as_of: str | None = None, bundle_path=BUNDLE_PATH) -> dict:
    config.ensure_dirs()
    status = {"job": "forecast_refresh", "started_at": _now(), "status": "RUNNING"}
    t0 = time.time()
    log.info("Forecast refresh started")
    try:
        products, promos, hol = L.load_products(), L.load_promotions(), L.load_holidays()
        panel = pd.read_csv(config.DAILY_SALES, parse_dates=["date"], dtype={"store_id": str, "sku_id": str})
        as_of_ts = pd.Timestamp(as_of) if as_of else panel["date"].max()
        resid_p = config.MODEL_DIR / "residual_stats.csv"
        resid = pd.read_csv(resid_p, dtype={"store_id": str, "sku_id": str}) if resid_p.exists() else None
        try:
            bundle, degraded = load_bundle(bundle_path), None
        except Exception as e:  # noqa: BLE001
            bundle, degraded = None, f"MODEL_UNAVAILABLE: {type(e).__name__}: {e}"
            log.error("%s -> seasonal naive fallback", degraded)
        origin = build_origin_features(panel)
        fc = forecast_all(bundle, origin, panel, as_of_ts, promos, hol, products, resid)

        per_series = fc.groupby(["store_id", "sku_id"]).agg(method=("method", "first"),
                                                             nan=("predicted_sales", lambda s: s.isna().any()))
        n_failed = int(per_series["nan"].sum())
        n_fallback = int((per_series["method"] != "model").sum()) - n_failed
        tmp = LATEST_PATH.with_suffix(".tmp")
        fc.to_csv(tmp, index=False)
        os.replace(tmp, LATEST_PATH)
        fc.to_csv(config.FORECAST_DIR / f"forecast_{as_of_ts.date()}.csv", index=False)
        status.update(status="DEGRADED" if degraded else "SUCCESS", error=degraded,
                      as_of_date=str(as_of_ts.date()), model_version=str(fc["model_version"].iloc[0]),
                      n_series=int(len(per_series)), n_success=int(len(per_series)) - n_failed - n_fallback,
                      n_fallback=n_fallback, n_failed=n_failed, n_rows=int(len(fc)))
    except Exception as e:  # noqa: BLE001
        log.exception("Forecast refresh FAILED")
        status.update(status="FAILED", error=f"{type(e).__name__}: {e}")
    status["finished_at"] = _now()
    status["duration_sec"] = round(time.time() - t0, 2)
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Forecast refresh finished: %s", json.dumps(status, ensure_ascii=False))
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--every-hours", type=float, default=None, help="Lặp định kỳ (demo, thay cho cron/Celery)")
    a = ap.parse_args()
    while True:
        run_refresh(a.as_of)
        if not a.every_hours:
            break
        time.sleep(a.every_hours * 3600)


if __name__ == "__main__":
    main()

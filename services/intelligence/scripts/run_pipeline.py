"""Chạy toàn bộ pipeline AI từ đầu đến cuối (tái lập được).

  1. (nếu chưa có) sinh dữ liệu tổng hợp vào data/raw
  2. Làm sạch giao dịch POS
  3. Tổng hợp Store–SKU–Day (zero-sales / missing / stockout)
  4. Feature engineering (Direct 7 horizon)
  5. Backtest rolling-origin 4 fold: Seasonal Naive vs MA-28 vs LightGBM
  6. Residual stats (sigma cho Safety Stock, WAPE cho confidence)
  7. Huấn luyện model cuối + lưu artifact & metadata
  8. Forecast 7 ngày cho mọi Store–SKU (job refresh)
  9. Biểu đồ + metrics.md + kịch bản đề xuất nhập hàng

Chạy (từ services/intelligence):  python scripts/run_pipeline.py
Tùy chọn: --regenerate-data  (sinh lại data/raw)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import load_data as L  # noqa: E402
from src.data.aggregate_daily import aggregate_store_sku_day, validate_daily  # noqa: E402
from src.data.clean_data import clean_transactions  # noqa: E402
from src.evaluation import plots  # noqa: E402
from src.evaluation.backtest import residual_stats, run_backtest  # noqa: E402
from src.evaluation.metrics import metrics_table  # noqa: E402
from src.features.build_features import to_model_matrix  # noqa: E402
from src.models.gbm_backend import backend_name  # noqa: E402
from src.models.train_lightgbm import (categories_from_master, prepare_frames, save_bundle,  # noqa: E402
                                       train_final, train_one)
from src.utils import config  # noqa: E402
from src.utils.logging_config import get_logger  # noqa: E402

log = get_logger("intelligence.pipeline", "pipeline_run.log")
PRED_COLS = {"Seasonal Naive": "pred_seasonal_naive", "MA-28": "pred_ma28", "LightGBM": "pred_lightgbm"}


def segment(df: pd.DataFrame, series_mean: pd.Series) -> pd.Series:
    key = list(zip(df.store_id, df.sku_id))
    mean = pd.Series(key).map(series_mean).to_numpy()
    seg = np.select(
        [df.history_days.to_numpy() < 90, df.t_is_promo.to_numpy() == 1,
         df.zero_share_28.fillna(0).to_numpy() > 0.3, mean >= 15],
        ["SKU mới (<90 ngày)", "Ngày khuyến mãi", "Bán thưa (>30% ngày = 0)", "Bán nhanh (>=15/ngày)"],
        default="Bán vừa/chậm")
    return pd.Series(seg, index=df.index)


def fmt(v, pct=False):
    return "N/A" if v is None or (isinstance(v, float) and np.isnan(v)) else (f"{v:.2f}%" if pct else f"{v:.3f}")


def write_metrics_md(overall, by_h, by_fold, seg, cat, worst, bt_info, path):
    def table(df, cols, pct_cols=("WAPE", "Bias_pct")):
        head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
        rows = ""
        for _, r in df.iterrows():
            cells = []
            for c in cols:
                v = r[c]
                if c in pct_cols:
                    cells.append(fmt(v, True))
                elif isinstance(v, (float, np.floating)) and float(v).is_integer() and c in ("horizon", "fold", "n"):
                    cells.append(str(int(v)))
                elif isinstance(v, (float, np.floating)):
                    cells.append(fmt(float(v)))
                else:
                    cells.append(str(v))
            rows += "| " + " | ".join(cells) + " |\n"
        return head + rows

    lg = overall.set_index("model")
    imp = (1 - lg.loc["LightGBM", "WAPE"] / lg.loc["Seasonal Naive", "WAPE"]) * 100
    verdict = (f"LightGBM giảm WAPE {imp:.1f}% tương đối so với Seasonal Naive trên cùng tập đánh giá."
               if imp > 0 else
               f"LightGBM KHÔNG tốt hơn Seasonal Naive (WAPE cao hơn {-imp:.1f}%). Cần dùng baseline làm fallback.")
    md = f"""# Kết quả đánh giá mô hình (tự sinh bởi scripts/run_pipeline.py)

> Sinh lúc: {bt_info['generated_at']} · Backend GBM: **{bt_info['backend']}** · Model version: `{bt_info['model_version']}`
> Dữ liệu: dataset tổng hợp SmartGrocery (xem docs/dataset_source.md) — kết quả không đại diện cho cửa hàng thật.

## Thiết lập
- Chiến lược: Direct forecasting, 7 model (t+1 … t+7), objective Poisson.
- Backtest rolling-origin {len(config.BACKTEST_CUTOFFS)} fold, cutoff: {', '.join(config.BACKTEST_CUTOFFS)};
  mỗi fold huấn luyện lại, validation {config.VALID_DAYS} ngày ngay trước cutoff (early stopping), test {config.BACKTEST_TEST_DAYS} origin.
- Tập so sánh: dòng có actual quan sát được, **không stockout** (doanh số bị chặn), và cả 3 mô hình đều có dự báo
  → {bt_info['n_eval']:,} điểm Store–SKU–Day–Horizon.
- Số cây cuối cùng theo horizon (median best iteration các fold): {bt_info['n_iter']}.

## 1. So sánh tổng thể

{table(overall, ['model', 'n', 'WAPE', 'RMSE', 'MAE', 'Bias_pct'])}
**Kết luận:** {verdict}

## 2. Theo horizon

{table(by_h.pivot(index='horizon', columns='model', values='WAPE').reset_index().rename_axis(None, axis=1)[['horizon','Seasonal Naive','MA-28','LightGBM']], ['horizon', 'Seasonal Naive', 'MA-28', 'LightGBM'], pct_cols=('Seasonal Naive','MA-28','LightGBM'))}
(giá trị = WAPE %)

## 3. Theo fold (độ ổn định)

{table(by_fold.pivot(index='fold', columns='model', values='WAPE').reset_index().rename_axis(None, axis=1)[['fold','Seasonal Naive','MA-28','LightGBM']], ['fold', 'Seasonal Naive', 'MA-28', 'LightGBM'], pct_cols=('Seasonal Naive','MA-28','LightGBM'))}

## 4. Theo nhóm SKU (mục 8.6)

{table(seg, ['segment', 'model', 'n', 'WAPE', 'RMSE', 'MAE'])}

## 5. Theo category (LightGBM)

{table(cat, ['category', 'n', 'WAPE', 'RMSE', 'MAE', 'Bias_pct'])}

## 6. 10 chuỗi Store–SKU khó dự báo nhất (LightGBM, theo WAPE)

{table(worst, ['store_id', 'sku_id', 'n', 'WAPE', 'MAE'])}

## Biểu đồ
- `model_comparison.png`, `wape_by_horizon.png`, `wape_by_segment.png`,
  `actual_vs_predicted.png`, `feature_importance.png`, `future_forecast_7d.png`, `data_overview.png`

## Giới hạn
- Dữ liệu tổng hợp: quan hệ nhân quả (khuyến mãi, Tết) được mô phỏng nên mô hình học dễ hơn thực tế.
- Ngày stockout bị loại khỏi target → mô hình ước lượng nhu cầu khi đủ hàng, nhưng chưa khôi phục (unconstrain) nhu cầu bị mất.
- SKU bán thưa có WAPE cao với mọi mô hình — đây là đặc tính dữ liệu, không phải lỗi pipeline.
"""
    Path(path).write_text(md, encoding="utf-8")


def run_scenarios(out_json: Path, out_md: Path):
    from src.inference.service import IntelligenceService, ServiceError
    svc = IntelligenceService()
    scenarios = [
        ("1. Sữa tươi sắp hết (CRITICAL)", {"store_id": "S001", "sku_id": "SKU005",
         "inventory": {"on_hand": 22, "on_order": 0, "reserved": 4}, "service_level": 0.95}),
        ("2. Nước suối tồn nhiều (không cần nhập)", {"store_id": "S002", "sku_id": "SKU016",
         "inventory": {"on_hand": 320, "on_order": 48, "reserved": 10}}),
        ("3. Mì gói gần ROP, làm tròn pack 30 / MOQ 60", {"store_id": "S001", "sku_id": "SKU014",
         "inventory": {"on_hand": 150, "on_order": 0, "reserved": 12}}),
        ("4. Táo nhập khẩu lead time 10 ngày > horizon 7", {"store_id": "S001", "sku_id": "SKU004",
         "inventory": {"on_hand": 8, "on_order": 0, "reserved": 0}}),
        ("5. SKU mới 5 ngày lịch sử (rule fallback)", {"store_id": "S002", "sku_id": "SKU032",
         "inventory": {"on_hand": 4, "on_order": 0, "reserved": 0}}),
        ("6. Thịt heo (tươi sống) – chi phí do Backend truyền", {"store_id": "S003", "sku_id": "SKU008",
         "inventory": {"on_hand": 6, "on_order": 0, "reserved": 1}, "lead_time_days": 1,
         "costs": {"selling_price": 85000, "purchase_cost": 66000, "holding_cost_per_unit": 300,
                   "stockout_penalty_per_unit": 8500, "waste_cost_per_unit": 33000}}),
        ("7. Thiếu tham số chi phí → không chạy MEU", {"store_id": "S001", "sku_id": "SKU017",
         "inventory": {"on_hand": 30, "on_order": 0, "reserved": 0},
         "costs": {"selling_price": 11000, "purchase_cost": 8000}}),
        ("8. Reserved > On hand + On order", {"store_id": "S002", "sku_id": "SKU011",
         "inventory": {"on_hand": 5, "on_order": 0, "reserved": 20}}),
        ("9. SKU không tồn tại", {"store_id": "S001", "sku_id": "SKU999",
         "inventory": {"on_hand": 5, "on_order": 0, "reserved": 0}}),
    ]
    results, rows = [], []
    for name, req in scenarios:
        try:
            res = svc.replenishment(req)
            results.append({"scenario": name, "request": req, "response": res})
            rows.append(f"| {name} | {res['status']} | {res['alert_level']} | {res.get('inventory_position')} | "
                        f"{res.get('reorder_point')} | {res.get('rop_order_qty')} | {res.get('suggested_order_qty')} | "
                        f"{res['confidence']} | {', '.join(res['warnings']) or '-'} |")
        except ServiceError as e:
            results.append({"scenario": name, "request": req, "error": {"error_code": e.code, "message": e.message,
                                                                        "http_status": e.http_status}})
            rows.append(f"| {name} | ERROR {e.http_status} {e.code} | - | - | - | - | - | - | - |")
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md = ("# Kịch bản đề xuất nhập hàng (tự sinh)\n\n"
          f"Model: `{svc.model_version}` · Dữ liệu as-of {svc.as_of_default.date()} · Chi tiết request/response: "
          "`recommendation_scenarios.json`\n\n"
          "| Kịch bản | Status | Alert | IP | ROP | Qty theo ROP | Qty đề xuất (MEU) | Confidence | Warnings |\n"
          "|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    out_md.write_text(md, encoding="utf-8")
    log.info("Scenarios written: %d", len(results))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regenerate-data", action="store_true")
    ap.add_argument("--skip-scenarios", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    config.ensure_dirs()
    evidence = config.REPO_ROOT / "docs" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    log.info("=== SmartGrocery AI pipeline | GBM backend: %s ===", backend_name())
    if backend_name() != "lightgbm":
        log.warning("lightgbm chưa được cài -> dùng sklearn HistGradientBoosting. "
                    "Chạy 'pip install lightgbm' rồi chạy lại để có model LightGBM chính thức.")

    if args.regenerate_data or not config.RAW_TRANSACTIONS.exists():
        log.info("[1/9] Sinh dữ liệu tổng hợp")
        import generate_synthetic_data  # noqa: PLC0415
        generate_synthetic_data.main()

    log.info("[2/9] Cleaning")
    products, stores = L.load_products(), L.load_stores()
    promos, hol = L.load_promotions(), L.load_holidays()
    clean, rep = clean_transactions(L.load_raw_transactions(), set(products.sku_id), set(stores.store_id))
    clean.to_csv(config.CLEAN_TRANSACTIONS, index=False, compression="gzip")
    log.info("cleaning report: %s", rep)

    log.info("[3/9] Store–SKU–Day aggregation")
    panel = aggregate_store_sku_day(clean, L.load_assortment(), L.load_store_calendar(), L.load_inventory(),
                                    promos, products)
    summary = validate_daily(panel)
    panel.to_csv(config.DAILY_SALES, index=False, compression="gzip", date_format="%Y-%m-%d")
    config.DATA_QUALITY_REPORT.write_text(json.dumps({"cleaning": rep, "panel": summary}, ensure_ascii=False,
                                                     indent=2), encoding="utf-8")
    log.info("panel summary: %s", summary)

    log.info("[4/9] Feature engineering")
    cats = categories_from_master(products, stores)
    origin, frames = prepare_frames(panel, promos, hol, products)

    log.info("[5/9] Backtest (%d folds x %d horizons)", len(config.BACKTEST_CUTOFFS), config.HORIZON)
    bt, n_iter = run_backtest(frames, cats, logger=log)
    bt.to_csv(config.EVAL_DIR / "backtest_predictions.csv.gz", index=False, compression="gzip")
    ev = bt[(bt.y_ok == 1)].dropna(subset=list(PRED_COLS.values())).copy()
    series_mean = ev.groupby(["store_id", "sku_id"])["y"].mean()
    series_mean.index = list(series_mean.index)
    ev["segment"] = segment(ev, series_mean)
    overall = metrics_table(ev, PRED_COLS)
    by_h = metrics_table(ev, PRED_COLS, ["horizon"])
    by_fold = metrics_table(ev, PRED_COLS, ["fold"])
    seg = metrics_table(ev, {"Seasonal Naive": "pred_seasonal_naive", "LightGBM": "pred_lightgbm"}, ["segment"])
    cat = metrics_table(ev, {"LightGBM": "pred_lightgbm"}, ["category"]).sort_values("WAPE")
    by_sku = metrics_table(ev, {"LightGBM": "pred_lightgbm"}, ["store_id", "sku_id"])
    worst = by_sku.sort_values("WAPE", ascending=False).head(10)
    # LightGBM trên mọi dòng hợp lệ (kể cả SKU mới không có baseline)
    all_ok = metrics_table(bt[bt.y_ok == 1], {"LightGBM (mọi dòng hợp lệ)": "pred_lightgbm"})
    for name, df in [("model_comparison", pd.concat([overall, all_ok])), ("metrics_by_horizon", by_h),
                     ("metrics_by_fold", by_fold), ("metrics_by_segment", seg), ("metrics_by_category", cat),
                     ("metrics_by_store_sku", by_sku)]:
        df.to_csv(config.EVAL_DIR / f"{name}.csv", index=False)
        df.to_csv(config.DOCS_EVAL_DIR / f"{name}.csv", index=False)
    log.info("overall metrics:\n%s", overall.to_string(index=False))

    log.info("[6/9] Residual stats")
    resid = residual_stats(bt, products)
    resid.to_csv(config.MODEL_DIR / "residual_stats.csv", index=False)

    log.info("[7/9] Final training")
    train_end = panel["date"].max()
    bundle = train_final(frames, cats, n_iter, train_end, logger=log)
    lg = overall.set_index("model")
    save_bundle(bundle, {"backtest_metrics": {m: {k: lg.loc[m, k] for k in ("WAPE", "RMSE", "MAE")}
                                              for m in lg.index},
                         "dataset": "SmartGrocery synthetic v1 (seed 42)", "data_as_of": str(train_end.date())})

    log.info("[8/9] Forecast refresh job")
    from src.jobs.refresh_forecasts import LATEST_PATH, run_refresh  # noqa: PLC0415
    st = run_refresh()
    if st["status"] == "FAILED":
        raise RuntimeError(st)
    fc = pd.read_csv(LATEST_PATH, parse_dates=["forecast_date"], dtype={"store_id": str, "sku_id": str})

    log.info("[9/9] Charts, docs, scenarios")
    names = dict(zip(products.sku_id, products.product_name))
    out = lambda n: [config.EVAL_DIR / n, config.DOCS_EVAL_DIR / n]  # noqa: E731
    plots.plot_model_comparison(overall, out("model_comparison.png"))
    plots.plot_metric_by_horizon(by_h, out("wape_by_horizon.png"))
    plots.plot_wape_by_segment(seg, out("wape_by_segment.png"))
    demo = [("S001", "SKU005"), ("S002", "SKU016"), ("S001", "SKU020"), ("S003", "SKU030")]
    plots.plot_actual_vs_pred(bt, demo, names, out("actual_vs_predicted.png"))
    plots.plot_future_forecast(panel, fc, demo[:3], names, out("future_forecast_7d.png"))
    plots.plot_data_overview(panel, out("data_overview.png"))
    # Feature importance: model h=1 của fold cuối, đo trên tập test của fold đó (out-of-sample)
    f1 = frames[1]
    C = pd.Timestamp(config.BACKTEST_CUTOFFS[-1])
    v0 = C - pd.Timedelta(days=config.VALID_DAYS)
    m1 = train_one(f1, cats, f1.target_date < v0, n_estimators=n_iter[1])
    te = f1[(f1.date >= C - pd.Timedelta(days=1)) & (f1.y_ok == 1)]
    imp = m1.feature_importance(to_model_matrix(te, cats), te.y.to_numpy(float))
    imp.to_csv(config.EVAL_DIR / "feature_importance_h1.csv", header=["importance"])
    kind = "gain" if backend_name() == "lightgbm" else "permutation, giảm MAE"
    plots.plot_feature_importance(imp, out("feature_importance.png"), title=f"Feature importance h=1 ({kind})")

    write_metrics_md(overall, by_h, by_fold, seg, cat, worst,
                     {"generated_at": pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").strftime("%Y-%m-%d %H:%M %Z"),
                      "backend": backend_name(), "model_version": bundle["model_version"],
                      "n_eval": int(len(ev)), "n_iter": n_iter},
                     config.DOCS_EVAL_DIR / "metrics.md")
    fc.head(70).to_csv(evidence / "sample_forecast_7d.csv", index=False)
    shutil.copy(config.MODEL_DIR / "model_metadata.json", evidence / "model_metadata.json")
    shutil.copy(config.DATA_QUALITY_REPORT, evidence / "data_quality_report.json")
    shutil.copy(config.FORECAST_DIR / "job_status.json", evidence / "forecast_job_status.json")
    if not args.skip_scenarios:
        run_scenarios(evidence / "recommendation_scenarios.json", evidence / "recommendation_scenarios.md")
    log.info("=== DONE in %.1fs ===", time.time() - t0)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    main()

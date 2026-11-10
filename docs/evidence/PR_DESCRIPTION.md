## Summary
- Data pipeline (cleaning, Store–SKU–Day với phân biệt zero-sales / missing / stockout)
- Seasonal Naive + MA-28 baseline; LightGBM Direct 7 horizon (Poisson), backtest rolling-origin 4 fold
- Forecast 7 ngày, Safety Stock (σ từ residual backtest), Reorder Point, MEU chọn lượng đặt
- Inference: Python module + FastAPI (port 8001), fallback có mã lỗi, scheduled refresh job

## Changes
- Files: `services/intelligence/**`, `docs/{data_dictionary,dataset_source,model_methodology}.md`, `docs/api/ai_contract.md`, `docs/evaluation/**`, `docs/evidence/**`, `tests/**`
- Dataset: SmartGrocery Synthetic Retail v1 (seed 42) — 3 cửa hàng, 32 SKU, 01/11/2024–09/11/2026
- Model/version: `lightgbm-direct-v1.0.0` (xem `artifacts/models/model_metadata.json`)

## How to run
1. `cd services/intelligence && py -m venv .venv && .venv\Scripts\Activate.ps1`
2. `pip install -r requirements.txt`
3. `python scripts/run_pipeline.py`  (preprocess → backtest → train → forecast → charts)
4. `cd ../.. && pytest tests -q`
5. `uvicorn src.inference.api:app --port 8001` → `/docs`

## Test results
- Unit tests: xem `docs/evidence/pytest_log.txt`
- WAPE (backtest 4 fold, 58,004 điểm): Seasonal Naive 56.00% · MA-28 41.11% · LightGBM 37.95%
- RMSE: 13.84 · 10.25 · 9.32 — LightGBM tốt nhất ở cả 7 horizon và 4 fold

## Evidence
- Forecast chart: `docs/evaluation/actual_vs_predicted.png`, `future_forecast_7d.png`
- Evaluation table: `docs/evaluation/metrics.md`, `model_comparison.csv`
- Recommendation scenarios: `docs/evidence/recommendation_scenarios.md`
- Logs: `docs/evidence/pipeline_run.log`, `forecast_job_status.json`

## Limitations
- Dữ liệu tổng hợp; hệ số chi phí MEU là giả định demo
- Lead time > 7 ngày trả HORIZON_INSUFFICIENT (chưa mở rộng horizon)
- Ngày stockout chỉ bị loại khỏi target, chưa unconstrain nhu cầu
- API contract & cách tích hợp (module vs service) chờ Backend xác nhận; chưa sửa docker-compose

# SmartGrocery Intelligence — Data / AI / Optimization

Phụ trách: **Bảo Khoa** · Thư mục: `services/intelligence/`, `docs/`, `tests/`

Dự báo nhu cầu 7 ngày cho từng Store–SKU và đề xuất nhập hàng (Safety Stock → Reorder Point → MEU),
đóng gói thành Python module hoặc FastAPI service để Backend gọi.

```
Raw POS ─► Cleaning ─► Store–SKU–Day ─► Features ─┬─► Seasonal Naive (baseline)
                                                  └─► LightGBM Direct ×7 (t+1..t+7)
                                                          │  backtest 4 fold · WAPE/RMSE/MAE
                                                          ▼
                                   Forecast 7 ngày ─► Safety Stock ─► ROP ─► MEU ─► JSON ─► Backend ─► Dashboard
```

## 1. Cài đặt (Windows PowerShell)

```powershell
cd services/intelligence
py -m venv .venv
.venv\Scripts\Activate.ps1          # bị chặn thì dùng: .venv\Scripts\activate.bat (CMD)
python -m pip install --upgrade pip
pip install -r requirements.txt
python -c "import pandas, numpy, sklearn, lightgbm; print('AI environment OK')"
```
macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`.

## 2. Chạy lại toàn bộ pipeline (≈ 2–3 phút)

```powershell
python scripts/run_pipeline.py --regenerate-data   # bản clone sạch: sinh dữ liệu tổng hợp (seed 42), train và tạo artifact
python scripts/run_pipeline.py                     # chỉ dùng khi đã có data/raw ở máy local
```
Kết quả:

| Đầu ra | Vị trí |
|---|---|
| Dữ liệu sạch, panel Store–SKU–Day | `data/processed/transactions_clean.csv.gz`, `daily_sales.csv.gz` |
| Báo cáo chất lượng dữ liệu | `data/processed/data_quality_report.json` |
| Model artifact (7 model) + metadata | `artifacts/models/forecast_model_bundle.joblib`, `model_metadata.json` |
| Sigma sai số dự báo theo Store–SKU | `artifacts/models/residual_stats.csv` |
| Dự đoán backtest, bảng metrics, biểu đồ | `artifacts/evaluation/` và `docs/evaluation/` |
| Forecast 7 ngày mọi Store–SKU | `artifacts/forecasts/latest_forecast.csv`, `job_status.json` |
| Log | `artifacts/logs/pipeline_run.log`, `refresh_job.log`, `inference.log` |
| Bằng chứng cho báo cáo | `docs/evidence/` |

> Dữ liệu thô, dữ liệu đã xử lý và model artifact là đầu ra local, không được commit vào Git. Sau khi clone, chạy lệnh `--regenerate-data` trước khi chạy test hoặc AI service. Các bảng và biểu đồ trong `docs/evaluation/` là bằng chứng của lần chạy Khoa bàn giao; chạy lại pipeline có thể cập nhật chúng tùy môi trường.

> **Về LightGBM:** code ưu tiên `lightgbm`. Nếu máy chưa cài được, `src/models/gbm_backend.py` tự chuyển sang
> `sklearn HistGradientBoostingRegressor` (cùng họ GBDT histogram), log cảnh báo và đổi `model_version` thành
> `histgb-direct-v1.0.0` để không nhầm. Artifact nộp chính thức phải là `lightgbm-direct-v1.0.0`
> → kiểm tra `artifacts/models/model_metadata.json` trường `"backend": "lightgbm"`.

## 3. Kiểm thử

```powershell
cd ../..                       # gốc repo
pytest tests/intelligence -q   # cần chạy pipeline trước (test dùng artifact)
```

## 4. Chạy AI service

```powershell
uvicorn src.inference.api:app --host 0.0.0.0 --port 8001
# Swagger: http://localhost:8001/docs
```

Hoặc build image độc lập từ bản clone sạch (image tự sinh dữ liệu tổng hợp và huấn luyện model):

```powershell
docker build -t smartgrocery-intelligence .
docker run --rm -p 8001:8001 smartgrocery-intelligence
```

```bash
curl -X POST http://localhost:8001/forecast/replenishment -H "Content-Type: application/json" -d '{
  "store_id": "S001", "sku_id": "SKU005",
  "inventory": {"on_hand": 22, "on_order": 0, "reserved": 4},
  "lead_time_days": 2, "service_level": 0.95 }'
```

Hoặc gọi trực tiếp như Python module (Phương án A):
```python
from src.inference.service import get_service
get_service().replenishment({"store_id": "S001", "sku_id": "SKU005",
                             "inventory": {"on_hand": 22, "on_order": 0, "reserved": 4}})
```

Endpoint: `GET /health` · `GET /model/info` · `GET /forecast/{store_id}/{sku_id}` ·
`POST /forecast/replenishment` · `POST /forecast/replenishment/batch`. Contract đầy đủ: `docs/api/ai_contract.md`.

## 5. Scheduled forecast refresh

```powershell
python -m src.jobs.refresh_forecasts                 # chạy 1 lần
python -m src.jobs.refresh_forecasts --every-hours 24  # demo lặp định kỳ
```
Celery beat (Backend) chỉ cần gọi `src.jobs.refresh_forecasts.run_refresh()`; kết quả ở `artifacts/forecasts/job_status.json`
(`SUCCESS` / `DEGRADED` khi model lỗi và chạy baseline / `FAILED` và giữ forecast cũ).

## 6. Cấu trúc

```
services/intelligence/
├── scripts/generate_synthetic_data.py   # sinh dataset (seed 42)
├── scripts/run_pipeline.py              # chạy end-to-end
├── src/data/        load_data · clean_data · aggregate_daily
├── src/features/    build_features      (lag, rolling, lịch, Tết, khuyến mãi; chống leakage)
├── src/models/      seasonal_naive · gbm_backend · train_lightgbm · predict
├── src/evaluation/  metrics · backtest · plots
├── src/optimization/ safety_stock · reorder_point · meu
├── src/inference/   schemas · service · api
├── src/jobs/        refresh_forecasts
├── src/utils/       config · logging_config
├── data/raw · data/processed · artifacts/
docs/  data_dictionary.md · dataset_source.md · model_methodology.md · api/ai_contract.md · evaluation/ · evidence/
tests/ test_data_pipeline · test_features · test_baseline · test_model · test_optimization · test_inference · test_api
```

## 7. Cần nhóm xác nhận (không tự quyết)

1. Dataset chính thức: hiện dùng dataset tổng hợp (lý do ở `docs/dataset_source.md`).
2. API contract với Tuấn Anh (field, status code, error code).
3. Tích hợp: module trong FastAPI chung (A) hay service riêng port 8001 (B). Chưa sửa `docker-compose.yml`.
4. Service level mặc định 95%, review period 1 ngày, các hệ số chi phí MEU (đang là giả định demo).
5. Định nghĩa `on_hand` khả dụng (đã loại hàng hỏng/khóa/sắp hết hạn?) phía Backend.

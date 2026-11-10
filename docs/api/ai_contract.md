# AI API Contract (ĐỀ XUẤT — cần Tuấn Anh xác nhận)

Service: `services/intelligence` · Base URL nội bộ đề xuất: `http://intelligence:8001` · Swagger: `/docs`
Schema Pydantic nguồn: `services/intelligence/src/inference/schemas.py`. Frontend không gọi trực tiếp; Backend gọi rồi trả cho Dashboard.

## Nguyên tắc
- Backend là nguồn sự thật về `on_hand`, `on_order`, `reserved`. AI không ghi database nghiệp vụ.
- AI chỉ đề xuất: `requires_approval` luôn `true`; PO thật tạo qua luồng phê duyệt của Backend.
- Không trả NaN/Infinity; số lượng dự báo ≥ 0; mọi response có `model_version`, `generated_at`, `status`, `warnings`.

## Endpoints
| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | `{status: ok|degraded, model_loaded, model_version, data_as_of, series}` |
| GET | `/model/info` | Metadata model (features, backend, ngày train, số cây) |
| GET | `/forecast/{store_id}/{sku_id}?horizon=7` | Chỉ dự báo |
| POST | `/forecast/replenishment` | Dự báo + Safety Stock + ROP + MEU |
| POST | `/forecast/replenishment/batch` | Tối đa 500 item; lỗi từng item không làm hỏng cả batch |

## POST /forecast/replenishment

### Request
```json
{
  "store_id": "S001",
  "sku_id": "SKU005",
  "forecast_horizon": 7,
  "inventory": { "on_hand": 22, "on_order": 0, "reserved": 4 },
  "lead_time_days": 2,
  "service_level": 0.95,
  "review_period_days": 1,
  "pack_size": 12,
  "moq": 24,
  "costs": {
    "selling_price": 34000, "purchase_cost": 26500, "holding_cost_per_unit": 127,
    "stockout_penalty_per_unit": 3400, "waste_cost_per_unit": 0
  },
  "use_meu": true,
  "as_of_date": null
}
```
| Field | Bắt buộc | Mặc định | Ràng buộc |
|---|---|---|---|
| store_id, sku_id | ✓ | — | tự strip + upper |
| inventory.on_hand | ✓ | — | ≥ 0 |
| inventory.on_order / reserved | | 0 | ≥ 0 |
| forecast_horizon | | 7 | 1–7 (số ngày trả về; ROP luôn tính trên forecast đầy đủ) |
| lead_time_days | | từ product master | 1–60; > 7 → HORIZON_INSUFFICIENT |
| service_level | | 0.95 | (0.5, 1) |
| review_period_days | | 1 | 0–6 |
| pack_size, moq | | từ product master | |
| costs | | product master (giả định demo) | thiếu bất kỳ field nào trong 5 field → MEU_INPUT_MISSING |
| use_meu | | true | |
| as_of_date | | ngày dữ liệu mới nhất | ≤ ngày dữ liệu mới nhất |

### Response 200 (rút gọn từ kết quả chạy thật)
```json
{
  "store_id": "S001", "sku_id": "SKU005", "product_name": "Sữa tươi tiệt trùng 1L",
  "model_version": "lightgbm-direct-v1.0.0", "forecast_method": "model",
  "generated_at": "2026-11-09T18:52:48+00:00", "as_of_date": "2026-11-09",
  "forecast": [
    {"date": "2026-11-10", "horizon": 1, "predicted_demand": 27.24, "baseline_seasonal_naive": 27.0},
    {"date": "2026-11-11", "horizon": 2, "predicted_demand": 27.88, "baseline_seasonal_naive": 34.0}
  ],
  "forecast_total": 213.85,
  "lead_time_days": 2, "service_level": 0.95, "sigma_daily": 13.84,
  "inventory_position": 18.0, "lead_time_demand": 55.12, "safety_stock": 32.18, "reorder_point": 87.30,
  "rop_order_qty": 72, "suggested_order_qty": 96, "days_of_cover": 0.6,
  "meu": {
    "enabled": true, "cost_source": "product_master_demo_assumption", "recommended_qty": 96,
    "protection_period_days": 3,
    "scenarios": [{"label": "very_low", "probability": 0.2, "demand": 53.2}, "..."],
    "expected_utility": 1101111.35, "expected_utility_reference_qty": 1036955.98,
    "top_candidates": [{"order_qty": 96, "expected_utility": 1101111.35}, "..."]
  },
  "status": "REORDER_RECOMMENDED", "alert_level": "CRITICAL", "confidence": "MEDIUM",
  "requires_approval": true, "warnings": [],
  "explanation": "Tồn khả dụng 18 <= điểm đặt hàng 87.3 ..."
}
```
Response đầy đủ thật của 9 kịch bản: `docs/evidence/recommendation_scenarios.json`.

### Giá trị enum
- `status`: `REORDER_RECOMMENDED` · `NO_REORDER_NEEDED` · `HORIZON_INSUFFICIENT` · `INSUFFICIENT_HISTORY` · `INVENTORY_DATA_CHECK` · `FORECAST_UNAVAILABLE`
- `alert_level`: `CRITICAL` (IP < nhu cầu lead time) · `WARNING` (IP ≤ ROP) · `OK` · `MANUAL_REVIEW`
- `confidence`: `HIGH` · `MEDIUM` · `LOW`
- `warnings[]`: `MODEL_UNAVAILABLE`, `INSUFFICIENT_HISTORY`, `LOW_CONFIDENCE`, `HORIZON_INSUFFICIENT`, `MEU_INPUT_MISSING`,
  `NEGATIVE_INVENTORY_POSITION`, `SIGMA_CATEGORY_CV_FALLBACK`, `SIGMA_POISSON_ASSUMPTION_FALLBACK`

### Lỗi
| HTTP | error_code | Khi nào |
|---|---|---|
| 404 | UNKNOWN_SKU | SKU không có trong product master |
| 404 | UNKNOWN_SERIES | Store không kinh doanh SKU / không có lịch sử |
| 400 | AS_OF_OUT_OF_RANGE | as_of_date sau ngày dữ liệu mới nhất |
| 422 | (FastAPI validation) | Sai kiểu / thiếu field / giá trị âm |
| 500 | INTERNAL_ERROR | Lỗi không lường trước (đã log, service vẫn chạy) |

Body lỗi: `{"error_code": "UNKNOWN_SKU", "message": "SKU SKU999 không có trong product master"}`

## Gợi ý docker-compose (CHƯA áp dụng — chờ Thành xác nhận)
```yaml
  intelligence:
    build: ./services/intelligence
    ports: ["8001:8001"]
    volumes: ["./services/intelligence/artifacts:/app/artifacts"]
    healthcheck: { test: ["CMD", "python", "-c", "import urllib.request;urllib.request.urlopen('http://localhost:8001/health')"] }
```
Backend gọi với timeout 5s; nếu AI không phản hồi, Backend hiển thị "chưa có đề xuất" chứ không chặn luồng đặt hàng thủ công.

# Data Dictionary — SmartGrocery Intelligence

## 1. Dữ liệu gốc (`services/intelligence/data/raw/`)

### pos_transactions.csv.gz — giao dịch POS (248,696 dòng)
| Column | Type | Description | Missing / xử lý |
|---|---|---|---|
| transaction_id | string | Mã dòng giao dịch `<store>-<yyyymmdd>-<seq>`; hậu tố `-R` = trả hàng, `-B2B` = đơn sỉ | Khóa khử trùng (744 dòng trùng bị loại) |
| Date | string `YYYY-MM-DD HH:MM:SS` | Thời điểm giao dịch | Không parse được → loại (30 dòng) |
| Store | string | Mã cửa hàng | Strip + upper |
| Product | string | Mã SKU | Strip + upper; thiếu → loại, không đoán mã (30 dòng) |
| Quantity | int | Số lượng; âm = trả hàng | RETURN tách khỏi demand (987 dòng); ≥100 = đơn sỉ B2B → loại (3 dòng) |
| UnitPrice | int (VND) | Giá bán thực tế (đã trừ khuyến mãi) | — |
| TransactionType | SALE / RETURN | Loại giao dịch | — |

### products.csv — master sản phẩm
| Column | Type | Description |
|---|---|---|
| sku_id | string | Mã SKU (SKU001–SKU032) |
| product_name | string | Tên sản phẩm |
| category | string | Nhóm hàng (12 nhóm) |
| unit_price | int VND | Giá bán niêm yết (trước tăng giá 07/2025) |
| purchase_cost | int VND | Giá vốn — dùng cho MEU |
| pack_size | int | Quy cách thùng/lốc khi đặt hàng |
| moq | int | Số lượng đặt tối thiểu |
| lead_time_days | int | Số ngày nhà cung cấp giao hàng (SKU004 = 10 ngày để kiểm thử horizon) |
| shelf_life_days | int | Hạn sử dụng; ≤ 7 ngày được coi là hàng dễ hỏng trong MEU |
| launch_date | date | Ngày mở bán SKU mới (trống = có từ đầu) |

### stores.csv
`store_id`, `store_name`, `address`.

### store_assortment.csv
`store_id`, `sku_id`, `listed_from` — Store–SKU nào được kinh doanh từ ngày nào. Chỉ những ngày ≥ `listed_from` mới được tạo trong panel.

### store_calendar.csv
| Column | Description |
|---|---|
| store_id, date | Khóa |
| status | `open` · `closed_holiday` (mùng 1–2 Tết) · `closed_renovation` (S003 04–06/08/2025) · `pos_outage` (S002 10–12/03/2026: mở cửa nhưng mất dữ liệu) |

### holidays_vn.csv
`date`, `holiday_name`, `holiday_type` (`public` / `tet`). Gồm Tết Dương lịch, Tết Nguyên đán (giao thừa → mùng 4), Giỗ Tổ, 30/4, 1/5, 2/9.

### promotions.csv
`promo_id`, `store_id`, `sku_id`, `start_date`, `end_date`, `discount_pct` (0.10–0.30). Là **kế hoạch đã biết trước** nên được dùng làm feature cho ngày tương lai.

### inventory_daily.csv.gz
`date`, `store_id`, `sku_id`, `closing_stock` — tồn kho cuối ngày (dùng để đánh dấu stockout; không dùng làm feature dự báo trực tiếp).

## 2. Dữ liệu đã xử lý (`data/processed/daily_sales.csv.gz`) — panel Store–SKU–Day
| Column | Type | Description | Quy tắc |
|---|---|---|---|
| date | date | Ngày | Lịch liên tục từ `listed_from` đến 09/11/2026 |
| store_id | string | Mã cửa hàng | — |
| sku_id | string | Mã SKU | — |
| store_status | string | Trạng thái cửa hàng (từ store_calendar) | — |
| sales | float | Tổng số lượng bán GROSS trong ngày (không gồm trả hàng, đơn sỉ) | **= 0** khi cửa hàng mở & SKU đang bán & không có giao dịch; **= NaN** khi đóng cửa / lỗi POS |
| n_transactions | float | Số dòng giao dịch | NaN khi missing |
| avg_unit_price | float | Giá bán bình quân thực tế | NaN khi không bán |
| is_missing | 0/1 | Ngày không có dữ liệu hợp lệ | 533 ngày |
| closing_stock | float | Tồn cuối ngày | — |
| is_stockout | 0/1 | Tồn cuối ngày = 0 khi đang mở cửa → doanh số bị chặn | 3,599 ngày; loại khỏi target train/đánh giá |
| discount_pct | float | Mức giảm giá khuyến mãi | 0 nếu không KM |
| is_promo | 0/1 | Có khuyến mãi | — |
| category | string | Nhóm hàng | — |

Kiểm tra bắt buộc (`validate_daily`, `tests/test_data_pipeline.py`): không null khóa, không trùng `date–store–sku`,
sales ≥ 0, ngày missing không bị điền số.

## 3. Feature (`src/features/build_features.py`)
Origin t = cuối ngày t; dự báo ngày t+h (h=1..7). Mọi feature lịch sử chỉ dùng dữ liệu ≤ t.

| Nhóm | Feature | Ý nghĩa |
|---|---|---|
| Static (categorical) | store_id, sku_id, category, log_unit_price | Đặc trưng chuỗi |
| Lag tại origin | lag_0, lag_1, lag_2, lag_3, lag_6, lag_13 | Doanh số ngày t−k |
| Rolling tại origin | roll_mean_7/14/28, roll_std_7/28, ewm_mean_7 | Mức bán & biến động gần đây |
| Chất lượng chuỗi | zero_share_28, stockout_days_7, missing_days_7, promo_days_7, history_days | Độ thưa, hết hàng, độ dài lịch sử |
| Ngày mục tiêu (biết trước) | t_dow, t_dom, t_month, t_weekofyear, t_is_weekend, t_is_holiday, t_holiday_eve, t_tet_window, t_is_payday, t_discount_pct, t_is_promo | Lịch, Tết (−21..+14 ngày), khuyến mãi đã lên kế hoạch |
| Same-weekday lag | sw_lag_1 = sales(t+h−7), sw_lag_2 = sales(t+h−14), sw_lag_4 = sales(t+h−28), sw_mean | Chu kỳ tuần; luôn ≤ t vì h ≤ 7 |

Target: `y = sales(t+h)`; chỉ train/đánh giá khi `y_ok = 1` (quan sát được và không stockout).

## 4. Output forecast (`artifacts/forecasts/latest_forecast.csv`)
| Column | Description |
|---|---|
| as_of_date | Ngày dữ liệu cuối cùng dùng để dự báo |
| forecast_date | Ngày được dự báo |
| store_id, sku_id, category | — |
| horizon | 1..7 |
| predicted_sales | Dự báo (≥ 0, không NaN) |
| baseline_seasonal_naive | Dự báo baseline cùng ngày để đối chiếu |
| method | `model` · `seasonal_naive_fallback` (model lỗi) · `rule_mean_fallback` (< 7 ngày lịch sử) |
| status | `OK` / `INSUFFICIENT_HISTORY` |
| confidence | HIGH (WAPE backtest ≤35%) · MEDIUM (≤60%) · LOW (>60% hoặc lịch sử < 28 ngày) |
| history_obs, wape_backtest | Căn cứ tính confidence |
| model_version, generated_at | Truy vết |

# Kết quả đánh giá mô hình (tự sinh bởi scripts/run_pipeline.py)

> Sinh lúc: 2026-11-10 14:29 +07 · Backend GBM: **lightgbm** · Model version: `lightgbm-direct-v1.0.0`
> Dữ liệu: dataset tổng hợp SmartGrocery (xem docs/dataset_source.md) — kết quả không đại diện cho cửa hàng thật.

## Thiết lập
- Chiến lược: Direct forecasting, 7 model (t+1 … t+7), objective Poisson.
- Backtest rolling-origin 4 fold, cutoff: 2026-08-01, 2026-08-29, 2026-09-26, 2026-10-24;
  mỗi fold huấn luyện lại, validation 28 ngày ngay trước cutoff (early stopping), test 28 origin.
- Tập so sánh: dòng có actual quan sát được, **không stockout** (doanh số bị chặn), và cả 3 mô hình đều có dự báo
  → 58,004 điểm Store–SKU–Day–Horizon.
- Số cây cuối cùng theo horizon (median best iteration các fold): {1: 341, 2: 200, 3: 260, 4: 211, 5: 231, 6: 255, 7: 249}.

## 1. So sánh tổng thể

| model | n | WAPE | RMSE | MAE | Bias_pct |
|---|---|---|---|---|---|
| Seasonal Naive | 58004 | 56.00% | 13.837 | 8.443 | -1.00% |
| MA-28 | 58004 | 41.11% | 10.249 | 6.198 | -0.66% |
| LightGBM | 58004 | 37.96% | 9.303 | 5.723 | -0.75% |

**Kết luận:** LightGBM giảm WAPE 32.2% tương đối so với Seasonal Naive trên cùng tập đánh giá.

## 2. Theo horizon

| horizon | Seasonal Naive | MA-28 | LightGBM |
|---|---|---|---|
| 1 | 55.84% | 40.98% | 37.84% |
| 2 | 55.89% | 40.99% | 37.97% |
| 3 | 55.97% | 41.09% | 38.03% |
| 4 | 56.05% | 41.14% | 37.99% |
| 5 | 56.06% | 41.19% | 38.05% |
| 6 | 56.09% | 41.15% | 37.95% |
| 7 | 56.14% | 41.26% | 37.91% |

(giá trị = WAPE %)

## 3. Theo fold (độ ổn định)

| fold | Seasonal Naive | MA-28 | LightGBM |
|---|---|---|---|
| 1 | 56.57% | 42.00% | 39.06% |
| 2 | 56.58% | 40.22% | 36.48% |
| 3 | 55.29% | 41.31% | 38.29% |
| 4 | 55.13% | 40.72% | 38.08% |


## 4. Theo nhóm SKU (mục 8.6)

| segment | model | n | WAPE | RMSE | MAE |
|---|---|---|---|---|---|
| Bán nhanh (>=15/ngày) | Seasonal Naive | 20398 | 52.15% | 19.833 | 14.216 |
| Bán nhanh (>=15/ngày) | LightGBM | 20398 | 35.25% | 13.377 | 9.609 |
| Bán thưa (>30% ngày = 0) | Seasonal Naive | 1816 | 113.05% | 2.407 | 1.770 |
| Bán thưa (>30% ngày = 0) | LightGBM | 1816 | 80.02% | 1.593 | 1.253 |
| Bán vừa/chậm | Seasonal Naive | 31288 | 65.29% | 6.342 | 4.638 |
| Bán vừa/chậm | LightGBM | 31288 | 44.69% | 4.294 | 3.174 |
| Ngày khuyến mãi | Seasonal Naive | 3704 | 54.70% | 22.021 | 13.106 |
| Ngày khuyến mãi | LightGBM | 3704 | 36.23% | 14.504 | 8.679 |
| SKU mới (<90 ngày) | Seasonal Naive | 798 | 63.28% | 4.607 | 3.579 |
| SKU mới (<90 ngày) | LightGBM | 798 | 49.07% | 3.338 | 2.775 |


## 5. Theo category (LightGBM)

| category | n | WAPE | RMSE | MAE | Bias_pct |
|---|---|---|---|---|---|
| instant_food | 3990 | 34.11% | 18.533 | 11.665 | -3.49% |
| fresh_produce | 7919 | 35.82% | 8.589 | 6.194 | -2.33% |
| dairy | 5785 | 36.85% | 9.449 | 6.533 | -0.98% |
| beverages | 9756 | 36.94% | 13.391 | 9.083 | 1.40% |
| eggs | 2002 | 38.03% | 10.552 | 8.417 | -0.62% |
| bakery | 2023 | 38.88% | 6.013 | 4.741 | -1.35% |
| snacks | 3877 | 40.65% | 5.875 | 4.231 | 0.20% |
| meat_seafood | 5969 | 40.83% | 5.388 | 4.105 | 0.20% |
| rice_grains | 1899 | 42.77% | 3.794 | 2.881 | -0.69% |
| condiments | 5582 | 44.13% | 3.983 | 3.030 | -2.45% |
| household | 5643 | 48.70% | 3.371 | 2.591 | 0.35% |
| personal_care | 3559 | 69.12% | 2.111 | 1.574 | 4.61% |


## 6. 10 chuỗi Store–SKU khó dự báo nhất (LightGBM, theo WAPE)

| store_id | sku_id | n | WAPE | MAE |
|---|---|---|---|---|
| S001 | SKU030 | 550 | 94.48% | 1.397 |
| S002 | SKU030 | 631 | 85.62% | 0.991 |
| S003 | SKU030 | 513 | 81.82% | 1.094 |
| S003 | SKU027 | 626 | 73.52% | 1.826 |
| S001 | SKU007 | 581 | 71.02% | 2.519 |
| S002 | SKU004 | 585 | 67.29% | 2.246 |
| S002 | SKU027 | 593 | 66.80% | 2.169 |
| S002 | SKU007 | 641 | 66.38% | 1.837 |
| S001 | SKU029 | 644 | 65.85% | 2.127 |
| S003 | SKU007 | 581 | 64.68% | 1.425 |


## Biểu đồ
- `model_comparison.png`, `wape_by_horizon.png`, `wape_by_segment.png`,
  `actual_vs_predicted.png`, `feature_importance.png`, `future_forecast_7d.png`, `data_overview.png`

## Giới hạn
- Dữ liệu tổng hợp: quan hệ nhân quả (khuyến mãi, Tết) được mô phỏng nên mô hình học dễ hơn thực tế.
- Ngày stockout bị loại khỏi target → mô hình ước lượng nhu cầu khi đủ hàng, nhưng chưa khôi phục (unconstrain) nhu cầu bị mất.
- SKU bán thưa có WAPE cao với mọi mô hình — đây là đặc tính dữ liệu, không phải lỗi pipeline.

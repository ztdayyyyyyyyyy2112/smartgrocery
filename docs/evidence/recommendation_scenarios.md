# Kịch bản đề xuất nhập hàng (tự sinh)

Model: `lightgbm-direct-v1.0.0` · Dữ liệu as-of 2026-11-09 · Chi tiết request/response: `recommendation_scenarios.json`

| Kịch bản | Status | Alert | IP | ROP | Qty theo ROP | Qty đề xuất (MEU) | Confidence | Warnings |
|---|---|---|---|---|---|---|---|---|
| 1. Sữa tươi sắp hết (CRITICAL) | REORDER_RECOMMENDED | CRITICAL | 18.0 | 85.618 | 72 | 96 | MEDIUM | - |
| 2. Nước suối tồn nhiều (không cần nhập) | NO_REORDER_NEEDED | OK | 358.0 | 119.733 | 0 | 0 | MEDIUM | - |
| 3. Mì gói gần ROP, làm tròn pack 30 / MOQ 60 | REORDER_RECOMMENDED | CRITICAL | 138.0 | 238.253 | 120 | 150 | HIGH | - |
| 4. Táo nhập khẩu lead time 10 ngày > horizon 7 | HORIZON_INSUFFICIENT | MANUAL_REVIEW | 8.0 | None | None | None | LOW | LOW_CONFIDENCE, HORIZON_INSUFFICIENT |
| 5. SKU mới 5 ngày lịch sử (rule fallback) | REORDER_RECOMMENDED | CRITICAL | 4.0 | 14.943 | 12 | 24 | LOW | SIGMA_CATEGORY_CV_FALLBACK, INSUFFICIENT_HISTORY, LOW_CONFIDENCE |
| 6. Thịt heo (tươi sống) – chi phí do Backend truyền | REORDER_RECOMMENDED | CRITICAL | 5.0 | 20.845 | 20 | 15 | MEDIUM | - |
| 7. Thiếu tham số chi phí → không chạy MEU | REORDER_RECOMMENDED | CRITICAL | 30.0 | 103.414 | 96 | 96 | HIGH | MEU_INPUT_MISSING |
| 8. Reserved > On hand + On order | INVENTORY_DATA_CHECK | MANUAL_REVIEW | -15.0 | None | None | None | MEDIUM | NEGATIVE_INVENTORY_POSITION |
| 9. SKU không tồn tại | ERROR 404 UNKNOWN_SKU | - | - | - | - | - | - | - |

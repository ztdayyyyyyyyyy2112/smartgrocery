# Phương pháp AI — Dự báo nhu cầu & Tối ưu nhập hàng

Số liệu kết quả chi tiết: `docs/evaluation/metrics.md` (tự sinh mỗi lần chạy pipeline).

## 1. Bài toán
Với mỗi Store–SKU, tại cuối ngày t, dự báo nhu cầu bán GROSS của 7 ngày t+1…t+7, sau đó đề xuất có nên nhập hàng
và nhập bao nhiêu, dựa trên tồn kho do Backend cung cấp.

## 2. Tiền xử lý
1. Chuẩn hóa cột, mã SKU/store; loại ngày lỗi, thiếu mã (không đoán), trùng `transaction_id`.
2. Tách trả hàng (dự báo gross demand), loại đơn sỉ B2B ≥ 100 đơn vị/dòng.
3. Tổng hợp Store–SKU–Day trên lịch liên tục từ ngày SKU được kinh doanh.
4. **Zero-sales vs missing vs stockout**: điền 0 chỉ khi cửa hàng mở và SKU đang bán; đóng cửa / lỗi POS = NaN;
   ngày tồn cuối = 0 đánh dấu stockout và **không dùng làm target** (doanh số bị chặn ≠ nhu cầu).

## 3. Baseline — Seasonal Naive
`Forecast(t+h) = Actual(t+h−7)` trong từng chuỗi; nếu ngày đó missing thì lùi thêm 1 tuần; vẫn thiếu → NaN
(không bịa). Thêm baseline tham khảo **MA-28** (trung bình 28 ngày).

## 4. LightGBM — Direct multi-horizon
- 7 model độc lập, model h học `sales(t+h)` từ feature tại origin t (mục 7.6 hướng dẫn) → không lan truyền sai số như recursive.
- Objective **Poisson** (số lượng không âm, nhiều số 0, phương sai tăng theo mức bán).
- Tham số: learning_rate 0.05, num_leaves 31, min_child_samples 20, subsample 0.8, colsample 0.9, λ2 = 1.
- Categorical native cho store_id / sku_id / category, danh mục cố định lưu trong bundle → nhất quán train/inference.
- Số cây: early stopping trên validation 28 ngày (chia theo thời gian), model cuối dùng median best iteration các fold.
- Output clip ≥ 0, NaN/Inf → 0 rồi được ghi nhận.

## 5. Thiết kế đánh giá (chống leakage)
- Không random split. Rolling-origin backtest 4 fold, cutoff 01/08, 29/08, 26/09, 24/10/2026.
- Mỗi fold: train target < C−28 · valid target ∈ [C−28, C) · test origin ∈ [C−1, C+27). Huấn luyện lại mỗi fold.
- Tập test chỉ dùng để đánh giá cuối, không chọn hyperparameter.
- Metrics: **WAPE** (chính), **RMSE**, **MAE**, Bias%. Tổng actual = 0 → WAPE = N/A.
- So sánh công bằng: cùng tập dòng (actual quan sát được, không stockout, mọi mô hình có dự báo).
- Kiểm thử leakage tự động: `tests/test_features.py::test_no_future_leakage` (đổi dữ liệu sau t, feature tại t không đổi).

## 6. Confidence & fallback
| Tình huống | Xử lý | Mã |
|---|---|---|
| Model không load | Seasonal naive đã kiểm chứng, health = degraded | MODEL_UNAVAILABLE |
| < 7 ngày lịch sử | Trung bình các ngày đã quan sát, confidence LOW, cần duyệt tay | INSUFFICIENT_HISTORY, LOW_CONFIDENCE |
| < 28 ngày hoặc WAPE backtest > 60% | Dự báo model, confidence LOW | LOW_CONFIDENCE |
| Lead time > 7 ngày | Không ngoại suy, không đề xuất số lượng | HORIZON_INSUFFICIENT |
| Thiếu hệ số chi phí | Không gọi là MEU, trả lượng theo ROP | MEU_INPUT_MISSING |
| reserved > on_hand + on_order | Không đề xuất, yêu cầu kiểm tra dữ liệu | INVENTORY_DATA_CHECK |

## 7. Tối ưu tồn kho
- **Inventory Position** `IP = on_hand + on_order − reserved` (Backend cung cấp).
- **Safety Stock** `SS = z(service level) × σ_daily × √L`. σ_daily = độ lệch chuẩn **residual backtest** của chính
  Store–SKU đó (không phải độ lệch chuẩn doanh số thô); chuỗi < 20 residual → σ theo hệ số biến thiên trung vị của category.
- **ROP** = Σ dự báo trong L ngày lead time + SS.
- **Lượng theo ROP**: IP ≤ ROP → `ROP − IP`, áp MOQ, làm tròn lên theo pack size. IP > ROP → 0.
- Cảnh báo: CRITICAL nếu IP < nhu cầu lead time (sẽ hết trước khi hàng về), WARNING nếu IP ≤ ROP.

## 8. Maximum Expected Utility
ROP quyết định **khi nào** cần xem xét đặt hàng; MEU chọn **đặt bao nhiêu**.
- Quyết định q ∈ {0, MOQ, MOQ+pack, …} (đã làm tròn quy cách).
- Kịch bản nhu cầu trong protection period P = L + review period (mặc định 1): phân phối chuẩn
  N(Σ forecast, σ_daily·√P) rời rạc hóa tại phân vị 10/30/50/70/90%, mỗi kịch bản p = 0.2 → xác suất suy ra từ residual thực nghiệm.
- Utility: `U = giá bán·bán được − giá vốn·q + salvage·dư − holding·dư − waste·dư − penalty·thiếu`.
  Hàng dư vẫn bán được kỳ sau (salvage = giá vốn), nên chi phí thật của hàng dư = holding + waste.
- Chọn `q* = argmax Σ p(s)·U(q, s)`. Kết quả: hàng hạn dài (chi phí dư thấp) → đặt nhiều hơn ROP; hàng tươi sống
  (waste cao) → đặt ít hơn ROP. Ví dụ trong `docs/evidence/recommendation_scenarios.md`: sữa tươi ROP 72 → MEU 96;
  thịt heo ROP 20 → MEU 15.
- Hệ số mặc định (giả định demo, cần business xác nhận): holding = 25%/năm giá vốn; stockout penalty = 10% giá bán;
  waste = 50% giá vốn cho hàng shelf life ≤ 7 ngày. Backend có thể truyền `costs` để ghi đè; response ghi rõ `cost_source`.

## 9. Giới hạn
- Dữ liệu tổng hợp; chưa có thử nghiệm trên dữ liệu thật.
- Chưa unconstrain nhu cầu ngày stockout (chỉ loại khỏi target).
- σ giả định sai số độc lập theo ngày; lead time cố định.
- Lead time > 7 ngày cần mở rộng horizon (ví dụ 14 ngày) trong phiên bản sau.
- MEU một kỳ (single-period); chưa tối ưu đa kỳ hay ràng buộc sức chứa kho.

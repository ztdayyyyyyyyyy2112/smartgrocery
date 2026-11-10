# Nguồn dữ liệu (Dataset Source)

## Dataset sử dụng
**SmartGrocery Synthetic Retail v1** — dữ liệu tổng hợp do nhóm tự sinh bằng
`services/intelligence/scripts/generate_synthetic_data.py` (seed = 42, tái lập 100%).
Ngày tạo: 09/11/2026. Không chứa dữ liệu cá nhân. Không phải dữ liệu thật của doanh nghiệp nào.

| Thuộc tính | Giá trị |
|---|---|
| Khoảng thời gian | 01/11/2024 → 09/11/2026 (739 ngày) |
| Cửa hàng | 3 (S001 Quận 1, S002 Thủ Đức, S003 Bình Thạnh — giả lập) |
| SKU | 32, 12 nhóm hàng (rau củ, sữa, thịt cá, trứng, bánh mì, gạo, mì gói, đồ uống, snack, gia vị, gia dụng, chăm sóc cá nhân) |
| Chuỗi Store–SKU | 95 (S003 không bán SKU004; 2 SKU mới mở bán 14/09 và 05/11/2026) |
| Giao dịch POS thô | 248,696 dòng |
| Panel Store–SKU–Day | 65,940 dòng |

## Vì sao chọn dữ liệu tổng hợp thay vì M5 / Favorita / UCI Online Retail
Các dataset ứng viên ở mục 4.3 hướng dẫn đều đã được khảo sát nhưng mỗi bộ thiếu một phần bắt buộc của đồ án:

| Yêu cầu đồ án | M5 | Favorita | UCI Online Retail | Synthetic v1 |
|---|---|---|---|---|
| Doanh số Store–SKU–Day | ✓ | ✓ | cần tổng hợp, không có store | ✓ |
| Tồn kho theo ngày (đánh dấu stockout) | ✗ | ✗ | ✗ | ✓ |
| Lead time, MOQ, pack size, giá vốn | ✗ | ✗ | ✗ | ✓ |
| Hạn sử dụng (rủi ro hàng hỏng cho MEU) | ✗ | ✗ | ✗ | ✓ |
| Lịch đóng cửa (phân biệt zero-sales vs missing) | một phần | một phần | ✗ | ✓ |
| Bối cảnh Việt Nam (Tết, ngày lễ, VND) | ✗ | ✗ | ✗ | ✓ |
| Dung lượng phù hợp laptop sinh viên | ✗ (~450MB) | ~120MB | ✓ | ✓ (~4MB) |

Kế hoạch nhóm cho phép "data có thể tự tạo miễn là đáp ứng nhu cầu đồ án". Dữ liệu tổng hợp cho phép kiểm thử đủ
luồng: checkout → tồn kho → dự báo → đề xuất nhập → phê duyệt → nhận hàng, khớp schema Backend.

## Cơ chế sinh dữ liệu (để giải thích trong báo cáo)
Nhu cầu ngày = `base × hệ số cửa hàng × thứ trong tuần × mùa vụ × ngày lương × xu hướng (+8%/năm) × Tết × ngày lễ
× uplift khuyến mãi exp(2.6·discount) × hiệu ứng sau KM × độ co giãn giá`, sau đó lấy mẫu **Negative Binomial**
(SKU bán thưa có phân tán lớn hơn).

- **Tết Nguyên đán** (29/01/2025, 17/02/2026): tăng dần 14 ngày trước Tết (snack ×2.6, đồ uống ×1.8…), đóng cửa mùng 1–2, giảm 35% ngày 2–7 sau Tết.
- **Ngày lễ** 1/1, 30/4, 1/5, 2/9: +15% 2 ngày trước. **Ngày lương** 1–5 và 15–16: +5%.
- **Khuyến mãi**: 804 đợt (3–10 ngày, giảm 10–30%) cho nhóm hàng đóng gói; có kế hoạch KM đến 30/11/2026 (biết trước → dùng làm feature tương lai).
- **Tăng giá** 4% từ 01/07/2025.
- **Tồn kho**: mô phỏng chính sách (s, S) theo lead time, 6% đơn nhập bị giao trễ 2–4 ngày → **5.5% ngày stockout**; doanh số bị chặn bởi tồn kho.
- **Sự cố dữ liệu cố ý**: lỗi POS S002 10–12/03/2026 (mất dữ liệu), S003 đóng cửa sửa chữa 04–06/08/2025,
  987 dòng trả hàng (số âm), 744 dòng trùng `transaction_id`, 30 ngày lỗi định dạng, 30 dòng thiếu mã SKU,
  400 mã SKU viết thường/khoảng trắng, 3 đơn sỉ B2B bất thường (180–300 đơn vị).

## Giới hạn
- Quan hệ nhân quả được mô phỏng nên mô hình học dễ hơn dữ liệu thật; metrics không đại diện cho cửa hàng thật.
- Hệ số chi phí (holding, stockout penalty, waste) là giả định demo, cần business xác nhận.
- Khi có dữ liệu thật từ Backend (bảng orders/inventory_batches), chỉ cần xuất cùng schema `data/raw/*` và chạy lại pipeline.

## File
`data/raw/`: `pos_transactions.csv.gz`, `products.csv`, `stores.csv`, `store_assortment.csv`, `store_calendar.csv`,
`holidays_vn.csv`, `promotions.csv`, `inventory_daily.csv.gz` — mô tả từng cột trong `docs/data_dictionary.md`.

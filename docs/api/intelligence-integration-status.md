# Intelligence integration status — 10/11/2026

Code Bảo Khoa đã được nhập vào `services/intelligence`, kèm tài liệu, bài test và bằng chứng tái tạo. Dịch vụ AI hoạt động độc lập; frontend vẫn chỉ gọi backend chính. **Chưa nối kết quả AI vào các bảng forecast/recommendation của backend.**

## Lý do chưa thể nối trực tiếp

- Bộ dữ liệu AI là dữ liệu tổng hợp, dùng `store_id` như `S001` và `sku_id` như `SKU005`.
- Backend seed hiện dùng `Store.code = SG-HCM-01`, sản phẩm `APL-FUJI-01`, `MILK-1L-01`, `VEG-CARROT-01`, với UUID nội bộ. Không có cặp Store–SKU chung để suy luận hợp lệ.
- `POST /api/v1/jobs/{job_id}/result` của backend yêu cầu `product_id` UUID thật và ngày dự báo trong cửa sổ job. Không được gắn dự báo SKU tổng hợp vào sản phẩm khác chỉ để làm demo.

## Việc còn lại để tích hợp thật

1. Chọn một bộ mã Store–SKU chung. Cách phù hợp cho demo: bổ sung catalog/seed backend bằng chính các mã tổng hợp của AI, hoặc xuất dữ liệu order/inventory backend đúng schema AI rồi train lại. Ghi rõ dữ liệu tổng hợp trong demo/báo cáo.
2. Viết adapter trong backend: lấy tồn khả dụng, reserved, on-order, lead time và giá vốn từ database; gọi AI service nội bộ; chuyển `sku_id` về `Product.id`, `store_id` về `Store.id`.
3. Worker xử lý `ForecastJob` từ QUEUED → RUNNING → SUCCEEDED/FAILED, ghi forecast/recommendation vào DB; không dùng endpoint nhập kết quả thủ công cho luồng sản phẩm.
4. Kiểm thử end-to-end với database mới: seed → chạy job → xem forecast/recommendation qua API chính → duyệt → tạo PO → nhận hàng. Frontend chỉ kết nối API chính.

Đã kiểm tra local: pipeline `--regenerate-data` hoàn thành với LightGBM và 46 bài test AI qua. Model nhị phân, dữ liệu thô/processed và virtualenv chỉ ở máy local; clone sạch sinh lại bằng lệnh trong README.

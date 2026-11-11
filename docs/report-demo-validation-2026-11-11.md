# SmartGrocery — bằng chứng kiểm thử demo ngày 11/11/2026

## Phạm vi

Kiểm thử bản chạy local bằng Docker Compose trên branch `feat/storefront-checkout-privacy`. Tất cả email, số điện thoại và địa chỉ trong bài kiểm thử đều là dữ liệu giả. Các thao tác đặt hàng, dự báo và nhập hàng đã ghi dữ liệu thử vào PostgreSQL local; đây không phải giao dịch thực.

## Kết quả chức năng

| Hạng mục | Kết quả quan sát |
|---|---|
| Dịch vụ | Web, API, PostgreSQL, Redis, worker và AI đều chạy; `/health` của API và AI trả `ok`. |
| Đăng ký khách | Tạo `report.customer.20261111.90f4da70@example.com` với đồng ý chia sẻ dữ liệu; backend lưu thời điểm đồng ý và mật khẩu dạng hash. |
| Giỏ hàng | Lưu SKU005 ở S001, đăng xuất không đọc được giỏ (401), đăng nhập lại khôi phục giỏ; xóa sản phẩm khỏi giỏ thành công. |
| Đặt hàng | Tạo đơn `38a70803-017c-470b-871a-2653ecff2f30` tại SmartGrocery Quận 1, giá 34.000₫, trạng thái `confirmed`; giỏ trống sau checkout. |
| Phân quyền merchant | Merchant S001 xem được đơn và thông tin giao hàng; merchant S002 mở cùng đơn nhận 404. Sổ tồn kho ghi giữ chỗ 1 đơn vị SKU005 cho S001. |
| Tìm kiếm | `q=SKU005` trong S001 trả đúng 1 sản phẩm. |
| AI qua backend | Job `a6621dcb-e0c1-4f70-92d5-1c843729c5df` hoàn tất, ghi 224 dòng dự báo (32 SKU × 7 ngày) và 29 gợi ý nhập hàng. |
| AI trực tiếp | Model `lightgbm-direct-v1.0.0` đã nạp, lịch sử đến 09/11/2026. Với SKU005 và đầu vào tồn 122, giữ chỗ 3, đang nhập 0: tổng dự báo 7 ngày 207,778; kết quả `NO_REORDER_NEEDED`, confidence `MEDIUM`. |
| Nhập hàng | Smoke test chạy trọn chuỗi checkout → giữ tồn → job AI → gợi ý → tạo/duyệt/gửi PO → nhận hàng; số lượng tồn của sản phẩm trong PO tăng. |

Bài smoke test ban đầu giả định SKU005 luôn cần nhập thêm. Sau các lượt demo trước, tồn SKU005 đã tăng nên AI không tạo gợi ý cho SKU này. Script đã được sửa để chọn một gợi ý đang chờ duyệt và kiểm tra đúng sản phẩm của PO; lượt chạy lại đạt `DEMO PASS`.

## Kiểm thử tự động và mô hình

- Backend: **43/43** test đạt trên database kiểm thử riêng `smartgrocery_feature_test3`.
- AI: **46/46** test đạt trong image intelligence hiện chạy. Có cảnh báo deprecation của FastAPI/Pandas và thư viện test; không có test thất bại.
- Frontend: `npm run lint` và `npm run build` đều đạt.
- Backtest trong [`docs/evaluation/metrics.md`](evaluation/metrics.md): LightGBM WAPE **37,96%**, RMSE **9,303**; Seasonal Naive WAPE **56,00%**, RMSE **13,837** trên **58.004** điểm đánh giá từ dữ liệu tổng hợp. Đây là kết quả trên tập dữ liệu demo, không phải độ chính xác đã chứng minh với đơn hàng thật.

## Giới hạn cần nêu trong report

1. Model học từ dữ liệu tổng hợp cố định đến **09/11/2026**. Dự báo vừa chạy có ngày mục tiêu **10–16/11/2026**; một phần khoảng dự báo đã qua tại ngày kiểm thử. Đơn hàng mới chỉ đổi tồn kho và quyết định nhập hàng, chưa được đưa vào huấn luyện lại.
2. Checkout demo giữ tồn kho nhưng chưa tích hợp thanh toán, đơn vị vận chuyển hoặc giao hàng thực tế.
3. Bản Docker Compose hiện là cấu hình local với tài khoản demo và các cổng dịch vụ công khai trên máy. Chưa đủ điều kiện đưa thông tin cá nhân thật lên môi trường public.
4. Kết quả trên chứng minh các luồng cốt lõi đã kiểm thử. Chưa thể kết luận mọi trạng thái giao diện, thiết bị và điều kiện tải đều ổn định.

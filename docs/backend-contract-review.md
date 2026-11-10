# Backend Contract Review — 27/10/2026

Tài liệu này là ghi chú học và review của Tuấn Anh. Nó không thay đổi ERD, RBAC hay REST contract.

## 1. Ba tài liệu đang dùng

### ERD — cấu trúc dữ liệu

ERD mô tả các bảng và quan hệ trong PostgreSQL. Ví dụ một `order` có nhiều `order_items`; một `order_item` có thể giữ hàng từ nhiều `inventory_batches`. Đây là lý do checkout phải lưu reservation thay vì chỉ trừ một con số tồn kho tổng.

Các nhóm dữ liệu chính:

- Người dùng và cửa hàng: `users`, `stores`.
- Catalog: `categories`, `products`.
- Bán hàng: `orders`, `order_items`, `stock_reservations`, `idempotency_keys`.
- Kho: `inventory_batches`.
- Nhập hàng: `suppliers`, `supplier_products`, `purchase_orders`, `purchase_order_items`, `goods_receipts`.
- AI và quyết định: `forecast_jobs`, `demand_forecasts`, `replenishment_recommendations`.
- Quy tắc: `business_rules`.

Các khái niệm cần nhớ:

- `on_hand`: lượng vật lý trong kho.
- `reserved`: lượng đã giữ cho đơn nhưng chưa xuất.
- `available = on_hand - reserved`: lượng có thể bán.
- Batch/lô: một phần hàng có lot code và hạn dùng riêng.
- FEFO: ưu tiên lô hết hạn sớm nhất trước.

### RBAC — ai được làm gì

MVP có ba role: `customer`, `merchant`, `admin`.

- Customer xem catalog, tạo checkout và xem đơn của chính mình.
- Merchant quản lý đơn của cửa hàng, kho, supplier, purchase order, forecast và recommendation.
- Admin có quyền của merchant và quản lý user/business rules.

Authentication trả JWT access token 15 phút và refresh token 7 ngày. Password phải được hash. Route protected phải kiểm tra token và role; customer không được đọc đơn của người khác.

### REST API — giao diện giữa các service

REST contract trả lời bốn câu hỏi: gọi URL nào, gửi field nào, nhận response nào và lỗi có mã gì. Frontend gọi FastAPI theo base URL `/api/v1`; FastAPI làm transaction/database; intelligence chỉ là service nội bộ.

Các nhóm endpoint:

- Auth: register, login, refresh, me.
- Catalog: categories, products.
- Orders: checkout, list/detail, cancel, fulfil.
- Inventory: positions, batches, quarantine.
- Procurement: suppliers, purchase orders, approve, send, receive.
- Intelligence: forecasts, recommendations, forecast jobs.

## 2. Luồng nghiệp vụ cần vẽ lại bằng lời

1. Customer gửi `POST /orders` cùng `Idempotency-Key`.
2. Backend mở một database transaction.
3. Backend khóa các batch phù hợp, chọn theo FEFO.
4. Nếu thiếu hàng, rollback toàn bộ và trả `STOCK_INSUFFICIENT`.
5. Nếu đủ hàng, tạo order/items/reservations và tăng `quantity_reserved`.
6. Nếu cùng key được gửi lại cùng payload, trả order cũ; payload khác trả `409`.
7. Khi fulfil, backend giảm on-hand và reserved trên các batch đã giữ.
8. Receiving một purchase order tạo goods receipt và inventory batches mới.

## 3. Những điểm đã hiểu

- Không được dùng `on_hand` một mình để hiển thị hàng bán được.
- Reservation phải nằm trong cùng transaction với checkout.
- FEFO là quy tắc backend, không giao cho frontend tự chọn batch.
- Idempotency chống tạo trùng order khi client retry.
- Customer scope được xác định bằng user hiện tại, không tin `customer_id` từ client.
- Forecast lỗi phải trả job failed; backend không tự bịa số forecast.

## 4. Điểm cần nhóm chốt trước khi code

- ERD/RBAC/API đang ở branch tài liệu riêng; cần xác nhận commit/PR nào là contract chính thức trên `develop`.
- PDF yêu cầu `database/migrations` và `database/seeds`, trong khi working tree hiện có `services/api/alembic`; cần chọn một nơi chính thức.
- REST contract nói `Idempotency-Key` unique theo customer, còn ERD đặt `idempotency_keys.key` làm primary key toàn cục; cần chốt scope/index.
- Cần chốt MVP có tách bước `confirmed` và `fulfilled` hay fulfil ngay sau checkout.
- Cần chốt seed password và tài khoản demo được quản lý bằng environment như thế nào.

## 5. Kết quả ngày 27/10

- [x] Đọc ERD, RBAC và REST contract.
- [x] Ghi lại mô hình dữ liệu, quyền và luồng checkout.
- [x] Ghi lại các điểm contract chưa thể tự quyết.
- [ ] Nhóm xác nhận các điểm cần chốt.
- [ ] Commit/PR tài liệu review trên branch riêng.

## 6. Lệnh Git cần chạy trên máy có quyền ghi `.git`

```powershell
git switch develop
git pull --ff-only origin develop
git switch -c feat/be-contract-review
git add docs/backend-contract-review.md docs/backend-task-checklist.md
git commit -m "docs(api): review backend contracts"
git push -u origin feat/be-contract-review
```

PR target: `develop`. Trong PR cần ghi rõ đây là review/clarification, không sửa contract; đính kèm các điểm cần nhóm xác nhận ở mục 4.

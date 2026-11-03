# SmartGrocery — Work Log

Nhật ký này ghi lại các phiên làm việc của Tuấn Anh với trợ lý, quyết định kỹ thuật, bằng chứng kiểm tra và việc còn lại. Các mục `[x]` chỉ mô tả công việc đã thực hiện trong workspace; chưa đồng nghĩa với PR đã merge.

## 2026-10-28 — Đọc kế hoạch và kiểm tra repo

### Mục tiêu

- Đọc `SmartGrocery_TaskPlan_26-10_to_18-11-2026.pdf`.
- Đối chiếu deadline, vai trò Backend/Database/Reasoning với repo.

### Đã làm

- [x] Đọc đủ 10 trang PDF.
- [x] Xác định vai trò Tuấn Anh: FastAPI, PostgreSQL, auth/RBAC, orders, inventory batches, FEFO, procurement, rules và concurrency.
- [x] Kiểm tra branch, commit và file hiện có trong repo.
- [x] Xác định frontend đang có shell/mock UI; backend mới có FastAPI health endpoint, DB connection và Alembic extension migration.
- [x] Xác định chưa có bằng chứng về models nghiệp vụ, seed, intelligence pipeline hay procurement implementation.

### Kết quả

- Repo mới ở giai đoạn foundation.
- Các mục tiêu lớn: storefront, auth/RBAC, catalog, checkout, inventory theo batch, supplier/PO, rules, forecast/replenishment, dashboard, deployment/test.

### Vấn đề phát hiện

- Lịch tổng và backend note có ngày setup khác nhau.
- ERD/RBAC/API contract tồn tại trên `origin/docs/be-erd-rbac-api`, chưa nằm trong `develop` tại thời điểm kiểm tra.
- PDF quy định branch/PR/test/evidence, không push trực tiếp vào `main` hoặc `develop`.

## 2026-10-28 — Tạo checklist backend

### Đã làm

- [x] Tạo `docs/backend-task-checklist.md`.
- [x] Chia công việc theo deadline 27/10–10/11.
- [x] Ghi tiêu chí hoàn thành: code, test, commit, PR và evidence.
- [x] Ghi quy trình GitHub và báo cáo hằng ngày.

### Ghi chú

- Checklist ban đầu đánh dấu FastAPI setup là đang làm dựa trên working tree; không khẳng định đó là phần Tuấn Anh đã commit.

## 2026-10-28 — Review ERD, RBAC và REST contract

### Đã làm

- [x] Đọc ERD: users, stores, products, batches, orders, reservations, suppliers, POs, forecasts, recommendations và jobs.
- [x] Đọc RBAC: customer, merchant, admin; route guards và error semantics.
- [x] Đọc REST API v1: auth, catalog, checkout, inventory, procurement, forecast và recommendation.
- [x] Tạo `docs/backend-contract-review.md`.
- [x] Ghi lại luồng FEFO, reservation transaction và idempotency.
- [x] Đánh dấu các điểm cần nhóm xác nhận: migration location, idempotency scope và confirmed/fulfilled flow.

### GitHub ghi chú

- [ ] Chưa tạo branch/commit/PR vì môi trường không cho ghi lock file trong `.git`.

## 2026-10-29 — Đọc định hướng đồ án mới

### Đã làm

- [x] Đọc `Sua Dinh Huong Do An.docx`.
- [x] Xác định vòng khép kín: SELL → OBSERVE → PREDICT → REASON → PLAN → APPROVE → RECEIVE → EVALUATE.
- [x] Xác định P0: commerce/inventory, procurement, forecasting, knowledge rules và decision optimization.
- [x] Xác định P1: planning/recovery và event/reliability.
- [x] Xác định P2: chatbot, A*, genetic algorithm, reinforcement learning.
- [x] Xác định yêu cầu evidence: concurrency, metrics, inference traces, decision experiment, retry và deployment.
- [x] Kiểm tra repo và xác nhận chưa có stock ledger, inference traces, model runs hay rule engine implementation.

## 2026-10-29 — Contract v2 alignment draft

### Đã làm

- [x] Tạo `docs/backend-contract-v2-alignment.md`.
- [x] Đề xuất tách current inventory state (`inventory_batches`) khỏi audit history (`stock_ledger`).
- [x] Chọn Rule Engine ở FastAPI business layer để giữ transaction boundary.
- [x] Chọn polling là P0, WebSocket là P1.
- [x] Chọn PO recovery là P1.
- [x] Chọn structured JSON/log cho inference trace tối thiểu; chưa tạo bảng riêng ở migration đầu tiên.
- [x] Chọn không tạo bảng `model_runs` ở P0; lưu metadata cần thiết trong job/artifact.

### Kiểm tra

- [x] Chạy `git diff --check`.
- [x] Không sửa ERD/API contract frozen.
- [x] Không tạo migration dựa trên các quyết định chưa được ghi lại.

## Quyết định hiện tại

- [x] Dùng `origin/docs/be-erd-rbac-api` làm baseline contract.
- [x] Bổ sung stock ledger ở database foundation.
- [x] Chưa tạo riêng `inference_traces` và `model_runs` ở P0.
- [x] Rule Engine thuộc FastAPI.
- [x] Polling trước WebSocket.
- [x] PO recovery sau khi P0 ổn định.

## Việc kế tiếp

- [ ] Kiểm tra dependencies và khả năng chạy FastAPI/pytest hiện tại.
- [ ] Viết database foundation models/migration theo baseline đã chọn.
- [ ] Tạo seed tối thiểu và chạy trên PostgreSQL sạch.
- [ ] Lưu log migration/seed/test.
- [ ] Sau foundation mới làm auth/RBAC và Products API.

## 2026-10-29 — Cài backend tools và chạy test đầu tiên

### Đã làm

- [x] Tạo virtual environment tại `services/api/.venv`.
- [x] Cài dependencies từ `services/api/requirements.txt`.
- [x] Chạy test bằng `services/api/.venv/Scripts/python.exe -m pytest -q`.

### Kết quả

- `1 passed` — `tests/api/test_health.py`.
- API health test trả response hợp lệ; database hiện có thể ở trạng thái disconnected nếu PostgreSQL chưa chạy, đúng với logic health hiện tại.
- Có hai warning môi trường: deprecation warning từ Starlette/AnyIO và pytest cache path đã tồn tại; không làm test fail.

### Bài học

- Không dùng Python hệ thống để chạy test dự án; luôn dùng interpreter trong `services/api/.venv`.
- Lệnh đúng từ repo root là:

```powershell
& .\services\api\.venv\Scripts\python.exe -m pytest -q
```

## 2026-10-29 — Audit Alembic và database connection

### Đã làm

- [x] Kiểm tra `alembic/env.py`, `alembic.ini`, `Base`, session engine và settings.
- [x] Kiểm tra Alembic head: `0001_extensions`.
- [x] Chạy Alembic bằng virtual environment.
- [x] Kiểm tra `.env` mà không in secret ra output.
- [x] Kiểm tra Docker Compose command availability.

### Kết quả

- Alembic package và migration script hoạt động đến bước kết nối database.
- PostgreSQL đang trả lời ở `localhost:5432` nhưng từ chối password của user `smartgrocery`; lỗi là `password authentication failed`.
- Docker CLI chưa có trong môi trường hiện tại, nên chưa thể dùng `docker compose` để kiểm tra hoặc tạo database.
- `0001_extensions` vẫn là migration head duy nhất; chưa chạy migration mới.

### Quyết định an toàn

- Không reset database, không xóa volume và không sửa password hiện tại vì có thể làm mất dữ liệu.
- Chưa viết migration nghiệp vụ khi database connection chưa xác nhận được.
- Bước tiếp theo là xác định nguồn PostgreSQL đang chạy và đồng bộ credential mà không làm mất dữ liệu.

## 2026-10-29 — Khởi tạo PostgreSQL sạch và chạy migration

### Đã làm

- [x] Xác nhận PostgreSQL service `postgresql-x64-18` đang chạy.
- [x] Xác nhận database instance ban đầu chưa có role `smartgrocery` và chưa có database `smartgrocery`.
- [x] Tạo role `smartgrocery` cho local development.
- [x] Tạo database `smartgrocery` với owner đúng role.
- [x] Chạy `alembic upgrade head` từ `services/api`.
- [x] Kiểm tra Alembic current.
- [x] Chạy toàn bộ pytest.

### Kết quả

- Migration `0001_extensions` đã chạy thành công.
- Alembic current: `0001_extensions (head)`.
- Test: `1 passed`.
- Database hiện sẵn sàng cho migration schema nghiệp vụ.
- Hai warning còn lại chỉ là cảnh báo môi trường, không làm test fail.

### Bài học

- Trong `psql`, mỗi meta-command như `\\c`, `\\dt`, `\\du` phải chạy riêng một dòng.
- Tạo database và chạy migration là hai bước khác nhau: database phải tồn tại trước, Alembic mới tạo extension/schema.

## 2026-10-29 — Database foundation: models và migration 0002

### Đã làm

- [x] Tạo SQLAlchemy models cho `users`, `stores`, `categories`, `products`, `inventory_batches` và `stock_ledger`.
- [x] Thêm enum role, batch status và stock event type.
- [x] Thêm foreign keys, unique constraints và quantity/price check constraints.
- [x] Import models vào `app.models` để Alembic nhận metadata.
- [x] Tạo migration `0002_foundation_entities.py`.
- [x] Chạy migration trên PostgreSQL sạch.
- [x] Kiểm tra Alembic current và danh sách bảng/cột bằng SQLAlchemy inspector.

### Lỗi phát hiện và sửa

- Lần chạy đầu bị `DuplicateObject: type "user_role" already exists` vì migration vừa tạo enum thủ công vừa để SQLAlchemy tạo lại enum khi tạo bảng.
- Đã sửa bằng `create_type=False` cho enum dùng trong columns và giữ một lần tạo enum có `checkfirst=True`.
- Chạy lại migration thành công sau khi sửa.

### Kết quả

- Alembic current: `0002_foundation (head)`.
- Database có đủ 6 bảng nền tảng và `alembic_version`.
- Pytest: `1 passed`.
- `git diff --check`: không có lỗi.

### Việc còn lại

- [ ] Viết seed cho store, categories, products, users và batches.
- [ ] Bổ sung migration orders/reservations/idempotency.
- [ ] Bổ sung test model/constraint và seed verification.

## 2026-10-29 — Seed dữ liệu catalog và inventory

### Đã làm

- [x] Tạo `services/api/scripts/seed.py`.
- [x] Seed một store demo, ba categories, ba products và ba inventory batches.
- [x] Dùng UUID cố định và unique lookup để seed chạy lặp lại không tạo bản ghi trùng.
- [x] Chạy seed hai lần liên tiếp.
- [x] Kiểm tra số lượng bản ghi bằng SQLAlchemy.

### Lỗi phát hiện và sửa

- Lần đầu seed lỗi `invalid input value for enum batch_status: "AVAILABLE"`.
- Nguyên nhân: SQLAlchemy mặc định gửi tên enum Python (`AVAILABLE`) trong khi PostgreSQL contract dùng giá trị lowercase (`available`).
- Đã thêm `values_callable` cho cả ba enum trong model để ORM gửi đúng contract.

### Kết quả

- Seed lần 1 và lần 2 đều thành công.
- Counts sau hai lần: 1 store, 3 categories, 3 products, 3 batches.
- Các batch đọc lại đúng `BatchStatus.AVAILABLE`/`available`.
- Pytest: `1 passed`.
- `git diff --check`: không có lỗi.

### Việc còn lại

- [ ] Seed user/role sau khi authentication có password hashing.
- [ ] Viết test tự động cho seed idempotency và constraints.
- [ ] Tạo orders, reservations và idempotency schema.

## 2026-10-29 — Kiểm tra môi trường chạy thử

### Đã làm

- [x] Đọc `services/api/requirements.txt` và `pytest.ini`.
- [x] Chạy `git diff --check` thành công.
- [x] Kiểm tra các package FastAPI, SQLAlchemy, Alembic, psycopg, pydantic-settings và pytest.
- [x] Thử chạy `python -m pytest -q`.

### Kết quả

- `pytest` chưa được cài trong Python environment hiện tại; lệnh test dừng với `No module named pytest`.
- Các dependency backend cũng chưa có trong environment hiện tại.
- Chưa chạy migration/test backend để tránh tạo kết luận sai từ môi trường thiếu dependency.

### Việc cần làm ở phiên sau

- Tạo hoặc kích hoạt `services/api/.venv`.
- Cài `services/api/requirements.txt`.
- Chạy lại test health trước khi viết model/migration.

## 2026-10-29 — Orders/Checkout foundation: migration 0003

### Đã làm

- [x] Thêm `OrderStatus` với pending, confirmed, cancelled, fulfilled.
- [x] Tạo models `orders`, `order_items`, `stock_reservations`, `idempotency_keys`.
- [x] Thêm check constraints cho tiền và quantity dương.
- [x] Thêm foreign keys và cascade phù hợp cho order items/reservations.
- [x] Tạo migration `0003_order_checkout_foundation.py`.
- [x] Chạy migration trên database local và kiểm tra Alembic head.
- [x] Chạy pytest và `git diff --check`.

### Kết quả

- Alembic current: `0003_orders (head)`.
- Orders/checkout foundation đã có schema để triển khai transaction và idempotency.
- Pytest: `1 passed`.
- Chưa triển khai API checkout, FEFO allocation hoặc reservation transaction; đó là bước business logic kế tiếp.
-
## 2026-11-03 — Authentication/RBAC và Products API nền tảng

### Đã làm

- [x] Thêm pwdlib Argon2 và PyJWT vào backend dependencies.
- [x] Thêm cấu hình JWT secret và TTL vào settings/.env.example.
- [x] Tạo password hashing bằng Argon2 và access token JWT.
- [x] Tạo current-user dependency và role guard helper.
- [x] Implement `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`.
- [x] Implement `GET /api/v1/categories` và `GET /api/v1/products` với search/category filter/available quantity.
- [x] Chạy smoke test register → login → me → categories → products.

### Kết quả

- Register `201`, login `200`, me `200`, categories `200`, products `200` với 3 sản phẩm seed.
- Pytest: `1 passed`.

### Giới hạn

- Refresh token chưa triển khai vì schema refresh-token chưa có.
- Role guard chưa gắn vào merchant routes vì inventory/procurement API chưa có.
- Product detail, pagination và test 401/403/404 còn thiếu.

## 2026-11-03 — Checkout transaction, FEFO reservation và idempotency

### Đã làm

- [x] Tạo `POST /api/v1/orders` yêu cầu Bearer token và `Idempotency-Key`.
- [x] Kiểm tra product/store và số lượng request.
- [x] Khóa các inventory batch bằng `SELECT ... FOR UPDATE`.
- [x] Chọn batch theo expiry date rồi received-at (FEFO).
- [x] Tạo order, order item và stock reservation trong một transaction.
- [x] Tăng `quantity_reserved` và ghi `stock_ledger` event `reserve`.
- [x] Replay cùng idempotency key trả order cũ.
- [x] Payload khác hoặc user khác với cùng key trả `409`.
- [x] Thiếu hàng trả `409 STOCK_INSUFFICIENT` và rollback transaction.
- [x] Thêm tests checkout success, replay, conflict và insufficient stock.

### Kết quả

- Pytest: `5 passed`.
- Checkout smoke flow chạy được trên PostgreSQL local.
- Đã rà và sửa transaction boundary sau truy vấn idempotency để không lồng transaction sai.

### Giới hạn còn lại

- Chưa có cancel/fulfil endpoint để release/decrement reservation.
- Chưa có concurrency test thật với nhiều request đồng thời.
- Chưa validate expired batch bằng rule engine; hiện chỉ chọn batch status `available`.

## 2026-11-03 — Cancel/fulfil order và expired-batch guard

### Đã làm

- [x] Thêm `POST /api/v1/orders/{order_id}/cancel`.
- [x] Cancel khóa order/batch, release reservation và ghi ledger event `release`.
- [x] Customer chỉ cancel được order của mình; merchant/admin có thể xử lý order store.
- [x] Thêm `POST /api/v1/orders/{order_id}/fulfil` cho merchant/admin.
- [x] Fulfil giảm on-hand/reserved, chuyển batch về depleted khi hết hàng và ghi ledger event `fulfil`.
- [x] Loại batch hết hạn khỏi product availability và checkout.
- [x] Thêm tests cancel release và merchant fulfil.

### Kết quả

- Pytest: `7 passed`.
- `git diff --check`: không có lỗi.
- Checkout lifecycle hiện có create → reserve → cancel/release hoặc fulfil.

### Giới hạn còn lại

- Chưa có concurrency test thật với nhiều process/request.
- Chưa có merchant user seed cố định.
- Chưa có business rule cấu hình riêng cho expiry warning/low stock.

## 2026-11-03 — Inventory read API và business alerts

### Đã làm

- [x] Tạo rule functions cho `DO_NOT_SELL_EXPIRED`, `EXPIRY_WARNING`, `LOW_STOCK_ALERT`.
- [x] Tạo `GET /api/v1/inventory` cho merchant/admin.
- [x] Hỗ trợ lọc `store_id`, `product_id`, `low_stock_only` và threshold cấu hình.
- [x] Tính on-hand, reserved, available và nearest expiry theo store/product.
- [x] Loại batch expired khỏi số lượng sellable.
- [x] Thêm test merchant inventory access và alerts shape.

### Kết quả

- Pytest: `8 passed`.
- `git diff --check`: không có lỗi.
- Chưa cần branch mới; vẫn cùng database/inventory foundation.

### Giới hạn còn lại

- Supplier/Purchase Order là module độc lập tiếp theo; trước khi làm sẽ tạo branch mới và báo trước.
- Reorder point chưa có cột/model; LOW_STOCK_ALERT hiện dùng threshold request.

## 2026-11-03 — Hoàn thiện catalog và auth tests

### Đã làm

- [x] Đổi `GET /api/v1/products` sang response pagination `{items, page, page_size, total}`.
- [x] Thêm query `q`, `category_id`, `page`, `page_size`.
- [x] Thêm `GET /api/v1/products/{product_id}`.
- [x] Bổ sung test pagination, product detail và 404.
- [x] Bổ sung test register/login/me, missing token và invalid password.
- [x] Chạy toàn bộ test suite và `git diff --check`.

### Kết quả

- Pytest: `3 passed`.
- Catalog có 3 sản phẩm seed và available quantity từ inventory batch.
- Auth test xác nhận access token và 401 cho request thiếu/sai credential.

### Lưu ý

- Đây là thay đổi response của Products API theo contract pagination; frontend cần đọc `response.items` thay vì dùng response list trực tiếp.

## 2026-11-03 — Smoke test server đang chạy

### Đã làm

- [x] Gọi `GET /health` từ PowerShell ngoài tiến trình Uvicorn.
- [x] Gọi `GET /api/v1/categories`.
- [x] Gọi `GET /api/v1/products`.
- [x] Chạy register với email smoke test ngẫu nhiên.
- [x] Chạy login và xác nhận access token.
- [x] Gọi `/api/v1/auth/me` với Bearer token.
- [x] Gọi `/openapi.json` để kiểm tra Swagger route registration.

### Kết quả

- Health: `status=ok`, `database=connected`.
- Categories: 3 bản ghi.
- Products: 3 bản ghi.
- Register: thành công.
- Login: access token được tạo.
- Me: trả đúng user smoke test.
- OpenAPI: có auth, catalog và health routes.

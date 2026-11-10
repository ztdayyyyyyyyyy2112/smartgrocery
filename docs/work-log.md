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

## 2026-11-03 — Procurement schema foundation

### Đã làm

- [x] Tạo models `suppliers` và `supplier_products`.
- [x] Tạo `PurchaseOrderStatus` theo lifecycle draft → approval → sent → receiving.
- [x] Tạo models `purchase_orders`, `purchase_order_items` và `goods_receipts`.
- [x] Thêm migration `0004_procurement`.
- [x] Chạy migration trên PostgreSQL local.
- [x] Chạy toàn bộ test suite và `git diff --check`.

### Kết quả

- Alembic current: `0004_procurement (head)`.
- Pytest: `8 passed`.
- Chưa có procurement API; lượt tiếp theo sẽ làm supplier/PO endpoints và state transition tests.

## 2026-11-03 — Procurement API và receiving workflow

### Đã làm

- [x] `GET/POST /api/v1/suppliers` cho merchant/admin.
- [x] `POST /api/v1/purchase-orders` với trạng thái `pending_approval`.
- [x] `GET /api/v1/purchase-orders`.
- [x] Approval transition: `pending_approval → approved`.
- [x] Send transition: `approved → sent`.
- [x] Receiving transition từ `sent/partially_received`.
- [x] Receiving tạo goods receipt, inventory batch và stock ledger event `receive` trong cùng transaction.
- [x] Kiểm tra quantity received không vượt quantity ordered.
- [x] Thêm integration test cho toàn bộ PO lifecycle.

### Lỗi phát hiện và sửa

- FastAPI không thể dùng SQLAlchemy model làm response type trực tiếp.
- Đã thêm `SupplierResponse` Pydantic schema với `from_attributes`.

### Kết quả

- Pytest: `9 passed`.
- `git diff --check`: không có lỗi.

### Giới hạn còn lại

- Chưa có cancel PO endpoint.
- Chưa có supplier product CRUD endpoint.
- Chưa có receiving partial-flow test riêng.

## 2026-11-03 — Hoàn thiện procurement state transitions

### Đã làm

- [x] Thêm `PUT/GET /api/v1/suppliers/{supplier_id}/products`.
- [x] Thêm `POST /api/v1/purchase-orders/{po_id}/cancel`.
- [x] Chặn cancel PO sau khi đã nhận một phần/toàn bộ.
- [x] Thêm test receiving một phần và kiểm tra trạng thái `partially_received`.
- [x] Thêm test supplier product upsert/list.
- [x] Thêm test cancel PO.

### Kết quả

- Pytest: `11 passed`.
- `git diff --check`: không có lỗi.
- Procurement P0 hiện đã có supplier, supplier product, PO create/list/approve/send/cancel/receive.

### Giới hạn còn lại

- Chưa có API PATCH supplier.
- Chưa có test quyền 403 riêng cho toàn bộ procurement routes.
- Chưa có background receiving event/outbox.

## 2026-11-03 — Procurement permission and transition regression tests

### Đã làm

- [x] Test customer bị từ chối truy cập supplier (`403`).
- [x] Test PO send khi chưa approve bị từ chối (`409`).
- [x] Kiểm tra danh sách procurement routes được đăng ký trong FastAPI.
- [x] Chạy lại toàn bộ test suite.

### Kết quả

- Pytest: `13 passed`.
- Procurement routes được đăng ký đầy đủ.
- Một lệnh kiểm tra route ban đầu chạy sai thư mục và báo `ModuleNotFoundError: app`; đã chạy lại đúng trong `services/api`, không phải lỗi ứng dụng.
- `git diff --check`: không có lỗi.

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

## 2026-11-03 — Kiểm tra workflow sau khi Docker Desktop gặp lỗi WSL

### Đã làm

- [x] Kiểm tra branch và thay đổi hiện tại: đang ở `feat/be-procurement`, các thay đổi procurement vẫn chưa commit.
- [x] Xác nhận PostgreSQL Windows đang chạy để không làm gián đoạn backend.
- [x] Chạy toàn bộ test từ thư mục root bằng virtualenv của API.
- [x] Kiểm tra Docker Engine; Docker CLI chưa kết nối được do lỗi Docker Desktop/WSL và quyền truy cập pipe.

### Kết quả

- Pytest: `13 passed`.
- Có 2 cảnh báo không làm fail test: cảnh báo deprecation của Starlette và pytest cache path.
- Không phát hiện lỗi test ứng dụng trong lần kiểm tra này.

### Blocker / hỗ trợ cần thiết

- Docker Desktop hiện chưa hoạt động ổn định sau lỗi `componentsVersion.json`/WSL. Không thực hiện reset hoặc unregister WSL để tránh mất dữ liệu.
- Có thể tiếp tục phát triển bằng PostgreSQL Windows; khi cần Docker, người dùng cần Restart/Repair Docker Desktop rồi kiểm tra lại `docker info`.

## 2026-11-03 — Bổ sung kiểm thử inactive-user

### Đã làm

- [x] Bổ sung regression test xác nhận tài khoản bị vô hiệu hóa không thể đăng nhập.
- [x] Chạy lại toàn bộ test suite và kiểm tra diff formatting.

### Kết quả

- Pytest: `14 passed`.
- `git diff --check`: đạt.

## 2026-11-05 — Xác minh database sạch cho release

- [x] Tạo database PostgreSQL riêng `smartgrocery_test`.
- [x] Chạy thành công migrations từ `0001` đến `0006`.
- [x] Chạy seed trên database mới.
- [x] Chạy toàn bộ test: `24 passed, 1 warning`.
- [x] Không reset hoặc thay đổi database phát triển `smartgrocery`.

## 2026-11-05 — Khởi tạo Celery worker/retry

### Đã làm

- [x] Thêm Celery + Redis dependency và cấu hình broker/result backend qua environment.
- [x] Cấu hình `acks_late`, `reject_on_worker_lost`, `track_started` và retry khi worker bị gián đoạn.
- [x] Thêm task `run_outbox_batch` với backoff/jitter, tối đa 3 lần retry.
- [x] Bổ sung test cấu hình worker và chạy regression suite.

### Kết quả

- Worker configuration test: passed.
- Toàn bộ test: `25 passed`.

## 2026-11-05 — Edge-case tests

- [x] Expired batch không xuất hiện trong available quantity.
- [x] Sparse SKU không có inventory trả available quantity bằng 0.
- [x] Zero-demand forecast được lưu với predicted quantity 0 và không tạo recommendation giả.
- [x] Chạy toàn bộ test suite: `29 passed`.

## 2026-11-05 — Security hardening Critical 1/7

- [x] Production settings từ chối JWT default secret hoặc secret ngắn hơn 32 ký tự.
- [x] JWT dùng `SecretStr` và chỉ lấy giá trị khi ký/giải mã token.
- [x] Checkout từ chối duplicate `product_id` trong cùng order với HTTP `422`.
- [x] Bổ sung regression tests cho hai lỗi trên.

### Kết quả

- Toàn bộ test: `32 passed`.

## 2026-11-05 — Security hardening C6 WebSocket

- [x] WebSocket yêu cầu access JWT khi handshake.
- [x] Chỉ merchant/admin được kết nối.
- [x] Giới hạn tối đa 100 kết nối process và từ chối khi vượt giới hạn.
- [x] Bổ sung test authenticated/unauthenticated WebSocket.
- [x] Toàn bộ test: `33 passed`.

## 2026-11-05 — Observability hardening

- [x] Thêm middleware tạo/bảo toàn `X-Request-ID`.
- [x] Map IntegrityError thành `409` và OperationalError thành `503`.
- [x] Chuẩn hóa lỗi nội bộ thành response `500` không lộ stack trace.
- [x] Bổ sung test request ID; toàn bộ suite đạt `34 passed`.

## 2026-11-05 — Rate limiting auth

- [x] Thêm Redis-backed rate limiter cho register (5/giờ/email).
- [x] Thêm Redis-backed rate limiter cho login (5/phút/email).
- [x] Production fail-closed khi rate limiter unavailable; development fail-open để không chặn local.
- [x] Bổ sung test vượt ngưỡng `429`; toàn bộ suite đạt `35 passed`.

## 2026-11-05 — Hot query indexes

- [x] Thêm migration `0007_hot_query_indexes` cho inventory, orders, purchase orders, forecasts và recommendations.
- [x] Alembic upgrade `0006 -> 0007` thành công.
- [x] Toàn bộ test: `35 passed`.

### Blocker cần nhóm xác nhận

- Store-level authorization cần thống nhất bảng/quan hệ `user_stores` trong ERD trước khi triển khai để tránh tự ý đổi contract/schema.
- Còn tiếp tục: store-level authorization, forecast result protection, rate limiting, WebSocket auth và global observability.

## 2026-11-05 — Security hardening C4 forecast result

- [x] Khóa forecast job bằng `FOR UPDATE` trong transaction.
- [x] Kiểm tra product active và target date nằm trong job horizon.
- [x] Giữ job terminal, không cho hoàn tất lại hoặc race completion.
- [x] Toàn bộ test: `32 passed`.

Hai lỗi ban đầu chỉ nằm trong test (format Decimal và detached SQLAlchemy object), đã sửa và xác nhận lại.
- Redis broker thật chưa chạy; cần integration test khi nhóm có Redis/Docker ổn định.
- Redis broker đã được chạy thực tế bằng Docker; Celery worker connected và `run_outbox_batch` succeeded với `published=12, failed=0`.

## 2026-11-05 — Scheduled refresh và WebSocket realtime

### Đã làm

- [x] Thêm Celery Beat schedule publish outbox mỗi phút và refresh forecast mỗi giờ.
- [x] Thêm task `refresh_forecast_jobs` chỉ đếm job queued, không tự sinh forecast giả.
- [x] Thêm WebSocket endpoint `/ws/events` và connection manager xử lý disconnect.
- [x] Bổ sung test WebSocket và schedule configuration.

### Kết quả

- Toàn bộ test: `26 passed`.
- `git diff --check`: đạt.
- WebSocket hiện là transport nền; broadcast event thực tế cần nối vào outbox consumer/frontend.

## 2026-11-05 — Load test 50/100/200 request

- [x] Chạy load probe read-only trên `/health` với 50 request / concurrency 10.
- [x] Chạy 100 request / concurrency 20.
- [x] Chạy 200 request / concurrency 40.
- [x] Ghi throughput và latency vào `docs/load-test-results.md`.

### Kết quả

- 50: `50/50` thành công, `148.89 req/s`, p50 `29.11 ms`.
- 100: `100/100` thành công, `261.50 req/s`, p50 `64.10 ms`.
- 200: `200/200` thành công, `329.31 req/s`, p50 `118.18 ms`.

### Percentile rerun

- 50: `203.20 req/s`, p50/p95/p99 `27.80/97.22/136.63 ms`, max `136.63 ms`.
- 100: `251.27 req/s`, p50/p95/p99 `65.11/138.95/186.13 ms`, max `186.13 ms`.
- 200: `341.90 req/s`, p50/p95/p99 `99.27/196.84/217.17 ms`, max `219.18 ms`.

## 2026-11-05 — RBAC/security matrix hardening

### Đã làm

- [x] Kiểm tra endpoint merchant-only khi thiếu token trả `401`.
- [x] Kiểm tra customer truy cập inventory/forecast/supplier bị từ chối `403`.
- [x] Chạy lại toàn bộ test suite.

### Kết quả

- Toàn bộ test: `24 passed`.
- `git diff --check`: đạt.

## 2026-11-05 — Hardening tests trên branch `feat/be-hardening-tests`

### Đã làm

- [x] Bổ sung test job failure thiếu `error_message` trả `422`.
- [x] Bổ sung test job terminal không thể complete lại sau khi đã `failed`.
- [x] Chạy lại toàn bộ test suite và kiểm tra diff.

### Kết quả

- Pytest: `22 passed`.
- `git diff --check`: đạt.
- Concurrency test thực tế vẫn cần chạy riêng với nhiều session PostgreSQL; chưa tự giả lập bằng dữ liệu dùng chung.

## 2026-11-05 — Concurrency checkout hardening

### Đã làm

- [x] Tạo test với hai PostgreSQL session/requests đồng thời trên SKU chỉ có 1 đơn vị tồn kho.
- [x] Xác nhận cơ chế `SELECT ... FOR UPDATE` ngăn oversell: một request thành công, một request `409 STOCK_INSUFFICIENT`.
- [x] Chạy lại toàn bộ suite.

### Kết quả

- Concurrency test: `1 passed`.
- Toàn bộ test: `23 passed`.
- `git diff --check`: đạt.
- Hai cảnh báo hiện tại vẫn là cảnh báo môi trường/deprecation, không làm fail test.

### Bước tiếp theo

- Tiếp tục triển khai outbox/event model cho các nghiệp vụ order, inventory và procurement.

## 2026-11-03 — Triển khai transactional outbox

### Đã làm

- [x] Thêm model `OutboxEvent` với trạng thái publish, số lần retry và payload JSONB.
- [x] Thêm migration `0005_outbox` và chạy thành công trên database hiện tại.
- [x] Thêm helper `enqueue_event()` để ghi event trong cùng transaction nghiệp vụ.
- [x] Tích hợp event cho order confirmed/cancelled/fulfilled và purchase-order created/status/cancelled/received.
- [x] Chạy toàn bộ test suite và `git diff --check`.

### Kết quả

- Alembic: `0004_procurement -> 0005_outbox` thành công.
- Pytest: `14 passed`.
- Chưa có worker publish/retry; hiện outbox đã sẵn sàng làm nguồn dữ liệu cho background worker tiếp theo.

## 2026-11-03 — Bổ sung polling worker cho outbox

### Đã làm

- [x] Thêm `publish_pending_events()` với batch limit, `FOR UPDATE SKIP LOCKED`, attempts và retry an toàn.
- [x] Thêm script `services/api/scripts/publish_outbox.py` để chạy một lượt bằng Task Scheduler/cron.
- [x] Sửa import path để script chạy trực tiếp từ thư mục API.

### Kết quả

- Worker chạy thành công: `outbox published=32 failed=0`.
- Test suite vẫn đạt `14 passed`.
- `git diff --check`: đạt.

### Giới hạn hiện tại

- `noop_publisher` mới là adapter cục bộ; cần nối message broker/webhook thật khi nhóm thống nhất hạ tầng tích hợp.

## 2026-11-03 — Kiểm thử retry outbox

### Đã làm

- [x] Thêm test publish thành công: event được đánh dấu `published_at` và tăng attempts.
- [x] Thêm test publisher lỗi: event giữ pending để retry và attempts được ghi nhận.
- [x] Xử lý dữ liệu pending cũ trong test để kết quả ổn định.

### Kết quả

- Pytest: `16 passed`.
- `git diff --check`: đạt.
- Không còn lỗi cần hỗ trợ.

## 2026-11-05 — Khởi tạo Forecast/Job API trên branch `feat/be-forecast-jobs`

### Đã làm

- [x] Tạo migration `0006_forecast_jobs` cho jobs, demand forecasts và replenishment recommendations.
- [x] Thêm model và enum trạng thái queued/running/succeeded/failed, pending/approved/rejected/converted.
- [x] Thêm `POST /jobs/forecasts` và `GET /jobs/{job_id}` với RBAC merchant/admin.
- [x] Thêm `GET /forecasts`, `GET /recommendations`, approve/reject recommendation.
- [x] Thêm test customer bị từ chối và merchant queue/poll job.

### Kết quả

- Alembic `0005_outbox -> 0006_forecast_jobs`: thành công.
- Pytest: `18 passed`.
- Chưa tự sinh forecast khi chưa có worker inference; job mới dừng ở trạng thái `queued` đúng contract.

## 2026-11-05 — Nhận output Intelligence và xử lý job failure

### Đã làm

- [x] Thêm `POST /jobs/{job_id}/result` để nhận output forecast/recommendation.
- [x] Job thành công lưu forecast/recommendation và chuyển `succeeded`.
- [x] Job lỗi bắt buộc `error_message`, chuyển `failed` và không sinh forecast giả.
- [x] Bổ sung test success/failure; nhóm Forecast đạt `3 passed`.

### Vấn đề phát hiện

- Chạy toàn bộ suite hiện có `3` test checkout fail `409 STOCK_INSUFFICIENT` do database test dùng chung đã bị giảm tồn kho sau nhiều lần chạy.
- Đây là vấn đề test isolation/seed reset, không phải lỗi Forecast API; cần xử lý trước khi chốt PR.

## 2026-11-05 — Sửa test isolation cho checkout

### Đã làm

- [x] Thêm pytest fixture tự động khôi phục tồn kho sản phẩm milk trước mỗi checkout test.
- [x] Fixture reset `quantity_on_hand`, `quantity_reserved` và batch status trong phạm vi test; không reset database ứng dụng thủ công.
- [x] Chạy lại toàn bộ backend test suite.

### Kết quả

- Pytest: `19 passed`.
- `git diff --check`: đạt.
- Hai cảnh báo còn lại là deprecation/cache warning, không làm fail test.

## 2026-11-05 — Integration E2E checkout → receiving

### Đã làm

- [x] Tạo integration test cho toàn bộ flow checkout → inventory → forecast job → recommendation → PO → receiving.
- [x] Kiểm tra liên kết giữa recommendation convert và supplier product/unit cost.
- [x] Chạy test riêng và toàn bộ backend suite.

### Kết quả

- Integration test: `1 passed`.
- Toàn bộ suite: `21 passed`.
- `git diff --check`: đạt.

## 2026-11-05 — Hoàn thiện Recommendation approve/convert-to-PO

### Đã làm

- [x] Approve recommendation thông thường.
- [x] Hỗ trợ `convert_to_po=true` với `supplier_id`.
- [x] Kiểm tra supplier và supplier-product mapping trước khi tạo PO.
- [x] Tạo PO `pending_approval`, thêm PO item theo suggested quantity/unit cost.
- [x] Chuyển recommendation sang `converted` và bổ sung test workflow.

### Kết quả

- Pytest: `20 passed`.
- `git diff --check`: đạt.

## 2026-11-05 — Cập nhật tiến độ tổng thể

### Đã hoàn thành

- Backend core, procurement, outbox, forecast/job, recommendation và integration E2E đã merge vào `develop`.
- Celery/Redis worker đã chạy thực tế; outbox task xử lý thành công.
- Celery Beat schedule và WebSocket endpoint đã có test.
- Load test `/health` 50/100/200 request đạt 100% success; p99 cao nhất `217.17 ms`.
- Edge-case suite và hardening suite đã nâng tổng kiểm thử lên `29 passed`.
- Database sạch đã chạy migration/seed thành công; schema backup PostgreSQL 18.6 đã tạo.
- Release tag `v1.0.0` đã xác nhận trên GitHub.
- Đã tạo backend runbook tại `docs/backend-runbook.md`.

### Còn lại

- Nối broadcast event thật từ outbox tới frontend/WebSocket.
- Nếu cần production evidence: load test trên business endpoint và staging.
- Hoàn thiện nội dung báo cáo nhóm, sơ đồ/logs và phần limitations.
## 2026-11-05 — Refresh token rotation

- Added refresh token persistence and migration `0008_refresh_tokens`.
- Register/login now return access and refresh tokens.
- Added `/api/v1/auth/refresh` with rotation and revocation of the previous token.
- Added unique JWT `jti` claims to prevent token hash collisions on rapid issuance.
- Verification: Alembic upgrade succeeded; `35 passed`; `git diff --check` passed.
## 2026-11-05 — Redis outbox publisher

- Replaced the Celery outbox task's no-op publisher with a Redis publisher.
- Events are serialized to the `smartgrocery:events` channel with stable metadata and payload.
- Added a unit test for event serialization and resource cleanup.
- Verification: `36 passed`; `git diff --check` passed.
## 2026-11-05 — Redis to WebSocket event stream

- WebSocket `/ws/events` now subscribes to `smartgrocery:events`.
- Authenticated merchant/admin connections forward valid JSON events to clients.
- Subscriber cleanup runs when the connection closes.
- Verification: Redis/WebSocket end-to-end test and full suite pass (`37 passed`).
## 2026-11-06 — Backend checklist status refresh

- Recorded the merged refresh-token, Redis outbox publisher, and Redis-to-WebSocket work.
- Clarified that frontend WebSocket UX and forecast intelligence inference are cross-team items, not standalone Backend tasks.
- Current backend verification baseline: `37 passed`.
## 2026-11-06 — Business endpoint load test

- Verified `GET /api/v1/products` under 50/10, 100/20, and 200/40 request/concurrency profiles.
- Success rate was 100% for all profiles.
- Highest observed p99 latency was `377.51 ms`; highest throughput was `192.93 RPS`.
- Recorded results in `docs/release-evidence.md`.
## 2026-11-06 — Security/RBAC matrix verification

- Added regression coverage for merchant success, inactive-user rejection, and missing-resource `404`.
- Confirmed existing unauthenticated/customer `401`/`403` coverage.
- Redis was restarted for realtime tests; full suite result: `38 passed, 1 warning`.
## 2026-11-06 — Final backend handoff preparation

- Consolidated release evidence, checklist status, and runbook verification.
- Alembic upgrade passed and full suite completed with `38 passed, 2 warnings`.
- Recorded remaining Frontend and Intelligence/Forecast ownership explicitly.

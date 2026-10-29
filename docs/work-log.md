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

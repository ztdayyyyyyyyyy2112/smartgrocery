# Tuấn Anh — Backend / Database / Rule Engine Checklist

Phạm vi theo `SmartGrocery_TaskPlan_26-10_to_18-11-2026.pdf`:

- FastAPI, PostgreSQL và migrations
- Authentication/RBAC
- Orders, checkout, stock reservation và idempotency
- Inventory batches, FEFO và rule engine
- Suppliers, purchase orders và goods receiving
- Forecast/job APIs và inventory events
- Integration, concurrency, security, deployment và backend evidence

## Cách theo dõi

- `[ ]` Chưa bắt đầu
- `[~]` Đang làm
- `[x]` Hoàn thành: phải có code, test chạy được, commit và Pull Request đã gửi để review
- Mỗi task dùng một branch riêng, tạo từ `develop` đã cập nhật.
- Không push trực tiếp vào `main` hoặc `develop`.
- Không đổi ERD/API contract nếu chưa được nhóm thống nhất.

## Quy trình GitHub cho từng task

```powershell
git switch develop
git pull --ff-only origin develop
git switch -c feat/be-<task-name>

# làm code và test
git add services/api database docs tests
git commit -m "feat(api): <mô tả ngắn>"
git push -u origin feat/be-<task-name>
```

Sau đó mở PR `feat/be-<task-name> -> develop`, ghi rõ chức năng, lệnh test, log/kết quả và vấn đề còn lại. Chỉ bắt đầu task kế tiếp sau khi PR được review/merge; khi merge xong cập nhật lại `develop` bằng `git pull --ff-only`.

## Checklist theo deadline

### 27/10 — Thiết kế và contract

- [x] Đọc và đối chiếu ERD tại `docs/architecture/erd.md`.
- [x] Đọc RBAC tại `docs/architecture/rbac.md`.
- [x] Đọc REST contract tại `docs/api/rest-api-v1.md`.
- [ ] Xác nhận với nhóm các enum, trường bắt buộc, trạng thái đơn hàng và quy tắc FEFO.
- [ ] Xác nhận vị trí migration/seed: `services/api/alembic` hay `database/migrations`.
- [ ] Ghi lại các điểm contract đã được nhóm chốt trong PR/ticket.

### 28/10 — FastAPI, PostgreSQL, migrations và seed

- [ ] Tạo/hoàn thiện cấu hình FastAPI và database connection.
- [ ] Tạo SQLAlchemy models theo ERD.
- [ ] Tạo migration cho users, stores, categories, products.
- [ ] Tạo migration cho inventory batches, orders, order items, reservations và idempotency.
- [ ] Tạo migration cho suppliers, purchase orders, goods receipts.
- [ ] Tạo migration cho forecasts, recommendations, jobs và business rules.
- [ ] Tạo seed tối thiểu: user/role, store, categories, products, batches và suppliers.
- [ ] Chạy migration trên database sạch và kiểm tra rollback cần thiết.
- [ ] Bằng chứng: log migration, kiểm tra bảng/seed và test backend.

### 29/10 — Authentication, RBAC và Products API

- [ ] Register/login/refresh/me.
- [ ] Hash password bằng Argon2 hoặc bcrypt; không lưu plaintext.
- [ ] JWT access token 15 phút và refresh token được lưu dạng hash.
- [ ] Guard customer, merchant và admin theo RBAC contract.
- [ ] `GET /categories`, `GET /products`, `GET /products/{id}`.
- [ ] Catalog chỉ tính available quantity từ batch còn bán được.
- [ ] Test 401, 403, 404, inactive user và customer scope.

### 30/10 — Orders, checkout và reservation

- [ ] `POST /orders` với `Idempotency-Key` bắt buộc.
- [ ] Transaction checkout khóa batch bằng `SELECT ... FOR UPDATE`.
- [ ] Reserve stock theo FEFO.
- [ ] Từ chối atomic khi thiếu stock; không để reservation dở dang.
- [ ] Replay cùng payload trả lại order cũ.
- [ ] Replay khác payload trả `409 IDEMPOTENCY_CONFLICT`.
- [ ] Orders list/detail/cancel/fulfil.
- [ ] Test checkout thành công, thiếu hàng, hủy đơn và hai checkout đồng thời.

### 31/10 — Inventory batches, FEFO và rule engine

- [ ] Inventory position: on-hand, reserved, available, nearest expiry.
- [ ] Batch status: available, depleted, expired, quarantined.
- [ ] Quarantine batch và loại khỏi số lượng bán được.
- [ ] FEFO: expiry sớm trước, sau đó received-at sớm trước.
- [ ] `DO_NOT_SELL_EXPIRED`.
- [ ] `EXPIRY_WARNING` với ngưỡng cấu hình.
- [ ] `LOW_STOCK_ALERT` theo reorder point hoặc threshold.
- [ ] Test edge cases expiry, reserved quantity và nhiều batch.

### 01/11 — Suppliers, Purchase Orders và Receiving

- [ ] CRUD suppliers và supplier products.
- [ ] Tạo PO với lifecycle draft/pending approval/approved/sent.
- [ ] Approval đúng role và trạng thái.
- [ ] Receive một phần/toàn bộ PO.
- [ ] Receiving tạo goods receipt và inventory batches.
- [ ] Cập nhật quantity received và PO status chính xác.
- [ ] Chặn receive/cancel sai trạng thái.

### 02/11 — AI integration và inventory alerts

- [ ] `POST /jobs/forecasts` và `GET /jobs/{job_id}`.
- [ ] `GET /forecasts` và `GET /recommendations`.
- [ ] API nhận output forecast/recommendation theo contract.
- [ ] Không tự sinh forecast khi inference thất bại; lưu job failed.
- [ ] Inventory alerts đọc được từ storefront/dashboard.
- [ ] Chạy end-to-end: checkout → inventory → forecast → recommendation → PO.
- [ ] Đóng băng API contract sau buổi demo.

### 03–05/11 — Background jobs và integration

- [ ] Outbox/event model cho inventory/order events.
- [ ] Celery worker, retry và xử lý interruption.
- [ ] Scheduled forecast refresh.
- [ ] API integration tests với database sạch.
- [ ] Regression test luồng checkout → receiving.
- [ ] 05/11: không thêm feature mới, chỉ sửa integration/blocker.

### 06–09/11 — Test, security, deployment và release candidate

- [ ] Concurrency tests ở mức 50/100/200 request theo khả năng môi trường.
- [ ] RBAC/security/failure/retry tests.
- [ ] Test sparse SKU, zero demand, expired batch và job failure.
- [ ] Docker Compose chạy được backend + PostgreSQL + Redis/worker nếu đã tích hợp.
- [ ] Cập nhật API docs, seed và README clone-to-run.
- [ ] Lưu logs, test results và evidence cho báo cáo.

### 10/11 — Backend freeze và nghiệm thu

- [ ] README có hướng dẫn chạy lại từ clone mới.
- [ ] Checkout → cập nhật tồn kho → dự báo → đề xuất → phê duyệt → nhận hàng chạy được.
- [ ] Không còn lỗi nghiêm trọng trong acceptance flow.
- [ ] Schema backup và API/test logs đã lưu.
- [ ] PR/release tag `v1.0.0` được review và chấp nhận.

## Báo cáo hằng ngày

Mỗi ngày cập nhật cuối file hoặc PR với:

- Completed
- Branch, commit, PR
- Tests và bằng chứng chạy được
- Blockers
- Next tasks

## Trạng thái hiện tại — 28/10/2026

- `[~]` FastAPI setup, database connection và migration extension đã có trong working tree.
- `[ ]` Models nghiệp vụ, schema đầy đủ và seed.
- `[ ]` Authentication/RBAC.
- `[ ]` Products API.
- `[ ]` Orders/checkout/reservation.
- `[ ]` Inventory/FEFO/rule engine.
- `[ ]` Procurement/receiving.
- `[ ]` Forecast/job integration.
- `[ ]` Background jobs, integration, security và release evidence.

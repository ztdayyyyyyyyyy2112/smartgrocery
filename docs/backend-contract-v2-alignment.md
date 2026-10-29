# Backend Contract v2 Alignment Draft

Ngày lập: 29/10/2026  
Phạm vi: Backend/Database/Rule Engine của Tuấn Anh

Đây là bản đề xuất để đối chiếu giữa định hướng đồ án mới, kế hoạch PDF và REST/ERD contract hiện tại. Tài liệu này chưa thay thế contract chính thức và chưa được dùng làm lý do tự ý đổi API.

## 1. Nguyên tắc giữ ổn định

- PostgreSQL là nguồn sự thật cho transaction và trạng thái nghiệp vụ.
- FastAPI sở hữu HTTP API, quyền truy cập và transaction.
- Intelligence xử lý forecasting/decision, nhưng không ghi database trực tiếp.
- Frontend không tự quyết định tồn kho, FEFO, quyền hoặc trạng thái PO.
- Mọi thay đổi table, required field, enum hoặc route phải qua review nhóm.

## 2. Đề xuất mô hình tồn kho

### Nguồn sự thật

`inventory_batches` giữ số lượng hiện tại theo từng lô; `stock_ledger` ghi lịch sử bất biến của mọi biến động. Hai bảng có vai trò khác nhau:

- Batch dùng để đọc số lượng bán được nhanh và thực hiện FEFO.
- Ledger dùng để audit: receiving, reservation, release, fulfil, adjustment, quarantine.
- `available = quantity_on_hand - quantity_reserved`; không tính available bằng cách cộng ledger trong request đọc thông thường.

Mỗi thay đổi batch phải nằm cùng transaction với một ledger entry. Nếu một request làm thay đổi nhiều batch, tất cả batch update và ledger entries phải commit/rollback cùng nhau.

### Stock ledger tối thiểu

Các field đề xuất: `id`, `store_id`, `product_id`, `batch_id`, `event_type`, `quantity_delta`, `reference_type`, `reference_id`, `created_by`, `created_at`.

Event type dự kiến: `receive`, `reserve`, `release`, `fulfil`, `adjust`, `quarantine`.

Đây là đề xuất schema, cần nhóm xác nhận trước migration.

## 3. Đề xuất Rule Engine

Rule Engine chạy trong backend business layer ở MVP để bảo đảm checkout và inventory dùng cùng transaction boundary. Intelligence có thể cung cấp forecast và risk inputs, nhưng không tự quyết định trạng thái kho.

Mỗi lần suy luận nên có:

- facts đầu vào: available, forecast, lead time, expiry, reorder point;
- rule code và version;
- kết luận: candidate/alert hoặc no-action;
- explanation text;
- timestamp và reference đến forecast/job.

`inference_traces` là đề xuất để lưu bằng chứng suy luận. Có thể triển khai sau P0 nếu nhóm xác nhận chỉ cần log JSON cho MVP.

## 4. Đề xuất forecast và decision boundary

- Intelligence trả forecast theo store-SKU-day, model name, version và generated timestamp.
- Backend lưu forecast và recommendation sau khi validate schema.
- Rule Engine quyết định có tạo `ReplenishmentCandidate` hay không.
- Decision Engine tính expected utility/cost giữa các phương án nhập.
- Recommendation không tự động tạo PO nếu chưa có merchant approval.

`model_runs` được đề xuất để lưu run metadata, metrics và artifact version; chưa bắt buộc đưa vào migration đầu tiên nếu nhóm chỉ cần evidence trong report.

## 5. PO state machine dự kiến

```text
draft → pending_approval → approved → sent
sent → partially_received → received
draft/pending_approval/approved/sent → cancelled
```

Preconditions cần giữ:

- Chỉ merchant/admin được approve, send, receive.
- Không cancel sau khi đã received một phần, trừ khi nhóm chốt cơ chế riêng.
- Receive phải tạo goods receipt và batch mới trong cùng transaction.
- Nhận thiếu phải cập nhật `quantity_received`, status và ledger chính xác.

## 6. Phân loại ưu tiên triển khai

### P0 — cần có cho demo chính

- Users, roles, stores, products, categories.
- Inventory batches, reservations, stock ledger cơ bản.
- Orders, checkout, idempotency, FEFO và chống oversell.
- Suppliers, purchase orders, approval và receiving.
- Forecast storage, recommendation và rule explanation tối thiểu.

### P1 — làm sau khi P0 chạy ổn

- PO recovery khi giao trễ/nhận thiếu.
- Outbox, retry, duplicate event handling.
- WebSocket và commit-to-alert latency.
- `inference_traces` đầy đủ và `model_runs`.

### P2 — chỉ làm nếu còn dữ liệu/thời gian

- Chatbot, A*, genetic algorithm, reinforcement learning.

## 7. Quyết định làm việc được chọn

Các lựa chọn dưới đây được dùng làm baseline triển khai để không bị đứng chờ. Đây là working assumptions; nếu nhóm review khác đi, thay đổi phải đi qua PR contract riêng trước khi sửa schema đã merge.

- [x] `stock_ledger` là bắt buộc trong MVP. Lý do: đây là bằng chứng audit quan trọng và giúp kiểm thử transaction/concurrency.
- [x] `inference_traces` trước mắt lưu dưới dạng JSON trong bảng recommendation/job hoặc structured log; chưa tạo bảng riêng ở migration đầu tiên.
- [x] `model_runs` chưa tạo bảng riêng ở P0; lưu `model_name`, `model_version`, timestamp và metrics ở job/artifact trước. Tách bảng khi cần truy vấn lịch sử.
- [x] Rule Engine đặt trong FastAPI business package, chạy sau khi có inventory/forecast facts; không cho frontend hoặc ML service thay đổi tồn kho.
- [x] PO recovery là P1. P0 xử lý chính xác receiving một phần/toàn bộ và trạng thái lỗi rõ ràng.
- [x] Polling job status là P0; WebSocket là P1 sau khi outbox/retry ổn định.
- [x] `origin/docs/be-erd-rbac-api` là baseline contract hiện tại; v2 chỉ bổ sung phần cần thiết cho định hướng mới.

## 8. Việc tiếp theo

1. Chốt các ô trong mục 7.
2. Cập nhật ERD/API contract chính thức qua PR riêng.
3. Tạo database foundation migration theo contract đã merge.
4. Seed store, user roles, catalog, batches và supplier.
5. Chạy migration trên database sạch và lưu log làm evidence.

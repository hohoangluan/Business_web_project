# State Diagrams — Business Web Project

> Máy trạng thái cho các entity có vòng đời nhiều trạng thái (gộp entity giống nhau).
> Thứ tự block ⇒ `svg/state-diagrams-NN.svg`. Ma trận: `docs/diagrams/COVERAGE.md` §State.
>
> Danh sách dự kiến: ST-CONTRACT (3.x) · ST-FACECHANGE (4.x) · ST-ADJUST (4.7-4.8) ·
> ST-APPROVAL2 (leave/OT 5-6) · ST-REWARD (8.x) · ST-REPORT (9.1-9.2) · ST-TICKET (9.3-9.4).

---

## ST-CONTRACT — Vòng đời hợp đồng lao động (mục 3.x)

> Status hiển thị tính từ ngày (không lưu field); `is_active` là cờ versioning.

```mermaid
stateDiagram-v2
  [*] --> SapHieuLuc: tạo HĐ · start_date > hôm nay
  [*] --> KhongThoiHan: end_date trống
  [*] --> CoHieuLuc: start ≤ hôm nay ≤ end
  SapHieuLuc --> CoHieuLuc: tới ngày bắt đầu
  CoHieuLuc --> SapHetHan: days_left ≤ 30 (cảnh báo)
  SapHetHan --> HetHan: quá end_date
  CoHieuLuc --> HetHan: quá end_date
  SapHetHan --> Archived: gia hạn · adjust_contract
  CoHieuLuc --> Archived: tạo phiên bản mới · adjust_contract
  KhongThoiHan --> Archived: tạo phiên bản mới · adjust_contract
  HetHan --> Archived: expire_overdue_contracts · is_active=False
  Archived --> [*]
  note right of Archived
    is_active=False
    bản cũ giữ làm lịch sử
  end note
```

## ST-FACECHANGE — Vòng đời yêu cầu đổi khuôn mặt (mục 4.1–4.3, 4.9)

```mermaid
stateDiagram-v2
  [*] --> Approved: lần đầu / HR upload (auto-enroll)
  [*] --> Pending: self-service gửi ảnh mới
  Pending --> Approved: HR duyệt · apply enrollment · xóa ảnh tạm
  Pending --> Rejected: HR từ chối · giữ ảnh minh chứng
  Approved --> [*]
  Rejected --> [*]
  note right of Pending
    Mặt nhận diện vẫn là mặt cũ
    cho tới khi được duyệt
  end note
```

## ST-ADJUST — Vòng đời yêu cầu điều chỉnh chấm công (mục 4.7–4.8)

```mermaid
stateDiagram-v2
  [*] --> Pending: NV gửi yêu cầu · record=pending_adjustment
  Pending --> Approved: HR duyệt · áp giờ khai báo · recompute status
  Pending --> Rejected: HR từ chối · recompute status
  Approved --> [*]
  Rejected --> [*]
```

## ST-APPROVAL2 — Vòng đời đơn duyệt 2 bước · dùng chung Nghỉ phép & Tăng ca (mục 5.x, 6.x)

```mermaid
stateDiagram-v2
  [*] --> Pending: NV nộp đơn · có leader/manager
  [*] --> LeaderApproved: NV nộp đơn · trống cả 2 (bỏ L1, thẳng HR L2)
  [*] --> Approved: NV nộp đơn · trống cả 2 & là HR (tự duyệt)
  Pending --> LeaderApproved: L1 · supervisor trực tiếp duyệt
  Pending --> Approved: NV là HR · L1 hoàn tất (bỏ qua L2)
  Pending --> Rejected: L1 từ chối
  Pending --> Cancelled: NV tự hủy (chỉ khi còn Pending)
  LeaderApproved --> Approved: L2 · HR duyệt cuối
  LeaderApproved --> Rejected: L2 từ chối
  Approved --> [*]
  Rejected --> [*]
  Cancelled --> [*]
```

## ST-EVAL — Vòng đời phiếu đánh giá hiệu suất (mục 7.x)

```mermaid
stateDiagram-v2
  [*] --> Submitted: Manager/Leader lập phiếu · create_evaluation (status=submitted)
  Submitted --> Acknowledged: HR xác nhận · guard status==submitted · acknowledged_by/at
  Acknowledged --> [*]
  note right of Submitted
    Draft = default model nhưng app luôn tạo thẳng submitted
    (không có endpoint tạo/sửa draft)
  end note
  note right of Acknowledged
    Immutable · không có edit endpoint
  end note
```

## ST-REWARD — Vòng đời phiếu khen thưởng / xử phạt (mục 8.x)

> Điểm khác ST-APPROVAL2: vai trò **người lập** quyết định có qua L1 hay không
> (Leader → cần Manager L1; Manager/HR → bỏ L1). HR lập KHÔNG bỏ L2: vẫn cần
> HR duyệt cuối, và phải là **HR khác** vì hệ thống chặn tự duyệt phiếu của chính mình.

```mermaid
stateDiagram-v2
  [*] --> Pending: Leader lập (cần Manager L1)
  [*] --> LeaderApproved: Manager/HR lập (bỏ L1)
  Pending --> LeaderApproved: Manager duyệt L1
  Pending --> Rejected: L1 từ chối
  LeaderApproved --> Approved: HR duyệt L2 (≠ người lập)
  LeaderApproved --> Rejected: L2 từ chối
  Approved --> [*]
  Rejected --> [*]
  note right of LeaderApproved
    HR lập vẫn dừng ở đây chờ L2.
    Người duyệt L2 phải là HR khác
    (tự duyệt phiếu của mình bị chặn).
  end note
```

## ST-REPORT — Vòng đời báo cáo công việc (mục 9.1–9.2)

```mermaid
stateDiagram-v2
  [*] --> Submitted: NV gửi báo cáo
  Submitted --> NeedsUpdate: quản lý yêu cầu cập nhật (+manager_note)
  NeedsUpdate --> Submitted: tác giả sửa & gửi lại
  Submitted --> Acknowledged: quản lý tiếp nhận
  Acknowledged --> [*]
  note right of Acknowledged
    can_edit_or_delete = False (khóa sửa/xóa)
  end note
```

## ST-TICKET — Vòng đời ticket hỗ trợ/khiếu nại (mục 9.3–9.4)

```mermaid
stateDiagram-v2
  [*] --> New: NV tạo ticket
  New --> Processing: HR/Admin tiếp nhận (assigned_to)
  New --> Rejected: HR/Admin từ chối (+lý do)
  Processing --> Resolved: HR/Admin giải quyết
  Processing --> Closed: HR/Admin đóng
  Processing --> Rejected: HR/Admin từ chối (+lý do)
  Resolved --> [*]
  Closed --> [*]
  Rejected --> [*]
```

<!-- BUILD-CURSOR -->

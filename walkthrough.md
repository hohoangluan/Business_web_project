# 📘 HRMS – Project Walkthrough Toàn Diện

> **Hệ thống Quản lý Nhân sự (Human Resource Management System)**
> Môn học: SE104 – Nhập môn Công nghệ Phần mềm
> Stack: Django · SQLite3 · HTML/CSS/JS · Tailwind · Alpine.js · Remote Face API (DeepFace/Facenet512)

---

## 1. Tổng Quan Kiến Trúc

### 1.1 Tech Stack

| Tầng | Công nghệ |
|------|-----------|
| **Backend** | Django (Python) — MTV pattern |
| **Database** | SQLite3 (dev) → MySQL (production) |
| **Frontend** | HTML/CSS, Tailwind CSS, Alpine.js |
| **AI** | Nhận diện khuôn mặt chạy trên **service từ xa** (FastAPI + DeepFace `Facenet512` + FAISS, host HuggingFace Space). Django chỉ gọi HTTP, không nạp model local. |
| **Email** | Gmail SMTP (OTP đặt lại mật khẩu) |
| **Kiến trúc** | Client–Server · Multi-App Django · 3 lớp |

> [!NOTE]
> Các tính năng sau **đã bị loại bỏ** khỏi phạm vi hiện tại: CEO role, Super_User role, Audit Log, Cơ chế tính lương (BangLuong).

### 1.2 Cấu Trúc 3 Lớp

```
┌─────────────────────────────────────┐
│  Presentation Layer                 │  Templates (HTML/CSS/JS/Tailwind)
│  → Views, Forms, URL routing        │
├─────────────────────────────────────┤
│  Business Logic Layer               │  Services, validation, workflows
│  → services/, forms validation      │
├─────────────────────────────────────┤
│  Data Layer                         │  Models, Django ORM
│  → models/, migrations/             │
└─────────────────────────────────────┘
```

> Mỗi app theo cấu trúc package hoá: `models/`, `views/`, `forms/`, `services/`, `urls.py`, `templates/`, `migrations/`. Mỗi model nằm trong 1 file riêng (VD: `accounts/models/role_model.py`).

### 1.3 Cấu Trúc App (10 Django Apps)

```
business_web/               ← Project root (settings, urls, wsgi)
├── accounts/               ← Tài khoản, đăng nhập, phân quyền, RBAC
├── employee_profiles/      ← Hồ sơ nhân sự (thông tin cá nhân, công việc)
├── contracts/              ← Hợp đồng lao động, cảnh báo hết hạn
├── attendance/             ← Chấm công FaceID, bảng công, điều chỉnh
├── leaves/                 ← Nghỉ phép, quỹ phép
├── overtime/               ← Tăng ca (OT), phê duyệt OT
├── performance/            ← Đánh giá nhân viên định kỳ
├── rewards_discipline/     ← Khen thưởng, xử phạt
├── reports_interactions/   ← Báo cáo công việc, helpdesk ticket
└── stats_reports/          ← Thống kê tổng hợp (không có model riêng)
```

---

## 2. Data Models

### 2.1 App: `accounts` — Tài Khoản & Phân Quyền

#### `Role`
| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `name` | CharField (unique, choices) | `admin` \| `hr` \| `manager` \| `leader` \| `employee` |
| `description` | TextField | Mô tả vai trò |

> [!IMPORTANT]
> Chỉ có **5 vai trò** trong code thực tế (`ROLE_CHOICES`). Không có `CEO` hay `Super_User`.

#### `CustomPermission`
| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `codename` | CharField (unique) | Mã quyền hạn (VD: `can_export_reports`) |
| `name` | CharField | Tên hiển thị |
| `description` | TextField | Giải thích quyền |

#### `UserProfile`
> **1 User Django ↔ 1 UserProfile** (OneToOne, `related_name='profile'`)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | OneToOneField → User | Django User sở hữu profile |
| `role` | ForeignKey → Role (SET_NULL) | Vai trò hệ thống (RBAC) |
| `permissions` | ManyToManyField → CustomPermission | Quyền riêng lẻ |
| `full_name` | CharField | Họ tên đầy đủ |
| `employee_id` | CharField (unique) | MSNV — format: `[YY][MaPhongBan][STT4]` |

> Helper: `has_custom_permission(codename)`, `get_role_name()`.

#### `OtpCode`
| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | ForeignKey → User | User yêu cầu reset mật khẩu |
| `code` | CharField(6) | Mã OTP 6 chữ số |
| `created_at` | DateTimeField (auto) | Hết hạn sau **120 giây** (`OTP_EXPIRY_SECONDS=120`, method `is_expired()`) |

> `login_history_model.py` hiện là **placeholder** (chưa có model). RBAC vận hành qua `UserProfile.role` + `permissions` M2M.

---

### 2.2 App: `employee_profiles` — Hồ Sơ Nhân Sự

#### `PersonalInfo`
> **1 User ↔ 1 PersonalInfo** (OneToOne, `related_name='personal_info'`)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | OneToOneField → User | Chủ sở hữu |
| `phone_number` | CharField(20) | Số điện thoại |
| `date_of_birth` | CharField(10) | Ngày sinh DD/MM/YYYY |
| `gender` | CharField | Giới tính |
| `marital_status` | CharField | Tình trạng hôn nhân |
| `nationality` | CharField | Quốc tịch |
| `id_card_number` | CharField | Số CCCD/CMND |
| `id_card_issue_place` | CharField | Nơi cấp |
| `id_card_issue_date` | CharField | Ngày cấp |
| `permanent_address` | TextField | Địa chỉ thường trú |
| `temporary_address` | TextField | Địa chỉ tạm trú |

> Property `employee_id` lấy gián tiếp từ `UserProfile`.

#### `EmployeeWorkInfo`
> **1 User ↔ 1 EmployeeWorkInfo** (OneToOne, `related_name='work_info'`)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | OneToOneField → User | Chủ sở hữu |
| `employee_type` | CharField | Loại NV: Toàn thời gian, Bán thời gian, Thực tập |
| `department` | CharField | Phòng ban |
| `position` | CharField | Chức danh |
| `workplace` | CharField | Nơi làm việc |
| `probation_start` | CharField | Ngày bắt đầu thử việc |
| `official_start_date` | CharField | Ngày làm việc chính thức |
| `work_status` | CharField (choices) | `working`, `probation`, `paused`, `resigned` |
| `manager_user` | ForeignKey → User (SET_NULL, `managed_employees`) | Quản lý trực tiếp |
| `leader_user` | ForeignKey → User (SET_NULL, `led_employees`) | Leader phụ trách |

#### `EducationAndSkills`
> **1 User ↔ 1 EducationAndSkills** (OneToOne, `related_name='education_and_skills'`)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `education_level` | CharField | Trình độ học vấn |
| `degree` | CharField | Bằng cấp |
| `major` | CharField | Chuyên ngành |
| `certificates` | TextField | Chứng chỉ |
| `foreign_languages` | TextField | Ngoại ngữ |
| `professional_skills` | TextField | Kỹ năng chuyên môn |

#### `EmergencyContact`
> **1 User ↔ 1 EmergencyContact** (OneToOne, `related_name='emergency_contact'`)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | OneToOneField → User | Nhân viên |
| `contact_name` | CharField | Tên người liên hệ khẩn |
| `contact_phone` | CharField | Số điện thoại khẩn |
| `relation` | CharField | Mối quan hệ |
| `contact_address` | TextField | Địa chỉ người liên hệ |

#### `EmployeeDocument`
> **1 User ↔ N EmployeeDocument** (ForeignKey, `related_name='documents'`)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | ForeignKey → User | Nhân viên sở hữu |
| `title` | CharField | Tên/tiêu đề minh chứng |
| `document_type` | CharField | Loại tài liệu |
| `file` | FileField (`employee_documents/`) | File đính kèm |
| `uploaded_at` | DateTimeField (auto) | Thời gian tải lên |

---

### 2.3 App: `contracts` — Hợp Đồng Lao Động

#### `ContractInfo`
> **1 User ↔ N ContractInfo** (ForeignKey, `related_name='contracts'`) — mỗi NV ký nhiều HĐ theo thời gian; tại một thời điểm chỉ có **1 HĐ đang hiệu lực** (`is_active=True`).

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | ForeignKey → User | Nhân viên có hợp đồng |
| `is_active` | BooleanField (default=True) | HĐ đang hiệu lực? |
| `contract_number` | CharField | Số HĐ — VD: `HD-2026-001` |
| `contract_type` | CharField | Loại HĐ — VD: Thử việc, Chính thức 1 năm |
| `contract_signed_date` | CharField | Ngày ký (DD/MM/YYYY) |
| `contract_start_date` | CharField | Ngày hiệu lực |
| `contract_end_date` | CharField | Ngày hết hạn (để trống = không thời hạn) |
| `contract_annual_leave_days` | PositiveIntegerField | Ngày phép/năm theo HĐ |
| `contract_standard_shift` | CharField | Ca làm tiêu chuẩn (text) — VD: 08:30-17:30 |
| `shift_start_time` | TimeField | Giờ bắt đầu ca — **đi trễ tính từ đây** |
| `shift_end_time` | TimeField | Giờ kết thúc ca — **về sớm tính từ đây** |
| `contract_attachment_reference` | CharField | Tên/link file PDF hợp đồng |

> **Ràng buộc nghiệp vụ:** `ngayBatDau >= ngayKy`, `ngayHetHan >= ngayBatDau`, mỗi NV chỉ giữ 1 HĐ `is_active=True` (enforce ở tầng service/view).

---

### 2.4 App: `attendance` — Chấm Công

#### `EmployeeFace`
> **1 User ↔ 1 EmployeeFace** (OneToOne, `related_name='employee_face'`)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | OneToOneField → User | Nhân viên sở hữu |
| `face_base64` | TextField | Ảnh khuôn mặt mã hóa Base64 — **chỉ để preview** trên UI |
| `slot_id` | PositiveSmallIntegerField (default=1) | Slot trên service từ xa (pin về 1, hỗ trợ multi-slot 1–5) |
| `embedding` | JSONField (nullable) | **Luôn `None`** — vector khuôn mặt nay lưu ở service từ xa (MongoDB + FAISS), không lưu local |
| `content_type` | CharField | MIME type ảnh: `image/png`, `image/jpeg` |
| `created_at` / `updated_at` | DateTimeField | Tạo / cập nhật cuối |

> [!NOTE]
> Row `EmployeeFace` local chỉ giữ ảnh preview + `slot_id`. Toàn bộ embedding/so khớp do service từ xa xử lý. Cột `embedding` còn lại vì lý do tương thích nhưng không còn ghi dữ liệu (có thể dọn bằng migration `RemoveField` sau).

#### `FaceChangeRequest`
> **Nghiệp vụ phê duyệt:** Chống gian lận chấm công hộ. Nếu nhân viên tự cập nhật khuôn mặt (khi đã có), hệ thống tạo `FaceChangeRequest` ở trạng thái `pending` và chờ HR duyệt. Nếu là **đăng ký lần đầu** hoặc do HR/Admin thao tác, yêu cầu sẽ được tự động `approved` và áp dụng ngay.

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | ForeignKey → User | Nhân viên chủ khuôn mặt |
| `submitted_by` | ForeignKey → User (PROTECT) | Người nộp ảnh (giám sát upload thay) |
| `image_base64` | TextField | Ảnh khuôn mặt chờ duyệt |
| `status` | CharField | `pending` → `approved` / `rejected` |
| `reviewed_by` / `reviewed_at` | FK User / DateTime | Người duyệt (HR/Admin) |
| `hr_note` | TextField | Ghi chú từ HR (lý do từ chối / tự động) |
| `created_at` | DateTimeField (auto) | Thời gian nộp yêu cầu |

#### `AttendanceRecord`
> **1 User ↔ N AttendanceRecord** (`unique_together: user + record_date`)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | ForeignKey → User | Nhân viên chấm công |
| `record_date` | DateField | Ngày chấm công |
| `check_in_time` | TimeField (nullable) | Giờ vào làm |
| `check_out_time` | TimeField (nullable) | Giờ tan làm |
| `status` | CharField | `on_time`, `late`, `early_leave`, `absent` |

#### `AttendanceAdjustmentRequest`
> **1 AttendanceRecord ↔ 1 AdjustmentRequest** (OneToOne, `related_name='adjustment_request'`)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `record` | OneToOneField → AttendanceRecord | Bản ghi cần điều chỉnh |
| `submitted_by` | ForeignKey → User (PROTECT) | Nhân viên nộp yêu cầu |
| `reason` | CharField (choices) | `forgot`, `technical`, `business_trip`, `other` |
| `reason_detail` | TextField | Chi tiết lý do |
| `claimed_check_in_time` | TimeField (nullable) | Giờ vào khai báo thực tế |
| `claimed_check_out_time` | TimeField (nullable) | Giờ ra khai báo thực tế |
| `evidence` | FileField (`attendance/adjustments/%Y/%m/`) | Ảnh/PDF minh chứng |
| `status` | CharField | `pending`, `approved`, `rejected` |
| `submitted_at` / `reviewed_at` | DateTimeField | Mốc nộp / mốc duyệt |
| `reviewed_by` | ForeignKey → User (SET_NULL) | HR duyệt |
| `hr_note` | TextField | Ghi chú từ HR |

---

### 2.5 App: `leaves` — Nghỉ Phép

#### `LeaveRequest`

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | ForeignKey → User | Nhân viên gửi đơn |
| `leave_type` | CharField (choices) | `annual`, `sick`, `personal`, `maternity`, `business`, `other` |
| `start_date` / `end_date` | DateField | Khoảng ngày nghỉ |
| `days` | DecimalField(4,1) | Số ngày nghỉ |
| `reason` | TextField | Lý do |
| `status` | CharField (choices) | `pending` → `leader_approved` → `approved` / `rejected` |
| `leader_approved_by` / `leader_approved_at` | FK User / DateTime | Duyệt L1 (Leader/Manager) |
| `approved_by` | ForeignKey → User | HR duyệt L2 |
| `rejected_reason` | TextField | Lý do từ chối |
| `attachment` | FileField (`leaves/attachments/%Y/%m/`, nullable) | Minh chứng (PDF/JPG/PNG, ≤5MB) |
| `created_at` | DateTimeField (auto) | Thời điểm tạo |

> Property tiện ích: `date_range_display`, `leave_type_display`, `is_waiting`.
>
> **Quy tắc L1:** Ai được gán là `leader_user` **hoặc** `manager_user` của NV trong `EmployeeWorkInfo` thì người đó duyệt — không phân biệt theo số ngày nghỉ.

---

### 2.6 App: `overtime` — Tăng Ca

#### `OvertimeRequest`

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user` | ForeignKey → User | Nhân viên đăng ký |
| `overtime_date` | DateField | Ngày tăng ca |
| `start_time` / `end_time` | TimeField | Giờ bắt đầu / kết thúc OT |
| `hours` | DecimalField(4,1) | Số giờ OT |
| `reason` | TextField | Lý do |
| `status` | CharField | `pending` → `leader_approved` → `approved` / `rejected` |
| `leader_approved_by` / `leader_approved_at` | FK User / DateTime | Duyệt L1 |
| `approved_by` | ForeignKey → User | HR duyệt L2 |
| `rejected_reason` | TextField | Lý do từ chối |
| `attachment` | FileField (`overtime/attachments/%Y/%m/`, nullable) | Minh chứng |
| `created_at` | DateTimeField (auto) | Thời điểm tạo |

> Property: `time_range_display`, `is_waiting`, `status_display_vi`.
>
> **Quy tắc L1:** Như leaves. **Ngoại lệ:** người tạo đơn có role HR → sau L1 chuyển thẳng `approved` (bỏ qua L2).

---

### 2.7 App: `performance` — Đánh Giá

#### `EvaluationCategory`
| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `name` | CharField (unique) | Tên loại: Chuyên cần, Hiệu suất, Kỹ năng nhóm... |
| `description` | TextField | Mô tả loại đánh giá |
| `created_at` | DateTimeField (auto) | — |

#### `Evaluation`

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `employee` | ForeignKey → User (`evaluations_received`) | Nhân viên được đánh giá |
| `reviewer` | ForeignKey → User (`evaluations_given`) | Manager/Leader đánh giá |
| `category` | ForeignKey → EvaluationCategory (SET_NULL) | Loại đánh giá |
| `status` | CharField | `draft` → `submitted` → `acknowledged` |
| `rating` | CharField (choices) | `A`(≥90), `B`(≥75), `C`(≥60), `D`(<60) — **tự tính trong `save()` từ `score`**, không nhập tay |
| `score` | PositiveSmallIntegerField (0–100) | Điểm thang 100 |
| `evaluation_date` | DateField | Ngày đánh giá |
| `content` | TextField | Nội dung |
| `evidence_reference` | CharField | File minh chứng |
| `acknowledged_by` / `acknowledged_at` | FK User / DateTime | HR xác nhận |
| `hr_note` | TextField | Ghi chú phản hồi từ HR |
| `created_at` | DateTimeField (auto) | — |

> **Quy định:** Sau khi `submitted` → KHÔNG thể chỉnh sửa.

---

### 2.8 App: `rewards_discipline` — Khen Thưởng / Xử Phạt

#### `RewardPenalty`

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `employee` | ForeignKey → User | Nhân viên được thưởng/phạt |
| `record_type` | CharField (choices) | `reward` / `penalty` |
| `amount` | PositiveIntegerField (default=0) | Số tiền (VND), 0 = văn bản |
| `reason_title` | CharField | Tiêu đề lý do |
| `reason_detail` | TextField | Chi tiết lý do |
| `proposer` | ForeignKey → User (SET_NULL) | Người đề xuất (Leader/Manager) |
| `status` | CharField (default `pending`) | `pending` → `approved` / `rejected` |
| `application_date` | DateField | Ngày áp dụng |
| `evidence_file` | FileField (`reward_evidence/`, nullable) | File minh chứng |
| `created_at` | DateTimeField (auto) | — |

> Property `evidence_filename` trả tên file gốc.

---

### 2.9 App: `reports_interactions` — Báo Cáo & Helpdesk

#### `Report`

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `author` | ForeignKey → User (`reports_sent`) | Người gửi báo cáo |
| `recipient` | ForeignKey → User (`reports_received`, nullable) | Quản lý nhận báo cáo |
| `title` / `content` | CharField / TextField | Tiêu đề / nội dung |
| `file_attachment` | FileField (`report_attachments/`) | File đính kèm |
| `is_viewed` / `viewed_at` | Boolean / DateTime | Quản lý đã xem? + mốc xem |
| `status` | CharField (choices) | `submitted` → `needs_update` → `acknowledged` |
| `manager_note` | TextField | Phản hồi/chỉ đạo của quản lý |
| `created_at` / `updated_at` | DateTimeField | — |

> Property `can_edit_or_delete` (khóa khi `acknowledged`), `filename`.
> **Quy định:** `status=acknowledged` → người gửi KHÔNG sửa/xóa. `is_viewed` set khi Manager mở xem; `status` mới là trạng thái nghiệp vụ chính thức.

#### `Ticket`

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `author` | ForeignKey → User (`tickets`) | Người tạo ticket |
| `ticket_type` | CharField (choices) | `support` / `complaint` |
| `priority` | CharField (choices) | `low`, `medium`, `high` |
| `title` / `content` | CharField / TextField | Tiêu đề / nội dung |
| `evidence_file` | FileField (`tickets/%Y/%m/`) | File minh chứng |
| `status` | CharField (choices) | `new` → `processing` → `resolved` → `closed` / `rejected` |
| `assigned_to` | ForeignKey → User (SET_NULL) | Người xử lý (định tuyến tự động) |
| `rejection_reason` | TextField | Lý do từ chối |
| `created_at` / `updated_at` | DateTimeField | — |

---

### 2.10 App: `stats_reports` — Thống Kê Tổng Hợp

> App này **không có model riêng**. Đọc và tổng hợp dữ liệu từ các app: `attendance`, `leaves`, `overtime`, `performance`, `rewards_discipline`. Hiện dùng mock data trong `services/` cho đến khi backend các app hoàn thiện.

---

## 3. Sơ Đồ Quan Hệ Model (ERD Tổng Quan)

```mermaid
erDiagram
    User ||--|| UserProfile : "has"
    User ||--|| PersonalInfo : "has"
    User ||--|| EmployeeWorkInfo : "has"
    User ||--|| EducationAndSkills : "has"
    User ||--|| EmergencyContact : "has"
    User ||--o{ ContractInfo : "signs (nhiều HĐ theo thời gian)"
    User ||--|| EmployeeFace : "has"
    User ||--o{ EmployeeDocument : "uploads"
    User ||--o{ AttendanceRecord : "clocks"
    User ||--o{ LeaveRequest : "submits"
    User ||--o{ OvertimeRequest : "registers"
    User ||--o{ OtpCode : "requests"
    User ||--o{ RewardPenalty : "receives"
    User ||--o{ Evaluation : "receives (employee)"
    User ||--o{ Evaluation : "creates (reviewer)"
    User ||--o{ Report : "sends"
    User ||--o{ Ticket : "creates"
    UserProfile }o--|| Role : "assigned"
    UserProfile }o--o{ CustomPermission : "granted"
    AttendanceRecord ||--o| AttendanceAdjustmentRequest : "may have"
    EvaluationCategory ||--o{ Evaluation : "categorizes"
    EmployeeWorkInfo }o--|| User : "manager_user"
    EmployeeWorkInfo }o--|| User : "leader_user"
```

---

## 4. Ma Trận Phân Quyền (RBAC)

> [!NOTE]
> Hệ thống chỉ có **5 vai trò** được định nghĩa trong `Role` model: `admin`, `hr`, `manager`, `leader`, `employee`.

| Chức năng | Admin | HR | Manager | Leader | Employee |
|-----------|:---:|:---:|:---:|:---:|:---:|
| Quản lý tài khoản (gán role, khóa/mở, xóa, reset MK) | ✅ | | | | |
| Toàn quyền hồ sơ & hợp đồng | | ✅ | | | |
| Phê duyệt L2 (nghỉ phép, OT, thưởng/phạt) | | ✅ | | | |
| Điều chỉnh giờ công thủ công | | ✅ | | | |
| Phê duyệt L1 — nếu là `manager_user` của NV đó | | | ✅ | | |
| Phê duyệt L1 — nếu là `leader_user` của NV đó | | | | ✅ | |
| Đánh giá nhân viên, lập phiếu thưởng/phạt | | | ✅ | ✅ | |
| Xem/nộp dữ liệu của chính mình | | | | | ✅ |

> [!IMPORTANT]
> **Quy tắc L1 thực tế:** Cả Leader và Manager đều có thể duyệt L1. Điều kiện không phụ thuộc số ngày/giờ, chỉ kiểm tra: `approver in (employee.work_info.leader_user, employee.work_info.manager_user)`. Ai được gán supervisor trực tiếp của NV đó → người đó duyệt.

---

## 5. Workflow & Sequence Diagrams

### 5.1 Đăng Nhập & Bảo Mật

```mermaid
sequenceDiagram
    actor User as Nhân viên
    participant Web as Web Browser
    participant Auth as accounts/views/auth
    participant DB as Database
    participant Session as Django Session

    User->>Web: Nhập username + password
    Web->>Auth: POST /login/
    Auth->>DB: Tìm User theo username
    DB-->>Auth: User record

    alt Tài khoản bị khóa (is_active=False)
        Auth-->>Web: ❌ "Tài khoản bị khóa"
    else Mật khẩu sai
        Auth-->>Web: ❌ "Sai thông tin đăng nhập"
    else Đăng nhập thành công
        Auth->>Session: Tạo session, ghi role
        Auth-->>Web: ✅ Redirect Dashboard theo Role
    end
```

> [!NOTE]
> Khóa sau 3 lần sai và session timeout 30 phút là yêu cầu nghiệp vụ (mục 7). Hiện chưa thấy cấu hình `SESSION_COOKIE_AGE`/đếm `failed_login` trong `settings.py`/views — cần bổ sung khi siết bảo mật (mục 8).

---

### 5.2 Quên Mật Khẩu (OTP qua Email)

```mermaid
sequenceDiagram
    actor User as Nhân viên
    participant Web as Browser
    participant View as forgot_password_view
    participant DB as Database
    participant SMTP as Gmail SMTP

    User->>Web: Nhập email
    Web->>View: POST /forgot-password/
    View->>DB: Tìm User theo email
    DB-->>View: User record

    alt Email không tồn tại
        View-->>Web: ❌ "Email không tìm thấy"
    else Email hợp lệ
        View->>View: Sinh mã OTP 6 chữ số
        View->>DB: Lưu OtpCode(user, code, created_at)
        View->>SMTP: Gửi email chứa OTP
        SMTP-->>User: 📧 Email OTP
        View-->>Web: "Kiểm tra email của bạn"
        User->>Web: Nhập OTP + mật khẩu mới
        Web->>View: POST /reset-password/
        View->>DB: Lấy OtpCode mới nhất của user
        alt OTP hết hạn (> 120 giây)
            View-->>Web: ❌ "OTP đã hết hạn"
        else OTP sai
            View-->>Web: ❌ "Mã OTP không đúng"
        else OTP đúng & còn hạn
            View->>DB: Cập nhật password mới
            View->>DB: Xóa OtpCode
            View-->>Web: ✅ "Đổi mật khẩu thành công"
        end
    end
```

---

### 5.3 Tạo Hồ Sơ Nhân Viên Mới (HR)

```mermaid
sequenceDiagram
    actor HR as HR Staff
    participant Web as Browser
    participant View as employee_profiles/views
    participant Service as services/
    participant DB as Database
    participant Email as Gmail SMTP

    HR->>Web: Điền form hồ sơ + upload ảnh khuôn mặt
    Web->>View: POST /employees/create/
    View->>View: Validate dữ liệu (tuổi>=18, SĐT, CCCD, ảnh 3x4)

    alt Validation failed
        View-->>Web: ❌ Hiển thị lỗi form
    else Validation passed
        View->>Service: generate_employee_id(department)
        Service-->>View: MSNV = [YY][MaPhongBan][STT4]
        View->>Service: generate_username(ten, ho, phongban)
        Service-->>View: Username (viết thường không dấu)
        View->>DB: Tạo User(username, password ngẫu nhiên)
        View->>DB: Tạo UserProfile(user, employee_id, role=Employee)
        View->>DB: Tạo PersonalInfo / EmployeeWorkInfo / ContractInfo
        View->>Service: Đăng ký khuôn mặt → POST /register (remote)
        View->>DB: Tạo EmployeeFace(user, face_base64 preview, slot_id)
        View->>Email: Gửi email tài khoản (username, password)
        View-->>Web: ✅ "Tạo hồ sơ thành công"
    end
```

---

### 5.4a Đăng Ký / Cập Nhật Khuôn Mặt

> Quy trình này xử lý cả lần đầu đăng ký (tự động duyệt) và cập nhật khuôn mặt (chờ HR duyệt). Giao diện Cài đặt cung cấp thanh theo dõi trạng thái `FaceChangeRequest` trực quan.

```mermaid
sequenceDiagram
    actor User as HR / Nhân viên
    participant Web as Browser (Cài đặt)
    participant Upload as image_upload_view
    participant FaceSvc as face_change_service
    participant API as Remote Face API
    participant DB as Database

    User->>Web: Chụp & Upload ảnh khuôn mặt
    Web->>Upload: POST /attendance/upload-image/ (field "image")
    Upload->>Upload: Validate MIME type
    Upload->>FaceSvc: submit_face_change(owner, submitted_by, image)

    alt Người dùng là HR/Admin HOẶC Đăng ký lần đầu
        FaceSvc->>API: face_service.apply_face_enrollment (gọi /register)
        API-->>FaceSvc: {status: success}
        FaceSvc->>DB: Upsert EmployeeFace, Tạo FaceChangeRequest (status=approved)
        FaceSvc-->>Upload: outcome='applied'
        Upload-->>Web: ✅ "Lưu ảnh thành công" (Trạng thái: Đang hoạt động)
    else Nhân viên tự cập nhật (Đã có khuôn mặt)
        FaceSvc->>DB: Xóa pending cũ, Tạo FaceChangeRequest mới (status=pending)
        FaceSvc-->>Upload: outcome='pending'
        Upload-->>Web: ⏳ "Đã gửi yêu cầu, chờ HR duyệt" (Trạng thái: Chờ duyệt)
    end
```

> **HR Duyệt:** Khi HR duyệt (`approve_face_change`), hệ thống mới đọc ảnh từ `FaceChangeRequest` và đẩy lên Remote Face API (`/register`), sau đó cập nhật `EmployeeFace`. Nếu từ chối, `status=rejected` kèm lý do.

---

### 5.4b Chấm Công FaceID (Remote `/recognize`)

```mermaid
sequenceDiagram
    actor Employee as Nhân viên
    participant Web as Browser (Webcam)
    participant View as face_attendance_view
    participant Verify as face_verification_service
    participant API as Remote Face API
    participant DB as Database

    Employee->>Web: Nhấn Check-in / Check-out
    Web->>Web: Webcam chụp ảnh
    Web->>View: POST /attendance/check/ (field "image")

    View->>View: Lockout gate (cache: 3 fail → khóa 300s)
    View->>Verify: verify_face_for_user(user, image_bytes)
    Verify->>API: POST /recognize (file)
    API-->>Verify: {status, employee_id, confidence, match_slot}

    alt no_face / service_down
        Verify-->>View: VerifyResult(fail, reason)
        View-->>Web: ❌ 400 no_face / 503 service unavailable
    else status = fail (không khớp ai)
        Verify-->>View: reason = no_match
        View-->>Web: ❌ 401 no_match
    else employee_id != str(user.id)
        Verify-->>View: reason = wrong_person
        View->>View: register_failure (tăng đếm lockout)
        View-->>Web: ❌ 403 wrong_person (fails_left)
    else Khớp đúng user (employee_id == str(user.id))
        View->>DB: select_for_update AttendanceRecord(user, today)
        View->>View: decide_next_action → check_in / check_out / done
        alt Check-in
            Note over View: check_in <= shift_start+grace → on_time<br/>else → late
            View->>DB: Lưu check_in_time, status
            View-->>Web: ✅ "Check-in thành công lúc HH:MM"
        else Check-out
            Note over View: ra trước giờ tan kỳ vọng → early_leave<br/>(giờ tan = max(shift_end, giờ OT đã duyệt))
            View->>DB: Lưu check_out_time, status
            View-->>Web: ✅ "Check-out thành công lúc HH:MM"
        end
        View->>View: clear_failures
    end
```

> [!NOTE]
> **Kiến trúc mới:** Django **không** so khớp embedding nữa. Toàn bộ trích xuất vector + tìm kiếm chạy trên service từ xa (FAISS, ngưỡng cosine `THRESHOLD = 0.40` phía server). Quy tắc 1:1 nằm ở `face_verification_service`: nhận diện hợp lệ ⟺ `recognize.employee_id == str(user.id)`.
>
> **Client (`attendance/services/face/face_api_client.py`):**
> - `register_face_remote()` → `POST {FACE_API_BASE_URL}/register`
> - `recognize_face_remote()` → `POST {FACE_API_BASE_URL}/recognize`
> - `health_check()` → `GET {FACE_API_BASE_URL}/health`
> - Cấu hình: `FACE_API_BASE_URL` (default HuggingFace Space), `FACE_API_TIMEOUT_SEC=30` trong `settings.py`.
> - Map lỗi: HTTP 400 + "no face" → `FaceApiError('no_face')`; lỗi mạng/timeout → `service_down`.

---

### 5.5 Nghỉ Phép — Luồng Phê Duyệt 2 Cấp

```mermaid
sequenceDiagram
    actor Employee as Nhân viên
    actor L1 as Leader / Manager (L1)
    actor HR as HR (L2)
    participant System as Hệ thống
    participant DB as Database

    Employee->>System: Nộp đơn nghỉ phép (loại, ngày, lý do)
    System->>DB: Kiểm tra số ngày <= quỹ phép còn lại?
    alt Vượt quỹ phép
        System-->>Employee: ❌ "Không đủ phép"
    else Hợp lệ
        System->>DB: Tạo LeaveRequest(status=pending)
        Note over L1: L1 = leader_user HOẶC manager_user trong EmployeeWorkInfo

        L1->>System: Duyệt L1 / Từ chối
        alt L1 Từ chối
            System->>DB: status = rejected
        else L1 Duyệt
            System->>DB: status = leader_approved, ghi leader_approved_by & at
            HR->>System: Duyệt L2 / Từ chối
            alt L2 Từ chối
                System->>DB: status = rejected
            else L2 Duyệt
                System->>DB: status = approved, ghi approved_by
                System->>DB: Trừ quỹ phép của NV
            end
        end
    end
```

---

### 5.6 Tăng Ca OT — Luồng Phê Duyệt 2 Cấp

```mermaid
sequenceDiagram
    actor Employee as Nhân viên
    actor L1 as Leader / Manager (L1)
    actor HR as HR (L2)
    participant System as Hệ thống
    participant DB as Database

    Employee->>System: Đăng ký OT (ngày, giờ, lý do)
    System->>DB: Tạo OvertimeRequest(status=pending)
    Note over L1: L1 = leader_user HOẶC manager_user trong EmployeeWorkInfo

    L1->>System: Duyệt L1 / Từ chối
    alt Từ chối
        System->>DB: status = rejected
    else Duyệt
        System->>DB: status = leader_approved
        Note over System: Ngoại lệ: người tạo có role HR → approved luôn, bỏ qua L2
        HR->>System: Duyệt L2 / Từ chối
        alt Duyệt
            System->>DB: status = approved
        end
    end
```

---

### 5.7 Hợp Đồng — Cảnh Báo Tự Động (Batch Job)

```mermaid
sequenceDiagram
    participant Cron as Batch Job (1-3h AM mỗi ngày)
    participant DB as Database
    participant Notif as Notification System
    actor HR as HR
    actor Manager as Manager
    actor Employee as Nhân viên

    Cron->>DB: Lấy ContractInfo có contract_end_date != null
    DB-->>Cron: Danh sách hợp đồng

    loop Mỗi hợp đồng
        Cron->>Cron: Số ngày còn lại = end_date - today
        alt Còn 30 ngày
            Cron->>Notif: Thông báo HR + Manager
        else Còn 15 ngày
            Cron->>Notif: Thông báo thêm cho Employee
        else Còn 7 ngày
            Cron->>Notif: Thông báo KHẨN cho tất cả
        else Đã hết hạn
            Cron->>DB: is_active = False (Hết hiệu lực)
            Cron->>Notif: Thông báo KHẨN cho HR
        end
    end
```

> Lập lịch qua Task Scheduler (`setup_task_scheduler.py`) trên Windows; production cân nhắc cron/Celery beat.

---

### 5.8 Đánh Giá Nhân Viên

```mermaid
sequenceDiagram
    actor Reviewer as Leader / Manager
    actor HR as HR
    participant System as Hệ thống
    participant DB as Database

    Reviewer->>System: Tạo phiếu đánh giá (nháp)
    System->>DB: Evaluation(status=draft, reviewer, employee, category)
    Reviewer->>System: Nhập score (0-100) + nội dung + minh chứng
    Note over DB: save() tự suy rating A/B/C/D từ score
    Reviewer->>System: Nhấn "Gửi"

    System->>DB: status = submitted
    Note over DB: 🔒 Khóa chỉnh sửa vĩnh viễn

    HR->>System: Xem đánh giá, thêm hr_note, Xác nhận
    System->>DB: status = acknowledged, ghi acknowledged_by & at
```

---

### 5.9 Khen Thưởng / Xử Phạt — Luồng 2 Cấp

```mermaid
sequenceDiagram
    actor Leader as Leader / Manager
    actor Manager as Manager (L1 nếu Leader lập)
    actor HR as HR (L2)
    participant System as Hệ thống
    participant DB as Database

    Leader->>System: Lập phiếu thưởng/phạt
    System->>DB: RewardPenalty(status=pending, proposer=Leader)

    alt Leader lập phiếu
        Manager->>System: Duyệt L1 / Từ chối
        alt Từ chối
            System->>DB: status = rejected
        else Duyệt L1
            System->>HR: Chuyển HR duyệt L2
        end
    else Manager lập phiếu
        System->>HR: Chuyển HR duyệt L2 (bỏ qua L1)
    end

    HR->>System: Duyệt L2 / Từ chối
    alt Duyệt
        System->>DB: status = approved
    else Từ chối
        System->>DB: status = rejected
    end
```

---

### 5.10 Báo Cáo Công Việc

```mermaid
sequenceDiagram
    actor Employee as Nhân viên / Leader
    actor Manager as Manager / HR
    participant System as Hệ thống
    participant DB as Database

    Note over Employee: Employee → gửi Leader; Leader → gửi Manager.<br/>Manager/HR không có nghĩa vụ nộp.

    Employee->>System: Tạo & gửi báo cáo (tiêu đề, nội dung, file)
    System->>DB: Report(author, recipient, is_viewed=False, status=submitted)

    Manager->>System: Xem báo cáo
    System->>DB: is_viewed = True, viewed_at = now()

    alt Cần bổ sung
        Manager->>System: Yêu cầu cập nhật + manager_note
        System->>DB: status = needs_update
    else Tiếp nhận
        Manager->>System: Xác nhận tiếp nhận
        System->>DB: status = acknowledged
        Note over DB: 🔒 Khóa sửa/xóa (can_edit_or_delete=False)
    end
```

---

### 5.11 Helpdesk Ticket — Định Tuyến Tự Động

```mermaid
sequenceDiagram
    actor Employee as Nhân viên
    participant System as Hệ thống
    participant Router as Auto-Router
    participant Assignee as Người xử lý
    participant DB as Database

    Employee->>System: Tạo ticket (loại, nhóm, tiêu đề, nội dung, file)
    System->>Router: Xác định bộ phận xử lý theo loại

    alt IT / Kỹ thuật
        Router->>DB: assigned_to = Admin
    else Lương / Phép / Hành chính
        Router->>DB: assigned_to = HR
    else Kết quả đánh giá
        Router->>DB: assigned_to = Manager
    end

    System->>DB: Ticket(status=new, assigned_to=...)
    System->>Assignee: Thông báo ticket mới

    alt Sai bộ phận
        Assignee->>System: Forward sang bộ phận đúng (giữ status=new)
    else Tiếp nhận
        Assignee->>System: status = processing → resolved
        Employee->>System: Xác nhận → status = closed
    end
```

---

## 6. Vòng Đời Trạng Thái Các Đối Tượng

### Đơn Nghỉ Phép / Tăng Ca

```mermaid
stateDiagram-v2
    [*] --> pending : NV nộp đơn
    pending --> leader_approved : L1 Duyệt
    pending --> rejected : L1 Từ chối
    leader_approved --> approved : HR (L2) Duyệt
    leader_approved --> rejected : HR (L2) Từ chối
    approved --> [*]
    rejected --> [*]
```

### Ticket Helpdesk

```mermaid
stateDiagram-v2
    [*] --> new : NV tạo ticket
    new --> processing : Người xử lý tiếp nhận
    new --> new : Forward sang bộ phận khác
    processing --> resolved : Đã xử lý xong
    resolved --> closed : NV xác nhận
    new --> rejected : Từ chối ngay
    closed --> [*]
    rejected --> [*]
```

### Hợp Đồng

```mermaid
stateDiagram-v2
    [*] --> active : HR tạo HĐ mới
    active --> warning_30d : Còn 30 ngày
    warning_30d --> warning_15d : Còn 15 ngày
    warning_15d --> warning_7d : Còn 7 ngày
    warning_7d --> expired : Hết hạn chưa gia hạn
    warning_30d --> renewed : HR gia hạn
    warning_15d --> renewed : HR gia hạn
    warning_7d --> renewed : HR gia hạn
    expired --> [*]
    renewed --> active : HĐ mới hiệu lực
```

### Đánh Giá Nhân Viên

```mermaid
stateDiagram-v2
    [*] --> draft : Leader/Manager tạo
    draft --> submitted : Nhấn Gửi (🔒 Khoá chỉnh sửa)
    submitted --> acknowledged : HR xác nhận
    acknowledged --> [*]
```

### Báo Cáo Công Việc

```mermaid
stateDiagram-v2
    [*] --> submitted : NV gửi
    submitted --> needs_update : Quản lý yêu cầu cập nhật
    needs_update --> submitted : NV gửi lại
    submitted --> acknowledged : Quản lý tiếp nhận (🔒)
    acknowledged --> [*]
```

---

## 7. Quy Định Nghiệp Vụ Quan Trọng

| Mã | Nội dung | Trạng thái trong code |
|----|---------|------------------------|
| `QĐ_TK1` | Sai MK 3 lần → khóa `is_active=False` | Yêu cầu nghiệp vụ (chưa thấy đếm failed_login) |
| `QĐ_TK2` | HR mở khóa Employee/Leader/Manager; Admin mở khóa mọi tài khoản | Có view khóa/mở (`account_status_view`) |
| `QĐ_Tao_MSNV` | `[YY][MaPhongBan][STT4]` — VD: `26IT0001` | Có service sinh MSNV |
| `QĐ_Tao_Username` | `[ten][ho][maphongban]` viết thường không dấu | Có service sinh username |
| `QĐ_PheDuyet_L1` | `leader_user` HOẶC `manager_user` của NV → duyệt L1 | ✅ Triển khai |
| `QĐ_PheDuyet_L2` | Sau L1 → HR xác nhận | ✅ (OT: HR tự tạo → bỏ qua L2) |
| `QĐ_CapNhat_DuLieu` | Nghỉ phép/OT/thưởng-phạt chỉ hiệu lực sau L2 | ✅ |
| `QĐ_CanhBao` | 30 ngày (HR+Manager) → 15 (+NV) → 7 (tất cả, KHẨN) | Batch job |
| `QĐ_DieuChinh` | HR chỉ sửa giờ công kỳ hiện tại (chưa chốt lương) | ✅ AdjustmentRequest |
| `QĐ_LuuTruDanhGia` | Sau `submitted` → không sửa đánh giá | ✅ |
| `QĐ_XacNhanBaoCao` | Sau `acknowledged` → khóa sửa/xóa báo cáo | ✅ `can_edit_or_delete` |
| `QĐ_DieuHuong` | Ticket định tuyến tự động theo loại | ✅ Auto-router |
| `QĐ_NghiViec` | NV `resigned` → `is_active=False` | Yêu cầu nghiệp vụ |
| `QĐ_Session` | Không hoạt động 30 phút → tự đăng xuất | Yêu cầu nghiệp vụ (chưa cấu hình `SESSION_COOKIE_AGE`) |

---

## 8. Tech Checklist Deploy

- [ ] Service nhận diện từ xa (`FACE_API_BASE_URL`) sống & `/health` ok; test `/register` + `/recognize` với webcam thực (server threshold cosine 0.40)
- [ ] `FACE_API_TIMEOUT_SEC` đủ lớn cho cold-start DeepFace; xử lý fallback khi service down (503)
- [ ] Batch Job cảnh báo HĐ chạy đúng giờ (Task Scheduler / cron / Celery beat)
- [ ] Gmail SMTP config qua `.env` cho OTP reset mật khẩu
- [ ] **Bổ sung** `SESSION_COOKIE_AGE` để có session timeout 30 phút
- [ ] **Bổ sung** đếm `failed_login` → khóa sau 3 lần sai
- [ ] File upload: validate định dạng (PDF/JPG/PNG) và giới hạn 5MB
- [ ] RBAC test đủ 5 role không bị bypass
- [ ] SQLite → cân nhắc MySQL khi deploy production
- [ ] HTTPS bắt buộc (dữ liệu nhân sự nhạy cảm)

---

> 📌 **Ghi chú:** File phản ánh codebase đến ngày **01/06/2026** (đã đối chiếu trực tiếp với models trong `business_web/*/models/`). Các mục đánh dấu "Yêu cầu nghiệp vụ" là quy định theo đặc tả nhưng chưa xác nhận trong code — cần kiểm tra/bổ sung khi siết bảo mật.

# Walkthrough — Business Web Project

> **Cập nhật:** 2026-06-03 — dựa 100% trên mã nguồn hiện tại, không đoán mò.

---

## 1. Tổng quan dự án

**Business Web** là hệ thống quản lý nhân sự nội bộ xây dựng trên **Django 4.2** (settings khai `Django 6.0.3` ở comment header, file `requirements.txt` pin `Django==4.2`). Hệ thống gồm **10 Django apps** phục vụ toàn bộ vòng đời quản lý nhân viên: từ đăng ký tài khoản, hồ sơ, hợp đồng, chấm công khuôn mặt, nghỉ phép, tăng ca, đánh giá, khen thưởng/xử phạt, báo cáo/ticket, đến thống kê tổng hợp.

### Stack công nghệ

| Thành phần | Công nghệ |
|---|---|
| Framework | Django 4.2, Python 3.13 |
| Database | SQLite (dev) / PostgreSQL (prod via `dj-database-url`) |
| Static files | WhiteNoise |
| Media storage | Local disk (dev) / Cloudinary (prod) |
| Face recognition | Remote API trên HuggingFace Spaces |
| Email | Gmail SMTP |
| Deploy | Render (web + PostgreSQL) |
| Dependencies | `pillow`, `openpyxl`, `requests`, `python-decouple`, `gunicorn`, `psycopg2-binary` |

---

## 2. Kiến trúc hệ thống

### 2.1 Cấu trúc thư mục gốc

```
Business_web_project/
├── business_web/                # Django project root
│   ├── manage.py
│   ├── requirements.txt
│   ├── build.sh                 # Render build script
│   ├── db.sqlite3
│   ├── business_web/            # Project settings
│   │   ├── settings.py
│   │   ├── urls.py              # Root URL router
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── accounts/                # Auth, RBAC, admin, notifications
│   ├── employee_profiles/       # Hồ sơ nhân viên
│   ├── contracts/               # Hợp đồng lao động
│   ├── attendance/              # Chấm công khuôn mặt
│   ├── leaves/                  # Nghỉ phép
│   ├── overtime/                # Tăng ca
│   ├── performance/             # Đánh giá nhân viên
│   ├── rewards_discipline/      # Khen thưởng & Xử phạt
│   ├── reports_interactions/    # Báo cáo & Ticket
│   ├── stats_reports/           # Thống kê tổng hợp (không có model)
│   ├── common/                  # Tiện ích dùng chung (file validation)
│   ├── tests/                   # Thư mục test scaffold (chỉ .gitkeep)
│   └── tests_perf/              # Locust load testing
├── render.yaml
├── docs/
└── *.md                         # Các tài liệu dự án
```

### 2.2 Mỗi app theo pattern chuẩn

```
app_name/
├── models/
│   ├── __init__.py              # Re-export models
│   └── *_model.py               # Từng model riêng file
├── views/
│   ├── __init__.py              # Re-export views
│   └── *.py hoặc thư mục con
├── services/
│   ├── __init__.py              # Business logic
│   └── *.py
├── forms/ hoặc forms.py
├── templates/app_name/
├── tests/
│   ├── __init__.py
│   └── test_*.py
├── urls.py
└── apps.py
```

### 2.3 Hệ thống vai trò (RBAC)

5 vai trò được định nghĩa trong `Role.ROLE_CHOICES`:

| Vai trò | Mã | Quyền chính |
|---|---|---|
| **Admin** | `admin` | Quản lý hệ thống: CRUD user, gán role/permission, khóa/mở tài khoản. **Không** truy cập chức năng nghiệp vụ (bị `deny_admin` decorator chặn). |
| **HR** | `hr` | Toàn quyền nghiệp vụ: duyệt cuối đơn phép/tăng ca (bước 2), quản lý hợp đồng, xác nhận đánh giá, xem thống kê toàn công ty. |
| **Manager** | `manager` | Duyệt bước 1 đơn phép/tăng ca cho nhân viên cùng phòng ban. Tạo đánh giá, đề xuất khen thưởng/xử phạt. Xem thống kê phòng ban. |
| **Leader** | `leader` | Duyệt bước 1 đơn phép/tăng ca cho nhân viên được gán. Tạo đánh giá, đề xuất khen thưởng/xử phạt. Xem thống kê nhóm. |
| **Employee** | `employee` | Xem hồ sơ/hợp đồng cá nhân, chấm công, tạo đơn phép/tăng ca, gửi báo cáo, tạo ticket. |

**CustomPermission**: Quyền bổ sung gán riêng cho user, độc lập với role (M2M qua `UserProfile.permissions`).

---

## 3. Các Django App chi tiết

### 3.1 accounts

**Models** (5 model, exported qua `__init__.py`):

| Model | Quan hệ | Mô tả |
|---|---|---|
| `UserProfile` | OneToOne → `User`, FK → `Role`, M2M → `CustomPermission` | Profile mở rộng: `employee_id` (unique), `full_name`, role, permissions. Property `is_admin`. |
| `Role` | — | 5 choices cố định: admin, hr, manager, leader, employee. |
| `CustomPermission` | — | `codename` (unique), `name`, `description`. |
| `OtpCode` | FK → `User` | OTP 6 chữ số, hết hạn sau 120 giây. Dùng cho quên mật khẩu. |
| `Notification` | FK → `User` | Thông báo hệ thống: title, message, link, is_read, created_at. |

**Views** (phân chia thư mục `auth/` và `account/`):

| View | URL | Phương thức | Vai trò |
|---|---|---|---|
| `AccountsLoginView` | `/login/` | GET/POST | Public. Class-based, override `form_valid` để đếm login fail + lockout. |
| `register_view` | `/register/` | GET/POST | Public. Tạo User + UserProfile + EmployeeWorkInfo. |
| `forgot_password_view` | `/forgot-password/` | GET/POST | Public. Tạo OTP, gửi email. |
| `reset_password_after_otp_view` | `/reset-password/` | GET/POST | Public. Xác thực OTP → đổi password. |
| `logout_view` | `/logout/` | GET | Authenticated. |
| `dashboard_view` | `/dashboard/` | GET | Authenticated. Hiện thông tin tổng hợp. |
| `settings_view` | `/settings/` | GET/POST | Authenticated. HR có thể cấu hình `WorkScheduleConfig`. |
| `switch_role_view` | `/switch-role/` | POST | Superuser. Mô phỏng vai trò khác (dev/demo). |
| `user_list_view` | `/users/` | GET | Admin/HR. Danh sách user với filter. |
| `admin_create_account_view` | `/users/create-account/` | GET/POST | Admin. Tạo tài khoản chỉ cần username + password. |
| `assign_permissions_view` | `/users/<id>/permissions/` | GET/POST | Admin. Gán role + custom permissions. |
| `delete_user_view` | `/users/<id>/delete/` | POST | Admin. Không cho xóa chính mình. |
| `toggle_user_active_view` | `/users/<id>/toggle-active/` | POST | Admin. Khóa/mở tài khoản. Không cho khóa chính mình. |
| `reset_user_password_view` | `/users/<id>/reset-password/` | POST | Admin. Reset về mật khẩu mặc định. |
| `notifications_view` | `/notifications/` | GET | Authenticated. Xem + đánh dấu đã đọc. |
| `mark_notifications_read_view` | `/notifications/mark-read/` | POST | Authenticated. Đánh dấu tất cả đã đọc. |

**Services** (tổ chức 4 module: `account/`, `auth/`, `notification_service.py`, `permission/`):
- `account/`: `ensure_profile`, `ensure_work_info`, `ensure_contract_info`, `get_user_display_name`, `get_department_label`, v.v.
- `auth/`: `create_automatic_account`, `create_manual_account`, `generate_otp`, `send_otp_email`, `verify_otp`, `reset_user_password`.
- `permission/`: `is_admin_user`, `is_hr_user`, `user_has_role`, `can_manage_requests`, `can_access_statistics`, `can_access_evaluations`, `can_acknowledge_evaluation`, `has_admin_business_access`.
- `notification_service.py`: `create_notification`.

**Context processors**: `notifications` — inject `unread_notifications` (top 5) và `unread_count` vào mọi template.

**Decorators**: `deny_admin` — chặn Admin truy cập view nghiệp vụ, redirect về dashboard.

**Cấu hình bảo mật** (từ `settings.py`):
- `SESSION_COOKIE_AGE = 1800` (30 phút không hoạt động → tự đăng xuất).
- `LOGIN_LOCKOUT_MAX_FAILS = 3`, `LOGIN_LOCKOUT_WINDOW_SEC = 900` — sai password 3 lần → khóa tài khoản.
- Production: HSTS, SSL redirect, secure cookies.

---

### 3.2 employee_profiles

**Models** (5 model):

| Model | Quan hệ | Mô tả |
|---|---|---|
| `PersonalInfo` | OneToOne → `User` | SĐT, ngày sinh, giới tính, CCCD, địa chỉ. |
| `EmployeeWorkInfo` | OneToOne → `User`, FK → `User` (manager_user, leader_user) | Phòng ban, chức danh, loại nhân viên, trạng thái (working/probation/paused/resigned). Quan hệ quản lý phân cấp. |
| `EducationAndSkills` | OneToOne → `User` | Học vấn, bằng cấp, chuyên ngành, chứng chỉ, ngoại ngữ, kỹ năng. |
| `EmergencyContact` | OneToOne → `User` | Tên, SĐT, quan hệ, địa chỉ người liên hệ khẩn cấp. |
| `EmployeeDocument` | FK → `User` (many) | File đính kèm: bằng cấp, CCCD, v.v. `upload_to='employee_documents/'`. |

**Views** (6 views trong `profile_views.py`):

| View | URL | Mô tả |
|---|---|---|
| `profile_view` | `/profile/` | Nhân viên xem/sửa hồ sơ cá nhân (PersonalInfo, EducationAndSkills, EmergencyContact). |
| `upload_document_view` | `/profile/upload-document/` | Upload tài liệu minh chứng. |
| `hr_create_profile_view` | `/hr/create-profile/` | HR tạo hồ sơ đầy đủ cho nhân viên mới. |
| `hr_view_profile_view` | `/users/<id>/profile/` | HR xem hồ sơ nhân viên bất kỳ. |
| `hr_assign_role_view` | `/users/<id>/assign-role/` | HR gán vai trò cho nhân viên. |
| `edit_work_info_view` | `/users/<id>/work-info/` | HR/Admin chỉnh sửa thông tin công việc. |

---

### 3.3 contracts

**Models** (1 model):

| Model | Quan hệ | Mô tả |
|---|---|---|
| `ContractInfo` | FK → `User` (many) | Hợp đồng lao động có lưu lịch sử. `is_active` phân biệt bản hiệu lực. Fields: contract_number, type, signed/start/end date (DD/MM/YYYY), annual_leave_days, shift times, attachment_reference. |

**Views** (6 views):

| View | URL | Mô tả |
|---|---|---|
| `contract_view` | `/contract/` | Nhân viên xem HĐ cá nhân. |
| `hr_expiring_contracts_view` | `/contract/hr/expiring/` | HR xem danh sách HĐ sắp hết hạn (ngưỡng 30 ngày). |
| `hr_send_reminder_view` | `/contract/hr/send-reminder/<id>/` | HR gửi email nhắc nhở 1 nhân viên. |
| `hr_send_all_reminders_view` | `/contract/hr/send-all-reminders/` | HR gửi nhắc nhở tất cả HĐ sắp hết hạn. |
| `hr_adjust_contract_view` | `/contract/hr/adjust/<id>/` | HR tạo phiên bản HĐ mới (archive bản cũ). |
| `contract_history_view` | `/contract/history/<id>/` | Xem lịch sử tất cả phiên bản HĐ. |

**Services** (3 file):
- `__init__.py`: `validate_contract_date_order`, `build_contract_page_context`, `get_active_contract`, `get_shift_times`, `adjust_contract` (versioning), `get_contract_history`.
- `renewal_service.py`: `parse_ddmmyyyy`, `get_days_until_expiry`, `expire_overdue_contracts`, `get_expiring_contracts` (ngưỡng 30/7 ngày), `get_recipients_for_contract`.
- `email_service.py`: `send_renewal_reminder_email` (Gmail SMTP).

---

### 3.4 attendance

**Models** (5 model):

| Model | Quan hệ | Mô tả |
|---|---|---|
| `AttendanceRecord` | FK → `User` | Bản ghi chấm công ngày: record_date, check_in_time, check_out_time, status (on_time/late/absent). `unique_together = ['user', 'record_date']`. |
| `EmployeeFace` | OneToOne → `User` | Marker enrollment khuôn mặt trên remote service. slot_id, timestamps. |
| `AttendanceAdjustmentRequest` | OneToOne → `AttendanceRecord`, FK → `User` (submitted_by, reviewed_by) | Yêu cầu sửa chấm công: reason choices (forgot/technical/business_trip/other), claimed times, evidence file, status (pending/approved/rejected). |
| `FaceChangeRequest` | FK → `User` (user, submitted_by, reviewed_by) | Yêu cầu cập nhật khuôn mặt chờ HR duyệt. Anti-fraud: `is_cross_user` property. image_sha256 audit. |
| `WorkScheduleConfig` | — | Singleton (pk=1): shift_start, shift_end, late_grace_minutes. `get_solo()` class method. |

**Views** (11 views):

| View | URL | Mô tả |
|---|---|---|
| `attendance_view` | `/attendance/` | Trang chấm công chính. |
| `upload_image_base64_view` | `/attendance/upload-image/` | Upload ảnh khuôn mặt base64 (đăng ký/cập nhật). |
| `face_check_view` | `/attendance/check/` | Nhận diện khuôn mặt và ghi nhận chấm công. |
| `face_change_review_view` | `/attendance/face-changes/review/` | HR xem danh sách yêu cầu đổi khuôn mặt. |
| `face_change_approve_action` | `/attendance/face-changes/<id>/approve/` | HR duyệt yêu cầu đổi khuôn mặt. |
| `face_change_reject_action` | `/attendance/face-changes/<id>/reject/` | HR từ chối yêu cầu đổi khuôn mặt. |
| `face_change_image_view` | `/attendance/face-changes/<id>/image/` | Xem ảnh khuôn mặt chờ duyệt. |
| `submit_adjustment_view` | `/attendance/adjustment/<record_id>/` | Nhân viên gửi yêu cầu sửa chấm công. |
| `adjustment_review_view` | `/attendance/adjustments/review/` | HR xem danh sách yêu cầu sửa chấm công. |
| `adjustment_approve_action` | `/attendance/adjustments/<id>/approve/` | HR duyệt yêu cầu sửa. |
| `adjustment_reject_action` | `/attendance/adjustments/<id>/reject/` | HR từ chối yêu cầu sửa. |

**Services** (5 module trong `face/`, `record/`, `schedule/`):
- `face_api_client`: Giao tiếp với remote Face Recognition API (HuggingFace Spaces). Endpoints: `/register`, `/recognize`.
- `face_lockout_service`: Khóa tạm sau `FACE_LOCKOUT_MAX_FAILS` (3 lần) thất bại, thời gian `FACE_LOCKOUT_DURATION_SEC` (300 giây).
- `face_service`: Điều phối đăng ký/cập nhật khuôn mặt.
- `face_verification_service`: Điều phối nhận diện + ghi chấm công.
- `attendance_logging_service`: Ghi AttendanceRecord, tính status dựa trên giờ ca từ `contracts.services.get_shift_times`.

**Cấu hình** (từ `settings.py`):
- `FACE_API_BASE_URL`: Remote API URL (HuggingFace Spaces).
- `WORK_START_TIME = 08:30`, `WORK_END_TIME = 17:30`, `WORK_LATE_GRACE_MIN = 5`.

---

### 3.5 leaves

**Models** (1 model):

| Model | Mô tả |
|---|---|
| `LeaveRequest` | Đơn nghỉ phép. 6 loại: annual/sick/personal/maternity/business/other. 4 status: pending → leader_approved → approved / rejected. Phê duyệt 2 bước. `days` auto-tính từ date range. Attachment file. |

**Quy trình phê duyệt 2 bước**:
1. **Bước 1**: Leader/Manager trực tiếp duyệt → `leader_approved`
2. **Bước 2**: HR duyệt cuối → `approved`
3. **Ngoại lệ**: Nếu người tạo đơn có role HR → chỉ cần bước 1 là hoàn tất.

**Views** (6 views):

| View | URL | Mô tả |
|---|---|---|
| `leave_view` | `/leave/` | Nhân viên xem/tạo đơn nghỉ phép + thống kê cá nhân. |
| `leave_approval_view` | `/leave/approval/` | Manager/HR xem đơn cần duyệt. |
| `leave_cancel_view` | `/leave/cancel/<pk>/` | Nhân viên hủy đơn (chỉ status=pending). |
| `leave_approve_action` | `/leave/approve/<pk>/` | Duyệt 1 đơn. |
| `leave_reject_action` | `/leave/reject/<pk>/` | Từ chối 1 đơn (ở cả 2 bước). |
| `leave_bulk_approve` | `/leave/bulk-approve/` | Duyệt hàng loạt. |

**Services** (`leaves/services/__init__.py`):
- `create_leave_request`: Auto-tính `days = (end_date - start_date).days + 1`.
- `cancel_leave_request`: Chỉ cho hủy đơn `pending`.
- `get_user_leave_stats`: Thống kê năm hiện tại (used_days từ approved, total_allowed từ contract).
- `approve_leave_request`: Logic 2 bước (kiểm tra `_is_direct_supervisor` + `_is_hr_role`).
- `reject_leave_request`: Cho reject ở cả 2 bước.
- `bulk_approve_requests`: Duyệt hàng loạt.
- Mỗi action approve/reject đều tạo `Notification` cho nhân viên.

---

### 3.6 overtime

**Models** (1 model):

| Model | Mô tả |
|---|---|
| `OvertimeRequest` | Đơn tăng ca. Fields: overtime_date, start_time, end_time, hours, reason, attachment. 4 status giống leaves. Phê duyệt 2 bước giống leaves. |

**Views** (6 views):

| View | URL | Mô tả |
|---|---|---|
| `overtime_view` | `/overtime/` | Xem/tạo đơn + thống kê tháng + biểu đồ 4 tuần. |
| `overtime_cancel_view` | `/overtime/cancel/<pk>/` | Hủy đơn (chỉ pending). |
| `overtime_approval_view` | `/overtime/approval/` | Manager/HR xem đơn cần duyệt. |
| `overtime_approve_action` | `/overtime/approve/<pk>/` | Duyệt 1 đơn. |
| `overtime_reject_action` | `/overtime/reject/<pk>/` | Từ chối 1 đơn. |
| `overtime_bulk_approve` | `/overtime/bulk-approve/` | Duyệt hàng loạt. |

**Services** (`overtime/services/__init__.py`):
- Logic phê duyệt 2 bước giống leaves.
- `get_user_overtime_stats`: Thống kê tháng (total_hours, approved_count, pending_count, total_pay = hours × 150,000 VND).
- `get_monthly_chart_data`: Dữ liệu biểu đồ 4 tuần gần nhất.
- `get_approved_overtime_end`: Trả giờ kết thúc OT muộn nhất (dùng cho tính chấm công).

---

### 3.7 performance

**Models** (2 model):

| Model | Quan hệ | Mô tả |
|---|---|---|
| `EvaluationCategory` | — | Loại đánh giá (HR/Admin cấu hình): name (unique), description. |
| `Evaluation` | FK → `User` (employee, reviewer, acknowledged_by), FK → `EvaluationCategory` | Bản đánh giá. Status: draft → submitted → acknowledged. Rating: A/B/C/D (auto từ score: ≥90→A, ≥75→B, ≥60→C, <60→D). Override `save()` để tính rating từ score. |

**Views** (3 views):

| View | URL | Mô tả |
|---|---|---|
| `evaluations_view` | `/evaluations/` | Xem/tạo đánh giá (Manager/Leader tạo, Employee xem received). |
| `evaluation_hr_approval_view` | `/evaluations/hr-approval/` | HR xem danh sách đánh giá chờ xác nhận. |
| `evaluation_hr_acknowledge_action` | `/evaluations/<pk>/acknowledge/` | HR xác nhận 1 đánh giá. |

---

### 3.8 rewards_discipline

**Models** (1 model):

| Model | Mô tả |
|---|---|
| `RewardPenalty` | Phiếu khen thưởng/xử phạt. type: reward/penalty. Phê duyệt 2 cấp: pending → leader_approved → approved. amount (VND), reason_title, reason_detail, evidence_file, application_date. |

**Views** (2 views):

| View | URL | Mô tả |
|---|---|---|
| `rewards_penalties_view` | `/rewards-penalties/` | Xem/tạo phiếu thưởng/phạt. |
| `rewards_penalties_approval_view` | `/rewards-penalties/approval/` | Manager/HR duyệt phiếu. |

---

### 3.9 reports_interactions

**Models** (2 model):

| Model | Mô tả |
|---|---|
| `Report` | Báo cáo cá nhân: author → recipient (quản lý). Status: submitted → needs_update / acknowledged. File attachment, manager_note. Property `can_edit_or_delete` (khóa khi acknowledged). |
| `Ticket` | Ticket hỗ trợ/khiếu nại: type (support/complaint), priority (low/medium/high), status (new/processing/resolved/closed/rejected). assigned_to (HR), evidence_file. |

**Views** (5 views):

| View | URL | Mô tả |
|---|---|---|
| `report_view` | `/reports/` | Nhân viên xem/tạo/sửa/xóa báo cáo. |
| `report_inbox_view` | `/reports/inbox/` | Quản lý xem báo cáo nhận được. |
| `report_detail_view` | `/reports/<pk>/` | Xem chi tiết + phản hồi báo cáo. |
| `ticket_list_view` | `/tickets/` | Xem/tạo ticket. |
| `ticket_process_view` | `/tickets/process/` | HR xử lý ticket. |

---

### 3.10 stats_reports

**Không có model riêng** — thu thập dữ liệu trực tiếp từ các app khác.

**Views** (3 views):

| View | URL | Mô tả |
|---|---|---|
| `statistics_view` | `/statistics/` | Trang thống kê tổng hợp với filter + charts. |
| `statistics_export_excel_view` | `/statistics/export-excel/` | Xuất dữ liệu thống kê ra file Excel (openpyxl). |
| `statistics_print_view` | `/statistics/print/` | Trang in thống kê. |

**Phạm vi thống kê** (từ `get_statistics_scope`):
- **HR/Admin**: Toàn công ty (trừ Admin users).
- **Manager**: Nhân viên cùng phòng ban.
- **Leader**: Nhân viên được gán làm leader_user.
- **Employee**: Không có quyền.

**Loại thống kê**: all, leave, attendance, summary, evaluation, rewards.

**Bộ lọc thời gian**: this_month, last_7_days, last_30_days, this_quarter, this_year, custom.

**Bộ lọc tổ chức**: department, manager, leader, employee.

---

## 4. Shared Module: common

- `common/file_validation.py`: Hàm `validate_upload` dùng chung cho mọi FileField.
  - `MAX_UPLOAD_BYTES = 5 MB`
  - `DOCUMENT_MIME = {application/pdf, image/jpeg, image/png}`
  - `EVIDENCE_MIME = DOCUMENT_MIME + {image/gif, image/webp}`

---

## 5. Deployment

### Render Blueprint (`render.yaml`)

```yaml
services:
  - type: web
    name: business-web
    runtime: python
    plan: free
    rootDir: business_web
    buildCommand: "./build.sh"
    startCommand: "gunicorn business_web.wsgi:application"
databases:
  - name: business-web-db
    plan: free
```

### Build script (`build.sh`)

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py ensure_superuser
```

### Biến môi trường production

| Biến | Mô tả |
|---|---|
| `SECRET_KEY` | Auto-generate bởi Render |
| `DEBUG=False` | Production mode |
| `DATABASE_URL` | PostgreSQL connection string |
| `USE_CLOUDINARY=True` | Media storage qua Cloudinary |
| `CLOUDINARY_*` | Cloud name, API key, API secret |
| `EMAIL_HOST_USER/PASSWORD` | Gmail SMTP credentials |
| `FACE_API_BASE_URL` | HuggingFace Spaces URL |

---

## 6. Tổng hợp URL Routes

### Public (không cần đăng nhập)
| Path | Name | View |
|---|---|---|
| `/` | `home` | Redirect → login |
| `/login/` | `login` | `AccountsLoginView` |
| `/register/` | `register` | `register_view` |
| `/forgot-password/` | `forgot_password` | `forgot_password_view` |
| `/reset-password/` | `reset_password_after_otp` | `reset_password_after_otp_view` |
| `/logout/` | `logout` | `logout_view` |

### Authenticated — Common
| Path | Name |
|---|---|
| `/dashboard/` | `dashboard` |
| `/settings/` | `settings` |
| `/notifications/` | `notifications` |
| `/notifications/mark-read/` | `mark_notifications_read` |

### Admin
| Path | Name |
|---|---|
| `/users/` | `user_list` |
| `/users/create-account/` | `admin_create_account` |
| `/users/<id>/permissions/` | `assign_permissions` |
| `/users/<id>/delete/` | `delete_user` |
| `/users/<id>/toggle-active/` | `toggle_active` |
| `/users/<id>/reset-password/` | `reset_user_password` |

### Employee Profiles
| Path | Name |
|---|---|
| `/profile/` | `profile` |
| `/profile/upload-document/` | `upload_document` |
| `/hr/create-profile/` | `hr_create_profile` |
| `/users/<id>/profile/` | `hr_view_profile` |
| `/users/<id>/assign-role/` | `hr_assign_role` |
| `/users/<id>/work-info/` | `edit_work_info` |

### Contracts
| Path | Name |
|---|---|
| `/contract/` | `contract` |
| `/contract/hr/expiring/` | `hr_expiring_contracts` |
| `/contract/hr/send-reminder/<id>/` | `hr_send_reminder` |
| `/contract/hr/send-all-reminders/` | `hr_send_all_reminders` |
| `/contract/hr/adjust/<id>/` | `hr_adjust_contract` |
| `/contract/history/<id>/` | `contract_history` |

### Attendance
| Path | Name |
|---|---|
| `/attendance/` | `attendance` |
| `/attendance/upload-image/` | `upload_image_base64` |
| `/attendance/check/` | `face_check` |
| `/attendance/face-changes/review/` | `face_change_review` |
| `/attendance/face-changes/<id>/approve/` | `face_change_approve` |
| `/attendance/face-changes/<id>/reject/` | `face_change_reject` |
| `/attendance/face-changes/<id>/image/` | `face_change_image` |
| `/attendance/adjustment/<record_id>/` | `attendance_adjustment` |
| `/attendance/adjustments/review/` | `attendance_adjustment_review` |
| `/attendance/adjustments/<id>/approve/` | `attendance_adjustment_approve` |
| `/attendance/adjustments/<id>/reject/` | `attendance_adjustment_reject` |

### Leaves
| Path | Name |
|---|---|
| `/leave/` | `leave` |
| `/leave/approval/` | `leave_approval` |
| `/leave/cancel/<pk>/` | `leave_cancel` |
| `/leave/approve/<pk>/` | `leave_approve` |
| `/leave/reject/<pk>/` | `leave_reject` |
| `/leave/bulk-approve/` | `leave_bulk_approve` |

### Overtime
| Path | Name |
|---|---|
| `/overtime/` | `overtime` |
| `/overtime/cancel/<pk>/` | `overtime_cancel` |
| `/overtime/approval/` | `overtime_approval` |
| `/overtime/approve/<pk>/` | `overtime_approve` |
| `/overtime/reject/<pk>/` | `overtime_reject` |
| `/overtime/bulk-approve/` | `overtime_bulk_approve` |

### Performance
| Path | Name |
|---|---|
| `/evaluations/` | `evaluations` |
| `/evaluations/hr-approval/` | `evaluation_hr_approval` |
| `/evaluations/<pk>/acknowledge/` | `evaluation_acknowledge` |

### Rewards & Discipline
| Path | Name |
|---|---|
| `/rewards-penalties/` | `rewards_penalties` |
| `/rewards-penalties/approval/` | `rewards_penalties_approval` |

### Reports & Interactions
| Path | Name |
|---|---|
| `/reports/` | `reports` |
| `/reports/inbox/` | `report_inbox` |
| `/reports/<pk>/` | `report_detail` |
| `/tickets/` | `tickets` |
| `/tickets/process/` | `ticket_process` |

### Statistics
| Path | Name |
|---|---|
| `/statistics/` | `statistics` |
| `/statistics/export-excel/` | `statistics_export_excel` |
| `/statistics/print/` | `statistics_print` |

---

## 7. Test Suite

Tổng cộng **229 unit tests** phân bổ trong thư mục `tests/` của từng app:

| App | Số file test | Test cases |
|---|---|---|
| `accounts` | 11 | Login, Register, Forgot Password, Admin Management, Role/Permission, Security (CSRF, IDOR, XSS, SQL injection, password hashing), Notifications, RBAC Approval, Admin Access, Work Schedule Settings, bổ sung (OTP boundary, session config) |
| `attendance` | 6 | Attendance view, Face check, Face upload, Face lockout, Work schedule, Adjustment |
| `contracts` | 5 | Contracts CRUD, Contract versioning, Date order validation, Renewal thresholds, Shift time order |
| `employee_profiles` | 6 | Profile view, HR create profile, HR assign role, Edit work info, Create validation, Upload document |
| `leaves` | 2 | Leave CRUD + approval 2 bước, Leave L1 |
| `overtime` | 2 | Overtime CRUD + approval 2 bước, OT HR skip L2 |
| `performance` | 3 | Evaluation CRUD, Eval lock (acknowledged → không sửa), Self-evaluation policy |
| `rewards_discipline` | 3 | Rewards CRUD + approval, Amount boundary, Rewards scope |
| `reports_interactions` | 1 | Reports + Tickets CRUD + workflow |
| `stats_reports` | 2 | Stats reports, Stats accuracy |

### Performance Tests (`tests_perf/`)
- `locustfile.py`: Load test chung.
- `locustfile_face.py`: Load test chấm công khuôn mặt.
- `fake_face_api.py`: Mock Face API server.

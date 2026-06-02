# 🧪 Kế Hoạch Kiểm Thử Toàn Hệ Thống — HRMS

> **Hệ thống Quản lý Nhân sự (HRMS)** · Môn SE104 – Nhập môn Công nghệ Phần mềm
> Stack: Django · PostgreSQL (prod) / SQLite3 (dev) · Tailwind · Alpine.js · Remote Face API
> Tài liệu nghiệp vụ gốc: [walkthrough.md](walkthrough.md) · Kiến trúc deploy: [deployment_architecture.md](deployment_architecture.md)
>
> Phiên bản kế hoạch: **v1.0** · Ngày lập: **02/06/2026** · Phạm vi: **10 Django app (đồng đều)**

---

## §0. Thông Tin Chung (Meta)

### 0.1 Mục tiêu
Đảm bảo HRMS **làm đúng nghiệp vụ**, **dễ dùng**, **chạy được trên nhiều môi trường**, **chịu tải mục tiêu**, và **an toàn dữ liệu**. Kế hoạch phủ 5 nhóm: Chức năng, UI/UX, Tương thích, Hiệu năng, Bảo mật + truy vết quy định nghiệp vụ.

### 0.2 Phạm vi
> [!IMPORTANT]
> **Scope hiện tại = chỉ KIỂM THỬ tính đúng đắn của hệ thống.** Việc *chỉnh sửa lại cơ chế thông báo lỗi/thành công* dựa trên kết quả kiểm thử là **giai đoạn SAU**, không nằm trong đợt này (xem §8).
> **Chỉ kiểm trên giao diện DESKTOP.** Mobile/tablet/cross-OS tạm out-of-scope (xem §3).

| Trong phạm vi | Ngoài phạm vi |
|---|---|
| 10 app: `accounts`, `employee_profiles`, `contracts`, `attendance`, `leaves`, `overtime`, `performance`, `rewards_discipline`, `reports_interactions`, `stats_reports` | Internals Remote Face API (DeepFace/FAISS — của bên thứ ba, chỉ test qua HTTP + mock) |
| CRUD, validation, boundary, business flow, RBAC, vòng đời trạng thái | Hạ tầng Render/Cloudinary/Gmail SMTP (chỉ test cấu hình + smoke) |
| Bảo mật tầng ứng dụng (authn/authz, XSS, SQLi, IDOR, upload, session) | Pentest chuyên sâu hạ tầng, audit mã nguồn bên thứ ba |
| Giao diện **desktop** (Chrome/Firefox/Edge trên Windows) | Mobile, tablet, iOS, Android, Safari/macOS, responsive breakpoint nhỏ |
| Kiểm cơ chế thông báo lỗi/thành công đã đúng chưa | **Sửa/redesign** cơ chế thông báo (đợt sau) |

### 0.2b Nguyên tắc "Kết quả mong đợi" cho thông báo end user
Mọi case mà **end user cần biết để điều chỉnh hành vi** → kết quả mong đợi phải gồm **thông báo lỗi/thành công hiển thị rõ ràng** (toast/inline error/flash message tiếng Việt). Cụ thể:
- ✅ **Phải có thông báo:** validation sai (sai định dạng, trống, quá ký tự, vượt biên), thao tác thành công (tạo/sửa/xóa/duyệt/chấm công), nghiệp vụ chặn có thể sửa (vượt quỹ phép, ngày không hợp lệ, OTP sai/hết hạn, file quá cỡ, đã nộp rồi…).
- 🚫 **KHÔNG cần thông báo cho end user (chỉ chặn):** lỗi `403`/redirect do thiếu quyền, vi phạm an toàn (CSRF, IDOR, truy cập URL trái phép). Các case này kết quả mong đợi = **chặn im lặng / redirect login**, KHÔNG lộ chi tiết.

### 0.3 Môi trường test
| Môi trường | Cấu hình | Dùng cho |
|---|---|---|
| **Dev/CI** | SQLite3 in-memory, `DEBUG=True`, Face API **mock** | Functional tự động (Django `TestCase`), chạy nhanh |
| **Staging-local** | SQLite3/PostgreSQL local, `runserver`, Locust trỏ vào | Performance (§4), UI/UX thủ công (§2) |
| **Prod (live)** | Render — https://business-web-project.onrender.com/login/ — PostgreSQL, `DEBUG=False`, HTTPS, Cloudinary, Face API thật | Smoke + Security (§5) + Compatibility desktop (§3) |

### 0.4 Công cụ
| Nhóm | Công cụ |
|---|---|
| Functional | Django `TestCase` + `Client`, `unittest.mock` (mock Face API & SMTP), `coverage.py` |
| UI/UX | Kiểm thử thủ công + checklist; Playwright (tùy chọn, nếu cài) cho trạng thái tương tác |
| Compatibility | Chrome, Firefox, Edge trên Windows (desktop) — bản mới nhất |
| Performance | **Locust** (HTTP load), Chrome DevTools Network throttle (3G) |
| Security | Django test client (RBAC/IDOR), `python manage.py check --deploy`, `bandit` (SAST), kiểm thử thủ công XSS/SQLi |

### 0.5 Cách chạy
```bash
# Functional — toàn bộ
cd business_web && python manage.py test

# Một app
python manage.py test leaves

# Độ phủ
coverage run --source='.' manage.py test && coverage report -m

# Bảo mật cấu hình deploy
python manage.py check --deploy

# Performance (sau khi runserver)
locust -f tests_perf/locustfile.py --host=http://127.0.0.1:8000
```

### 0.6 Quy ước Test Case ID
| Tiền tố | Nhóm | Ví dụ |
|---|---|---|
| `FUNC-<APP>-NNN` | Chức năng (theo app) | `FUNC-LEA-003` |
| `UIX-NNN` | UI/UX | `UIX-007` |
| `COMPAT-NNN` | Tương thích | `COMPAT-002` |
| `PERF-NNN` | Hiệu năng | `PERF-001` |
| `SEC-NNN` | Bảo mật | `SEC-005` |

Mã app: `ACC` accounts · `EP` employee_profiles · `CON` contracts · `ATT` attendance · `LEA` leaves · `OT` overtime · `PERF`→`PER` performance · `RW` rewards_discipline · `RI` reports_interactions · `ST` stats_reports.

**Ưu tiên:** 🔴 Cao (chặn release) · 🟡 Trung bình · 🟢 Thấp.
**Loại:** H = Happy path · N = Negative · B = Boundary.
**Cột "Tự động hóa":** tên file test đã tồn tại / `[BỔ SUNG]` = cần viết thêm.

---

## §1. Kiểm Thử Chức Năng (Functional Testing)

> Phần quan trọng nhất. Mỗi app có bảng riêng phủ CRUD + validation (H/N/B) + business flow + RBAC + vòng đời trạng thái.

### 1.1 `accounts` — Tài khoản, Đăng nhập, Phân quyền

| ID | Chức năng | Tiền điều kiện | Bước | Dữ liệu vào | Kết quả mong đợi | Loại | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|---|---|---|
| FUNC-ACC-001 | Đăng nhập đúng | User active tồn tại | POST /login/ | username + password đúng | Redirect dashboard theo role, tạo session | H | 🔴 | test_login.py::valid_credentials |
| FUNC-ACC-002 | Đăng nhập sai mật khẩu | User tồn tại | POST /login/ | password sai | Báo "Sai thông tin đăng nhập", không tạo session | N | 🔴 | test_login.py::invalid_credentials |
| FUNC-ACC-003 | Đăng nhập tài khoản bị khóa | `is_active=False` | POST /login/ | credentials đúng | Báo "Tài khoản bị khóa" | N | 🔴 | test_login.py::inactive_account |
| FUNC-ACC-004 | Khóa sau 3 lần sai (QĐ_TK1) | User active | POST /login/ sai 3 lần | sai liên tiếp | Lần 3 → `is_active=False` | B | 🔴 | **[BỔ SUNG]** — chưa có code đếm failed_login (xem §6) |
| FUNC-ACC-005 | Quên MK — gửi OTP | Email tồn tại | POST /forgot-password/ | email hợp lệ | Sinh OTP 6 số, lưu `OtpCode`, gửi email | H | 🔴 | test_forgot_password.py::request_otp_valid |
| FUNC-ACC-006 | Quên MK — email không tồn tại | — | POST /forgot-password/ | email lạ | Báo "Email không tìm thấy" | N | 🟡 | **[BỔ SUNG]** |
| FUNC-ACC-007 | Xác thực OTP đúng & còn hạn | OTP vừa tạo | POST /reset-password/ | OTP đúng, <120s | Cho đổi MK | H | 🔴 | test_forgot_password.py::verify_otp_valid |
| FUNC-ACC-008 | OTP sai | OTP tồn tại | POST /reset-password/ | OTP sai | Báo "Mã OTP không đúng" | N | 🔴 | test_forgot_password.py::verify_otp_invalid |
| FUNC-ACC-009 | OTP hết hạn (boundary 120s) | OTP tạo >120s | POST /reset-password/ | OTP đúng nhưng quá hạn | Báo "OTP đã hết hạn"; thử tại 119s/120s/121s | B | 🔴 | **[BỔ SUNG]** (mở rộng từ verify_otp) |
| FUNC-ACC-010 | Đổi MK thành công | OTP hợp lệ | POST /reset-password/ | MK mới hợp lệ | Cập nhật password, xóa OtpCode | H | 🔴 | test_forgot_password.py::reset_password_success |
| FUNC-ACC-011 | Gán role (Admin) | Đăng nhập Admin | Gán role cho user | role hợp lệ | Cập nhật `UserProfile.role` | H | 🔴 | test_role_permission.py::assign_role |
| FUNC-ACC-012 | Gỡ role | role đã gán | Gỡ role | — | `role=None` (SET_NULL) | H | 🟡 | test_role_permission.py::remove_role |
| FUNC-ACC-013 | Gán custom permission | Admin | Gán `CustomPermission` | codename | M2M thêm quyền, `has_custom_permission()=True` | H | 🟡 | test_role_permission.py::assign_custom_permission |
| FUNC-ACC-014 | Non-admin không gán được role | User thường | Truy cập trang gán role | — | 403/redirect | N | 🔴 | test_role_permission.py::non_admin_access |
| FUNC-ACC-015 | Admin xem danh sách user | Admin | GET trang user list | — | Hiển thị danh sách | H | 🟡 | test_admin_management.py::view_user_list_as_admin |
| FUNC-ACC-016 | Non-admin xem user list bị chặn | User thường | GET user list | — | 403/redirect | N | 🔴 | test_admin_management.py::view_user_list_as_non_admin |
| FUNC-ACC-017 | Admin xóa user khác | Admin | Xóa user | target user | User bị xóa | H | 🟡 | test_admin_management.py::delete_other_user |
| FUNC-ACC-018 | Admin không tự xóa mình | Admin | Xóa chính mình | self | Bị chặn | N | 🔴 | test_admin_management.py::delete_self |
| FUNC-ACC-019 | Khóa/mở tài khoản | Admin/HR | Toggle `is_active` | target | Trạng thái đảo | H | 🟡 | test_admin_management.py::toggle_user_active |
| FUNC-ACC-020 | Không tự khóa mình | Admin | Toggle self | self | Bị chặn | N | 🟡 | test_admin_management.py::toggle_self_active |
| FUNC-ACC-021 | Admin reset MK user | Admin | Reset password | target | MK đặt lại | H | 🟡 | test_admin_management.py::reset_user_password |

### 1.2 `employee_profiles` — Hồ sơ nhân sự

| ID | Chức năng | Tiền điều kiện | Bước | Dữ liệu vào | Kết quả mong đợi | Loại | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|---|---|---|
| FUNC-EP-001 | HR tạo hồ sơ hợp lệ (Create) | Đăng nhập HR | POST /employees/create/ | MSNV + đủ field | Tạo User+UserProfile+PersonalInfo+WorkInfo, gửi email, username=MSNV thường, pass `{MSNV}@2026` | H | 🔴 | test_hr_create_profile.py::valid_creation |
| FUNC-EP-002 | Trùng MSNV (employee_id) | MSNV đã tồn tại | POST create | MSNV trùng | Báo lỗi, không tạo | N | 🔴 | test_hr_create_profile.py::duplicate_employee_id |
| FUNC-EP-003 | MSNV trống (bắt buộc) | HR | POST create | MSNV rỗng | Lỗi validation | N | 🔴 | **[BỔ SUNG]** |
| FUNC-EP-004 | Department trống (bắt buộc) | HR | POST create | thiếu department | Lỗi validation | N | 🟡 | **[BỔ SUNG]** |
| FUNC-EP-005 | Non-HR tạo hồ sơ bị chặn | User thường | POST create | — | 403/redirect | N | 🔴 | test_hr_create_profile.py::non_hr_access |
| FUNC-EP-006 | Ngày phép HĐ không hợp lệ (boundary) | HR | POST create | annual_leave_days âm/0/quá lớn | Lỗi validation; thử -1, 0, max | B | 🟡 | test_hr_create_profile.py::invalid_contract_days |
| FUNC-EP-007 | Xem hồ sơ (Read) | NV đăng nhập | GET /profile/ | — | Hiển thị đúng thông tin | H | 🔴 | test_profile_view.py::view_profile |
| FUNC-EP-008 | Cập nhật thông tin cơ bản (Update) | NV | POST update | field mới hợp lệ | Lưu thành công | H | 🔴 | test_profile_view.py::update_basic_info |
| FUNC-EP-009 | Email trùng khi cập nhật | Email đã dùng | POST update | email trùng | Lỗi validation | N | 🟡 | test_profile_view.py::duplicate_email |
| FUNC-EP-010 | HR sửa toàn bộ bảng work info | HR | POST edit work info | đủ bảng | Lưu hết | H | 🟡 | test_edit_work_info.py::edit_all_tables |
| FUNC-EP-011 | Non-HR sửa work info bị chặn | User thường | POST edit | — | 403 | N | 🔴 | test_edit_work_info.py::non_hr_access |
| FUNC-EP-012 | HR gán role qua hồ sơ | HR | Gán role | employee/leader/manager | Thành công | H | 🟡 | test_hr_assign_role.py::hr_assign_role |
| FUNC-EP-013 | HR không gán được role admin | HR | Gán admin | role=admin | Bị từ chối | N | 🔴 | test_hr_assign_role.py::hr_assign_admin_denied |
| FUNC-EP-014 | Admin gán role admin | Admin | Gán admin | role=admin | Thành công | H | 🟡 | test_hr_assign_role.py::admin_assign_admin |
| FUNC-EP-015 | Upload tài liệu hợp lệ (Create) | NV | POST upload doc | PDF/JPG hợp lệ | Lưu `EmployeeDocument` | H | 🟡 | test_upload_document.py::upload_valid_document |
| FUNC-EP-016 | Upload không có file | NV | POST upload | trống | Lỗi validation | N | 🟡 | test_upload_document.py::no_file |
| FUNC-EP-017 | Upload sai định dạng/quá 5MB (boundary) | NV | POST upload | .exe / 5MB+1 byte | Bị từ chối; thử 5MB-1, 5MB, 5MB+1 | B | 🟡 | **[BỔ SUNG]** |

### 1.3 `contracts` — Hợp đồng lao động

| ID | Chức năng | Tiền điều kiện | Bước | Dữ liệu vào | Kết quả mong đợi | Loại | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|---|---|---|
| FUNC-CON-001 | Xem hợp đồng (Read) | HĐ tồn tại | GET contract view | — | Hiển thị HĐ | H | 🟡 | test_contracts.py::contract_view |
| FUNC-CON-002 | Lấy HĐ đang hiệu lực | Nhiều HĐ, 1 active | gọi `get_active_contract` | — | Trả HĐ `is_active=True` | H | 🔴 | test_contracts.py::get_active_contract_returns_active |
| FUNC-CON-003 | 1 NV nhiều HĐ theo thời gian | — | Tạo nhiều HĐ | — | Cho phép N HĐ, chỉ 1 active | H | 🟡 | test_contracts.py::user_can_have_multiple_contracts |
| FUNC-CON-004 | Ràng buộc ngày: BĐ ≥ Ký | HR | Tạo HĐ | start < signed | Lỗi validation | N | 🔴 | **[BỔ SUNG]** |
| FUNC-CON-005 | Ràng buộc ngày: Hết hạn ≥ BĐ | HR | Tạo HĐ | end < start | Lỗi validation | N | 🔴 | **[BỔ SUNG]** |
| FUNC-CON-006 | HR xem HĐ sắp hết hạn | Có HĐ gần hết | GET expiring view | — | Liệt kê đúng | H | 🟡 | test_contracts.py::hr_expiring_contracts_view |
| FUNC-CON-007 | HR gửi nhắc hết hạn | HĐ sắp hết | Bấm gửi nhắc | — | Gửi thông báo | H | 🟢 | test_contracts.py::hr_send_reminder |
| FUNC-CON-008 | Batch cảnh báo 2 mốc 30/7 ngày (boundary) | HĐ end_date đa dạng | Chạy batch | days_left = 31,30,8,7,1,0,-1 | 30→far, 7→near, <0→`is_active=False`; kiểm biên 30/31, 7/8, 0/-1 | B | 🔴 | **[BỔ SUNG]** (xem §6: Render free no cron) |

### 1.4 `attendance` — Chấm công FaceID

| ID | Chức năng | Tiền điều kiện | Bước | Dữ liệu vào | Kết quả mong đợi | Loại | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|---|---|---|
| FUNC-ATT-001 | NV tự upload mặt → pending | Đã có mặt | POST upload-image | ảnh | Tạo `FaceChangeRequest(pending)` | H | 🔴 | test_face_upload.py::self_upload_is_pending |
| FUNC-ATT-002 | HR upload → áp ngay (approved) | HR | POST upload | ảnh | Upsert EmployeeFace, request=approved | H | 🔴 | test_face_upload.py::hr_upload_applies_immediately |
| FUNC-ATT-003 | HR duyệt pending → enroll | Có pending | approve_face_change | — | Gọi /register, cập nhật EmployeeFace | H | 🔴 | test_face_upload.py::hr_approve_pending_enrolls |
| FUNC-ATT-004 | HR từ chối → không enroll | Có pending | reject | lý do | status=rejected, không gọi register | N | 🔴 | test_face_upload.py::hr_reject_does_not_enroll |
| FUNC-ATT-005 | Upload không data | NV | POST upload | trống | Lỗi | N | 🟡 | test_face_upload.py::no_data |
| FUNC-ATT-006 | Upload yêu cầu login | Chưa login | POST upload | — | Redirect login | N | 🔴 | test_face_upload.py::require_login |
| FUNC-ATT-007 | Employee không vào trang duyệt | Employee | GET review | — | 403 | N | 🔴 | test_face_upload.py::employee_cannot_access_review |
| FUNC-ATT-008 | Check-in khớp mặt | Mặt đã enroll | POST /check/ | ảnh khớp | Lưu check_in, status on_time/late | H | 🔴 | test_face_check.py::check_in |
| FUNC-ATT-009 | Check-out | Đã check-in | POST /check/ | ảnh khớp | Lưu check_out, status (early_leave?) | H | 🔴 | test_face_check.py::check_out |
| FUNC-ATT-010 | Sai người (wrong_person) | Mặt người khác | POST /check/ | employee_id≠user | 403 wrong_person, tăng đếm lockout | N | 🔴 | test_face_check.py::wrong_face |
| FUNC-ATT-011 | Chưa upload mặt | Không có EmployeeFace | POST /check/ | ảnh | Báo lỗi no_face_uploaded | N | 🟡 | test_face_check.py::no_face_uploaded |
| FUNC-ATT-012 | Lockout 3 fail → khóa 300s (boundary) | — | fail 3 lần | sai liên tiếp | Lần 3 khóa 300s; kiểm fail 2/3/4 | B | 🔴 | **[BỔ SUNG]** |
| FUNC-ATT-013 | Phân loại on_time/late biên grace | — | check_in quanh shift_start+grace | t = grace-1, grace, grace+1 | Đúng on_time/late tại biên | B | 🔴 | test_attendance_view.py::classify_status |
| FUNC-ATT-014 | early_leave = max(shift_end, OT duyệt) | Có OT approved | check_out sớm | — | Tính đúng giờ tan kỳ vọng | B | 🟡 | test_attendance_view.py::get_shift_times_fallback |
| FUNC-ATT-015 | Xem lịch sử chấm công | Có record | GET records | — | Hiển thị đúng | H | 🟡 | test_attendance_view.py::view_records / data_correctness |
| FUNC-ATT-016 | Xem record yêu cầu login | Chưa login | GET | — | Redirect | N | 🟡 | test_attendance_view.py::require_login |
| FUNC-ATT-017 | Nộp yêu cầu điều chỉnh hợp lệ | Có record | POST adjustment | giờ + minh chứng | Tạo `AdjustmentRequest(pending)` | H | 🔴 | test_adjustment.py::submit_valid |
| FUNC-ATT-018 | Đã nộp rồi không nộp lại | Có pending | POST lần 2 | — | Bị chặn (OneToOne) | N | 🟡 | test_adjustment.py::already_submitted |
| FUNC-ATT-019 | Ngoài tháng bị từ chối | Record tháng trước | POST adjustment | ngày ngoài tháng | Bị chặn | N | 🟡 | test_adjustment.py::out_of_month_rejected |
| FUNC-ATT-020 | Yêu cầu ≥1 giờ (in HOẶC out) | — | POST | cả 2 trống | Lỗi validation | B | 🔴 | test_adjustment.py::requires_at_least_one_time |
| FUNC-ATT-021 | Bắt buộc minh chứng | — | POST | thiếu evidence | Lỗi | N | 🔴 | test_adjustment.py::requires_evidence |
| FUNC-ATT-022 | HR duyệt áp cả giờ vào/ra | Có pending | approve | — | Cập nhật record + status | H | 🔴 | test_adjustment.py::approve_applies_both_times |
| FUNC-ATT-023 | HR từ chối khôi phục trạng thái | Có pending | reject | — | Khôi phục late/no_checkout | N | 🔴 | test_adjustment.py::reject_restores_* |
| FUNC-ATT-024 | Leader/Manager nộp điều chỉnh | Leader/Manager | POST | — | Cho phép | H | 🟢 | test_adjustment.py::leader_can_submit / manager_can_submit |
| FUNC-ATT-025 | Non-HR không duyệt điều chỉnh | Employee | GET review | — | 403 | N | 🔴 | test_adjustment.py::non_hr_cannot_access_review |

### 1.5 `leaves` — Nghỉ phép

| ID | Chức năng | Tiền điều kiện | Bước | Dữ liệu vào | Kết quả mong đợi | Loại | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|---|---|---|
| FUNC-LEA-001 | Xem trang nghỉ phép | NV | GET leaves | — | Hiển thị | H | 🟢 | test_leaves.py::leave_view_get |
| FUNC-LEA-002 | Tạo đơn hợp lệ (Create) | Còn quỹ phép | POST create | loại+ngày+lý do | Tạo `LeaveRequest(pending)` | H | 🔴 | test_leaves.py::leave_create_valid |
| FUNC-LEA-003 | Ngày không hợp lệ (end < start) | — | POST create | end<start | Lỗi validation | N | 🔴 | test_leaves.py::leave_create_invalid_date |
| FUNC-LEA-004 | Vượt quỹ phép (boundary) | Quỹ còn N ngày | POST create | days = N-1, N, N+1 | N+1 bị chặn "Không đủ phép" | B | 🔴 | **[BỔ SUNG]** |
| FUNC-LEA-005 | Hủy đơn pending | Đơn pending | Cancel | — | Đơn bị hủy | H | 🟡 | test_leaves.py::leave_cancel |
| FUNC-LEA-006 | Không hủy đơn đã approved | Đơn approved | Cancel | — | Bị chặn | N | 🟡 | test_leaves.py::leave_cancel_approved |
| FUNC-LEA-007 | Luồng duyệt 2 cấp (L1→L2) | Đơn pending | L1 duyệt → HR duyệt | — | pending→leader_approved→approved | H | 🔴 | test_leaves.py::leave_approval_flow |
| FUNC-LEA-008 | Từ chối đơn | Đơn pending | Reject | lý do | status=rejected | N | 🔴 | test_leaves.py::leave_reject |
| FUNC-LEA-009 | Đính kèm minh chứng | NV | POST + file | PDF/JPG ≤5MB | Lưu attachment | H | 🟢 | test_leaves.py::create_leave_with_attachment |
| FUNC-LEA-010 | Từ chối file quá cỡ (boundary 5MB) | — | POST | file 5MB+ | Bị chặn | B | 🟡 | test_leaves.py::reject_oversize_attachment |
| FUNC-LEA-011 | L1 chỉ leader/manager của NV mới duyệt (QĐ_PheDuyet_L1) | NV có leader/manager gán | User khác duyệt L1 | non-supervisor | 403 | N | 🔴 | **[BỔ SUNG]** |

### 1.6 `overtime` — Tăng ca

| ID | Chức năng | Tiền điều kiện | Bước | Dữ liệu vào | Kết quả mong đợi | Loại | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|---|---|---|
| FUNC-OT-001 | Xem trang OT | NV | GET overtime | — | Hiển thị | H | 🟢 | test_overtime.py::overtime_view_get |
| FUNC-OT-002 | Đăng ký OT hợp lệ | — | POST create | ngày+giờ+lý do | Tạo `OvertimeRequest(pending)` | H | 🔴 | test_overtime.py::overtime_create_valid |
| FUNC-OT-003 | Giờ không hợp lệ (end ≤ start) | — | POST | end≤start | Lỗi | N | 🔴 | test_overtime.py::overtime_create_invalid_time |
| FUNC-OT-004 | Hủy đơn OT | pending | Cancel | — | Hủy | H | 🟡 | test_overtime.py::overtime_cancel |
| FUNC-OT-005 | Luồng duyệt 2 cấp | pending | L1→L2 | — | approved | H | 🔴 | test_overtime.py::overtime_approval_flow |
| FUNC-OT-006 | Từ chối OT | pending | Reject | lý do | rejected | N | 🔴 | test_overtime.py::overtime_reject |
| FUNC-OT-007 | Đính kèm minh chứng | — | POST + file | hợp lệ | Lưu | H | 🟢 | test_overtime.py::create_overtime_with_attachment |
| FUNC-OT-008 | HR tự tạo → bỏ qua L2 (QĐ ngoại lệ) | HR tạo đơn | L1 duyệt | — | Sau L1 → approved luôn | B | 🔴 | **[BỔ SUNG]** |

### 1.7 `performance` — Đánh giá nhân viên

| ID | Chức năng | Tiền điều kiện | Bước | Dữ liệu vào | Kết quả mong đợi | Loại | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|---|---|---|
| FUNC-PER-001 | Xem danh sách đánh giá | NV | GET evaluations | — | Hiển thị | H | 🟢 | test_performance.py::evaluations_view_get |
| FUNC-PER-002 | Manager tạo phiếu đánh giá | Manager | Create evaluation | score+nội dung | Tạo `Evaluation(draft)` | H | 🔴 | test_performance.py::manager_create_evaluation |
| FUNC-PER-003 | Rating tự suy từ score (boundary) | — | save() | score=59,60,74,75,89,90,100,0,101 | A≥90,B≥75,C≥60,D<60; kiểm biên & score ngoài 0-100 bị chặn | B | 🔴 | test_performance.py::rating_auto_from_score |
| FUNC-PER-004 | HR xác nhận đánh giá | submitted | Acknowledge | — | status=acknowledged | H | 🔴 | test_performance.py::hr_acknowledge_evaluation |
| FUNC-PER-005 | Submitted → khóa sửa (QĐ_LuuTruDanhGia) | submitted | Sửa | — | Bị chặn | N | 🔴 | **[BỔ SUNG]** |

### 1.8 `rewards_discipline` — Khen thưởng / Xử phạt

| ID | Chức năng | Tiền điều kiện | Bước | Dữ liệu vào | Kết quả mong đợi | Loại | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|---|---|---|
| FUNC-RW-001 | Employee xem thưởng/phạt | Employee | GET view | — | Chỉ thấy của mình | H | 🟡 | test_rewards_discipline.py::view_employee |
| FUNC-RW-002 | Manager lập phiếu thưởng | Manager | Propose | loại+amount+lý do | Tạo `RewardPenalty(pending)` | H | 🔴 | test_rewards_discipline.py::manager_propose_reward |
| FUNC-RW-003 | HR truy cập trang duyệt | HR | GET approval | — | Cho phép | H | 🟡 | test_rewards_discipline.py::hr_approval_access |
| FUNC-RW-004 | HR duyệt/từ chối | pending | Approve/Reject | — | approved/rejected | H | 🔴 | test_rewards_discipline.py::hr_approve_reject_reward |
| FUNC-RW-005 | Luồng 2 cấp: Leader lập → Manager L1 → HR L2 | Leader lập | L1→L2 | — | Đúng chuỗi; Manager lập thì bỏ L1 | B | 🟡 | **[BỔ SUNG]** |
| FUNC-RW-006 | amount boundary (0 = văn bản) | — | Create | amount=0, âm | 0 hợp lệ, âm bị chặn (PositiveInteger) | B | 🟢 | **[BỔ SUNG]** |

### 1.9 `reports_interactions` — Báo cáo & Helpdesk

| ID | Chức năng | Tiền điều kiện | Bước | Dữ liệu vào | Kết quả mong đợi | Loại | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|---|---|---|
| FUNC-RI-001 | Tạo báo cáo (Create) | NV | POST report | tiêu đề+nội dung+file | Tạo `Report(submitted)` | H | 🔴 | test_reports_interactions.py::create_report |
| FUNC-RI-002 | Sửa báo cáo (Update) | submitted/needs_update | Edit | — | Cập nhật | H | 🟡 | test_reports_interactions.py::edit_report |
| FUNC-RI-003 | Xóa báo cáo (Delete) | chưa acknowledged | Delete | — | Xóa | H | 🟡 | test_reports_interactions.py::delete_report |
| FUNC-RI-004 | Manager xem → mark viewed | submitted | Manager GET | — | is_viewed=True, viewed_at set | H | 🟡 | test_reports_interactions.py::view_report_marks_as_viewed |
| FUNC-RI-005 | Manager yêu cầu cập nhật | submitted | request update | note | status=needs_update | H | 🟡 | test_reports_interactions.py::recipient_request_update_sets_needs_update |
| FUNC-RI-006 | needs_update → NV sửa → submitted | needs_update | Edit | — | Quay lại submitted | H | 🟡 | test_reports_interactions.py::author_edit_needs_update_resets_to_submitted |
| FUNC-RI-007 | Acknowledged → khóa sửa/xóa (QĐ_XacNhanBaoCao) | acknowledged | Edit/Delete | — | Bị chặn | N | 🔴 | test_reports_interactions.py::acknowledged_locks |
| FUNC-RI-008 | Non-recipient không request update | User khác | request update | — | 403 | N | 🔴 | test_reports_interactions.py::non_recipient_request_update_denied |
| FUNC-RI-009 | Tạo ticket | NV | POST ticket | loại+ưu tiên+nội dung | Tạo `Ticket(new, assigned=null)` | H | 🔴 | test_reports_interactions.py::create_ticket |
| FUNC-RI-010 | Tiếp nhận ticket (claim) | new | Receive | — | assigned_to=self, status=processing | H | 🔴 | test_reports_interactions.py::process_ticket_receive |
| FUNC-RI-011 | Giải quyết ticket | processing | Resolve | — | status=resolved | H | 🟡 | test_reports_interactions.py::process_ticket_resolve |
| FUNC-RI-012 | Từ chối ticket | new/processing | Reject | lý do | status=rejected | N | 🟡 | test_reports_interactions.py::process_ticket_reject |

### 1.10 `stats_reports` — Thống kê tổng hợp

| ID | Chức năng | Tiền điều kiện | Bước | Dữ liệu vào | Kết quả mong đợi | Loại | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|---|---|---|
| FUNC-ST-001 | Employee xem thống kê của mình | Employee | GET stats | — | Chỉ dữ liệu cá nhân | H | 🟡 | test_stats_reports.py::statistics_view_employee |
| FUNC-ST-002 | Manager xem thống kê nhóm | Manager | GET stats | — | Dữ liệu nhân viên quản lý | H | 🟡 | test_stats_reports.py::statistics_view_manager |
| FUNC-ST-003 | Xuất Excel | Có dữ liệu | Export | — | File .xlsx hợp lệ | H | 🟢 | test_stats_reports.py::statistics_export_excel |
| FUNC-ST-004 | In thống kê | Có dữ liệu | Print | — | View in được | H | 🟢 | test_stats_reports.py::statistics_print |
| FUNC-ST-005 | Số liệu khớp DB thật (không mock) | Dữ liệu đa app | So khớp tổng | — | Tổng hợp đúng từ attendance/leaves/OT/perf/rewards | H | 🔴 | **[BỔ SUNG]** |

---

## §2. Kiểm Thử Giao Diện & Trải Nghiệm (UI/UX) — **desktop**

> Thủ công, kèm checklist. Không có Figma gốc → kiểm **nhất quán nội tại** thay vì so thiết kế ngoài. Chỉ trên desktop.
> Liên quan §0.2b: các case phản hồi (UIX-003/006/009) phải có thông báo rõ ràng cho end user.

| ID | Hạng mục | Cách kiểm | Kết quả mong đợi | Ưu tiên |
|---|---|---|---|---|
| UIX-001 | Nhất quán thị giác nội tại (không có Figma gốc) | Rà màu/font/size/spacing giữa các trang dashboard, form, bảng | Đồng nhất xuyên hệ thống, dùng đúng Tailwind token (không lệch tùy trang) | 🟡 |
| UIX-002 | Nhất quán nút bấm | Rà tất cả button (primary/secondary/danger) toàn hệ thống | Cùng style, cùng vị trí, cùng wording | 🟡 |
| UIX-003 | Nhất quán thông báo lỗi | Submit form sai ở mỗi app | Error message cùng phong cách, tiếng Việt rõ ràng | 🟡 |
| UIX-004 | Điều hướng menu theo role | Đăng nhập từng role | Menu hiện đúng quyền, link không gãy | 🔴 |
| UIX-005 | Nút Back / breadcrumb | Duyệt qua nhiều trang rồi Back | Quay lại đúng trạng thái, không lỗi | 🟡 |
| UIX-006 | Redirect sau hành động | Tạo/sửa/xóa thành công | Redirect đúng trang + flash message | 🟡 |
| UIX-007 | Trạng thái hover | Di chuột lên button/link | Có phản hồi visual (đổi màu/con trỏ) | 🟢 |
| UIX-008 | Trạng thái loading | Submit form chậm / chấm công FaceID (cold-start) | Hiện spinner / disable nút, không double-submit | 🔴 |
| UIX-009 | Phản hồi thành công/thất bại | Chấm công, nộp đơn, duyệt | Toast/badge rõ ràng (✅/❌) | 🔴 |
| UIX-010 | Trạng thái rỗng (empty state) | Xem danh sách khi chưa có dữ liệu | Hiển thị thông báo "Chưa có…" thay vì bảng trống lỗi | 🟢 |
| UIX-011 | Webcam permission denied | Từ chối quyền camera khi chấm công | Thông báo hướng dẫn rõ ràng, không crash | 🟡 |
| UIX-012 | Thanh theo dõi FaceChangeRequest | Trang Cài đặt khi pending/approved/rejected | Hiển thị đúng trạng thái trực quan | 🟡 |

---

## §3. Kiểm Thử Tương Thích (Compatibility) — **CHỈ DESKTOP**

> [!NOTE]
> Scope hiện tại: web **chỉ cần chạy tốt trên desktop**. Mobile/tablet/iOS/Android/Safari-macOS **tạm out-of-scope** — sẽ bổ sung khi mở rộng responsive ở đợt sau.

### 3.1 Ma trận trình duyệt desktop (Windows)
| ID | Trình duyệt | OS | Kiểm | Kết quả mong đợi |
|---|---|---|---|---|
| COMPAT-001 | Chrome (mới nhất) | Windows | Toàn bộ flow chính (login, dashboard, CRUD, FaceID) | Hoạt động đầy đủ, không lỗi JS/layout |
| COMPAT-002 | Firefox (mới nhất) | Windows | Như trên | Tương đương Chrome |
| COMPAT-003 | Edge (mới nhất) | Windows | Như trên | Tương đương Chrome |

### 3.2 Độ phân giải desktop
| ID | Loại màn hình | Breakpoint | Kiểm | Kết quả mong đợi |
|---|---|---|---|---|
| COMPAT-004 | Desktop lớn | 1920×1080 | Dashboard, bảng dữ liệu | Layout đầy đủ, không tràn/khoảng trống lớn |
| COMPAT-005 | Laptop phổ thông | 1366×768 | Form, modal, bảng | Vừa khít, không cắt nội dung, không scroll ngang ngoài ý muốn |

### 3.3 Chức năng nhạy trình duyệt (desktop)
| ID | Chức năng | Rủi ro | Kiểm |
|---|---|---|---|
| COMPAT-006 | Chấm công FaceID (getUserMedia) | Quyền camera + HTTPS khác nhau giữa Chrome/Firefox/Edge | Webcam hoạt động trên cả 3 trình duyệt desktop |
| COMPAT-007 | Upload file | Hộp thoại chọn file | Chọn & upload được PDF/JPG trên cả 3 |
| COMPAT-008 | Alpine.js interactivity | Dropdown/modal/toggle | Hoạt động đồng nhất trên cả 3 |

---

## §4. Kiểm Thử Hiệu Năng (Performance)

> **Mục tiêu chốt:** Load = **50 user đồng thời**, Stress = **200 user**. Chạy thật trên **local** (`runserver`/gunicorn local). Render free cold-start làm sai lệch số đo → đo trên local là chính, prod chỉ smoke.

| ID | Loại | Kịch bản | Mục tiêu | Đo | Tiêu chí đạt |
|---|---|---|---|---|---|
| PERF-001 | Load | 50 user đồng thời: login → dashboard → xem danh sách (leaves/attendance) | 50 concurrent | p95 response time, throughput, error rate | p95 < 2s, error < 1% |
| PERF-002 | Load | 50 user: nộp đơn nghỉ phép/OT đồng thời | 50 concurrent ghi DB | Thời gian ghi, deadlock | Không deadlock, p95 < 3s |
| PERF-003 | Stress | Tăng dần 50→200 user | 200 concurrent | Điểm gãy (breakpoint), hành vi khi quá tải | Xác định ngưỡng sập + phục hồi sau khi giảm tải |
| PERF-004 | Stress | Chấm công FaceID đồng thời (mock Face API để cô lập backend) | 50 concurrent | Latency backend (loại trừ Face API) | Backend không nghẽn select_for_update |
| PERF-005 | Network | Mạng yếu 3G (DevTools throttle) | 1 user, Slow 3G | Thời gian tải trang, hành vi FaceID | Trang dùng được, có loading state (liên kết UIX-008) |
| PERF-006 | Soak (tùy chọn) | 50 user chạy liên tục 30 phút | ổn định | Memory leak, kết nối DB | Không rò rỉ tài nguyên |

**Script:** `tests_perf/locustfile.py` (tạo ở giai đoạn code). Tham số: `--users 50 --spawn-rate 5` (load), `--users 200 --spawn-rate 10` (stress).

---

## §5. Kiểm Thử Bảo Mật (Security)

> [!IMPORTANT]
> Theo §0.2b: các case bảo mật (403, IDOR, CSRF, truy cập URL trái phép) → kết quả mong đợi = **chặn im lặng / redirect**, **KHÔNG** thông báo chi tiết cho end user (tránh lộ thông tin). Đây là ngoại lệ của nguyên tắc "phải có thông báo".

| ID | Hạng mục | Kịch bản | Kết quả mong đợi | Ưu tiên | Tự động hóa |
|---|---|---|---|---|---|
| SEC-001 | Authn — trang nội bộ chặn ẩn danh | GET các URL nội bộ khi chưa login | Redirect /login/ | 🔴 | **[BỔ SUNG]** (quét toàn URL) |
| SEC-002 | Authz — Employee không vào chức năng HR/Admin | Employee GET/POST endpoint HR (tạo hồ sơ, duyệt, quản lý user) | 403/redirect mọi endpoint | 🔴 | Mở rộng từ các `non_hr_access`/`non_admin_access` đã có |
| SEC-003 | Authz — RBAC đủ 5 role không bypass | Ma trận role × endpoint nhạy cảm | Đúng ma trận §4 walkthrough | 🔴 | **[BỔ SUNG]** (test ma trận đầy đủ) |
| SEC-004 | IDOR — rò rỉ qua URL | NV A sửa id trên URL xem hồ sơ/đơn/báo cáo NV B | Bị chặn (404/403) | 🔴 | **[BỔ SUNG]** |
| SEC-005 | Mã hóa mật khẩu | Đọc DB sau khi tạo user | Password là hash PBKDF2, không plain text | 🔴 | **[BỔ SUNG]** (assert `password.startswith('pbkdf2_')`) |
| SEC-006 | SQL Injection | Nhập payload `' OR 1=1 --` vào ô tìm kiếm/login | Django ORM tham số hóa → vô hại | 🔴 | **[BỔ SUNG]** |
| SEC-007 | XSS | Nhập `<script>alert(1)</script>` vào tiêu đề báo cáo/lý do | Template autoescape → render text, không chạy JS | 🔴 | **[BỔ SUNG]** |
| SEC-008 | CSRF | POST không kèm csrf token | 403 Forbidden | 🟡 | **[BỔ SUNG]** |
| SEC-009 | Upload file độc hại | Upload .exe/.php/.svg, file >5MB | Chặn theo định dạng + size 5MB | 🔴 | **[BỔ SUNG]** (liên kết FUNC-EP-017, FUNC-LEA-010) |
| SEC-010 | Session timeout 30 phút (QĐ_Session) | Idle >30 phút | Tự đăng xuất | 🟡 | ✅ Cấu hình xong `SESSION_COOKIE_AGE=1800` + `SESSION_SAVE_EVERY_REQUEST` (§6) |
| SEC-011 | Khóa sau 3 lần sai (QĐ_TK1) | Login sai 3 lần | Khóa tài khoản | 🔴 | ✅ `test_login.py::lockout_after_3_fails` (§6) |
| SEC-012 | OTP brute-force / hết hạn | Thử nhiều OTP sai, hết hạn 120s | Giới hạn thử + hết hạn đúng | 🟡 | Mở rộng test_forgot_password |
| SEC-013 | Lockout chấm công 3 fail/300s | Sai mặt 3 lần | Khóa 300s | 🔴 | **[BỔ SUNG]** (liên kết FUNC-ATT-012) |
| SEC-014 | Cấu hình deploy an toàn | `python manage.py check --deploy` (DEBUG=False) | Không cảnh báo nghiêm trọng; HSTS/SSL redirect bật | 🟡 | check --deploy trong CI |
| SEC-015 | Bí mật không lộ | Rà `SECRET_KEY`, API key, SMTP pass | Đọc từ env, không hardcode trong repo | 🔴 | `bandit` + rà tay |

---

## §6. Hạn Chế Hiện Tại & Hướng Cải Thiện

> Tổng hợp từ §7–§8 walkthrough. Mỗi mục: trạng thái hiện tại → ảnh hưởng test → cách khắc phục.

| Mã QĐ | Hạn chế | Ảnh hưởng | Hướng cải thiện / Trạng thái |
|---|---|---|---|
| QĐ_TK1 | ~~Chưa có code đếm `failed_login`~~ | FUNC-ACC-004, SEC-011 | ✅ **ĐÃ LÀM** — `accounts/services/auth/login_lockout_service.py` (cache) + override `AccountsLoginView`; 3 sai liên tiếp → `is_active=False`. Test: `test_login.py::lockout_after_3_fails` |
| QĐ_Session | ~~Chưa cấu hình `SESSION_COOKIE_AGE`~~ | SEC-010 | ✅ **ĐÃ LÀM** — `SESSION_COOKIE_AGE=1800` + `SESSION_SAVE_EVERY_REQUEST=True` trong settings (idle 30 phút → logout) |
| Upload | ~~Validate định dạng/size 5MB lặp & thiếu ở reports/rewards~~ | FUNC-EP-017, SEC-009 | ✅ **ĐÃ LÀM** — validator chung `common/file_validation.py` áp cho leaves/overtime/attendance/reports/ticket/rewards + view upload document. Test: `test_leaves.py::TestSharedUploadValidator` |
| QĐ_CanhBao | Batch cảnh báo HĐ chỉ chạy qua Task Scheduler **local**; Render free **không có cron** | FUNC-CON-008 không tự chạy trên prod | Render Cron Job (paid) / external scheduler gọi endpoint trigger / Celery beat + worker |
| Face API | Cold-start DeepFace trên HuggingFace Space gây timeout, sai số đo perf | PERF-004 phải mock; UIX-008 cần loading state | Tăng `FACE_API_TIMEOUT_SEC`, warm-up ping định kỳ, xử lý fallback 503 |
| Face upload (test) | ~~3 test FAIL sẵn từ trước~~ | Mâu thuẫn spec code-vs-test trong commit `ff9418a` | ✅ **ĐÃ FIX** — chốt nghiệp vụ: đăng ký lần đầu tự duyệt, chỉ CẬP NHẬT mặt đã có mới cần HR duyệt. Sửa 3 test khớp + thêm `test_att_face_02_first_enrollment_applies`. 136/136 pass |
| Responsive | Web chưa tối ưu mobile/tablet (scope hiện tại chỉ desktop) | §3 chỉ phủ desktop | Đợt sau: thêm responsive + ma trận mobile/iOS/Android |
| Cơ chế thông báo | Thông báo lỗi/thành công hiện chưa chuẩn hóa toàn hệ thống | Là đối tượng kiểm ở §0.2b/§2 | **Đợt SAU kiểm thử:** redesign cơ chế thông báo dựa trên lỗi phát hiện |
| Performance | Render free không phản ánh tải thật (cold-start, 1 instance) | PERF-* đo trên local | Đo local là chuẩn; ghi rõ giả định; nâng plan Render nếu cần số prod |

---

## §7. Ma Trận Truy Vết (Traceability) — Quy Định Nghiệp Vụ → Test Case

> Đảm bảo mọi quy định trong [walkthrough.md](walkthrough.md) §7 đều có test phủ.

| Mã QĐ | Nội dung | Test case phủ |
|---|---|---|
| QĐ_TK1 | Sai MK 3 lần → khóa | FUNC-ACC-004, SEC-011 ✅ (đã code + test) |
| QĐ_TK2 | HR/Admin mở khóa tài khoản | FUNC-ACC-019, FUNC-ACC-020 |
| QĐ_Tao_MSNV | HR nhập MSNV tay | FUNC-EP-001, FUNC-EP-003 |
| QĐ_Tao_Username | username=MSNV thường, pass `{MSNV}@2026` | FUNC-EP-001 |
| QĐ_PheDuyet_L1 | leader/manager của NV duyệt L1 | FUNC-LEA-007, FUNC-LEA-011, FUNC-OT-005 |
| QĐ_PheDuyet_L2 | HR xác nhận L2 (OT: HR tạo bỏ L2) | FUNC-LEA-007, FUNC-OT-008 |
| QĐ_CapNhat_DuLieu | Chỉ hiệu lực sau L2 | FUNC-LEA-007, FUNC-OT-005, FUNC-RW-004 |
| QĐ_CanhBao | 2 mốc 30/7 ngày | FUNC-CON-008 |
| QĐ_DieuChinh | HR sửa giờ công kỳ hiện tại | FUNC-ATT-017→025 |
| QĐ_LuuTruDanhGia | Submitted → không sửa | FUNC-PER-005 |
| QĐ_XacNhanBaoCao | Acknowledged → khóa sửa/xóa | FUNC-RI-007 |
| QĐ_DieuHuong | Ticket new → tự nhận (claim) | FUNC-RI-010 |
| QĐ_NghiViec | resigned → is_active=False | **[BỔ SUNG]** test |
| QĐ_Session | Idle 30 phút → logout | SEC-010 ✅ (đã cấu hình) |

---

## §8. Tổng Kết & Bước Tiếp Theo

- **Tổng test case:** ~90 functional + 12 UI/UX + 8 compatibility (desktop) + 6 performance + 15 security = **~131 case**.
- **Đã tự động hóa:** ~70 case (qua ~2.383 dòng test Django hiện có).
- **Cần bổ sung code:** các case `[BỔ SUNG]` (boundary, RBAC ma trận, IDOR, XSS/SQLi, lockout, OTP biên, perf Locust).
- **Phụ thuộc code mới:** QĐ_TK1, QĐ_Session (cần implement trước khi test PASS).

**Thứ tự ưu tiên khi viết code** (đã chốt): **Security + boundary trước** — SEC-004 IDOR, SEC-005 hash MK, SEC-006 SQLi, SEC-007 XSS, SEC-003 RBAC ma trận, và các boundary cao (OTP 120s, score 0-100, file 5MB, lockout, vượt quỹ phép). Sau đó tới perf Locust, rồi các case còn lại.

### Lộ trình giai đoạn
| Đợt | Nội dung | Trạng thái |
|---|---|---|
| **1 (hiện tại)** | Kiểm thử hệ thống chạy đúng đắn (10 app, 5 nhóm, desktop). Ghi nhận lỗi + chỗ thông báo chưa rõ. | ⏳ Đang plan |
| **2 (sau)** | Dựa trên kết quả đợt 1 → **chỉnh sửa/redesign cơ chế thông báo lỗi/thành công** cho end user (theo §0.2b). | 🔜 Chưa bắt đầu |
| **3 (tương lai)** | Mở rộng responsive mobile/tablet + ma trận tương thích đầy đủ. | 🔜 Out-of-scope hiện tại |

**Sau khi duyệt plan này → chuyển sang giai đoạn viết code test** (Locust + các case `[BỔ SUNG]`) theo `superpowers:writing-plans`.

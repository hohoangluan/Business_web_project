# 🔄 Sơ Đồ Luồng Dữ Liệu (Data Flow Diagram) — Hệ Thống HRMS

> **Hệ thống Quản lý Nhân sự (Human Resource Management System)**
> Môn học: SE104 – Nhập môn Công nghệ Phần mềm
>
> Mỗi chức năng gồm: **DFD** (mermaid) · **Từ điển dữ liệu** · **Thuật toán xử lý**.
> Logic trích từ code thật trong `business_web/` (services & views).

---

## Quy ước ký hiệu DFD

| Hình | Ý nghĩa |
|------|---------|
| `[Tác nhân]` (chữ nhật) | **External Entity** — người/hệ thống ngoài (Nhân viên, HR, Gmail SMTP, Remote Face API) |
| `((Process))` (tròn) | **Process** — bước xử lý, đánh số `n.0` |
| `[(Data Store)]` (trụ) | **Data Store** — bảng CSDL |
| `-->|dữ liệu|` | **Data Flow** — luồng dữ liệu, nhãn = nội dung |

> **Render:** Mermaid — hiển thị trực tiếp trên GitHub, VSCode (Markdown Preview), hoặc <https://mermaid.live>.

---

## 🌐 DFD Mức 0 — Sơ đồ ngữ cảnh (Context Diagram)

```mermaid
flowchart TB
    EMP[Nhân viên]
    LM[Leader / Manager]
    HR[Nhân sự HR]
    ADM[Quản trị viên]
    SMTP[Gmail SMTP]
    FACE[Remote Face API]

    SYS(((HRMS<br/>Hệ thống Quản lý Nhân sự)))

    EMP -->|đăng nhập, chấm công, đơn từ, báo cáo| SYS
    SYS -->|hồ sơ, lịch sử, trạng thái đơn| EMP

    LM -->|phê duyệt L1, đánh giá, phản hồi| SYS
    SYS -->|danh sách chờ duyệt, thống kê nhóm| LM

    HR -->|duyệt L2, hồ sơ, hợp đồng, cấu hình| SYS
    SYS -->|dữ liệu nhân sự, báo cáo tổng hợp| HR

    ADM -->|tạo tài khoản, phân quyền| SYS
    SYS -->|trạng thái hệ thống| ADM

    SYS -->|mã OTP, email tài khoản, cảnh báo HĐ| SMTP
    SYS -->|ảnh khuôn mặt base64| FACE
    FACE -->|employee_id, confidence| SYS
```

---

# 1. Đăng nhập hệ thống

```mermaid
flowchart LR
    U[Nhân viên]
    P1((1.0<br/>Xác thực<br/>đăng nhập))
    DSU[(User)]
    DSP[(UserProfile)]

    U -->|username, password| P1
    P1 -->|tra cứu hash mật khẩu| DSU
    DSU -->|password_hash, is_active| P1
    P1 -->|lấy role| DSP
    DSP -->|role| P1
    P1 -->|session_id + redirect theo role| U
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `username`, `password` | str |
| Tra cứu | `password_hash`, `is_active` | str, bool |
| Đầu ra | `session_id`, trang đích theo vai trò | cookie, URL |

**Thuật toán**
1. Nhận `username` + `password` từ form.
2. `authenticate()` — băm `password` và so với `password_hash` trong `User`.
3. Sai → trả lỗi "Sai tài khoản hoặc mật khẩu".
4. Đúng nhưng `is_active = False` → chặn, báo "Tài khoản bị khóa".
5. Hợp lệ → `login()` tạo session.
6. Đọc `UserProfile.role` → điều hướng trang chủ tương ứng (admin/hr/manager/leader/employee).

---

# 2. Quên mật khẩu qua OTP

```mermaid
flowchart LR
    U[Nhân viên]
    P21((2.1<br/>Sinh & gửi OTP))
    P22((2.2<br/>Xác thực OTP))
    P23((2.3<br/>Đổi mật khẩu))
    DSU[(User)]
    DSO[(OtpCode)]
    SMTP[Gmail SMTP]

    U -->|email| P21
    P21 -->|tìm user theo email| DSU
    P21 -->|xóa OTP cũ, tạo OTP mới| DSO
    P21 -->|mã 6 số| SMTP
    SMTP -->|email chứa OTP| U
    P21 -->|email che dấu| U

    U -->|OTP nhập| P22
    DSO -->|code, created_at| P22
    P22 -->|hợp lệ → xóa OTP| DSO
    P22 -->|cho phép đổi| P23
    U -->|mật khẩu mới| P23
    P23 -->|set_password + save| DSU
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào B1 | `email` | str |
| OtpCode | `code` (6 số), `created_at`, hạn `OTP_EXPIRY_SECONDS=120s` | str, datetime |
| Đầu vào B2 | `input_code` | str(6) |
| Đầu vào B3 | `new_password` | str |
| Đầu ra | email che dấu (`a***z@gmail.com`), mật khẩu mới đã lưu | str |

**Thuật toán** (`forgot_password_service.py`)
1. Nhận `email` → tìm `User`. Không có → báo lỗi (không lộ tồn tại).
2. `create_otp_for_user()`: **xóa toàn bộ OTP cũ** của user, sinh `generate_otp()` = 6 chữ số ngẫu nhiên, lưu `OtpCode`.
3. `send_otp_email()` qua Gmail SMTP; hiển thị `mask_email()` cho UI.
4. Người dùng nhập `input_code` → `verify_otp()`:
   - Không tồn tại OTP → "yêu cầu mã mới".
   - `is_expired()` (>120s) → **xóa record**, báo hết hạn.
   - `code != input_code` → báo sai.
   - Đúng & còn hạn → **xóa record** (one-time), trả hợp lệ.
5. `reset_user_password()`: `set_password(new_password)` + `save()`.

---

# 3. Tạo tài khoản & hồ sơ nhân viên mới (HR)

```mermaid
flowchart LR
    HR[HR]
    P31((3.1<br/>Validate &<br/>sinh username/pass))
    P32((3.2<br/>Tạo User + hồ sơ))
    P33((3.3<br/>Gửi email<br/>tài khoản))
    DSU[(User)]
    DSP[(UserProfile)]
    DSW[(EmployeeWorkInfo)]
    DSPI[(PersonalInfo)]
    SMTP[Gmail SMTP]

    HR -->|employee_id, full_name, email, department, position...| P31
    P31 -->|check trùng employee_id/username| DSP
    P31 -->|username, password tạm| P32
    P32 -->|create_user| DSU
    P32 -->|employee_id, full_name, role| DSP
    P32 -->|department, position, manager/leader| DSW
    P32 -->|thông tin cá nhân| DSPI
    P32 -->|username + mật khẩu| P33
    P33 -->|email tài khoản| SMTP
    SMTP -->|thông tin đăng nhập| HR
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `employee_id`, `full_name`, `email`, `department`, `position`, `manager_user`, `leader_user` | str/FK |
| Sinh ra | `username = employee_id.lower().replace(' ','')`, `password = "{employee_id}@2026"` | str |
| Đầu ra | email chứa username + mật khẩu tạm | email |

**Thuật toán** (`profile_views.py`, `register_service.py`)
1. Validate: `employee_id` không rỗng, **chưa tồn tại** trong `UserProfile`; `department` bắt buộc.
2. Sinh `username` từ `employee_id` (thường, bỏ khoảng trắng); chặn nếu `username` đã tồn tại.
3. Đặt mật khẩu tạm mặc định `"{employee_id}@2026"`.
4. `create_user(username, email, password)` → tạo `User`.
5. `ensure_account_profiles()` tạo `UserProfile` (gắn `employee_id`, `full_name`, role), `EmployeeWorkInfo`, `PersonalInfo`.
6. Gửi email chứa thông tin đăng nhập cho nhân viên mới.

---

# 4. Chấm công bằng FaceID (Check-in / Check-out)

```mermaid
flowchart LR
    U[Nhân viên]
    P41((4.1<br/>Nhận diện<br/>khuôn mặt))
    P42((4.2<br/>Quyết định<br/>hành động))
    P43((4.3<br/>Ghi giờ &<br/>phân loại status))
    FACE[Remote Face API]
    DSA[(AttendanceRecord)]
    DSC[(ContractInfo)]
    DSO[(OvertimeRequest)]

    U -->|ảnh webcam bytes| P41
    P41 -->|ảnh| FACE
    FACE -->|status, employee_id, confidence| P41
    P41 -->|user hợp lệ| P42
    DSA -->|record hôm nay| P42
    P42 -->|check_in / check_out / done| P43
    DSC -->|shift_start, shift_end| P43
    DSO -->|giờ OT approved| P43
    P43 -->|check_in_time/out_time + status| DSA
    P43 -->|kết quả chấm công| U
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `image_bytes` (ảnh webcam) | bytes |
| Face API trả | `status`, `employee_id`, `confidence` | json |
| Hợp đồng | `shift_start_time`, `shift_end_time` | time |
| Ghi | `check_in_time`, `check_out_time`, `status ∈ {on_time, late, early_leave, no_checkout, absent}` | time, str |

**Thuật toán** (`face_verification_service.py`, `attendance_logging_service.py`)
1. Chụp ảnh → `recognize_face_remote(image_bytes)`.
   - Lỗi `no_face` → "không thấy mặt"; lỗi khác → `service_down`.
2. `status != success` → `no_match`.
3. **Đối chiếu 1:1**: `matched_employee_id == str(user.id)`?
   - Khác → `wrong_person` (chặn — chống chấm hộ).
   - Trùng → `ok`.
4. `decide_next_action(record)`:
   - `check_in_time is None` → **check_in**;
   - `check_out_time is None` → **check_out**;
   - else → **done**.
5. Lấy ca làm từ `ContractInfo` (`get_shift_times`).
6. `classify_status()`:
   - vào > `shift_start + WORK_LATE_GRACE_MIN` → `late`, ngược lại `on_time`;
   - ra < `shift_end` (đã dời theo OT approved nếu có) → `early_leave`.
7. Lưu giờ + `status` vào `AttendanceRecord` (transaction).

---

# 5. Đăng ký / Cập nhật khuôn mặt + Duyệt (chống gian lận)

```mermaid
flowchart LR
    U[Nhân viên]
    HR[HR]
    P51((5.1<br/>Nộp ảnh<br/>khuôn mặt))
    P52((5.2<br/>HR duyệt /<br/>từ chối))
    FACE[Remote Face API]
    DSF[(EmployeeFace)]
    DSR[(FaceChangeRequest)]

    U -->|ảnh base64, content_type| P51
    P51 -->|tính sha256, kiểm tra đã có mặt?| DSF
    P51 -->|đường tin cậy → enroll ngay| FACE
    P51 -->|self-service → pending| DSR
    FACE -->|ok / no_face| P51
    P51 -->|EmployeeFace upsert| DSF

    HR -->|approve/reject + ghi chú| P52
    DSR -->|ảnh pending| P52
    P52 -->|enroll ảnh đã duyệt| FACE
    P52 -->|cập nhật EmployeeFace| DSF
    P52 -->|status approved/rejected| DSR
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `image_base64`, `content_type`, `ip_address` | str |
| Audit | `image_sha256`, `submitted_by`, `is_cross_user` | str, FK, bool |
| Trạng thái | `status ∈ {pending, approved, rejected}` | str |

**Thuật toán** (`face_change_service.py`, `face_service.py`)
1. Đọc ảnh → `base64`, `content_type`, `sha256(raw_bytes)`.
2. **Đường tin cậy** = người nộp là HR/Admin **HOẶC** chủ chưa có mặt (`not has_face`):
   - `apply_face_enrollment()` đẩy ảnh lên Remote API (`register_face_remote`) → upsert `EmployeeFace`.
   - Ghi `FaceChangeRequest(status=approved)` làm audit. Remote từ chối → `FaceApiError`, không ghi local.
3. **Self-service** (đã có mặt, không phải HR/Admin):
   - Xóa các `pending` cũ → tạo `FaceChangeRequest(pending)`. **Không** đổi enrollment đang dùng.
4. HR `approve_face_change()`: decode base64 → `apply_face_enrollment()` → cập nhật `EmployeeFace`, set `approved`.
5. HR `reject_face_change()`: set `rejected` + `hr_note`, enrollment giữ nguyên.

---

# 6. Yêu cầu & duyệt điều chỉnh giờ công

```mermaid
flowchart LR
    U[Nhân viên]
    HR[HR]
    P61((6.1<br/>Gửi yêu cầu<br/>điều chỉnh))
    P62((6.2<br/>HR duyệt /<br/>từ chối))
    DSADJ[(AttendanceAdjustmentRequest)]
    DSA[(AttendanceRecord)]

    U -->|reason, giờ khai báo, minh chứng| P61
    P61 -->|tạo request pending| DSADJ
    HR -->|approve/reject + note| P62
    DSADJ -->|claimed_check_in/out| P62
    P62 -->|cập nhật giờ + recompute status| DSA
    P62 -->|status approved/rejected| DSADJ
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `reason ∈ {forgot, technical, business_trip, other}`, `reason_detail`, `claimed_check_in_time`, `claimed_check_out_time`, `evidence` | str, time, file |
| Đầu ra | `record.check_in/out_time` mới, `record.status` tính lại | time, str |

**Thuật toán** (`adjustment_review_service.py`)
1. NV tạo `AttendanceAdjustmentRequest(status=pending)` gắn vào `AttendanceRecord` (1–1).
2. HR `approve_adjustment()` (transaction):
   - Nếu có `claimed_check_in_time` → ghi đè `record.check_in_time`; tương tự check_out.
   - `recompute_record_status(record)` tính lại status từ ca HĐ + OT.
   - Lưu record; set request `approved` + `reviewed_by/at` + `hr_note`.
3. HR `reject_adjustment()`: chỉ `recompute` lại status hiện có; set request `rejected`.
4. Chặn nếu request không còn `pending`.

---

# 7. Nghỉ phép — nộp đơn & duyệt 2 cấp

```mermaid
flowchart LR
    U[Nhân viên]
    LM[Leader / Manager]
    HR[HR]
    P71((7.1<br/>Nộp đơn +<br/>tính số ngày))
    P72((7.2<br/>Duyệt L1))
    P73((7.3<br/>Duyệt L2 + trừ quỹ))
    DSL[(LeaveRequest)]
    DSC[(ContractInfo)]

    U -->|leave_type, start/end, reason, minh chứng| P71
    P71 -->|days = end-start+1, status=pending| DSL
    LM -->|approve/reject| P72
    DSL -->|đơn pending của NV trực tiếp| P72
    P72 -->|leader_approved| DSL
    HR -->|approve/reject| P73
    DSL -->|đơn leader_approved| P73
    DSC -->|contract_annual_leave_days| P73
    P73 -->|approved| DSL
    P73 -->|quỹ phép còn lại| U
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `leave_type`, `start_date`, `end_date`, `reason`, `attachment` | str, date, file |
| Tính | `days = (end-start).days + 1` | decimal |
| Trạng thái | `pending → leader_approved → approved` / `rejected` | str |
| Quỹ phép | `total_allowed` (từ HĐ), `used_days` (Σ approved), `remaining = max(total-used,0)` | decimal |

**Thuật toán** (`leaves/services/__init__.py`)
1. `create_leave_request()`: tính `days`, set `pending`.
2. **L1** `approve_leave_request()`:
   - Chặn tự duyệt; approver phải là `leader_user`/`manager_user` của NV.
   - Nếu **người tạo có role HR** → nhảy thẳng `approved`.
   - Ngược lại → `leader_approved` (chờ HR).
3. **L2** (HR): `leader_approved → approved`. Chỉ role HR.
4. `reject_leave_request()`: từ chối ở cả 2 bước, ghi `rejected_reason`.
5. Quỹ phép `get_user_leave_stats()`: `used = Σ days (approved trong năm)`, `remaining = total_allowed - used`.
6. `bulk_approve_requests()`: duyệt hàng loạt theo quyền.

---

# 8. Tăng ca (OT) — nộp đơn & duyệt 2 cấp

```mermaid
flowchart LR
    U[Nhân viên]
    LM[Leader / Manager]
    HR[HR]
    P81((8.1<br/>Đăng ký OT))
    P82((8.2<br/>Duyệt L1))
    P83((8.3<br/>Duyệt L2))
    DSO[(OvertimeRequest)]

    U -->|date, start/end, hours, reason| P81
    P81 -->|status=pending| DSO
    LM -->|approve/reject| P82
    DSO -->|pending của NV trực tiếp| P82
    P82 -->|leader_approved hoặc approved nếu NV là HR| DSO
    HR -->|approve/reject| P83
    DSO -->|leader_approved| P83
    P83 -->|approved| DSO
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `overtime_date`, `start_time`, `end_time`, `hours`, `reason` | date, time, decimal |
| Trạng thái | `pending → leader_approved → approved` / `rejected` | str |
| Thống kê | `total_hours` (Σ approved/tháng), `total_pay = hours × 150 000` | decimal, int |

**Thuật toán** (`overtime/services/__init__.py`) — **giống nghỉ phép**
1. `create_overtime_request()` → `pending`.
2. **L1**: quản lý trực tiếp duyệt; **ngoại lệ**: người tạo là HR → thẳng `approved` (1 bước).
3. **L2**: HR duyệt `leader_approved → approved`.
4. Từ chối ở cả 2 bước (`rejected_reason`).
5. OT đã `approved` dời giờ tan kỳ vọng (dùng ở chức năng 4 — `get_approved_overtime_end`).
6. `bulk_approve_requests()` duyệt hàng loạt.

---

# 9. Đánh giá hiệu suất

```mermaid
flowchart LR
    LM[Leader / Manager]
    HR[HR]
    EMP[Nhân viên]
    P91((9.1<br/>Lập phiếu +<br/>auto xếp loại))
    P92((9.2<br/>Gửi → khóa))
    P93((9.3<br/>HR xác nhận))
    DSE[(Evaluation)]
    DSCAT[(EvaluationCategory)]

    LM -->|employee, category, score, content| P91
    DSCAT -->|loại đánh giá| P91
    P91 -->|rating A/B/C/D, status=draft| DSE
    LM -->|gửi| P92
    P92 -->|status=submitted khóa sửa| DSE
    HR -->|hr_note, xác nhận| P93
    DSE -->|phiếu submitted| P93
    P93 -->|status=acknowledged| DSE
    DSE -->|điểm, xếp loại| EMP
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `employee`, `reviewer`, `category`, `score (0–100)`, `content`, `evidence_reference` | FK, int, text |
| Tính | `rating ∈ {A,B,C,D}` từ `score` | str |
| Trạng thái | `draft → submitted → acknowledged` | str |

**Thuật toán** (`evaluation_model.py::save()`)
1. Leader/Manager lập phiếu `draft`: chọn NV, loại, nhập `score`, `content`.
2. `save()` **tự xếp loại**: `≥90→A`, `≥75→B`, `≥60→C`, `<60→D`.
3. Gửi → `status=submitted` → **khóa chỉnh sửa vĩnh viễn**.
4. HR thêm `hr_note`, xác nhận → `acknowledged` + `acknowledged_by/at`.
5. NV xem điểm + xếp loại.

---

# 10. Khen thưởng & Kỷ luật

```mermaid
flowchart LR
    PROP[Leader / Manager / HR]
    MGR[Manager]
    HR[HR]
    EMP[Nhân viên]
    P101((10.1<br/>Đề xuất<br/>thưởng/phạt))
    P102((10.2<br/>Duyệt L1))
    P103((10.3<br/>Duyệt L2))
    DSR[(RewardPenalty)]

    PROP -->|employee, type, amount, reason, minh chứng| P101
    P101 -->|status=pending| DSR
    MGR -->|duyệt L1 nếu Leader đề xuất| P102
    P102 -->|chuyển HR| DSR
    HR -->|duyệt/từ chối L2| P103
    P103 -->|approved/rejected| DSR
    DSR -->|quyết định| EMP
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `record_type ∈ {reward, penalty}`, `amount` (VND), `reason_title`, `reason_detail`, `evidence_file`, `application_date` | str, int, file, date |
| Trạng thái | `pending → approved` / `rejected` | str |

**Thuật toán**
1. Leader/Manager/HR lập phiếu `RewardPenalty(status=pending)`, gắn `proposer`.
2. **L1**: Manager duyệt nếu Leader đề xuất; Manager tự đề xuất → bỏ qua L1, chuyển thẳng HR.
3. **L2**: HR duyệt → `approved` (ban hành) hoặc `rejected`.
4. NV xem quyết định của mình.

---

# 11. Báo cáo công việc

```mermaid
flowchart LR
    AUTH[Nhân viên / Leader]
    MGR[Quản lý cấp trên]
    P111((11.1<br/>Gửi báo cáo))
    P112((11.2<br/>Xem & phản hồi))
    DSR[(Report)]

    AUTH -->|title, content, file| P111
    P111 -->|recipient theo phân cấp, status=submitted| DSR
    MGR -->|xem| P112
    DSR -->|báo cáo nhận được| P112
    P112 -->|is_viewed=True, viewed_at| DSR
    P112 -->|needs_update + manager_note| DSR
    P112 -->|acknowledged → khóa sửa/xóa| DSR
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `title`, `content`, `file_attachment`, `recipient` | str, file, FK |
| Trạng thái | `submitted → needs_update / acknowledged` | str |
| Khóa | `can_edit_or_delete = status != acknowledged` | bool |

**Thuật toán** (`report_model.py`)
1. Gửi báo cáo: Employee → Leader, Leader → Manager (`recipient` theo phân cấp), `status=submitted`.
2. Quản lý xem → `is_viewed=True`, ghi `viewed_at`.
3. `needs_update` + `manager_note`: yêu cầu NV cập nhật lại.
4. `acknowledged`: tiếp nhận → **khóa** sửa/xóa (`can_edit_or_delete=False`).

---

# 12. Ticket hỗ trợ / khiếu nại

```mermaid
flowchart LR
    U[Nhân viên]
    H[HR / Admin]
    P121((12.1<br/>Tạo ticket))
    P122((12.2<br/>Xử lý ticket))
    DST[(Ticket)]

    U -->|type, priority, title, content, minh chứng| P121
    P121 -->|status=new, assigned_to=null| DST
    H -->|tiếp nhận| P122
    DST -->|ticket new| P122
    P122 -->|assigned_to, status=processing| DST
    P122 -->|resolved / rejected| DST
    U -->|xác nhận| P122
    P122 -->|closed| DST
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Đầu vào | `ticket_type ∈ {support, complaint}`, `priority ∈ {low, medium, high}`, `title`, `content`, `evidence_file` | str, file |
| Trạng thái | `new → processing → resolved → closed` / `rejected` | str |
| Người xử lý | `assigned_to` | FK User |

**Thuật toán** (`ticket_model.py`, views)
1. NV tạo `Ticket(status=new, assigned_to=null)`.
2. Người xử lý (HR/Admin) tiếp nhận → gán `assigned_to=self`, `status=processing`.
3. Giải quyết → `resolved`; sai bộ phận → forward (đổi `assigned_to`); không hợp lệ → `rejected` + `rejection_reason`.
4. NV xác nhận → `closed`.

---

# 13. Hợp đồng — cảnh báo sắp hết hạn (batch) & gia hạn

```mermaid
flowchart LR
    CRON[Batch job / Cron]
    HR[HR]
    P131((13.1<br/>Quét HĐ<br/>sắp hết hạn))
    P132((13.2<br/>Gửi cảnh báo))
    P133((13.3<br/>Gia hạn HĐ))
    DSC[(ContractInfo)]
    DSW[(EmployeeWorkInfo)]
    SMTP[Gmail SMTP]

    CRON -->|trigger| P131
    DSC -->|is_active, contract_end_date| P131
    P131 -->|days_left, urgency| P132
    DSW -->|manager, leader| P132
    P132 -->|email cảnh báo| SMTP
    HR -->|HĐ mới| P133
    P133 -->|đóng HĐ cũ is_active=False, tạo HĐ mới| DSC
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Quét | `contract_end_date` (DD/MM/YYYY), `is_active` | str, bool |
| Tính | `days_left = end_date - today`, `urgency = near (≤7) / far (≤30)` | int, str |
| Người nhận | email NV + manager + leader + tất cả HR (unique) | list |

**Thuật toán** (`renewal_service.py`)
1. `get_expiring_contracts()`: lọc `ContractInfo(is_active=True, end_date ≠ '')`.
2. `parse_ddmmyyyy()` → `days_left`. Giữ nếu `0 ≤ days_left ≤ 30`.
3. Phân loại `urgency`: `near` nếu ≤7 ngày, `far` nếu ≤30. Sắp xếp tăng dần.
4. `get_recipients_for_contract()`: gộp email NV + manager_user + leader_user + **mọi HR**, loại trùng/rỗng.
5. Gửi cảnh báo qua Gmail SMTP tại mốc 30/15/7 ngày.
6. Gia hạn: tạo HĐ mới, đóng HĐ cũ `is_active=False`. HĐ quá hạn chưa gia hạn → tự `is_active=False`.

---

# 14. Thống kê tổng hợp

```mermaid
flowchart LR
    MGR[Manager]
    HR[HR / Admin]
    P141((14.1<br/>Tổng hợp<br/>dữ liệu))
    P142((14.2<br/>Xuất báo cáo))
    DSA[(AttendanceRecord)]
    DSL[(LeaveRequest)]
    DSO[(OvertimeRequest)]
    DSE[(Evaluation)]
    DSRW[(RewardPenalty)]

    DSA --> P141
    DSL --> P141
    DSO --> P141
    DSE --> P141
    DSRW --> P141
    MGR -->|phạm vi nhóm trực thuộc| P141
    HR -->|phạm vi toàn công ty| P141
    P141 -->|dashboard tổng hợp| MGR
    P141 -->|dashboard + dữ liệu| HR
    P141 --> P142
    P142 -->|file báo cáo| HR
```

**Từ điển dữ liệu**

| Luồng | Dữ liệu | Kiểu |
|-------|---------|------|
| Nguồn | chấm công, nghỉ phép, tăng ca, đánh giá, thưởng/phạt | aggregate |
| Phạm vi | Manager → nhân viên trực thuộc; HR/Admin → toàn công ty | filter |
| Đầu ra | dashboard số liệu, file xuất | view, file |

**Thuật toán** (`stats_reports` — **không có model riêng**)
1. App thống kê **chỉ đọc** dữ liệu từ các app khác qua các builder trong `services/`.
2. Manager: lọc theo `_get_direct_report_user_ids()` (nhân viên trực thuộc).
3. HR/Admin: tổng hợp toàn công ty.
4. Tính `Sum/Count/aggregate` theo kỳ (tháng/năm) → dashboard.
5. Xuất file báo cáo (HR).

---

## Tổng hợp Data Store

| Data Store | Bảng (model) | Chức năng dùng |
|------------|--------------|----------------|
| User / UserProfile | `auth.User`, `UserProfile` | 1, 2, 3 |
| OtpCode | `OtpCode` | 2 |
| PersonalInfo / EmployeeWorkInfo | hồ sơ | 3, 7, 8, 13 |
| ContractInfo | `ContractInfo` | 4, 7, 13 |
| AttendanceRecord / AdjustmentRequest | chấm công | 4, 6 |
| EmployeeFace / FaceChangeRequest | khuôn mặt | 4, 5 |
| LeaveRequest | nghỉ phép | 7, 14 |
| OvertimeRequest | tăng ca | 4, 8, 14 |
| Evaluation / EvaluationCategory | đánh giá | 9, 14 |
| RewardPenalty | thưởng/phạt | 10, 14 |
| Report / Ticket | báo cáo, hỗ trợ | 11, 12 |

**External Entities:** Nhân viên · Leader/Manager · HR · Admin · **Gmail SMTP** (OTP, email tài khoản, cảnh báo HĐ) · **Remote Face API** (nhận diện & enroll khuôn mặt).

# Code Flow — Business Web Project

> **Cập nhật:** 2026-06-04 — verify lại 100% so với code thật (đã sửa các chỗ lệch ở mục 1, 3, 5, 6, 9, 12).

---

## 1. Luồng Đăng ký tài khoản (Register)

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant V as register_view
    participant S as create_manual_account
    participant P as ensure_account_profiles
    participant DB as Database

    U->>V: GET /register/
    alt Đã đăng nhập
        V-->>U: Redirect → /dashboard/
    end
    V-->>U: Render RegisterForm (employee_id, email, full_name, password)

    U->>V: POST /register/ (form data)
    V->>V: RegisterForm.is_valid()
    alt Form invalid
        V-->>U: Render form với lỗi
    else Form valid
        V->>S: create_manual_account(employee_id, password, full_name, email)
        Note over S,DB: @transaction.atomic
        S->>S: username = normalize_employee_username(employee_id)
        S->>S: validate_email(email) + validate_password(password)
        S->>DB: Check trùng username / email (iexact)
        alt Trùng hoặc password yếu
            S-->>V: raise ValidationError
            V-->>U: form.add_error(None, exc) → render lại
        else Hợp lệ
            S->>DB: User.objects.create_user(username, email, password)
            S->>P: ensure_account_profiles(user, employee_id, full_name, email)
            P->>DB: UserProfile (employee_id, full_name, email, role=None)
            P->>DB: PersonalInfo / WorkInfo / ContractInfo / EmergencyContact / EducationInfo (rỗng)
            S-->>V: user
            V->>V: login(request, user)
            V-->>U: Redirect → /dashboard/ + message thành công
        end
    end
```

**Chi tiết từ code:**
- View gọi `create_manual_account` (KHÔNG phải `create_automatic_account` — hàm đó raise `NotImplementedError`).
- `normalize_employee_username`: `strip().lower().replace(" ", "")` → username.
- Transaction atomic: lỗi tạo profile → rollback cả User.
- Đăng ký xong **tự đăng nhập ngay** (`login()`) rồi redirect `/dashboard/` — không quay về trang login.
- User mới `role=None` → chờ Admin/HR gán.

---

## 2. Luồng Đăng nhập (Login)

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant V as AccountsLoginView
    participant Lock as login_lockout_service (Cache)
    participant DB as Database

    U->>V: GET /login/
    V-->>U: Render LoginForm

    U->>V: POST /login/ (username, password)
    V->>DB: authenticate (Django LoginView)
    alt Đúng credentials (form_valid)
        V->>Lock: clear_failures(username)
        V->>DB: super().form_valid → tạo session
        V-->>U: Redirect → LOGIN_REDIRECT (/dashboard/)
    else Sai credentials (form_invalid)
        V->>DB: User.objects.filter(username__iexact).first()
        alt User tồn tại & is_active=False (đã khóa từ trước)
            V-->>U: Render form + LOCKED_MESSAGE (không đếm thêm)
        else
            V->>Lock: count = register_failure(username)
            alt reached_limit(count) (count >= LOGIN_LOCKOUT_MAX_FAILS)
                V->>DB: _lock_account → is_active=False
                V->>Lock: clear_failures(username)
                V-->>U: Render form + "Tài khoản đã bị khóa do sai N lần"
            else
                V-->>U: Render form + lỗi đăng nhập
            end
        end
    end
```

**Chi tiết từ code:**
- Counter lưu ở **cache** (`login_lockout:fails:<sha256(username)>`), không thêm model.
- `register_failure` dùng `cache.add` (init=1) rồi `cache.incr`; TTL = `LOGIN_LOCKOUT_WINDOW_SEC`.
- Chạm ngưỡng → `_lock_account` set `is_active=False` + `clear_failures` (HR/Admin mở khóa sau).
- Tài khoản đã khóa từ trước: báo `LOCKED_MESSAGE`, KHÔNG tăng counter.

---

## 3. Luồng Quên mật khẩu (Forgot Password + OTP)

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant V as forgot_password_view
    participant R as reset_password_after_otp_view
    participant S as forgot_password_service
    participant Email as Gmail SMTP
    participant DB as Database

    U->>V: GET /forgot-password/
    V-->>U: Render form (step=username)

    U->>V: POST step=username (username)
    V->>DB: User.objects.filter(username=username).first()
    alt Không nhập / không tìm thấy / chưa có email
        V-->>U: Render step=username + error tương ứng
    else User hợp lệ
        V->>S: create_otp_for_user(user)
        S->>DB: Xóa OtpCode cũ + Create OtpCode (code 6 số)
        S->>Email: send_otp_email(email, code)
        alt Gửi email OK
            V-->>U: Render step=code (masked_email)
        else Gửi lỗi
            V-->>U: Render step=username + error gửi mail
        end
    end

    opt step=resend ("Gửi lại mã")
        V->>S: create_otp_for_user + send_otp_email
        V-->>U: Render step=code
    end

    U->>V: POST step=code (verification_code)
    V->>S: verify_otp(user, code)
    S->>DB: OtpCode.objects.get(user)
    alt OTP đúng & chưa hết hạn (<=120s)
        S->>DB: Delete OtpCode (consume)
        V->>V: session["otp_verified_username"] = username
        V-->>U: Redirect → reset_password_after_otp
    else Sai / hết hạn (hết hạn → xóa record)
        V-->>U: Render step=code + error
    end

    U->>R: GET /reset-password/ (sau OTP)
    R->>R: Guard: session["otp_verified_username"] tồn tại?
    alt Không có session
        R-->>U: Redirect → forgot_password
    else Có
        R-->>U: Render ResetPasswordForm
        U->>R: POST (new_password1, new_password2)
        R->>DB: reset_user_password → user.set_password + save
        R->>R: del session["otp_verified_username"]
        R-->>U: Redirect → /login/
    end
```

**Chi tiết từ code:**
- Tìm tài khoản bằng **`username`** trực tiếp (không qua employee_id/UserProfile).
- 3 step trong cùng view: `username` → `code` (+ `resend`); bước đổi mật khẩu là **view riêng** `reset_password_after_otp_view`, vào được nhờ session key `otp_verified_username`.
- OTP hết hạn thật theo model: `OtpCode.OTP_EXPIRY_SECONDS = 120` (text email ghi "1 phút" là không khớp model nhưng hiệu lực thực = 120s).

---

## 4. Luồng Phê duyệt 2 bước (Leaves / Overtime)

Hai module leaves và overtime dùng chung pattern phê duyệt 2 bước dưới đây.
**rewards_discipline khác** — xem note cuối mục:

```mermaid
sequenceDiagram
    participant EMP as Employee
    participant LM as Leader/Manager
    participant HR as HR

    EMP->>EMP: Tạo đơn → status = pending

    Note over LM: Bước 1: Leader/Manager duyệt
    LM->>LM: Kiểm tra _is_direct_supervisor(approver, employee)
    alt Duyệt
        alt Employee có role HR
            LM->>EMP: status = approved (hoàn tất, bỏ bước 2)
        else Employee không phải HR
            LM->>HR: status = leader_approved (chờ HR)
        end
    else Từ chối
        LM->>EMP: status = rejected
    end

    Note over HR: Bước 2: HR duyệt cuối
    HR->>HR: Kiểm tra _is_hr_role(approver)
    alt Duyệt
        HR->>EMP: status = approved + tạo Notification
    else Từ chối
        HR->>EMP: status = rejected + tạo Notification
    end
```

**Quy tắc chung (từ code):**
- Không thể tự duyệt/từ chối đơn của chính mình.
- Leader/Manager chỉ duyệt nhân viên trực tiếp (qua `EmployeeWorkInfo.leader_user` hoặc `manager_user`).
- HR duyệt tất cả đơn `leader_approved` (trừ đơn của chính mình).
- Employee hủy được đơn chỉ khi `status = pending` (chưa ai duyệt).
- Bulk approve: duyệt tất cả đơn thuộc quyền hạn.

**Khác biệt rewards_discipline (phiếu khen thưởng/xử phạt — xem ST-REWARD):**
- Người lập (`proposer`) lập phiếu cho NV khác → proposer ≠ đối tượng phiếu.
- Trạng thái đầu theo **role người lập**: Leader → `pending` (cần Manager L1); Manager/HR → `leader_approved` (bỏ L1).
- L1 = **Manager** (`_is_l1_approver`), không phải supervisor trực tiếp.
- **Không** có "HR thì bỏ L2": HR lập vẫn dừng `leader_approved`, cần **HR khác** duyệt L2 (tự duyệt bị chặn).

---

## 5. Luồng Chấm công khuôn mặt

### 5.1 Đăng ký khuôn mặt

```mermaid
sequenceDiagram
    participant U as Employee (Browser)
    participant V as upload_image_base64_view
    participant CS as submit_face_change
    participant FS as apply_face_enrollment
    participant API as Remote Face API
    participant DB as Database

    U->>V: POST /attendance/upload-image/ (multipart field "image")
    V->>V: Validate file tồn tại + MIME (jpeg/png/gif/webp/bmp)
    V->>CS: submit_face_change(owner, submitted_by, image_file, ip)
    CS->>CS: Tinh sha256(bytes), kiem tra owner da co employee_face chua

    alt submitted_by là HR/Admin (trusted) HOẶC lần đầu (chưa có face)
        CS->>FS: apply_face_enrollment(owner, bytes)
        FS->>API: POST /register (employee_id=str(user.id), slot_id)
        API-->>FS: OK (lỗi → raise FaceApiError)
        FS->>DB: update_or_create EmployeeFace (chỉ slot_id, KHÔNG lưu ảnh)
        CS->>DB: FaceChangeRequest(status=APPROVED, auto-duyệt, không lưu ảnh)
        CS-->>V: ('applied', face)
        V-->>U: "Lưu ảnh thành công"
    else Self-service & đã có face → chờ HR duyệt
        CS->>DB: Xóa FaceChangeRequest PENDING cũ
        CS->>DB: Create FaceChangeRequest(status=PENDING, image lưu Cloudinary, sha256, ip)
        CS-->>V: ('pending', req)
        V-->>U: "Đã gửi yêu cầu cập nhật, chờ HR duyệt"
    end
```

**Chi tiết từ code:**
- Ảnh gửi dạng **multipart/form-data** (field `image`), KHÔNG phải base64.
- `EmployeeFace` chỉ lưu `slot_id` (đánh dấu đã enroll); nhận diện chạy remote (FAISS), ảnh KHÔNG lưu local.
- `apply_face_enrollment` là điểm DUY NHẤT khiến một khuôn mặt thành enrollment có hiệu lực; remote từ chối → `FaceApiError`, không ghi row.

### 5.2 Nhận diện + Chấm công

```mermaid
sequenceDiagram
    participant U as Employee (Browser)
    participant V as face_check_view
    participant Lock as face_lockout_service
    participant FV as verify_face_for_user
    participant API as Remote Face API
    participant AL as attendance_logging_service
    participant CS as contracts.get_shift_times
    participant DB as Database

    U->>V: POST /attendance/check/ (multipart "image")
    Note over V: request_time = localtime() (chốt ngay đầu)
    V->>Lock: is_locked(user)
    alt Đang khóa
        V-->>U: 423 {locked, retry_after}
    end
    V->>V: _extract_image_bytes (no_image / too_large → 400)

    V->>FV: verify_face_for_user(user, bytes)
    FV->>API: recognize_face_remote(bytes)
    API-->>FV: {status, employee_id, confidence}
    Note over FV: match khi str(employee_id) == str(user.id)

    alt result.success == False
        alt reason=wrong_person
            V->>Lock: register_failure(user)
            V-->>U: 403 {wrong_person, fails_left}
        else reason=no_match
            V-->>U: 401
        else reason=no_face
            V-->>U: 400
        else reason=service_down
            V-->>U: 503
        end
    else Thành công
        Note over V,DB: transaction.atomic + select_for_update
        V->>DB: get_or_create AttendanceRecord(user, localdate())
        V->>AL: decide_next_action(record)
        alt action=check_in
            AL->>CS: get_shift_times(user)
            CS-->>AL: (shift_start, shift_end) — HĐ active override WorkScheduleConfig
            AL->>DB: set check_in_time + classify_status (on_time/late)
        else action=check_out
            AL->>CS: get_shift_times + effective_shift_end (cộng OT approved)
            AL->>DB: set check_out_time + classify_status (early_leave nếu ra sớm)
        else action=done
            Note over AL: no-op (đã đủ vào/ra)
        end
        V->>Lock: clear_failures(user)
        V-->>U: 200 {success, action, confidence, time, status}
    end
```

**Tính status (`classify_status`, từ code):**
- `late`: `check_in_time > shift_start + grace_minutes` (grace từ `WorkScheduleConfig`).
- `early_leave`: `check_out_time < shift_end` (shift_end đã dời theo OT approved qua `effective_shift_end`).
- ngược lại → `on_time`.
- `absent` / `no_checkout`: tính ở `recompute_record_status` / job đóng record, KHÔNG ở luồng check trực tiếp.

---

## 6. Luồng Hợp đồng — Versioning

```mermaid
sequenceDiagram
    participant HR as HR/Manager
    participant V as hr_adjust_contract_view
    participant S as adjust_contract
    participant DB as Database

    HR->>V: GET /contract/hr/adjust/<user_id>/
    Note over V: @user_passes_test(can_manage_work_info)
    alt request.user là Admin
        V-->>HR: Chặn ("Admin không có quyền") → redirect user_list
    end
    V->>DB: ensure_profile + ensure_contract_info(target_user)
    V-->>HR: Render ContractAdjustForm (initial = HĐ hiện tại)

    HR->>V: POST (modified fields)
    V->>V: ContractAdjustForm.is_valid()
    alt valid
        V->>S: adjust_contract(target_user, cleaned_data)
        Note over S,DB: @transaction.atomic
        S->>DB: old = ensure_contract_info(user)
        S->>S: new_values = {f: getattr(old,f) for f in CONTRACT_VERSION_FIELDS}
        S->>S: Ghi đè các field có trong data
        S->>DB: old.is_active = False (save)
        S->>DB: ContractInfo.create(user, is_active=True, **new_values)
        S-->>V: HĐ mới
        V-->>HR: Redirect → contract_history + message
    else invalid
        V-->>HR: Render lại form với lỗi
    end
```

**CONTRACT_VERSION_FIELDS** (copy-forward khi tạo phiên bản mới):
- contract_number, contract_type, contract_signed_date, contract_start_date, contract_end_date
- contract_annual_leave_days, contract_standard_shift, shift_start_time, shift_end_time
- contract_attachment_reference

### 6.1 Xem lịch sử hợp đồng

```mermaid
sequenceDiagram
    participant U as User
    participant V as contract_history_view
    participant DB as Database

    U->>V: GET /contract/history/<user_id>/
    alt request.user là Admin
        V-->>U: Chặn → redirect dashboard
    else
        V->>DB: get_object_or_404(User, pk=user_id)
        alt can_manage_work_info(user) HOẶC user.id == target.id
            V->>DB: get_contract_history → contracts.order_by('-created_at','-id')
            V-->>U: Render lịch sử (mọi phiên bản: active + archived)
        else
            V-->>U: "Không có quyền" → redirect dashboard
        end
    end
```

**Quyền xem (từ code):** HR/quản lý (`can_manage_work_info`) xem mọi người; nhân viên chỉ xem của chính mình; Admin bị chặn.

---

## 7. Luồng Báo cáo (Report Workflow)

```mermaid
stateDiagram-v2
    [*] --> submitted : Employee tạo báo cáo
    submitted --> needs_update : Manager "Yêu cầu cập nhật"
    submitted --> acknowledged : Manager "Tiếp nhận"
    needs_update --> submitted : Employee sửa và gửi lại
    acknowledged --> [*] : Khóa chỉnh sửa (can_edit_or_delete = False)
```

**Quy tắc:**
- `recipient` auto-set theo `EmployeeWorkInfo.manager_user` hoặc `leader_user`.
- Chỉ recipient mới được yêu cầu cập nhật hoặc tiếp nhận.
- Khi `status = acknowledged`: employee không thể sửa/xóa.

---

## 8. Luồng Ticket

```mermaid
stateDiagram-v2
    [*] --> new : Employee tạo ticket
    new --> processing : HR nhận xử lý
    processing --> resolved : HR giải quyết xong
    processing --> rejected : HR từ chối
    resolved --> closed : Auto/Manual đóng
    new --> rejected : HR từ chối ngay
```

---

## 9. Luồng Đánh giá nhân viên (Performance)

```mermaid
sequenceDiagram
    participant ML as Manager/Leader
    participant V as evaluations_view
    participant S as create_evaluation
    participant DB as Database
    participant HR as HR

    ML->>V: POST /evaluations/ (employee, category, score 0-100, content, date)
    V->>V: build_evaluation_form_state → validate (score 0..100, content, date, category)
    alt Hợp lệ
        V->>S: create_evaluation(reviewer, employee, data, file)
        S->>DB: Evaluation.create(status='submitted')
        Note over DB: save() tự tính rating: ≥90 A, ≥75 B, ≥60 C, else D
        S-->>V: eval_obj
        V-->>ML: preview + "Đã lưu và gửi lên HR"
    end

    HR->>V: GET /evaluations/hr-approval/
    V->>DB: get_pending_evaluations_for_hr → status='submitted'
    V-->>HR: Danh sách chờ xác nhận

    HR->>V: POST acknowledge (eval_id, note)
    V->>DB: acknowledge_evaluation → status='acknowledged', acknowledged_by/at, hr_note
    V-->>HR: Success
```

**Chi tiết từ code:** đánh giá tạo thẳng `status='submitted'` (KHÔNG có bước `draft`). `rating` auto-tính trong `Evaluation.save()` từ `score`.

---

## 10. Luồng Thống kê (Statistics)

```mermaid
flowchart TD
    A[User truy cập /statistics/] --> B{get_statistics_scope}
    B -->|HR/Admin| C[Scope: Toàn công ty]
    B -->|Manager| D[Scope: Phòng ban]
    B -->|Leader| E[Scope: Nhóm]
    B -->|Employee| F[Từ chối truy cập]

    C --> G[get_scope_users]
    D --> G
    E --> G

    G --> H[build_statistics_filters]
    H --> I[Áp dụng filter: department, manager, leader, employee]
    I --> J[build_statistics_records - từ attendance, leaves, overtime]
    I --> K[build_evaluation_records - từ performance]
    I --> L[build_rewards_penalties_records - từ rewards_discipline]
    J --> M[Lọc theo thời gian]
    K --> M
    L --> M
    M --> N[build_statistics_sections - cards + charts + tables]
    N --> O[Render template / Export Excel / Print]
```

---

## 11. Luồng Notification System

```mermaid
flowchart LR
    A[Service action] -->|create_notification| B[Notification record]
    B --> C[context_processor]
    C --> D[Every template render]
    D --> E[Bell icon: unread_count]
    E -->|Click| F["/notifications/ page"]
    F -->|Auto| G[Mark all as read]
    H[POST /notifications/mark-read/] -->|Manual| G
```

**Các sự kiện tạo notification:**
- Đơn nghỉ phép được duyệt/từ chối
- Đơn tăng ca được duyệt/từ chối
- (Mở rộng bởi các module khác)

---

## 12. Luồng Face Change Request (Anti-fraud)

```mermaid
sequenceDiagram
    participant EMP as Employee
    participant V as upload_image_base64_view
    participant DB as Database
    participant HR as HR (face_change_review)
    participant API as Remote Face API

    EMP->>V: POST /attendance/upload-image/ (new face image)
    Note over V: Employee đã có EmployeeFace
    V->>DB: Create FaceChangeRequest(status=pending, image, image_sha256, ip_address)
    V-->>EMP: "Yêu cầu đã gửi, chờ HR duyệt"

    HR->>HR: GET /attendance/face-changes/review/
    HR->>HR: Xem ảnh, kiểm tra is_cross_user

    alt approve_face_change
        HR->>API: apply_face_enrollment → POST /register (str(user.id), bytes)
        Note over HR: API từ chối → return (False, lý do), giữ pending
        HR->>DB: update_or_create EmployeeFace (slot_id)
        HR->>DB: status=APPROVED, reviewed_by/at, hr_note
        HR->>DB: req.image.delete() — purge ảnh (giảm PII)
    else reject_face_change
        HR->>DB: status=REJECTED, reviewed_by/at, hr_note
        Note over DB: GIỮ req.image làm minh chứng chống gian lận
    end
```

**Anti-fraud flags:**
- `is_cross_user` (property): True nếu `submitted_by_id != user_id` (người upload khác chủ khuôn mặt).
- `image_sha256`: Hash ảnh để phát hiện đảo ảnh.
- `ip_address`: Ghi nhận IP gửi yêu cầu.
- Approve xong **purge ảnh** (đã enroll remote); Reject **giữ ảnh** làm bằng chứng.

---

## 13. Luồng Cảnh báo hợp đồng sắp hết hạn

```mermaid
flowchart TD
    A[HR truy cập /contract/hr/expiring/] --> B[get_expiring_contracts]
    B --> C{Lọc HĐ active có end_date}
    C --> D[Parse DD/MM/YYYY → date]
    D --> E{"0 ≤ days_left ≤ 30?"}
    E -->|Yes| F[Thêm vào danh sách]
    F --> G{"days_left ≤ 7?"}
    G -->|Yes| H["urgency = 'near'"]
    G -->|No| I["urgency = 'far'"]
    H --> J[Sắp xếp theo days_left tăng dần]
    I --> J
    J --> K[Render danh sách cho HR]

    K --> L{HR gửi nhắc nhở}
    L -->|1 người| M[get_recipients_for_contract]
    L -->|Tất cả| N[Loop: send_renewal_reminder_email]
    M --> O[Email: nhân viên + manager + leader + tất cả HR]
```

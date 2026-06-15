# Test Plan — Business Web Project

> **Cập nhật:** 2026-06-03 — dựa 100% trên test code hiện có trong project.

---

## 1. Tổng quan

| Metric | Giá trị |
|---|---|
| **Framework** | Django TestCase (unittest) |
| **Database** | In-memory SQLite |
| **Tổng test files** | 40 files |
| **Tổng test cases** | 229 |
| **Coverage apps** | 10/10 apps |
| **Loại test** | Unit tests, Integration tests (view + service + DB), Security tests |

---

## 2. Cấu trúc test

```
business_web/
├── accounts/tests/
│   ├── test_admin_access.py          # 8 tests - Admin RBAC, deny_admin
│   ├── test_admin_management.py      # 7 tests - CRUD user, khóa/mở, reset
│   ├── test_bo_sung.py               # 8 tests - CSRF, OTP boundary, RBAC matrix, session
│   ├── test_forgot_password.py       # 4 tests - OTP flow
│   ├── test_login.py                 # 7 tests - Auth, lockout
│   ├── test_notifications.py         # 5 tests - Notification CRUD + context processor
│   ├── test_rbac_approval.py         # 1 test  - Employee blocked from approval
│   ├── test_register.py              # 6 tests - Registration + validation
│   ├── test_role_permission.py       # 4 tests - Role/permission assignment
│   ├── test_security.py              # 6 tests - IDOR, XSS, SQLi, password hash
│   └── test_work_schedule_settings.py # 3 tests - WorkScheduleConfig
├── attendance/tests/
│   ├── test_adjustment.py            # Attendance adjustment requests
│   ├── test_attendance_view.py       # Attendance page rendering
│   ├── test_face_check.py            # Face recognition check-in/out
│   ├── test_face_lockout.py          # Face lockout mechanism
│   ├── test_face_upload.py           # Face registration/update
│   └── test_work_schedule.py         # WorkScheduleConfig singleton
├── contracts/tests/
│   ├── test_contracts.py             # Contract CRUD
│   ├── test_contract_versioning.py   # Contract versioning (archive + new)
│   ├── test_date_order.py            # Date validation rules
│   ├── test_renewal_thresholds.py    # Expiring contracts logic
│   └── test_shift_time_order.py      # Shift time validation
├── employee_profiles/tests/
│   ├── test_create_validation.py     # Profile creation validation
│   ├── test_edit_work_info.py        # Work info editing
│   ├── test_hr_assign_role.py        # HR role assignment
│   ├── test_hr_create_profile.py     # HR profile creation
│   ├── test_profile_view.py          # Profile viewing/editing
│   └── test_upload_document.py       # Document upload
├── leaves/tests/
│   ├── test_leaves.py                # Full leave workflow
│   └── test_leave_l1.py              # L1 approval specifics
├── overtime/tests/
│   ├── test_overtime.py              # Full overtime workflow
│   └── test_ot_hr_skip_l2.py         # HR skip L2
├── performance/tests/
│   ├── test_performance.py           # Evaluation CRUD
│   ├── test_eval_lock.py             # Immutability after acknowledge
│   └── test_self_evaluation_policy.py # Employee blocked
├── rewards_discipline/tests/
│   ├── test_rewards_discipline.py    # Full reward/penalty workflow
│   ├── test_amount_boundary.py       # Amount validation
│   └── test_rewards_scope.py         # Scope visibility
├── reports_interactions/tests/
│   └── test_reports_interactions.py   # Reports + Tickets full workflow
├── stats_reports/tests/
│   ├── test_stats_reports.py         # Statistics views + export
│   └── test_stats_accuracy.py        # Data accuracy verification
└── tests_perf/
    ├── locustfile.py                 # General load testing
    ├── locustfile_face.py            # Face API load testing
    └── fake_face_api.py              # Mock Face API server
```

---

## 3. Test Plan chi tiết theo Module

### 3.1 accounts — Xác thực & Phân quyền

#### TP-ACC-LOGIN: Đăng nhập
| Test ID | Mô tả | Input | Expected Output | Priority |
|---|---|---|---|---|
| ACC-LOGIN-01 | Đăng nhập đúng credentials | username + đúng password | Redirect → /dashboard/, session chứa user_id | Critical |
| ACC-LOGIN-02 | Sai password | username + sai password | Hiển thị thông báo tiếng Việt, không redirect | Critical |
| ACC-LOGIN-02b | Username không tồn tại | unknown username | Thông báo trung lập (không leak info) | High |
| ACC-LOGIN-03 | TK bị khóa (is_active=False) | Đúng creds, account inactive | Hiển thị "Tài khoản đã bị khóa" | Critical |
| ACC-LOGIN-04 | Kiểm tra session | Đăng nhập thành công | Session._auth_user_id chứa đúng user.pk | High |
| ACC-LOGIN-05 | Lockout sau 3 lần sai (QĐ_TK1) | 3 lần sai password liên tiếp | user.is_active = False, hiển thị locked | Critical |
| ACC-LOGIN-06 | Đăng nhập đúng reset counter | 2 lần sai → 1 lần đúng → 2 lần sai | Không bị khóa (counter reset) | High |

#### TP-ACC-REG: Đăng ký
| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| ACC-REG-01,02,03,04 | Đăng ký hợp lệ | Tạo User + UserProfile + EmployeeWorkInfo, redirect /login/ | Critical |
| ACC-REG-05 | Employee_id trùng | Form error, không tạo user | High |
| ACC-REG-06 | Email trùng | Form error | High |
| ACC-REG-07 | Mật khẩu yếu | Django password validators reject | High |
| ACC-REG-08 | Transaction rollback | Nếu tạo profile lỗi → không tạo User | Critical |
| ACC-REG-09 | Đã đăng nhập | Redirect → dashboard | Low |

#### TP-ACC-FORGOT: Quên mật khẩu
| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| ACC-FORGOT-01,02 | Yêu cầu OTP | Tạo OtpCode, gửi email (mock) | Critical |
| ACC-FORGOT-03 | OTP đúng | Cho phép đặt mật khẩu mới | Critical |
| ACC-FORGOT-04 | OTP sai | Từ chối, giữ step=verify | High |
| ACC-FORGOT-05 | Reset password | Password thay đổi, redirect /login/ | Critical |
| FUNC-ACC-006 | Username không tồn tại | Báo lỗi, không tạo OTP | High |
| OTP-BOUNDARY-01 | OTP hết hạn sau 120s | is_expired() = True sau 120s | High |
| OTP-BOUNDARY-02 | OTP hợp lệ trước 120s | is_expired() = False ở 119s | Medium |
| ACC-OTP-03 | OTP sai mã | Từ chối, giữ step=verify | High |

#### TP-ACC-ADMIN: Quản lý User
| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| ACC-ADMIN-01 | Admin xem user list | HTTP 200, hiển thị users | High |
| ACC-ADMIN-02 | Non-Admin xem user list | Redirect/forbidden | High |
| ACC-ADMIN-03 | Admin xóa user khác | User bị xóa | High |
| ACC-ADMIN-04 | Admin xóa chính mình | Từ chối | Critical |
| ACC-ADMIN-05,06 | Khóa/mở tài khoản | Toggle is_active | High |
| ACC-ADMIN-07 | Admin khóa chính mình | Từ chối | Critical |
| ACC-ADMIN-08 | Reset password | Password đổi về DEFAULT_RESET_PASSWORD | High |

#### TP-ACC-ROLE: Gán vai trò & Quyền
| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| ACC-ROLE-01 | Admin gán role | UserProfile.role cập nhật | High |
| ACC-ROLE-03 | Admin gỡ role | UserProfile.role = None | Medium |
| ACC-ROLE-04 | Admin gán custom permission | UserProfile.permissions M2M cập nhật | Medium |
| ACC-ROLE-05 | Non-Admin gán role | Bị chặn (redirect) | High |

#### TP-SEC: Bảo mật
| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| SEC-001 | Anonymous → protected pages | Redirect → /login/ | Critical |
| SEC-004-IDOR-01 | Hủy đơn nghỉ người khác qua URL | Không hủy được | Critical |
| SEC-004-IDOR-02 | Xem báo cáo người khác | 403/redirect | Critical |
| SEC-005 | Password hashing | DB không lưu plaintext | Critical |
| SEC-006 | SQL injection payload | Không inject được | Critical |
| SEC-007 | XSS content escaped | Script tag bị escape | Critical |
| SEC-008 | Session settings đúng cấu hình | Cookie age/httponly/samesite đúng | Medium |
| CSRF | POST không CSRF token | HTTP 403 Forbidden | Critical |

#### TP-ACC-RBAC: Phân quyền RBAC (Admin/HR/Employee)
| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| ACC-RBAC-01 | Admin bị chặn khỏi business views | Redirect/forbidden | High |
| ACC-RBAC-02 | Admin tạo account reject mismatch/weak password | Form error | High |
| ACC-RBAC-03 | Admin tạo account chỉ username+password | Tạo account thành công | High |
| ACC-RBAC-04 | HR xem được profile nhân viên | HTTP 200 | High |
| ACC-RBAC-05 | HR xem được Khen thưởng & Xử phạt | HTTP 200 | High |
| ACC-RBAC-06 | is_admin property đúng logic | True/False đúng role | Medium |
| ACC-RBAC-07 | Non-admin không tạo được account | Bị chặn | High |
| ACC-RBAC-08 | Superuser mô phỏng role | Role simulation hoạt động | Medium |
| ACC-RBAC-09 | Employee bị chặn khỏi HR/Admin endpoints | Redirect/forbidden | High |
| ACC-RBAC-10 | Employee không xóa được user | Bị chặn | High |
| ACC-RBAC-11 | Employee bị chặn khỏi approval pages | Redirect/forbidden | High |

#### TP-ACC-NOTIF: Thông báo
| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| ACC-NOTIF-01 | create_notification tạo bản ghi đúng user | Notification created | High |
| ACC-NOTIF-02 | POST mark-read đánh dấu tất cả đã đọc | is_read=True | High |
| ACC-NOTIF-03 | mark-read yêu cầu POST | GET bị từ chối | Medium |
| ACC-NOTIF-04 | Context processor inject notifications | Có trong template context | Medium |
| ACC-NOTIF-05 | Mở trang xem tất cả → đánh dấu đã đọc | Notifications marked read | Medium |

#### TP-ACC-WSCHED: Cấu hình lịch làm việc
| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| ACC-WSCHED-01 | Employee không đổi được work schedule | Bị chặn | High |
| ACC-WSCHED-02 | HR lưu work schedule thành công | Lưu thành công | High |
| ACC-WSCHED-03 | HR GET hiển thị giá trị hiện tại | Hiển thị đúng giá trị | Medium |

---

### 3.2 attendance — Chấm công

| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| ATT-VIEW | GET /attendance/ | HTTP 200, hiển thị trang | High |
| ATT-FACE-REG | Đăng ký khuôn mặt lần đầu | Tạo EmployeeFace, gọi remote API | Critical |
| ATT-FACE-UPDATE | Cập nhật khuôn mặt (đã có) | Tạo FaceChangeRequest(pending) | Critical |
| ATT-FACE-CHANGE | HR duyệt/từ chối face change request | Status → approved/rejected | High |
| ATT-FACE-CHECK | Nhận diện thành công | Ghi AttendanceRecord (check-in hoặc check-out) | Critical |
| ATT-FACE-FAIL | Nhận diện thất bại | Đếm fail, không ghi chấm công | High |
| ATT-LOCKOUT | 3 lần fail liên tiếp | Bị khóa 300 giây | High |
| ATT-ADJ-SUBMIT | Gửi yêu cầu điều chỉnh | Tạo AdjustmentRequest(pending) | High |
| ATT-ADJ-APPROVE | HR duyệt điều chỉnh | Status → approved, cập nhật record | High |
| ATT-ADJ-REJECT | HR từ chối điều chỉnh | Status → rejected | High |
| ATT-SCHEDULE | WorkScheduleConfig singleton | get_solo() tạo/trả pk=1 | Medium |

---

### 3.3 contracts — Hợp đồng

| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| CON-VIEW | Employee/HR xem HĐ | HTTP 200, hiển thị thông tin | High |
| CON-EDIT | HR chỉnh sửa HĐ | Cập nhật thành công | High |
| CON-STATUS | Tính status HĐ | có hiệu lực / hết hạn / sắp hiệu lực / không thời hạn | High |
| CON-VERSIONING | HR tạo phiên bản mới | Archive cũ (is_active=False), tạo mới (is_active=True), copy-forward | Critical |
| CON-DATE-ORDER-01 | Ngày bắt đầu < ngày ký | Validation error | High |
| CON-DATE-ORDER-02 | Ngày hết hạn < ngày bắt đầu | Validation error | High |
| CON-DATE-ORDER-03 | Ngày trống/sai format | Bỏ qua validation | Medium |
| CON-RENEWAL-01 | HĐ còn ≤ 30 ngày | Xuất hiện trong get_expiring_contracts | High |
| CON-RENEWAL-02 | HĐ còn ≤ 7 ngày | urgency = 'near' | High |
| CON-EXPIRE | HĐ quá hạn | expire_overdue_contracts → is_active=False | High |
| CON-RECIPIENTS | Thu thập email nhắc nhở | Bao gồm: nhân viên, manager, leader, tất cả HR | Medium |
| CON-SHIFT | Giờ kết thúc < giờ bắt đầu | Validation error | Medium |

---

### 3.4 employee_profiles — Hồ sơ

| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| PROF-VIEW | GET /profile/ | HTTP 200, hiển thị hồ sơ | High |
| PROF-EDIT | POST /profile/ | Cập nhật PersonalInfo | High |
| PROF-HR-CREATE | HR tạo hồ sơ mới | Tạo đầy đủ các bảng liên quan | Critical |
| PROF-CREATE-VALIDATION | Validation khi tạo hồ sơ | Field bắt buộc thiếu → error | High |
| PROF-HR-ROLE | HR gán role | UserProfile.role thay đổi | High |
| PROF-WORK-INFO | HR sửa work info | EmployeeWorkInfo cập nhật | High |
| PROF-DOC-UPLOAD | Upload tài liệu | Tạo EmployeeDocument | Medium |

---

### 3.5 leaves — Nghỉ phép

| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| LEA-CREATE | Tạo đơn hợp lệ | LeaveRequest(status=pending), days auto-tính | Critical |
| LEA-CANCEL | Hủy đơn pending | Đơn bị xóa | High |
| LEA-CANCEL-NON-PENDING | Hủy đơn không pending | Từ chối | High |
| LEA-L1-APPROVE | Manager duyệt bước 1 | Status → leader_approved | Critical |
| LEA-L2-APPROVE | HR duyệt bước 2 | Status → approved, tạo notification | Critical |
| LEA-REJECT | Từ chối ở bước 1 hoặc 2 | Status → rejected, tạo notification | High |
| LEA-SELF-APPROVE | Tự duyệt đơn mình | Từ chối | Critical |
| LEA-NON-SUPERVISOR | Không phải supervisor duyệt | Từ chối | High |
| LEA-HR-SKIP-L2 | Employee HR chỉ cần L1 | Status → approved ngay sau L1 | High |
| LEA-BULK | Duyệt hàng loạt | Tất cả đơn đủ quyền được duyệt | Medium |
| LEA-ATTACH | Đơn nghỉ có attachment | FileField lưu đúng | Medium |

---

### 3.6 overtime — Tăng ca

| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| OT-VIEW | GET /overtime/ | HTTP 200, form + danh sách | High |
| OT-CREATE | Tạo đơn hợp lệ | OvertimeRequest(status=pending) | Critical |
| OT-INVALID-TIME | end_time < start_time | Form validation error | High |
| OT-CANCEL | Hủy đơn pending | Đơn bị xóa | High |
| OT-APPROVAL | Luồng 2 bước Manager → HR | Status transitions đúng | Critical |
| OT-REJECT | Từ chối bước 1 | Status → rejected | High |
| OT-HR-SKIP | HR employee → L1 approve = done | Status → approved | High |
| OT-ATTACH | Đơn có attachment | FileField lưu đúng | Medium |

---

### 3.7 performance — Đánh giá

| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| EVAL-VIEW | GET /evaluations/ | HTTP 200, danh sách đánh giá | High |
| EVAL-CREATE | Manager tạo đánh giá | Evaluation created | Critical |
| EVAL-SCORE | Score → rating auto | ≥90→A, ≥75→B, ≥60→C, <60→D | High |
| EVAL-ACK | HR xác nhận | Status → acknowledged | High |
| EVAL-LOCK | Sau acknowledge | Không có edit endpoint | High |
| EVAL-SELF-POLICY | Employee xem evaluations | Bị redirect/chặn | High |
| EVAL-EXCLUDE-SELF | exclude_self_records | Loại bỏ record viewer là employee | Medium |

---

### 3.8 rewards_discipline — Khen thưởng & Xử phạt

| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| RW-MANAGER-PROPOSE | Manager lập phiếu | Bỏ L1, vào thẳng leader_approved | Critical |
| RW-LEADER-FULL-FLOW | Leader → Manager L1 → HR L2 | 3 bước hoàn tất → approved | Critical |
| RW-HR-L2 | HR duyệt/từ chối L2 | Status approved/rejected | High |
| RW-HR-NO-L1 | HR duyệt L1 (cấp 1) | Bị chặn (phải Manager) | High |
| RW-EMPLOYEE-BLOCK | Employee truy cập | Redirect → dashboard | High |
| RW-ACCESS | Manager & HR vào trang duyệt | HTTP 200 | Medium |
| RW-AMOUNT-NEGATIVE | Số tiền âm | Bị reject | Medium |
| RW-AMOUNT-ZERO | Số tiền = 0 | Hợp lệ | Medium |
| RW-SCOPE-HR | HR xem phiếu mọi NV | Được phép | High |
| RW-SCOPE-ADMIN | HR xem phiếu Admin | Bị chặn | High |

---

### 3.9 reports_interactions — Báo cáo & Ticket

| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| RPT-CREATE | Tạo báo cáo | Report(status=submitted) | High |
| RPT-EDIT | Sửa báo cáo | Nội dung thay đổi | High |
| RPT-DELETE | Xóa báo cáo | Bản ghi bị xóa | High |
| RPT-VIEWED | Manager xem báo cáo | is_viewed=True, viewed_at set | High |
| RPT-INBOX | Manager xem inbox | Hiển thị reports_received | High |
| RPT-STATUS-ACK | Manager tiếp nhận | Status → acknowledged, lock edit | Critical |
| RPT-STATUS-UPDATE | Manager yêu cầu cập nhật | Status → needs_update | High |
| RPT-EDIT-AFTER-ACK | Sửa sau acknowledged | Bị chặn | High |
| RPT-NON-RECIPIENT | Non-recipient request update | Bị từ chối | High |
| RPT-AUTHOR-RESUBMIT | Author sửa needs_update | Status reset → submitted | High |
| TKT-CREATE | Tạo ticket | Ticket(status=new) | High |
| TKT-PROCESS | HR nhận xử lý | Status → processing | High |
| TKT-RESOLVE | HR giải quyết | Status → resolved | High |
| TKT-REJECT | HR từ chối | Status → rejected | High |

---

### 3.10 stats_reports — Thống kê

| Test ID | Mô tả | Expected | Priority |
|---|---|---|---|
| STAT-MANAGER | Manager xem statistics | HTTP 200, dữ liệu phòng ban | High |
| STAT-EMPLOYEE | Employee xem statistics | Bị chặn/error message | High |
| STAT-EXPORT | Export Excel | HTTP 200, content-type xlsx | High |
| STAT-PRINT | Print view | HTTP 200 | Medium |
| STAT-ACCURACY | Dữ liệu tổng hợp khớp DB | Aggregates đúng | Critical |

---

## 4. Performance Tests (Locust)

| File | Mô tả |
|---|---|
| `tests_perf/locustfile.py` | Load test các endpoint chính (login, dashboard, leave, overtime, etc.) |
| `tests_perf/locustfile_face.py` | Load test chấm công khuôn mặt (upload + check) |
| `tests_perf/fake_face_api.py` | Mock Face API server cho test isolated |

**Chạy Locust:**
```bash
# Chạy load test chung
locust -f tests_perf/locustfile.py --host=http://localhost:8000

# Chạy load test face (cần fake API)
python tests_perf/fake_face_api.py &
locust -f tests_perf/locustfile_face.py --host=http://localhost:8000
```

---

## 5. Quy ước test

1. **Naming**: `test_{module}_{feature}_{scenario}` hoặc `test_{test_id}_{description}`
2. **Setup**: Mỗi TestCase class có `setUpTestData` hoặc `setUp` tạo user + profile + role
3. **Client**: Dùng `self.client` (Django test client) cho view tests
4. **Assertions**: `assertEqual`, `assertTrue`, `assertRedirects`, `assertContains`
5. **Mocking**: `unittest.mock.patch` cho external services (email, face API)
6. **Database**: In-memory SQLite, auto-rollback sau mỗi test

# Test Result — Business Web Project

> **Cập nhật:** 2026-06-03 — kết quả thực thi `python manage.py test --verbosity=2`.
> **Kết quả: 229/229 tests PASSED (OK) — thời gian: 222.678s**

---

## 1. Tổng kết

| Metric | Giá trị |
|---|---|
| **Tổng số test** | 229 |
| **Passed** | 229 |
| **Failed** | 0 |
| **Errors** | 0 |
| **Skipped** | 0 |
| **Thời gian** | 222.678 giây |
| **Database** | In-memory SQLite (`file:memorydb_default?mode=memory&cache=shared`) |
| **System checks** | No issues (0 silenced) |
| **Ngày chạy** | 2026-06-03 |

---

## 2. Kết quả chi tiết theo App

### 2.1 accounts (48 tests) ✅

> ID = Test ID trong [test_plan.md](test_plan.md). Tên method Python tương ứng nằm trong test_plan §5 quy ước naming.

#### test_admin_access.py (8 tests)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | Admin bị chặn khỏi business views | `ACC-RBAC-01` | ✅ OK |
| 2 | Admin tạo account reject mismatch/weak password | `ACC-RBAC-02` | ✅ OK |
| 3 | Admin tạo account chỉ cần username+password | `ACC-RBAC-03` | ✅ OK |
| 4 | HR xem được profile | `ACC-RBAC-04` | ✅ OK |
| 5 | HR xem được Khen thưởng & Xử phạt | `ACC-RBAC-05` | ✅ OK |
| 6 | is_admin property đúng logic | `ACC-RBAC-06` | ✅ OK |
| 7 | Non-admin không tạo được account | `ACC-RBAC-07` | ✅ OK |
| 8 | Superuser mô phỏng role | `ACC-RBAC-08` | ✅ OK |

#### test_admin_management.py (7 tests)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | Admin xem danh sách user | `ACC-ADMIN-01` | ✅ OK |
| 2 | Non-Admin truy cập /users/ bị chặn | `ACC-ADMIN-02` | ✅ OK |
| 3 | Admin xóa user khác | `ACC-ADMIN-03` | ✅ OK |
| 4 | Admin xóa chính mình bị từ chối | `ACC-ADMIN-04` | ✅ OK |
| 5 | Admin khóa/mở tài khoản | `ACC-ADMIN-05,06` | ✅ OK |
| 6 | Admin khóa chính mình bị từ chối | `ACC-ADMIN-07` | ✅ OK |
| 7 | Admin reset password | `ACC-ADMIN-08` | ✅ OK |

#### test_bo_sung.py (8 tests)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | POST không có CSRF bị forbidden | `CSRF` | ✅ OK |
| 2 | Username không tồn tại → lỗi, không tạo OTP | `FUNC-ACC-006` | ✅ OK |
| 3 | OTP hết hạn sau 120 giây | `OTP-BOUNDARY-01` | ✅ OK |
| 4 | OTP hợp lệ ngay trước khi hết hạn | `OTP-BOUNDARY-02` | ✅ OK |
| 5 | OTP sai mã | `ACC-OTP-03` | ✅ OK |
| 6 | Employee bị chặn khỏi HR/Admin endpoints | `ACC-RBAC-09` | ✅ OK |
| 7 | Employee không xóa được user | `ACC-RBAC-10` | ✅ OK |
| 8 | Session settings đúng cấu hình | `SEC-008` | ✅ OK |

#### test_forgot_password.py (4 tests)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | Yêu cầu OTP với employee_id hợp lệ | `ACC-FORGOT-01,02` | ✅ OK |
| 2 | Nhập OTP đúng → cho đặt mật khẩu mới | `ACC-FORGOT-03` | ✅ OK |
| 3 | Nhập OTP sai → từ chối | `ACC-FORGOT-04` | ✅ OK |
| 4 | Reset password thành công | `ACC-FORGOT-05` | ✅ OK |

#### test_login.py (7 tests)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | Đăng nhập đúng username/password | `ACC-LOGIN-01` | ✅ OK |
| 2 | Sai password → thông báo tiếng Việt | `ACC-LOGIN-02` | ✅ OK |
| 3 | Sai tài khoản → thông báo trung lập | `ACC-LOGIN-02b` | ✅ OK |
| 4 | TK đã khóa → báo bị khóa | `ACC-LOGIN-03` | ✅ OK |
| 5 | Session chứa user_id đúng | `ACC-LOGIN-04` | ✅ OK |
| 6 | Sai 3 lần → khóa tài khoản | `ACC-LOGIN-05` | ✅ OK |
| 7 | Đăng nhập đúng reset counter | `ACC-LOGIN-06` | ✅ OK |

#### test_notifications.py (5 tests)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | create_notification tạo bản ghi đúng user | `ACC-NOTIF-01` | ✅ OK |
| 2 | POST mark-read đánh dấu tất cả đã đọc | `ACC-NOTIF-02` | ✅ OK |
| 3 | mark-read yêu cầu POST | `ACC-NOTIF-03` | ✅ OK |
| 4 | Context processor inject notifications | `ACC-NOTIF-04` | ✅ OK |
| 5 | Mở trang xem tất cả → đánh dấu đã đọc | `ACC-NOTIF-05` | ✅ OK |

#### test_rbac_approval.py (1 test)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | Employee bị chặn khỏi approval pages | `ACC-RBAC-11` | ✅ OK |

#### test_register.py (6 tests)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | Đăng ký hợp lệ | `ACC-REG-01,02,03,04` | ✅ OK |
| 2 | Employee_id trùng | `ACC-REG-05` | ✅ OK |
| 3 | Email trùng | `ACC-REG-06` | ✅ OK |
| 4 | Mật khẩu yếu | `ACC-REG-07` | ✅ OK |
| 5 | Transaction rollback | `ACC-REG-08` | ✅ OK |
| 6 | Đã đăng nhập → redirect | `ACC-REG-09` | ✅ OK |

#### test_role_permission.py (4 tests)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | Admin gán role Manager | `ACC-ROLE-01` | ✅ OK |
| 2 | Admin gỡ role | `ACC-ROLE-03` | ✅ OK |
| 3 | Admin gán custom permission | `ACC-ROLE-04` | ✅ OK |
| 4 | Non-Admin truy cập assign role bị chặn | `ACC-ROLE-05` | ✅ OK |

#### test_security.py (6 tests)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | Anonymous truy cập protected pages → redirect | `SEC-001` | ✅ OK |
| 2 | IDOR không hủy được đơn nghỉ người khác | `SEC-004-IDOR-01` | ✅ OK |
| 3 | IDOR không xem được báo cáo người khác | `SEC-004-IDOR-02` | ✅ OK |
| 4 | XSS content bị escaped khi render | `SEC-007` | ✅ OK |
| 5 | Password được hash | `SEC-005` | ✅ OK |
| 6 | SQL injection payload vô hại | `SEC-006` | ✅ OK |

#### test_work_schedule_settings.py (3 tests)
| # | Test | ID | Kết quả |
|---|---|---|---|
| 1 | Employee không thay đổi được work schedule | `ACC-WSCHED-01` | ✅ OK |
| 2 | HR lưu work schedule thành công | `ACC-WSCHED-02` | ✅ OK |
| 3 | HR GET hiển thị giá trị hiện tại | `ACC-WSCHED-03` | ✅ OK |

---

### 2.2 attendance (37 tests) ✅

#### test_adjustment.py
| Test | ID | Kết quả |
|---|---|---|
| Nhân viên gửi yêu cầu điều chỉnh (reason choices, validation evidence) | `ATT-ADJ-SUBMIT` | ✅ OK |
| HR duyệt điều chỉnh → approved, cập nhật record | `ATT-ADJ-APPROVE` | ✅ OK |
| HR từ chối điều chỉnh → rejected | `ATT-ADJ-REJECT` | ✅ OK |

#### test_attendance_view.py
| Test | ID | Kết quả |
|---|---|---|
| GET /attendance/ hiển thị trang + lịch sử chấm công | `ATT-VIEW` | ✅ OK |

#### test_face_check.py
| Test | ID | Kết quả |
|---|---|---|
| Nhận diện thành công → ghi chấm công (check-in/check-out) | `ATT-FACE-CHECK` | ✅ OK |
| Nhận diện thất bại → đếm fail, không ghi | `ATT-FACE-FAIL` | ✅ OK |

#### test_face_lockout.py
| Test | ID | Kết quả |
|---|---|---|
| 3 lần fail → khóa tạm; hết thời gian → cho thử lại | `ATT-LOCKOUT` | ✅ OK |

#### test_face_upload.py
| Test | ID | Kết quả |
|---|---|---|
| Đăng ký khuôn mặt lần đầu | `ATT-FACE-REG` | ✅ OK |
| Cập nhật khuôn mặt → tạo FaceChangeRequest | `ATT-FACE-UPDATE` | ✅ OK |
| HR duyệt/từ chối face change request | `ATT-FACE-CHANGE` | ✅ OK |

#### test_work_schedule.py
| Test | ID | Kết quả |
|---|---|---|
| WorkScheduleConfig singleton, get_solo() tạo mặc định | `ATT-SCHEDULE` | ✅ OK |

---

### 2.3 contracts (18 tests) ✅

#### test_contracts.py
| Test | ID | Kết quả |
|---|---|---|
| HR/Employee xem hợp đồng | `CON-VIEW` | ✅ OK |
| HR chỉnh sửa hợp đồng | `CON-EDIT` | ✅ OK |
| Tính status: có hiệu lực / hết hạn / sắp hiệu lực / không thời hạn | `CON-STATUS` | ✅ OK |

#### test_contract_versioning.py
| Test | ID | Kết quả |
|---|---|---|
| Tạo phiên bản mới (archive cũ), copy-forward, is_active chỉ 1 bản True | `CON-VERSIONING` | ✅ OK |

#### test_date_order.py
| Test | ID | Kết quả |
|---|---|---|
| Ngày bắt đầu ≥ ngày ký | `CON-DATE-ORDER-01` | ✅ OK |
| Ngày hết hạn ≥ ngày bắt đầu | `CON-DATE-ORDER-02` | ✅ OK |
| Ngày trống/sai format → bỏ qua | `CON-DATE-ORDER-03` | ✅ OK |

#### test_renewal_thresholds.py
| Test | ID | Kết quả |
|---|---|---|
| get_expiring_contracts ngưỡng 30 ngày | `CON-RENEWAL-01` | ✅ OK |
| get_expiring_contracts ngưỡng 7 ngày (urgency near) | `CON-RENEWAL-02` | ✅ OK |
| expire_overdue_contracts đặt is_active=False | `CON-EXPIRE` | ✅ OK |
| get_recipients_for_contract thu thập email đúng | `CON-RECIPIENTS` | ✅ OK |

#### test_shift_time_order.py
| Test | ID | Kết quả |
|---|---|---|
| Giờ kết thúc ca ≥ giờ bắt đầu ca | `CON-SHIFT` | ✅ OK |

---

### 2.4 employee_profiles (21 tests) ✅

#### test_profile_view.py
| Test | ID | Kết quả |
|---|---|---|
| GET /profile/ hiển thị hồ sơ | `PROF-VIEW` | ✅ OK |
| POST /profile/ cập nhật PersonalInfo | `PROF-EDIT` | ✅ OK |

#### test_hr_create_profile.py
| Test | ID | Kết quả |
|---|---|---|
| HR tạo hồ sơ mới cho nhân viên | `PROF-HR-CREATE` | ✅ OK |

#### test_create_validation.py
| Test | ID | Kết quả |
|---|---|---|
| Validation field bắt buộc khi tạo hồ sơ | `PROF-CREATE-VALIDATION` | ✅ OK |

#### test_hr_assign_role.py
| Test | ID | Kết quả |
|---|---|---|
| HR gán role cho nhân viên; Non-HR bị chặn | `PROF-HR-ROLE` | ✅ OK |

#### test_edit_work_info.py
| Test | ID | Kết quả |
|---|---|---|
| HR chỉnh sửa EmployeeWorkInfo, gán manager_user/leader_user | `PROF-WORK-INFO` | ✅ OK |

#### test_upload_document.py
| Test | ID | Kết quả |
|---|---|---|
| Upload tài liệu minh chứng | `PROF-DOC-UPLOAD` | ✅ OK |

---

### 2.5 leaves (17 tests) ✅

#### test_leaves.py
| Test | ID | Kết quả |
|---|---|---|
| Tạo đơn hợp lệ, auto-tính days | `LEA-CREATE` | ✅ OK |
| Hủy đơn pending | `LEA-CANCEL` | ✅ OK |
| Hủy đơn không pending → từ chối | `LEA-CANCEL-NON-PENDING` | ✅ OK |
| Manager duyệt bước 1 → leader_approved | `LEA-L1-APPROVE` | ✅ OK |
| HR duyệt bước 2 → approved + notification | `LEA-L2-APPROVE` | ✅ OK |
| Từ chối ở bước 1 hoặc 2 | `LEA-REJECT` | ✅ OK |
| Tự duyệt đơn mình → từ chối | `LEA-SELF-APPROVE` | ✅ OK |
| Không phải supervisor → từ chối | `LEA-NON-SUPERVISOR` | ✅ OK |
| Bulk approve | `LEA-BULK` | ✅ OK |
| Attachment upload | `LEA-ATTACH` | ✅ OK |

#### test_leave_l1.py
| Test | ID | Kết quả |
|---|---|---|
| Leader duyệt bước 1 đúng; HR employee chỉ cần 1 bước | `LEA-HR-SKIP-L2` | ✅ OK |

---

### 2.6 overtime (14 tests) ✅

#### test_overtime.py
| Test | ID | Kết quả |
|---|---|---|
| GET /overtime/ hiển thị form + danh sách | `OT-VIEW` | ✅ OK |
| Tạo đơn tăng ca hợp lệ | `OT-CREATE` | ✅ OK |
| end_time < start_time → reject | `OT-INVALID-TIME` | ✅ OK |
| Hủy đơn pending | `OT-CANCEL` | ✅ OK |
| Luồng duyệt 2 bước Manager → HR | `OT-APPROVAL` | ✅ OK |
| Từ chối ngay từ bước 1 | `OT-REJECT` | ✅ OK |
| Attachment upload | `OT-ATTACH` | ✅ OK |

#### test_ot_hr_skip_l2.py
| Test | ID | Kết quả |
|---|---|---|
| HR employee chỉ cần bước 1 → approved | `OT-HR-SKIP` | ✅ OK |

---

### 2.7 performance (8 tests) ✅

#### test_performance.py
| Test | ID | Kết quả |
|---|---|---|
| GET /evaluations/ hiển thị danh sách | `EVAL-VIEW` | ✅ OK |
| Manager tạo đánh giá cho nhân viên | `EVAL-CREATE` | ✅ OK |
| Rating auto từ score (≥90→A, ≥75→B, ≥60→C, <60→D) | `EVAL-SCORE` | ✅ OK |
| HR xác nhận đánh giá | `EVAL-ACK` | ✅ OK |

#### test_eval_lock.py
| Test | ID | Kết quả |
|---|---|---|
| Acknowledge endpoint tồn tại, không có edit endpoint (immutable) | `EVAL-LOCK` | ✅ OK |

#### test_self_evaluation_policy.py
| Test | ID | Kết quả |
|---|---|---|
| Employee bị chặn khỏi trang đánh giá | `EVAL-SELF-POLICY` | ✅ OK |
| exclude_self_records loại record của viewer | `EVAL-EXCLUDE-SELF` | ✅ OK |

---

### 2.8 rewards_discipline (11 tests) ✅

#### test_rewards_discipline.py
| Test | ID | Kết quả |
|---|---|---|
| Manager lập phiếu → bỏ L1, vào thẳng leader_approved | `RW-MANAGER-PROPOSE` | ✅ OK |
| Leader lập → Manager L1 → HR L2 → approved (FUNC-RW-005) | `RW-LEADER-FULL-FLOW` | ✅ OK |
| HR duyệt/từ chối phiếu L2 | `RW-HR-L2` | ✅ OK |
| HR không duyệt được phiếu cấp 1 | `RW-HR-NO-L1` | ✅ OK |
| Employee không truy cập trang thưởng/phạt | `RW-EMPLOYEE-BLOCK` | ✅ OK |
| Manager và HR vào được trang duyệt | `RW-ACCESS` | ✅ OK |

#### test_amount_boundary.py
| Test | ID | Kết quả |
|---|---|---|
| Số tiền âm bị reject | `RW-AMOUNT-NEGATIVE` | ✅ OK |
| Số tiền = 0 hợp lệ | `RW-AMOUNT-ZERO` | ✅ OK |

#### test_rewards_scope.py
| Test | ID | Kết quả |
|---|---|---|
| HR xem được phiếu mọi nhân viên | `RW-SCOPE-HR` | ✅ OK |
| HR không xem được phiếu của Admin | `RW-SCOPE-ADMIN` | ✅ OK |

---

### 2.9 reports_interactions (14 tests) ✅

#### test_reports_interactions.py
| Test | ID | Kết quả |
|---|---|---|
| Tạo báo cáo (status=submitted) | `RPT-CREATE` | ✅ OK |
| Sửa báo cáo | `RPT-EDIT` | ✅ OK |
| Xóa báo cáo | `RPT-DELETE` | ✅ OK |
| Xem báo cáo → is_viewed=True | `RPT-VIEWED` | ✅ OK |
| Report inbox access (reports_received) | `RPT-INBOX` | ✅ OK |
| Recipient acknowledge → acknowledged, khóa edit | `RPT-STATUS-ACK` | ✅ OK |
| Recipient request update → needs_update | `RPT-STATUS-UPDATE` | ✅ OK |
| Sửa sau acknowledged → bị chặn | `RPT-EDIT-AFTER-ACK` | ✅ OK |
| Non-recipient request update → denied | `RPT-NON-RECIPIENT` | ✅ OK |
| Author sửa needs_update → reset về submitted | `RPT-AUTHOR-RESUBMIT` | ✅ OK |
| Tạo ticket (status=new) | `TKT-CREATE` | ✅ OK |
| HR nhận xử lý → processing | `TKT-PROCESS` | ✅ OK |
| HR giải quyết → resolved | `TKT-RESOLVE` | ✅ OK |
| HR từ chối → rejected | `TKT-REJECT` | ✅ OK |

---

### 2.10 stats_reports (4 tests) ✅

#### test_stats_reports.py
| Test | ID | Kết quả |
|---|---|---|
| Manager xem được statistics | `STAT-MANAGER` | ✅ OK |
| Employee bị chặn statistics | `STAT-EMPLOYEE` | ✅ OK |
| Export Excel thành công | `STAT-EXPORT` | ✅ OK |
| Print view thành công | `STAT-PRINT` | ✅ OK |

#### test_stats_accuracy.py
| Test | ID | Kết quả |
|---|---|---|
| Dữ liệu tổng hợp khớp với DB thật | `STAT-ACCURACY` | ✅ OK |

---

## 3. Lệnh chạy test

```bash
# Chạy toàn bộ test suite
python manage.py test --verbosity=2

# Chạy test 1 app
python manage.py test accounts --verbosity=2
python manage.py test attendance --verbosity=2

# Chạy 1 test class cụ thể
python manage.py test accounts.tests.test_login.TestLoginView --verbosity=2

# Chạy 1 test method cụ thể
python manage.py test accounts.tests.test_login.TestLoginView.test_acc_login_01_valid_credentials
```

---

## 4. Performance Tests (Locust)

Kết quả chạy Performance test trên local environment sử dụng `tests_perf/locustfile.py`. Kịch bản load bao gồm 50% `VisitorLoad` và 50% `EmployeeJourney`. Server được test là Gunicorn/Django test server nội bộ kết nối với SQLite.

### 4.1. Kịch bản 20 Concurrent Users (Thời gian: 10 giây)
- **Tổng số Requests**: 315
- **Failures**: 0 (0.00%)
- **Requests per Second (RPS)**: ~36.39 req/s
- **Average Response Time**: 52 ms
- **Max Response Time**: 918 ms
- **P50 Response Time**: 9 ms
- **P95 Response Time**: 260 ms

### 4.2. Kịch bản 50 Concurrent Users (Thời gian: 20 giây)
- **Tổng số Requests**: 1849
- **Failures**: 0 (0.00%)
- **Requests per Second (RPS)**: ~96.06 req/s
- **Average Response Time**: 26 ms
- **Max Response Time**: 1030 ms
- **P50 Response Time**: 6 ms
- **P95 Response Time**: 100 ms

*→ Hệ thống phản hồi cực tốt ở mức 50 người dùng đồng thời, RPS đạt mức ~96, không có lỗi (0% fail).*

### 4.3. Kịch bản 200 Concurrent Users (Thời gian: 20 giây)
- **Tổng số Requests**: 4660
- **Failures**: 72 (1.55%)
- **Requests per Second (RPS)**: ~239.87 req/s
- **Average Response Time**: 277 ms
- **Max Response Time**: 13350 ms
- **P50 Response Time**: 24 ms
- **P95 Response Time**: 730 ms

*→ Ở mức tải 200 người dùng, RPS đạt đỉnh ~240. Tuy nhiên hệ thống bắt đầu xuất hiện thắt cổ chai (bottleneck) tại database. Lỗi phát sinh (1.55% failures) chủ yếu là `500 Internal Server Error` do `OperationalError: database is locked` (đặc trưng của SQLite khi chịu tải ghi đồng thời cao) và timeout ở CSRF Token. Giải pháp cho production là sử dụng PostgreSQL đúng như cấu trúc deployment (Render Blueprint).*

**Chi tiết theo Endpoints (Trích xuất từ kịch bản 50 Users):**

| Type | Endpoint | Requests | Fails | Avg (ms) | Min (ms) | Max (ms) | P50 (ms) |
|---|---|---|---|---|---|---|---|
| POST | /login/ | 25 | 0.00% | 630 | 403 | 1030 | 630 |
| GET | /dashboard/ | 268 | 0.00% | 54 | 12 | 325 | 30 |
| GET | /leave/ | 139 | 0.00% | 70 | 17 | 667 | 42 |
| GET | /login/ | 1417 | 0.00% | 6 | 2 | 72 | 5 |

*Lưu ý: Thời gian `POST /login/` tốn kém nhất là hành vi thiết kế chủ ý do Django sử dụng PBKDF2 để hash mật khẩu nhằm chống Brute-force.*

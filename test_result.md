# 📊 Báo Cáo Kết Quả Kiểm Thử — HRMS

> Đối chiếu với [test_plan.md](test_plan.md). Ngày chạy: **02/06/2026** · Lệnh: `python manage.py test` (Django TestCase, SQLite in-memory, Face API & SMTP mock).
>
> **Kết quả tổng:** `Ran 136 tests — OK` → **136 PASS / 0 FAIL / 0 ERROR**.

## Quy ước trạng thái
| Ký hiệu | Nghĩa |
|---|---|
| ✅ PASS | Test tự động chạy & đạt |
| 🟡 PARTIAL | Có phủ một phần (logic đã có/đã cấu hình) nhưng chưa phủ hết biên/kịch bản trong plan |
| ⚪ NR | Chưa thực thi — thủ công (UI/UX, Compatibility), Locust (Performance), hoặc case `[BỔ SUNG]` chưa code |

---

## §A. Tổng Hợp Số Liệu

| Nhóm | Tổng case (plan) | ✅ PASS | 🟡 PARTIAL | ⚪ NR | Ghi chú |
|---|---|---|---|---|---|
| §1 Functional | 91 | 78 | 1 | 12 | Auto qua Django TestCase |
| §2 UI/UX | 12 | 0 | 0 | 12 | Thủ công — chưa thực thi |
| §3 Compatibility (desktop) | 8 | 0 | 0 | 8 | Thủ công đa trình duyệt — chưa thực thi |
| §4 Performance | 6 | 0 | 0 | 6 | Locust — chưa thực thi |
| §5 Security | 15 | 2 | 3 | 10 | Phần [BỔ SUNG] chưa code |
| **Tổng** | **132** | **80** | **4** | **48** | 136 test method auto đều PASS |

> Lưu ý: 1 case plan có thể map nhiều test method (vd EP-CREATE-01..05). 136 = số *test method* thực chạy; 132 = số *case* trong plan.

---

## §1. Functional — Kết quả theo app

### 1.1 accounts
| ID | Trạng thái | Test method (bằng chứng) |
|---|---|---|
| FUNC-ACC-001 | ✅ PASS | ACC-LOGIN-01 valid_credentials |
| FUNC-ACC-002 | ✅ PASS | ACC-LOGIN-02 invalid_credentials |
| FUNC-ACC-003 | ✅ PASS | ACC-LOGIN-03 inactive_account |
| FUNC-ACC-004 | ✅ PASS | **ACC-LOGIN-05 lockout_after_3_fails** (mới) |
| FUNC-ACC-005 | ✅ PASS | ACC-FORGOT-01,02 request_otp_valid |
| FUNC-ACC-006 | ⚪ NR | `[BỔ SUNG]` email không tồn tại |
| FUNC-ACC-007 | ✅ PASS | ACC-FORGOT-03 verify_otp_valid |
| FUNC-ACC-008 | ✅ PASS | ACC-FORGOT-04 verify_otp_invalid |
| FUNC-ACC-009 | ⚪ NR | `[BỔ SUNG]` boundary OTP 119/120/121s |
| FUNC-ACC-010 | ✅ PASS | ACC-FORGOT-05 reset_password_success |
| FUNC-ACC-011 | ✅ PASS | ACC-ROLE-01 assign_role |
| FUNC-ACC-012 | ✅ PASS | ACC-ROLE-03 remove_role |
| FUNC-ACC-013 | ✅ PASS | ACC-ROLE-04 assign_custom_permission |
| FUNC-ACC-014 | ✅ PASS | ACC-ROLE-05 non_admin_access |
| FUNC-ACC-015 | ✅ PASS | ACC-ADMIN-01 view_user_list_as_admin |
| FUNC-ACC-016 | ✅ PASS | ACC-ADMIN-02 non_admin |
| FUNC-ACC-017 | ✅ PASS | ACC-ADMIN-03 delete_other_user |
| FUNC-ACC-018 | ✅ PASS | ACC-ADMIN-04 delete_self |
| FUNC-ACC-019 | ✅ PASS | ACC-ADMIN-05,06 toggle_user_active |
| FUNC-ACC-020 | ✅ PASS | ACC-ADMIN-07 toggle_self_active |
| FUNC-ACC-021 | ✅ PASS | ACC-ADMIN-08 reset_user_password |
| (bonus) | ✅ PASS | ACC-LOGIN-06 valid_login_resets_counter |
| (bonus) | ✅ PASS | ACC-REG-01..09 (đăng ký) |

### 1.2 employee_profiles
| ID | Trạng thái | Test method |
|---|---|---|
| FUNC-EP-001 | ✅ PASS | EP-CREATE-01..05 valid_creation |
| FUNC-EP-002 | ✅ PASS | EP-CREATE-06 duplicate_employee_id |
| FUNC-EP-003 | ⚪ NR | `[BỔ SUNG]` MSNV trống |
| FUNC-EP-004 | ⚪ NR | `[BỔ SUNG]` department trống |
| FUNC-EP-005 | ✅ PASS | EP-CREATE-09 non_hr_access |
| FUNC-EP-006 | ✅ PASS | EP-CREATE-10 invalid_contract_days |
| FUNC-EP-007 | ✅ PASS | EP-PROF-01 view_profile |
| FUNC-EP-008 | ✅ PASS | EP-PROF-02 update_basic_info |
| FUNC-EP-009 | ✅ PASS | EP-PROF-06 duplicate_email |
| FUNC-EP-010 | ✅ PASS | EP-EDIT-01,02 edit_all_tables |
| FUNC-EP-011 | ✅ PASS | EP-EDIT-03 non_hr_access |
| FUNC-EP-012 | ✅ PASS | EP-ROLE-01 hr_assign_role |
| FUNC-EP-013 | ✅ PASS | EP-ROLE-02 hr_assign_admin_denied |
| FUNC-EP-014 | ✅ PASS | EP-ROLE-03 admin_assign_admin |
| FUNC-EP-015 | ✅ PASS | EP-DOC-01 upload_valid_document |
| FUNC-EP-016 | ✅ PASS | EP-DOC-03 no_file |
| FUNC-EP-017 | ✅ PASS | validator chung: test_rejects_oversize / test_rejects_bad_mime + view upload validate |

### 1.3 contracts
| ID | Trạng thái | Test method |
|---|---|---|
| FUNC-CON-001 | ✅ PASS | contract_view |
| FUNC-CON-002 | ✅ PASS | get_active_contract_returns_active |
| FUNC-CON-003 | ✅ PASS | user_can_have_multiple_contracts |
| FUNC-CON-004 | ⚪ NR | `[BỔ SUNG]` BĐ ≥ Ký |
| FUNC-CON-005 | ⚪ NR | `[BỔ SUNG]` Hết hạn ≥ BĐ |
| FUNC-CON-006 | ✅ PASS | hr_expiring_contracts_view |
| FUNC-CON-007 | ✅ PASS | hr_send_reminder |
| FUNC-CON-008 | ⚪ NR | `[BỔ SUNG]` batch boundary 30/7 (Render free no cron) |

### 1.4 attendance
| ID | Trạng thái | Test method |
|---|---|---|
| FUNC-ATT-001 | ✅ PASS | ATT-FACE-01 self_update_is_pending (đã sửa) |
| FUNC-ATT-001b | ✅ PASS | **ATT-FACE-02 first_enrollment_applies** (mới) |
| FUNC-ATT-002 | ✅ PASS | hr_upload_applies_immediately |
| FUNC-ATT-003 | ✅ PASS | hr_approve_pending_enrolls |
| FUNC-ATT-004 | ✅ PASS | hr_reject_does_not_enroll |
| FUNC-ATT-005 | ✅ PASS | ATT-FACE-03 no_data |
| FUNC-ATT-006 | ✅ PASS | ATT-FACE-04 require_login |
| FUNC-ATT-007 | ✅ PASS | employee_cannot_access_review |
| FUNC-ATT-008 | ✅ PASS | ATT-CHECK-01,03 check_in |
| FUNC-ATT-009 | ✅ PASS | ATT-CHECK-04 check_out |
| FUNC-ATT-010 | ✅ PASS | ATT-CHECK-05 wrong_face |
| FUNC-ATT-011 | ✅ PASS | ATT-CHECK-06 no_face_uploaded |
| FUNC-ATT-012 | ⚪ NR | `[BỔ SUNG]` lockout chấm công 3 fail/300s |
| FUNC-ATT-013 | ✅ PASS | classify_status |
| FUNC-ATT-014 | ✅ PASS | get_shift_times_fallback |
| FUNC-ATT-015 | ✅ PASS | ATT-VIEW-01,02 view_records / data_correctness |
| FUNC-ATT-016 | ✅ PASS | require_login |
| FUNC-ATT-017 | ✅ PASS | ATT-ADJ-01 submit_valid |
| FUNC-ATT-018 | ✅ PASS | ATT-ADJ-03 already_submitted |
| FUNC-ATT-019 | ✅ PASS | out_of_month_rejected |
| FUNC-ATT-020 | ✅ PASS | requires_at_least_one_time |
| FUNC-ATT-021 | ✅ PASS | requires_evidence |
| FUNC-ATT-022 | ✅ PASS | approve_applies_both_times |
| FUNC-ATT-023 | ✅ PASS | reject_restores_late_status / no_checkout |
| FUNC-ATT-024 | ✅ PASS | leader_can_submit / manager_can_submit |
| FUNC-ATT-025 | ✅ PASS | non_hr_cannot_access_review |

### 1.5 leaves
| ID | Trạng thái | Test method |
|---|---|---|
| FUNC-LEA-001 | ✅ PASS | leave_view_get |
| FUNC-LEA-002 | ✅ PASS | leave_create_valid |
| FUNC-LEA-003 | ✅ PASS | leave_create_invalid_date |
| FUNC-LEA-004 | ⚪ NR | `[BỔ SUNG]` vượt quỹ phép (boundary) |
| FUNC-LEA-005 | ✅ PASS | leave_cancel |
| FUNC-LEA-006 | ✅ PASS | leave_cancel_approved |
| FUNC-LEA-007 | ✅ PASS | leave_approval_flow |
| FUNC-LEA-008 | ✅ PASS | leave_reject |
| FUNC-LEA-009 | ✅ PASS | create_leave_with_attachment |
| FUNC-LEA-010 | ✅ PASS | reject_oversize_attachment |
| FUNC-LEA-011 | ⚪ NR | `[BỔ SUNG]` L1 chỉ leader/manager |

### 1.6 overtime
| ID | Trạng thái | Test method |
|---|---|---|
| FUNC-OT-001 | ✅ PASS | overtime_view_get |
| FUNC-OT-002 | ✅ PASS | overtime_create_valid |
| FUNC-OT-003 | ✅ PASS | overtime_create_invalid_time |
| FUNC-OT-004 | ✅ PASS | overtime_cancel |
| FUNC-OT-005 | ✅ PASS | overtime_approval_flow |
| FUNC-OT-006 | ✅ PASS | overtime_reject |
| FUNC-OT-007 | ✅ PASS | create_overtime_with_attachment |
| FUNC-OT-008 | ⚪ NR | `[BỔ SUNG]` HR tạo → bỏ qua L2 |

### 1.7 performance (đánh giá)
| ID | Trạng thái | Test method |
|---|---|---|
| FUNC-PER-001 | ✅ PASS | evaluations_view_get |
| FUNC-PER-002 | ✅ PASS | manager_create_evaluation |
| FUNC-PER-003 | ✅ PASS | rating_auto_from_score |
| FUNC-PER-004 | ✅ PASS | hr_acknowledge_evaluation |
| FUNC-PER-005 | ⚪ NR | `[BỔ SUNG]` submitted → khóa sửa |

### 1.8 rewards_discipline
| ID | Trạng thái | Test method |
|---|---|---|
| FUNC-RW-001 | ✅ PASS | view_employee |
| FUNC-RW-002 | ✅ PASS | manager_propose_reward |
| FUNC-RW-003 | ✅ PASS | hr_approval_access |
| FUNC-RW-004 | ✅ PASS | hr_approve_reject_reward |
| FUNC-RW-005 | ⚪ NR | `[BỔ SUNG]` luồng 2 cấp Leader→Manager→HR |
| FUNC-RW-006 | ⚪ NR | `[BỔ SUNG]` amount boundary |

### 1.9 reports_interactions
| ID | Trạng thái | Test method |
|---|---|---|
| FUNC-RI-001 | ✅ PASS | create_report |
| FUNC-RI-002 | ✅ PASS | edit_report |
| FUNC-RI-003 | ✅ PASS | delete_report |
| FUNC-RI-004 | ✅ PASS | view_report_marks_as_viewed |
| FUNC-RI-005 | ✅ PASS | recipient_request_update_sets_needs_update |
| FUNC-RI-006 | ✅ PASS | author_edit_needs_update_resets_to_submitted |
| FUNC-RI-007 | ✅ PASS | acknowledged_locks |
| FUNC-RI-008 | ✅ PASS | non_recipient_request_update_denied |
| FUNC-RI-009 | ✅ PASS | create_ticket |
| FUNC-RI-010 | ✅ PASS | process_ticket_receive |
| FUNC-RI-011 | ✅ PASS | process_ticket_resolve |
| FUNC-RI-012 | ✅ PASS | process_ticket_reject |

### 1.10 stats_reports
| ID | Trạng thái | Test method |
|---|---|---|
| FUNC-ST-001 | ✅ PASS | statistics_view_employee |
| FUNC-ST-002 | ✅ PASS | statistics_view_manager |
| FUNC-ST-003 | ✅ PASS | statistics_export_excel |
| FUNC-ST-004 | ✅ PASS | statistics_print |
| FUNC-ST-005 | ⚪ NR | `[BỔ SUNG]` số liệu khớp DB tổng hợp |

---

## §2. UI/UX — ⚪ Chưa thực thi (thủ công)
| ID | Trạng thái |
|---|---|
| UIX-001 … UIX-012 | ⚪ NR — cần chạy thủ công trên desktop (Chrome/Firefox/Edge). Chưa thực hiện đợt này. |

## §3. Compatibility (desktop) — ⚪ Chưa thực thi
| ID | Trạng thái |
|---|---|
| COMPAT-001 … COMPAT-008 | ⚪ NR — cần kiểm thủ công 3 trình duyệt + 2 độ phân giải. Chưa thực hiện. |

## §4. Performance — ⚪ Chưa thực thi
| ID | Trạng thái |
|---|---|
| PERF-001 … PERF-006 | ⚪ NR — cần dựng `tests_perf/locustfile.py` và chạy Load 50 / Stress 200. Chưa thực hiện. |

---

## §5. Security — Kết quả
| ID | Trạng thái | Bằng chứng / Ghi chú |
|---|---|---|
| SEC-001 | ⚪ NR | `[BỔ SUNG]` quét toàn URL ẩn danh |
| SEC-002 | 🟡 PARTIAL | Đã phủ qua non_hr_access / non_admin_access rải rác; chưa quét toàn endpoint |
| SEC-003 | ⚪ NR | `[BỔ SUNG]` ma trận RBAC 5 role đầy đủ |
| SEC-004 | ⚪ NR | `[BỔ SUNG]` IDOR sửa id URL |
| SEC-005 | ⚪ NR | `[BỔ SUNG]` assert hash PBKDF2 |
| SEC-006 | ⚪ NR | `[BỔ SUNG]` SQLi payload |
| SEC-007 | ⚪ NR | `[BỔ SUNG]` XSS payload |
| SEC-008 | ⚪ NR | `[BỔ SUNG]` CSRF thiếu token |
| SEC-009 | ✅ PASS | validator chung: test_rejects_bad_mime / test_rejects_oversize + áp cho reports/ticket/rewards (trước thiếu) |
| SEC-010 | 🟡 PARTIAL | `SESSION_COOKIE_AGE=1800` + `SESSION_SAVE_EVERY_REQUEST` đã cấu hình; chưa có test runtime idle-timeout |
| SEC-011 | ✅ PASS | ACC-LOGIN-05 lockout_after_3_fails |
| SEC-012 | 🟡 PARTIAL | OTP sai/hết hạn có (verify_otp_invalid); chưa test brute-force/biên 120s |
| SEC-013 | ⚪ NR | `[BỔ SUNG]` lockout chấm công 3 fail/300s |
| SEC-014 | ⚪ NR | `[BỔ SUNG]` `manage.py check --deploy` trong CI |
| SEC-015 | ⚪ NR | `[BỔ SUNG]` rà secret hardcode (bandit) |

---

## §6. Kết Quả Đợt Cải Thiện (commit gần nhất)
| Hạng mục | Test | Kết quả |
|---|---|---|
| QĐ_TK1 lockout đăng nhập | ACC-LOGIN-05, ACC-LOGIN-06 | ✅ PASS |
| Validator upload dùng chung | TestSharedUploadValidator (5 case) | ✅ PASS |
| Fix mâu thuẫn face enrollment | ATT-FACE-01 (sửa) + ATT-FACE-02 (mới) + approve/reject | ✅ PASS |
| QĐ_Session timeout | settings (cấu hình) | 🟡 cấu hình xong, chưa test runtime |

---

## §7. Kết Luận
- **Toàn bộ 136 test tự động PASS** (0 fail). Luồng nghiệp vụ chính (CRUD, duyệt 2 cấp, chấm công, RBAC cơ bản, vòng đời trạng thái) đã được phủ và đạt.
- **Còn lại (⚪ NR):** UI/UX, Compatibility, Performance (thủ công/Locust) + các case bảo mật chuyên sâu & boundary `[BỔ SUNG]`.
- **Ưu tiên đợt code tiếp theo** (theo test_plan §8): Security + boundary trước (IDOR, XSS, SQLi, RBAC ma trận, hash MK, boundary OTP/quỹ phép/score), sau đó Locust.

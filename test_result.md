# 📊 Báo Cáo Kết Quả Kiểm Thử — HRMS

> Đối chiếu với [test_plan.md](test_plan.md). Ngày chạy: **02/06/2026** · Lệnh: `python manage.py test` (Django TestCase, SQLite in-memory, Face API & SMTP mock) + Locust (nhóm 4).
>
> **Kết quả tự động:** `Ran 176 tests — OK` → **176 PASS / 0 FAIL / 0 ERROR**.
>
> Đợt cuối: F3 (chặn thứ tự ngày HĐ), F4 (duyệt 2 cấp thưởng/phạt), F5 (siết SECRET_KEY), F6 (auto hết hiệu lực HĐ), + test PER-005/ST-005/SEC-002/CON-008.

## Quy ước trạng thái
| Ký hiệu | Nghĩa |
|---|---|
| ✅ PASS | Test tự động chạy & đạt |
| 🟡 PARTIAL | Phủ một phần (logic/cấu hình có) nhưng chưa phủ hết biên/kịch bản |
| 🟠 FINDING | Test/đối chiếu **phát hiện gap** — hành vi chưa khớp spec (xem §6b) |
| ⚪ NR | Chưa thực thi — thủ công (UI/UX), Locust nâng cao, hoặc chưa code |

---

## §A. Tổng Hợp Số Liệu

| Nhóm | ✅ PASS | 🟡 PARTIAL | 🟠 FINDING | ⚪ NR | Ghi chú |
|---|---|---|---|---|---|
| §1 Functional | ~121 | 0 | 0 | 0 | F3/F4/F6 đã xử lý — không còn treo |
| §2 UI/UX | 0 | 0 | 0 | 12 | Thủ công — chưa thực thi |
| §3 Compatibility (desktop) | 0 | 0 | 0 | 8 | Thủ công đa trình duyệt — chưa thực thi |
| §4 Performance | 2 | 1 | 1 | 2 | Load 50 / Stress 200 / PERF-004 FaceID (F7 SQLite) |
| §5 Security | 15 | 0 | 0 | 0 | Toàn bộ SEC PASS |

> Headline: **176 test method tự động, tất cả PASS.** Finding nghiệp vụ F1–F6 đã xử lý. PERF-004 đã chạy → F7 (SQLite khóa ghi đồng thời) là hạn chế **môi trường dev**, giảm nhẹ bằng PostgreSQL ở prod. Còn NR: UI/UX, Compatibility (thủ công), PERF-005/006.

---

## §1. Functional — Kết quả theo app

### 1.1 accounts — 21/21 ✅
Toàn bộ ACC-001…021 PASS (login, lockout 3 sai, quên MK/OTP, role, admin mgmt).
| ID nổi bật | Trạng thái | Bằng chứng |
|---|---|---|
| FUNC-ACC-004 | ✅ | test_login::lockout_after_3_fails |
| FUNC-ACC-006 | ✅ | test_bo_sung::unknown_username_no_otp |
| FUNC-ACC-009 | ✅ | test_bo_sung::OtpExpiryBoundary (119s valid / 121s hết hạn) |

### 1.2 employee_profiles — 17/17 ✅
| ID nổi bật | Trạng thái | Bằng chứng |
|---|---|---|
| FUNC-EP-003 | ✅ | test_create_validation::employee_id_required |
| FUNC-EP-004 | ✅ | test_create_validation::department_required |
| FUNC-EP-017 | ✅ | validator chung (size/MIME) |

### 1.3 contracts
| ID | Trạng thái | Ghi chú |
|---|---|---|
| FUNC-CON-001/002/003/006/007 | ✅ | test_contracts.py |
| FUNC-CON-004 | ✅ | test_date_order (BĐ<ký → chặn) — F3 đã xử lý |
| FUNC-CON-005 | ✅ | test_date_order (hết hạn<BĐ → chặn) — F3 đã xử lý |
| FUNC-CON-008 (cảnh báo 7/30) | ✅ | test_renewal_thresholds (biên 7 khẩn / 30 xa / >30 loại) |
| FUNC-CON-008 (auto hết hiệu lực) | ✅ | **F6 đã làm** — `expire_overdue_contracts` (quá hạn → is_active=False), gọi trong command. test_renewal_thresholds::TestExpireOverdueContracts |

### 1.4 attendance — 26/26 ✅
| ID nổi bật | Trạng thái | Bằng chứng |
|---|---|---|
| FUNC-ATT-001/001b | ✅ | self_update_is_pending + first_enrollment_applies |
| FUNC-ATT-012 | ✅ | test_face_lockout (3 fail → khóa 300s) |

### 1.5 leaves — 11/11 ✅
| ID nổi bật | Trạng thái | Bằng chứng |
|---|---|---|
| FUNC-LEA-004 | ✅ | TestLeaveQuotaWarning (vượt quỹ → cảnh báo, không chặn) |
| FUNC-LEA-011 | ✅ | test_leave_l1 (chỉ supervisor duyệt L1) |

### 1.6 overtime — 8/8 ✅
| ID nổi bật | Trạng thái | Bằng chứng |
|---|---|---|
| FUNC-OT-008 | ✅ | test_ot_hr_skip_l2 (HR owner → approved sau L1) |

### 1.7 performance
| ID | Trạng thái | Ghi chú |
|---|---|---|
| FUNC-PER-001/002/003/004 | ✅ | test_performance.py |
| FUNC-PER-005 | ✅ | test_eval_lock (không có endpoint sửa → bất biến sau submitted; chỉ acknowledge) |

### 1.8 rewards_discipline
| ID | Trạng thái | Ghi chú |
|---|---|---|
| FUNC-RW-001/002/003/004 | ✅ | test_rewards_discipline.py |
| FUNC-RW-005 | ✅ | **F4 đã triển khai 2 cấp** — test_full_two_level_flow (Leader→Manager L1→HR L2) + hr_cannot_do_l1 |
| FUNC-RW-006 | ✅ | test_amount_boundary (0 hợp lệ, âm bị form chặn) |

### 1.9 reports_interactions — 12/12 ✅
RI-001…012 PASS (CRUD báo cáo, vòng đời, ticket claim/resolve/reject).

### 1.10 stats_reports
| ID | Trạng thái | Ghi chú |
|---|---|---|
| FUNC-ST-001/002/003/004 | ✅ | test_stats_reports.py |
| FUNC-ST-005 | ✅ | test_stats_accuracy (leave/OT/late khớp build_statistics_records) |

---

## §2. UI/UX — ⚪ Chưa thực thi (thủ công, desktop)
UIX-001 … UIX-012: ⚪ NR — chạy tay trên Chrome/Firefox/Edge.

## §3. Compatibility (desktop) — ⚪ Chưa thực thi
COMPAT-001 … COMPAT-008: ⚪ NR — kiểm tay 3 trình duyệt + 2 độ phân giải.

---

## §4. Performance — Đã chạy Locust (local, SQLite dev)

> Công cụ: Locust 2.44.1 + `business_web/tests_perf/locustfile.py`. Server: `runserver` local. **Lưu ý:** SQLite dev + `SESSION_SAVE_EVERY_REQUEST=True` (ghi session mỗi request) làm tăng latency; prod dùng PostgreSQL + gunicorn sẽ khác.

| ID | Kịch bản | Số đo thực tế | Trạng thái |
|---|---|---|---|
| (baseline) | 30 user, GET /login/ | 1299 req, **0 fail**, 91 req/s, p50=5ms, p95=12ms, p99=25ms | ✅ |
| PERF-001 | **Load 50** authenticated (login→dashboard→leave) | 796 req, **0 fail**, 41 req/s; GET dashboard p95=760ms, GET leave p95=790ms (mục tiêu p95<2s → ĐẠT) | ✅ |
| PERF-002 | 50 ghi đồng thời (POST /login/) | p50=850ms, **p95=3.7s** (do PBKDF2 hashing nặng có chủ đích + ghi session SQLite); 0 fail | 🟡 PARTIAL |
| PERF-003 | **Stress 200** (GET /login/) | 10.686 req, 554 req/s, p50=12ms, p95=53ms, p99=530ms, **fail 0.04%** (4 connection-refused lúc ramp); chưa tới điểm sập cho tải đọc | ✅ |
| PERF-004 | FaceID đồng thời — fake remote cô lập backend (recognize + enroll) | Xem bảng dưới | 🟠 FINDING (SQLite) |
| PERF-005 | Mạng 3G (DevTools) | ⚪ NR (thủ công) | ⚪ |
| PERF-006 | Soak 30 phút | ⚪ NR | ⚪ |

**Nhận xét:** Tải đọc rất tốt (200 concurrent, p95=53ms). Nút thắt là **đăng nhập** (PBKDF2 hashing) — hiếm gặp trong thực tế (login thưa). Khuyến nghị prod: PostgreSQL + nhiều gunicorn worker; cân nhắc cache session thay vì DB nếu cần.

### PERF-004 — FaceID đồng thời (fake remote, đo backend Django/DB)
> Setup: `tests_perf/fake_face_api.py` (trả lời tức thì, nhúng `UID:<id>` để recognize 1:1 pass) + `runserver` trỏ `FACE_API_BASE_URL` vào fake → loại AI từ xa, đo riêng backend. `tests_perf/locustfile_face.py`.

| Kịch bản | Đồng thời | req/s | p50 | p95 | Lỗi | Ghi chú |
|---|---|---|---|---|---|---|
| Nhận diện (/check/) | 10 | 20 | 47ms | 190ms | **3.3%** | tải thấp — backend xử lý tốt |
| Nhận diện (/check/) | 50 | 14.5 | 1900ms | 6700ms | **56.7%** | **SQLite vỡ** dưới ghi đồng thời cao |
| Đăng ký (/upload-image/) | 30 | 20 | 170ms | 2100ms | **21.3%** | ghi EmployeeFace + FaceChangeRequest + session |

**Nguyên nhân lỗi (đã xác minh từ log):** 100% lỗi là `sqlite3.OperationalError: database is locked` — **KHÔNG phải bug code**. `/check/` dùng `select_for_update` + ghi AttendanceRecord, cộng `SESSION_SAVE_EVERY_REQUEST=True` (ghi session mỗi request) → SQLite (1 writer) khóa ghi dưới đồng thời cao.

**Kết luận PERF-004:**
- Backend **logic đúng**; ở đồng thời thấp (≤10) hoạt động tốt (p95<200ms).
- Nút thắt là **SQLite dev** — không chịu nổi ghi đồng thời ~30+.
- **Khuyến nghị prod:** PostgreSQL (đa writer, MVCC) — đã cấu hình sẵn cho Render; cân nhắc session backend cache để giảm ghi DB; gunicorn nhiều worker. Lặp lại PERF-004 trên Postgres để xác nhận.

---

## §5. Security — Kết quả
| ID | Trạng thái | Bằng chứng / Ghi chú |
|---|---|---|
| SEC-001 | ✅ | test_security::protected_pages_redirect_anonymous |
| SEC-002 | ✅ | test_rbac_approval (employee bị chặn leave/overtime/rewards/evaluation approval) + RBAC matrix |
| SEC-003 | ✅ | test_bo_sung::TestRbacMatrix (employee bị chặn HR/Admin endpoints) |
| SEC-004 | ✅ | test_security::IDOR (leave + report) |
| SEC-005 | ✅ | test_security::password_is_hashed (PBKDF2) |
| SEC-006 | ✅ | test_security::sqli_login_payload_is_harmless |
| SEC-007 | ✅ | test_security::xss_report_content_is_escaped |
| SEC-008 | ✅ | test_bo_sung::TestCsrf (POST thiếu token → 403) |
| SEC-009 | ✅ | validator chung (bad MIME / oversize) |
| SEC-010 | ✅ | test_bo_sung::TestSessionConfig (COOKIE_AGE=1800 + SAVE_EVERY_REQUEST) |
| SEC-011 | ✅ | test_login::lockout_after_3_fails |
| SEC-012 | ✅ | test_bo_sung::OtpExpiryBoundary (biên 120s) + wrong_code |
| SEC-013 | ✅ | test_face_lockout (3 fail/300s) |
| SEC-014 | ✅ | `check --deploy` (key mạnh) sạch. **Đã siết:** settings raise `ImproperlyConfigured` nếu DEBUG=False + SECRET_KEY yếu (default/<50/<5 ký tự) → chặn deploy key yếu |
| SEC-015 | ✅ | Bí mật đọc qua env (`python-decouple`); gate SECRET_KEY ngăn prod chạy với key mặc định |

---

## §6. Kết Quả Đợt Cải Thiện
| Hạng mục | Test | Kết quả |
|---|---|---|
| QĐ_TK1 lockout đăng nhập | ACC-LOGIN-05/06 | ✅ |
| Validator upload dùng chung | TestSharedUploadValidator | ✅ |
| Fix enrollment khuôn mặt | ATT-FACE-01/02 + approve/reject | ✅ |
| QĐ_Session timeout | TestSessionConfig | ✅ |
| Cảnh báo vượt quỹ phép | TestLeaveQuotaWarning | ✅ |

## §6b. Phát Hiện (Findings)
| # | Mức | Phát hiện | Trạng thái |
|---|---|---|---|
| F1 | 🟠 TB | Không chặn vượt quỹ phép | ✅ ĐÃ XỬ LÝ — cảnh báo, không chặn (TestLeaveQuotaWarning) |
| F2 | 🟡 Thấp | Cache key lockout chứa username thô (CacheKeyWarning) | ✅ ĐÃ FIX — hash SHA256 |
| F3 | 🟠 TB | HĐ không enforce thứ tự ngày | ✅ ĐÃ FIX — chốt "chặn". `validate_contract_date_order` áp cho EmployeeProfileForm + hr_create_profile_view; test_date_order (5) |
| F4 | 🟠 TB | Thưởng/phạt chưa duyệt 2 cấp | ✅ ĐÃ FIX — chốt "triển khai 2 cấp". Model +status `leader_approved`/field, service routing theo role proposer, view Manager(L1)+HR(L2); migration 0003; test (4) |
| F5 | 🟡 Thấp | SECRET_KEY mặc định yếu (W009) | ✅ ĐÃ FIX — settings raise khi DEBUG=False + key yếu |
| F6 | 🟠 TB | HĐ quá hạn không tự `is_active=False` | ✅ ĐÃ FIX — `expire_overdue_contracts` + gọi trong command (bỏ qua dry-run); test (2). ⚠️ Render free không cron → cần trigger định kỳ (xem §6) |
| F7 | 🟠 TB (môi trường) | **SQLite khóa ghi dưới FaceID đồng thời cao** (PERF-004: 50 nhận diện → 56.7% lỗi `database is locked`; 30 đăng ký → 21.3%). Logic backend đúng, lỗi do dev DB. | ⏳ Giảm nhẹ ở prod: PostgreSQL (đã cấu hình Render) + session cache. Cần lặp PERF-004 trên Postgres để đóng |

---

## §7. Kết Luận
- **176 test tự động — toàn bộ PASS.** Toàn bộ FINDING (F1–F6) đã xử lý: cảnh báo quỹ phép, cache key, **thứ tự ngày HĐ (F3)**, **duyệt 2 cấp thưởng/phạt (F4)**, **siết SECRET_KEY (F5)**, **auto hết hiệu lực HĐ (F6)**.
- **Functional:** không còn gap treo. UI/UX + Compatibility là thủ công (NR).
- **Performance:** Load 50 đạt (p95 đọc <800ms, 0 fail); Stress 200 đọc ổn (554 req/s, fail 0.04%). **PERF-004 FaceID:** backend đúng nhưng SQLite khóa ghi ở đồng thời cao (50 nhận diện→56.7% lỗi, 30 đăng ký→21.3%) — F7, giảm nhẹ bằng PostgreSQL prod. Nút thắt khác = login (PBKDF2).
- **Còn ⚪ NR:** UI/UX, Compatibility (thủ công desktop), PERF-005 (3G), PERF-006 (soak) — cần chạy tay/Locust nâng cao.

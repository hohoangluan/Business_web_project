# Design — Căn Chỉnh Code Theo Nghiệp Vụ Walkthrough

> Ngày: 2026-06-01
> Nguồn: so sánh `walkthrough__1_.md` vs codebase `business_web/`
> Mục tiêu: code phản ánh đúng nghiệp vụ HRMS; walkthrough khớp code.

## Bối Cảnh

So sánh model code vs walkthrough phát hiện 6 khác biệt. Phân tích nghiệp vụ:
walkthrough đúng hơn ở 4/6 điểm → sửa code; code đúng hơn ở 2/6 → sửa doc.

| # | Khác biệt | Hướng xử lý |
|---|-----------|-------------|
| A1 | EmergencyContact field names | Sửa doc (code đúng) |
| A2 | QĐ_PheDuyet_L1 threshold sai | Sửa doc (code đúng) |
| B | Leave/Overtime thiếu attachment | Sửa code (thêm field) |
| C | Evaluation thiếu score | Sửa code (thêm field + auto-rating) |
| D | Report thiếu status/manager_note | Sửa code (thêm workflow) |
| E | ContractInfo OneToOne (không lưu lịch sử) | Sửa code (→ ForeignKey + is_active) |
| F | AttendanceAdjustmentRequest thiếu HR duyệt/từ chối | Sửa code (thêm trang + action HR) |
| G | Giờ check-in/out bắt sau khi nhận diện (thiệt NV nếu chậm) | Sửa code (bắt giờ đầu view) |

## Ràng Buộc

- KHÔNG auto-commit. Báo người dùng review sau mỗi phase.
- Chạy `python manage.py test` sau mỗi phase (Django 4.2, không có pytest).
- Mỗi thay đổi schema = additive migration khi có thể.
- Thứ tự: A → B → C → D → E → F0 → F → G (F0/F phụ thuộc E; G độc lập, làm cuối).

---

## Section A — Doc Fixes (0 risk)

Sửa `walkthrough__1_.md`:

1. **EmergencyContact** (mục 2.2): đổi field cho khớp code
   - `phone_number` → `contact_phone`
   - `relationship` → `relation`
   - thêm dòng `contact_address` (TextField — Địa chỉ)
2. **QĐ_PheDuyet_L1** (bảng mục 7): đổi nội dung
   - Cũ: "Nghỉ <2 ngày / OT <4h → Leader; còn lại → Manager"
   - Mới: "Ai là `leader_user` HOẶC `manager_user` của NV → người đó duyệt L1, không phân biệt số ngày/giờ" (khớp mục 4 & 5 và code `_is_direct_supervisor`).

## Section B — Attachment cho Leave + Overtime (low risk)

Model `LeaveRequest` + `OvertimeRequest` thêm:
```python
attachment = models.FileField(
    upload_to='leaves/attachments/%Y/%m/',   # overtime: 'overtime/attachments/%Y/%m/'
    null=True, blank=True,
    help_text='Tệp minh chứng (PDF/JPG/PNG, ≤5MB).',
)
```
- Forms: thêm `attachment` vào `fields` + `ClearableFileInput` widget + label.
- Validate: `clean_attachment` — ext ∈ {pdf,jpg,jpeg,png}, size ≤ 5MB.
- Views: đảm bảo form nhận `request.FILES` (kiểm tra create view của 2 app).
- Migration mỗi app.

## Section C — Evaluation.score + auto-rating (low-med risk)

Model `Evaluation`:
```python
score = models.PositiveSmallIntegerField(
    null=True, blank=True,
    help_text='Điểm đánh giá thang 100.',
)

def save(self, *args, **kwargs):
    if self.score is not None:
        if self.score >= 90: self.rating = 'A'
        elif self.score >= 75: self.rating = 'B'
        elif self.score >= 60: self.rating = 'C'
        else: self.rating = 'D'
    super().save(*args, **kwargs)
```
- Form `EvaluationForm`: bỏ `rating` khỏi fields, thêm `score` (NumberInput min=0 max=100).
- `create_evaluation`: nhận `score` thay vì `rating`.
- `build_evaluation_form_state`: validate `score` (0–100, bắt buộc) thay vì `rating`; cập nhật `form_data` key.
- `to_evaluation_dict`: thêm `'score': evaluation.score`.
- Template `evaluations.html`: đổi input rating → score (kiểm tra & cập nhật).
- Migration.

## Section D — Report.status + manager_note (med risk)

Model `Report`:
```python
SUBMITTED = 'submitted'
NEEDS_UPDATE = 'needs_update'
ACKNOWLEDGED = 'acknowledged'
STATUS_CHOICES = [
    (SUBMITTED, 'Đã gửi'),
    (NEEDS_UPDATE, 'Yêu cầu cập nhật'),
    (ACKNOWLEDGED, 'Đã tiếp nhận'),
]
status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SUBMITTED)
manager_note = models.TextField(blank=True, default='')
```
- `can_edit_or_delete` → `return self.status != self.ACKNOWLEDGED`
  (Quyết định: `needs_update` CHO PHÉP NV sửa & gửi lại. Lock chỉ khi `acknowledged`.)
- Views `report_detail_view` / `report_inbox_view`: thêm action manager
  - `request_update`: set status=needs_update + manager_note, NV sửa lại → status=submitted.
  - `acknowledge`: set status=acknowledged.
- `report_view` edit action: chặn khi status==acknowledged (thay vì is_viewed).
- `is_viewed`/`viewed_at` GIỮ NGUYÊN cho badge "đã xem".
- Data migration: report cũ `is_viewed=True` → status=`acknowledged`; còn lại `submitted`.

## Section E — ContractInfo OneToOne → ForeignKey + lịch sử (HIGH risk)

Lý do: HRMS phải lưu lịch sử HĐ (thử việc → chính thức → gia hạn) — yêu cầu pháp lý.

Model `ContractInfo`:
```python
user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contracts', ...)
is_active = models.BooleanField(default=True, help_text='HĐ đang hiệu lực?')
# Giờ ca làm có cấu trúc — dùng cho phân loại đi trễ / về sớm
shift_start_time = models.TimeField(null=True, blank=True, help_text='Giờ bắt đầu ca (đi trễ tính từ đây).')
shift_end_time = models.TimeField(null=True, blank=True, help_text='Giờ kết thúc ca (về sớm tính từ đây).')
```
(`contract_standard_shift` text GIỮ NGUYÊN cho hiển thị; 2 TimeField mới là nguồn tính toán.)

**Form HR create + edit work info:** thêm 2 input `shift_start_time`/`shift_end_time` (TimeInput type=time). `save_contract_info_from_data` lưu thêm 2 field này.

Backward-compat (giảm breaking surface):
- Service mới `get_active_contract(user)`: trả HĐ `is_active=True` mới nhất, hoặc None.
- `ensure_contract_info(user)` (account_info_service): trả HĐ active, tạo mới nếu chưa có.
- Khi gia hạn/tạo HĐ mới: deactivate HĐ cũ (`is_active=False`), tạo HĐ mới `is_active=True`.

Call sites cần sửa:
- `accounts/services/account/account_info_service.py` — `ensure_contract_info` (get_or_create → active logic).
- `employee_profiles/services/__init__.py` — `save_contract_info_from_data`.
- `employee_profiles/views/profile_views.py` — dùng context `contract_info` (đã truyền sẵn).
- `contracts/services/renewal_service.py` — `get_expiring_contracts` query (lọc is_active nếu cần).
- Templates `contracts/contract.html` — `request.user.contract_info.X` → context var `contract_info` (view contract truyền vào).
- Tests: `accounts/tests/test_register.py`, `employee_profiles/tests/test_edit_work_info.py`, `employee_profiles/tests/test_hr_create_profile.py`.

Migration:
- Schema: OneToOne → FK, add `is_active`. Dữ liệu hiện có set `is_active=True`.

## Section F0 — Giờ ca làm từ Hợp Đồng (phụ thuộc Section E)

Đi trễ (check-in) + về sớm (check-out) tính từ ca làm của HĐ active, fallback setting global.

- **Settings:** thêm `WORK_END_TIME = _time(17, 30)` làm fallback (đã có `WORK_START_TIME = 08:30`).
- **Service** `contracts/services` → `get_shift_times(user)`:
  - `contract = get_active_contract(user)`
  - `start = contract.shift_start_time or settings.WORK_START_TIME`
  - `end = contract.shift_end_time or settings.WORK_END_TIME`
  - trả `(start, end)`. Không có HĐ → cả 2 lấy từ settings.
- **Phân loại status** (`attendance_logging_service`):
  - `classify_status(check_in_time, check_out_time, shift_start, shift_end)`:
    - base = `late` nếu `check_in_time > shift_start + grace` else `on_time`
    - nếu có `check_out_time` và `check_out_time < shift_end` → `early_leave` (override base)
  - `record_check_in`: dùng `shift_start` từ `get_shift_times(user)` thay vì settings trực tiếp.
  - `record_check_out`: sau khi set check_out_time → gọi classify để set `early_leave` nếu về sớm (hiện chưa phân loại).
- **Lưu ý:** đây là điểm couple attendance → contracts. Vì `get_shift_times` có fallback nên an toàn khi NV chưa có HĐ.

## Section F — HR Duyệt/Từ Chối AttendanceAdjustmentRequest (med risk, feature mới)

Model đã có sẵn fields: `status` (pending/approved/rejected), `reviewed_by`, `reviewed_at`, `hr_note`, `claimed_check_out_time`. **Không cần migration.** Chỉ thêm view/service/template/url.

Luồng hiện tại (employee-side): submit → `adj.status='pending'`, `record.status='pending_adjustment'`.

Thêm:
- **Service** `attendance/services/record/adjustment_review_service.py`:
  - `get_pending_adjustments()` — tất cả adj `status='pending'`, select_related record/submitted_by (HR xem toàn bộ, theo RBAC "Điều chỉnh giờ công thủ công → HR").
  - `get_reviewed_adjustments()` — adj đã approved/rejected (lịch sử).
  - `approve_adjustment(hr_user, adj_id, hr_note)`:
    - `record.check_out_time = adj.claimed_check_out_time`
    - `shift_start, shift_end = get_shift_times(record.user)`
    - `record.status = classify_status(record.check_in_time, record.check_out_time, shift_start, shift_end)` (on_time/late, hoặc early_leave nếu giờ khai báo < giờ kết thúc ca HĐ)
    - `adj.status='approved'`, `reviewed_by=hr_user`, `reviewed_at=now`, `hr_note`
    - transaction.atomic; trả `(success, msg)`.
  - `reject_adjustment(hr_user, adj_id, hr_note)`:
    - `adj.status='rejected'`, `reviewed_by/at`, `hr_note`
    - `record.status='no_checkout'` (trở lại trạng thái cũ)
    - trả `(success, msg)`.
- **Views** `attendance/views/adjustment/adjustment_review_view.py`:
  - `adjustment_review_view` (GET) — list pending + reviewed; guard `is_hr_user` else redirect.
  - `adjustment_approve_action` (POST, require_POST) — gọi approve, redirect về review.
  - `adjustment_reject_action` (POST, require_POST) — đọc `hr_note`, gọi reject.
- **URLs**:
  - `attendance/adjustments/review/` → `attendance_adjustment_review`
  - `attendance/adjustments/<int:adj_id>/approve/` → `attendance_adjustment_approve`
  - `attendance/adjustments/<int:adj_id>/reject/` → `attendance_adjustment_reject`
- **Template** `attendance/adjustment/adjustment_review.html` — bảng pending (record, NV, lý do, giờ khai báo, evidence link, nút Duyệt/Từ chối + ô hr_note) + bảng đã xử lý.
- **Permission**: chỉ HR (+ admin nếu `is_hr_user` bao admin — kiểm tra `role_service.is_hr_user`).

Tests (`attendance/tests/test_adjustment.py` bổ sung):
- HR approve → record.check_out_time set, status khôi phục on_time/late, adj.status=approved, reviewed_by=hr.
- HR reject → adj.status=rejected, record.status='no_checkout', hr_note lưu.
- Non-HR user truy cập review → redirect/từ chối.
- approve adj không tồn tại → (False, msg).

## Section G — Bắt Giờ Lúc Request Đến Server (low risk)

Hiện tại `record_check_in`/`record_check_out` tự lấy `timezone.localtime().time()` lúc xử lý — SAU bước verify face (có thể chậm), gây thiệt cho NV.

Sửa: bắt giờ ngay đầu `face_check_view`, truyền xuống service.
- `face_check_view`: dòng đầu (trước lockout gate) `request_time = timezone.localtime()`.
- `record_check_in(user, now=None)` / `record_check_out(user, now=None)`: nhận tham số `now`; nếu None thì fallback `timezone.localtime()` (giữ tương thích test cũ + command `close_open_attendance`).
- View truyền `record_check_in(request.user, now=request_time)` và `record_check_out(request.user, now=request_time)`.
- `record_check_in` dùng `now.time()` cho `check_in_time` và `_classify` theo `now`.
- KHÔNG tin client timestamp (chống gian lận lùi giờ). Độ trễ nhận diện nằm giữa request-đến và ghi-DB → bắt ở đầu view giải quyết trọn.

Tests:
- check-in time = giờ đầu view, không phải sau verify (mock verify chậm → giờ vẫn đúng đầu view).
- `now=None` fallback vẫn hoạt động (test cũ không vỡ).

---

## Testing Strategy

- Sau mỗi section: `python manage.py test <app>` rồi `python manage.py test` (full).
- Section B: test tạo đơn có/không attachment, validate size/ext.
- Section C: test score→rating mapping (90→A, 75→B, 60→C, 59→D), score bắt buộc.
- Section D: test needs_update cho phép sửa, acknowledged khóa; data migration.
- Section E: test get_active_contract, tạo HĐ mới deactivate cũ, register tạo 1 HĐ active, edit_work_info, hr_create_profile.
- Section F0: test get_shift_times (có HĐ → giờ HĐ; không HĐ → settings); classify_status (vào trễ→late, ra sớm→early_leave, đúng giờ→on_time).
- Section F: test approve tính đúng early_leave khi giờ khai báo < shift_end HĐ.
- Section G: check-in time = giờ đầu view (mock verify chậm vẫn đúng); fallback now=None không vỡ test cũ.

## Out of Scope

- Tính lương, audit log, CEO/Super_User (đã loại khỏi phạm vi).
- Ca làm nhiều khung giờ / theo thứ trong tuần (chỉ 1 cặp start-end mỗi HĐ).
- Refactor không liên quan.

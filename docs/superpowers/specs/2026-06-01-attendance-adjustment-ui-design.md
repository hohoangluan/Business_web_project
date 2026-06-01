# Design — Giao Diện & Mở Rộng Điều Chỉnh Chấm Công

> Ngày: 2026-06-01
> Tiếp nối Task 8 (HR duyệt/từ chối adjustment) của milestone walkthrough-alignment.

## Mục Tiêu

1. Nhân viên gửi yêu cầu điều chỉnh giờ công cho **bất kỳ ngày trong tháng hiện tại** (không chỉ ngày quên chấm ra), điều chỉnh **giờ vào và/hoặc giờ ra**. HR quyết định duyệt/từ chối.
2. Giao diện: lối vào rõ ràng cho nhân viên (nút trong bảng lịch sử + banner) và trang HR review hoàn chỉnh, có link nav.

## Hiện Trạng (đã có từ Task 8)

- Model `AttendanceAdjustmentRequest`: `record` (OneToOne→AttendanceRecord), `submitted_by`, `reason`, `reason_detail`, `claimed_check_out_time` (required), `evidence`, `status`, `reviewed_by`, `reviewed_at`, `hr_note`.
- View `submit_adjustment_view`: chỉ cho record `status=='no_checkout'`, set `record.status='pending_adjustment'`. Trả JsonResponse cho lỗi 409/400.
- Service review: `approve_adjustment` (set check_out = claimed, classify_status), `reject_adjustment` (hardcode `record.status='no_checkout'`), `get_pending_adjustments`, `get_reviewed_adjustments`.
- Trang HR review + URL + template cơ bản đã có; **thiếu link nav**.
- Trang Chấm công: banner cho ngày `no_checkout` → nút "Gửi yêu cầu điều chỉnh".

## Bug Phát Hiện

`reject_adjustment` hardcode `record.status='no_checkout'`. Đúng cho ngày quên chấm ra, nhưng SAI khi mở rộng cho mọi ngày: yêu cầu đến từ ngày `late`/`early_leave` khi bị từ chối sẽ ghi đè nhầm thành `no_checkout`. Phải khôi phục trạng thái gốc.

---

## A. Backend

### A1. Model — thêm giờ vào, nới giờ ra
`attendance/models/attendance_adjustment_request_model.py`:
```python
claimed_check_in_time = models.TimeField(
    null=True, blank=True,
    help_text='Giờ vào thực tế nhân viên khai báo (nếu cần sửa).',
)
# đổi claimed_check_out_time:
claimed_check_out_time = models.TimeField(
    null=True, blank=True,
    help_text='Giờ ra thực tế nhân viên khai báo (nếu cần sửa).',
)
```
Migration: 1 cái (add claimed_check_in_time + alter claimed_check_out_time nullable).

### A2. Helper khôi phục trạng thái
`attendance/services/record/attendance_logging_service.py`:
```python
def recompute_record_status(record):
    """Suy lại status của record từ giờ vào/ra hiện có (dùng ca HĐ)."""
    from contracts.services import get_shift_times
    if record.check_in_time is None and record.check_out_time is None:
        return 'absent'
    if record.check_out_time is None:
        return 'no_checkout'
    shift_start, shift_end = get_shift_times(record.user)
    return classify_status(record.check_in_time, record.check_out_time, shift_start, shift_end)
```

### A3. submit_adjustment_view — mở rộng + UX
`attendance/views/adjustment/attendance_adjustment_view.py`:
- Bỏ điều kiện `record.status != 'no_checkout'`. Thay bằng: record thuộc `request.user` (đã có get_object_or_404 user=request.user) **và** record nằm trong **đúng tháng dương lịch hiện tại** — so khớp `(record_date.year, record_date.month) == (today.year, today.month)` (ngày 1 → cuối tháng theo lịch, KHÔNG phụ thuộc lúc bật hệ thống/ngày tham gia). Ngoài tháng → message + redirect attendance.
- Đã có request (OneToOne) → message "Đã gửi yêu cầu cho ngày này" + redirect (thay JsonResponse 409).
- Submit thành công: set `record.status='pending_adjustment'`, message, redirect.
- GET: render form.
- **Phân quyền:** KHÔNG giới hạn role — mọi nhân sự có chấm công (employee, leader, manager) đều gửi yêu cầu cho record CỦA CHÍNH MÌNH tới HR. View chỉ kiểm tra ownership (`user=request.user`), không gate role. Trang Chấm công dùng chung nên nút hiển thị cho tất cả các role này.

### A4. approve_adjustment — áp cả 2 giờ
`attendance/services/record/adjustment_review_service.py`:
```python
if adj.claimed_check_in_time:
    record.check_in_time = adj.claimed_check_in_time
if adj.claimed_check_out_time:
    record.check_out_time = adj.claimed_check_out_time
record.status = recompute_record_status(record)
record.save(update_fields=['check_in_time', 'check_out_time', 'status'])
```

### A5. reject_adjustment — khôi phục đúng
Thay `record.status='no_checkout'` bằng `record.status = recompute_record_status(record)`.

---

## B. Giao Diện Employee

### B1. Form `adjustment_request_form.html`
- Tổng quát hóa câu chữ (bỏ giả định "quên chấm ra").
- Hiển thị giờ vào/ra hiện tại của record để đối chiếu.
- 2 input: giờ vào (mới), giờ ra (mới) — đều optional, ghi rõ "để trống nếu không đổi".
- Giữ reason, reason_detail.
- **Minh chứng (evidence): BẮT BUỘC** — label ghi rõ "(bắt buộc)", thuộc tính `required`.

### B2. Form class `AttendanceAdjustmentForm`
`attendance/forms/adjustment/attendance_adjustment_form.py`:
- Thêm `claimed_check_in_time` vào fields; cả 2 time field optional widget TimeInput.
- `clean()`: nếu cả `claimed_check_in_time` và `claimed_check_out_time` đều trống → ValidationError "Phải khai báo ít nhất giờ vào hoặc giờ ra."
- **Evidence bắt buộc:** model field giữ `null=True, blank=True` (linh hoạt dữ liệu cũ), nhưng FORM ép bắt buộc — trong `clean_evidence`, nếu không có file → `ValidationError('Phải đính kèm minh chứng (ảnh hoặc PDF).')`. Giữ nguyên validate size ≤5MB + MIME đã có.

### B3. Bảng lịch sử (attendance.html)
- View `attendance_view`: gắn `row.adjustment` cho mỗi history row (dict record_id→AdjustmentRequest).
- Template: cột "Điều chỉnh":
  - Nếu `r.adjustment` tồn tại → badge trạng thái (`r.adjustment.get_status_display`).
  - Else → nút "Yêu cầu điều chỉnh" link `{% url 'attendance_adjustment' r.id %}`.
- Giữ banner quên-chấm-ra.

---

## C. Giao Diện HR

### C1. Nav link
`accounts/templates/accounts/base_dashboard.html` — trong khối `{% if role == 'hr' %}`, thêm:
```html
<a href="{% url 'attendance_adjustment_review' %}" class="nav-item {% if active_page == 'attendance_adjustment_review' %}active{% endif %}">
    <i class="fa-regular fa-clock"></i> Duyệt điều chỉnh công
</a>
```
View `adjustment_review_view` đã set `active_page='attendance'` → đổi thành `'attendance_adjustment_review'` để highlight đúng.

### C2. Polish `adjustment_review.html`
Theo design system (card, badge, thẻ thống kê) như attendance.html:
- Header + thẻ "Đang chờ duyệt: N".
- Bảng pending: NV, ngày, lý do, **giờ vào khai báo**, **giờ ra khai báo**, minh chứng, nút Duyệt/Từ chối + ô hr_note.
- Bảng đã xử lý: NV, ngày, badge trạng thái, người duyệt, ghi chú HR.
- Badge: pending (vàng), approved (xanh), rejected (đỏ).

---

## D. Tests

`attendance/tests/test_adjustment.py`:
- submit cho ngày `late` (current month, CÓ evidence) → tạo request, record→`pending_adjustment`.
- submit cho leader/manager (record của chính họ, current month) → tạo request OK (xác nhận không gate role).
- submit ngoài tháng hiện tại → redirect, không tạo request.
- submit với cả 2 giờ trống → form invalid.
- **submit KHÔNG có evidence → form invalid** (evidence bắt buộc).
- approve áp cả giờ vào + giờ ra → record cập nhật cả 2, status recompute.
- reject yêu cầu ngày `late` → record khôi phục `late` (KHÔNG `no_checkout`).
- reject yêu cầu ngày `no_checkout` → khôi phục `no_checkout`.

**Test cũ cần cập nhật (bị ảnh hưởng bởi thay đổi):**
- `test_att_adj_01_submit_valid` / `test_att_adj_04_upload_evidence`: hiện post KHÔNG có evidence (01) → phải thêm evidence vào payload (evidence giờ bắt buộc).
- `test_att_adj_invalid_status` (post record status `late` mong 400): hành vi đổi — record `late` trong tháng hiện tại giờ HỢP LỆ. Sửa test: đổi thành kỳ vọng tạo request thành công, HOẶC đổi sang case ngoài-tháng để vẫn kiểm reject. Giữ ý nghĩa kiểm "record không đủ điều kiện" qua case ngoài tháng.

`attendance/tests/test_attendance_view.py`:
- history row chưa có request → context có cờ cho nút; row đã có request → mang adjustment.

Nav (kiểm tra nhẹ): HR thấy link review; employee không (đã có `is_hr_user` gate ở view — test gate đủ).

## Out of Scope
- Sửa ngày ngoài tháng hiện tại (kỳ đã chốt).
- Điều chỉnh các field khác ngoài giờ vào/ra (reason đã có).
- Tạo record cho ngày hoàn toàn không có chấm công (absent thuần).

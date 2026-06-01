# Attendance Adjustment UI + Mở Rộng — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho phép employee/leader/manager gửi yêu cầu điều chỉnh giờ vào/ra cho mọi ngày trong tháng hiện tại (kèm minh chứng bắt buộc), và hoàn thiện giao diện trang gửi + trang HR duyệt (có link nav).

**Architecture:** Django 4.2 MTV. Backend nới điều kiện submit + thêm field giờ vào + fix khôi phục trạng thái khi reject. Frontend thêm lối vào trong bảng lịch sử + polish trang HR. Service layer giữ business logic.

**Tech Stack:** Django 4.2, SQLite3, `python manage.py test` (KHÔNG pytest).

> **KHÔNG auto-commit.** Mỗi Task có bước commit — chỉ chạy khi người dùng duyệt. Branch hiện tại: `fixbug`.
> **Lệnh chạy ở:** `d:/Study/Nhập môn công nghệ phần mềm/Business_web_project/business_web`.

**Spec:** `docs/superpowers/specs/2026-06-01-attendance-adjustment-ui-design.md`

---

## File Structure

| Task | Files |
|------|-------|
| 1 | `attendance/models/attendance_adjustment_request_model.py` + migration |
| 2 | `attendance/forms/adjustment/attendance_adjustment_form.py` |
| 3 | `attendance/services/record/attendance_logging_service.py`, `attendance/services/record/adjustment_review_service.py` |
| 4 | `attendance/views/adjustment/attendance_adjustment_view.py`, `attendance/tests/test_adjustment.py` |
| 5 | `attendance/views/record/attendance_view.py`, `attendance/templates/attendance/record/attendance.html`, `attendance/templates/attendance/adjustment/adjustment_request_form.html` |
| 6 | `accounts/templates/accounts/base_dashboard.html`, `attendance/views/adjustment/adjustment_review_view.py`, `attendance/templates/attendance/adjustment/adjustment_review.html` |
| 7 | Verification |

---

## Task 1: Model — thêm giờ vào, nới giờ ra nullable

**Files:**
- Modify: `business_web/attendance/models/attendance_adjustment_request_model.py`
- Test: `business_web/attendance/tests/test_adjustment.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào cuối `business_web/attendance/tests/test_adjustment.py`:
```python
class TestAdjustmentModelFields(TestCase):
    def test_create_with_check_in_time(self):
        from datetime import time
        u = User.objects.create_user('nvmodel', password='1')
        rec = AttendanceRecord.objects.create(
            user=u, record_date=timezone.localdate(),
            check_in_time=time(8, 0), status='late',
        )
        adj = AttendanceAdjustmentRequest.objects.create(
            record=rec, submitted_by=u, reason='forgot',
            claimed_check_in_time=time(8, 30),
            claimed_check_out_time=None,
        )
        self.assertEqual(adj.claimed_check_in_time, time(8, 30))
        self.assertIsNone(adj.claimed_check_out_time)
```

- [ ] **Step 2: Chạy test — FAIL**

Run: `python manage.py test attendance.tests.test_adjustment.TestAdjustmentModelFields -v 2`
Expected: FAIL (`claimed_check_in_time` chưa tồn tại; `claimed_check_out_time` chưa nullable).

- [ ] **Step 3: Sửa model**

`business_web/attendance/models/attendance_adjustment_request_model.py` — tìm field `claimed_check_out_time` và thay block thành:
```python
    claimed_check_in_time = models.TimeField(
        null=True, blank=True,
        help_text='Giờ vào thực tế nhân viên khai báo (nếu cần sửa).',
    )
    claimed_check_out_time = models.TimeField(
        null=True, blank=True,
        help_text='Giờ ra thực tế nhân viên khai báo (nếu cần sửa).',
    )
```

- [ ] **Step 4: Tạo migration**

Run: `python manage.py makemigrations attendance`
Expected: migration add `claimed_check_in_time` + alter `claimed_check_out_time`.

- [ ] **Step 5: Chạy test — PASS**

Run: `python manage.py test attendance.tests.test_adjustment.TestAdjustmentModelFields -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" add business_web/attendance/
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" commit -m "feat(attendance): thêm claimed_check_in_time, nới claimed_check_out_time nullable

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Form — 2 giờ optional (ít nhất 1), evidence bắt buộc

**Files:**
- Modify: `business_web/attendance/forms/adjustment/attendance_adjustment_form.py`
- Test: `business_web/attendance/tests/test_adjustment.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `business_web/attendance/tests/test_adjustment.py`:
```python
class TestAdjustmentForm(TestCase):
    def _file(self):
        return SimpleUploadedFile('e.jpg', b'x', content_type='image/jpeg')

    def test_requires_at_least_one_time(self):
        from attendance.forms.adjustment.attendance_adjustment_form import AttendanceAdjustmentForm
        form = AttendanceAdjustmentForm(
            data={'reason': 'forgot', 'reason_detail': ''},
            files={'evidence': self._file()},
        )
        self.assertFalse(form.is_valid())

    def test_requires_evidence(self):
        from attendance.forms.adjustment.attendance_adjustment_form import AttendanceAdjustmentForm
        form = AttendanceAdjustmentForm(
            data={'reason': 'forgot', 'claimed_check_out_time': '17:30'},
            files={},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('evidence', form.errors)

    def test_valid_with_one_time_and_evidence(self):
        from attendance.forms.adjustment.attendance_adjustment_form import AttendanceAdjustmentForm
        form = AttendanceAdjustmentForm(
            data={'reason': 'forgot', 'claimed_check_out_time': '17:30'},
            files={'evidence': self._file()},
        )
        self.assertTrue(form.is_valid(), form.errors)
```

- [ ] **Step 2: Chạy test — FAIL**

Run: `python manage.py test attendance.tests.test_adjustment.TestAdjustmentForm -v 2`
Expected: FAIL (form chưa có claimed_check_in_time; evidence chưa bắt buộc; chưa có rule "ít nhất 1 giờ").

- [ ] **Step 3: Sửa form**

Thay toàn bộ nội dung `business_web/attendance/forms/adjustment/attendance_adjustment_form.py`:
```python
"""ModelForm for AttendanceAdjustmentRequest with evidence + time validation."""
from django import forms

from attendance.models import AttendanceAdjustmentRequest

MAX_EVIDENCE_BYTES = 5 * 1024 * 1024
ALLOWED_EVIDENCE_MIME = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf',
}


class AttendanceAdjustmentForm(forms.ModelForm):
    class Meta:
        model = AttendanceAdjustmentRequest
        fields = [
            'reason', 'reason_detail',
            'claimed_check_in_time', 'claimed_check_out_time', 'evidence',
        ]
        widgets = {
            'reason_detail': forms.Textarea(attrs={'rows': 3}),
            'claimed_check_in_time': forms.TimeInput(attrs={'type': 'time'}),
            'claimed_check_out_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_evidence(self):
        f = self.cleaned_data.get('evidence')
        if not f:
            raise forms.ValidationError(
                'Phải đính kèm minh chứng (ảnh hoặc PDF).'
            )
        if f.size > MAX_EVIDENCE_BYTES:
            raise forms.ValidationError('Chứng từ tối đa 5 MB.')
        content_type = getattr(f, 'content_type', '') or ''
        if content_type not in ALLOWED_EVIDENCE_MIME:
            raise forms.ValidationError(
                'Sai định dạng. Chấp nhận: ảnh (JPG/PNG/GIF/WEBP) hoặc PDF.'
            )
        return f

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('claimed_check_in_time') and not cleaned.get('claimed_check_out_time'):
            raise forms.ValidationError(
                'Phải khai báo ít nhất giờ vào hoặc giờ ra.'
            )
        return cleaned
```

- [ ] **Step 4: Chạy test — PASS**

Run: `python manage.py test attendance.tests.test_adjustment.TestAdjustmentForm -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" add business_web/attendance/
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" commit -m "feat(attendance): form điều chỉnh - giờ vào/ra (ít nhất 1) + minh chứng bắt buộc

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Service — recompute_record_status + approve cả 2 giờ + reject khôi phục

**Files:**
- Modify: `business_web/attendance/services/record/attendance_logging_service.py`
- Modify: `business_web/attendance/services/record/adjustment_review_service.py`
- Test: `business_web/attendance/tests/test_adjustment.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `business_web/attendance/tests/test_adjustment.py`:
```python
class TestAdjustmentApplyBothTimes(TestCase):
    def setUp(self):
        from accounts.models import Role, UserProfile
        self.hr = User.objects.create_user('hr_apply', password='1')
        hr_role, _ = Role.objects.get_or_create(name='hr')
        UserProfile.objects.create(user=self.hr, role=hr_role, employee_id='HRAP')
        self.emp = User.objects.create_user('emp_apply', password='1')
        from datetime import time
        self.rec_late = AttendanceRecord.objects.create(
            user=self.emp, record_date=timezone.localdate(),
            check_in_time=time(9, 0), check_out_time=time(17, 30), status='late',
        )

    def test_approve_applies_both_times(self):
        from datetime import time
        from attendance.services.record.adjustment_review_service import approve_adjustment
        adj = AttendanceAdjustmentRequest.objects.create(
            record=self.rec_late, submitted_by=self.emp, reason='technical',
            claimed_check_in_time=time(8, 0), claimed_check_out_time=time(17, 30),
            status='pending',
        )
        ok, _ = approve_adjustment(self.hr, adj.id, 'ok')
        self.assertTrue(ok)
        self.rec_late.refresh_from_db()
        self.assertEqual(self.rec_late.check_in_time, time(8, 0))
        self.assertEqual(self.rec_late.check_out_time, time(17, 30))
        self.assertEqual(self.rec_late.status, 'on_time')  # 8:00 + 17:30 đúng ca mặc định

    def test_reject_restores_late_status(self):
        from datetime import time
        from attendance.services.record.adjustment_review_service import reject_adjustment
        # record late, đã set pending_adjustment khi submit
        self.rec_late.status = 'pending_adjustment'
        self.rec_late.save(update_fields=['status'])
        adj = AttendanceAdjustmentRequest.objects.create(
            record=self.rec_late, submitted_by=self.emp, reason='technical',
            claimed_check_in_time=time(8, 0), status='pending',
        )
        ok, _ = reject_adjustment(self.hr, adj.id, 'thiếu')
        self.assertTrue(ok)
        self.rec_late.refresh_from_db()
        self.assertEqual(self.rec_late.status, 'late')  # KHÔNG phải no_checkout

    def test_reject_restores_no_checkout(self):
        from datetime import time
        from attendance.services.record.adjustment_review_service import reject_adjustment
        rec = AttendanceRecord.objects.create(
            user=self.emp, record_date=timezone.localdate() - timedelta(days=2),
            check_in_time=time(8, 0), check_out_time=None, status='pending_adjustment',
        )
        adj = AttendanceAdjustmentRequest.objects.create(
            record=rec, submitted_by=self.emp, reason='forgot',
            claimed_check_out_time=time(17, 30), status='pending',
        )
        ok, _ = reject_adjustment(self.hr, adj.id, 'x')
        self.assertTrue(ok)
        rec.refresh_from_db()
        self.assertEqual(rec.status, 'no_checkout')
```

- [ ] **Step 2: Chạy test — FAIL**

Run: `python manage.py test attendance.tests.test_adjustment.TestAdjustmentApplyBothTimes -v 2`
Expected: FAIL (approve chưa áp check_in; reject hardcode no_checkout).

- [ ] **Step 3: Thêm recompute_record_status**

`business_web/attendance/services/record/attendance_logging_service.py` — thêm hàm sau `classify_status`:
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

- [ ] **Step 4: Sửa approve + reject**

`business_web/attendance/services/record/adjustment_review_service.py`:

Đổi import dòng đầu:
```python
from attendance.services.record.attendance_logging_service import (
    classify_status, recompute_record_status,
)
```
(Có thể bỏ `classify_status` nếu không dùng trực tiếp nữa — kiểm tra; recompute thay thế. Giữ import `recompute_record_status`, bỏ `classify_status` và `get_shift_times` nếu không còn dùng ở file này.)

Thay block trong `approve_adjustment` (phần `with transaction.atomic()`):
```python
    with transaction.atomic():
        record = adj.record
        if adj.claimed_check_in_time:
            record.check_in_time = adj.claimed_check_in_time
        if adj.claimed_check_out_time:
            record.check_out_time = adj.claimed_check_out_time
        record.status = recompute_record_status(record)
        record.save(update_fields=['check_in_time', 'check_out_time', 'status'])
        adj.status = 'approved'
        adj.reviewed_by = hr_user
        adj.reviewed_at = timezone.now()
        adj.hr_note = (hr_note or '').strip()
        adj.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_note'])
    return True, 'Đã duyệt yêu cầu điều chỉnh.'
```

Thay block trong `reject_adjustment`:
```python
    with transaction.atomic():
        record = adj.record
        record.status = recompute_record_status(record)
        record.save(update_fields=['status'])
        adj.status = 'rejected'
        adj.reviewed_by = hr_user
        adj.reviewed_at = timezone.now()
        adj.hr_note = (hr_note or '').strip()
        adj.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_note'])
    return True, 'Đã từ chối yêu cầu điều chỉnh.'
```

- [ ] **Step 5: Chạy test — PASS**

Run: `python manage.py test attendance.tests.test_adjustment.TestAdjustmentApplyBothTimes attendance.tests.test_adjustment.TestAdjustmentReview -v 2`
Expected: PASS (gồm cả test reject cũ của Task 8 — record no_checkout vẫn ra no_checkout qua recompute).

- [ ] **Step 6: Commit**

```bash
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" add business_web/attendance/
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" commit -m "feat(attendance): approve áp cả giờ vào/ra, reject khôi phục đúng trạng thái

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: submit view — mở rộng tháng hiện tại + mọi role + UX + sửa test cũ

**Files:**
- Modify: `business_web/attendance/views/adjustment/attendance_adjustment_view.py`
- Test: `business_web/attendance/tests/test_adjustment.py`

- [ ] **Step 1: Viết test thất bại + sửa test cũ**

Trong `business_web/attendance/tests/test_adjustment.py`:

(a) Sửa `TestAdjustment.setUp` — record dùng ngày TRONG tháng hiện tại + thêm helper file:
```python
class TestAdjustment(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nv001', password='123')
        from datetime import time
        first_of_month = timezone.localdate().replace(day=1)
        self.record = AttendanceRecord.objects.create(
            user=self.user,
            record_date=first_of_month,
            check_in_time=time(8, 0),
            status='no_checkout'
        )
        self.url = reverse('attendance_adjustment', args=[self.record.id])

    def _evidence(self):
        return SimpleUploadedFile('e.jpg', b'x', content_type='image/jpeg')
```

(b) Sửa `test_att_adj_01_submit_valid` — thêm evidence + giờ ra:
```python
    def test_att_adj_01_submit_valid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'reason': 'forgot',
            'reason_detail': 'Quên chấm ra',
            'claimed_check_out_time': '17:30',
            'evidence': self._evidence(),
        })
        self.assertRedirects(response, reverse('attendance'))
        adj = AttendanceAdjustmentRequest.objects.get(record=self.record)
        self.assertEqual(adj.status, 'pending')
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'pending_adjustment')
```

(c) Sửa `test_att_adj_04_upload_evidence` — đã có evidence, chỉ đảm bảo claimed time + evidence (giữ nguyên nếu đã đủ; nếu thiếu giờ, thêm `'claimed_check_out_time': '18:00'`).

(d) Thay `test_att_adj_invalid_status` bằng test ngoài-tháng:
```python
    def test_att_adj_out_of_month_rejected(self):
        from datetime import time
        last_month = timezone.localdate().replace(day=1) - timedelta(days=1)
        old_rec = AttendanceRecord.objects.create(
            user=self.user, record_date=last_month,
            check_in_time=time(8, 0), status='no_checkout',
        )
        url = reverse('attendance_adjustment', args=[old_rec.id])
        self.client.force_login(self.user)
        response = self.client.post(url, data={
            'reason': 'forgot', 'claimed_check_out_time': '17:30',
            'evidence': self._evidence(),
        })
        self.assertFalse(AttendanceAdjustmentRequest.objects.filter(record=old_rec).exists())
```

(e) Thêm test mới — leader & ngày `late` hợp lệ:
```python
class TestAdjustmentSubmitRoles(TestCase):
    def _evidence(self):
        return SimpleUploadedFile('e.jpg', b'x', content_type='image/jpeg')

    def _submit_for_role(self, role_name, username):
        from accounts.models import Role, UserProfile
        from datetime import time
        role, _ = Role.objects.get_or_create(name=role_name)
        u = User.objects.create_user(username, password='1')
        UserProfile.objects.create(user=u, role=role, employee_id=username.upper())
        rec = AttendanceRecord.objects.create(
            user=u, record_date=timezone.localdate(),
            check_in_time=time(9, 0), check_out_time=time(17, 30), status='late',
        )
        self.client.force_login(u)
        resp = self.client.post(
            reverse('attendance_adjustment', args=[rec.id]),
            data={'reason': 'technical', 'claimed_check_in_time': '08:00',
                  'evidence': self._evidence()},
        )
        return rec, resp

    def test_leader_can_submit(self):
        rec, resp = self._submit_for_role('leader', 'ldr_adj')
        self.assertRedirects(resp, reverse('attendance'))
        self.assertTrue(AttendanceAdjustmentRequest.objects.filter(record=rec).exists())

    def test_manager_can_submit(self):
        rec, resp = self._submit_for_role('manager', 'mgr_adj')
        self.assertTrue(AttendanceAdjustmentRequest.objects.filter(record=rec).exists())
```

- [ ] **Step 2: Chạy test — FAIL**

Run: `python manage.py test attendance.tests.test_adjustment -v 2`
Expected: FAIL (view vẫn chặn status != no_checkout; chưa lọc tháng; vẫn JsonResponse).

- [ ] **Step 3: Viết lại submit view**

Thay toàn bộ `business_web/attendance/views/adjustment/attendance_adjustment_view.py`:
```python
"""GET/POST /attendance/adjustment/<record_id>/ — nhân viên gửi yêu cầu điều chỉnh.

Mọi role có chấm công (employee/leader/manager) gửi cho record CỦA CHÍNH MÌNH
trong tháng hiện tại. HR duyệt ở trang review.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from attendance.forms.adjustment.attendance_adjustment_form import AttendanceAdjustmentForm
from attendance.models import AttendanceAdjustmentRequest, AttendanceRecord


@login_required
def submit_adjustment_view(request, record_id):
    record = get_object_or_404(
        AttendanceRecord, id=record_id, user=request.user,
    )

    # Đã có yêu cầu cho record này (OneToOne).
    if AttendanceAdjustmentRequest.objects.filter(record=record).exists():
        messages.error(request, 'Ngày này đã có yêu cầu điều chỉnh.')
        return redirect(reverse('attendance'))

    # Chỉ cho điều chỉnh record trong ĐÚNG THÁNG DƯƠNG LỊCH HIỆN TẠI
    # (ngày 1 → cuối tháng theo lịch; không phụ thuộc lúc bật hệ thống).
    today = timezone.localdate()
    if (record.record_date.year, record.record_date.month) != (today.year, today.month):
        messages.error(
            request, 'Chỉ được yêu cầu điều chỉnh cho ngày trong tháng hiện tại.'
        )
        return redirect(reverse('attendance'))

    if request.method == 'POST':
        form = AttendanceAdjustmentForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                adj = form.save(commit=False)
                adj.record = record
                adj.submitted_by = request.user
                adj.status = 'pending'
                adj.save()
                record.status = 'pending_adjustment'
                record.save(update_fields=['status'])
            messages.success(request, 'Đã gửi yêu cầu điều chỉnh tới HR.')
            return redirect(reverse('attendance'))
    else:
        form = AttendanceAdjustmentForm()

    return render(
        request,
        'attendance/adjustment/adjustment_request_form.html',
        {'form': form, 'record': record, 'active_page': 'attendance'},
    )
```

- [ ] **Step 4: Chạy test — PASS**

Run: `python manage.py test attendance.tests.test_adjustment -v 2`
Expected: PASS toàn bộ test_adjustment.

- [ ] **Step 5: Commit**

```bash
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" add business_web/attendance/
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" commit -m "feat(attendance): nhân viên/leader/manager gửi điều chỉnh mọi ngày trong tháng

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Giao diện Employee — nút trong bảng lịch sử + form copy

**Files:**
- Modify: `business_web/attendance/views/record/attendance_view.py`
- Modify: `business_web/attendance/templates/attendance/record/attendance.html`
- Modify: `business_web/attendance/templates/attendance/adjustment/adjustment_request_form.html`
- Test: `business_web/attendance/tests/test_attendance_view.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `business_web/attendance/tests/test_attendance_view.py`:
```python
class TestHistoryAdjustmentColumn(TestCase):
    def setUp(self):
        from datetime import time
        self.user = User.objects.create_user('nvhist', password='1')
        first_of_month = timezone.localdate().replace(day=1)
        self.rec = AttendanceRecord.objects.create(
            user=self.user, record_date=first_of_month,
            check_in_time=time(8, 0), status='no_checkout',
        )

    def test_row_without_request_has_no_adjustment(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('attendance'))
        rows = resp.context['history_rows']
        self.assertIsNone(getattr(rows[0], 'adjustment', None))

    def test_row_with_request_carries_adjustment(self):
        from datetime import time
        AttendanceAdjustmentRequest.objects.create(
            record=self.rec, submitted_by=self.user, reason='forgot',
            claimed_check_out_time=time(17, 30), status='pending',
        )
        self.client.force_login(self.user)
        resp = self.client.get(reverse('attendance'))
        rows = resp.context['history_rows']
        self.assertIsNotNone(getattr(rows[0], 'adjustment', None))
```
Thêm import nếu thiếu ở đầu file: `from attendance.models import AttendanceAdjustmentRequest`.

- [ ] **Step 2: Chạy test — FAIL**

Run: `python manage.py test attendance.tests.test_attendance_view.TestHistoryAdjustmentColumn -v 2`
Expected: FAIL (rows chưa có attr `adjustment`).

- [ ] **Step 3: Gắn adjustment vào history rows**

`business_web/attendance/views/record/attendance_view.py` — thay `_history_rows` + dùng trong view:
```python
def _history_rows(user, limit=10):
    today = timezone.localdate()
    first_of_month = today.replace(day=1)
    rows = list(
        AttendanceRecord.objects
        .filter(user=user, record_date__gte=first_of_month)
        .order_by('-record_date')[:limit]
    )
    adj_map = {
        a.record_id: a
        for a in AttendanceAdjustmentRequest.objects.filter(
            record__in=rows,
        )
    }
    for r in rows:
        r.adjustment = adj_map.get(r.id)
    return rows
```
(`AttendanceAdjustmentRequest` đã import sẵn trong file — kiểm tra dòng `from attendance.models import AttendanceRecord, AttendanceAdjustmentRequest`; có rồi.)

- [ ] **Step 4: Chạy test — PASS**

Run: `python manage.py test attendance.tests.test_attendance_view.TestHistoryAdjustmentColumn -v 2`
Expected: PASS.

- [ ] **Step 5: Thêm cột "Điều chỉnh" vào bảng lịch sử**

`business_web/attendance/templates/attendance/record/attendance.html`:
- Trong `<thead><tr>` của bảng lịch sử, thêm cột cuối: `<th>ĐIỀU CHỈNH</th>` (sau cột TRẠNG THÁI).
- Trong `{% for r in history_rows %}` `<tr>`, sau ô trạng thái (`<td>...status...</td>`), thêm:
```html
                            <td>
                                {% if r.adjustment %}
                                    {% if r.adjustment.status == 'pending' %}
                                        <span class="table-badge" style="background:#eef2ff;color:#3730a3;">Chờ HR duyệt</span>
                                    {% elif r.adjustment.status == 'approved' %}
                                        <span class="table-badge badge-ontime">Đã duyệt</span>
                                    {% else %}
                                        <span class="table-badge" style="background:#fee2e2;color:#991b1b;">Từ chối</span>
                                    {% endif %}
                                {% elif r.record_date >= today_first_of_month %}
                                    <a class="btn btn-outline" style="padding:0.25rem 0.6rem;font-size:0.8rem;" href="{% url 'attendance_adjustment' r.id %}">Yêu cầu điều chỉnh</a>
                                {% else %}—{% endif %}
                            </td>
```
- Cập nhật dòng "empty" colspan từ `colspan="5"` thành `colspan="6"`.
- View cần truyền `today_first_of_month`. Trong `attendance_view` context (file `attendance_view.py`), thêm key:
```python
        'today_first_of_month': timezone.localdate().replace(day=1),
```

- [ ] **Step 6: Tổng quát hóa form template**

`business_web/attendance/templates/attendance/adjustment/adjustment_request_form.html` — thay phần thân form:
- Đổi câu mô tả dòng ~7-9 thành:
```html
    <p style="color:var(--text-muted); margin-bottom:1.5rem;">
        Khai báo giờ vào/ra thực tế cho ngày này và đính kèm minh chứng. Yêu cầu sẽ gửi HR duyệt.
    </p>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:var(--radius-md);padding:0.75rem 1rem;margin-bottom:1.25rem;font-size:0.9rem;">
        Giờ hiện tại — Vào:
        <strong>{% if record.check_in_time %}{{ record.check_in_time|time:"H:i" }}{% else %}—{% endif %}</strong>,
        Ra:
        <strong>{% if record.check_out_time %}{{ record.check_out_time|time:"H:i" }}{% else %}—{% endif %}</strong>
    </div>
```
- Thay 1 group `claimed_check_out_time` cũ bằng 2 group giờ vào/ra:
```html
        <div class="form-group">
            <label>Giờ vào mới (để trống nếu không đổi)</label>
            {{ form.claimed_check_in_time }}
            {{ form.claimed_check_in_time.errors }}
        </div>
        <div class="form-group">
            <label>Giờ ra mới (để trống nếu không đổi)</label>
            {{ form.claimed_check_out_time }}
            {{ form.claimed_check_out_time.errors }}
        </div>
```
- Đổi label evidence thành bắt buộc:
```html
        <div class="form-group">
            <label>Minh chứng (ảnh hoặc PDF, tối đa 5 MB) — bắt buộc</label>
            {{ form.evidence }}
            {{ form.evidence.errors }}
        </div>
```
- Hiển thị lỗi tổng (non_field) trên đầu form: ngay sau `{% csrf_token %}` thêm:
```html
        {{ form.non_field_errors }}
```

- [ ] **Step 7: Chạy test attendance — PASS**

Run: `python manage.py test attendance -v 1`
Expected: chỉ PASS (không còn pre-existing fail vì đã fix ở milestone trước). Nếu có fail, kiểm tra.

- [ ] **Step 8: Commit**

```bash
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" add business_web/attendance/
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" commit -m "feat(attendance): nút yêu cầu điều chỉnh trong lịch sử + form giờ vào/ra

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Giao diện HR — nav link + polish trang review

**Files:**
- Modify: `business_web/accounts/templates/accounts/base_dashboard.html`
- Modify: `business_web/attendance/views/adjustment/adjustment_review_view.py`
- Modify: `business_web/attendance/templates/attendance/adjustment/adjustment_review.html`
- Test: `business_web/attendance/tests/test_adjustment.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `business_web/attendance/tests/test_adjustment.py`:
```python
class TestAdjustmentReviewNav(TestCase):
    def test_hr_sees_review_link(self):
        from accounts.models import Role, UserProfile
        hr = User.objects.create_user('hr_nav', password='1')
        role, _ = Role.objects.get_or_create(name='hr')
        UserProfile.objects.create(user=hr, role=role, employee_id='HRNAV')
        self.client.force_login(hr)
        resp = self.client.get(reverse('attendance_adjustment_review'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse('attendance_adjustment_review'))
        self.assertContains(resp, 'Duyệt điều chỉnh công')
```

- [ ] **Step 2: Chạy test — FAIL**

Run: `python manage.py test attendance.tests.test_adjustment.TestAdjustmentReviewNav -v 2`
Expected: FAIL (chưa có link "Duyệt điều chỉnh công" trong nav).

- [ ] **Step 3: Thêm nav link**

`business_web/accounts/templates/accounts/base_dashboard.html` — trong khối `{% if request.user.profile.role.name == 'hr' %}` (gần dòng 103-125, nơi có hr_create_profile / evaluation_hr_approval), thêm 1 mục:
```html
                <a href="{% url 'attendance_adjustment_review' %}" class="nav-item {% if active_page == 'attendance_adjustment_review' %}active{% endif %}">
                    <i class="fa-regular fa-clock"></i>
                    <span>Duyệt điều chỉnh công</span>
                </a>
```
(Đặt cạnh `evaluation_hr_approval` cho gọn nhóm duyệt. Khớp cấu trúc `<a class="nav-item">...<i>...<span>...` với các mục lân cận — đọc 1 mục kề để sao đúng markup icon/span.)

- [ ] **Step 4: active_page đúng**

`business_web/attendance/views/adjustment/adjustment_review_view.py` — trong `adjustment_review_view`, đổi context `'active_page': 'attendance'` thành `'active_page': 'attendance_adjustment_review'`.

- [ ] **Step 5: Chạy test — PASS**

Run: `python manage.py test attendance.tests.test_adjustment.TestAdjustmentReviewNav -v 2`
Expected: PASS.

- [ ] **Step 6: Polish trang review**

Thay toàn bộ `business_web/attendance/templates/attendance/adjustment/adjustment_review.html`:
```html
{% extends 'accounts/base_dashboard.html' %}
{% block title %}Duyệt điều chỉnh chấm công{% endblock %}

{% block content %}
<style>
    .adj-badge { padding:0.3rem 0.8rem; border-radius:var(--radius-full); font-size:0.8rem; font-weight:600; }
    .adj-pending { background:#eef2ff; color:#3730a3; }
    .adj-approved { background:#ecfdf5; color:#059669; }
    .adj-rejected { background:#fee2e2; color:#991b1b; }
    .adj-actions form { display:inline-flex; gap:0.4rem; align-items:center; margin-right:0.5rem; }
    .adj-actions input[type=text] { padding:0.3rem 0.5rem; border:1px solid var(--border, #e2e8f0); border-radius:var(--radius-md); font-size:0.85rem; }
</style>

<div class="animate-fade">
    <div style="margin-bottom:1.5rem;">
        <h2 style="font-size:1.6rem; font-weight:700; color:var(--text-main);">Duyệt điều chỉnh chấm công</h2>
        <p style="color:var(--text-muted); font-size:0.95rem;">Xem xét và phê duyệt yêu cầu điều chỉnh giờ công của nhân viên.</p>
    </div>

    {% if messages %}
        {% for m in messages %}
        <div class="alert" style="margin-bottom:1rem;">{{ m }}</div>
        {% endfor %}
    {% endif %}

    <div class="stats-grid" style="grid-template-columns: repeat(2, minmax(0,260px)); gap:1.5rem; margin-bottom:2rem;">
        <div class="card" style="padding:1.25rem; display:flex; align-items:center; gap:1rem;">
            <div class="stat-icon" style="background:#eef2ff; color:#4f46e5; width:45px; height:45px; font-size:1.2rem; border-radius:12px; display:flex; align-items:center; justify-content:center;">
                <i class="fa-regular fa-hourglass-half"></i>
            </div>
            <div>
                <div style="font-size:0.85rem; color:var(--text-muted);">Đang chờ duyệt</div>
                <div style="font-size:1.35rem; font-weight:700;">{{ pending|length }}</div>
            </div>
        </div>
    </div>

    <div class="card" style="margin-bottom:2rem;">
        <div class="card-header"><h3>Đang chờ duyệt</h3></div>
        <div class="card-body" style="padding:0;">
            <div class="table-wrapper" style="border:none;">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th style="padding-left:1.5rem;">NHÂN VIÊN</th>
                            <th>NGÀY</th>
                            <th>LÝ DO</th>
                            <th>GIỜ VÀO KHAI BÁO</th>
                            <th>GIỜ RA KHAI BÁO</th>
                            <th>MINH CHỨNG</th>
                            <th>XỬ LÝ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for adj in pending %}
                        <tr>
                            <td style="padding-left:1.5rem;">{{ adj.submitted_by.profile.full_name|default:adj.submitted_by.username }}</td>
                            <td>{{ adj.record.record_date|date:"d/m/Y" }}</td>
                            <td>{{ adj.get_reason_display }}{% if adj.reason_detail %}<br><small style="color:var(--text-muted);">{{ adj.reason_detail }}</small>{% endif %}</td>
                            <td>{% if adj.claimed_check_in_time %}{{ adj.claimed_check_in_time|time:"H:i" }}{% else %}—{% endif %}</td>
                            <td>{% if adj.claimed_check_out_time %}{{ adj.claimed_check_out_time|time:"H:i" }}{% else %}—{% endif %}</td>
                            <td>{% if adj.evidence %}<a href="{{ adj.evidence.url }}" target="_blank">Xem</a>{% else %}—{% endif %}</td>
                            <td class="adj-actions">
                                <form method="post" action="{% url 'attendance_adjustment_approve' adj.id %}">
                                    {% csrf_token %}
                                    <input type="text" name="hr_note" placeholder="Ghi chú">
                                    <button class="btn btn-primary" style="padding:0.3rem 0.7rem;font-size:0.85rem;" type="submit">Duyệt</button>
                                </form>
                                <form method="post" action="{% url 'attendance_adjustment_reject' adj.id %}">
                                    {% csrf_token %}
                                    <input type="text" name="hr_note" placeholder="Lý do từ chối">
                                    <button class="btn btn-outline" style="padding:0.3rem 0.7rem;font-size:0.85rem;" type="submit">Từ chối</button>
                                </form>
                            </td>
                        </tr>
                        {% empty %}
                        <tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-muted);">Không có yêu cầu nào đang chờ duyệt.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-header"><h3>Đã xử lý</h3></div>
        <div class="card-body" style="padding:0;">
            <div class="table-wrapper" style="border:none;">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th style="padding-left:1.5rem;">NHÂN VIÊN</th>
                            <th>NGÀY</th>
                            <th>TRẠNG THÁI</th>
                            <th>NGƯỜI DUYỆT</th>
                            <th>GHI CHÚ HR</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for adj in reviewed %}
                        <tr>
                            <td style="padding-left:1.5rem;">{{ adj.submitted_by.profile.full_name|default:adj.submitted_by.username }}</td>
                            <td>{{ adj.record.record_date|date:"d/m/Y" }}</td>
                            <td>
                                {% if adj.status == 'approved' %}
                                    <span class="adj-badge adj-approved">Đã duyệt</span>
                                {% else %}
                                    <span class="adj-badge adj-rejected">Từ chối</span>
                                {% endif %}
                            </td>
                            <td>{{ adj.reviewed_by.profile.full_name|default:adj.reviewed_by.username|default:"—" }}</td>
                            <td>{{ adj.hr_note|default:"—" }}</td>
                        </tr>
                        {% empty %}
                        <tr><td colspan="5" style="text-align:center;padding:2rem;color:var(--text-muted);">Chưa có yêu cầu nào được xử lý.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 7: Chạy test review + adjustment — PASS**

Run: `python manage.py test attendance.tests.test_adjustment -v 1`
Expected: PASS toàn bộ.

- [ ] **Step 8: Commit**

```bash
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" add business_web/accounts/ business_web/attendance/
git -C "d:/Study/Nhập môn công nghệ phần mềm/Business_web_project" commit -m "feat(attendance): nav link HR + polish trang duyệt điều chỉnh công

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Verification cuối

- [ ] **Step 1: Full suite**

Run: `python manage.py test -v 1`
Expected: PASS toàn bộ (0 fail).

- [ ] **Step 2: Migration check**

Run: `python manage.py makemigrations --check --dry-run`
Expected: "No changes detected".

- [ ] **Step 3: Báo người dùng tổng kết** — các tính năng: submit mọi role/mọi ngày-tháng-này, giờ vào+ra, minh chứng bắt buộc, nút trong lịch sử, nav link HR, trang review polish. Hỏi muốn cập nhật `walkthrough__1_.md` ghi giờ vào khai báo + minh chứng bắt buộc không.

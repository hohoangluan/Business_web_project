# Walkthrough Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Căn chỉnh code HRMS khớp nghiệp vụ walkthrough (attachment, evaluation score, report workflow, lịch sử hợp đồng, giờ ca từ HĐ, HR duyệt điều chỉnh công, bắt giờ chấm công sớm).

**Architecture:** Django 4.2 MTV, multi-app. Mỗi thay đổi schema = migration riêng (dùng `makemigrations`). Service layer giữ business logic. TDD: viết test trước, chạy `python manage.py test`, rồi implement.

**Tech Stack:** Django 4.2, SQLite3, `python manage.py test` (KHÔNG có pytest).

> **RÀNG BUỘC: KHÔNG auto-commit.** Mỗi Task kết thúc bằng *Checkpoint* — chạy test, báo người dùng review. Chỉ chạy lệnh `git commit` khi người dùng đồng ý. Lệnh commit ghi sẵn trong checkpoint để dùng khi được duyệt.

> **Lệnh chạy ở thư mục:** `d:/Study/Nhập môn công nghệ phần mềm/Business_web_project/business_web` (chứa `manage.py`).

**Thứ tự:** A → B → C → D → E → F0 → F → G (F0/F/G phụ thuộc E).

---

## File Structure

| Section | Files |
|---------|-------|
| A | `walkthrough__1_.md` (doc) |
| B | `leaves/models/leave_request_model.py`, `leaves/forms.py`, `leaves/views/__init__.py`, `overtime/...` tương tự, migrations |
| C | `performance/models/evaluation_model.py`, `performance/forms.py`, `performance/services/__init__.py`, template, migration |
| D | `reports_interactions/models/report_model.py`, `reports_interactions/views/__init__.py`, data migration |
| E | `contracts/models/contract_info_model.py`, `contracts/services/__init__.py`, `accounts/services/account/account_info_service.py`, `employee_profiles/services/__init__.py`, `contracts/services/renewal_service.py`, `contracts/templates/contracts/contract.html`, forms, 3 test files, migration |
| F0 | `business_web/settings.py`, `contracts/services/__init__.py`, `attendance/services/record/attendance_logging_service.py` |
| F | `attendance/services/record/adjustment_review_service.py`, `attendance/views/adjustment/adjustment_review_view.py`, `attendance/views/__init__.py`, `attendance/urls.py`, `attendance/templates/attendance/adjustment/adjustment_review.html`, test |
| G | `attendance/views/face/face_attendance_view.py`, `attendance/services/record/attendance_logging_service.py`, test |

---

## Task 1: Section A — Doc fixes

**Files:**
- Modify: `walkthrough__1_.md`

- [ ] **Step 1: Sửa EmergencyContact (mục 2.2)**

Tìm bảng `EmergencyContact` (dòng ~144-150). Thay 3 dòng field:
```markdown
| `user` | OneToOneField → User | Nhân viên |
| `contact_name` | CharField | Tên người liên hệ khẩn |
| `relation` | CharField | Mối quan hệ |
| `contact_phone` | CharField | Số điện thoại khẩn |
| `contact_address` | TextField | Địa chỉ người liên hệ |
```

- [ ] **Step 2: Sửa QĐ_PheDuyet_L1 (mục 7, dòng ~885)**

Thay dòng:
```markdown
| `QĐ_PheDuyet_L1` | Ai là `leader_user` HOẶC `manager_user` của NV trong EmployeeWorkInfo → người đó duyệt L1, không phân biệt số ngày/giờ |
```

- [ ] **Step 3: Checkpoint**

Không có test (chỉ doc). Báo người dùng review. Khi duyệt:
```bash
git add walkthrough__1_.md
git commit -m "docs: sửa EmergencyContact fields và QĐ_PheDuyet_L1 khớp code"
```

---

## Task 2: Section B — Attachment cho LeaveRequest

**Files:**
- Modify: `leaves/models/leave_request_model.py`
- Modify: `leaves/forms.py`
- Modify: `leaves/views/__init__.py:34`
- Test: `leaves/tests/test_leaves.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `leaves/tests/test_leaves.py`:
```python
from django.core.files.uploadedfile import SimpleUploadedFile

class TestLeaveAttachment(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='nvleave', password='123')
        self.client.force_login(self.user)
        self.today = timezone.localdate()

    def test_create_leave_with_attachment(self):
        from datetime import timedelta
        pdf = SimpleUploadedFile('don.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        resp = self.client.post(reverse('leave'), data={
            'leave_type': 'annual',
            'start_date': (self.today + timedelta(days=1)).isoformat(),
            'end_date': (self.today + timedelta(days=2)).isoformat(),
            'reason': 'Việc gia đình',
            'attachment': pdf,
        })
        from leaves.models import LeaveRequest
        req = LeaveRequest.objects.get(user=self.user)
        self.assertTrue(req.attachment.name.startswith('leaves/attachments/'))

    def test_reject_oversize_attachment(self):
        from datetime import timedelta
        big = SimpleUploadedFile('big.pdf', b'x' * (5 * 1024 * 1024 + 1), content_type='application/pdf')
        from leaves.forms import LeaveRequestForm
        form = LeaveRequestForm(data={
            'leave_type': 'annual',
            'start_date': (self.today + timedelta(days=1)).isoformat(),
            'end_date': (self.today + timedelta(days=2)).isoformat(),
            'reason': 'x',
        }, files={'attachment': big})
        self.assertFalse(form.is_valid())
        self.assertIn('attachment', form.errors)
```
Đảm bảo file có sẵn `from django.urls import reverse`, `from django.test import TestCase`, `from django.utils import timezone` (kiểm tra đầu file, thêm nếu thiếu).

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test leaves.tests.test_leaves.TestLeaveAttachment -v 2`
Expected: FAIL (`LeaveRequest` chưa có field `attachment`).

- [ ] **Step 3: Thêm field vào model**

`leaves/models/leave_request_model.py` — thêm sau field `rejected_reason` (trước `created_at`):
```python
    attachment = models.FileField(
        upload_to='leaves/attachments/%Y/%m/',
        null=True,
        blank=True,
        help_text='Tệp minh chứng (PDF/JPG/PNG, ≤5MB).',
    )
```

- [ ] **Step 4: Thêm field + validate vào form**

`leaves/forms.py` — trong `Meta.fields` đổi thành:
```python
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'attachment']
```
Thêm vào `Meta.widgets`:
```python
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
```
Thêm vào `Meta.labels`:
```python
            'attachment': 'Tệp minh chứng (nếu có)',
```
Thêm method trong class `LeaveRequestForm`:
```python
    MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
    ALLOWED_ATTACHMENT_MIME = {'application/pdf', 'image/jpeg', 'image/png'}

    def clean_attachment(self):
        f = self.cleaned_data.get('attachment')
        if not f:
            return f
        if f.size > self.MAX_ATTACHMENT_BYTES:
            raise forms.ValidationError('Tệp tối đa 5 MB.')
        content_type = getattr(f, 'content_type', '') or ''
        if content_type not in self.ALLOWED_ATTACHMENT_MIME:
            raise forms.ValidationError('Chấp nhận PDF / JPG / PNG.')
        return f
```

- [ ] **Step 5: View nhận request.FILES**

`leaves/views/__init__.py:34` — đổi:
```python
        form = LeaveRequestForm(request.POST, request.FILES)
```

- [ ] **Step 6: Tạo migration**

Run: `python manage.py makemigrations leaves`
Expected: tạo `leaves/migrations/0003_leaverequest_attachment.py`.

- [ ] **Step 7: Chạy test — kỳ vọng PASS**

Run: `python manage.py test leaves -v 2`
Expected: PASS toàn bộ.

- [ ] **Step 8: Checkpoint**

Báo người dùng. Khi duyệt:
```bash
git add leaves/
git commit -m "feat(leaves): thêm tệp minh chứng đính kèm đơn nghỉ phép"
```

---

## Task 3: Section B — Attachment cho OvertimeRequest

**Files:**
- Modify: `overtime/models/overtime_request_model.py`
- Modify: `overtime/forms.py`
- Modify: `overtime/views/__init__.py:35`
- Test: `overtime/tests/test_overtime.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `overtime/tests/test_overtime.py`:
```python
from django.core.files.uploadedfile import SimpleUploadedFile

class TestOvertimeAttachment(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='nvot', password='123')
        self.client.force_login(self.user)
        self.today = timezone.localdate()

    def test_create_overtime_with_attachment(self):
        pdf = SimpleUploadedFile('ot.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        self.client.post(reverse('overtime'), data={
            'overtime_date': self.today.isoformat(),
            'start_time': '18:00',
            'end_time': '20:00',
            'hours': '2.0',
            'reason': 'Chạy deadline',
            'attachment': pdf,
        })
        from overtime.models import OvertimeRequest
        req = OvertimeRequest.objects.get(user=self.user)
        self.assertTrue(req.attachment.name.startswith('overtime/attachments/'))
```
Kiểm tra đầu file có `reverse`, `TestCase`, `timezone` — thêm nếu thiếu.

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test overtime.tests.test_overtime.TestOvertimeAttachment -v 2`
Expected: FAIL (chưa có field).

- [ ] **Step 3: Thêm field vào model**

`overtime/models/overtime_request_model.py` — thêm sau `rejected_reason` (trước `created_at`):
```python
    attachment = models.FileField(
        upload_to='overtime/attachments/%Y/%m/',
        null=True,
        blank=True,
        help_text='Tệp minh chứng (PDF/JPG/PNG, ≤5MB).',
    )
```

- [ ] **Step 4: Thêm field + validate vào form**

`overtime/forms.py` — `Meta.fields` đổi thành:
```python
        fields = ['overtime_date', 'start_time', 'end_time', 'hours', 'reason', 'attachment']
```
Thêm vào `Meta.widgets`:
```python
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
```
Thêm vào `Meta.labels`:
```python
            'attachment': 'Tệp minh chứng (nếu có)',
```
Thêm method trong class:
```python
    MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
    ALLOWED_ATTACHMENT_MIME = {'application/pdf', 'image/jpeg', 'image/png'}

    def clean_attachment(self):
        f = self.cleaned_data.get('attachment')
        if not f:
            return f
        if f.size > self.MAX_ATTACHMENT_BYTES:
            raise forms.ValidationError('Tệp tối đa 5 MB.')
        content_type = getattr(f, 'content_type', '') or ''
        if content_type not in self.ALLOWED_ATTACHMENT_MIME:
            raise forms.ValidationError('Chấp nhận PDF / JPG / PNG.')
        return f
```

- [ ] **Step 5: View nhận request.FILES**

`overtime/views/__init__.py:35` — đổi:
```python
        form = OvertimeRequestForm(request.POST, request.FILES)
```

- [ ] **Step 6: Tạo migration**

Run: `python manage.py makemigrations overtime`
Expected: tạo `overtime/migrations/0004_overtimerequest_attachment.py`.

- [ ] **Step 7: Chạy test — kỳ vọng PASS**

Run: `python manage.py test overtime -v 2`
Expected: PASS.

- [ ] **Step 8: Checkpoint**

```bash
git add overtime/
git commit -m "feat(overtime): thêm tệp minh chứng đính kèm đơn tăng ca"
```

---

## Task 4: Section C — Evaluation.score + auto-rating

**Files:**
- Modify: `performance/models/evaluation_model.py`
- Modify: `performance/forms.py`
- Modify: `performance/services/__init__.py` (`create_evaluation`, `build_evaluation_form_state`, `to_evaluation_dict`)
- Modify: `performance/templates/performance/evaluations.html`
- Test: `performance/tests/test_performance.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `performance/tests/test_performance.py`:
```python
class TestEvaluationScore(TestCase):
    def test_rating_auto_from_score(self):
        from django.contrib.auth.models import User
        from performance.models import Evaluation
        from django.utils import timezone
        emp = User.objects.create_user('emp_sc', password='1')
        rev = User.objects.create_user('rev_sc', password='1')
        cases = [(95, 'A'), (80, 'B'), (65, 'C'), (40, 'D'), (90, 'A'), (75, 'B'), (60, 'C')]
        for score, expected in cases:
            ev = Evaluation.objects.create(
                employee=emp, reviewer=rev, status='submitted',
                score=score, evaluation_date=timezone.localdate(), content='x',
            )
            self.assertEqual(ev.rating, expected, f'score {score}')
```
Kiểm tra đầu file có `from django.test import TestCase`.

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test performance.tests.test_performance.TestEvaluationScore -v 2`
Expected: FAIL (chưa có `score`, rating không tự tính).

- [ ] **Step 3: Thêm score + save() override**

`performance/models/evaluation_model.py` — trong class `Evaluation`, thêm field sau `rating`:
```python
    score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='Điểm đánh giá thang 100 (tự suy ra xếp loại).',
    )
```
Thêm method `save` trước `def __str__`:
```python
    def save(self, *args, **kwargs):
        if self.score is not None:
            if self.score >= 90:
                self.rating = 'A'
            elif self.score >= 75:
                self.rating = 'B'
            elif self.score >= 60:
                self.rating = 'C'
            else:
                self.rating = 'D'
        super().save(*args, **kwargs)
```

- [ ] **Step 4: Tạo migration**

Run: `python manage.py makemigrations performance`
Expected: tạo `performance/migrations/0004_evaluation_score.py`.

- [ ] **Step 5: Chạy test — kỳ vọng PASS**

Run: `python manage.py test performance.tests.test_performance.TestEvaluationScore -v 2`
Expected: PASS.

- [ ] **Step 6: Form dùng score thay rating**

`performance/forms.py` — đổi `Meta.fields`:
```python
        fields = ['category', 'score', 'evaluation_date', 'content', 'evidence_reference']
```
Trong `widgets` bỏ dòng `'rating'`, thêm:
```python
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'Điểm 0-100'}),
```

- [ ] **Step 7: Service create + form_state + dict dùng score**

`performance/services/__init__.py`:

Trong `create_evaluation` đổi tham số `rating=...` thành:
```python
        score=form_data.get('score'),
```
(bỏ dòng `rating=form_data.get('rating', ''),`)

Trong `build_evaluation_form_state`:
- `form_data` mặc định (dòng ~293): đổi `'rating': ''` thành `'score': ''`.
- block đọc post_data (dòng ~315): đổi `'rating': post_data.get('rating', '').strip(),` thành `'score': post_data.get('score', '').strip(),`.
- đổi biến `rating = form_state['form_data']['rating']` thành `score = form_state['form_data']['score']`.
- đổi validate:
```python
    if not score:
        form_state['errors']['score'] = 'Vui lòng nhập điểm đánh giá.'
    else:
        try:
            score_int = int(score)
            if not (0 <= score_int <= 100):
                form_state['errors']['score'] = 'Điểm phải từ 0 đến 100.'
        except ValueError:
            form_state['errors']['score'] = 'Điểm phải là số.'
```

Trong `to_evaluation_dict` thêm key:
```python
        'score': evaluation.score,
```

- [ ] **Step 8: Template input score**

`performance/templates/performance/evaluations.html` — tìm input/select `name="rating"`, thay bằng:
```html
<input type="number" name="score" min="0" max="100" class="form-control" placeholder="Điểm 0-100" value="{{ form_state.form_data.score }}">
```
Tìm hiển thị rating trong bảng (nếu có cột rating) — giữ `rating_display`, thêm cột điểm `{{ record.score }}` nếu phù hợp.

- [ ] **Step 9: Chạy test toàn app — kỳ vọng PASS**

Run: `python manage.py test performance -v 2`
Expected: PASS (sửa test cũ nếu test cũ post `rating` — đổi sang post `score`).

- [ ] **Step 10: Checkpoint**

```bash
git add performance/
git commit -m "feat(performance): thêm điểm đánh giá 0-100, tự suy xếp loại A/B/C/D"
```

---

## Task 5: Section D — Report.status + manager_note

**Files:**
- Modify: `reports_interactions/models/report_model.py`
- Modify: `reports_interactions/views/__init__.py`
- Create: data migration
- Test: `reports_interactions/tests/test_reports_interactions.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `reports_interactions/tests/test_reports_interactions.py`:
```python
class TestReportStatus(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.author = User.objects.create_user('rauthor', password='1')
        self.mgr = User.objects.create_user('rmgr', password='1')

    def _make(self, **kw):
        from reports_interactions.models import Report
        return Report.objects.create(author=self.author, recipient=self.mgr,
                                      title='t', content='c', **kw)

    def test_default_status_submitted(self):
        r = self._make()
        self.assertEqual(r.status, 'submitted')
        self.assertTrue(r.can_edit_or_delete)

    def test_needs_update_allows_edit(self):
        r = self._make(status='needs_update')
        self.assertTrue(r.can_edit_or_delete)

    def test_acknowledged_locks(self):
        r = self._make(status='acknowledged')
        self.assertFalse(r.can_edit_or_delete)
```
Kiểm tra đầu file có `from django.test import TestCase`.

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test reports_interactions.tests.test_reports_interactions.TestReportStatus -v 2`
Expected: FAIL (chưa có `status`).

- [ ] **Step 3: Thêm status + manager_note + sửa can_edit_or_delete**

`reports_interactions/models/report_model.py` — trong class `Report`, thêm trước field `author` (hằng số) hoặc đầu class:
```python
    SUBMITTED = 'submitted'
    NEEDS_UPDATE = 'needs_update'
    ACKNOWLEDGED = 'acknowledged'
    STATUS_CHOICES = [
        (SUBMITTED, 'Đã gửi'),
        (NEEDS_UPDATE, 'Yêu cầu cập nhật'),
        (ACKNOWLEDGED, 'Đã tiếp nhận'),
    ]
```
Thêm field sau `viewed_at`:
```python
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=SUBMITTED,
        help_text='Trạng thái nghiệp vụ của báo cáo.',
    )
    manager_note = models.TextField(
        blank=True, default='',
        help_text='Phản hồi/chỉ đạo của quản lý.',
    )
```
Sửa property `can_edit_or_delete`:
```python
    @property
    def can_edit_or_delete(self):
        """Khóa chỉnh sửa khi đã được quản lý tiếp nhận (acknowledged)."""
        return self.status != self.ACKNOWLEDGED
```

- [ ] **Step 4: Tạo schema migration**

Run: `python manage.py makemigrations reports_interactions`
Expected: tạo `0005_report_status_report_manager_note.py`.

- [ ] **Step 5: Tạo data migration backfill**

Run: `python manage.py makemigrations reports_interactions --empty --name backfill_report_status`
Sửa file `0006_backfill_report_status.py` thành:
```python
from django.db import migrations


def backfill(apps, schema_editor):
    Report = apps.get_model('reports_interactions', 'Report')
    Report.objects.filter(is_viewed=True).update(status='acknowledged')
    Report.objects.filter(is_viewed=False).update(status='submitted')


class Migration(migrations.Migration):
    dependencies = [
        ('reports_interactions', '0005_report_status_report_manager_note'),
    ]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
```
(Đổi tên dependency cho khớp tên migration Step 4 thực tế.)

- [ ] **Step 6: Chạy test — kỳ vọng PASS**

Run: `python manage.py test reports_interactions.tests.test_reports_interactions.TestReportStatus -v 2`
Expected: PASS.

- [ ] **Step 7: Thêm action manager trong report_detail_view**

`reports_interactions/views/__init__.py` — trong `report_detail_view`, sau block đánh dấu is_viewed (dòng ~94-97), thêm xử lý POST:
```python
    if request.method == 'POST' and (is_recipient or is_superuser):
        action = request.POST.get('action')
        if action == 'request_update':
            report.status = report.NEEDS_UPDATE
            report.manager_note = request.POST.get('manager_note', '').strip()
            report.save(update_fields=['status', 'manager_note'])
            messages.success(request, 'Đã yêu cầu nhân viên cập nhật báo cáo.')
            return redirect('report_detail', pk=report.pk)
        elif action == 'acknowledge':
            report.status = report.ACKNOWLEDGED
            report.save(update_fields=['status'])
            messages.success(request, 'Đã tiếp nhận báo cáo.')
            return redirect('report_detail', pk=report.pk)
```
(Kiểm tra tên URL `report_detail` trong `reports_interactions/urls.py`; dùng đúng tên.)

- [ ] **Step 8: Edit/delete dùng status thay is_viewed**

`reports_interactions/views/__init__.py` — `report_view`: 2 chỗ check `not report.can_edit_or_delete` đã đúng (property mới dựa status). Khi edit thành công sau khi needs_update, reset về submitted:
Trong block `action == 'edit'` sau `form.save()` thêm:
```python
                if report.status == Report.NEEDS_UPDATE:
                    report.status = Report.SUBMITTED
                    report.save(update_fields=['status'])
```

- [ ] **Step 9: Chạy test toàn app — kỳ vọng PASS**

Run: `python manage.py test reports_interactions -v 2`
Expected: PASS.

- [ ] **Step 10: Checkpoint**

```bash
git add reports_interactions/
git commit -m "feat(reports): thêm trạng thái báo cáo + yêu cầu cập nhật/tiếp nhận"
```

---

## Task 6: Section E — ContractInfo OneToOne → ForeignKey + lịch sử + shift fields

> **Cảnh báo:** Task rủi ro cao. Chạy full suite cuối task.

**Files:**
- Modify: `contracts/models/contract_info_model.py`
- Modify: `contracts/services/__init__.py` (thêm `get_active_contract`)
- Modify: `accounts/services/account/account_info_service.py` (`ensure_contract_info`)
- Modify: `employee_profiles/services/__init__.py` (`save_contract_info_from_data`)
- Modify: `contracts/services/renewal_service.py` (`get_expiring_contracts`)
- Modify: `contracts/templates/contracts/contract.html`
- Modify: `employee_profiles/forms.py` (2 field shift)
- Test: `accounts/tests/test_register.py`, `employee_profiles/tests/test_edit_work_info.py`, `employee_profiles/tests/test_hr_create_profile.py`, `contracts/tests/test_contracts.py`

- [ ] **Step 1: Viết test thất bại cho get_active_contract**

Thêm vào `contracts/tests/test_contracts.py`:
```python
class TestContractHistory(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user('ctruser', password='1')

    def test_get_active_contract_returns_active(self):
        from contracts.models import ContractInfo
        from contracts.services import get_active_contract
        old = ContractInfo.objects.create(user=self.user, contract_number='OLD', is_active=False)
        new = ContractInfo.objects.create(user=self.user, contract_number='NEW', is_active=True)
        self.assertEqual(get_active_contract(self.user), new)

    def test_user_can_have_multiple_contracts(self):
        from contracts.models import ContractInfo
        ContractInfo.objects.create(user=self.user, contract_number='C1', is_active=False)
        ContractInfo.objects.create(user=self.user, contract_number='C2', is_active=True)
        self.assertEqual(self.user.contracts.count(), 2)
```
Kiểm tra đầu file có `from django.test import TestCase`.

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test contracts.tests.test_contracts.TestContractHistory -v 2`
Expected: FAIL (OneToOne không cho 2 HĐ; chưa có `is_active`/`get_active_contract`).

- [ ] **Step 3: Đổi model sang ForeignKey + thêm fields**

`contracts/models/contract_info_model.py` — đổi field `user`:
```python
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contracts',
        help_text="Nhân viên sở hữu hợp đồng này.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Hợp đồng đang hiệu lực?",
    )
```
Thêm 2 field shift sau `contract_standard_shift`:
```python
    shift_start_time = models.TimeField(
        null=True, blank=True,
        help_text="Giờ bắt đầu ca (đi trễ tính từ đây).",
    )
    shift_end_time = models.TimeField(
        null=True, blank=True,
        help_text="Giờ kết thúc ca (về sớm tính từ đây).",
    )
```
Sửa docstring class: bỏ "OneToOne", ghi "1 User → N ContractInfo, 1 HĐ active tại 1 thời điểm".

- [ ] **Step 4: Tạo migration**

Run: `python manage.py makemigrations contracts`
Expected: tạo `0002_...` đổi OneToOne→FK + add is_active + shift fields. Dữ liệu cũ giữ `is_active=True` (default).

- [ ] **Step 5: Thêm get_active_contract**

`contracts/services/__init__.py` — thêm cuối file:
```python
def get_active_contract(user):
    """Trả hợp đồng đang hiệu lực (is_active=True) mới nhất, hoặc None."""
    return user.contracts.filter(is_active=True).order_by('-id').first()
```

- [ ] **Step 6: Sửa ensure_contract_info**

`accounts/services/account/account_info_service.py` — sửa hàm:
```python
def ensure_contract_info(user):
    """Trả HĐ active của user, tạo mới nếu chưa có HĐ nào active."""
    from contracts.models import ContractInfo
    active = user.contracts.filter(is_active=True).order_by('-id').first()
    if active:
        return active
    return ContractInfo.objects.create(user=user, is_active=True)
```

- [ ] **Step 7: Chạy test — kỳ vọng PASS**

Run: `python manage.py test contracts.tests.test_contracts.TestContractHistory -v 2`
Expected: PASS.

- [ ] **Step 8: Sửa save_contract_info_from_data (lưu thêm shift)**

`employee_profiles/services/__init__.py` — trong `save_contract_info_from_data`, trước `contract_info.save()` thêm:
```python
    contract_info.shift_start_time = data.get('shift_start_time') or None
    contract_info.shift_end_time = data.get('shift_end_time') or None
```

- [ ] **Step 9: Sửa renewal_service lọc is_active**

`contracts/services/renewal_service.py` — trong `get_expiring_contracts`, đổi dòng query:
```python
    all_contracts = ContractInfo.objects.select_related('user').filter(
        is_active=True,
    ).exclude(contract_end_date='')
```

- [ ] **Step 10: Sửa template contract.html**

`contracts/templates/contracts/contract.html` — thay mọi `request.user.contract_info.X` bằng `contract_info.X` (view `contract` đã truyền context `contract_info` qua `build_contract_page_context`? Kiểm tra view). Nếu view chưa truyền instance, thêm vào context: `'contract_info': get_active_contract(request.user)`.

Kiểm tra view contracts: `contracts/views/__init__.py`. Nếu render `contract.html`, đảm bảo context có `contract_info`.

- [ ] **Step 11: Thêm 2 input shift vào EmployeeProfileForm**

`employee_profiles/forms.py` — sau field `contract_standard_shift` (dòng ~159) thêm:
```python
    shift_start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    shift_end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
```

- [ ] **Step 12: Sửa 3 test cũ dùng ContractInfo**

Kiểm tra & sửa:
- `accounts/tests/test_register.py:45` — `ContractInfo.objects.filter(user=user).exists()` vẫn đúng (FK), giữ nguyên. Thêm assert chỉ 1 active: `self.assertEqual(user.contracts.filter(is_active=True).count(), 1)`.
- `employee_profiles/tests/test_edit_work_info.py:26` — `ContractInfo.objects.create(user=self.normal_user)` OK với FK. Giữ. Nếu test refresh `self.contract_info` — vẫn OK.
- `employee_profiles/tests/test_hr_create_profile.py:63` — `ContractInfo.objects.filter(user=user).first()` OK.

- [ ] **Step 13: Chạy FULL suite — kỳ vọng PASS**

Run: `python manage.py test -v 1`
Expected: PASS toàn bộ. Sửa các lỗi do OneToOne→FK (chỗ nào dùng `user.contract_info` còn sót → đổi sang `get_active_contract(user)`).

- [ ] **Step 14: Checkpoint**

```bash
git add contracts/ accounts/ employee_profiles/
git commit -m "feat(contracts): lưu lịch sử hợp đồng (FK + is_active) và giờ ca làm có cấu trúc"
```

---

## Task 7: Section F0 — Giờ trễ/về sớm từ hợp đồng

**Files:**
- Modify: `business_web/settings.py:159`
- Modify: `contracts/services/__init__.py` (`get_shift_times`)
- Modify: `attendance/services/record/attendance_logging_service.py` (`classify_status`, `record_check_in`, `record_check_out`)
- Test: `attendance/tests/test_attendance_view.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `attendance/tests/test_attendance_view.py`:
```python
class TestShiftClassify(TestCase):
    def test_classify_status(self):
        from datetime import time
        from attendance.services.record.attendance_logging_service import classify_status
        ss, se = time(8, 30), time(17, 30)
        # đúng giờ vào, ra đủ giờ
        self.assertEqual(classify_status(time(8, 30), time(17, 30), ss, se), 'on_time')
        # vào trễ (sau 8:35 do grace 5')
        self.assertEqual(classify_status(time(9, 0), time(17, 30), ss, se), 'late')
        # về sớm
        self.assertEqual(classify_status(time(8, 30), time(16, 0), ss, se), 'early_leave')
        # chưa check-out
        self.assertEqual(classify_status(time(8, 30), None, ss, se), 'on_time')

    def test_get_shift_times_fallback(self):
        from django.contrib.auth.models import User
        from contracts.services import get_shift_times
        from django.conf import settings
        u = User.objects.create_user('noshift', password='1')
        start, end = get_shift_times(u)
        self.assertEqual(start, settings.WORK_START_TIME)
        self.assertEqual(end, settings.WORK_END_TIME)
```
Kiểm tra đầu file có `from django.test import TestCase`.

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test attendance.tests.test_attendance_view.TestShiftClassify -v 2`
Expected: FAIL (`classify_status`, `get_shift_times`, `WORK_END_TIME` chưa có).

- [ ] **Step 3: Thêm WORK_END_TIME settings**

`business_web/settings.py` — sau dòng `WORK_START_TIME = _time(8, 30)` (159) thêm:
```python
WORK_END_TIME = _time(17, 30)
```

- [ ] **Step 4: Thêm get_shift_times**

`contracts/services/__init__.py` — thêm import đầu file nếu cần `from django.conf import settings`; thêm hàm:
```python
def get_shift_times(user):
    """Trả (shift_start, shift_end) từ HĐ active, fallback settings."""
    from django.conf import settings
    contract = get_active_contract(user)
    start = (contract.shift_start_time if contract and contract.shift_start_time
             else settings.WORK_START_TIME)
    end = (contract.shift_end_time if contract and contract.shift_end_time
           else settings.WORK_END_TIME)
    return start, end
```

- [ ] **Step 5: Thêm classify_status + dùng trong check-in/out**

`attendance/services/record/attendance_logging_service.py` — thêm hàm sau `_classify_check_in_status`:
```python
def classify_status(check_in_time, check_out_time, shift_start, shift_end):
    """Phân loại bản ghi: late nếu vào trễ, early_leave nếu ra sớm, else on_time."""
    grace = timedelta(minutes=settings.WORK_LATE_GRACE_MIN)
    today = date.today()
    in_limit = (datetime.combine(today, shift_start) + grace).time()
    status = 'late' if check_in_time and check_in_time > in_limit else 'on_time'
    if check_out_time and check_out_time < shift_end:
        status = 'early_leave'
    return status
```
Sửa `record_check_in` — đổi dùng shift từ HĐ:
```python
def record_check_in(user, now=None) -> AttendanceRecord:
    from contracts.services import get_shift_times
    today = timezone.localdate()
    now_time = (now or timezone.localtime()).time()
    rec, _ = AttendanceRecord.objects.get_or_create(user=user, record_date=today)
    if rec.check_in_time is None:
        shift_start, shift_end = get_shift_times(user)
        rec.check_in_time = now_time
        rec.status = classify_status(now_time, rec.check_out_time, shift_start, shift_end)
        rec.save(update_fields=['check_in_time', 'status'])
        logger.info('check_in user=%s time=%s status=%s', user.id, now_time, rec.status)
    return rec
```
Sửa `record_check_out` — phân loại early_leave:
```python
def record_check_out(user, now=None) -> AttendanceRecord:
    from contracts.services import get_shift_times
    today = timezone.localdate()
    now_time = (now or timezone.localtime()).time()
    rec, _ = AttendanceRecord.objects.get_or_create(user=user, record_date=today)
    if rec.check_out_time is None:
        shift_start, shift_end = get_shift_times(user)
        rec.check_out_time = now_time
        rec.status = classify_status(rec.check_in_time, now_time, shift_start, shift_end)
        rec.save(update_fields=['check_out_time', 'status'])
        logger.info('check_out user=%s time=%s status=%s', user.id, now_time, rec.status)
    return rec
```
(Lưu ý: thêm `now=None` param đã chuẩn bị sẵn cho Task 9/Section G.)

- [ ] **Step 6: Chạy test — kỳ vọng PASS**

Run: `python manage.py test attendance.tests.test_attendance_view.TestShiftClassify -v 2`
Expected: PASS.

- [ ] **Step 7: Chạy full attendance — kỳ vọng PASS**

Run: `python manage.py test attendance -v 1`
Expected: PASS (test check-out cũ giờ có thể set early_leave — kiểm tra & cập nhật assertion nếu cần).

- [ ] **Step 8: Checkpoint**

```bash
git add business_web/settings.py contracts/ attendance/
git commit -m "feat(attendance): tính đi trễ/về sớm theo giờ ca trong hợp đồng"
```

---

## Task 8: Section F — HR duyệt/từ chối điều chỉnh chấm công

**Files:**
- Create: `attendance/services/record/adjustment_review_service.py`
- Create: `attendance/views/adjustment/adjustment_review_view.py`
- Modify: `attendance/views/__init__.py`
- Modify: `attendance/urls.py`
- Create: `attendance/templates/attendance/adjustment/adjustment_review.html`
- Test: `attendance/tests/test_adjustment.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `attendance/tests/test_adjustment.py`:
```python
class TestAdjustmentReview(TestCase):
    def setUp(self):
        from accounts.models import Role, UserProfile
        self.hr = User.objects.create_user('hruser', password='1')
        hr_role, _ = Role.objects.get_or_create(name='hr')
        UserProfile.objects.create(user=self.hr, role=hr_role, employee_id='HR01')
        self.emp = User.objects.create_user('empadj', password='1')
        today = timezone.localdate()
        self.record = AttendanceRecord.objects.create(
            user=self.emp, record_date=today - timedelta(days=1),
            check_in_time=timezone.now().replace(hour=8, minute=0).time(),
            status='pending_adjustment',
        )
        self.adj = AttendanceAdjustmentRequest.objects.create(
            record=self.record, submitted_by=self.emp, reason='forgot',
            claimed_check_out_time='17:30', status='pending',
        )

    def test_hr_approve_sets_checkout_and_status(self):
        from attendance.services.record.adjustment_review_service import approve_adjustment
        ok, _ = approve_adjustment(self.hr, self.adj.id, 'Đồng ý')
        self.assertTrue(ok)
        self.adj.refresh_from_db(); self.record.refresh_from_db()
        self.assertEqual(self.adj.status, 'approved')
        self.assertEqual(self.adj.reviewed_by, self.hr)
        self.assertEqual(self.record.check_out_time.strftime('%H:%M'), '17:30')
        self.assertEqual(self.record.status, 'on_time')

    def test_hr_reject_resets_record(self):
        from attendance.services.record.adjustment_review_service import reject_adjustment
        ok, _ = reject_adjustment(self.hr, self.adj.id, 'Thiếu chứng từ')
        self.assertTrue(ok)
        self.adj.refresh_from_db(); self.record.refresh_from_db()
        self.assertEqual(self.adj.status, 'rejected')
        self.assertEqual(self.record.status, 'no_checkout')

    def test_non_hr_cannot_access_review(self):
        self.client.force_login(self.emp)
        resp = self.client.get(reverse('attendance_adjustment_review'))
        self.assertEqual(resp.status_code, 302)
```
Kiểm tra đầu file có `reverse` import (thêm `from django.urls import reverse` nếu thiếu).

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test attendance.tests.test_adjustment.TestAdjustmentReview -v 2`
Expected: FAIL (service/url chưa có).

- [ ] **Step 3: Tạo service**

Create `attendance/services/record/adjustment_review_service.py`:
```python
"""HR-side review (approve/reject) cho yêu cầu điều chỉnh chấm công."""
from django.db import transaction
from django.utils import timezone

from attendance.models import AttendanceAdjustmentRequest
from attendance.services.record.attendance_logging_service import classify_status
from contracts.services import get_shift_times


def get_pending_adjustments():
    """Tất cả yêu cầu đang chờ HR duyệt."""
    return (AttendanceAdjustmentRequest.objects
            .filter(status='pending')
            .select_related('record', 'submitted_by')
            .order_by('-submitted_at'))


def get_reviewed_adjustments():
    """Lịch sử đã duyệt/từ chối."""
    return (AttendanceAdjustmentRequest.objects
            .exclude(status='pending')
            .select_related('record', 'submitted_by', 'reviewed_by')
            .order_by('-reviewed_at'))


def approve_adjustment(hr_user, adj_id, hr_note=''):
    try:
        adj = AttendanceAdjustmentRequest.objects.select_related('record').get(id=adj_id)
    except AttendanceAdjustmentRequest.DoesNotExist:
        return False, 'Không tìm thấy yêu cầu.'
    if adj.status != 'pending':
        return False, 'Yêu cầu đã được xử lý.'
    with transaction.atomic():
        record = adj.record
        record.check_out_time = adj.claimed_check_out_time
        shift_start, shift_end = get_shift_times(record.user)
        record.status = classify_status(
            record.check_in_time, record.check_out_time, shift_start, shift_end,
        )
        record.save(update_fields=['check_out_time', 'status'])
        adj.status = 'approved'
        adj.reviewed_by = hr_user
        adj.reviewed_at = timezone.now()
        adj.hr_note = (hr_note or '').strip()
        adj.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_note'])
    return True, 'Đã duyệt yêu cầu điều chỉnh.'


def reject_adjustment(hr_user, adj_id, hr_note=''):
    try:
        adj = AttendanceAdjustmentRequest.objects.select_related('record').get(id=adj_id)
    except AttendanceAdjustmentRequest.DoesNotExist:
        return False, 'Không tìm thấy yêu cầu.'
    if adj.status != 'pending':
        return False, 'Yêu cầu đã được xử lý.'
    with transaction.atomic():
        record = adj.record
        record.status = 'no_checkout'
        record.save(update_fields=['status'])
        adj.status = 'rejected'
        adj.reviewed_by = hr_user
        adj.reviewed_at = timezone.now()
        adj.hr_note = (hr_note or '').strip()
        adj.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_note'])
    return True, 'Đã từ chối yêu cầu điều chỉnh.'
```

- [ ] **Step 4: Tạo view**

Create `attendance/views/adjustment/adjustment_review_view.py`:
```python
"""HR review trang điều chỉnh chấm công."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.services.permission.role_service import is_hr_user
from attendance.services.record.adjustment_review_service import (
    approve_adjustment, get_pending_adjustments, get_reviewed_adjustments,
    reject_adjustment,
)


@login_required
def adjustment_review_view(request):
    if not is_hr_user(request.user):
        messages.error(request, 'Bạn không có quyền duyệt điều chỉnh chấm công.')
        return redirect('attendance')
    return render(request, 'attendance/adjustment/adjustment_review.html', {
        'active_page': 'attendance',
        'pending': get_pending_adjustments(),
        'reviewed': get_reviewed_adjustments(),
    })


@login_required
@require_POST
def adjustment_approve_action(request, adj_id):
    if not is_hr_user(request.user):
        messages.error(request, 'Không có quyền.')
        return redirect('attendance')
    ok, msg = approve_adjustment(request.user, adj_id, request.POST.get('hr_note', ''))
    (messages.success if ok else messages.error)(request, msg)
    return redirect('attendance_adjustment_review')


@login_required
@require_POST
def adjustment_reject_action(request, adj_id):
    if not is_hr_user(request.user):
        messages.error(request, 'Không có quyền.')
        return redirect('attendance')
    ok, msg = reject_adjustment(request.user, adj_id, request.POST.get('hr_note', ''))
    (messages.success if ok else messages.error)(request, msg)
    return redirect('attendance_adjustment_review')
```

- [ ] **Step 5: Export views**

`attendance/views/__init__.py` — thêm import + __all__:
```python
from attendance.views.adjustment.adjustment_review_view import (
    adjustment_approve_action,
    adjustment_reject_action,
    adjustment_review_view,
)
```
Thêm vào `__all__`: `"adjustment_review_view"`, `"adjustment_approve_action"`, `"adjustment_reject_action"`.

- [ ] **Step 6: Thêm URLs**

`attendance/urls.py` — thêm import 3 view vào block `from attendance.views import (...)` và thêm paths:
```python
    path('attendance/adjustments/review/', adjustment_review_view, name='attendance_adjustment_review'),
    path('attendance/adjustments/<int:adj_id>/approve/', adjustment_approve_action, name='attendance_adjustment_approve'),
    path('attendance/adjustments/<int:adj_id>/reject/', adjustment_reject_action, name='attendance_adjustment_reject'),
```

- [ ] **Step 7: Tạo template**

Create `attendance/templates/attendance/adjustment/adjustment_review.html`:
```html
{% extends 'base.html' %}
{% block content %}
<div class="container">
  <h2>Duyệt điều chỉnh chấm công</h2>

  <h3>Đang chờ duyệt</h3>
  <table class="table">
    <thead><tr><th>Nhân viên</th><th>Ngày</th><th>Lý do</th><th>Giờ ra khai báo</th><th>Minh chứng</th><th></th></tr></thead>
    <tbody>
    {% for adj in pending %}
      <tr>
        <td>{{ adj.submitted_by.username }}</td>
        <td>{{ adj.record.record_date }}</td>
        <td>{{ adj.get_reason_display }} — {{ adj.reason_detail }}</td>
        <td>{{ adj.claimed_check_out_time|time:"H:i" }}</td>
        <td>{% if adj.evidence %}<a href="{{ adj.evidence.url }}" target="_blank">Xem</a>{% else %}—{% endif %}</td>
        <td>
          <form method="post" action="{% url 'attendance_adjustment_approve' adj.id %}" style="display:inline">
            {% csrf_token %}
            <input type="text" name="hr_note" placeholder="Ghi chú">
            <button type="submit">Duyệt</button>
          </form>
          <form method="post" action="{% url 'attendance_adjustment_reject' adj.id %}" style="display:inline">
            {% csrf_token %}
            <input type="text" name="hr_note" placeholder="Lý do từ chối">
            <button type="submit">Từ chối</button>
          </form>
        </td>
      </tr>
    {% empty %}
      <tr><td colspan="6">Không có yêu cầu chờ duyệt.</td></tr>
    {% endfor %}
    </tbody>
  </table>

  <h3>Đã xử lý</h3>
  <table class="table">
    <thead><tr><th>Nhân viên</th><th>Ngày</th><th>Trạng thái</th><th>HR</th><th>Ghi chú</th></tr></thead>
    <tbody>
    {% for adj in reviewed %}
      <tr>
        <td>{{ adj.submitted_by.username }}</td>
        <td>{{ adj.record.record_date }}</td>
        <td>{{ adj.get_status_display }}</td>
        <td>{{ adj.reviewed_by.username|default:"—" }}</td>
        <td>{{ adj.hr_note|default:"—" }}</td>
      </tr>
    {% empty %}
      <tr><td colspan="5">Chưa có.</td></tr>
    {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
```
(Kiểm tra tên base template — dự án dùng `base.html` hay tên khác; sửa `{% extends %}` cho khớp template hiện có.)

- [ ] **Step 8: Chạy test — kỳ vọng PASS**

Run: `python manage.py test attendance.tests.test_adjustment -v 2`
Expected: PASS.

- [ ] **Step 9: Checkpoint**

```bash
git add attendance/
git commit -m "feat(attendance): HR duyệt/từ chối yêu cầu điều chỉnh chấm công"
```

---

## Task 9: Section G — Bắt giờ lúc request đến server

**Files:**
- Modify: `attendance/views/face/face_attendance_view.py`
- Test: `attendance/tests/test_face_check.py`

> `record_check_in`/`record_check_out` đã nhận `now=None` từ Task 7. Task này chỉ truyền giờ từ view.

- [ ] **Step 1: Viết test thất bại**

Thêm vào `attendance/tests/test_face_check.py`:
```python
class TestRequestTimeCapture(TestCase):
    def test_check_in_uses_passed_now(self):
        from django.contrib.auth.models import User
        from datetime import datetime
        from django.utils import timezone as tz
        from attendance.services.record.attendance_logging_service import record_check_in
        u = User.objects.create_user('nowuser', password='1')
        fixed = tz.make_aware(datetime(2026, 6, 1, 7, 59, 0))
        rec = record_check_in(u, now=fixed)
        self.assertEqual(rec.check_in_time.strftime('%H:%M'), '07:59')
```
Kiểm tra đầu file có `from django.test import TestCase`.

- [ ] **Step 2: Chạy test — kỳ vọng PASS hoặc FAIL**

Run: `python manage.py test attendance.tests.test_face_check.TestRequestTimeCapture -v 2`
Expected: PASS (vì Task 7 đã thêm `now`). Nếu Task 7 chưa làm → FAIL, quay lại Task 7.

- [ ] **Step 3: View bắt giờ đầu request và truyền xuống**

`attendance/views/face/face_attendance_view.py` — trong `face_check_view`, thêm dòng đầu (ngay sau `def face_check_view(request):`, trước comment lockout):
```python
    request_time = timezone.localtime()
```
Sửa block success (dòng ~96-100):
```python
        if action == 'check_in':
            record_check_in(request.user, now=request_time)
        elif action == 'check_out':
            record_check_out(request.user, now=request_time)
```

- [ ] **Step 4: Test mô phỏng verify chậm không ảnh hưởng giờ**

Thêm test vào `attendance/tests/test_face_check.py`:
```python
    def test_slow_verify_does_not_shift_time(self):
        # giờ bắt ở đầu view → không phụ thuộc thời gian verify
        # kiểm tra qua service: record_check_in dùng now truyền vào, không gọi localtime
        from django.contrib.auth.models import User
        from datetime import datetime
        from django.utils import timezone as tz
        from attendance.services.record.attendance_logging_service import record_check_in
        u = User.objects.create_user('slowuser', password='1')
        early = tz.make_aware(datetime(2026, 6, 1, 8, 0, 0))
        rec = record_check_in(u, now=early)
        self.assertEqual(rec.check_in_time.strftime('%H:%M'), '08:00')
```

- [ ] **Step 5: Chạy test + full attendance — kỳ vọng PASS**

Run: `python manage.py test attendance -v 1`
Expected: PASS.

- [ ] **Step 6: Checkpoint**

```bash
git add attendance/
git commit -m "feat(attendance): bắt giờ chấm công lúc request đến server (chống nhận diện chậm)"
```

---

## Task 10: Verification cuối

- [ ] **Step 1: Full suite**

Run: `python manage.py test -v 1`
Expected: PASS toàn bộ.

- [ ] **Step 2: Migration check**

Run: `python manage.py makemigrations --check --dry-run`
Expected: "No changes detected".

- [ ] **Step 3: Checkpoint cuối**

Báo người dùng tổng kết: tất cả section A–G hoàn tất, test pass. Hỏi có muốn cập nhật `walkthrough__1_.md` ghi các tính năng mới (score, report status, contract history, shift, HR adjustment) không.

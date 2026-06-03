# Contract Versioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mỗi lần điều chỉnh hợp đồng tạo một bản `ContractInfo` mới (giữ HĐ cũ archived), và thêm trang lịch sử để HR xem mọi nhân viên / nhân viên xem của chính mình.

**Architecture:** Versioning bằng cách archive HĐ active (`is_active=False`) rồi tạo bản mới copy-forward toàn bộ field + áp field sửa, trong một transaction. Hai view mới (điều chỉnh HĐ, lịch sử HĐ) + form riêng. Gỡ field HĐ khỏi form hồ sơ chung để chỉ còn một đường ghi.

**Tech Stack:** Django 4.2, SQLite, Django test framework (`manage.py test`).

**Lưu ý chạy lệnh:** mọi lệnh `python manage.py ...` chạy từ thư mục `business_web/` (nơi chứa `manage.py`).

---

### Task 1: Thêm field `created_at` cho ContractInfo

**Files:**
- Modify: `business_web/contracts/models/contract_info_model.py`
- Create: `business_web/contracts/migrations/0003_contractinfo_created_at.py` (qua makemigrations)

- [ ] **Step 1: Thêm field vào model**

Trong `contracts/models/contract_info_model.py`, ngay sau field `is_active` (dòng ~16-19) thêm:

```python
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Thời điểm tạo bản HĐ này (dùng cho lịch sử).",
    )
```

(`null=True` để các row HĐ đã tồn tại không vỡ migration; bản mới luôn có giá trị nhờ `auto_now_add`.)

- [ ] **Step 2: Tạo migration**

Run: `python manage.py makemigrations contracts`
Expected: `Migrations for 'contracts': 0003_contractinfo_created_at.py - Add field created_at to contractinfo`

- [ ] **Step 3: Áp migration**

Run: `python manage.py migrate contracts`
Expected: `Applying contracts.0003_contractinfo_created_at... OK`

- [ ] **Step 4: Commit**

```bash
git add business_web/contracts/models/contract_info_model.py business_web/contracts/migrations/0003_contractinfo_created_at.py
git commit -m "feat(contracts): them created_at cho ContractInfo (lich su HD)"
```

---

### Task 2: Service `adjust_contract` + `get_contract_history`

**Files:**
- Modify: `business_web/contracts/services/__init__.py`
- Test: `business_web/contracts/tests/test_contract_versioning.py` (tạo mới)

- [ ] **Step 1: Viết test thất bại**

Tạo `business_web/contracts/tests/test_contract_versioning.py`:

```python
"""Test versioning hợp đồng: adjust_contract + get_contract_history."""
from django.test import TestCase
from django.contrib.auth.models import User

from contracts.models import ContractInfo
from contracts.services import adjust_contract, get_contract_history
from accounts.services import ensure_contract_info


class AdjustContractTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='nv001', password='x')
        contract = ensure_contract_info(self.user)
        contract.contract_number = 'HD-2026-001'
        contract.contract_type = 'Thử việc 2 tháng'
        contract.contract_annual_leave_days = 12
        contract.save()

    def test_adjust_creates_new_active_and_archives_old(self):
        adjust_contract(self.user, {'contract_type': 'Chính thức 1 năm'})
        contracts = ContractInfo.objects.filter(user=self.user)
        self.assertEqual(contracts.count(), 2)
        self.assertEqual(contracts.filter(is_active=True).count(), 1)
        self.assertEqual(contracts.filter(is_active=False).count(), 1)

    def test_unchanged_fields_carry_forward(self):
        new = adjust_contract(self.user, {'contract_type': 'Chính thức 1 năm'})
        self.assertEqual(new.contract_type, 'Chính thức 1 năm')   # field sửa
        self.assertEqual(new.contract_number, 'HD-2026-001')      # carry-forward
        self.assertEqual(new.contract_annual_leave_days, 12)      # carry-forward
        self.assertTrue(new.is_active)

    def test_ensure_contract_info_returns_new_version(self):
        new = adjust_contract(self.user, {'contract_number': 'HD-2026-002'})
        self.assertEqual(ensure_contract_info(self.user).pk, new.pk)

    def test_history_lists_all_newest_first(self):
        adjust_contract(self.user, {'contract_number': 'HD-2026-002'})
        history = list(get_contract_history(self.user))
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].contract_number, 'HD-2026-002')  # mới nhất trước
        self.assertEqual(history[1].contract_number, 'HD-2026-001')
```

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test contracts.tests.test_contract_versioning -v 2`
Expected: FAIL — `ImportError: cannot import name 'adjust_contract'`

- [ ] **Step 3: Implement service**

Trong `contracts/services/__init__.py`, thêm cuối file:

```python
# ----- Versioning hợp đồng -----

CONTRACT_VERSION_FIELDS = [
    'contract_number', 'contract_type', 'contract_signed_date',
    'contract_start_date', 'contract_end_date', 'contract_annual_leave_days',
    'contract_standard_shift', 'shift_start_time', 'shift_end_time',
    'contract_attachment_reference',
]


def adjust_contract(user, data):
    """Tạo phiên bản HĐ mới từ HĐ active hiện tại + field sửa.

    Archive HĐ active cũ (is_active=False) và tạo HĐ mới copy-forward toàn bộ
    field rồi ghi đè các field có trong `data`. Nguyên tử trong transaction.
    Trả về HĐ mới.
    """
    from django.db import transaction
    from contracts.models import ContractInfo
    from accounts.services import ensure_contract_info

    with transaction.atomic():
        old = ensure_contract_info(user)
        new_values = {f: getattr(old, f) for f in CONTRACT_VERSION_FIELDS}
        for f in CONTRACT_VERSION_FIELDS:
            if f in data:
                new_values[f] = data[f]
        old.is_active = False
        old.save(update_fields=['is_active'])
        return ContractInfo.objects.create(user=user, is_active=True, **new_values)


def get_contract_history(user):
    """Mọi phiên bản HĐ của user (active + archived), mới nhất trước."""
    return user.contracts.order_by('-created_at', '-id')
```

- [ ] **Step 4: Chạy test — kỳ vọng PASS**

Run: `python manage.py test contracts.tests.test_contract_versioning -v 2`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add business_web/contracts/services/__init__.py business_web/contracts/tests/test_contract_versioning.py
git commit -m "feat(contracts): adjust_contract + get_contract_history"
```

---

### Task 3: `ContractAdjustForm`

**Files:**
- Modify: `business_web/contracts/forms.py`
- Test: `business_web/contracts/tests/test_contract_versioning.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `test_contract_versioning.py`:

```python
from contracts.forms import ContractAdjustForm


class ContractAdjustFormTests(TestCase):
    BASE = {
        'contract_number': 'HD-2026-001',
        'contract_type': 'Chính thức',
        'contract_signed_date': '01/05/2026',
        'contract_start_date': '05/05/2026',
        'contract_end_date': '05/05/2027',
        'contract_annual_leave_days': 12,
        'contract_standard_shift': '08:30 - 17:30',
        'contract_attachment_reference': '',
    }

    def test_valid_form(self):
        self.assertTrue(ContractAdjustForm(data=self.BASE).is_valid())

    def test_bad_date_format_invalid(self):
        data = {**self.BASE, 'contract_signed_date': '2026-05-01'}
        form = ContractAdjustForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('contract_signed_date', form.errors)

    def test_wrong_date_order_invalid(self):
        data = {**self.BASE, 'contract_start_date': '01/04/2026'}  # trước ngày ký
        form = ContractAdjustForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('contract_start_date', form.errors)
```

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test contracts.tests.test_contract_versioning.ContractAdjustFormTests -v 2`
Expected: FAIL — `ImportError: cannot import name 'ContractAdjustForm'`

- [ ] **Step 3: Implement form**

Thay toàn bộ nội dung `contracts/forms.py`:

```python
"""Forms cho contracts."""
import re

from django import forms

from contracts.services import validate_contract_date_order


class ContractAdjustForm(forms.Form):
    """Form điều chỉnh hợp đồng — chỉ field HĐ. Mỗi lần lưu = 1 phiên bản mới."""

    contract_number = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: HD-2026-001'}),
    )
    contract_type = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Chính thức 1 năm'}),
    )
    contract_signed_date = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 01/05/2026'}),
    )
    contract_start_date = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 05/05/2026'}),
    )
    contract_end_date = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 05/05/2027'}),
    )
    contract_annual_leave_days = forms.IntegerField(
        required=False, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'VD: 12'}),
    )
    contract_standard_shift = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 08:30 - 17:30'}),
    )
    shift_start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    shift_end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    contract_attachment_reference = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: HD_NV001.pdf'}),
    )

    def clean(self):
        cleaned_data = super().clean()

        date_pattern = re.compile(r'^\d{2}/\d{2}/\d{4}$')
        date_fields = ['contract_signed_date', 'contract_start_date', 'contract_end_date']
        bad_format = False
        for field_name in date_fields:
            value = cleaned_data.get(field_name)
            if value and not date_pattern.match(value.strip()):
                self.add_error(field_name, 'Định dạng ngày phải là DD/MM/YYYY.')
                bad_format = True

        if not bad_format:
            order_errors = validate_contract_date_order(
                cleaned_data.get('contract_signed_date'),
                cleaned_data.get('contract_start_date'),
                cleaned_data.get('contract_end_date'),
            )
            for err in order_errors:
                if 'phải từ ngày ký' in err:
                    self.add_error('contract_start_date', err)
                elif 'từ ngày bắt đầu' in err:
                    self.add_error('contract_end_date', err)

        return cleaned_data
```

- [ ] **Step 4: Chạy test — kỳ vọng PASS**

Run: `python manage.py test contracts.tests.test_contract_versioning.ContractAdjustFormTests -v 2`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add business_web/contracts/forms.py business_web/contracts/tests/test_contract_versioning.py
git commit -m "feat(contracts): ContractAdjustForm voi validate ngay"
```

---

### Task 4: Views điều chỉnh + lịch sử và URLs

**Files:**
- Create: `business_web/contracts/views/contract_versioning_view.py`
- Modify: `business_web/contracts/views/__init__.py`
- Modify: `business_web/contracts/urls.py`
- Test: `business_web/contracts/tests/test_contract_versioning.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `test_contract_versioning.py`:

```python
from django.urls import reverse
from accounts.models import Role, UserProfile


def _set_role(user, role_name):
    role, _ = Role.objects.get_or_create(name=role_name)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.role = role
    profile.save()


class ContractViewsTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(username='emp', password='x')
        _set_role(self.employee, Role.EMPLOYEE)
        ensure_contract_info(self.employee)

        self.other = User.objects.create_user(username='other', password='x')
        _set_role(self.other, Role.EMPLOYEE)

        self.hr = User.objects.create_user(username='hr', password='x')
        _set_role(self.hr, Role.HR)

    def test_hr_adjust_creates_version(self):
        self.client.force_login(self.hr)
        url = reverse('hr_adjust_contract', args=[self.employee.id])
        resp = self.client.post(url, {
            'contract_number': 'HD-2026-009',
            'contract_annual_leave_days': 12,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(ContractInfo.objects.filter(user=self.employee).count(), 2)

    def test_owner_can_view_history(self):
        self.client.force_login(self.employee)
        resp = self.client.get(reverse('contract_history', args=[self.employee.id]))
        self.assertEqual(resp.status_code, 200)

    def test_employee_cannot_view_others_history(self):
        self.client.force_login(self.employee)
        resp = self.client.get(reverse('contract_history', args=[self.other.id]))
        self.assertEqual(resp.status_code, 302)  # bị chặn, redirect

    def test_hr_can_view_any_history(self):
        self.client.force_login(self.hr)
        resp = self.client.get(reverse('contract_history', args=[self.employee.id]))
        self.assertEqual(resp.status_code, 200)
```

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test contracts.tests.test_contract_versioning.ContractViewsTests -v 2`
Expected: FAIL — `NoReverseMatch: 'hr_adjust_contract' is not a valid view function or pattern name`

- [ ] **Step 3: Tạo views**

Tạo `business_web/contracts/views/contract_versioning_view.py`:

```python
"""Views điều chỉnh hợp đồng (tạo phiên bản mới) và xem lịch sử HĐ."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from accounts.services import (
    ensure_profile, ensure_contract_info,
    is_admin_user, is_hr_user, can_manage_work_info,
)
from contracts.forms import ContractAdjustForm
from contracts.services import adjust_contract, get_contract_history


@login_required
@user_passes_test(can_manage_work_info)
def hr_adjust_contract_view(request, user_id):
    """HR/Admin điều chỉnh HĐ — mỗi lần lưu tạo một phiên bản mới."""
    if is_admin_user(request.user):
        messages.error(request, 'Tài khoản Admin không có quyền điều chỉnh hợp đồng.')
        return redirect('user_list')

    target_user = get_object_or_404(User, pk=user_id)
    ensure_profile(target_user)
    contract = ensure_contract_info(target_user)

    if request.method == 'POST':
        form = ContractAdjustForm(request.POST)
        if form.is_valid():
            adjust_contract(target_user, form.cleaned_data)
            messages.success(request, f'Đã tạo phiên bản hợp đồng mới cho "{target_user.username}".')
            return redirect('contract_history', user_id=target_user.pk)
    else:
        form = ContractAdjustForm(initial={
            'contract_number': contract.contract_number,
            'contract_type': contract.contract_type,
            'contract_signed_date': contract.contract_signed_date,
            'contract_start_date': contract.contract_start_date,
            'contract_end_date': contract.contract_end_date,
            'contract_annual_leave_days': contract.contract_annual_leave_days,
            'contract_standard_shift': contract.contract_standard_shift,
            'shift_start_time': contract.shift_start_time,
            'shift_end_time': contract.shift_end_time,
            'contract_attachment_reference': contract.contract_attachment_reference,
        })

    return render(request, 'contracts/hr_adjust_contract.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
    })


@login_required
def contract_history_view(request, user_id):
    """Lịch sử HĐ. HR/superuser xem mọi người; nhân viên xem của chính mình. Admin bị chặn."""
    if is_admin_user(request.user):
        messages.error(request, 'Tài khoản Admin không sử dụng chức năng này.')
        return redirect('dashboard')

    target_user = get_object_or_404(User, pk=user_id)

    if not (is_hr_user(request.user) or request.user.id == target_user.id):
        messages.error(request, 'Bạn không có quyền xem lịch sử hợp đồng này.')
        return redirect('dashboard')

    history = get_contract_history(target_user)
    return render(request, 'contracts/contract_history.html', {
        'target_user': target_user,
        'history': history,
        'is_hr_viewer': is_hr_user(request.user),
        'active_page': 'contract',
    })
```

- [ ] **Step 4: Re-export views**

Trong `contracts/views/__init__.py`, sau khối re-export `expiring_view` (dòng ~9-13) thêm:

```python
from contracts.views.contract_versioning_view import (
    hr_adjust_contract_view,
    contract_history_view,
)
```

- [ ] **Step 5: Thêm URLs**

Trong `contracts/urls.py`, cập nhật import từ `contracts.views` để thêm 2 view, và thêm 2 path vào `urlpatterns`:

```python
from contracts.views import (
    contract_view,
    hr_expiring_contracts_view,
    hr_send_reminder_view,
    hr_send_all_reminders_view,
    hr_adjust_contract_view,
    contract_history_view,
)
```

Thêm vào `urlpatterns`:

```python
    # HR điều chỉnh HĐ (tạo phiên bản mới)
    path('contract/hr/adjust/<int:user_id>/', hr_adjust_contract_view, name='hr_adjust_contract'),

    # Xem lịch sử HĐ (HR mọi người / nhân viên của mình)
    path('contract/history/<int:user_id>/', contract_history_view, name='contract_history'),
```

- [ ] **Step 6: Tạo template tối thiểu để test 200 pass**

Tạo `business_web/contracts/templates/contracts/hr_adjust_contract.html`:

```html
{% extends 'accounts/base_dashboard.html' %}
{% block title %}Điều chỉnh hợp đồng{% endblock %}
{% block content %}
<form method="post">{% csrf_token %}{{ form.as_p }}
<button type="submit">Lưu</button></form>
{% endblock %}
```

Tạo `business_web/contracts/templates/contracts/contract_history.html`:

```html
{% extends 'accounts/base_dashboard.html' %}
{% block title %}Lịch sử hợp đồng{% endblock %}
{% block content %}
<ul>{% for c in history %}<li>{{ c.contract_number }} — {{ c.is_active }}</li>{% endfor %}</ul>
{% endblock %}
```

(Template đầy đủ ở Task 5; bản tối thiểu này để test view PASS.)

- [ ] **Step 7: Chạy test — kỳ vọng PASS**

Run: `python manage.py test contracts.tests.test_contract_versioning.ContractViewsTests -v 2`
Expected: PASS (4 tests)

- [ ] **Step 8: Commit**

```bash
git add business_web/contracts/views/ business_web/contracts/urls.py business_web/contracts/templates/contracts/hr_adjust_contract.html business_web/contracts/templates/contracts/contract_history.html business_web/contracts/tests/test_contract_versioning.py
git commit -m "feat(contracts): view dieu chinh HD + lich su HD + urls"
```

---

### Task 5: Template đầy đủ cho trang điều chỉnh + lịch sử

**Files:**
- Modify: `business_web/contracts/templates/contracts/hr_adjust_contract.html`
- Modify: `business_web/contracts/templates/contracts/contract_history.html`

- [ ] **Step 1: Template form điều chỉnh**

Thay toàn bộ `contracts/templates/contracts/hr_adjust_contract.html`:

```html
{% extends 'accounts/base_dashboard.html' %}
{% block title %}Điều chỉnh hợp đồng - {{ target_user.username }}{% endblock %}

{% block content %}
<div class="animate-fade">
    <div style="margin-bottom:1.5rem;">
        <h2 style="font-size:1.5rem; font-weight:700; color:var(--text-main);">
            <i class="fa-solid fa-file-pen" style="color:var(--primary); margin-right:8px;"></i>
            Điều chỉnh hợp đồng
        </h2>
        <p style="color:var(--text-muted); font-size:0.9rem;">
            Nhân viên: <strong>{{ target_user.profile.full_name|default:target_user.username }}</strong>.
            Mỗi lần lưu sẽ tạo một phiên bản hợp đồng mới; bản hiện tại được lưu vào lịch sử.
        </p>
    </div>

    {% if form.non_field_errors %}
        <div class="alert alert-danger">{{ form.non_field_errors }}</div>
    {% endif %}

    <div class="card">
        <div class="card-body">
            <form method="post">
                {% csrf_token %}
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Số hợp đồng</label>
                        {{ form.contract_number }}
                        {% for e in form.contract_number.errors %}<small class="text-danger">{{ e }}</small>{% endfor %}
                    </div>
                    <div class="form-group">
                        <label class="form-label">Loại hợp đồng</label>
                        {{ form.contract_type }}
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Ngày ký hợp đồng</label>
                        {{ form.contract_signed_date }}
                        {% for e in form.contract_signed_date.errors %}<small class="text-danger">{{ e }}</small>{% endfor %}
                    </div>
                    <div class="form-group">
                        <label class="form-label">Ngày bắt đầu hiệu lực</label>
                        {{ form.contract_start_date }}
                        {% for e in form.contract_start_date.errors %}<small class="text-danger">{{ e }}</small>{% endfor %}
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Ngày hết hạn</label>
                        {{ form.contract_end_date }}
                        {% for e in form.contract_end_date.errors %}<small class="text-danger">{{ e }}</small>{% endfor %}
                    </div>
                    <div class="form-group">
                        <label class="form-label">Số ngày nghỉ phép/năm</label>
                        {{ form.contract_annual_leave_days }}
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Ca làm tiêu chuẩn</label>
                        {{ form.contract_standard_shift }}
                    </div>
                    <div class="form-group">
                        <label class="form-label">File tham chiếu hợp đồng</label>
                        {{ form.contract_attachment_reference }}
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Giờ bắt đầu ca</label>
                        {{ form.shift_start_time }}
                    </div>
                    <div class="form-group">
                        <label class="form-label">Giờ kết thúc ca</label>
                        {{ form.shift_end_time }}
                    </div>
                </div>

                <div style="margin-top:1.5rem; display:flex; gap:0.75rem;">
                    <button type="submit" class="btn btn-primary">
                        <i class="fa-solid fa-floppy-disk"></i> Lưu phiên bản mới
                    </button>
                    <a href="{% url 'contract_history' target_user.id %}" class="btn btn-outline">Xem lịch sử</a>
                    <a href="{% url 'hr_view_profile' target_user.id %}" class="btn btn-secondary">Hủy</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Template lịch sử**

Thay toàn bộ `contracts/templates/contracts/contract_history.html`:

```html
{% extends 'accounts/base_dashboard.html' %}
{% block title %}Lịch sử hợp đồng - {{ target_user.username }}{% endblock %}

{% block content %}
<div class="animate-fade">
    <div style="margin-bottom:1.5rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
        <div>
            <h2 style="font-size:1.5rem; font-weight:700; color:var(--text-main);">
                <i class="fa-solid fa-clock-rotate-left" style="color:var(--primary); margin-right:8px;"></i>
                Lịch sử hợp đồng
            </h2>
            <p style="color:var(--text-muted); font-size:0.9rem;">
                Nhân viên: <strong>{{ target_user.profile.full_name|default:target_user.username }}</strong>
            </p>
        </div>
        {% if is_hr_viewer %}
        <a href="{% url 'hr_adjust_contract' target_user.id %}" class="btn btn-primary">
            <i class="fa-solid fa-file-pen"></i> Điều chỉnh hợp đồng
        </a>
        {% endif %}
    </div>

    {% for c in history %}
    <div class="card" style="margin-bottom:1rem;">
        <div class="card-header">
            <h3><i class="fa-solid fa-file-invoice" style="color:var(--primary);"></i>&nbsp;
                {{ c.contract_number|default:"(chưa có số HĐ)" }}</h3>
            {% if c.is_active %}
                <span class="badge badge-active">Đang hiệu lực</span>
            {% else %}
                <span class="badge badge-inactive">Đã thay thế</span>
            {% endif %}
        </div>
        <div class="card-body">
            <div class="info-grid">
                <div class="info-item"><div class="info-label">Loại hợp đồng</div><div class="info-value">{{ c.contract_type|default:"—" }}</div></div>
                <div class="info-item"><div class="info-label">Ngày ký</div><div class="info-value">{{ c.contract_signed_date|default:"—" }}</div></div>
                <div class="info-item"><div class="info-label">Ngày bắt đầu</div><div class="info-value">{{ c.contract_start_date|default:"—" }}</div></div>
                <div class="info-item"><div class="info-label">Ngày hết hạn</div><div class="info-value">{{ c.contract_end_date|default:"—" }}</div></div>
                <div class="info-item"><div class="info-label">Nghỉ phép/năm</div><div class="info-value">{% if c.contract_annual_leave_days != None %}{{ c.contract_annual_leave_days }} ngày{% else %}—{% endif %}</div></div>
                <div class="info-item"><div class="info-label">Ca làm tiêu chuẩn</div><div class="info-value">{{ c.contract_standard_shift|default:"—" }}</div></div>
                <div class="info-item"><div class="info-label">File tham chiếu</div><div class="info-value">{{ c.contract_attachment_reference|default:"—" }}</div></div>
                <div class="info-item"><div class="info-label">Tạo lúc</div><div class="info-value">{{ c.created_at|date:"d/m/Y H:i"|default:"—" }}</div></div>
            </div>
        </div>
    </div>
    {% empty %}
    <div class="card"><div class="card-body"><div class="empty-state">
        <i class="fa-solid fa-file-circle-xmark"></i>
        <h3>Chưa có hợp đồng nào</h3>
    </div></div></div>
    {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 3: Chạy test — kỳ vọng PASS (không vỡ)**

Run: `python manage.py test contracts.tests.test_contract_versioning.ContractViewsTests -v 2`
Expected: PASS (4 tests)

- [ ] **Step 4: Commit**

```bash
git add business_web/contracts/templates/contracts/hr_adjust_contract.html business_web/contracts/templates/contracts/contract_history.html
git commit -m "feat(contracts): template dieu chinh HD + lich su HD"
```

---

### Task 6: Gỡ field HĐ khỏi form/hồ sơ chung (một đường ghi)

**Files:**
- Modify: `business_web/employee_profiles/forms.py`
- Modify: `business_web/employee_profiles/views/profile_views.py`
- Modify: `business_web/employee_profiles/templates/employee_profiles/edit_work_info.html`
- Test: `business_web/contracts/tests/test_contract_versioning.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `test_contract_versioning.py` (trong class `ContractViewsTests`):

```python
    def test_edit_work_info_does_not_create_contract_version(self):
        self.client.force_login(self.hr)
        before = ContractInfo.objects.filter(user=self.employee).count()
        url = reverse('edit_work_info', args=[self.employee.id])
        self.client.post(url, {
            'full_name': 'Nguyen Van A',
            'department': 'Kinh doanh',
            'contract_number': 'HD-PHAI-BO-QUA',
        })
        after = ContractInfo.objects.filter(user=self.employee).count()
        self.assertEqual(before, after)  # không sinh phiên bản
        contract = ensure_contract_info(self.employee)
        self.assertNotEqual(contract.contract_number, 'HD-PHAI-BO-QUA')  # không ghi đè
```

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run: `python manage.py test contracts.tests.test_contract_versioning.ContractViewsTests.test_edit_work_info_does_not_create_contract_version -v 2`
Expected: FAIL — `contract_number` bị ghi thành `HD-PHAI-BO-QUA` (assertNotEqual fail).

- [ ] **Step 3: Bỏ gọi save_contract_info trong view**

Trong `employee_profiles/views/profile_views.py`, hàm `edit_work_info_view`, xóa dòng:

```python
            # Lưu thông tin hợp đồng vào ContractInfo
            save_contract_info_from_data(target_user, form.cleaned_data)
```

Trong khối `initial={...}` của cùng hàm, xóa 8 dòng field HĐ:

```python
                'contract_number': contract_info.contract_number,
                'contract_type': contract_info.contract_type,
                'contract_signed_date': contract_info.contract_signed_date,
                'contract_start_date': contract_info.contract_start_date,
                'contract_end_date': contract_info.contract_end_date,
                'contract_annual_leave_days': contract_info.contract_annual_leave_days,
                'contract_standard_shift': contract_info.contract_standard_shift,
                'contract_attachment_reference': contract_info.contract_attachment_reference,
```

Trong import từ `employee_profiles.services`, bỏ `save_contract_info_from_data` khỏi danh sách import (nó vẫn dùng ở `hr_create_profile_view` nên **giữ trong services/__init__.py**, chỉ bỏ import nếu không còn dùng trong file này — kiểm tra: `hr_create_profile_view` trong cùng file vẫn gọi nó, nên **giữ nguyên import**).

> Lưu ý: `hr_create_profile_view` cùng file vẫn dùng `save_contract_info_from_data` → KHÔNG bỏ import, KHÔNG xóa hàm trong services.

- [ ] **Step 4: Bỏ field HĐ khỏi EmployeeProfileForm**

Trong `employee_profiles/forms.py`:

1. Xóa toàn bộ khối field HĐ (từ comment `# ----- Thông tin hợp đồng (ContractInfo) -----` đến hết field `contract_attachment_reference`, tức các field: `contract_number, contract_type, contract_signed_date, contract_start_date, contract_end_date, contract_annual_leave_days, contract_standard_shift, shift_start_time, shift_end_time, contract_attachment_reference`).

2. Trong `clean()`, xóa khối validate ngày HĐ (từ `# Validate date format DD/MM/YYYY for contract dates` đến hết khối `validate_contract_date_order`), giữ lại phần đầu `clean()` và `return cleaned_data`. Sau khi sửa, `clean()` còn:

```python
    def clean(self):
        """Công việc và hợp đồng phải đủ, cá nhân có thể để trống."""
        cleaned_data = super().clean()
        required_messages = {}
        for field_name, error_message in required_messages.items():
            value = cleaned_data.get(field_name)
            if value in [None, '']:
                self.add_error(field_name, error_message)
        return cleaned_data
```

3. Bỏ import không dùng nếu có: `from contracts.models import ContractInfo` (kiểm tra không còn tham chiếu trong file → xóa dòng import này).

- [ ] **Step 5: Gỡ section HĐ khỏi template edit_work_info**

Trong `employee_profiles/templates/employee_profiles/edit_work_info.html`, xóa khối từ dòng `<hr ...>` ngay trước `<h4 ...>Thông tin hợp đồng</h4>` đến hết `</div>` của form-row cuối (file tham chiếu hợp đồng) — tức bỏ phần `<h4>Thông tin hợp đồng</h4>` và 4 `form-row` HĐ. Thay bằng link:

```html
            <hr style="border:0; border-top:1px solid var(--border-light); margin: 1.25rem 0;">

            <h4 style="margin-bottom: 1rem;">Thông tin hợp đồng</h4>
            <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:0.75rem;">
                Hợp đồng được quản lý riêng để lưu lịch sử điều chỉnh.
            </p>
            <a href="{% url 'hr_adjust_contract' target_user.id %}" class="btn btn-outline">
                <i class="fa-solid fa-file-pen"></i> Điều chỉnh hợp đồng
            </a>
            <a href="{% url 'contract_history' target_user.id %}" class="btn btn-outline">
                <i class="fa-solid fa-clock-rotate-left"></i> Xem lịch sử hợp đồng
            </a>
```

(Giữ nguyên `<hr>` sau đó và section "Người liên hệ khẩn cấp".)

- [ ] **Step 6: Chạy test — kỳ vọng PASS**

Run: `python manage.py test contracts.tests.test_contract_versioning.ContractViewsTests.test_edit_work_info_does_not_create_contract_version -v 2`
Expected: PASS

- [ ] **Step 7: Chạy lại test hồ sơ cũ để chắc không vỡ**

Run: `python manage.py test employee_profiles -v 2`
Expected: PASS (nếu có test cũ assert field HĐ trong edit_work_info, cập nhật/xóa assert đó cho khớp hành vi mới — HĐ không còn sửa qua form này).

- [ ] **Step 8: Commit**

```bash
git add business_web/employee_profiles/forms.py business_web/employee_profiles/views/profile_views.py business_web/employee_profiles/templates/employee_profiles/edit_work_info.html business_web/contracts/tests/test_contract_versioning.py
git commit -m "refactor(profiles): go field HD khoi edit_work_info, chi sua qua trang dieu chinh"
```

---

### Task 7: Nút điều hướng trong hồ sơ HR + trang HĐ nhân viên

**Files:**
- Modify: `business_web/employee_profiles/templates/employee_profiles/hr_view_profile.html`
- Modify: `business_web/contracts/templates/contracts/contract.html`

- [ ] **Step 1: Thêm nút vào header card HĐ (hr_view_profile)**

Trong `hr_view_profile.html`, thay khối header section HĐ (dòng ~377-380):

```html
        <div class="profile-card-header">
            <i class="pc-icon-contract fa-solid fa-file-contract"></i>
            <h3>Hợp đồng lao động</h3>
        </div>
```

thành:

```html
        <div class="profile-card-header" style="display:flex; justify-content:space-between; align-items:center;">
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <i class="pc-icon-contract fa-solid fa-file-contract"></i>
                <h3>Hợp đồng lao động</h3>
            </div>
            {% if can_manage_work_info %}
            <div style="display:flex; gap:0.5rem;">
                <a href="{% url 'hr_adjust_contract' target_user.id %}" class="btn btn-sm btn-primary">
                    <i class="fa-solid fa-file-pen"></i> Điều chỉnh HĐ
                </a>
                <a href="{% url 'contract_history' target_user.id %}" class="btn btn-sm btn-outline">
                    <i class="fa-solid fa-clock-rotate-left"></i> Lịch sử HĐ
                </a>
            </div>
            {% endif %}
        </div>
```

- [ ] **Step 2: Thêm nút "Xem lịch sử HĐ" cho nhân viên (contract.html)**

Trong `contracts/templates/contracts/contract.html`, trong khối actions header (dòng ~16-20), ngay trước `{% endif %}` của block HR, thêm nút lịch sử cho mọi user (dùng `request.user.id`):

```html
        <a href="{% url 'contract_history' request.user.id %}" class="btn btn-outline" style="display: inline-flex; align-items: center; gap: 0.5rem; font-weight: 600;">
            <i class="fa-solid fa-clock-rotate-left"></i> Xem lịch sử HĐ
        </a>
```

Đặt nút này **ngoài** block `{% if request.user.profile.role.name == 'hr' %}` (sau dòng `{% endif %}` của block HR, vẫn trong div actions) để mọi nhân viên thấy được.

- [ ] **Step 3: Kiểm tra render thủ công**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 4: Commit**

```bash
git add business_web/employee_profiles/templates/employee_profiles/hr_view_profile.html business_web/contracts/templates/contracts/contract.html
git commit -m "feat(contracts): nut dieu chinh + lich su HD trong ho so & trang HD"
```

---

### Task 8: Chạy toàn bộ test suite

- [ ] **Step 1: Chạy full app contracts + employee_profiles**

Run: `python manage.py test contracts employee_profiles -v 2`
Expected: PASS toàn bộ.

- [ ] **Step 2: Chạy full suite (an toàn regression)**

Run: `python manage.py test -v 1`
Expected: PASS. Nếu có test cũ giả định luồng ghi đè HĐ qua edit_work_info → cập nhật cho khớp hành vi versioning mới.

- [ ] **Step 3: Commit (nếu có sửa test regression)**

```bash
git add -A
git commit -m "test(contracts): cap nhat test cho luong versioning HD"
```

---

## Self-Review Notes

- **Spec coverage:** Model created_at (T1) · adjust_contract + history service (T2) · form (T3) · views + quyền HR/owner/admin (T4) · UI điều chỉnh + lịch sử snapshot đầy đủ (T5) · gỡ field HĐ khỏi edit_work_info, giữ save_contract_info_from_data cho create (T6) · nút điều hướng (T7) · regression (T8). Đủ.
- **Quyền:** `is_hr_user` (HR + superuser) xem tất cả; owner xem của mình; `is_admin_user` bị chặn — khớp "chỉ HR xem tất cả, nhân viên xem của mình".
- **Một đường ghi:** sau T6 chỉ `hr_adjust_contract_view` → `adjust_contract` tạo phiên bản; `hr_create_profile_view` vẫn dùng `save_contract_info_from_data` cho HĐ đầu tiên (không versioning, đúng ý YAGNI).

# Bugfix + Evolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the reported bugs in `Lỗi bug tìm được và những gì cần thêm.txt` and add the requested features, keeping every flow consistent with `sequence_diagrams (1).md`.

**Architecture:** Django monolith, per-app structure (`accounts`, `employee_profiles`, `contracts`, `rewards_discipline`, `reports_interactions`, `performance`, `attendance`, ...). Business logic lives in `services/`, request handling in `views/`, validation in `forms/`. Evolution config (#28–33) is implemented as a new set of **Admin-managed lookup tables** consumed as dropdowns by HR forms.

**Tech Stack:** Django (templates + ModelForm), SQLite dev DB, `manage.py test` (Django `TestCase`). Date fields are stored as `DD/MM/YYYY` strings; validators live in `contracts/services`.

## Global Constraints

- Run all tests from the `business_web/` directory: `python manage.py test <dotted.path> -v 2`.
- Date strings are `DD/MM/YYYY`. Reuse `contracts.services.parse_ddmmyyyy` / `validate_contract_date_order` — do NOT invent a new date parser.
- Permission checks go through `accounts.services` helpers (`is_hr_user`, `is_admin_user`, `user_has_role`, `can_manage_work_info`, `can_process_tickets`). Never branch on `is_superuser` directly for business rules — superuser only *simulates* a role.
- Admin accounts are NOT employees: they have no profile/contract/reward records and are excluded from employee dropdowns.
- Contract date rule (decided): `signed_date ≤ start_date` and `end_date > start_date` (end strictly after start).
- Evolution config (decided): Admin-managed lookup lists; **only the Admin role** edits the lists; HR consumes them as dropdowns.
- Commit after every task with a conventional-commit message. Branch: `fixbug`.
- Vietnamese user-facing copy, matching the existing tone in each file.

---

## File Structure

**New files**
- `common/config/models.py` (or new app `system_config`) — `LookupCategory` + `LookupOption` lookup tables for departments, positions, workplaces, contract types, reward mechanisms, penalty mechanisms.
- `common/config/services.py` — `get_options(category)`, `option_choices(category)`, seed helper.
- `accounts` (or `stats_reports`) admin-config view + template `*/system_config.html` — Admin CRUD for lookup options.
- `common/middleware.py` — `NoCacheForAuthenticatedMiddleware` (logout/back-button fix).
- `common/validators.py` — `validate_phone_number(value)`.

**Modified files** (per task; exact lines resolved at execution time)
- `accounts/views/auth/logout_view.py`, `business_web/settings.py` (middleware), `accounts/views/account/account_create_view.py` (admin create account session fix).
- `employee_profiles/forms.py`, `employee_profiles/views/profile_views.py`, `employee_profiles/services/__init__.py`, `employee_profiles/templates/...`.
- `contracts/services/__init__.py`, `contracts/forms.py`.
- `rewards_discipline/forms.py`, `rewards_discipline/models/reward_penalty_model.py`.
- `performance/forms.py`, `performance/services/evaluation_data.py`, `performance/views/__init__.py`.
- `accounts/templates/accounts/account/settings.html` (tax removal).

---

## PHASE 0 — Verify "already-handled" items (regression tests, fix only on leak)

Bugs #1, #2, #3, #6 appear satisfied in code. Lock them with tests; fix only if a test fails or a UI/nav leak is found.

### Task 0.1: Lock Leader/Manager reward-employee scoping (#1)

**Files:**
- Test: `rewards_discipline/tests/test_reward_scope.py` (create)
- Modify only if failing: `rewards_discipline/forms.py:37-65`

**Interfaces:**
- Consumes: `RewardPenaltyForm(user=<proposer>)` exposes `.fields['employee'].choices`.

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from rewards_discipline.forms import RewardPenaltyForm


class RewardScopeTest(TestCase):
    def setUp(self):
        self.leader_role, _ = Role.objects.get_or_create(name=Role.LEADER)
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)

        self.leader = User.objects.create_user('lead', password='x')
        UserProfile.objects.create(user=self.leader, role=self.leader_role, employee_id='L1')
        self.sub = User.objects.create_user('sub', password='x')
        UserProfile.objects.create(user=self.sub, role=self.emp_role, employee_id='S1')
        self.other = User.objects.create_user('other', password='x')
        UserProfile.objects.create(user=self.other, role=self.emp_role, employee_id='O1')

        EmployeeWorkInfo.objects.create(user=self.sub, leader_user=self.leader)
        EmployeeWorkInfo.objects.create(user=self.other)  # no supervisor link

    def test_leader_sees_only_subordinates(self):
        form = RewardPenaltyForm(user=self.leader)
        ids = {val for val, _ in form.fields['employee'].choices if val}
        self.assertIn(self.sub.id, ids)
        self.assertNotIn(self.other.id, ids)
```

- [ ] **Step 2: Run test**

Run: `python manage.py test rewards_discipline.tests.test_reward_scope -v 2`
Expected: PASS (confirms existing behavior). If FAIL, fix `RewardPenaltyForm.__init__` so the non-HR branch filters `work_info__leader_user=user | work_info__manager_user=user`.

- [ ] **Step 3: Commit**

```bash
git add rewards_discipline/tests/test_reward_scope.py
git commit -m "test(rewards): lock leader/manager employee scoping (#1)"
```

### Task 0.2: Lock Leader-cannot-approve + ticket reception access (#3, #6)

**Files:**
- Test: `rewards_discipline/tests/test_approval_roles.py` (create)
- Test: `reports_interactions/tests/test_ticket_access.py` (create)
- Modify only if failing: `rewards_discipline/services/__init__.py`, `reports_interactions/views/__init__.py:198-204`

- [ ] **Step 1: Write the failing tests**

```python
# rewards_discipline/tests/test_approval_roles.py
from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from rewards_discipline.models import RewardPenalty
from rewards_discipline.services import approve_reward_penalty


class ApprovalRoleTest(TestCase):
    def setUp(self):
        self.leader_role, _ = Role.objects.get_or_create(name=Role.LEADER)
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.leader = User.objects.create_user('lead', password='x')
        UserProfile.objects.create(user=self.leader, role=self.leader_role, employee_id='L1')
        self.emp = User.objects.create_user('emp', password='x')
        UserProfile.objects.create(user=self.emp, role=self.emp_role, employee_id='E1')
        self.rec = RewardPenalty.objects.create(
            employee=self.emp, proposer=self.leader, record_type='reward',
            amount=100, reason_title='t', status=RewardPenalty.PENDING,
        )

    def test_leader_cannot_approve_l1(self):
        ok, _ = approve_reward_penalty(self.leader, self.rec.id)
        self.assertFalse(ok)
```

```python
# reports_interactions/tests/test_ticket_access.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class TicketAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.mgr_role, _ = Role.objects.get_or_create(name=Role.MANAGER)
        self.mgr = User.objects.create_user('mgr', password='x')
        UserProfile.objects.create(user=self.mgr, role=self.mgr_role, employee_id='M1')

    def test_manager_blocked_from_ticket_process(self):
        self.client.login(username='mgr', password='x')
        resp = self.client.get(reverse('ticket_process'), follow=True)
        self.assertContains(resp, 'không có quyền')
```

- [ ] **Step 2: Run tests**

Run: `python manage.py test rewards_discipline.tests.test_approval_roles reports_interactions.tests.test_ticket_access -v 2`
Expected: PASS. If ticket test fails because the nav still shows the link to managers, gate the template link on `can_process` (already passed to ticket_list context) and keep the view guard.

- [ ] **Step 3: Commit**

```bash
git add rewards_discipline/tests/test_approval_roles.py reports_interactions/tests/test_ticket_access.py
git commit -m "test: lock leader-no-approve and ticket reception access (#3,#6)"
```

### Task 0.3: Verify ticket type has no "điều chỉnh giờ công" (#2)

**Files:**
- Test: `reports_interactions/tests/test_ticket_types.py` (create)
- Inspect: `reports_interactions/templates/reports_interactions/tickets.html`

- [ ] **Step 1: Write the test**

```python
from django.test import TestCase
from reports_interactions.models.ticket_model import Ticket


class TicketTypeTest(TestCase):
    def test_no_timesheet_adjustment_type(self):
        labels = ' '.join(label for _, label in Ticket.TYPE_CHOICES).lower()
        self.assertNotIn('giờ công', labels)
        self.assertNotIn('điều chỉnh', labels)
```

- [ ] **Step 2: Run test**

Run: `python manage.py test reports_interactions.tests.test_ticket_types -v 2`
Expected: PASS. Then grep `tickets.html` for any hardcoded "điều chỉnh giờ công" option/link; if present, delete that markup.

- [ ] **Step 3: Commit**

```bash
git add reports_interactions/tests/test_ticket_types.py
git commit -m "test(tickets): assert no timesheet-adjustment ticket type (#2)"
```

---

## PHASE 1 — Auth / session (#11–14)

### Task 1.1: Logout back-button must not show authenticated page (#11, #12)

**Files:**
- Create: `common/middleware.py`
- Modify: `business_web/settings.py` (MIDDLEWARE list)
- Test: `accounts/tests/test_logout_cache.py` (create)

**Interfaces:**
- Produces: `common.middleware.NoCacheForAuthenticatedMiddleware` — sets `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` on responses for authenticated requests.

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class LogoutCacheTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.user = User.objects.create_user('emp', password='x')
        UserProfile.objects.create(user=self.user, role=self.emp_role, employee_id='E1')

    def test_authenticated_page_is_no_store(self):
        self.client.login(username='emp', password='x')
        resp = self.client.get(reverse('dashboard'))
        self.assertIn('no-store', resp.headers.get('Cache-Control', ''))

    def test_dashboard_requires_login_after_logout(self):
        self.client.login(username='emp', password='x')
        self.client.get(reverse('logout'))
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)  # redirected to login
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test accounts.tests.test_logout_cache -v 2`
Expected: FAIL on `test_authenticated_page_is_no_store` (no Cache-Control header).

- [ ] **Step 3: Implement middleware**

```python
# common/middleware.py
"""Chống dùng nút Back để xem lại trang sau khi đăng xuất."""


class NoCacheForAuthenticatedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(request, 'user', None) and request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
```

- [ ] **Step 4: Register middleware**

In `business_web/settings.py`, append to `MIDDLEWARE` (after `AuthenticationMiddleware`):

```python
    'common.middleware.NoCacheForAuthenticatedMiddleware',
```

- [ ] **Step 5: Run tests to verify pass**

Run: `python manage.py test accounts.tests.test_logout_cache -v 2`
Expected: PASS (both tests).

- [ ] **Step 6: Commit**

```bash
git add common/middleware.py business_web/settings.py accounts/tests/test_logout_cache.py
git commit -m "fix(auth): no-store cache on authed pages so Back after logout requires login (#11,#12)"
```

### Task 1.2: Admin "create account → change role" must not log Admin out (#13, #14)

**Files:**
- Inspect: `accounts/views/account/account_create_view.py` (admin create) and `accounts/views/auth/register_view.py`
- Test: `accounts/tests/test_admin_create_session.py` (create)
- Modify the offending view (the one that calls `login(request, new_user)` while an Admin is acting, replacing the Admin's session).

**Interfaces:**
- Rule: creating an account on behalf of someone must NOT call `login()` for the new user when an authenticated Admin is performing the action. The Admin session must persist; redirect to `user_list`.

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class AdminCreateSessionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        self.admin = User.objects.create_user('admin_u', password='x')
        UserProfile.objects.create(user=self.admin, role=self.admin_role, employee_id='ADM')

    def test_admin_stays_logged_in_after_creating_account(self):
        self.client.login(username='admin_u', password='x')
        self.client.post(reverse('admin_create_account'), {
            'username': 'newbie', 'password': 'Password@123',
            'password_confirm': 'Password@123',
        })
        # Admin session still belongs to admin_u, not newbie
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.admin.id)
```

> Resolve the exact URL name + POST fields by reading `accounts/urls.py` and the admin create view/form during execution. Adjust the field names in the test to match.

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test accounts.tests.test_admin_create_session -v 2`
Expected: FAIL (session id flips to the new user, or the admin gets redirected to login).

- [ ] **Step 3: Implement fix**

In the admin create-account view, remove/guard any `login(request, new_user)` call:

```python
    # Chỉ tự đăng nhập khi đây là self-register (khách chưa đăng nhập).
    if not request.user.is_authenticated:
        login(request, user)
        return redirect('dashboard')
    messages.success(request, f'Đã tạo tài khoản "{user.username}".')
    return redirect('user_list')
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python manage.py test accounts.tests.test_admin_create_session accounts.tests.test_register -v 2`
Expected: PASS (admin path fixed, self-register unaffected).

- [ ] **Step 5: Commit**

```bash
git add accounts/views/account/account_create_view.py accounts/tests/test_admin_create_session.py
git commit -m "fix(auth): admin keeps own session when creating accounts (#13,#14)"
```

---

## PHASE 2 — Profile self-edit validation + UI (#7, #15–22)

### Task 2.1: Phone-number validator (#16, #21)

**Files:**
- Create: `common/validators.py`
- Test: `common/tests/test_validators.py` (create; add `common/tests/__init__.py` if missing)

**Interfaces:**
- Produces: `common.validators.validate_phone_number(value) -> str` — raises `django.core.exceptions.ValidationError` for non-numeric / wrong-length input; returns the cleaned digits. Accepts Vietnamese mobile format: 10 digits starting with `0`.

- [ ] **Step 1: Write the failing test**

```python
from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from common.validators import validate_phone_number


class PhoneValidatorTest(SimpleTestCase):
    def test_rejects_letters(self):
        with self.assertRaises(ValidationError):
            validate_phone_number('09abc1234x')

    def test_rejects_wrong_length(self):
        with self.assertRaises(ValidationError):
            validate_phone_number('012')

    def test_accepts_valid(self):
        self.assertEqual(validate_phone_number('0901234567'), '0901234567')

    def test_blank_allowed(self):
        self.assertEqual(validate_phone_number(''), '')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test common.tests.test_validators -v 2`
Expected: FAIL with "No module named 'common.validators'".

- [ ] **Step 3: Implement**

```python
# common/validators.py
import re
from django.core.exceptions import ValidationError

_PHONE_RE = re.compile(r'^0\d{9}$')


def validate_phone_number(value):
    value = (value or '').strip()
    if not value:
        return ''
    if not _PHONE_RE.match(value):
        raise ValidationError('Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.')
    return value
```

- [ ] **Step 4: Run test to verify pass**

Run: `python manage.py test common.tests.test_validators -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add common/validators.py common/tests/test_validators.py common/tests/__init__.py
git commit -m "feat(common): add Vietnamese phone-number validator (#16,#21)"
```

### Task 2.2: Profile self-edit uses a validating form with field errors (#20, #21, #22)

**Files:**
- Modify: `employee_profiles/views/profile_views.py:42-99` (`profile_view`)
- Create: `employee_profiles/forms.py` — add `PersonalEditForm`
- Test: `employee_profiles/tests/test_profile_edit_validation.py` (create)

**Interfaces:**
- Consumes: `common.validators.validate_phone_number`, `contracts.services.parse_ddmmyyyy`.
- Produces: `PersonalEditForm(data, instance_user=...)` validating `full_name`, `email` (unique), `phone_number` (validator), `date_of_birth` (`DD/MM/YYYY`, not future). On invalid POST, `profile_view` re-renders the page with `form` so per-field errors show instead of a silent redirect.

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class ProfileEditValidationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.user = User.objects.create_user('emp', password='x', email='e@x.vn')
        UserProfile.objects.create(user=self.user, role=self.emp_role, employee_id='E1')
        self.client.login(username='emp', password='x')

    def test_invalid_phone_shows_error_not_silent(self):
        resp = self.client.post(reverse('profile'), {
            'full_name': 'A', 'email': 'e@x.vn',
            'phone_number': 'abc', 'date_of_birth': '',
        })
        self.assertContains(resp, 'Số điện thoại')  # error rendered on page
        self.assertEqual(resp.status_code, 200)

    def test_future_dob_rejected(self):
        resp = self.client.post(reverse('profile'), {
            'full_name': 'A', 'email': 'e@x.vn',
            'phone_number': '', 'date_of_birth': '01/01/2999',
        })
        self.assertContains(resp, 'ngày sinh')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test employee_profiles.tests.test_profile_edit_validation -v 2`
Expected: FAIL (current view redirects silently / accepts bad input).

- [ ] **Step 3: Implement `PersonalEditForm`**

```python
# employee_profiles/forms.py  (append)
from datetime import date
from common.validators import validate_phone_number
from contracts.services import parse_ddmmyyyy


class PersonalEditForm(forms.Form):
    full_name = forms.CharField(max_length=255, required=False)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.CharField(max_length=10, required=False)

    def __init__(self, *args, instance_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance_user = instance_user

    def clean_email(self):
        value = (self.cleaned_data.get('email') or '').strip()
        if not value:
            return ''
        qs = User.objects.filter(email__iexact=value)
        if self.instance_user:
            qs = qs.exclude(pk=self.instance_user.pk)
        if qs.exists():
            raise forms.ValidationError('Email này đã được sử dụng.')
        return value

    def clean_phone_number(self):
        return validate_phone_number(self.cleaned_data.get('phone_number'))

    def clean_date_of_birth(self):
        value = (self.cleaned_data.get('date_of_birth') or '').strip()
        if not value:
            return ''
        parsed = parse_ddmmyyyy(value)
        if not parsed:
            raise forms.ValidationError('Ngày sinh phải có định dạng DD/MM/YYYY.')
        if parsed > date.today():
            raise forms.ValidationError('Ngày sinh không thể ở tương lai.')
        return value
```

- [ ] **Step 4: Wire form into `profile_view`**

Replace the manual POST block in `profile_view` so it builds `PersonalEditForm(request.POST, instance_user=request.user)`, and on `form.is_valid()` runs the existing `transaction.atomic` save using `form.cleaned_data`; on invalid, `render` the profile template with `{'form': form, 'active_page': 'profile'}` (status 200). Ensure the template renders `form.<field>.errors`. Keep `save_personal_info_from_data` / `save_emergency_contact_from_data` / `save_education_info_from_data` calls.

- [ ] **Step 5: Run tests to verify pass**

Run: `python manage.py test employee_profiles.tests.test_profile_edit_validation -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add employee_profiles/forms.py employee_profiles/views/profile_views.py employee_profiles/templates/employee_profiles/profile.html employee_profiles/tests/test_profile_edit_validation.py
git commit -m "fix(profile): validate self-edit with visible field errors (#20,#21,#22)"
```

### Task 2.3: Education level dropdown + searchable major (#17, #18, #19)

**Files:**
- Modify: `employee_profiles/forms.py` (`EmployeeProfileForm` + add same fields to `PersonalEditForm` if education editable there)
- Modify: `employee_profiles/templates/.../edit_work_info.html` and `profile.html` (use `<datalist>` for searchable major)
- Test: `employee_profiles/tests/test_education_choices.py` (create)

**Interfaces:**
- Produces: `EDUCATION_LEVEL_CHOICES` in `employee_profiles/forms.py`; `MAJOR_SUGGESTIONS` list rendered as a `<datalist>` so the `major` text input gets type-ahead search (no new dependency).

- [ ] **Step 1: Write the failing test**

```python
from django.test import SimpleTestCase
from employee_profiles.forms import EmployeeProfileForm, EDUCATION_LEVEL_CHOICES


class EducationChoiceTest(SimpleTestCase):
    def test_education_level_is_choice_field(self):
        form = EmployeeProfileForm()
        widget = form.fields['education_level'].widget.__class__.__name__
        self.assertEqual(widget, 'Select')
        labels = [label for _, label in EDUCATION_LEVEL_CHOICES]
        self.assertIn('THPT', labels)
        self.assertIn('Đại học', labels)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test employee_profiles.tests.test_education_choices -v 2`
Expected: FAIL (`education_level` is currently a `CharField`/`TextInput`).

- [ ] **Step 3: Implement choices + datalist**

```python
# employee_profiles/forms.py  (module level)
EDUCATION_LEVEL_CHOICES = [
    ('', '-- Chọn trình độ --'),
    ('THPT', 'THPT'),
    ('Trung cấp', 'Trung cấp'),
    ('Cao đẳng', 'Cao đẳng'),
    ('Đại học', 'Đại học'),
    ('Thạc sĩ', 'Thạc sĩ'),
    ('Tiến sĩ', 'Tiến sĩ'),
]

MAJOR_SUGGESTIONS = [
    'Công nghệ thông tin', 'Kế toán', 'Quản trị kinh doanh', 'Marketing',
    'Tài chính - Ngân hàng', 'Kỹ thuật phần mềm', 'Khoa học máy tính',
    'Ngôn ngữ Anh', 'Luật', 'Nhân sự', 'Cơ khí', 'Điện - Điện tử',
]
```

Change `education_level` field to:

```python
    education_level = forms.ChoiceField(
        required=False, choices=EDUCATION_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
```

Change `major` widget to bind a datalist:

```python
    major = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'list': 'major-suggestions',
            'placeholder': 'Gõ để tìm chuyên ngành...',
        }),
    )
```

In the templates that render `form.major`, add once:

```html
<datalist id="major-suggestions">
  {% for m in major_suggestions %}<option value="{{ m }}">{% endfor %}
</datalist>
```

and pass `'major_suggestions': MAJOR_SUGGESTIONS` from the view context.

- [ ] **Step 4: Run tests to verify pass**

Run: `python manage.py test employee_profiles.tests.test_education_choices -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add employee_profiles/forms.py employee_profiles/views/profile_views.py employee_profiles/templates/employee_profiles/edit_work_info.html employee_profiles/templates/employee_profiles/profile.html employee_profiles/tests/test_education_choices.py
git commit -m "feat(profile): education-level dropdown + searchable major datalist (#17,#18,#19)"
```

### Task 2.4: Remove tax code from company settings (#7)

**Files:**
- Modify: `accounts/templates/accounts/account/settings.html:202-206`
- Test: `accounts/tests/test_settings_no_tax.py` (create)

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class SettingsNoTaxTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        self.admin = User.objects.create_user('admin_u', password='x')
        UserProfile.objects.create(user=self.admin, role=self.admin_role, employee_id='ADM')

    def test_no_tax_code_field(self):
        self.client.login(username='admin_u', password='x')
        resp = self.client.get(reverse('settings'))
        self.assertNotContains(resp, 'Mã số thuế')
```

> Confirm the settings URL name (`settings`) in `accounts/urls.py` during execution.

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test accounts.tests.test_settings_no_tax -v 2`
Expected: FAIL (page contains "Mã số thuế").

- [ ] **Step 3: Delete the tax `st-form-group` block** (the `<div class="st-form-group">` wrapping the "Mã số thuế" label + input).

- [ ] **Step 4: Run test to verify pass**

Run: `python manage.py test accounts.tests.test_settings_no_tax -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add accounts/templates/accounts/account/settings.html accounts/tests/test_settings_no_tax.py
git commit -m "chore(settings): remove tax-code field (#7)"
```

---

## PHASE 3 — Work info + contract date validation (#23–27)

### Task 3.1: Probation start ≤ official start (#23, #24)

**Files:**
- Create: `contracts/services/__init__.py` — `validate_work_date_order(probation_start, official_start)` (place beside `validate_contract_date_order`; reuses `parse_ddmmyyyy`)
- Modify: `employee_profiles/forms.py` (`EmployeeProfileForm.clean`) and `employee_profiles/views/profile_views.py` (`hr_create_profile_view` validation block)
- Test: `employee_profiles/tests/test_work_date_order.py` (create)

**Interfaces:**
- Produces: `validate_work_date_order(probation_start, official_start) -> list[str]` — returns `['Ngày thử việc phải trước hoặc bằng ngày chính thức.']` when probation date is after official date; `[]` otherwise; ignores blanks/bad format.

- [ ] **Step 1: Write the failing test**

```python
from django.test import SimpleTestCase
from contracts.services import validate_work_date_order


class WorkDateOrderTest(SimpleTestCase):
    def test_probation_after_official_rejected(self):
        errs = validate_work_date_order('01/09/2026', '01/08/2026')
        self.assertTrue(errs)

    def test_probation_before_official_ok(self):
        self.assertEqual(validate_work_date_order('01/06/2026', '01/08/2026'), [])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test employee_profiles.tests.test_work_date_order -v 2`
Expected: FAIL ("cannot import name 'validate_work_date_order'").

- [ ] **Step 3: Implement validator**

```python
# contracts/services/__init__.py  (near validate_contract_date_order)
def validate_work_date_order(probation_start, official_start):
    """Ngày thử việc phải ≤ ngày chính thức (chuỗi DD/MM/YYYY)."""
    errors = []
    d_prob = parse_ddmmyyyy(probation_start)
    d_off = parse_ddmmyyyy(official_start)
    if d_prob and d_off and d_prob > d_off:
        errors.append('Ngày thử việc phải trước hoặc bằng ngày chính thức.')
    return errors
```

- [ ] **Step 4: Call validator in both forms/views**

In `hr_create_profile_view`, after the contract-date check, add:

```python
        from contracts.services import validate_work_date_order
        errors.extend(validate_work_date_order(probation_start, official_start))
```

In `EmployeeProfileForm.clean`, add:

```python
        from contracts.services import validate_work_date_order
        for err in validate_work_date_order(
            self.cleaned_data.get('probation_start'),
            self.cleaned_data.get('official_start_date'),
        ):
            self.add_error('official_start_date', err)
```

- [ ] **Step 5: Run tests to verify pass**

Run: `python manage.py test employee_profiles.tests.test_work_date_order -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add contracts/services/__init__.py employee_profiles/forms.py employee_profiles/views/profile_views.py employee_profiles/tests/test_work_date_order.py
git commit -m "fix(workinfo): probation start must be <= official start (#23,#24)"
```

### Task 3.2: Contract end strictly after start (#25, #26)

**Files:**
- Modify: `contracts/services/__init__.py:39` (`validate_contract_date_order`)
- Test: `contracts/tests/test_date_order.py` (extend existing)

**Interfaces:**
- Change: end-vs-start comparison from `d_end < d_start` to `d_end <= d_start` with the message "Ngày hết hạn hợp đồng phải sau ngày bắt đầu." Signed-vs-start stays `<` (equal allowed).

- [ ] **Step 1: Add the failing test**

```python
# contracts/tests/test_date_order.py  (append a test method)
    def test_end_equal_start_rejected(self):
        from contracts.services import validate_contract_date_order
        errs = validate_contract_date_order('01/01/2026', '01/01/2026', '01/01/2026')
        self.assertTrue(any('hết hạn' in e for e in errs))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test contracts.tests.test_date_order -v 2`
Expected: FAIL (equal end/start currently allowed).

- [ ] **Step 3: Implement**

```python
    if d_start and d_end and d_end <= d_start:
        errors.append('Ngày hết hạn hợp đồng phải sau ngày bắt đầu.')
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python manage.py test contracts.tests.test_date_order contracts.tests.test_contract_versioning -v 2`
Expected: PASS (update any existing test that asserted equal dates were valid).

- [ ] **Step 5: Commit**

```bash
git add contracts/services/__init__.py contracts/tests/test_date_order.py
git commit -m "fix(contracts): end date must be strictly after start (#25,#26)"
```

### Task 3.3: Surface shift-time + contract-date errors in create-profile, and validate shift in create (#27)

**Files:**
- Modify: `employee_profiles/views/profile_views.py` (`hr_create_profile_view`) — read `shift_start_time`/`shift_end_time`, validate order, push errors; ensure `messages.error` already lists every error (it does).
- Modify: `employee_profiles/templates/.../hr_create_profile.html` and `contracts` adjust template — confirm field errors render near each field.
- Test: `employee_profiles/tests/test_create_profile_shift.py` (create)

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class CreateProfileShiftTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)
        self.hr = User.objects.create_user('hr_u', password='x')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR')
        self.client.login(username='hr_u', password='x')

    def test_bad_shift_time_shows_error(self):
        resp = self.client.post(reverse('hr_create_profile'), {
            'employee_id': 'NV9', 'department': 'X', 'position': 'Y',
            'employee_type': 'Z', 'workplace': 'W', 'work_status': 'official',
            'probation_start': '01/06/2026', 'official_start_date': '01/08/2026',
            'contract_number': 'C1', 'contract_type': 'T',
            'contract_signed_date': '01/05/2026', 'contract_start_date': '05/05/2026',
            'contract_end_date': '05/05/2027', 'contract_annual_leave_days': '12',
            'contract_standard_shift': '08:00-17:00',
            'shift_start_time': '17:00', 'shift_end_time': '08:00',
            'auto_create_account': 'on',
        }, follow=True)
        self.assertContains(resp, 'Giờ kết thúc ca')
```

> Confirm the create template posts `shift_start_time`/`shift_end_time`; if it currently only has `contract_standard_shift` text, add the two `type="time"` inputs to the form.

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test employee_profiles.tests.test_create_profile_shift -v 2`
Expected: FAIL (no shift validation in create flow).

- [ ] **Step 3: Implement** — in `hr_create_profile_view`, parse the two time fields and validate:

```python
        from datetime import datetime
        shift_start_raw = request.POST.get('shift_start_time', '').strip()
        shift_end_raw = request.POST.get('shift_end_time', '').strip()
        def _parse_time(v):
            try:
                return datetime.strptime(v, '%H:%M').time()
            except ValueError:
                return None
        s_start, s_end = _parse_time(shift_start_raw), _parse_time(shift_end_raw)
        if s_start and s_end and s_end <= s_start:
            errors.append('Giờ kết thúc ca phải sau giờ bắt đầu ca.')
```

Persist `shift_start_time` / `shift_end_time` into the `save_contract_info_from_data` payload.

- [ ] **Step 4: Run tests to verify pass**

Run: `python manage.py test employee_profiles.tests.test_create_profile_shift contracts.tests.test_shift_time_order -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add employee_profiles/views/profile_views.py employee_profiles/services/__init__.py employee_profiles/templates/employee_profiles/hr_create_profile.html employee_profiles/tests/test_create_profile_shift.py
git commit -m "fix(contracts): validate + surface shift-time/date errors on profile create (#27)"
```

---

## PHASE 4 — Evidence upload on employee creation (#5)

### Task 4.1: Upload/scan evidence file after contract info in create-profile

**Files:**
- Modify: `employee_profiles/templates/.../hr_create_profile.html` — add a file input section after the contract block: `<input type="file" name="evidence_files" multiple accept="image/*,.pdf,capture=environment">` (the `capture` attr enables mobile camera "scan").
- Modify: `employee_profiles/views/profile_views.py` (`hr_create_profile_view`) — after creating the user/profile, loop `request.FILES.getlist('evidence_files')`, validate each via `validate_upload`, and create `EmployeeDocument` rows.
- Test: `employee_profiles/tests/test_create_profile_evidence.py` (create)

**Interfaces:**
- Consumes: `common.file_validation.validate_upload`, `employee_profiles.models.EmployeeDocument`.

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeDocument


class CreateProfileEvidenceTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)
        self.hr = User.objects.create_user('hr_u', password='x')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR')
        self.client.login(username='hr_u', password='x')

    def test_evidence_file_attached_to_new_employee(self):
        png = SimpleUploadedFile('cccd.png', b'\x89PNG\r\n\x1a\n' + b'0' * 100, content_type='image/png')
        self.client.post(reverse('hr_create_profile'), {
            'employee_id': 'NV5', 'department': 'X', 'position': 'Y',
            'employee_type': 'Z', 'workplace': 'W', 'work_status': 'official',
            'probation_start': '01/06/2026', 'official_start_date': '01/08/2026',
            'contract_number': 'C1', 'contract_type': 'T',
            'contract_signed_date': '01/05/2026', 'contract_start_date': '05/05/2026',
            'contract_end_date': '05/05/2027', 'contract_annual_leave_days': '12',
            'contract_standard_shift': '08:00-17:00',
            'auto_create_account': 'on', 'evidence_files': png,
        })
        new_user = User.objects.get(profile__employee_id='NV5')
        self.assertEqual(EmployeeDocument.objects.filter(user=new_user).count(), 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test employee_profiles.tests.test_create_profile_evidence -v 2`
Expected: FAIL (no `EmployeeDocument` created).

- [ ] **Step 3: Implement** — inside the `auto_create` success branch, after `save_contract_info_from_data(...)`:

```python
            from common.file_validation import validate_upload
            for f in request.FILES.getlist('evidence_files'):
                try:
                    validate_upload(f)
                except ValidationError as exc:
                    messages.warning(request, f'Bỏ qua "{f.name}": {" ".join(exc.messages)}')
                    continue
                EmployeeDocument.objects.create(
                    user=user, title=f.name, document_type='Minh chứng hồ sơ', file=f,
                )
```

- [ ] **Step 4: Run test to verify pass**

Run: `python manage.py test employee_profiles.tests.test_create_profile_evidence -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add employee_profiles/views/profile_views.py employee_profiles/templates/employee_profiles/hr_create_profile.html employee_profiles/tests/test_create_profile_evidence.py
git commit -m "feat(profile): upload/scan evidence files when creating employee (#5)"
```

---

## PHASE 5 — Evolution: Admin-managed lookup lists (#28–33)

> Decided: new Admin-only lookup tables for **workplace, contract type, reward mechanism, penalty mechanism, department, position**. HR forms consume them as dropdowns. Only the Admin role can edit the lists.

### Task 5.1: Lookup model + service + seed

**Files:**
- Create: `common/config/__init__.py`, `common/config/models.py`, `common/config/services.py`
- Modify: `business_web/settings.py` `INSTALLED_APPS` if a new app label is needed (else keep models under an existing migrated app — prefer adding to `employee_profiles` app to avoid new-app wiring; place model in `employee_profiles/models/lookup_model.py`).
- Migration: `employee_profiles/migrations/000X_lookupoption.py` (+ data migration to seed categories)
- Test: `employee_profiles/tests/test_lookup.py` (create)

**Decision:** to minimize wiring, put the model in the existing `employee_profiles` app.

**Interfaces:**
- Produces: `employee_profiles.models.LookupOption(category, value, is_active, order)` with `CATEGORY_CHOICES = [('department',...),('position',...),('workplace',...),('contract_type',...),('reward_mechanism',...),('penalty_mechanism',...)]`.
- Produces: `employee_profiles.services.lookup.option_choices(category, blank_label='-- Chọn --') -> list[tuple]` and `active_values(category) -> list[str]`.

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase
from employee_profiles.models import LookupOption
from employee_profiles.services.lookup import option_choices


class LookupTest(TestCase):
    def test_option_choices_filters_active_by_category(self):
        LookupOption.objects.create(category='department', value='Phòng Kinh doanh', order=1)
        LookupOption.objects.create(category='department', value='Phòng Kế toán', order=2)
        LookupOption.objects.create(category='department', value='Đã xóa', is_active=False)
        LookupOption.objects.create(category='position', value='Trưởng phòng')
        choices = option_choices('department')
        values = [v for v, _ in choices if v]
        self.assertEqual(values, ['Phòng Kinh doanh', 'Phòng Kế toán'])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test employee_profiles.tests.test_lookup -v 2`
Expected: FAIL ("cannot import name 'LookupOption'").

- [ ] **Step 3: Implement model**

```python
# employee_profiles/models/lookup_model.py
from django.db import models


class LookupOption(models.Model):
    DEPARTMENT = 'department'
    POSITION = 'position'
    WORKPLACE = 'workplace'
    CONTRACT_TYPE = 'contract_type'
    REWARD_MECHANISM = 'reward_mechanism'
    PENALTY_MECHANISM = 'penalty_mechanism'
    CATEGORY_CHOICES = [
        (DEPARTMENT, 'Phòng ban'),
        (POSITION, 'Chức vụ'),
        (WORKPLACE, 'Nơi làm việc'),
        (CONTRACT_TYPE, 'Loại hợp đồng'),
        (REWARD_MECHANISM, 'Cơ chế khen thưởng'),
        (PENALTY_MECHANISM, 'Cơ chế xử phạt'),
    ]
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    value = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category', 'order', 'value']
        unique_together = [('category', 'value')]

    def __str__(self):
        return f'{self.get_category_display()}: {self.value}'
```

Export it in `employee_profiles/models/__init__.py`.

- [ ] **Step 4: Implement service**

```python
# employee_profiles/services/lookup.py
from employee_profiles.models import LookupOption


def active_values(category):
    return list(
        LookupOption.objects.filter(category=category, is_active=True)
        .values_list('value', flat=True)
    )


def option_choices(category, blank_label='-- Chọn --'):
    choices = [(v, v) for v in active_values(category)]
    return [('', blank_label)] + choices
```

- [ ] **Step 5: Make migrations + seed data migration**

```bash
python manage.py makemigrations employee_profiles
```

Then add a data migration seeding a few defaults per category (e.g. departments: Phòng Kinh doanh / Kế toán / Nhân sự / Kỹ thuật; contract types: Thử việc / Xác định thời hạn / Không xác định thời hạn; reward mechanisms: Thưởng nóng / Thưởng tháng / Thưởng dự án; penalty mechanisms: Nhắc nhở / Khiển trách / Cảnh cáo / Phạt tiền).

- [ ] **Step 6: Run tests to verify pass**

Run: `python manage.py test employee_profiles.tests.test_lookup -v 2`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add employee_profiles/models/ employee_profiles/services/lookup.py employee_profiles/migrations/ employee_profiles/tests/test_lookup.py
git commit -m "feat(config): admin lookup model + service + seed (#28-33 base)"
```

### Task 5.2: Admin-only management page for lookup lists

**Files:**
- Create: view `employee_profiles/views/config_views.py` (`system_config_view`), URL name `system_config`, template `employee_profiles/templates/employee_profiles/system_config.html`
- Modify: `employee_profiles/urls.py` (or the project urls) to register the route; add a nav entry visible only when `is_admin_user`.
- Test: `employee_profiles/tests/test_config_access.py` (create)

**Interfaces:**
- Guard: `@user_passes_test(is_admin_user)`. POST actions: `add` (category+value), `toggle` (option_id), `delete` (option_id). HR/Manager get 302 redirect + error message.

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from employee_profiles.models import LookupOption


class ConfigAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)
        self.admin = User.objects.create_user('admin_u', password='x')
        UserProfile.objects.create(user=self.admin, role=self.admin_role, employee_id='ADM')
        self.hr = User.objects.create_user('hr_u', password='x')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR')

    def test_hr_cannot_open_config(self):
        self.client.login(username='hr_u', password='x')
        resp = self.client.get(reverse('system_config'))
        self.assertEqual(resp.status_code, 302)

    def test_admin_can_add_option(self):
        self.client.login(username='admin_u', password='x')
        self.client.post(reverse('system_config'), {
            'action': 'add', 'category': 'department', 'value': 'Phòng IT',
        })
        self.assertTrue(LookupOption.objects.filter(category='department', value='Phòng IT').exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test employee_profiles.tests.test_config_access -v 2`
Expected: FAIL (no `system_config` URL).

- [ ] **Step 3: Implement view + url + template** (CRUD over `LookupOption`, grouped by category, Admin-only). Render existing options with toggle/delete buttons and an add form per category.

- [ ] **Step 4: Run tests to verify pass**

Run: `python manage.py test employee_profiles.tests.test_config_access -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add employee_profiles/views/config_views.py employee_profiles/urls.py employee_profiles/templates/employee_profiles/system_config.html employee_profiles/tests/test_config_access.py
git commit -m "feat(config): admin-only management page for lookup lists (#28-33)"
```

### Task 5.3: Consume lookups in profile/contract/reward forms

**Files:**
- Modify: `employee_profiles/forms.py` — `department`, `position`, `workplace` become `ChoiceField` whose choices come from `option_choices(...)` in `__init__`.
- Modify: `contracts/forms.py` — `contract_type` becomes a `ChoiceField` from `option_choices('contract_type')`.
- Modify: `rewards_discipline/forms.py` — add `mechanism` `ChoiceField` (reward/penalty depending on `record_type`) from lookups; map onto `reason_title` or a new model field.
- Modify: create-profile template + view to render selects (free-text fallback allowed if list empty).
- Test: `employee_profiles/tests/test_form_lookup_choices.py` (create)

**Interfaces:**
- Forms must degrade gracefully: if a category has zero active options, keep a text input so HR is never blocked.

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase
from employee_profiles.models import LookupOption
from employee_profiles.forms import EmployeeProfileForm


class FormLookupChoicesTest(TestCase):
    def test_department_choices_come_from_lookup(self):
        LookupOption.objects.create(category='department', value='Phòng IT')
        form = EmployeeProfileForm()
        values = [v for v, _ in form.fields['department'].choices if v]
        self.assertIn('Phòng IT', values)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test employee_profiles.tests.test_form_lookup_choices -v 2`
Expected: FAIL (`department` is a free-text `CharField`).

- [ ] **Step 3: Implement** — convert the three work fields in `EmployeeProfileForm` to `ChoiceField` and set `.choices` in `__init__` via `option_choices('department')` etc.; same pattern for `contracts.forms.ContractAdjustForm.contract_type` and the reward mechanism. Use `forms.ChoiceField(required=False)` and assign choices in `__init__` so DB is queried at runtime, not import time.

- [ ] **Step 4: Run tests to verify pass**

Run: `python manage.py test employee_profiles.tests.test_form_lookup_choices employee_profiles.tests.test_education_choices -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add employee_profiles/forms.py contracts/forms.py rewards_discipline/forms.py employee_profiles/templates/ employee_profiles/views/profile_views.py employee_profiles/tests/test_form_lookup_choices.py
git commit -m "feat(config): consume admin lookups as dropdowns in HR forms (#28-33)"
```

---

## PHASE 6 — Evaluation create/submit fix + subordinate target (#4)

> Decided: fix create/submit; the evaluator must see a dropdown of the employees they supervise (their subordinates) to evaluate.

### Task 6.1: Evaluation form exposes a subordinate `target_user` and saves correctly

**Files:**
- Modify: `performance/forms.py` (`EvaluationForm`) — add `target_user` field scoped to subordinates.
- Modify: `performance/services/evaluation_data.py` (`build_evaluations_page_context` / create logic) — accept `target_user`, persist it, compute `score → rating`.
- Modify: `performance/views/__init__.py` if it must pass the evaluator to the form.
- Modify: `performance/templates/performance/evaluations.html` — render the `target_user` select + score/rating.
- Test: `performance/tests/test_evaluation_create.py` (create)

**Interfaces:**
- Subordinate set = users where `work_info.leader_user == evaluator` OR `work_info.manager_user == evaluator`. Exclude self. Mirror the proven query in `RewardPenaltyForm`.
- `score → rating`: ≥90 A, ≥75 B, ≥60 C, else D (matches `sequence_diagrams (1).md` §7.2).

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from performance.models import Evaluation, EvaluationCategory


class EvaluationCreateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.mgr_role, _ = Role.objects.get_or_create(name=Role.MANAGER)
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.mgr = User.objects.create_user('mgr', password='x')
        UserProfile.objects.create(user=self.mgr, role=self.mgr_role, employee_id='M1')
        self.sub = User.objects.create_user('sub', password='x')
        UserProfile.objects.create(user=self.sub, role=self.emp_role, employee_id='S1')
        EmployeeWorkInfo.objects.create(user=self.sub, manager_user=self.mgr)
        self.cat = EvaluationCategory.objects.create(name='Hiệu suất')
        self.client.login(username='mgr', password='x')

    def test_manager_lists_only_subordinates(self):
        resp = self.client.get(reverse('evaluations'))
        self.assertContains(resp, 'sub')      # subordinate selectable
        self.assertNotContains(resp, '>mgr<')  # not self

    def test_submit_creates_evaluation_with_rating(self):
        self.client.post(reverse('evaluations'), {
            'target_user': self.sub.id, 'category': self.cat.id,
            'score': 92, 'evaluation_date': '2026-06-22', 'content': 'Tốt',
        })
        ev = Evaluation.objects.get(employee=self.sub)
        self.assertEqual(ev.status, 'submitted')
        self.assertEqual(ev.rating, 'A')
```

> Confirm the exact `Evaluation` field names (`employee` vs `target_user`, `rating` storage) by reading `performance/models/` during execution and adjust the assertions/save accordingly.

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test performance.tests.test_evaluation_create -v 2`
Expected: FAIL (no `target_user` field / create path broken).

- [ ] **Step 3: Implement** — add `target_user = UserChoiceField(...)` to `EvaluationForm`, scoped in `__init__(evaluator=...)` to subordinates; in the create service set `evaluation.employee = target_user`, `evaluation.evaluator = request.user`, `status='submitted'`, and `rating` from the score thresholds. Render the select + computed rating in the template.

- [ ] **Step 4: Run tests to verify pass**

Run: `python manage.py test performance.tests.test_evaluation_create performance.tests -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add performance/forms.py performance/services/evaluation_data.py performance/views/__init__.py performance/templates/performance/evaluations.html performance/tests/test_evaluation_create.py
git commit -m "fix(evaluation): subordinate target dropdown + working submit with rating (#4)"
```

---

## PHASE 7 — Full regression

### Task 7.1: Run the whole suite

- [ ] **Step 1: Run all tests**

Run: `python manage.py test -v 1`
Expected: PASS (0 failures, 0 errors). Fix any regression before finishing.

- [ ] **Step 2: Manual smoke (optional, via /run skill)** — log in as Admin (config lists), HR (create profile w/ evidence, edit contract), Manager (evaluate subordinate), employee (edit profile w/ bad phone → sees error; logout → Back → login required).

- [ ] **Step 3: Commit any fixes**

```bash
git add -A
git commit -m "test: full regression green after bugfix+evolution"
```

---

## Self-Review notes (spec coverage)

| Bug item | Task |
|---|---|
| #1 leader/manager reward scope | 0.1 |
| #2 remove timesheet ticket type | 0.3 |
| #3 ticket reception HR/Admin only | 0.2 |
| #4 evaluation create/submit + subordinates | 6.1 |
| #5 evidence upload on create | 4.1 |
| #6 leader cannot approve reward | 0.2 |
| #7 remove tax code | 2.4 |
| #11/#12 logout back-button | 1.1 |
| #13/#14 admin create-account session | 1.2 |
| #16/#21 phone validation | 2.1, 2.2 |
| #17/#18 education dropdown | 2.3 |
| #19 searchable major | 2.3 |
| #20/#22 personal-info validation + errors | 2.2 |
| #23/#24 probation vs official date | 3.1 |
| #25/#26 contract date order (equal-day) | 3.2 |
| #27 shift-time error surfacing | 3.3 |
| #28–33 evolution config lists | 5.1, 5.2, 5.3 |

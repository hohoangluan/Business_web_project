# Attendance Folder Sectioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the Django `attendance` app's `services/`, `views/`, `forms/`, `templates/`, and `tests/` into feature sub-packages (`face/`, `adjustment/`, `record/`) matching the `accounts` app convention, with zero behavior change.

**Architecture:** Pure structural refactor. Files move into feature sub-folders via `git mv`. Each type-package `__init__.py` re-exports its public API so shallow imports (`from attendance.services import X`) keep working. Deep imports and template strings are repointed via an exhaustive, deterministic find-replace table. The attendance test suite is the safety net after every task.

**Tech Stack:** Django 6.0 / Python 3.13 / SQLite (dev). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-05-31-attendance-folder-sectioning-design.md` (HEAD `a003282`).

**Test runner:** `python manage.py test attendance` — run from the `business_web/` directory.

**Note on environment:** All paths below are relative to repo root unless stated. The app root is `business_web/attendance/`. Commands assume you `cd business_web` first.

---

## Master Path Map (old → new)

This table is the single source of truth. Every deep import string and template string in the table must be replaced project-wide. Shallow imports (`from attendance.services import name`) are preserved by the re-export `__init__.py` files and need no change.

### Python module paths

| Old dotted path | New dotted path |
|---|---|
| `attendance.services.face_api_client` | `attendance.services.face.face_api_client` |
| `attendance.services.face_lockout_service` | `attendance.services.face.face_lockout_service` |
| `attendance.services.face_service` | `attendance.services.face.face_service` |
| `attendance.services.face_verification_service` | `attendance.services.face.face_verification_service` |
| `attendance.services.image_service` | `attendance.services.face.image_service` |
| `attendance.services.attendance_logging_service` | `attendance.services.record.attendance_logging_service` |
| `attendance.views.face_attendance_view` | `attendance.views.face.face_attendance_view` |
| `attendance.views.image_upload_view` | `attendance.views.face.image_upload_view` |
| `attendance.views.attendance_adjustment_view` | `attendance.views.adjustment.attendance_adjustment_view` |
| `attendance.forms.attendance_adjustment_form` | `attendance.forms.adjustment.attendance_adjustment_form` |

> `attendance_view` is currently defined **inline** in `attendance/views/__init__.py` (not a module). Task 2 extracts it to `attendance/views/record/attendance_view.py`.

### Template strings

| Old template string | New template string |
|---|---|
| `attendance/attendance.html` | `attendance/record/attendance.html` |
| `attendance/adjustment_request_form.html` | `attendance/adjustment/adjustment_request_form.html` |

### Filesystem moves

| Old file | New file |
|---|---|
| `services/face_api_client.py` | `services/face/face_api_client.py` |
| `services/face_lockout_service.py` | `services/face/face_lockout_service.py` |
| `services/face_service.py` | `services/face/face_service.py` |
| `services/face_verification_service.py` | `services/face/face_verification_service.py` |
| `services/image_service.py` | `services/face/image_service.py` |
| `services/attendance_logging_service.py` | `services/record/attendance_logging_service.py` |
| `views/face_attendance_view.py` | `views/face/face_attendance_view.py` |
| `views/image_upload_view.py` | `views/face/image_upload_view.py` |
| `views/attendance_adjustment_view.py` | `views/adjustment/attendance_adjustment_view.py` |
| (inline in `views/__init__.py`) | `views/record/attendance_view.py` (extracted) |
| `forms/attendance_adjustment_form.py` | `forms/adjustment/attendance_adjustment_form.py` |
| `templates/attendance/attendance.html` | `templates/attendance/record/attendance.html` |
| `templates/attendance/adjustment_request_form.html` | `templates/attendance/adjustment/adjustment_request_form.html` |
| `tests/test_face_*.py`, `tests/test_image_upload_view.py`, `tests/test_app_ready_warmup.py` | `tests/face/<same name>` |
| `tests/test_attendance_adjustment_view.py` | `tests/adjustment/<same name>` |
| `tests/test_attendance_logging_service.py`, `tests/test_attendance_view_context.py`, `tests/test_close_open_attendance_command.py` | `tests/record/<same name>` |

**Stays put:** `models/` (flat), `migrations/` (Django), `management/commands/`, `tests/fixtures/`, `tests/forms.py`, `tests/__init__.py`.

---

## Task 0: Baseline — confirm green before touching anything

**Files:** none.

- [ ] **Step 1: Run the full attendance suite to capture the baseline**

Run: `cd business_web && python manage.py test attendance -v 1`
Expected: PASS (all tests green). Record the test count. If anything fails here, STOP — the refactor's safety net is broken; fix or report before proceeding.

---

## Task 1: Section the `services/` folder

**Files:**
- Create dir: `business_web/attendance/services/face/` with `__init__.py`
- Create dir: `business_web/attendance/services/record/` with `__init__.py`
- Move: 6 service files (see Master Path Map)
- Modify: `business_web/attendance/services/__init__.py` (currently empty → re-export)
- Modify (repoint deep service imports): `business_web/attendance/views/face_attendance_view.py`, `business_web/attendance/views/image_upload_view.py`, `business_web/attendance/views/__init__.py`, `business_web/attendance/management/commands/close_open_attendance.py`

- [ ] **Step 1: Create the sub-package directories with empty inits**

```bash
cd business_web/attendance/services
mkdir face record
new-item -ItemType File face/__init__.py    # PowerShell; or: touch face/__init__.py
new-item -ItemType File record/__init__.py   # PowerShell; or: touch record/__init__.py
```

Both `__init__.py` files stay empty (submodule imports work with empty package inits).

- [ ] **Step 2: Move the service files with git mv**

```bash
cd business_web/attendance/services
git mv face_api_client.py face/face_api_client.py
git mv face_lockout_service.py face/face_lockout_service.py
git mv face_service.py face/face_service.py
git mv face_verification_service.py face/face_verification_service.py
git mv image_service.py face/image_service.py
git mv attendance_logging_service.py record/attendance_logging_service.py
```

- [ ] **Step 3: Write the re-export `services/__init__.py`**

Overwrite `business_web/attendance/services/__init__.py` with:

```python
"""Public service exports for the attendance app.

Re-exports submodules so existing shallow imports keep working, e.g.
``from attendance.services import face_api_client``.
"""
from attendance.services.face import (
    face_api_client,
    face_lockout_service,
    face_service,
    face_verification_service,
    image_service,
)
from attendance.services.record import attendance_logging_service

__all__ = [
    "face_api_client",
    "face_lockout_service",
    "face_service",
    "face_verification_service",
    "image_service",
    "attendance_logging_service",
]
```

This keeps `attendance/apps.py`'s `from attendance.services import face_api_client` working with no edit to `apps.py`.

- [ ] **Step 4: Repoint deep service imports in importer files**

Apply the **Python module paths** replacements from the Master Path Map for the `services.*` rows in these four files only:

- `business_web/attendance/views/face_attendance_view.py` — change `attendance.services.attendance_logging_service` → `attendance.services.record.attendance_logging_service`; `attendance.services.face_lockout_service` → `attendance.services.face.face_lockout_service`; `attendance.services.face_verification_service` → `attendance.services.face.face_verification_service`.
- `business_web/attendance/views/image_upload_view.py` — change `attendance.services.face_service` → `attendance.services.face.face_service`; `attendance.services.face_api_client` → `attendance.services.face.face_api_client`.
- `business_web/attendance/views/__init__.py` — change `attendance.services.attendance_logging_service` → `attendance.services.record.attendance_logging_service` (the `get_open_previous_record` import used by the inline `attendance_view`).
- `business_web/attendance/management/commands/close_open_attendance.py` — change `attendance.services.attendance_logging_service` → `attendance.services.record.attendance_logging_service`.

- [ ] **Step 5: Run the suite**

Run: `cd business_web && python manage.py test attendance -v 1`
Expected: PASS, same test count as Task 0. (Tests using shallow `from attendance.services import X` survive via re-export; tests using deep service paths are fixed in Task 5 — if any fail here with `ModuleNotFoundError: attendance.services.<name>`, that is a deep test import; defer its fix to Task 5 OR apply the path-map replacement to that test file now and note it.)

> If deep-import test failures appear, the cleanest move is to run the global replace from Task 5's table against the `tests/` tree now. It is idempotent and safe to run early.

- [ ] **Step 6: Commit**

```bash
git add business_web/attendance/services business_web/attendance/views business_web/attendance/management
git commit -m "refactor(attendance): section services into face/ and record/"
```

---

## Task 2: Section the `views/` folder and extract `attendance_view`

**Files:**
- Create dir: `business_web/attendance/views/face/`, `views/adjustment/`, `views/record/` each with `__init__.py`
- Create: `business_web/attendance/views/record/attendance_view.py` (extracted from `views/__init__.py`)
- Move: 3 view files (see Master Path Map)
- Modify: `business_web/attendance/views/__init__.py` (re-export)
- Modify: `business_web/attendance/urls.py` (shallow imports)

- [ ] **Step 1: Create the sub-package directories**

```bash
cd business_web/attendance/views
mkdir face adjustment record
new-item -ItemType File face/__init__.py
new-item -ItemType File adjustment/__init__.py
new-item -ItemType File record/__init__.py
```

- [ ] **Step 2: Move the existing view files**

```bash
cd business_web/attendance/views
git mv face_attendance_view.py face/face_attendance_view.py
git mv image_upload_view.py face/image_upload_view.py
git mv attendance_adjustment_view.py adjustment/attendance_adjustment_view.py
```

- [ ] **Step 3: Create `views/record/attendance_view.py` with the extracted view**

Create `business_web/attendance/views/record/attendance_view.py`:

```python
"""Views cho chấm công."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from accounts.services import ensure_profile
from attendance.models import AttendanceRecord, AttendanceAdjustmentRequest
from attendance.services.record.attendance_logging_service import get_open_previous_record


def _history_rows(user, limit=10):
    today = timezone.localdate()
    first_of_month = today.replace(day=1)
    return list(
        AttendanceRecord.objects
        .filter(user=user, record_date__gte=first_of_month)
        .order_by('-record_date')[:limit]
    )


@login_required
def attendance_view(request):
    """Trang chấm công. Real data."""
    ensure_profile(request.user)

    open_prev = get_open_previous_record(request.user)
    # banner_eligible_for_adjustment = status is exactly 'no_checkout' (no submission yet)
    eligible = (
        open_prev is not None
        and open_prev.status == 'no_checkout'
        and not AttendanceAdjustmentRequest.objects.filter(record=open_prev).exists()
    )

    return render(request, 'attendance/attendance.html', {
        'active_page': 'attendance',
        'open_previous_record': open_prev,
        'banner_eligible_for_adjustment': eligible,
        'history_rows': _history_rows(request.user),
        'today_short': timezone.localdate().strftime('%d/%m'),
    })
```

> The render string stays `'attendance/attendance.html'` for now; Task 4 moves the template and updates this string. The unused `from datetime import timedelta` from the original `__init__.py` is intentionally dropped (it was dead).

- [ ] **Step 4: Replace `views/__init__.py` with re-exports**

Overwrite `business_web/attendance/views/__init__.py`:

```python
"""Public view exports for the attendance app."""

from attendance.views.record.attendance_view import attendance_view
from attendance.views.face.face_attendance_view import face_check_view
from attendance.views.face.image_upload_view import (
    get_image_base64_view,
    upload_image_base64_view,
)
from attendance.views.adjustment.attendance_adjustment_view import submit_adjustment_view

__all__ = [
    "attendance_view",
    "face_check_view",
    "get_image_base64_view",
    "submit_adjustment_view",
    "upload_image_base64_view",
]
```

- [ ] **Step 5: Simplify `urls.py` to shallow imports**

Overwrite the import block of `business_web/attendance/urls.py` so lines 2–6 become:

```python
from django.urls import path

from attendance.views import (
    attendance_view,
    face_check_view,
    get_image_base64_view,
    submit_adjustment_view,
    upload_image_base64_view,
)
```

Leave the `urlpatterns` list unchanged (the callable names are identical).

- [ ] **Step 6: Run the suite**

Run: `cd business_web && python manage.py test attendance -v 1`
Expected: PASS, same count. (The adjustment view's `from attendance.forms.attendance_adjustment_form import ...` is still valid — forms not moved until Task 3.)

- [ ] **Step 7: Commit**

```bash
git add business_web/attendance/views business_web/attendance/urls.py
git commit -m "refactor(attendance): section views into face/adjustment/record + extract attendance_view"
```

---

## Task 3: Section the `forms/` folder

**Files:**
- Create dir: `business_web/attendance/forms/adjustment/` with `__init__.py`
- Move: `forms/attendance_adjustment_form.py`
- Modify: `business_web/attendance/forms/__init__.py` (re-export)
- Modify: `business_web/attendance/views/adjustment/attendance_adjustment_view.py` (repoint forms import)

- [ ] **Step 1: Create the sub-package directory**

```bash
cd business_web/attendance/forms
mkdir adjustment
new-item -ItemType File adjustment/__init__.py
```

- [ ] **Step 2: Move the form file**

```bash
cd business_web/attendance/forms
git mv attendance_adjustment_form.py adjustment/attendance_adjustment_form.py
```

- [ ] **Step 3: Write the re-export `forms/__init__.py`**

Overwrite `business_web/attendance/forms/__init__.py`:

```python
"""Public form exports for the attendance app."""

from attendance.forms.adjustment.attendance_adjustment_form import (
    AttendanceAdjustmentForm,
)

__all__ = ["AttendanceAdjustmentForm"]
```

- [ ] **Step 4: Repoint the deep forms import in the adjustment view**

In `business_web/attendance/views/adjustment/attendance_adjustment_view.py`, change:

```python
from attendance.forms.attendance_adjustment_form import AttendanceAdjustmentForm
```

to:

```python
from attendance.forms.adjustment.attendance_adjustment_form import AttendanceAdjustmentForm
```

- [ ] **Step 5: Run the suite**

Run: `cd business_web && python manage.py test attendance -v 1`
Expected: PASS, same count.

- [ ] **Step 6: Commit**

```bash
git add business_web/attendance/forms business_web/attendance/views/adjustment
git commit -m "refactor(attendance): section forms into adjustment/"
```

---

## Task 4: Section the `templates/` folder and update render strings

**Files:**
- Create dir: `business_web/attendance/templates/attendance/record/`, `.../adjustment/`
- Move: 2 template files
- Modify render strings in: `business_web/attendance/views/record/attendance_view.py`, `business_web/attendance/views/adjustment/attendance_adjustment_view.py`

- [ ] **Step 1: Create template sub-directories and move templates**

```bash
cd business_web/attendance/templates/attendance
mkdir record adjustment
git mv attendance.html record/attendance.html
git mv adjustment_request_form.html adjustment/adjustment_request_form.html
```

- [ ] **Step 2: Update render string in `attendance_view.py`**

In `business_web/attendance/views/record/attendance_view.py`, change `'attendance/attendance.html'` → `'attendance/record/attendance.html'`.

- [ ] **Step 3: Update render string in `attendance_adjustment_view.py`**

In `business_web/attendance/views/adjustment/attendance_adjustment_view.py`, change `'attendance/adjustment_request_form.html'` → `'attendance/adjustment/adjustment_request_form.html'`.

- [ ] **Step 4: Check for cross-references inside the moved templates**

Open `record/attendance.html` and `adjustment/adjustment_request_form.html`. Confirm any `{% extends %}` / `{% include %}` targets are unchanged (they reference `accounts/...` base templates by app-namespaced path, which did not move). No edits expected; if an `{% include 'attendance/...' %}` points at one of the two moved files, update it to the new path.

- [ ] **Step 5: Run the suite**

Run: `cd business_web && python manage.py test attendance -v 1`
Expected: PASS. (A `TemplateDoesNotExist` here means a render string or `{% include %}` was missed — fix per the Master Path Map.)

- [ ] **Step 6: Commit**

```bash
git add business_web/attendance/templates business_web/attendance/views
git commit -m "refactor(attendance): section templates into record/ and adjustment/"
```

---

## Task 5: Section the `tests/` folder

**Files:**
- Create dir: `business_web/attendance/tests/face/`, `tests/adjustment/`, `tests/record/` each with `__init__.py`
- Move: test files per the Master Path Map filesystem table
- Modify: any moved test that imports a deep `attendance.services|views|forms` path, or asserts a moved template string, or loads `tests/fixtures/` via a `__file__`-relative path

- [ ] **Step 1: Create test sub-package directories**

```bash
cd business_web/attendance/tests
mkdir face adjustment record
new-item -ItemType File face/__init__.py
new-item -ItemType File adjustment/__init__.py
new-item -ItemType File record/__init__.py
```

- [ ] **Step 2: Move the test files**

```bash
cd business_web/attendance/tests
git mv test_face_api_client.py face/test_face_api_client.py
git mv test_face_lockout_service.py face/test_face_lockout_service.py
git mv test_face_service.py face/test_face_service.py
git mv test_face_verification_service.py face/test_face_verification_service.py
git mv test_image_upload_view.py face/test_image_upload_view.py
git mv test_app_ready_warmup.py face/test_app_ready_warmup.py
git mv test_attendance_adjustment_view.py adjustment/test_attendance_adjustment_view.py
git mv test_attendance_logging_service.py record/test_attendance_logging_service.py
git mv test_attendance_view_context.py record/test_attendance_view_context.py
git mv test_close_open_attendance_command.py record/test_close_open_attendance_command.py
```

`tests/forms.py`, `tests/fixtures/`, and `tests/__init__.py` stay at the tests root.

- [ ] **Step 3: Apply the Master Path Map module + template replacements across the tests tree**

In every moved test file, replace each **old → new** string from the Master Path Map (both the *Python module paths* table and the *Template strings* table). This is a literal string replace — apply all rows; rows that do not appear in a given file are no-ops. After this, no test references a pre-move `attendance.services.<name>` / `attendance.views.<name>` / `attendance.forms.<name>` deep path or the old `attendance/attendance.html` / `attendance/adjustment_request_form.html` template strings.

- [ ] **Step 4: Fix fixture paths if any test loads `tests/fixtures/` relative to its own file**

A test moved from `tests/` to `tests/face/` is now one directory deeper, so a path built from its own `__file__` pointing at `fixtures/` will break. For any moved test that opens `sample_face.jpg`, anchor the path at the tests root:

```python
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SAMPLE_FACE = FIXTURES_DIR / "sample_face.jpg"
```

(`parent.parent` = from `tests/face/` up to `tests/`.) Apply only where a `__file__`-relative fixture path exists; leave tests that import the fixture path from a shared helper untouched.

- [ ] **Step 5: Run the suite**

Run: `cd business_web && python manage.py test attendance -v 2`
Expected: PASS, same count as Task 0, and `-v 2` output should show every test still collected (no silent drop from a missing `__init__.py`). If the count dropped, a sub-package is missing its `__init__.py`.

- [ ] **Step 6: Commit**

```bash
git add business_web/attendance/tests
git commit -m "refactor(attendance): section tests into face/adjustment/record"
```

---

## Task 6: Document the app-layout convention

**Files:**
- Modify: `README.md` (add a short pointer)
- Modify: `PROJECT_WALKTHROUGH.md` (add a short pointer)

- [ ] **Step 1: Add a convention note to `README.md`**

Append a short section (place it under any existing project-structure / development section, or at the end):

```markdown
## App layout convention

Apps that span multiple feature domains group their code by feature
sub-package inside each type folder (`forms/`, `services/`, `views/`,
`templates/<app>/`, `tests/`), mirroring `accounts` and `attendance`.
`models/` and `migrations/` stay flat. Each type-package `__init__.py`
re-exports its public API so `from <app>.views import X` works regardless
of sub-package. Do not pre-create empty feature folders in stub apps —
add them when the code arrives. See
`docs/superpowers/specs/2026-05-31-attendance-folder-sectioning-design.md`.
```

- [ ] **Step 2: Add the same pointer to `PROJECT_WALKTHROUGH.md`**

Add a one-line cross-reference under the most relevant existing structure section:

```markdown
> **App layout convention:** multi-domain apps section code by feature inside each type folder (see `accounts`, `attendance`). Details: `docs/superpowers/specs/2026-05-31-attendance-folder-sectioning-design.md`.
```

- [ ] **Step 3: Commit**

```bash
git add README.md PROJECT_WALKTHROUGH.md
git commit -m "docs: record app-layout sectioning convention"
```

---

## Task 7: Final verification

**Files:** none.

- [ ] **Step 1: Full attendance suite, verbose**

Run: `cd business_web && python manage.py test attendance -v 2`
Expected: PASS, test count equals the Task 0 baseline.

- [ ] **Step 2: Django system check**

Run: `cd business_web && python manage.py check`
Expected: `System check identified no issues`.

- [ ] **Step 3: Confirm no stale references remain**

Run (any reported hit must be a *new* path, not an old one):

```bash
cd business_web
grep -rn "attendance.services.face_api_client\|attendance.services.face_lockout_service\|attendance.services.face_service\|attendance.services.face_verification_service\|attendance.services.image_service\|attendance.services.attendance_logging_service\|attendance.views.face_attendance_view\|attendance.views.image_upload_view\|attendance.views.attendance_adjustment_view\|attendance.forms.attendance_adjustment_form\|attendance/attendance.html\|attendance/adjustment_request_form.html" --include=*.py --include=*.html . | grep -v __pycache__
```

Expected: every remaining hit is a re-export `__init__.py` line pointing at a **new** sub-package path (e.g. `attendance.services.face.face_service`) or a `{% extends %}` in a moved template — i.e. nothing references a pre-move flat path. If a flat old path appears outside an `__init__.py` re-export, fix it via the Master Path Map and re-run Steps 1–3.

- [ ] **Step 4: Run the whole project test suite (sanity)**

Run: `cd business_web && python manage.py test`
Expected: no new failures versus a pre-refactor run (only `attendance` was touched).

---

## Self-Review Notes

- **Spec coverage:** services/views/forms/templates/tests sectioning (Tasks 1–5) ✓; `attendance_view` extraction (Task 2) ✓; re-export import strategy "A" (each task's `__init__.py`) ✓; template-string updates (Task 4) ✓; convention doc (Task 6) ✓; `models/`+`migrations/` left flat ✓; `tests/fixtures` + `tests/forms.py` at root ✓; verification via `manage.py test attendance` (Tasks 0 & 7) ✓.
- **No `face/` template folder** — consistent with spec (face flow has no template).
- **Green at every commit** — each task ends with a passing suite; ordering keeps not-yet-moved deep imports valid until their own task.

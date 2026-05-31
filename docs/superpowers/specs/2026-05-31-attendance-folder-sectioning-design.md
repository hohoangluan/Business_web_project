# Attendance Folder Sectioning — Design

**Date:** 2026-05-31
**Status:** Approved
**Scope:** Restructure the `attendance` app into feature sub-folders matching the `accounts` app convention. Document the convention for other apps; do not pre-create folders in stub apps.

## Problem

The `accounts` app groups its code into feature sub-packages (`auth/`, `account/`, `permission/`) inside each type folder (`views/`, `services/`, `forms/`, `templates/`), with each type-package `__init__.py` re-exporting its public API. No other app follows this. `attendance` has grown enough — face recognition, attendance adjustment, and core record logging — that its flat `services/`, `views/`, etc. mix unrelated concerns. The remaining apps are either small single-domain (`contracts`, `employee_profiles`) or stubs (`leaves`, `overtime`, `performance`, `reports_interactions`, `rewards_discipline`, `stats_reports`) and do not yet justify sectioning.

## Decision

Apply accounts-style sectioning to `attendance` only. Leave small and stub apps flat. Document the convention so future code in any app lands in the right place.

## Feature Sections

Three domains in `attendance`:

- **`face`** — face capture, embedding, verification, lockout, image upload
- **`adjustment`** — attendance adjustment requests
- **`record`** — core attendance record view + logging

## File Moves

| Folder | → Section | Files |
|---|---|---|
| `services/` | `face/` | `face_api_client.py`, `face_lockout_service.py`, `face_service.py`, `face_verification_service.py`, `image_service.py` |
| `services/` | `record/` | `attendance_logging_service.py` |
| `views/` | `face/` | `face_attendance_view.py`, `image_upload_view.py` |
| `views/` | `adjustment/` | `attendance_adjustment_view.py` |
| `views/` | `record/` | `attendance_view.py` (**extracted** from current `views/__init__.py`) |
| `forms/` | `adjustment/` | `attendance_adjustment_form.py` |
| `templates/attendance/` | `record/` | `attendance.html` |
| `templates/attendance/` | `adjustment/` | `adjustment_request_form.html` |
| `tests/` | `face/` | `test_face_api_client.py`, `test_face_lockout_service.py`, `test_face_service.py`, `test_face_verification_service.py`, `test_image_upload_view.py`, `test_app_ready_warmup.py` |
| `tests/` | `adjustment/` | `test_attendance_adjustment_view.py` |
| `tests/` | `record/` | `test_attendance_logging_service.py`, `test_attendance_view_context.py`, `test_close_open_attendance_command.py` |

### Unchanged

- `models/` — stays flat (accounts keeps `models/` flat too).
- `migrations/` — stays flat (Django requirement).
- `management/commands/` — stays as is.
- `tests/fixtures/` and `tests/forms.py` — shared test helpers, stay at `tests/` root.
- No `face/` template folder — the face flow has no template (JS + API on the record page).

Each new feature sub-package gets an `__init__.py`.

## Import Strategy

**Re-export at the type-package level (matches accounts).**

Each type-package `__init__.py` re-exports its public API so existing shallow imports keep working:

- `from attendance.services import …`
- `from attendance.views import …`
- `from attendance.forms import …`

Then update the deep importers to the new paths:

- `attendance/urls.py` — imports `attendance.views.image_upload_view`, `attendance.views.face_attendance_view`, `attendance.views.attendance_adjustment_view`, and `attendance.views.attendance_view`. The `attendance_view` import currently resolves via `views/__init__.py`; after extraction it lives at `views/record/attendance_view.py` and is re-exported from `views/__init__.py`.
- `attendance/apps.py` — app ready / warmup logic referencing face services.
- `attendance/management/commands/close_open_attendance.py` — references logging service.
- Test modules — update to new deep paths (or rely on shallow re-exports where they already use them).

Rejected alternatives:

- **B — rewrite every import to deep paths, no re-exports:** more churn, diverges from accounts.
- **C — re-exports only, leave deep imports broken:** breaks tests; rejected.

## Template Path Updates

`render()` template strings change to include the section:

- `'attendance/attendance.html'` → `'attendance/record/attendance.html'`
- `'attendance/adjustment_request_form.html'` → `'attendance/adjustment/adjustment_request_form.html'`

Grep the codebase for these strings and update all occurrences.

## App Layout Convention (for future apps)

When an app grows beyond a single domain, group code by feature sub-package inside each type folder, mirroring `accounts` and `attendance`:

```
<app>/
  models/                 # flat — one file per model
  forms/<feature>/...
  services/<feature>/...
  views/<feature>/...
  templates/<app>/<feature>/...
  tests/<feature>/...      # fixtures/ and shared helpers at tests/ root
  migrations/             # flat — Django requirement
```

Each type-package `__init__.py` re-exports its public API so `from <app>.views import X` works regardless of sub-package. Do **not** pre-create empty feature folders in stub apps — add them when the code arrives. A short note pointing here goes in `README.md` / `PROJECT_WALKTHROUGH.md`.

## Verification

After the move:

```
python manage.py test attendance
```

Green suite confirms imports and template paths are intact. This is the safety net for the whole refactor.

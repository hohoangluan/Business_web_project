# Face Recognition Attendance — Design Spec

- **Date:** 2026-05-27
- **Branch:** `feature/attendance`
- **Author:** hohoangluan2006@gmail.com
- **Status:** Approved (pre-implementation)

## 1. Goal

Add a face-recognition check-in/check-out flow to the existing `attendance` Django app. Frontend captures a webcam frame, Django calls an existing local FastAPI face service (Facenet512 + FAISS + MongoDB) in `backend/backend/`, Django interprets the result, and an `AttendanceRecord` row is created or updated accordingly. Each function has a single responsibility.

## 2. Scope

**In:**
- Django-side enrollment that mirrors locally stored base64 to the FastAPI registry.
- Django-side daily check-in/check-out endpoint backed by FastAPI `/recognize`.
- 1:1 verify against the logged-in user (`employee_id == str(user.id)`).
- Lockout after repeated wrong-person verifications (cache-backed).
- Auto direction selection: first scan of the day → check-in; second → check-out; third → no-op.
- Replace template fake-alert buttons with real webcam capture and result UI.
- Unit + integration tests for each new service and the view.
- **Remove hardcoded `MONGO_URI` credentials** from `backend/backend/main.py` and `backend/backend/db_tools.py`. Service must fail fast at startup when `MONGO_URI` env var is unset. Add `.env.example` documenting the variable. Rotate the leaked Atlas password (out-of-band — separate action by repo owner).

**Out (explicitly):**
- Liveness / anti-spoof.
- Kiosk (1:N identify) mode.
- Background async (Celery) retries.
- Admin bulk enrollment UI.
- Adding auth to FastAPI (relies on 127.0.0.1 binding for now).
- Per-team / per-employee late thresholds.
- Holiday/leave integration with attendance status.

## 3. Existing context

### 3.1 Django app (`business_web/attendance/`)

- `models/attendance_record_model.py` — `AttendanceRecord(user, record_date, check_in_time, check_out_time, status)`, `unique_together=(user, record_date)`. Fits as-is.
- `models/employee_face_model.py` — `EmployeeFace(user, face_base64, content_type, updated_at, created_at)`, OneToOne with `User`. Stays as local preview/cache.
- `services/face_service.py` — `save_employee_face`, `get_employee_face`, `delete_employee_face`. **Will be modified** so save also pushes to the FastAPI registry.
- `services/image_service.py` — `image_to_base64`. Keep.
- `views/image_upload_view.py` — `upload_image_base64_view`, `get_image_base64_view`. Upload view path will be modified to trigger remote enrollment.
- `views/__init__.py` — `attendance_view` renders `attendance/attendance.html` with mock data. Template will be modified for real webcam flow.
- `urls.py` — adds one new route.

### 3.2 FastAPI service (`backend/backend/main.py`)

- Engine: DeepFace `Facenet512` → 512-d embeddings → FAISS `IndexFlatIP` + `IndexIDMap` (cosine on L2-normalized vectors).
- Threshold: `0.40` cosine distance (smaller = stricter).
- Storage: MongoDB Atlas, collections `employee_faces`, `id_mappings`. Multi-slot per employee (1..5).
- Endpoints used:
  - `POST /register` — multipart `{employee_id: str, slot_id?: int, file}` → `{status, message}`. Auto-picks free slot when `slot_id` omitted; raises 400 when 5 slots full.
  - `POST /recognize` — multipart `{file}` → `{status:'success', employee_id, confidence, match_slot}` on hit, `{status:'fail', message}` on miss/empty registry.
  - `GET /health` — pre-flight.
- Bound to localhost port `7860` (Docker `EXPOSE 7860`, dev `uvicorn main:app`).

### 3.3 Credential leak fix (in scope this phase)

`backend/backend/main.py:15` and `backend/backend/db_tools.py:6` embed a full MongoDB Atlas connection string with username + password as the `os.getenv` default. This phase removes those defaults and forces fail-fast startup when `MONGO_URI` is unset. See §5.8 for the exact change. Atlas password rotation itself is an out-of-band action by the repo owner.

## 4. Architecture

### 4.1 Module layout

```
business_web/attendance/
├── services/
│   ├── face_api_client.py            NEW  pure HTTP -> FastAPI :7860
│   ├── face_verification_service.py  NEW  1:1 verify orchestration
│   ├── attendance_logging_service.py NEW  check-in/out decision + write
│   ├── face_lockout_service.py       NEW  cache-backed fail counter
│   ├── face_service.py               MOD  add register-remote on save
│   ├── image_service.py              KEEP base64 helpers
│   └── __init__.py
├── views/
│   ├── face_attendance_view.py       NEW  POST /attendance/check/
│   ├── image_upload_view.py          MOD  remote enroll on upload
│   └── __init__.py                   KEEP attendance_view (history wired)
├── models/
│   ├── attendance_record_model.py    KEEP
│   ├── employee_face_model.py        KEEP
│   └── __init__.py
├── templates/attendance/
│   └── attendance.html               MOD  webcam capture + real API
├── tests/
│   ├── test_face_api_client.py            NEW
│   ├── test_face_verification_service.py  NEW
│   ├── test_attendance_logging_service.py NEW
│   ├── test_face_lockout_service.py       NEW
│   ├── test_face_attendance_view.py       NEW
│   └── fixtures/sample_face.jpg           NEW
└── urls.py                                 MOD  add /attendance/check/
```

### 4.2 Settings additions (`business_web/business_web/settings.py`)

| Name | Default | Purpose |
|---|---|---|
| `FACE_API_URL` | `http://127.0.0.1:7860` | Base URL of FastAPI face service. |
| `FACE_API_TIMEOUT_SEC` | `15` | HTTP client timeout (covers cold-start). |
| `FACE_LOCKOUT_MAX_FAILS` | `3` | Wrong-person verifications before lock. |
| `FACE_LOCKOUT_DURATION_SEC` | `300` | Lock window in seconds. |
| `WORK_START_TIME` | `time(8, 30)` | Used by check-in status decision. |
| `WORK_LATE_GRACE_MIN` | `5` | Minutes of grace before status flips to `late`. |

### 4.3 New dependency

`requirements.txt`: add `requests`. No other deps.

## 5. Components (single-responsibility)

### 5.1 `face_api_client.py`

Pure HTTP. **No Django model or settings-side-effect imports** other than `from django.conf import settings` for URL/timeout. Reads only.

```python
class FaceApiError(Exception):
    """code in {'unreachable','timeout','bad_response','no_face','unknown'}."""
    code: str
    message: str

def health_check() -> bool: ...
def register_face_remote(employee_id: str, image_bytes: bytes,
                         filename: str = "face.jpg",
                         slot_id: int | None = None) -> dict: ...
def recognize_face_remote(image_bytes: bytes,
                          filename: str = "probe.jpg") -> dict: ...
```

Error mapping:

| Source | `FaceApiError.code` |
|---|---|
| `requests.ConnectionError` | `unreachable` |
| `requests.Timeout` | `timeout` |
| HTTP 400 body contains `"No face detected"` | `no_face` |
| Other 4xx/5xx | `bad_response` |
| JSON decode failure | `bad_response` |

`recognize_face_remote` does **not** raise on `status:'fail'`; it returns the JSON for the caller to interpret.

### 5.2 `face_verification_service.py`

```python
@dataclass
class VerifyResult:
    success: bool
    confidence: float | None
    matched_employee_id: str | None
    reason: str  # 'ok' | 'wrong_person' | 'no_match' | 'no_face' | 'service_down'

def verify_face_for_user(user: User, image_bytes: bytes) -> VerifyResult: ...
```

Decision table:

| FastAPI/client outcome | `reason` | `success` |
|---|---|---|
| Client raises `unreachable`/`timeout`/`bad_response`/`unknown` | `service_down` | `False` |
| Client raises `no_face` | `no_face` | `False` |
| Response `status='fail'` | `no_match` | `False` |
| Response `status='success'` and `employee_id != str(user.id)` | `wrong_person` | `False` |
| Response `status='success'` and `employee_id == str(user.id)` | `ok` | `True` |

### 5.3 `attendance_logging_service.py`

```python
def get_or_create_today_record(user: User) -> AttendanceRecord: ...
def decide_next_action(record: AttendanceRecord) -> str:  # 'check_in'|'check_out'|'done'
def record_check_in(user: User) -> AttendanceRecord: ...
def record_check_out(user: User) -> AttendanceRecord: ...  # idempotent guard
```

- `get_or_create_today_record` uses `timezone.localdate()`.
- `record_check_in` writes `check_in_time = timezone.localtime().time()` and sets `status='on_time'` when `now <= WORK_START_TIME + WORK_LATE_GRACE_MIN`, else `'late'`.
- `record_check_out` only writes if `check_out_time is None`.

### 5.4 `face_lockout_service.py`

Backed by `django.core.cache`. No new model.

```python
def is_locked(user: User) -> tuple[bool, int]: ...   # (locked, seconds_remaining)
def register_failure(user: User) -> int: ...         # new fail count
def clear_failures(user: User) -> None: ...
```

Keys: `face_lockout:fails:{user.id}` (int, TTL = `FACE_LOCKOUT_DURATION_SEC`, reset on each failure via `cache.set`), `face_lockout:until:{user.id}` (epoch seconds, set when count reaches `FACE_LOCKOUT_MAX_FAILS`).
Counter incremented with `cache.add` (init) + `cache.incr`.

### 5.5 `face_service.py` (modified)

```python
def save_employee_face(user, image_file) -> EmployeeFace:
    # 1. raw_bytes = image_file.read(); image_file.seek(0)
    # 2. base64_str = image_service.image_to_base64(image_file)
    # 3. face_api_client.register_face_remote(str(user.id), raw_bytes,
    #                                         filename=image_file.name)
    #    -> raises FaceApiError; do NOT save local row in that case
    # 4. EmployeeFace.objects.update_or_create(user=..., defaults={...})
```

Atomic: remote-first. If FastAPI fails, no local row created/updated.

Partial-failure note: if FastAPI succeeded but the local `update_or_create` then crashes, an orphan slot remains in Mongo. Acceptable because the next re-enrollment overwrites the same `(employee_id, slot_id)` upsert. Documented; no compensating delete (FastAPI has no DELETE endpoint).

### 5.6 `face_attendance_view.py`

```python
@login_required
@require_POST
def face_check_view(request): ...
```

Pipeline:
1. `is_locked(request.user)` → 423 with `retry_after` if locked.
2. Extract `image_bytes` from `request.FILES['image']` (preferred) or JSON body `image_base64`.
3. `verify_face_for_user(request.user, image_bytes)`.
4. Failure branches (map `reason` → HTTP per Section 6.4). Only `wrong_person` increments the fail counter (no_match is a benign "not enrolled / unknown face" signal and must not lock out new users).
5. On success: `clear_failures`, fetch today's record, dispatch via `decide_next_action`.
6. Return JSON with action, time, status, confidence.

### 5.7 `image_upload_view.py` (modified)

`upload_image_base64_view` already validates MIME/size. Change is that `save_employee_face` now performs the remote enroll first. On `FaceApiError`, return:

```json
{"success": false, "error": "<message>", "code": "<face_api_error_code>"}
```
with status `502` (remote dependency), or `400` when `code == 'no_face'`.

### 5.8 FastAPI credential hardening (`backend/backend/main.py`, `backend/backend/db_tools.py`)

Replace:

```python
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://kimluanlu95_db_user:...")
```

with:

```python
MONGO_URI = os.environ["MONGO_URI"]  # raises KeyError at import time if unset
```

(or an explicit `if not MONGO_URI: raise RuntimeError("MONGO_URI env var is required")` for a clearer message).

Add `backend/backend/.env.example`:

```
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>/?retryWrites=true&w=majority&appName=<app>
```

Add `.env` to `backend/backend/.gitignore` if not already present. The leaked password from the previous default **must be rotated in MongoDB Atlas** by the repo owner — that action is out-of-band and not gated by this code change. Note this in the README of `backend/backend/`.

## 6. Data flow

### 6.1 Enrollment

```
Browser  webcam capture  → POST /attendance/upload-image/  multipart{image}
Django   upload_image_base64_view
         ├─ validate MIME / size
         ├─ image_service.image_to_base64        (local preview)
         ├─ read raw bytes
         └─ face_service.save_employee_face
                ├─ face_api_client.register_face_remote(
                │       employee_id=str(user.id),
                │       image_bytes=<raw>,
                │       slot_id=None)
                │       FastAPI: DeepFace.represent → Mongo upsert → FAISS add
                ├─ remote success → EmployeeFace.update_or_create(base64)
                └─ remote failure → raise → 502, nothing saved locally
Browser  {success, data:{base64,...}}
```

### 6.2 Daily check

```
Browser  capture frame → POST /attendance/check/  multipart{image}
Django   face_check_view
         ├─ face_lockout_service.is_locked  → 423 if locked
         ├─ extract bytes
         ├─ face_verification_service.verify_face_for_user
         │     └─ face_api_client.recognize_face_remote
         │           FastAPI: DeepFace.represent → FAISS k=1 → JSON
         ├─ VerifyResult
         ├─ FAIL paths (map reason → HTTP, see 6.4)
         │     wrong_person → register_failure
         │     no_match / no_face / service_down → no counter change
         └─ OK path
               ├─ clear_failures
               ├─ get_or_create_today_record
               ├─ decide_next_action
               │     check_in  → record_check_in
               │     check_out → record_check_out
               │     done      → no-op
               └─ 200 JSON {action, time, status, confidence}
```

### 6.3 Cache keys

| Key | Type | TTL | Set by |
|---|---|---|---|
| `face_lockout:fails:<user.id>` | int | `FACE_LOCKOUT_DURATION_SEC` | `register_failure` |
| `face_lockout:until:<user.id>` | epoch sec | until expiry | `register_failure` when count hits max |

### 6.4 HTTP status map

| Outcome | Status | Body |
|---|---|---|
| Locked | 423 | `{locked: true, retry_after: <sec>}` |
| Service down | 503 | `{error: "face_service_unavailable"}` |
| No face / bad image | 400 | `{error: "no_face_detected"}` |
| No match in registry | 401 | `{error: "no_match"}` |
| Wrong person | 403 | `{error: "wrong_person", fails_left: N}` |
| Check-in OK | 200 | `{action: "check_in", time, status, confidence}` |
| Check-out OK | 200 | `{action: "check_out", time, confidence}` |
| Already done today | 200 | `{action: "done"}` |

## 7. Error handling and edge cases

| # | Scenario | Handling |
|---|---|---|
| 1 | FastAPI cold start (weights download) | 15 s client timeout → 503; UI: "Dịch vụ chưa sẵn sàng." |
| 2 | User not enrolled | `/recognize` → `status='fail'` → `no_match` → UI prompts to enroll. |
| 3 | Blank frame / no face | Client raises `no_face` → 400, **not counted as failure**. |
| 4 | Image too large (>5 MB) | View rejects pre-call with 400 `image_too_large`. Frontend downscales to ≤800 px. |
| 5 | Empty FAISS registry | FastAPI `"No employee data found"` → treat as `no_match` (same as #2). |
| 6 | Concurrent double-click | View `select_for_update` (SQLite no-op, Postgres safe); second call sees `check_in_time` set → returns `check_out` or `done`. Idempotent. |
| 7 | Check-out before check-in (forgot scan in) | `decide_next_action` sees `check_in_time is None` → returns `check_in`, regardless of clock time. |
| 8 | Midnight crossing | `timezone.localdate()` re-evaluated each scan → new day = new record = new `check_in`. Documented limitation. |
| 9 | Lockout race | `cache.add` + `cache.incr`; acceptable for class scope. |
| 10 | Enrollment partial (remote ok, local crash) | Orphan Mongo slot; next re-enroll overwrites same `(employee_id, slot_id)`. No compensating delete. |
| 11 | Wrong-person attack | Lockout after `FACE_LOCKOUT_MAX_FAILS` for `FACE_LOCKOUT_DURATION_SEC`. No liveness — out of scope. |
| 12 | `FACE_API_URL` misconfigured | `face.client` logger errors with URL once; admin can probe via `health_check`. |
| 13 | Late status threshold | `now > WORK_START_TIME + WORK_LATE_GRACE_MIN` → `status='late'`, else `'on_time'`. |
| 14 | Session expiry mid-scan | `@login_required` returns 302; frontend fetch wrapper treats redirect as `auth_expired`. |

### 7.1 Security checklist

- FastAPI Mongo credentials are hardcoded — **removed in this phase** (§5.8). Service fails fast without `MONGO_URI`. Atlas password rotation is an out-of-band action by the repo owner.
- FastAPI has no auth; only safe because `127.0.0.1`. Do not expose externally without an auth layer.
- Django view uses `@login_required` + `@require_POST` + CSRF (default middleware).
- Image bytes never logged. `face.verify` logs reason + confidence only.
- Lockout keys namespaced per user; no cross-user leak.
- Daily check has **no file-upload fallback** — webcam-only to prevent stored-photo bypass (§9).
- Replay/liveness: explicitly out of scope.

### 7.2 Logging channels

- `face.client` — HTTP request/response status (no payloads).
- `face.verify` — verify outcome (`reason`, `confidence`, `user.id`).
- `face.attendance` — `record_check_in` / `record_check_out` events.

## 8. Testing

### 8.1 Layout

```
business_web/attendance/tests/
├── test_face_api_client.py            unit, mock `requests`
├── test_face_verification_service.py  unit, mock client
├── test_attendance_logging_service.py unit, real DB
├── test_face_lockout_service.py       unit, real cache (locmem)
├── test_face_attendance_view.py       integration, mock client
└── fixtures/sample_face.jpg
```

### 8.2 Required coverage

**`face_api_client`** (mock `requests`)
- `register_face_remote` success returns dict.
- `register_face_remote` HTTP 400 with `"No face detected"` → `FaceApiError('no_face')`.
- `register_face_remote` `ConnectionError` → `unreachable`.
- `recognize_face_remote` `status='fail'` returns dict (does not raise).
- `recognize_face_remote` `Timeout` → `timeout`.

**`face_verification_service`** (mock client)
- Success → `VerifyResult(success=True, reason='ok')`.
- `employee_id != str(user.id)` → `reason='wrong_person'`.
- Client `unreachable` → `reason='service_down'`.
- Client returns `status='fail'` → `reason='no_match'`.

**`attendance_logging_service`** (DB)
- `decide_next_action`: no record → `check_in`; check_in only → `check_out`; both set → `done`.
- `record_check_in` before grace → `on_time`.
- `record_check_in` after grace → `late`.
- `record_check_out` idempotent.
- Unique per `(user, date)`.

**`face_lockout_service`** (cache, `override_settings` short TTL)
- One failure → not locked, count 1.
- N failures → locked, `is_locked → (True, ≤ duration)`.
- `clear_failures` resets.
- Lock auto-expires after TTL.

**`face_attendance_view`** (integration, mock client)
- Anonymous → 302.
- Locked → 423.
- Service down → 503, no record written.
- Wrong person → 403, counter incremented.
- First scan of day → 200, `check_in_time` set.
- Second scan → 200, `check_out_time` set.
- Third scan → 200, `action='done'`.

## 9. Frontend integration (`attendance/templates/attendance/attendance.html`)

Replace fake-alert buttons with one **"Chấm công"** button that opens a modal:
- Use `navigator.mediaDevices.getUserMedia({video: {width:800, height:600, facingMode:'user'}, audio:false})`.
- Preview ~3 s, then click capture.
- Draw frame to `<canvas>` 800×600, `canvas.toBlob('image/jpeg', 0.85)`.
- `FormData` append `image`, POST `/attendance/check/` with CSRF token.
- Response handling:
  - 200 → toast: "Chấm vào lúc HH:MM" / "Chấm ra lúc HH:MM"; refresh today's row in history table.
  - 401/403 → toast: "Không nhận diện được, còn N lần thử".
  - 423 → toast: "Đã khóa, thử lại sau X giây".
  - 503 → toast: "Dịch vụ chưa sẵn sàng".
  - Always: stop video tracks, close modal.

**No file-input fallback.** Allowing arbitrary image upload defeats the purpose of webcam-based attendance — a user could submit a stored photo of themselves (or anyone) and bypass the live-capture requirement. Instead, when `getUserMedia` is unavailable or denied, the modal shows a blocking permission-required state:

- `NotAllowedError` (permission denied) → message: "Bạn đã từ chối quyền truy cập Camera. Hãy mở quyền Camera trong cài đặt trình duyệt rồi thử lại." with a "Hướng dẫn" link to a help anchor that explains per-browser steps (Chrome / Edge / Firefox). No bypass button.
- `NotFoundError` (no camera hardware) → message: "Không tìm thấy camera. Cần thiết bị có webcam để chấm công." Modal closes; user cannot proceed.
- `NotReadableError` (device busy) → message: "Camera đang được ứng dụng khác sử dụng. Đóng ứng dụng đó rồi thử lại."
- HTTPS-required note: webcam access requires `https://` or `localhost`. If `location.protocol === 'http:'` and host is not `localhost`/`127.0.0.1`, the modal shows: "Trang phải chạy trên HTTPS để dùng camera."

Enrollment view (`upload_image_base64_view`) keeps its current `<input type="file">` since enrollment is a deliberate one-time action under the user's account control, but the **daily check** flow is camera-only.

`attendance_view` is extended to pass real history rows (current month, last 10) for the table, replacing mock data.

## 10. Done definition

- All tests in §8.2 pass under `manage.py test attendance`.
- Manual demo path:
  1. Start FastAPI (`uvicorn main:app --port 7860`).
  2. User enrolls via existing upload page.
  3. User clicks **Chấm công** → row appears with `check_in_time`.
  4. User clicks **Chấm công** again same day → `check_out_time` filled.
  5. Third click same day → toast: "Bạn đã chấm công hôm nay".
  6. Holding another user's photo to webcam → 403; after 3 attempts → 423 lock.

## 11. Out-of-scope follow-ups

- Add auth layer to FastAPI before any non-localhost deploy.
- Liveness / anti-spoof.
- Kiosk (1:N) mode.
- Per-team late thresholds; leave/holiday integration into `AttendanceRecord.status`.
- Background retry for failed enrollment.
- Admin bulk enrollment UI.
- Rotation of the previously-leaked MongoDB Atlas password (manual Atlas console action by repo owner).

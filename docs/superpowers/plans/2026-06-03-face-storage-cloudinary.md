# Face Storage → Cloudinary (lưu tối thiểu) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bỏ lưu base64 ảnh khuôn mặt trong DB — EmployeeFace không lưu ảnh; FaceChangeRequest dùng ImageField (Cloudinary ở prod), serve qua view login-gated; approve→xóa ảnh, reject→giữ làm minh chứng.

**Architecture:** Nhận diện/đăng ký vẫn chạy remote Face API. Ảnh local chỉ phục vụ HR review phiếu pending. Dùng Django `ImageField` + default storage (RawMediaCloudinaryStorage khi `USE_CLOUDINARY`, FileSystemStorage ở dev). Ảnh phục vụ qua endpoint Django kiểm quyền, không phơi URL Cloudinary.

**Tech Stack:** Django 6, Pillow 11.3 (đã cài), cloudinary_storage, Locust (không dùng ở plan này).

**Spec:** `docs/superpowers/specs/2026-06-03-face-storage-cloudinary-design.md`

---

## File Structure

| File | Trách nhiệm | Thao tác |
|---|---|---|
| `attendance/models/employee_face_model.py` | Row enroll (bỏ ảnh) | Modify |
| `attendance/models/face_change_request_model.py` | Phiếu đổi mặt + ảnh ImageField | Modify |
| `attendance/migrations/00XX_*.py` | Schema thay đổi | Create (makemigrations) |
| `attendance/services/face/face_service.py` | Enroll remote + upsert row | Modify |
| `attendance/services/face/face_change_service.py` | submit/approve/reject + purge | Modify |
| `attendance/views/face/image_upload_view.py` | upload + (bỏ get-face) | Modify |
| `attendance/views/face/face_change_review_view.py` | + view stream ảnh | Modify |
| `attendance/views/__init__.py` | export view | Modify |
| `attendance/urls.py` | bỏ get-face, thêm image url | Modify |
| `attendance/templates/attendance/face/face_change_review.html` | src ảnh → view | Modify |
| `attendance/tests/test_face_upload.py` | cập nhật + thêm test | Modify |

---

## Task 1: Model — bỏ ảnh EmployeeFace, FaceChangeRequest dùng ImageField

**Files:**
- Modify: `attendance/models/employee_face_model.py`
- Modify: `attendance/models/face_change_request_model.py`
- Create: migration

- [ ] **Step 1: Sửa EmployeeFace — xóa `face_base64` và `content_type`**

Trong `employee_face_model.py`, xóa 2 field `face_base64` (TextField) và `content_type` (CharField). Giữ `user`, `slot_id`, `created_at`, `updated_at`. Cập nhật docstring/`__str__` nếu tham chiếu ảnh.

- [ ] **Step 2: Sửa FaceChangeRequest — `image_base64`→`image`, xóa `content_type`**

Trong `face_change_request_model.py`, thay:

```python
    image_base64 = models.TextField(
        help_text='Ảnh khuôn mặt chờ duyệt (base64).',
    )
    content_type = models.CharField(max_length=50, default='image/jpeg')
```

bằng:

```python
    image = models.ImageField(
        upload_to='face_changes/%Y/%m/', null=True, blank=True,
        help_text='Ảnh khuôn mặt chờ duyệt (Cloudinary ở prod). '
                  'Approve → xóa; reject → giữ làm minh chứng.',
    )
```

Giữ nguyên `image_sha256`, `ip_address`, `status`, `reviewed_by`, `reviewed_at`, `hr_note`.

- [ ] **Step 3: Tạo migration**

Run: `python manage.py makemigrations attendance`
Expected: 1 migration — remove `employeeface.face_base64`, `employeeface.content_type`, `facechangerequest.image_base64`, `facechangerequest.content_type`; add `facechangerequest.image`.

- [ ] **Step 4: Áp migration (DB dev)**

Run: `python manage.py migrate attendance`
Expected: `Applying attendance.00XX... OK`

- [ ] **Step 5: Commit**

```bash
git add business_web/attendance/models/employee_face_model.py business_web/attendance/models/face_change_request_model.py business_web/attendance/migrations/
git commit -m "refactor(attendance): bỏ base64, FaceChangeRequest dùng ImageField"
```

---

## Task 2: Services — enroll không lưu ảnh; submit/approve/reject + purge

**Files:**
- Modify: `attendance/services/face/face_service.py`
- Modify: `attendance/services/face/face_change_service.py`

- [ ] **Step 1: `face_service.py` — bỏ base64 khỏi enroll, xóa `get_employee_face`**

Thay toàn bộ file bằng:

```python
"""Register employee face on the remote service; keep a minimal local row.

Remote-first: nếu remote /register từ chối ảnh, không ghi row local.
EmployeeFace chỉ giữ slot_id (đánh dấu đã enroll). Ảnh KHÔNG lưu local —
nhận diện chạy remote (FAISS).
"""
from attendance.models import EmployeeFace
from attendance.services.face import face_api_client


def resolve_slot_id(user) -> int:
    """Slot hiện có của user, hoặc 1 nếu chưa enroll."""
    existing = EmployeeFace.objects.filter(user=user).first()
    return existing.slot_id if existing else 1


def apply_face_enrollment(user, raw_bytes, content_type='image/jpeg') -> EmployeeFace:
    """Đẩy ảnh lên service từ xa rồi upsert row local (chỉ slot_id).

    Điểm DUY NHẤT khiến một khuôn mặt trở thành enrollment có hiệu lực.
    Raises FaceApiError nếu remote từ chối.
    """
    slot_id = resolve_slot_id(user)
    face_api_client.register_face_remote(
        employee_id=str(user.id),
        image_bytes=raw_bytes,
        slot_id=slot_id,
    )
    face, _ = EmployeeFace.objects.update_or_create(
        user=user,
        defaults={'slot_id': slot_id},
    )
    return face


def save_employee_face(user, image_file) -> EmployeeFace:
    """Enroll trực tiếp (đường tin cậy — VD HR/Admin). Có hiệu lực ngay."""
    image_file.seek(0)
    raw_bytes = image_file.read()
    image_file.seek(0)
    content_type = getattr(image_file, 'content_type', 'image/jpeg')
    return apply_face_enrollment(user, raw_bytes, content_type)


def delete_employee_face(user) -> bool:
    deleted_count, _ = EmployeeFace.objects.filter(user=user).delete()
    return deleted_count > 0
```

(Đã xóa `image_to_base64` import + `get_employee_face`.)

- [ ] **Step 2: `face_change_service.py` — submit lưu ImageField, approve purge, reject giữ**

Thay phần đầu + `submit_face_change` + `approve_face_change` + `reject_face_change`:

Imports (đầu file): bỏ `import base64`, bỏ `from ...image_service import image_to_base64`; thêm `from django.core.files.base import ContentFile`.

`submit_face_change`:

```python
def submit_face_change(owner, submitted_by, image_file, ip_address=None):
    """Nộp cập nhật khuôn mặt. Trả (outcome, obj)."""
    import hashlib
    image_file.seek(0)
    raw_bytes = image_file.read()
    image_file.seek(0)
    content_type = getattr(image_file, 'content_type', 'image/jpeg')
    sha = hashlib.sha256(raw_bytes).hexdigest()

    has_face = hasattr(owner, 'employee_face')
    # Đường tin cậy (HR/Admin) HOẶC lần đầu → enroll ngay, KHÔNG lưu ảnh.
    if _is_trusted(submitted_by) or not has_face:
        face = face_service.apply_face_enrollment(owner, raw_bytes, content_type)
        note = ('Tự động duyệt (người thực hiện là HR/Admin).'
                if _is_trusted(submitted_by) else 'Tự động duyệt (Lần đầu đăng ký).')
        FaceChangeRequest.objects.create(
            user=owner, submitted_by=submitted_by,
            image_sha256=sha, ip_address=ip_address,
            status=FaceChangeRequest.APPROVED,
            reviewed_by=submitted_by, reviewed_at=timezone.now(),
            hr_note=note,
        )
        return 'applied', face

    # Self-service: chờ HR duyệt — lưu ảnh để HR xem (Cloudinary).
    with transaction.atomic():
        FaceChangeRequest.objects.filter(
            user=owner, status=FaceChangeRequest.PENDING,
        ).delete()
        req = FaceChangeRequest.objects.create(
            user=owner, submitted_by=submitted_by,
            image=ContentFile(raw_bytes, name=f'{owner.id}_{sha[:10]}.jpg'),
            image_sha256=sha, ip_address=ip_address,
            status=FaceChangeRequest.PENDING,
        )
    return 'pending', req
```

`approve_face_change` (đọc ảnh từ storage, register, rồi PURGE):

```python
def approve_face_change(hr_user, req_id, hr_note=''):
    try:
        req = FaceChangeRequest.objects.select_related('user').get(id=req_id)
    except FaceChangeRequest.DoesNotExist:
        return False, 'Không tìm thấy yêu cầu.'
    if req.status != FaceChangeRequest.PENDING:
        return False, 'Yêu cầu đã được xử lý.'
    if not req.image:
        return False, 'Thiếu ảnh để duyệt.'

    raw_bytes = req.image.read()
    try:
        face_service.apply_face_enrollment(req.user, raw_bytes)
    except face_api_client.FaceApiError as exc:
        return False, f'Service nhận diện từ chối ảnh: {exc.message or exc.code}'

    req.status = FaceChangeRequest.APPROVED
    req.reviewed_by = hr_user
    req.reviewed_at = timezone.now()
    req.hr_note = (hr_note or '').strip()
    # Đã enroll remote → ảnh local hết tác dụng → purge (giảm PII/dung lượng).
    req.image.delete(save=False)
    req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_note', 'image'])
    return True, 'Đã duyệt và cập nhật khuôn mặt.'
```

`reject_face_change` (GIỮ ảnh làm minh chứng — chỉ đổi status/metadata):

```python
def reject_face_change(hr_user, req_id, hr_note=''):
    try:
        req = FaceChangeRequest.objects.get(id=req_id)
    except FaceChangeRequest.DoesNotExist:
        return False, 'Không tìm thấy yêu cầu.'
    if req.status != FaceChangeRequest.PENDING:
        return False, 'Yêu cầu đã được xử lý.'
    # GIỮ req.image làm minh chứng chống gian lận.
    req.status = FaceChangeRequest.REJECTED
    req.reviewed_by = hr_user
    req.reviewed_at = timezone.now()
    req.hr_note = (hr_note or '').strip()
    req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_note'])
    return True, 'Đã từ chối yêu cầu cập nhật khuôn mặt.'
```

- [ ] **Step 3: Chạy test hiện có (sẽ có cái fail — xử lý ở Task 5)**

Run: `python manage.py test attendance.tests.test_face_upload`
Expected: một số FAIL (test còn tham chiếu base64/get-face) — sẽ sửa ở Task 5. Xác nhận KHÔNG có ImportError/SyntaxError từ service.

- [ ] **Step 4: Commit**

```bash
git add business_web/attendance/services/face/face_service.py business_web/attendance/services/face/face_change_service.py
git commit -m "refactor(attendance): enroll không lưu ảnh; approve purge, reject giữ minh chứng"
```

---

## Task 3: Views/URLs — bỏ get-face, thêm view stream ảnh login-gated

**Files:**
- Modify: `attendance/views/face/image_upload_view.py`
- Modify: `attendance/views/face/face_change_review_view.py`
- Modify: `attendance/views/__init__.py`
- Modify: `attendance/urls.py`

- [ ] **Step 1: `image_upload_view.py` — bỏ `get_image_base64_view` + data base64 khỏi response**

Sửa imports: bỏ `get_employee_face` (giữ `delete_employee_face` nếu còn dùng — kiểm tra; nếu không, bỏ luôn).
Trong `upload_image_base64_view`, nhánh applied đổi block return có `data` thành:

```python
    return JsonResponse({
        "success": True,
        "pending": False,
        "message": "Lưu ảnh thành công.",
    })
```

Xóa toàn bộ hàm `get_image_base64_view` và decorator của nó.

- [ ] **Step 2: Thêm `face_change_image_view` vào `face_change_review_view.py`**

Thêm vào cuối file:

```python
import mimetypes

from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required

from accounts.services import is_admin_user, is_hr_user
from attendance.models import FaceChangeRequest


@login_required
def face_change_image_view(request, req_id):
    """Stream ảnh phiếu đổi mặt — chỉ chủ mặt hoặc HR/Admin. Không phơi URL Cloudinary."""
    try:
        req = FaceChangeRequest.objects.get(id=req_id)
    except FaceChangeRequest.DoesNotExist:
        raise Http404
    allowed = (
        request.user == req.user
        or is_hr_user(request.user)
        or is_admin_user(request.user)
    )
    if not allowed or not req.image:
        raise Http404
    ctype = mimetypes.guess_type(req.image.name)[0] or 'image/jpeg'
    return FileResponse(req.image.open('rb'), content_type=ctype)
```

(Nếu các import trùng đã có ở đầu file thì gộp, đừng lặp.)

- [ ] **Step 3: `views/__init__.py` — bỏ export get-face, thêm image view**

Bỏ `get_image_base64_view` khỏi import + `__all__`. Thêm `face_change_image_view` vào import từ `face_change_review_view` + `__all__`.

- [ ] **Step 4: `urls.py` — bỏ get-face, thêm image path**

Bỏ dòng `path('attendance/get-face/', get_image_base64_view, ...)` + import `get_image_base64_view`.
Thêm:

```python
    path('attendance/face-changes/<int:req_id>/image/',
         face_change_image_view, name='face_change_image'),
```

và import `face_change_image_view`.

- [ ] **Step 5: Kiểm tra hệ thống**

Run: `python manage.py check`
Expected: `System check identified no issues`.

- [ ] **Step 6: Commit**

```bash
git add business_web/attendance/views/ business_web/attendance/urls.py
git commit -m "feat(attendance): view stream ảnh phiếu đổi mặt (login-gated), bỏ get-face"
```

---

## Task 4: Template — src ảnh trỏ view

**Files:**
- Modify: `attendance/templates/attendance/face/face_change_review.html`

- [ ] **Step 1: Đổi src ảnh**

Thay dòng 58:

```html
<img class="fc-thumb" src="data:{{ req.content_type }};base64,{{ req.image_base64 }}" alt="face">
```

bằng:

```html
<img class="fc-thumb" src="{% url 'face_change_image' req.id %}" alt="face">
```

- [ ] **Step 2: Commit**

```bash
git add business_web/attendance/templates/attendance/face/face_change_review.html
git commit -m "feat(attendance): render ảnh phiếu đổi mặt qua view login-gated"
```

---

## Task 5: Tests — cập nhật + thêm

**Files:**
- Modify: `attendance/tests/test_face_upload.py`

- [ ] **Step 1: Sửa `TestFaceUpload.test_att_face_01_self_update_is_pending`**

EmployeeFace cũ giờ không có base64. Thay phần tạo + assert:

```python
    @patch('attendance.services.face.face_api_client.register_face_remote')
    def test_att_face_01_self_update_is_pending(self, mock_register):
        """NV đã có mặt, tự upload CẬP NHẬT → pending, lưu ảnh chờ HR, CHƯA enroll lại."""
        EmployeeFace.objects.create(user=self.user, slot_id=1)  # đã enroll trước
        self.client.force_login(self.user)
        image = SimpleUploadedFile("test_face.gif", DUMMY_GIF, content_type="image/gif")
        response = self.client.post(self.url, {'image': image})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['pending'])
        mock_register.assert_not_called()
        req = FaceChangeRequest.objects.get(user=self.user)
        self.assertEqual(req.status, FaceChangeRequest.PENDING)
        self.assertTrue(bool(req.image))          # ảnh được lưu để HR xem
        self.assertEqual(req.submitted_by, self.user)
```

- [ ] **Step 2: Sửa `test_att_face_02_first_enrollment_applies`**

Thêm assert không lưu ảnh cho auto-approve:

```python
        req = FaceChangeRequest.objects.get(user=self.user)
        self.assertEqual(req.status, FaceChangeRequest.APPROVED)
        self.assertFalse(bool(req.image))         # auto-approve → không lưu ảnh
```

(Giữ phần còn lại: mock_register.assert_called_once, EmployeeFace tồn tại.)

- [ ] **Step 3: Xóa `test_att_get_01_has_image` và `test_att_get_02_no_image`**

Endpoint get-face đã bị xóa → xóa 2 test này hoàn toàn (chúng tạo `EmployeeFace(face_base64=...)` không còn hợp lệ).

- [ ] **Step 4: Sửa `TestFaceChangeWorkflow.setUp` + approve/reject**

`setUp`: thay `EmployeeFace.objects.create(user=self.emp, face_base64=..., content_type=...)` bằng `EmployeeFace.objects.create(user=self.emp, slot_id=1)`.

`test_hr_approve_pending_enrolls` — thay assert "face đổi" bằng assert ảnh phiếu bị purge:

```python
        resp = self.client.post(reverse('face_change_approve', args=[req.id]), {'hr_note': 'ok'})
        self.assertEqual(resp.status_code, 302)
        mock_register.assert_called_once()
        self.assertTrue(EmployeeFace.objects.filter(user=self.emp).exists())
        req.refresh_from_db()
        self.assertEqual(req.status, FaceChangeRequest.APPROVED)
        self.assertEqual(req.reviewed_by, self.hr)
        self.assertFalse(bool(req.image))         # approve → ảnh bị purge
```

`test_hr_reject_does_not_enroll` — thay assert "face cũ giữ" bằng giữ ảnh minh chứng:

```python
        resp = self.client.post(reverse('face_change_reject', args=[req.id]), {'hr_note': 'no'})
        self.assertEqual(resp.status_code, 302)
        mock_register.assert_not_called()
        req.refresh_from_db()
        self.assertEqual(req.status, FaceChangeRequest.REJECTED)
        self.assertTrue(bool(req.image))          # reject → GIỮ ảnh làm minh chứng
```

- [ ] **Step 5: Thêm test cho `face_change_image_view`**

Thêm class mới vào cuối file:

```python
class TestFaceChangeImageView(TestCase):
    def setUp(self):
        from accounts.models import Role, UserProfile
        self.client = Client()
        self.hr_role = Role.objects.create(name=Role.HR)
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR001')
        self.emp = User.objects.create_user(username='emp', password='123')
        UserProfile.objects.create(user=self.emp, role=self.emp_role, employee_id='E001')
        self.stranger = User.objects.create_user(username='str', password='123')
        UserProfile.objects.create(user=self.stranger, role=self.emp_role, employee_id='S001')
        # emp đã có face → upload là cập nhật → pending có ảnh
        EmployeeFace.objects.create(user=self.emp, slot_id=1)
        self.client.force_login(self.emp)
        img = SimpleUploadedFile("f.gif", DUMMY_GIF, content_type="image/gif")
        self.client.post(reverse('upload_image_base64'), {'image': img})
        self.req = FaceChangeRequest.objects.get(user=self.emp)
        self.url = reverse('face_change_image', args=[self.req.id])

    def test_owner_can_view(self):
        self.client.force_login(self.emp)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_hr_can_view(self):
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_stranger_404(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(self.url).status_code, 404)
```

- [ ] **Step 6: Chạy test attendance**

Run: `python manage.py test attendance.tests.test_face_upload`
Expected: tất cả PASS.

- [ ] **Step 7: Commit**

```bash
git add business_web/attendance/tests/test_face_upload.py
git commit -m "test(attendance): cập nhật test ảnh ImageField + purge/giữ + image view"
```

---

## Task 6: Verify toàn cục + dọn tham chiếu sót

**Files:** (kiểm tra, sửa nếu sót)

- [ ] **Step 1: Grep tham chiếu base64/get-face còn sót**

Run: `grep -rn "face_base64\|image_base64\|get_image_base64\|get_employee_face\|image_to_base64" business_web --include="*.py" --include="*.html" | grep -v migrations | grep -v __pycache__`
Expected: KHÔNG còn match ngoài migration cũ. Nếu còn (vd `image_service.image_to_base64` không ai dùng) → có thể để hoặc xóa file `image_service.py` nếu rỗng consumer.

- [ ] **Step 2: Chạy full suite**

Run: `python manage.py test`
Expected: tất cả PASS (≈ số test trước − 2 test get-face đã xóa + 3 test image view).

- [ ] **Step 3: Smoke thủ công (tùy chọn)**

`python manage.py runserver` → đăng nhập → Cài đặt → chụp & lưu mặt (lần 2 = pending) → đăng nhập HR → trang duyệt đổi mặt → ảnh hiển thị qua `/attendance/face-changes/<id>/image/` → approve → ảnh biến mất; thử 1 phiếu reject → ảnh còn.

- [ ] **Step 4: Commit (nếu có dọn dẹp)**

```bash
git add -A business_web/attendance/
git commit -m "chore(attendance): dọn tham chiếu base64 còn sót"
```

---

## Ghi chú triển khai
- **Prod:** cần `USE_CLOUDINARY=True` để ảnh `face_changes/` lên Cloudinary; dev dùng disk `media/`. Không đổi code.
- **PII:** ảnh reject giữ lâu dài — chính sách dọn định kỳ là việc tương lai (ngoài plan).
- **Migration:** nhớ `migrate` khi deploy.

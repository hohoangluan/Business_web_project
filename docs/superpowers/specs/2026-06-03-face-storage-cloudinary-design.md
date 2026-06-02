# Spec: Bỏ base64 ảnh khuôn mặt → Cloudinary (lưu tối thiểu)

> Ngày: 2026-06-03 · Trạng thái: Approved · Phạm vi: app `attendance`

## 1. Bối cảnh & Vấn đề

Hiện ảnh khuôn mặt lưu dạng **base64 TextField** trong DB:
- `EmployeeFace.face_base64` (+`content_type`) — ảnh enrolled.
- `FaceChangeRequest.image_base64` (+`content_type`) — ảnh chờ HR duyệt.

Nhận diện + đăng ký chạy trên **Remote Face API** (FAISS embeddings). Ảnh local chỉ phục vụ hiển thị.

**Phát hiện khi kiểm chứng code:**
- `EmployeeFace.face_base64` **không UI nào hiển thị**; endpoint `get_image_base64_view` (`get-face`) **không nơi nào gọi → code chết**. Upload response trả `base64` nhưng `settings.html` chỉ đọc `success`/`code`, bỏ qua. ⇒ Ảnh enrolled là **dead weight**.
- `FaceChangeRequest.image_base64` **có dùng thật**: `face_change_review.html` hiển thị cho HR duyệt; `approve_face_change` decode gửi lại remote `/register`.

base64 trong DB: phình +33%, bloat row/backup, không CDN. Liên quan F7 (ghi DB lớn giữ write-lock lâu hơn).

## 2. Mục tiêu

- DB không còn blob base64.
- **Bỏ hẳn** lưu ảnh ở `EmployeeFace` (giữ row để đánh dấu đã enroll).
- `FaceChangeRequest` ảnh → `ImageField` (Cloudinary ở prod, disk ở dev tự động qua `USE_CLOUDINARY`).
- Ảnh phục vụ qua **view login-gated** (không phơi URL public — PII sinh trắc).
- **Retention theo nghiệp vụ:** approve → xóa ảnh (đã enroll remote); reject → **giữ ảnh làm minh chứng** chống gian lận.

Non-goals: không đổi cơ chế nhận diện/đăng ký remote; không đổi `settings.html`; không làm signed-URL Cloudinary (dùng view stream là đủ).

## 3. Thiết kế

### 3.1 Models (`attendance/models/`)
- `EmployeeFace`: **xóa** `face_base64`, `content_type`. Giữ `user (OneToOne), slot_id, created_at, updated_at`.
- `FaceChangeRequest`: thay `image_base64 (TextField)` → `image = ImageField(upload_to='face_changes/%Y/%m/')`. **Xóa** `content_type`.
- Migrations: 1 cho mỗi model (remove/add field). **Không** mang dữ liệu base64 cũ (theo quyết định: bỏ cột, user re-enroll).

### 3.2 Services (`attendance/services/face/`)
- `face_service.apply_face_enrollment(user, raw_bytes, content_type)`: bỏ tham số `base64_str`; chỉ gọi remote `register` + upsert `EmployeeFace(slot_id)`. **Không lưu ảnh.**
- `face_service.get_employee_face`: **xóa** (không còn consumer).
- `face_change_service.submit_face_change(owner, submitted_by, image_file, ip_address)`:
  - Nhánh tin cậy (HR/Admin) **hoặc** lần đầu (`not has_face`): remote register (raw_bytes) → upsert EmployeeFace → tạo `FaceChangeRequest(status=approved)` **không lưu image** (đã enroll, không cần minh chứng).
  - Nhánh self-update (đã có face): tạo `FaceChangeRequest(status=pending, image=ContentFile(raw_bytes))`.
- `face_change_service.approve_face_change(hr, req_id, note)`: `raw = req.image.read()` → remote register → upsert EmployeeFace → status approved → **`req.image.delete(save=False)`** (purge) → save.
- `face_change_service.reject_face_change(hr, req_id, note)`: status rejected → **giữ `req.image`** (minh chứng).
- Bỏ import/dùng `image_to_base64` ở 2 service trên (giữ util nếu nơi khác cần — kiểm tra; hiện chỉ 2 chỗ này).

### 3.3 Views/URLs (`attendance/views/face/`, `attendance/urls.py`)
- `upload_image_base64_view`: bỏ `base64`/`data` khỏi JSON response (giữ `success`, `pending`, `message`, `error`, `code`).
- **Xóa** `get_image_base64_view` + url `attendance/get-face/` + export trong `views/__init__.py`.
- **Thêm** `face_change_image_view(request, req_id)`:
  - `@login_required`.
  - Quyền: `request.user == req.user` (chủ mặt) **hoặc** HR/Admin (`is_hr_user`/`is_admin_user`). Khác → 404 (không lộ tồn tại).
  - Không có `req.image` → 404.
  - Trả `FileResponse(req.image.open('rb'), content_type=...)` (stream từ storage, hoạt động cả Cloudinary lẫn disk).
  - URL: `path('attendance/face-changes/<int:req_id>/image/', face_change_image_view, name='face_change_image')`.

### 3.4 Templates
- `attendance/templates/attendance/face/face_change_review.html`: `src="data:{{req.content_type}};base64,{{req.image_base64}}"` → `src="{% url 'face_change_image' req.id %}"`.
- `settings.html`: không đổi.

### 3.5 Storage / Cloudinary
- `ImageField` dùng default storage: `RawMediaCloudinaryStorage` khi `USE_CLOUDINARY=True` (prod), `FileSystemStorage` (dev) — tự động, không code riêng.
- View `face_change_image` stream bytes → không phơi public URL.
- Purge approved: `image.delete()` xóa asset Cloudinary.
- Cần `Pillow` cho `ImageField` (kiểm tra đã có; nếu chưa → thêm requirements).

## 4. Luồng dữ liệu (sau thay đổi)

```
Upload (self-update): raw_bytes → FaceChangeRequest(pending, image=Cloudinary)
HR xem: face_change_review → <img src=face_change_image view> → stream từ Cloudinary (login-gated)
Approve: read image → remote register → EmployeeFace upsert → image.delete() (purge)
Reject: status=rejected → image GIỮ (minh chứng)
Lần đầu/HR upload: remote register → EmployeeFace → FaceChangeRequest(approved, KHÔNG image)
Nhận diện (/check/): KHÔNG đụng ảnh local (remote)
```

## 5. Error handling
- `approve`: `req.image` rỗng/đọc lỗi → trả `(False, 'Thiếu ảnh để duyệt')`, không đổi status.
- Remote register lỗi lúc approve → giữ pending, báo lỗi (như hiện tại).
- `face_change_image_view`: thiếu quyền/thiếu ảnh → 404.

## 6. Testing
- **Sửa** `attendance/tests/test_face_upload.py`:
  - ATT-FACE-01 (self_update_pending): tạo EmployeeFace cũ (không cần base64) + upload → assert `FaceChangeRequest.pending` có `image`.
  - approve test: assert remote called + EmployeeFace tồn tại + `req.image` **đã bị xóa** (purge) sau approve.
  - reject test: assert `req.image` **còn** (minh chứng) + status rejected.
  - **Xóa** `test_att_get_01_has_image`, `test_att_get_02_no_image` (endpoint biến mất).
- **Thêm** `face_change_image_view`: chủ mặt + HR xem được (200); người lạ → 404; không ảnh → 404.
- Chạy full suite, đảm bảo không vỡ test khác (đặc biệt test tham chiếu `face_base64`/`image_base64`).

## 7. Data migration
- Dev: không mang data cũ. Migration drop `face_base64`/`content_type` (EmployeeFace) + thay `image_base64`→`image`, drop `content_type` (FaceChangeRequest).
- Pending base64 cũ (nếu có) mất ảnh — chấp nhận (user re-submit).

## 8. Rủi ro
- Quên 1 consumer base64 → vỡ render. Mitigation: grep toàn bộ `base64`/`get_image_base64`/`content_type` sau khi sửa.
- Pillow chưa cài → ImageField lỗi. Mitigation: kiểm tra requirements.
- PII: ảnh reject giữ lâu dài → ghi nhận retention policy (out-of-scope, future).

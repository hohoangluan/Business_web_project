# 🔬 HRMS — Dữ Liệu Chảy Qua Code Như Thế Nào (Flow Chi Tiết)

> File này dành cho người mới, đi **sâu hơn** [how_it_works.md](how_it_works.md).
> Trong khi `how_it_works.md` giải thích *khái niệm* (Django là gì, ORM là gì), file này bám **đúng từng bước**:
>
> - Người dùng nhập gì ở **frontend**, dữ liệu được **đóng gói** ra sao?
> - Trình duyệt **gửi** đi như thế nào (form thường? multipart? JSON?)?
> - **Backend nhận** ở đâu, qua những **hàm cụ thể nào**, **theo thứ tự** ra sao?
> - Mỗi bước **chạm database** bằng câu lệnh ORM nào?
> - **Trả** gì về cho người dùng?
>
> Mọi tên hàm, field, đường dẫn đều lấy **trực tiếp từ code** (`business_web/`, đối chiếu 03/06/2026). Không suy diễn.

---

## Mục lục

0. [Trước tiên: 3 cách dữ liệu đi từ trình duyệt tới server](#0-trước-tiên-3-cách-dữ-liệu-đi-từ-trình-duyệt-tới-server)
1. [Giải phẫu một request: các "trạm" cố định mọi flow đều qua](#1-giải-phẫu-một-request-các-trạm-cố-định-mọi-flow-đều-qua)
2. [FLOW A — Form đồng bộ (Nghỉ phép): nhập → gửi → lưu → reload](#2-flow-a--form-đồng-bộ-nghỉ-phép)
3. [FLOW B — Hành động qua URL (Duyệt/Từ chối/Hủy đơn)](#3-flow-b--hành-động-qua-url-duyệttừ-chốihủy-đơn)
4. [FLOW C — AJAX trả JSON (Chấm công khuôn mặt)](#4-flow-c--ajax-trả-json-chấm-công-khuôn-mặt)
5. [FLOW D — Upload + workflow rẽ nhánh (Đăng ký/Đổi khuôn mặt)](#5-flow-d--upload--workflow-rẽ-nhánh-đăng-kýđổi-khuôn-mặt)
6. [Dữ liệu chạm Database: tổng kết các pattern ORM theo flow](#6-dữ-liệu-chạm-database-tổng-kết-các-pattern-orm-theo-flow)
7. [Validation: dữ liệu bẩn bị chặn ở đâu](#7-validation-dữ-liệu-bẩn-bị-chặn-ở-đâu)
8. [Bảng đối chiếu: field frontend → cột database](#8-bảng-đối-chiếu-field-frontend--cột-database)

---

## 0. Trước tiên: 3 cách dữ liệu đi từ trình duyệt tới server

Project dùng **3 kiểu** truyền dữ liệu. Phân biệt được 3 cái này là hiểu 90% mọi flow.

| Kiểu | Khi nào dùng | Trình duyệt gửi gì | Backend đọc ở đâu |
|------|--------------|--------------------|-------------------|
| **① Form thường** (`application/x-www-form-urlencoded`) | Form không có file (đăng nhập, từ chối kèm lý do) | Cặp `key=value` | `request.POST['key']` |
| **② Form có file** (`multipart/form-data`) | Form kèm upload (nghỉ phép + minh chứng, hồ sơ + ảnh) | `key=value` + bytes file | `request.POST` (text) + `request.FILES` (file) |
| **③ AJAX JSON / FormData qua `fetch`** | Không reload trang (chấm công, đổi mặt) | `FormData` hoặc JSON, gửi ngầm bằng JavaScript | `request.FILES` / `request.POST`, view trả `JsonResponse` |

Điểm chung **bắt buộc**: mọi request **POST** đều phải mang **CSRF token**, nếu không `CsrfViewMiddleware` chặn (403).
- Form HTML: chèn bằng `{% csrf_token %}` (Django render thành `<input type=hidden name=csrfmiddlewaretoken>`).
- AJAX: đọc token đó rồi gắn vào header `X-CSRFToken` (xem FLOW C).

---

## 1. Giải phẫu một request: các "trạm" cố định mọi flow đều qua

Dù là flow nào, request luôn đi qua đúng chuỗi trạm này (định nghĩa thứ tự trong `settings.py → MIDDLEWARE`):

```
Trình duyệt
   │  HTTP request (method + URL + headers + body)
   ▼
[gunicorn] ──► [Middleware chain] ──► [URL resolver] ──► [Decorators] ──► [VIEW]
                    │                      │                  │             │
   Session/Auth ◄───┘            urls.py khớp path    @login_required   request.POST
   CSRF check                    → chọn view          @require_POST     request.FILES
                                                       @deny_admin       → gọi FORM/SERVICE
                                                                              │
                                                                         [ORM ↔ Database]
                                                                              │
                                                       ◄── render() HTML  hoặc  JsonResponse()
```

**Decorator** (dòng `@...` ngay trên hàm view) là "trạm gác riêng" của view, chạy **trước** thân hàm:

| Decorator | Tác dụng | Nếu fail |
|-----------|----------|----------|
| `@login_required` | Bắt buộc đã đăng nhập | Redirect `/login/` |
| `@require_POST` | Chỉ cho method POST | Trả 405 |
| `@deny_admin` | Cấm tài khoản Admin vào chức năng nghiệp vụ | Redirect `dashboard` + message |
| `@user_passes_test(is_admin_user)` | Chỉ cho Admin | 302/403 |

Bên trong view, dữ liệu được lấy từ object `request`:
- `request.method` → `'GET'` hay `'POST'`
- `request.POST.get('ten_field')` → giá trị text từ form
- `request.FILES.get('image')` → file upload
- `request.user` → người đang đăng nhập (do `AuthenticationMiddleware` gắn)
- tham số trong URL (vd `<int:pk>`) → truyền thẳng làm **đối số hàm view**: `def leave_approve_action(request, pk)`

---

## 2. FLOW A — Form đồng bộ (Nghỉ phép)

Đây là **flow mẫu** cho mọi chức năng "điền form → lưu". Hiểu kỹ cái này thì OT, báo cáo, đánh giá, hồ sơ... đều y hệt.

**Các file:** form [leaves/forms.py](business_web/leaves/forms.py) · view [leaves/views/__init__.py](business_web/leaves/views/__init__.py) (`leave_view`) · service [leaves/services/__init__.py](business_web/leaves/services/__init__.py) · model `LeaveRequest`.

### Bước 1 — Frontend: người dùng thấy form gì

URL `/leave/` (GET). View render `leaves/leave.html` với biến `form` (một `LeaveRequestForm`).
Form này là **ModelForm** — Django tự sinh các ô input từ model. Các field (khai trong `Meta.fields`):

```python
fields = ['leave_type', 'start_date', 'end_date', 'reason', 'attachment']
```

Mỗi field render thành 1 `<input>`/`<select>` với **thuộc tính `name`** đúng bằng tên field. Tức HTML sinh ra có:
`<select name="leave_type">`, `<input name="start_date" type="date">`, ..., `<input name="attachment" type="file">`.
Vì có field file → thẻ form **phải** là `<form method="post" enctype="multipart/form-data">`.

### Bước 2 — Người dùng bấm "Gửi": trình duyệt đóng gói & gửi

Trình duyệt gom toàn bộ input theo `name`, đóng thành **multipart/form-data** (vì có file), gửi:

```
POST /leave/   Content-Type: multipart/form-data
  leave_type = "annual"
  start_date = "2026-06-10"
  end_date   = "2026-06-12"
  reason     = "Về quê"
  attachment = <bytes file đơn.pdf>
  csrfmiddlewaretoken = "abc..."     ← do {% csrf_token %} tự chèn
```

### Bước 3 — Backend nhận: cùng một view, rẽ theo method

```python
@login_required
@deny_admin
def leave_view(request):
    ensure_profile(request.user)                       # đảm bảo user có UserProfile

    if request.method == 'POST':                        # ← nhánh GỬI
        form = LeaveRequestForm(request.POST, request.FILES)   # ❶ nạp dữ liệu vào form
        if form.is_valid():                              # ❷ chạy toàn bộ validation
            obj = create_leave_request(request.user, form)     # ❸ gọi service lưu DB
            ...
            return redirect('leave')                     # ❹ PRG: chuyển hướng GET lại
        else:
            messages.error(request, 'Vui lòng kiểm tra lại...')
    else:                                                # ← nhánh XEM (GET)
        form = LeaveRequestForm()

    stats = get_user_leave_stats(request.user)           # số liệu quỹ phép (truy vấn DB)
    requests_list = get_user_leave_requests(request.user)# danh sách đơn của user
    return render(request, 'leaves/leave.html', {...})
```

Giải thích từng mốc:

- **❶ `LeaveRequestForm(request.POST, request.FILES)`** — Django "đổ" `request.POST` (text) và `request.FILES` (file)
  vào form, **ghép theo tên field**. `start_date="2026-06-10"` (chuỗi) sẽ được Django ép kiểu sang `date` Python.
- **❷ `form.is_valid()`** — chạy lần lượt: ép kiểu từng field → các hàm `clean_<field>()` → hàm `clean()` tổng.
  Của form nghỉ phép (xem `forms.py`):
  - `clean_attachment()` → gọi `validate_upload(...)` (chung): bỏ qua nếu rỗng; nếu có thì ≤5MB và là PDF/JPG/PNG.
  - `clean_start_date()` → chặn ngày bắt đầu cách quá 7 ngày trong quá khứ.
  - `clean()` → bắt `end_date >= start_date`.
  - Nếu **bất kỳ** cái nào `raise ValidationError` → `is_valid()` trả `False`, lỗi gắn vào `form.errors` để template hiện.
- **❸ `create_leave_request(user, form)`** — *service* mới là nơi ghi DB:
  ```python
  def create_leave_request(user, form):
      obj = form.save(commit=False)        # tạo object LeaveRequest từ form, CHƯA lưu
      obj.user = user                      # gắn chủ đơn (form không có field này)
      obj.status = LeaveRequest.PENDING    # trạng thái khởi đầu
      obj.days = Decimal(str((obj.end_date - obj.start_date).days + 1))   # tự tính số ngày
      obj.save()                           # ← lúc này mới INSERT vào bảng leave_request
      return obj
  ```
  `commit=False` cho phép gắn thêm `user`/`status`/`days` (những thứ **không** đến từ form) **trước khi** chạm DB.
- **❹ `redirect('leave')`** — **PRG (Post-Redirect-Get)**: sau khi lưu, server không trả HTML ngay mà bảo trình duyệt
  **GET lại** `/leave/`. Nhờ vậy bấm F5 không gửi lại đơn lần nữa. Thông báo thành công đi kèm qua **messages framework**
  (`messages.success(...)`) — lưu tạm trong session, hiện ở lần load sau rồi tự biến mất.

### Bước 4 — Trả về

Trình duyệt nhận redirect → tự GET `/leave/` → view chạy nhánh GET → render lại bảng đơn (giờ có đơn mới ở trạng thái
"Chờ duyệt") + toast "Đã gửi đơn thành công". **DB đã có 1 dòng mới** trong `leave_request`.

```
[Form HTML] ──POST multipart──► leave_view(POST)
                                   │ LeaveRequestForm(POST, FILES)
                                   │ form.is_valid() → clean_*()/clean()
                                   │ create_leave_request() → form.save(commit=False)
                                   │                          → obj.save()  ─► INSERT DB
                                   └ redirect('leave') ──► leave_view(GET) ──► render bảng
```

> **Mọi form nghiệp vụ khác đi đúng khuôn này.** Khác biệt chỉ ở: tên form, danh sách `fields`, và service được gọi.
> Ví dụ adjustment ([attendance_adjustment_form.py](business_web/attendance/forms/adjustment/attendance_adjustment_form.py))
> dùng `validate_upload(required=True, allowed_mime=EVIDENCE_MIME)` (minh chứng **bắt buộc**) và `clean()` ép
> "phải khai ít nhất giờ vào hoặc giờ ra".

---

## 3. FLOW B — Hành động qua URL (Duyệt/Từ chối/Hủy đơn)

Không phải lúc nào cũng có form lớn. Nhiều thao tác chỉ là 1 nút "Duyệt" cho **một đơn cụ thể**.
Cách định danh "đơn nào" = nhúng **id vào URL**.

Khai báo trong [leaves/urls.py](business_web/leaves/urls.py):
```python
path('leave/approve/<int:pk>/', leave_approve_action, name='leave_approve'),
path('leave/reject/<int:pk>/',  leave_reject_action,  name='leave_reject'),
```
`<int:pk>` = "ô trống" hứng một số nguyên. Trong template, nút Duyệt là 1 form nhỏ:
```html
<form method="post" action="{% url 'leave_approve' pk=don.id %}">
    {% csrf_token %}
    <button>Duyệt</button>
</form>
```

### Luồng duyệt một đơn

```python
@login_required
@require_POST                                   # chỉ POST (chống duyệt bằng cách dán link GET)
def leave_approve_action(request, pk):          # pk lấy thẳng từ URL
    ensure_profile(request.user)
    if not can_manage_requests(request.user):   # chốt quyền lần nữa ở server
        messages.error(request, 'Bạn không có quyền...')
        return redirect('leave')
    success, msg = approve_leave_request(request.user, pk)   # ← service quyết định L1/L2
    messages.success(request, msg) if success else messages.error(request, msg)
    return redirect('leave_approval')           # PRG
```

`approve_leave_request(approver, pk)` (service) là "bộ não" — **một hàm xử lý cả 2 cấp** tùy trạng thái đơn:

```
nạp đơn theo pk (select_related user/profile/role)
   │
   ├─ approver == chủ đơn?            → chặn "không tự duyệt"
   │
   ├─ đơn đang PENDING (cấp 1):
   │     approver có là leader_user/manager_user của NV?  ─ không ─► chặn
   │     ├─ NV là HR?  → status=APPROVED luôn (bỏ qua cấp 2) + create_notification
   │     └─ else       → status=LEADER_APPROVED (chờ HR)
   │
   └─ đơn đang LEADER_APPROVED (cấp 2):
         approver có role HR?  ─ không ─► chặn
         status=APPROVED + approved_by + create_notification
```

Mỗi nhánh kết bằng `obj.save(update_fields=[...])` — **chỉ UPDATE đúng các cột đổi** (nhanh, an toàn).
Khi duyệt xong cấp cuối, `create_notification(obj.user, 'Đơn nghỉ phép đã được duyệt', ...)` ghi 1 dòng vào bảng
`notification` → chuông của nhân viên sáng lên (xem cơ chế chuông ở `how_it_works.md` §8.5).

**Từ chối** (`leave_reject_action`) tương tự nhưng lấy thêm lý do từ form thường (không có file):
```python
reason = request.POST.get('rejected_reason', '')   # đọc field text
reject_leave_request(request.user, pk, reason)
```

> Pattern "service trả `(success, message)`" lặp khắp project: view chỉ việc bật message + redirect, **không** chứa logic.

---

## 4. FLOW C — AJAX trả JSON (Chấm công khuôn mặt)

Đây là flow **không reload trang**: JavaScript tự gửi ảnh, tự đọc kết quả. Frontend và backend "nói chuyện" bằng **JSON + mã HTTP**.

**Các file:** template [attendance/.../attendance.html](business_web/attendance/templates/attendance/record/attendance.html) · view [face_attendance_view.py](business_web/attendance/views/face/face_attendance_view.py) · services `face/*` + `record/*`.

### Bước 1 — Frontend: webcam → ảnh → FormData → fetch

```javascript
const ctx = canvas.getContext('2d');
ctx.drawImage(video, 0, 0, canvas.width, canvas.height);   // chụp 1 khung từ webcam
canvas.toBlob(async (blob) => {
    const form = new FormData();
    form.append('image', blob, 'check.jpg');               // ❶ đóng gói ảnh vào field "image"
    const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const resp = await fetch('{% url "face_check" %}', {   // ❷ POST ngầm
        method: 'POST',
        headers: { 'X-CSRFToken': csrf },                  // ❸ token CSRF qua HEADER
        body: form,
    });
    const body = await resp.json();                        // ❹ đọc JSON server trả
    if (resp.status === 200)      showToast('Chấm công lúc ' + body.time);
    else if (resp.status === 403) showToast('Mặt không khớp. Còn ' + body.fails_left + ' lần');
    else if (resp.status === 423) showToast('Đã khóa. Thử lại sau ' + body.retry_after + 's');
}, 'image/jpeg', 0.80);
```

Khác FLOW A: không có `<form submit>`, không reload. Dữ liệu vẫn là **multipart** (FormData) nên backend đọc bằng
`request.FILES['image']` y như form thường — nhưng **trả về JSON**, không phải HTML.

### Bước 2 — Backend nhận, xử lý theo thứ tự cứng

`face_check_view(request)` chạy đúng 6 bước (đã trình bày chi tiết ở `how_it_works.md` §8.3, đây là bản rút gọn theo *thứ tự hàm*):

```
1. request_time = timezone.localtime()              # chốt giờ NGAY (tránh độ trễ API làm lệch)
2. is_locked(user)                  ──cache──►       # đang khóa? → JSON 423
3. _extract_image_bytes(request)    ──request.FILES─►# lấy bytes, chặn >2MB → JSON 400
4. verify_face_for_user(user, bytes)
       └► face_api_client.recognize_face_remote(bytes)
              └► requests.post(FACE_API_BASE_URL + '/recognize', files=...)  ──HTTP──► server AI
       ◄ {status, employee_id, confidence}
       so khớp 1:1: employee_id == str(user.id)?
          - khác   → reason 'wrong_person' → register_failure(user) [cache] → JSON 403
          - không khớp ai → 'no_match'     → JSON 401
          - không thấy mặt → 'no_face'     → JSON 400
          - lỗi/timeout → 'service_down'   → JSON 503
5. (đúng người) with transaction.atomic():
       record = AttendanceRecord.objects.select_for_update().get_or_create(user, today)[0]   # KHÓA dòng
       action = decide_next_action(record)          # check_in / check_out / done
       record_check_in() | record_check_out()        # ─► UPDATE giờ + status
6. clear_failures(user) [cache]; record.refresh_from_db(); return JsonResponse(payload, 200)
```

Mấu chốt: **mã HTTP là giao diện**. View không nói "thành công/thất bại" bằng chữ — nó nói bằng **status code**
(200/400/401/403/423/503), JS map mỗi mã thành một toast. Mỗi mã = một tình huống nghiệp vụ rõ ràng.

Việc phân loại `on_time`/`late`/`early_leave` xảy ra trong `record_check_in`/`record_check_out` → `classify_status`,
dựa trên **giờ ca từ hợp đồng** (`get_shift_times`, fallback 08:30–17:30) và **OT đã duyệt** (`effective_shift_end`).

---

## 5. FLOW D — Upload + workflow rẽ nhánh (Đăng ký/Đổi khuôn mặt)

Flow này cho thấy: **cùng một request upload, backend rẽ 2 hướng khác nhau tùy người gửi & trạng thái** — để chống gian lận "đổi mặt chấm hộ".

**Các file:** view [image_upload_view.py](business_web/attendance/views/face/image_upload_view.py) · service [face_change_service.py](business_web/attendance/services/face/face_change_service.py).

### Bước 1 — Frontend gửi (giống FLOW C): FormData field `image` → `POST /attendance/upload-image/`

### Bước 2 — View nhận, kiểm sơ bộ, gọi service

```python
@login_required
@require_POST
def upload_image_base64_view(request):
    image_file = request.FILES.get("image")
    if not image_file:                                  # thiếu file → JSON 400
        return JsonResponse({"success": False, "error": "..."} , status=400)
    if image_file.content_type not in allowed_types:    # không phải ảnh → JSON 400
        return JsonResponse({...}, status=400)
    try:
        outcome, obj = submit_face_change(              # ← service quyết định rẽ nhánh
            owner=request.user, submitted_by=request.user,
            image_file=image_file, ip_address=_client_ip(request),
        )
    except FaceApiError as exc:                          # server AI từ chối ảnh
        return JsonResponse({...}, status=400 if exc.code=='no_face' else 502)
    if outcome == 'pending':
        return JsonResponse({"success": True, "pending": True,  "message": "Chờ HR duyệt..."})
    return JsonResponse({"success": True, "pending": False, "message": "Lưu ảnh thành công."})
```
`_client_ip(request)` đọc header `X-Forwarded-For`/`REMOTE_ADDR` để ghi lại IP người upload (phục vụ audit).

### Bước 3 — Service `submit_face_change`: điểm rẽ nhánh

```python
def submit_face_change(owner, submitted_by, image_file, ip_address=None):
    raw_bytes = image_file.read()
    sha = hashlib.sha256(raw_bytes).hexdigest()         # vân tay ảnh (audit/chống đảo ảnh)
    has_face = hasattr(owner, 'employee_face')          # đã có khuôn mặt chưa?

    # ─ ĐƯỜNG TIN CẬY: người gửi là HR/Admin, HOẶC đây là lần đầu (chưa có mặt) ─
    if _is_trusted(submitted_by) or not has_face:
        face = face_service.apply_face_enrollment(owner, raw_bytes)   # ─HTTP─► /register, áp dụng NGAY
        FaceChangeRequest.objects.create(status=APPROVED, reviewed_by=submitted_by, ...)  # ghi audit
        return 'applied', face

    # ─ SELF-SERVICE: nhân viên tự đổi mặt khi ĐÃ có → KHÔNG áp dụng, chờ HR ─
    with transaction.atomic():
        FaceChangeRequest.objects.filter(user=owner, status=PENDING).delete()   # bỏ pending cũ
        req = FaceChangeRequest.objects.create(
            image=ContentFile(raw_bytes, name=...),     # LƯU ảnh (Cloudinary) để HR xem
            image_sha256=sha, ip_address=ip_address, status=PENDING,
        )
    return 'pending', req
```

So sánh hai hướng:

| | Đường tin cậy (HR/Admin **hoặc** lần đầu) | Self-service (đã có mặt, NV tự đổi) |
|--|--|--|
| Gọi server AI `/register` ngay? | ✅ Có (`apply_face_enrollment`) | ❌ Không |
| Lưu ảnh? | Không (chỉ lưu `sha256` làm dấu vết) | Có (lưu để HR duyệt) |
| Trạng thái request | `APPROVED` | `PENDING` |
| Khuôn mặt nhận diện đổi ngay? | ✅ | ❌ — chờ HR |
| outcome trả về | `'applied'` | `'pending'` |

### Bước 4 — HR duyệt sau (đóng vòng)

HR vào trang duyệt, bấm "Duyệt" cho `req_id` → `approve_face_change(hr_user, req_id)`:
```python
raw_bytes = req.image.read()
face_service.apply_face_enrollment(req.user, raw_bytes)   # ─HTTP─► /register (giờ mới áp dụng)
req.status = APPROVED; req.reviewed_by = hr_user; req.reviewed_at = now()
req.image.delete(save=False)                              # xóa ảnh sau khi enroll (giảm PII)
req.save(update_fields=[...])
```
Nếu từ chối: `reject_face_change` đặt `REJECTED` + `hr_note`, **giữ lại ảnh** làm bằng chứng. Cả hai trả `(success, message)`.

```
NV tự đổi ──upload──► view ──► submit_face_change ──PENDING──► (chờ)
                                                                  │
HR bấm Duyệt ──► approve_face_change ──HTTP /register──► EmployeeFace cập nhật ──► APPROVED
```

---

## 6. Dữ liệu chạm Database: tổng kết các pattern ORM theo flow

Gom lại **đúng** các câu ORM xuất hiện trong các flow trên, kèm SQL tương đương để bạn hình dung:

| Mục đích | ORM (trong code) | SQL tương đương |
|----------|------------------|------------------|
| Lưu đơn mới | `obj.save()` (sau `form.save(commit=False)`) | `INSERT INTO leave_request (...)` |
| Cập nhật vài cột | `obj.save(update_fields=['status','approved_by'])` | `UPDATE ... SET status=?, approved_by=?` |
| Lấy 1 dòng theo khóa | `LeaveRequest.objects.get(pk=request_id)` | `SELECT ... WHERE id=? ` |
| Tìm-hoặc-tạo (chấm công) | `AttendanceRecord.objects.get_or_create(user, record_date=today)` | `SELECT ...; nếu trống → INSERT` |
| Khóa dòng chống tranh chấp | `.select_for_update().get_or_create(...)` trong `transaction.atomic()` | `SELECT ... FOR UPDATE` |
| Lọc danh sách | `LeaveRequest.objects.filter(user=user)` | `SELECT ... WHERE user_id=?` |
| Lọc nâng cao (lookup) | `filter(status=PENDING, user_id__in=ids)` | `WHERE status='pending' AND user_id IN (...)` |
| JOIN sẵn (chống N+1) | `.select_related('user','user__profile')` | `SELECT ... JOIN auth_user JOIN userprofile` |
| Tính tổng | `approved_qs.aggregate(total=Sum('days'))` | `SELECT SUM(days) ...` |
| Lấy 1 cột | `.values_list('user_id', flat=True)` | `SELECT user_id ...` |
| Xóa | `FaceChangeRequest.objects.filter(status=PENDING).delete()` | `DELETE FROM ... WHERE status='pending'` |
| Cập nhật hàng loạt | `Notification.objects.filter(is_read=False).update(is_read=True)` | `UPDATE ... SET is_read=true WHERE ...` |

**Hai điều người mới hay nhầm:**
1. **QuerySet "lười":** `qs = Model.objects.filter(...)` **chưa** chạm DB. Chỉ khi lặp `for`/`list()`/`.count()`/`.first()`
   mới bắn SQL. Cho phép nối nhiều `.filter().exclude().select_related()` rồi mới query **một** lần.
2. **`save()` vs `save(update_fields=...)`:** không truyền `update_fields` → UPDATE **mọi** cột; truyền vào → chỉ cột đó.
   Project ưu tiên `update_fields` ở các thao tác duyệt để an toàn + nhanh.

Tất cả chạy trên DB nào? `settings.DATABASES` quyết định: dev = SQLite (file `db.sqlite3`), prod = PostgreSQL (Render),
**cùng một code ORM** (xem `how_it_works.md` §5.4).

---

## 7. Validation: dữ liệu bẩn bị chặn ở đâu

Dữ liệu người dùng **không bao giờ được tin**. Nó bị lọc qua **nhiều lớp**, từ ngoài vào trong:

```
① Trình duyệt (HTML)      type="date", required, accept="image/*"   ← chặn nhẹ, dễ bị bỏ qua
② CSRF middleware         token hợp lệ?                              ← chống giả mạo request
③ Decorator               @login_required / quyền hạn               ← chống truy cập trái phép
④ Form.is_valid()         ép kiểu + clean_<field>() + clean()        ← LỚP CHÍNH cho form
⑤ Service                 quy tắc nghiệp vụ (ai duyệt? tự duyệt?)     ← chốt logic
⑥ Model/Database          unique_together, NOT NULL, FK              ← rào chắn cuối
```

Lớp ④ là quan trọng nhất cho form. Ví dụ thật:
- Upload: hàm chung [validate_upload()](business_web/common/file_validation.py) — ≤ **5 MB**, MIME ∈ {PDF, JPG, PNG}
  (minh chứng linh hoạt thêm GIF/WEBP). Dùng lại ở leaves/overtime/attendance/reports/rewards → một chỗ sửa, mọi nơi đổi.
- Nghỉ phép: `clean_start_date` (không quá 7 ngày quá khứ) + `clean` (`end >= start`).
- Điều chỉnh công: `clean_evidence(required=True)` (bắt buộc) + `clean` (phải có ít nhất giờ vào **hoặc** giờ ra).

Nếu lớp ④ raise `ValidationError` → `is_valid()` = `False` → view **không** gọi service → render lại form kèm lỗi đỏ.
Dữ liệu bẩn **không bao giờ** tới được DB.

---

## 8. Bảng đối chiếu: field frontend → cột database

Lấy nghỉ phép làm ví dụ trọn vẹn "người dùng gõ gì → nằm ở cột nào":

| Người dùng nhập (HTML `name`) | Đi vào `request` | Form field | Cột DB (`leave_request`) | Ai đặt |
|-------------------------------|------------------|------------|--------------------------|--------|
| `leave_type` (select) | `request.POST` | `leave_type` | `leave_type` | người dùng |
| `start_date` (date) | `request.POST` | `start_date` | `start_date` | người dùng |
| `end_date` (date) | `request.POST` | `end_date` | `end_date` | người dùng |
| `reason` (textarea) | `request.POST` | `reason` | `reason` | người dùng |
| `attachment` (file) | `request.FILES` | `attachment` | `attachment` (đường dẫn file) | người dùng |
| `csrfmiddlewaretoken` | `request.POST` | — | (không lưu) | Django |
| — | `request.user` | — | `user_id` | **service** gán |
| — | — | — | `status='pending'` | **service** gán |
| — | — | — | `days` (tính từ start/end) | **service** tính |
| — | — | — | `created_at` | **DB** auto |
| — | — | — | `leader_approved_by/at`, `approved_by` | điền khi **duyệt** |

Đọc bảng này từ trên xuống chính là đọc vòng đời một bản ghi: **người dùng cấp phần nhập liệu → service cấp phần
hệ thống → DB cấp phần tự động → quy trình duyệt cấp phần phê duyệt.**

---

### Nhớ 4 điều

1. **Phân biệt 3 kênh truyền:** form-thường (`request.POST`), form-file (`+request.FILES`), AJAX-JSON (`fetch` → `JsonResponse`).
2. **View điều phối, không quyết định:** view chỉ `is_valid()` → gọi **service** → `redirect`/`JsonResponse`. Logic ở service.
3. **PRG cho form, status-code cho AJAX:** form lưu xong thì *redirect*; AJAX thì trả *mã HTTP* để JS hiểu.
4. **DB chỉ bị chạm ở `service` (qua `.save()/.filter()/...`)**, sau khi dữ liệu đã qua mọi lớp validation.

> 📌 Đối chiếu code ngày **03/06/2026**. Mọi tên hàm/field/path trích trực tiếp từ `business_web/`.
> Đọc kèm: [how_it_works.md](how_it_works.md) (khái niệm nền), [walkthrough.md](walkthrough.md) (nghiệp vụ + sơ đồ).

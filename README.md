# Business Web — Hệ thống Quản lý Nhân sự (HRM)

Đồ án môn **Nhập môn Công nghệ Phần mềm** — Trường Đại học Công nghệ Thông tin (UIT).

Ứng dụng web quản lý nhân sự nội bộ xây trên **Django**: quản lý người dùng &
phân quyền, hồ sơ nhân viên, hợp đồng lao động, chấm công bằng **nhận diện khuôn
mặt**, nghỉ phép, tăng ca, đánh giá hiệu suất, khen thưởng/kỷ luật, báo cáo,
ticket và thống kê tổng hợp — với luồng phê duyệt nhiều cấp và phân quyền theo
vai trò (RBAC).

## Tổng quan

Hệ thống số hóa vòng đời nhân sự trong một doanh nghiệp trên một nền tảng duy nhất:

- **Tài khoản & phân quyền** — đăng ký, đăng nhập, quên mật khẩu qua **OTP gửi
  email** (hiệu lực 2 phút). 5 vai trò hệ thống, mỗi vai trò thấy giao diện và
  quyền khác nhau. Admin chỉ quản trị hệ thống, **không** dùng các chức năng
  nghiệp vụ (bị chặn bởi decorator `deny_admin`).
- **Chấm công nhận diện khuôn mặt** — nhân viên check-in/check-out bằng camera;
  ảnh được gửi tới **một API nhận diện khuôn mặt bên ngoài** (Hugging Face Space)
  để xác thực. Toàn bộ trích xuất vector, lưu trữ và so khớp chạy trên service từ
  xa — **không** load model AI trong ứng dụng. Khóa tạm sau nhiều lần thất bại
  (mặc định 3 lần / 300 giây).
- **Luồng phê duyệt nhiều cấp** — nghỉ phép, tăng ca, khen thưởng/kỷ luật đi qua
  quy trình 2 bước (Leader/Manager → HR); yêu cầu điều chỉnh công và đổi khuôn
  mặt do HR duyệt. Đổi khuôn mặt là **chống gian lận**: thay đổi không có hiệu
  lực ngay mà chờ HR duyệt, lưu SHA-256 + IP + cờ đổi-mặt-hộ-người-khác để audit.
- **Báo cáo & thống kê** — báo cáo cá nhân gửi theo phân cấp quản lý, ticket
  hỗ trợ/khiếu nại, và trang thống kê tổng hợp công/nghỉ/tăng ca có **xuất Excel**
  và bản in.

## Vai trò người dùng (RBAC)

Định nghĩa tại [accounts/models/role_model.py](business_web/accounts/models/role_model.py):

| Vai trò    | Mô tả |
|------------|-------|
| `admin`    | Quản trị hệ thống: quản lý người dùng, gán vai trò/quyền. Không dùng chức năng nghiệp vụ |
| `hr`       | Nhân sự: hồ sơ, hợp đồng, duyệt cuối các yêu cầu, cấu hình chấm công |
| `manager`  | Quản lý phòng ban: duyệt bước 1 cho nhân viên cấp dưới |
| `leader`   | Trưởng nhóm: duyệt bước 1 trong phạm vi nhóm |
| `employee` | Nhân viên: xem hồ sơ, chấm công, gửi các loại yêu cầu |

Ngoài vai trò, mỗi tài khoản có thể được gán thêm **quyền tùy chỉnh**
(`CustomPermission`) độc lập với vai trò.

## Các module chức năng

Ứng dụng gồm **10 Django app nghiệp vụ** + package `common` dùng chung
(đăng ký tại [business_web/urls.py](business_web/business_web/urls.py)):

### `accounts` — Tài khoản, phân quyền, dashboard
Đăng nhập/đăng ký/đăng xuất, quên & đặt lại mật khẩu qua OTP email, dashboard,
mô phỏng vai trò (switch-role), thông báo (`Notification`). Quản trị người dùng:
tạo tài khoản, gán vai trò/quyền, khóa/mở, xóa, đặt lại mật khẩu.
Models: `UserProfile`, `Role`, `CustomPermission`, `OtpCode`, `Notification`.

### `employee_profiles` — Hồ sơ nhân viên
Thông tin cá nhân, học vấn & kỹ năng, liên hệ khẩn cấp, thông tin công việc
(phòng ban, chức danh, quản lý/leader trực tiếp, trạng thái làm việc), và tải lên
tệp minh chứng. HR tạo hồ sơ, xem hồ sơ, gán vai trò, sửa thông tin công việc.
Models: `PersonalInfo`, `EmployeeWorkInfo`, `EducationAndSkills`,
`EmergencyContact`, `EmployeeDocument`.

### `contracts` — Hợp đồng lao động
Hợp đồng có **lưu lịch sử phiên bản** (1 hợp đồng hiệu lực tại một thời điểm).
Nhân viên xem hợp đồng cá nhân; HR xem danh sách sắp hết hạn, điều chỉnh (tạo
phiên bản mới), gửi email nhắc gia hạn (từng người hoặc tất cả). Model: `ContractInfo`.

### `attendance` — Chấm công nhận diện khuôn mặt
Check-in/out qua ảnh khuôn mặt, ghi `AttendanceRecord` (đúng giờ/trễ/vắng).
Yêu cầu điều chỉnh công (HR duyệt), yêu cầu đổi khuôn mặt (HR duyệt, chống gian
lận), cấu hình giờ làm toàn công ty (singleton 08:30–17:30, ân hạn trễ 5 phút).
Models: `AttendanceRecord`, `EmployeeFace`, `AttendanceAdjustmentRequest`,
`FaceChangeRequest`, `WorkScheduleConfig`.

### `leaves` — Nghỉ phép
Đơn nghỉ (phép năm, ốm, việc riêng, thai sản, công tác, khác) kèm minh chứng.
Duyệt 2 bước: Leader/Manager → HR (HR tự gửi chỉ cần 1 bước). Model: `LeaveRequest`.

### `overtime` — Tăng ca
Đăng ký tăng ca theo ngày/giờ, duyệt 2 bước như nghỉ phép. Model: `OvertimeRequest`.

### `performance` — Đánh giá hiệu suất
Manager/Leader tạo đánh giá theo hạng mục (`EvaluationCategory`); chấm điểm
thang 100 tự suy ra xếp loại A/B/C/D; HR xác nhận hoặc từ chối.
Models: `Evaluation`, `EvaluationCategory`.

### `rewards_discipline` — Khen thưởng & Kỷ luật
Phiếu khen thưởng/xử phạt (số tiền VND, lý do, minh chứng), duyệt nhiều cấp
kết thúc ở HR. Model: `RewardPenalty`.

### `reports_interactions` — Báo cáo & Ticket
Báo cáo cá nhân gửi lên quản lý theo phân cấp (khóa sửa/xóa sau khi được tiếp
nhận). Ticket hỗ trợ/khiếu nại có mức ưu tiên, trạng thái xử lý, người phụ trách.
Models: `Report`, `Ticket`.

### `stats_reports` — Thống kê tổng hợp
Tổng hợp dữ liệu chấm công/nghỉ phép/tăng ca thực từ CSDL, **xuất Excel**
(openpyxl) và bản in. Không có model riêng — đọc dữ liệu từ các app khác.

### `common` — Tiện ích dùng chung
Validator, kiểm tra file tải lên (`file_validation.py`), middleware
`NoCacheForAuthenticatedMiddleware` (chặn cache trang cho user đã đăng nhập).

## Công nghệ

- **Backend:** Django 4.2 (Python)
- **Database:** cấu hình qua `DATABASE_URL` (dj-database-url) — PostgreSQL
  (`psycopg2-binary`) ở production, SQLite mặc định khi dev local
- **Nhận diện khuôn mặt:** API ngoài (Hugging Face Space) qua endpoint
  `/register` + `/recognize`, cấu hình bằng `FACE_API_BASE_URL`
- **Lưu trữ:** static qua WhiteNoise; media qua Cloudinary
  (`RawMediaCloudinaryStorage` — nhận cả ảnh lẫn PDF) khi `USE_CLOUDINARY=True`,
  ngược lại lưu đĩa local
- **Email:** Gmail SMTP (gửi OTP và nhắc gia hạn hợp đồng)
- **Xuất file:** openpyxl (Excel) · Pillow (xử lý ảnh)
- **Deploy:** Render (web service + Postgres) · Gunicorn

## Bố cục code

Mỗi app gom code theo **feature sub-package** bên trong từng thư mục theo loại
(`forms/`, `services/`, `views/`, `templates/<app>/`, `tests/`), tham khảo
`accounts` và `attendance`. Ví dụ `attendance`: `services/face/`,
`services/record/`, `services/schedule/`, `views/`, `templates/attendance/`.

- `models/` và `migrations/` giữ phẳng (flat) — không chia sub-package.
- Mỗi `__init__.py` cấp type-package re-export public API, nên
  `from <app>.views import X` chạy được bất kể X nằm ở sub-package nào.
- KHÔNG tạo sẵn thư mục feature rỗng — chỉ thêm khi có code.

Chi tiết: `docs/superpowers/specs/2026-05-31-attendance-folder-sectioning-design.md`.

## Chạy local

```bash
cd business_web

# 1. Cài dependency
pip install -r requirements.txt

# 2. Tạo file .env từ mẫu rồi điền giá trị (xem .env.example)
cp .env.example .env

# 3. Khởi tạo database (mặc định SQLite)
python manage.py migrate

# 4. Tạo tài khoản quản trị
python manage.py createsuperuser

# 5. Chạy server
python manage.py runserver
```

Mở http://127.0.0.1:8000 (route gốc `/` chuyển hướng tới trang đăng nhập).

### Biến môi trường (`.env`)

Khai báo đầy đủ trong [business_web/.env.example](business_web/.env.example):

| Biến | Mục đích |
|------|----------|
| `SECRET_KEY`          | Khóa bí mật Django. Prod bắt buộc chuỗi mạnh ≥50 ký tự (khởi động sẽ chặn nếu yếu khi `DEBUG=False`) |
| `DEBUG`               | `True` cho dev, `False` cho prod |
| `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` | Host & origin cho phép |
| `DATABASE_URL`        | Chuỗi kết nối Postgres (để trống = SQLite local) |
| `EMAIL_HOST_*`        | Gmail SMTP cho OTP và email nhắc hợp đồng |
| `USE_CLOUDINARY` + `CLOUDINARY_*` | Bật lưu media trên Cloudinary (prod) |
| `FACE_API_BASE_URL`   | Endpoint API nhận diện khuôn mặt |
| `FACE_API_TIMEOUT_SEC`, `FACE_LOCKOUT_MAX_FAILS`, `FACE_LOCKOUT_DURATION_SEC` | Tinh chỉnh chấm công khuôn mặt |

## Tác vụ định kỳ (management commands)

| Lệnh | Chức năng |
|------|-----------|
| `python manage.py ensure_superuser` | Tạo/cập nhật superuser từ env (idempotent) — dùng khi deploy không có shell |
| `python manage.py close_open_attendance [--cutoff YYYY-MM-DD]` | Đánh dấu `no_checkout` cho bản ghi có giờ vào nhưng thiếu giờ ra |
| `python manage.py send_contract_renewal_reminders` | Quét hợp đồng sắp hết hạn và gửi email nhắc gia hạn |

`setup_task_scheduler.py` (Windows) tạo Scheduled Task chạy lệnh nhắc gia hạn
hợp đồng lúc 0:00 hàng ngày.

## Deploy (Render)

Repo có sẵn [render.yaml](render.yaml) (Blueprint) — tự tạo web service + Postgres:

1. Render Dashboard → **New** → **Blueprint** → chọn repo này.
2. Điền các secret đánh dấu `sync: false` (Cloudinary, Email).
3. `build.sh` tự chạy khi deploy: cài deps → `collectstatic` → `migrate`
   → `ensure_superuser`.
4. Khởi động bằng `gunicorn business_web.wsgi:application`.

## Kiểm thử

- Chạy toàn bộ: `python manage.py test` (mỗi app có thư mục `tests/`).
- Chạy theo app: `python manage.py test <app>`.
- Tài liệu kiểm thử ở gốc repo: `test_plan.md`, `test_result.md`, `walkthrough.md`.

> `interface.py` và `register.py` ở gốc repo là script demo thủ công gọi trực
> tiếp API nhận diện khuôn mặt (`/recognize`, `/register`) — không thuộc ứng dụng Django.

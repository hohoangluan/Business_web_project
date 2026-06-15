# Gói 2 — Cấu hình giờ làm (HR) + chấm công dùng config

Ngày: 2026-06-03. Gói 2/5 của kế hoạch cải thiện UI/RBAC.

## Vấn đề

1. Giờ vào/ra hiện lấy từ `contracts.services.get_shift_times(user)`: HĐ active override →
   fallback **hằng số tĩnh** `settings.WORK_START_TIME` (08:30) / `WORK_END_TIME` (17:30).
   Không ai (kể cả HR) sửa được giờ chuẩn công ty mà không deploy lại code.
2. Panel "Quy định Nhân Sự" trong `settings.html` (tab-hr) hiển thị ô giờ 08:30/17:30 +
   "ngưỡng cảnh báo đi trễ" nhưng **toàn bộ là DEMO**: giá trị hardcode, nút lưu chỉ chạy
   `onclick="alert('...demo...')"`. Không persist, không ảnh hưởng backend.
3. Form điều chỉnh HĐ (`ContractAdjustForm`) có `shift_start_time`/`shift_end_time` nhưng
   **không validate** end > start → có thể lưu giờ ra trước giờ vào, làm sai phân loại
   trễ/sớm (lỗi đồng bộ dữ liệu).

## Quyết định (đã chốt với người dùng)

- HR cấu hình **một** lịch giờ cố định toàn công ty (giờ vào, giờ ra, ân hạn đi trễ).
- Ưu tiên: **giờ ca HĐ (nếu set) → WorkScheduleConfig (HR) → hằng số settings**.
  HĐ vẫn override được cho nhân viên có giờ riêng (giữ tính linh hoạt feature HĐ).
- UI nhúng vào panel tab-hr của `settings.html` hiện có (không tạo trang mới).
- Phạm vi: chỉ 3 thông số (giờ vào, giờ ra, ân hạn). Các ô demo khác (nghỉ phép, tăng ca,
  SLA, ngưỡng cảnh báo lần/tháng) **giữ nguyên demo** — ngoài phạm vi.

## Thiết kế

### Model — `attendance.WorkScheduleConfig` (singleton)

Đặt trong app `attendance` (nơi tiêu thụ phân loại trễ/sớm).

| Field | Kiểu | Mặc định |
|---|---|---|
| `shift_start` | TimeField | 08:30 |
| `shift_end` | TimeField | 17:30 |
| `late_grace_minutes` | PositiveIntegerField | 5 |

- `get_solo()` classmethod: trả dòng pk=1, tạo với mặc định nếu chưa có. Toàn hệ thống 1 dòng.
- Migration: tạo bảng + data migration seed dòng pk=1 = (08:30, 17:30, 5) khớp settings cũ.

### Service (attendance)

- `get_work_schedule()` → `WorkScheduleConfig.get_solo()`.
- `get_late_grace_minutes()` → `get_work_schedule().late_grace_minutes`.

### Resolver giờ (contracts)

- `get_shift_times(user)`: HĐ active có `shift_start_time`/`shift_end_time` → dùng;
  else → `WorkScheduleConfig.get_solo()` (thay đọc thẳng settings).
- `attendance_logging_service.classify_status`: đọc grace qua `get_late_grace_minutes()`
  thay `settings.WORK_LATE_GRACE_MIN`. (Chữ ký hàm có thể nhận grace tham số để test thuần.)

### UI HR — panel tab-hr trong `settings.html`

- `WorkScheduleConfigForm` (ModelForm trên `WorkScheduleConfig`), `clean()`:
  `shift_end > shift_start`; `late_grace_minutes >= 0`. Lỗi → thông báo tiếng Việt.
- `settings_view`:
  - GET: nạp form từ singleton, render giá trị thật vào ô (bỏ hardcode).
  - POST (chỉ HR/admin/superuser): bind form, valid → save + `messages.success`;
    invalid → render lại panel kèm lỗi. Employee POST → bỏ qua (không đổi gì).
- Đổi nút lưu panel HR: bỏ `alert(...)`, dùng `<form method="post">` + `{% csrf_token %}`.
  Input giờ dùng `type="time"`, ân hạn `type="number" min="0"`.

### Fix đồng bộ form HĐ

- `ContractAdjustForm.clean()`: nếu cả `shift_start_time` và `shift_end_time` có giá trị
  và `shift_end_time <= shift_start_time` → `add_error('shift_end_time', ...)` tiếng Việt.

## Test (TDD)

- Model: `get_solo()` tạo 1 dòng + idempotent; mặc định đúng.
- Resolver: HĐ set giờ → thắng config; HĐ trống → lấy config; grace lấy từ config.
- `classify_status`: late tính theo grace của config (vd grace=0 vs grace=15 cho cùng giờ vào).
- View settings: employee GET không thấy panel HR / POST không lưu; HR POST hợp lệ → lưu +
  message; HR POST end<start → hiện lỗi, không lưu.
- Form HĐ: end<start bị từ chối; end>start qua.

## Loại trừ (YAGNI)

Không: lịch theo phòng ban / theo thứ trong tuần / ca xoay / nhiều ca. Không đụng field demo
khác trong panel HR. Một lịch cố định toàn công ty + override theo HĐ.

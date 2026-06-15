# Gói 5 — Báo cáo Audit RBAC / Form / Đồng bộ dữ liệu

Ngày: 2026-06-03. Quét toàn bộ (theo yêu cầu "quét hết, báo cáo trước rồi mới fix").

## Tổng quan — phần lớn ĐẠT

Quét gating quyền + validate form + phản hồi lỗi trên tất cả app. Kết quả: **hệ thống
phần lớn chắc chắn**. Các điểm đã xác minh tốt:

- **Gating quyền (RBAC) ở endpoint mutate**: leaves / overtime / rewards / reports / performance
  đều có `@login_required` + `@require_POST` + kiểm tra role (`can_manage_requests` /
  `can_manage_work_info` / `can_acknowledge_evaluation`) TRƯỚC khi đổi dữ liệu. Không thấy
  endpoint duyệt/từ chối nào hở quyền.
- **Validate form luồng chính**: leaves (thứ tự ngày), overtime (giờ > 0, ≤ 8h, ngày),
  contracts (thứ tự ngày + giờ ca — vừa thêm Gói 2), evaluation. Có `add_error` + thông báo
  tiếng Việt → user sửa được.
- **Phản hồi lỗi**: dùng Django messages framework rộng khắp; ticket reject yêu cầu lý do →
  báo lỗi nếu thiếu.

Đã fix ở Gói 1–4: thông báo đăng nhập, cấu hình giờ làm, hợp nhất phân role, ẩn đánh giá của mình.

## Findings cần xử lý

### F1 — [CAO] hr_create_profile giả-lưu khi không tạo tài khoản
`employee_profiles/views/profile_views.py:322-327`. Khi HR bỏ tick "tạo tài khoản"
(`auto_create=False`), view hiện `"✅ Đã mô phỏng lưu hồ sơ ... Demo UI"` nhưng **không lưu
gì cả**. HR tưởng đã lưu hồ sơ → mất dữ liệu / hiểu sai trạng thái.
→ Fix: hoặc lưu hồ sơ thật (không kèm account), hoặc chặn rõ ("Bắt buộc tạo tài khoản"),
không báo thành công giả.

### F2 — [TRUNG] Panel Settings "Cá nhân" + "Hồ sơ Công ty" chỉ là alert demo
`accounts/templates/accounts/account/settings.html:184` (Cá nhân) và `:210` (Công ty, Admin).
Nút lưu = `onclick="alert(...)"`, không persist. User bấm "Lưu" tưởng đã lưu.
→ Fix: nối backend thật, hoặc gắn nhãn "(demo)" / ẩn nút cho tới khi có backend.
(Panel HR "Giờ làm" đã được làm thật ở Gói 2.)

### F3 — [THẤP] rewards_penalties_view: HR xem được phiếu của bất kỳ user qua GET param
`rewards_discipline/views/__init__.py:40-42`. HR truyền `?employee_id=` →
`get_object_or_404(User, id=...)` không giới hạn role mục tiêu (xem được cả manager/admin).
Không sửa dữ liệu, chỉ xem. Rủi ro thấp.
→ Fix (tuỳ chọn): giới hạn danh sách mục tiêu theo phạm vi HR.

### F4 — [INFO] Field demo còn lại trong panel HR Settings
Nghỉ phép / tăng ca / SLA / ngưỡng cảnh báo lần-tháng: để `disabled` demo (đã ghi nhận ở Gói 2).
Chưa nối backend — ngoài phạm vi giờ-làm.

## Trạng thái fix (yêu cầu "fix hết lỗi ngầm")

- **F1 — ĐÃ FIX.** Bỏ tick tạo TK → báo lỗi rõ "phải gắn tài khoản", không success giả,
  không mất dữ liệu. Test: `test_create_without_account_does_not_fake_success`,
  `test_create_with_account_persists`.
- **F2 — ĐÃ FIX.** Nút lưu panel "Cá nhân" + "Hồ sơ Công ty" chuyển `disabled` +
  nhãn "(đang phát triển)", bỏ `alert('Đã lưu...')` giả. Hết hiểu sai.
- **F3 — ĐÃ FIX (theo ý người dùng).** HR xem được phiếu thưởng/phạt của TẤT CẢ nhân viên
  (mọi staff: employee/leader/manager/hr), chỉ loại tài khoản Admin hệ thống. Target = Admin
  → báo lỗi + fallback. Test: `test_hr_can_view_any_employee_records`,
  `test_hr_cannot_view_admin_records`.
- **F4 — chưa fix (info).** Field demo nghỉ phép/tăng ca/SLA cần spec riêng từng quy định
  (không phải lỗi ngầm — đã gắn nhãn demo/disabled).

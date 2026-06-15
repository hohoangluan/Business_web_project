# Gói 3 — Hợp nhất phân vai trò (HR + Admin)

Ngày: 2026-06-03. Gói 3/5.

## Vấn đề

1. **Admin không có lối vào phân role qua UI.** View `assign_role_view` + URL `assign_role`
   tồn tại nhưng `user_management.html` không hề link tới → admin không đổi được vai trò
   từ giao diện.
2. **Hai đường phân role song song, trùng:**
   - Admin: `assign_role_view` (accounts) → `assign_role.html` (select thường).
   - HR: `hr_assign_role_view` (employee_profiles) → `hr_assign_role.html` (card picker đẹp),
     chặn admin, back-nav về `hr_view_profile` (cũng chặn admin).
3. **Field `role` trong form sửa hồ sơ là rác.** `EmployeeProfileForm` có field `role`
   nhưng `edit_work_info_view` POST KHÔNG lưu nó, và template edit chỉ hiển thị read-only +
   link "Đổi vai trò". Field editable nhưng vô tác dụng → gây nhầm.

## Quyết định (đã chốt với người dùng)

- Dùng **card picker** (`hr_assign_role.html`) làm trang phân role CHUNG cho cả HR + Admin.
- **Gỡ** field `role` khỏi `EmployeeProfileForm` (chỉ đổi vai trò qua trang phân role).
- Xóa hẳn đường cũ của admin (`assign_role_view` + template + form + URL).

## Thiết kế

### View hợp nhất — `hr_assign_role_view`

- Bỏ block redirect admin đi chỗ khác → admin dùng chung trang.
- `available_roles`: admin = tất cả; HR = trừ Admin (giữ nguyên).
- Bảo vệ: HR gán Admin → từ chối + ở lại trang.
- Sau khi lưu/bỏ vai trò: **admin → `user_list`**; **HR → `hr_view_profile`**
  (admin không có trang hồ sơ nhân sự).
- Quyền truy cập: decorator `can_manage_work_info` (đã bao gồm admin).

### Template card picker

- Back + Cancel link rẽ nhánh theo `editor_is_admin` (admin → `user_list`, HR → hồ sơ).

### Entry cho admin

- `user_management.html`: thêm nút "Phân vai trò" (icon user-tag) trong khối
  `can_manage_system_users`, link `hr_assign_role`.

### Dọn rác

- `EmployeeProfileForm`: bỏ field `role` + logic queryset role trong `__init__`;
  bỏ `'role'` khỏi initial dict ở `edit_work_info_view`.
- Xóa: `assign_role_view`, URL `assign_role`, `accounts/permission/assign_role.html`,
  `AssignRoleForm` + mọi export.
- Repoint test cũ (`test_role_permission`, `test_bo_sung`) sang URL `hr_assign_role`
  (hành vi tương đương: admin → user_list, employee → login redirect).

## Test (TDD)

- Admin POST trang chung gán Admin → role set + redirect `user_list`.
- Admin GET → `available_roles` chứa Admin; HR GET → không chứa Admin.
- HR gán Admin → từ chối, role không đổi.
- `EmployeeProfileForm()` không còn field `role`.
- Bỏ vai trò (role rỗng) → None.

## Loại trừ (YAGNI)

Không đổi tên URL `hr_assign_role` (giữ để giảm churn). Không đụng `assign_permissions`
(phân quyền chi tiết) — ngoài phạm vi.

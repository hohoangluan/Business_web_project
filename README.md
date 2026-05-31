# Business_web_project
This is Introduction to Software Engineering Project in UIT

## Quy ước bố cục app (App layout convention)

Các app có nhiều mảng chức năng gom code theo **feature sub-package** bên trong mỗi
thư mục theo loại (`forms/`, `services/`, `views/`, `templates/<app>/`, `tests/`),
giống `accounts` và `attendance`. Ví dụ `attendance`: `services/face/`,
`services/record/`, `views/adjustment/`, `templates/attendance/record/`, `tests/face/`.

- `models/` và `migrations/` giữ phẳng (flat) — không chia sub-package.
- Mỗi `__init__.py` cấp type-package re-export public API, nên
  `from <app>.views import X` vẫn chạy bất kể X nằm ở sub-package nào.
- KHÔNG tạo sẵn thư mục feature rỗng trong app stub — chỉ thêm khi có code.

Chi tiết: `docs/superpowers/specs/2026-05-31-attendance-folder-sectioning-design.md`.

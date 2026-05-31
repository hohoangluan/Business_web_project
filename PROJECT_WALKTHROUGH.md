# PROJECT WALKTHROUGH — HRM System (Django)

> Cập nhật: 05/05/2026 — Sau khi tái cấu trúc thành kiến trúc đa-app.

---

## 1. Tổng quan kiến trúc

Project HRM System được xây dựng bằng Django 6.0, sử dụng SQLite làm database.
Giao diện dùng Django Templates + Tailwind CSS + Alpine.js, theme Pastel Light.

### Kiến trúc 10 Django Apps

| # | App | Chức năng | Models chính |
|---|-----|-----------|--------------|
| 1 | `accounts` | Auth, dashboard, admin user management, settings | `Role`, `CustomPermission`, `UserProfile` |
| 2 | `employee_profiles` | Hồ sơ nhân viên, thông tin công việc | `EmployeeWorkInfo` |
| 3 | `contracts` | Hợp đồng lao động | `ContractInfo` |
| 4 | `attendance` | Chấm công | `AttendanceRecord` (placeholder) |
| 5 | `leaves` | Nghỉ phép & phê duyệt | `LeaveRequest` (placeholder) |
| 6 | `overtime` | Tăng ca & phê duyệt | `OvertimeRequest` (placeholder) |
| 7 | `performance` | Đánh giá nhân viên | `Evaluation` (placeholder) |
| 8 | `rewards_discipline` | Khen thưởng & Xử phạt | `RewardPenalty` (placeholder) |
| 9 | `reports_interactions` | Báo cáo, hộp thư, ticket | `Report`, `Ticket` (placeholder) |
| 10 | `stats_reports` | Thống kê tổng hợp (đọc từ app khác) | Không có model riêng |

> **Lưu ý:** App `stats_reports` dùng tên `stats_reports` thay vì `statistics` để tránh trùng với thư viện chuẩn Python.

---

## 2. Cấu trúc thư mục

> **Quy ước bố cục app:** App nhiều mảng chức năng chia code theo feature bên trong mỗi
> thư mục theo loại (xem `accounts`, `attendance`: `services/face/`, `views/adjustment/`,
> `templates/attendance/record/`, `tests/face/`...). `models/` và `migrations/` giữ phẳng;
> mỗi type-package `__init__.py` re-export public API. Chi tiết:
> `docs/superpowers/specs/2026-05-31-attendance-folder-sectioning-design.md`.

```text
business_web/
├── manage.py
├── db.sqlite3
├── business_web/           # Project config
│   ├── settings.py         # INSTALLED_APPS, middleware, database...
│   ├── urls.py             # Root URL config — include từ 10 apps
│   └── wsgi.py
│
├── accounts/               # Auth & Admin
│   ├── models.py           # Role, CustomPermission, UserProfile
│   ├── views.py            # Login, register, dashboard, admin user mgmt
│   ├── forms.py            # RegisterForm, AssignRoleForm, AssignPermissionsForm
│   ├── urls.py             # Auth routes + admin routes
│   ├── admin.py            # Django admin config
│   ├── services/           # Shared helpers (ensure_profile, role checks...)
│   │   └── __init__.py
│   ├── templates/accounts/ # 10 templates (login, register, dashboard...)
│   └── static/accounts/    # CSS, JS dùng chung
│
├── employee_profiles/      # Hồ sơ nhân viên
│   ├── models.py           # EmployeeWorkInfo (OneToOne → User)
│   ├── views/              # profile_view, hr_create_profile, edit_work_info
│   ├── forms.py            # EmployeeProfileForm
│   ├── urls.py
│   ├── services/           # Helpers: queryset quản lý, save data...
│   └── templates/employee_profiles/  # 3 templates
│
├── contracts/              # Hợp đồng lao động
│   ├── models.py           # ContractInfo (OneToOne → User)
│   ├── views/              # contract_view
│   ├── urls.py
│   ├── services/           # Contract context builder, date parser
│   └── templates/contracts/  # 1 template
│
├── attendance/             # Chấm công
│   ├── models.py           # AttendanceRecord (placeholder)
│   ├── views/              # attendance_view (mock)
│   ├── urls.py
│   └── templates/attendance/  # 1 template
│
├── leaves/                 # Nghỉ phép
│   ├── models.py           # LeaveRequest (placeholder)
│   ├── views/              # leave_view, leave_approval_view (mock)
│   ├── urls.py
│   └── templates/leaves/   # 2 templates
│
├── overtime/               # Tăng ca
│   ├── models.py           # OvertimeRequest (placeholder)
│   ├── views/              # overtime_view, overtime_approval_view (mock)
│   ├── urls.py
│   └── templates/overtime/ # 2 templates
│
├── performance/            # Đánh giá nhân viên
│   ├── models.py           # Evaluation (placeholder)
│   ├── views/              # evaluations_view
│   ├── urls.py
│   ├── services/           # Evaluation logic + mock data (evaluation_data.py)
│   └── templates/performance/  # 1 template
│
├── rewards_discipline/     # Khen thưởng & Xử phạt
│   ├── models.py           # RewardPenalty (placeholder)
│   ├── views/              # rewards_penalties_view, approval
│   ├── urls.py
│   ├── services/           # Mock data (rewards_data.py)
│   └── templates/rewards_discipline/  # 2 templates
│
├── reports_interactions/   # Báo cáo & Ticket
│   ├── models.py           # Report, Ticket (placeholder)
│   ├── views/              # report, inbox, tickets, process
│   ├── urls.py
│   └── templates/reports_interactions/  # 4 templates
│
└── stats_reports/          # Thống kê tổng hợp
    ├── models.py           # Không có model (aggregator)
    ├── views/              # statistics_view, export CSV, print
    ├── urls.py
    ├── services/           # Statistics logic + mock data (statistics_data.py)
    └── templates/stats_reports/  # 2 templates
```

---

## 3. Model Architecture

### 3.1 accounts — Auth & Identity

```
UserProfile (OneToOne → User)
├── role          → ForeignKey(Role)
├── permissions   → ManyToMany(CustomPermission)
├── full_name     # Họ tên
├── phone_number  # SĐT
├── date_of_birth # Ngày sinh (DD/MM/YYYY)
└── employee_id   # Mã nhân viên (unique)

Role
├── name          # admin, hr, manager, leader, employee
└── description

CustomPermission
├── codename      # VD: can_export_reports
├── name          # Tên hiển thị
└── description
```

### 3.2 employee_profiles — Work Info

```
EmployeeWorkInfo (OneToOne → User, related_name='work_info')
├── employee_type     # Loại NV: Toàn thời gian, Thực tập...
├── department        # Phòng ban
├── position          # Chức danh
├── workplace         # Nơi làm việc
├── probation_start   # Ngày thử việc
├── official_start_date
├── work_status       # Choices: working, probation, paused, resigned
├── manager_user      → ForeignKey(User)
└── leader_user       → ForeignKey(User)
```

### 3.3 contracts — Contract Info

```
ContractInfo (OneToOne → User, related_name='contract_info')
├── contract_number
├── contract_type
├── contract_signed_date
├── contract_start_date
├── contract_end_date
├── contract_annual_leave_days
├── contract_standard_shift
└── contract_attachment_reference
```

### 3.4 Placeholder Models (chờ backend thật)

- `attendance.AttendanceRecord` — bản ghi chấm công theo ngày
- `leaves.LeaveRequest` — đơn nghỉ phép
- `overtime.OvertimeRequest` — đơn tăng ca
- `performance.Evaluation` — bản đánh giá
- `rewards_discipline.RewardPenalty` — phiếu thưởng/phạt
- `reports_interactions.Report` — báo cáo
- `reports_interactions.Ticket` — ticket hỗ trợ/khiếu nại

---

## 4. URL Routing

### Root `business_web/urls.py`

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('employee_profiles.urls')),
    path('', include('contracts.urls')),
    path('', include('attendance.urls')),
    path('', include('leaves.urls')),
    path('', include('overtime.urls')),
    path('', include('performance.urls')),
    path('', include('rewards_discipline.urls')),
    path('', include('reports_interactions.urls')),
    path('', include('stats_reports.urls')),
]
```

### Bảng route theo app

| URL | View | App | Template |
|-----|------|-----|----------|
| `/` | → redirect `/login/` | accounts | — |
| `/login/` | LoginView | accounts | `accounts/login.html` |
| `/register/` | register_view | accounts | `accounts/register.html` |
| `/forgot-password/` | forgot_password_view | accounts | `accounts/forgot_password.html` |
| `/logout/` | logout_view | accounts | — |
| `/dashboard/` | dashboard_view | accounts | `accounts/dashboard.html` |
| `/settings/` | settings_view | accounts | `accounts/settings.html` |
| `/switch-role/` | switch_role_view | accounts | — |
| `/users/` | user_list_view | accounts | `accounts/user_management.html` |
| `/users/<id>/role/` | assign_role_view | accounts | `accounts/assign_role.html` |
| `/users/<id>/permissions/` | assign_permissions_view | accounts | `accounts/assign_permissions.html` |
| `/users/<id>/delete/` | delete_user_view | accounts | `accounts/delete_user.html` |
| `/users/<id>/toggle-active/` | toggle_user_active_view | accounts | — |
| `/users/<id>/reset-password/` | reset_user_password_view | accounts | — |
| `/profile/` | profile_view | employee_profiles | `employee_profiles/profile.html` |
| `/hr/create-profile/` | hr_create_profile_view | employee_profiles | `employee_profiles/hr_create_profile.html` |
| `/users/<id>/work-info/` | edit_work_info_view | employee_profiles | `employee_profiles/edit_work_info.html` |
| `/contract/` | contract_view | contracts | `contracts/contract.html` |
| `/attendance/` | attendance_view | attendance | `attendance/attendance.html` |
| `/leave/` | leave_view | leaves | `leaves/leave.html` |
| `/leave/approval/` | leave_approval_view | leaves | `leaves/leave_approval.html` |
| `/overtime/` | overtime_view | overtime | `overtime/overtime.html` |
| `/overtime/approval/` | overtime_approval_view | overtime | `overtime/overtime_approval.html` |
| `/evaluations/` | evaluations_view | performance | `performance/evaluations.html` |
| `/statistics/` | statistics_view | stats_reports | `stats_reports/statistics.html` |
| `/statistics/export-csv/` | statistics_export_csv_view | stats_reports | — |
| `/statistics/print/` | statistics_print_view | stats_reports | `stats_reports/statistics_print.html` |
| `/rewards-penalties/` | rewards_penalties_view | rewards_discipline | `rewards_discipline/rewards_penalties.html` |
| `/rewards-penalties/approval/` | rewards_penalties_approval_view | rewards_discipline | `rewards_discipline/rewards_penalties_approval.html` |
| `/reports/` | report_view | reports_interactions | `reports_interactions/report.html` |
| `/reports/inbox/` | report_inbox_view | reports_interactions | `reports_interactions/report_inbox.html` |
| `/tickets/` | ticket_list_view | reports_interactions | `reports_interactions/tickets.html` |
| `/tickets/process/` | ticket_process_view | reports_interactions | `reports_interactions/ticket_process.html` |

---

## 5. Shared Services Architecture

### `accounts/services/__init__.py`

File trung tâm chứa các helper mà mọi app đều import:

| Function | Mô tả | Dùng bởi |
|----------|--------|----------|
| `ensure_profile(user)` | Tạo UserProfile nếu chưa có | Tất cả apps |
| `ensure_work_info(user)` | Tạo EmployeeWorkInfo nếu chưa có | employee_profiles, contracts, stats_reports... |
| `ensure_contract_info(user)` | Tạo ContractInfo nếu chưa có | contracts, employee_profiles |
| `is_admin_user(user)` | Check admin permission | accounts, employee_profiles |
| `is_hr_user(user)` | Check HR permission | employee_profiles |
| `can_manage_requests(user)` | HR/Manager/Leader/Admin | leaves, overtime, rewards_discipline, reports |
| `can_manage_work_info(user)` | HR/Admin | employee_profiles, accounts |
| `can_access_statistics(user)` | HR/Admin/Manager/Leader | stats_reports |
| `can_access_evaluations(user)` | Manager/Leader | performance |
| `get_user_role_name(user)` | Lấy tên role | Nhiều apps |
| `get_user_display_name(user)` | Ưu tiên full_name | stats_reports, performance |

---

## 6. Vai trò & Phân quyền

| Role | Dashboard | Profile | Attendance | Leave | Overtime | Evaluations | Statistics | Rewards | Reports | Tickets | Users |
|------|:---------:|:-------:|:----------:|:-----:|:--------:|:-----------:|:----------:|:-------:|:-------:|:-------:|:-----:|
| Admin | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| HR | ✅ | ✅ | ✅ | ✅ (+duyệt) | ✅ (+duyệt) | ❌ | ✅ | ✅ (+duyệt) | ✅ (+inbox) | ✅ (+xử lý) | ✅ |
| Manager | ✅ | ✅ | ✅ | ✅ (+duyệt) | ✅ (+duyệt) | ✅ | ✅ | ✅ (+duyệt) | ✅ (+inbox) | ✅ (+xử lý) | ❌ |
| Leader | ✅ | ✅ | ✅ | ✅ (+duyệt) | ✅ (+duyệt) | ✅ | ✅ | ✅ (+duyệt) | ✅ (+inbox) | ✅ (+xử lý) | ❌ |
| Employee | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |

---

## 7. Mock Data & Services

Hiện tại các module sau vẫn dùng mock data (chưa có backend thật):

| App | Mock data file | Mô tả |
|-----|----------------|--------|
| `stats_reports` | `services/statistics_data.py` | Chấm công, nghỉ phép, tăng ca theo ngày |
| `performance` | `services/evaluation_data.py` | Đánh giá từ Leader/Manager |
| `rewards_discipline` | `services/rewards_data.py` | Phiếu thưởng/phạt |

> **Khi xây dựng backend thật**, thay thế mock data bằng query từ model thật trong cùng thư mục services.

---

## 8. Technology Stack

- **Backend:** Django 6.0 (Python 3.13)
- **Database:** SQLite3
- **Frontend:** Django Templates + Tailwind CSS + Alpine.js
- **Theme:** Pastel Light (card-based layout)
- **CSS/JS:** `accounts/static/accounts/css/style.css`, `accounts/static/accounts/js/accounts.js`

---

## 9. Hướng dẫn chạy project

```bash
cd business_web
python3 manage.py migrate
python3 manage.py runserver
```

Tài khoản test:
- **Admin:** username `admin`, password `admin123`
- **Tạo vai trò:** vào `/admin/` → thêm Role (admin, hr, manager, leader, employee)
- **Switch role nhanh (DEV):** Superuser dùng form switch role trên sidebar

---

## 10. Cách thêm chức năng mới

1. Xác định chức năng thuộc app nào
2. Thêm view vào `app/views/`
3. Thêm URL vào `app/urls.py`
4. Tạo template trong `app/templates/app_name/`
5. Nếu cần logic phức tạp → thêm vào `app/services/`
6. Nếu cần model mới → thêm vào `app/models.py` + chạy `makemigrations` + `migrate`

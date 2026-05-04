"""
==============================================================================
ACCOUNTS URL CONFIG - accounts/urls.py
==============================================================================
Tất cả URL routes cho app accounts.
File này được include từ business_web/urls.py: path('', include('accounts.urls'))

Tổ chức:
  - Public routes: trang chủ, đăng ký, đăng nhập, đăng xuất, dashboard, hồ sơ
  - Management routes: quản lý user, chỉnh work info, gán vai trò, gán quyền, xóa, khóa/mở, reset mật khẩu
==============================================================================
"""

from django.urls import path
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from .views import (
    register_view,
    forgot_password_view,
    logout_view,
    dashboard_view,
    profile_view,               # MỚI: hồ sơ cá nhân
    contract_view,              # MỚI: hợp đồng lao động
    attendance_view,            # MỚI: lịch sử chấm công
    leave_view,                 # MỚI: nghỉ phép cá nhân
    leave_approval_view,        # MỚI: duyệt nghỉ phép
    overtime_view,              # MỚI: tăng ca cá nhân
    overtime_approval_view,     # MỚI: duyệt tăng ca
    statistics_view,            # MỚI: thống kê biểu đồ
    statistics_export_csv_view, # MỚI: xuất CSV statistics
    statistics_print_view,      # MỚI: in / lưu PDF statistics
    report_view,                # MỚI: báo cáo cá nhân
    report_inbox_view,          # MỚI: hộp thư báo cáo
    ticket_list_view,           # MỚI: hỗ trợ khiếu nại (cá nhân)
    ticket_process_view,        # MỚI: xử lý khiếu nại (quản lý)
    rewards_penalties_view,         # MỚI: khen thưởng xử phạt
    rewards_penalties_approval_view,# MỚI: duyệt thưởng phạt
    settings_view,              # MỚI: cài đặt chung
    switch_role_view,           # DEV: đổi vai trò nhanh
    hr_create_profile_view,     # MỚI: HR tạo hồ sơ
    user_list_view,
    edit_work_info_view,
    assign_role_view,
    assign_permissions_view,
    delete_user_view,
    toggle_user_active_view,    # MỚI: khóa/mở khóa tài khoản
    reset_user_password_view,   # MỚI: reset mật khẩu
)

urlpatterns = [
    # ---------- Public routes ----------
    # Trang chủ → redirect về login
    path('', lambda request: redirect('login'), name='home'),

    # Đăng ký tài khoản
    path('register/', register_view, name='register'),

    # Đăng nhập: dùng Django LoginView built-in
    # template_name trỏ tới template login.html đã redesign
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),

    # Quên mật khẩu: UI nhập username và mã xác nhận
    path('forgot-password/', forgot_password_view, name='forgot_password'),

    # Đăng xuất
    path('logout/', logout_view, name='logout'),

    # Dashboard (trang chủ sau đăng nhập)
    path('dashboard/', dashboard_view, name='dashboard'),

    # Hồ sơ cá nhân (MỚI)
    path('profile/', profile_view, name='profile'),

    # Hợp đồng lao động
    path('contract/', contract_view, name='contract'),

    # Chấm công
    path('attendance/', attendance_view, name='attendance'),

    # Nghỉ phép
    path('leave/', leave_view, name='leave'),
    path('leave/approval/', leave_approval_view, name='leave_approval'),

    # Tăng ca
    path('overtime/', overtime_view, name='overtime'),
    path('overtime/approval/', overtime_approval_view, name='overtime_approval'),

    # Thống kê
    path('statistics/', statistics_view, name='statistics'),
    path('statistics/export-csv/', statistics_export_csv_view, name='statistics_export_csv'),
    path('statistics/print/', statistics_print_view, name='statistics_print'),

    # Báo cáo
    path('reports/', report_view, name='reports'),
    path('reports/inbox/', report_inbox_view, name='report_inbox'),

    # Hỗ trợ & Khiếu nại (Tickets)
    path('tickets/', ticket_list_view, name='tickets'),
    path('tickets/process/', ticket_process_view, name='ticket_process'),

    # Khen thưởng & Xử phạt
    path('rewards-penalties/', rewards_penalties_view, name='rewards_penalties'),
    path('rewards-penalties/approval/', rewards_penalties_approval_view, name='rewards_penalties_approval'),

    # Cài đặt
    path('settings/', settings_view, name='settings'),

    # DEV Toggles
    path('switch-role/', switch_role_view, name='switch_role'),

    # HR: Tạo hồ sơ nhân viên
    path('hr/create-profile/', hr_create_profile_view, name='hr_create_profile'),

    # ---------- Admin routes (Admin / superuser only) ----------
    # Tất cả routes bên dưới yêu cầu quyền admin

    # Danh sách tài khoản
    path('users/', user_list_view, name='user_list'),

    # Chỉnh hồ sơ nhân sự đang lưu cho user
    path('users/<int:user_id>/work-info/', edit_work_info_view, name='edit_work_info'),

    # Gán vai trò cho user
    path('users/<int:user_id>/role/', assign_role_view, name='assign_role'),

    # Gán quyền cho user
    path('users/<int:user_id>/permissions/', assign_permissions_view, name='assign_permissions'),

    # Xóa tài khoản
    path('users/<int:user_id>/delete/', delete_user_view, name='delete_user'),

    # Khóa / Mở khóa tài khoản (MỚI)
    path('users/<int:user_id>/toggle-active/', toggle_user_active_view, name='toggle_active'),

    # Reset mật khẩu (MỚI)
    path('users/<int:user_id>/reset-password/', reset_user_password_view, name='reset_user_password'),
]

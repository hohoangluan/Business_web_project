"""
==============================================================================
ACCOUNTS URL CONFIG - accounts/urls.py
==============================================================================
Sau tái cấu trúc, chỉ giữ:
  - Public routes: home, login, register, forgot_password, logout
  - Dashboard
  - Settings, Switch Role
  - Admin: quản lý user, gán role, gán quyền, xóa, khóa/mở, reset

Các chức năng khác đã chuyển sang app riêng (xem root urls.py).
==============================================================================
"""

from django.urls import path
from django.shortcuts import redirect
from .views import (
    AccountsLoginView,
    register_view,
    forgot_password_view,
    logout_view,
    dashboard_view,
    settings_view,
    switch_role_view,
    user_list_view,
    assign_role_view,
    assign_permissions_view,
    delete_user_view,
    toggle_user_active_view,
    reset_user_password_view,
)

urlpatterns = [
    # ---------- Public routes ----------
    path('', lambda request: redirect('login'), name='home'),
    path('register/', register_view, name='register'),
    path('login/', AccountsLoginView.as_view(), name='login'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('logout/', logout_view, name='logout'),

    # ---------- Dashboard ----------
    path('dashboard/', dashboard_view, name='dashboard'),

    # ---------- Settings & DEV ----------
    path('settings/', settings_view, name='settings'),
    path('switch-role/', switch_role_view, name='switch_role'),

    # ---------- Admin: User Management ----------
    path('users/', user_list_view, name='user_list'),
    path('users/<int:user_id>/role/', assign_role_view, name='assign_role'),
    path('users/<int:user_id>/permissions/', assign_permissions_view, name='assign_permissions'),
    path('users/<int:user_id>/delete/', delete_user_view, name='delete_user'),
    path('users/<int:user_id>/toggle-active/', toggle_user_active_view, name='toggle_active'),
    path('users/<int:user_id>/reset-password/', reset_user_password_view, name='reset_user_password'),
]

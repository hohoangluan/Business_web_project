"""
==============================================================================
EMPLOYEE_PROFILES VIEWS
==============================================================================
Views cho hồ sơ nhân viên:
  - profile_view: xem/chỉnh sửa hồ sơ cá nhân
  - hr_create_profile_view: HR tạo hồ sơ nhân viên mới
  - edit_work_info_view: HR/Admin chỉnh hồ sơ đang lưu
==============================================================================
"""

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User

from accounts.models import UserProfile, Role
from accounts.services import (
    ensure_profile, ensure_work_info, ensure_contract_info,
    is_admin_user, is_hr_user, can_manage_work_info,
)
from employee_profiles.forms import EmployeeProfileForm
from employee_profiles.services import (
    get_manager_user_queryset, get_leader_user_queryset,
    build_hr_create_profile_context,
    save_work_info_from_data, save_contract_info_from_data,
)

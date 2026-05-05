"""
==============================================================================
EMPLOYEE_PROFILES SERVICES
==============================================================================
Helpers cho hồ sơ nhân viên: queryset quản lý/leader, context builder...
==============================================================================
"""

from django.contrib.auth.models import User
from django.db.models import Q
from accounts.models import Role
from accounts.services import ensure_work_info, ensure_contract_info


def get_manager_user_queryset():
    """Danh sách user có thể được chọn làm quản lý trực tiếp."""
    return User.objects.select_related('profile__role').filter(
        Q(is_superuser=True) | Q(profile__role__name__in=[Role.ADMIN, Role.MANAGER])
    ).order_by('profile__full_name', 'username')


def get_leader_user_queryset():
    """Danh sách user có thể được chọn làm leader."""
    return User.objects.select_related('profile__role').filter(
        Q(profile__role__name__in=[Role.LEADER, Role.MANAGER])
    ).order_by('profile__full_name', 'username')


def build_hr_create_profile_context(form_data=None):
    """Context chung cho trang tạo hồ sơ (GET/POST dùng chung)."""
    return {
        'active_page': 'hr_profiles',
        'form_data': form_data or {},
        'manager_choices': get_manager_user_queryset(),
        'leader_choices': get_leader_user_queryset(),
    }


def save_work_info_from_data(user, data):
    """Lưu thông tin công việc từ dict data vào EmployeeWorkInfo."""
    work_info = ensure_work_info(user)
    work_info.employee_type = data.get('employee_type', '')
    work_info.department = data.get('department', '')
    work_info.position = data.get('position', '')
    work_info.workplace = data.get('workplace', '')
    work_info.probation_start = data.get('probation_start', '')
    work_info.official_start_date = data.get('official_start_date', '')
    work_info.work_status = data.get('work_status', '')
    work_info.manager_user = data.get('manager_user')
    work_info.leader_user = data.get('leader_user')
    work_info.save()
    return work_info


def save_contract_info_from_data(user, data):
    """Lưu thông tin hợp đồng từ dict data vào ContractInfo."""
    contract_info = ensure_contract_info(user)
    contract_info.contract_number = data.get('contract_number', '')
    contract_info.contract_type = data.get('contract_type', '')
    contract_info.contract_signed_date = data.get('contract_signed_date', '')
    contract_info.contract_start_date = data.get('contract_start_date', '')
    contract_info.contract_end_date = data.get('contract_end_date', '')
    contract_info.contract_annual_leave_days = data.get('contract_annual_leave_days')
    contract_info.contract_standard_shift = data.get('contract_standard_shift', '')
    contract_info.contract_attachment_reference = data.get('contract_attachment_reference', '')
    contract_info.save()
    return contract_info

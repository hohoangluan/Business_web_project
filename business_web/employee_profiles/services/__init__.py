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
from accounts.services import (
    ensure_work_info, ensure_contract_info,
    ensure_personal_info, ensure_emergency_contact, ensure_education_info
)
from employee_profiles.forms import (
    DEPARTMENT_CHOICES, EMPLOYEE_TYPE_CHOICES, GENDER_CHOICES, configured_company_choices,
    MARITAL_STATUS_CHOICES, NATIONALITY_CHOICES, POSITION_CHOICES, WORKPLACE_CHOICES,
)


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
    data = form_data or {}
    contract_type_fallback = [
        ('', '-- Chọn loại hợp đồng --'),
        ('Thử việc', 'Thử việc'),
        ('Xác định thời hạn', 'Xác định thời hạn'),
        ('Không xác định thời hạn', 'Không xác định thời hạn'),
        ('Thời vụ', 'Thời vụ'),
    ]
    return {
        'active_page': 'hr_profiles',
        'form_data': data,
        'manager_choices': get_manager_user_queryset(),
        'leader_choices': get_leader_user_queryset(),
        'department_choices': configured_company_choices(
            'departments', DEPARTMENT_CHOICES, '-- Chọn phòng ban --', data.get('department')
        ),
        'position_choices': configured_company_choices(
            'positions', POSITION_CHOICES, '-- Chọn chức vụ --', data.get('position')
        ),
        'employee_type_choices': EMPLOYEE_TYPE_CHOICES,
        'workplace_choices': configured_company_choices(
            'workplaces', WORKPLACE_CHOICES, '-- Chọn nơi làm việc --', data.get('workplace')
        ),
        'contract_type_choices': configured_company_choices(
            'contract_types', contract_type_fallback, '-- Chọn loại hợp đồng --', data.get('contract_type')
        ),
        'gender_choices': GENDER_CHOICES,
        'marital_status_choices': MARITAL_STATUS_CHOICES,
        'nationality_choices': NATIONALITY_CHOICES,
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
    contract_info.shift_start_time = data.get('shift_start_time') or None
    contract_info.shift_end_time = data.get('shift_end_time') or None
    contract_info.save()
    return contract_info

def save_personal_info_from_data(user, data):
    """Lưu thông tin cá nhân mở rộng từ dict data vào PersonalInfo."""
    personal_info = ensure_personal_info(user)
    personal_info.gender = data.get('gender', '')
    personal_info.marital_status = data.get('marital_status', '')
    personal_info.nationality = data.get('nationality', '')
    personal_info.id_card_number = data.get('id_card_number', '')
    personal_info.id_card_issue_place = data.get('id_card_issue_place', '')
    personal_info.id_card_issue_date = data.get('id_card_issue_date', '')
    personal_info.permanent_address = data.get('permanent_address', '')
    personal_info.temporary_address = data.get('temporary_address', '')
    personal_info.save()
    return personal_info

def save_emergency_contact_from_data(user, data):
    """Lưu thông tin người liên hệ khẩn cấp từ dict data vào EmergencyContact."""
    contact = ensure_emergency_contact(user)
    contact.contact_name = data.get('contact_name', '')
    contact.contact_phone = data.get('contact_phone', '')
    contact.relation = data.get('relation', '')
    contact.contact_address = data.get('contact_address', '')
    contact.save()
    return contact

def save_education_info_from_data(user, data):
    """Lưu thông tin học vấn từ dict data vào EducationAndSkills."""
    edu = ensure_education_info(user)
    edu.education_level = data.get('education_level', '')
    edu.degree = data.get('degree', '')
    edu.major = data.get('major', '')
    edu.certificates = data.get('certificates', '')
    edu.foreign_languages = data.get('foreign_languages', '')
    edu.professional_skills = data.get('professional_skills', '')
    edu.save()
    return edu

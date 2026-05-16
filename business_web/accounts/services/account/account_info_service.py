"""Account profile helpers shared across apps."""

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from accounts.models import UserProfile

def ensure_profile(user):
    """
    Đảm bảo user có UserProfile.
    Nếu chưa có (VD: user tạo trước khi có profile system), tự động tạo.
    """
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


def ensure_work_info(user):
    """
    Đảm bảo user có EmployeeWorkInfo.
    Import tại đây để tránh circular import.
    """
    from employee_profiles.models import EmployeeWorkInfo
    work_info, created = EmployeeWorkInfo.objects.get_or_create(user=user)
    return work_info


def ensure_contract_info(user):
    """
    Đảm bảo user có ContractInfo.
    Import tại đây để tránh circular import.
    """
    from contracts.models import ContractInfo
    contract_info, _ = ContractInfo.objects.get_or_create(user=user)
    return contract_info


def ensure_personal_info(user):
    """
    Đảm bảo user có PersonalInfo.
    Import tại đây để tránh circular import.
    """
    from employee_profiles.models import PersonalInfo
    personal_info, created = PersonalInfo.objects.get_or_create(user=user)
    return personal_info


def ensure_emergency_contact(user):
    """Đảm bảo user có EmergencyContact."""
    from employee_profiles.models import EmergencyContact
    contact, created = EmergencyContact.objects.get_or_create(user=user)
    return contact


def ensure_education_info(user):
    """Đảm bảo user có EducationAndSkills."""
    from employee_profiles.models import EducationAndSkills
    education, created = EducationAndSkills.objects.get_or_create(user=user)
    return education


def ensure_account_profiles(user, employee_id="", full_name="", email=""):
    """
    Ensure all base profiles exist for a new account.
    """
    profile = ensure_profile(user)
    if employee_id:
        profile.employee_id = employee_id
    if full_name:
        profile.full_name = full_name
    if email:
        profile.email = email
    profile.save()

    ensure_personal_info(user)
    ensure_work_info(user)
    ensure_contract_info(user)  
    ensure_emergency_contact(user)
    ensure_education_info(user)


def get_user_display_name(user):
    """Prefer the UserProfile full name, then fall back to username."""

    profile = ensure_profile(user)
    return profile.full_name or user.username


def get_department_label(user):
    """Return the user's department label."""

    work_info = ensure_work_info(user)
    return work_info.department or "Chua phan phong ban"


def get_manager_display_name(user):
    """Return the user's manager display name."""

    work_info = ensure_work_info(user)
    manager_user = work_info.manager_user
    if not manager_user:
        return "Chua gan quan ly"
    return get_user_display_name(manager_user)


def get_leader_display_name(user):
    """Return the user's leader display name."""

    work_info = ensure_work_info(user)
    leader_user = work_info.leader_user
    if not leader_user:
        return "Chua gan leader"
    return get_user_display_name(leader_user)

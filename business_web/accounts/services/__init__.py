"""Shared accounts service exports.

Other apps should keep importing helpers from ``accounts.services``.
"""

from accounts.services.account import (
    DEFAULT_RESET_PASSWORD,
    ensure_account_profiles,
    ensure_contract_info,
    ensure_personal_info,
    ensure_emergency_contact,
    ensure_education_info,
    ensure_profile,
    ensure_work_info,
    get_department_label,
    get_leader_display_name,
    get_manager_display_name,
    get_user_display_name,
)
from accounts.services.auth import (
    create_automatic_account,
    create_manual_account,
    mask_email,
    normalize_employee_username,
)
from accounts.services.permission import (
    can_access_evaluations,
    can_access_statistics,
    can_manage_requests,
    can_manage_work_info,
    can_submit_evaluation_demo,
    get_user_role_name,
    has_admin_business_access,
    has_custom_permission,
    is_admin_user,
    is_hr_user,
    user_has_role,
)

__all__ = [
    "DEFAULT_RESET_PASSWORD",
    "can_access_evaluations",
    "can_access_statistics",
    "can_manage_requests",
    "can_manage_work_info",
    "can_submit_evaluation_demo",
    "create_automatic_account",
    "create_manual_account",
    "ensure_account_profiles",
    "ensure_contract_info",
    "ensure_personal_info",
    "ensure_emergency_contact",
    "ensure_education_info",
    "ensure_profile",
    "ensure_work_info",
    "get_department_label",
    "get_leader_display_name",
    "get_manager_display_name",
    "get_user_display_name",
    "get_user_role_name",
    "has_admin_business_access",
    "has_custom_permission",
    "is_admin_user",
    "is_hr_user",
    "mask_email",
    "normalize_employee_username",
    "user_has_role",
]

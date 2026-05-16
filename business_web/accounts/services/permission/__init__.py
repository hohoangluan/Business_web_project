"""Permission service exports."""

from accounts.services.permission.access_control_service import (
    can_access_evaluations,
    can_access_statistics,
    can_manage_requests,
    can_manage_work_info,
    can_submit_evaluation_demo,
    has_admin_business_access,
)
from accounts.services.permission.permission_service import has_custom_permission
from accounts.services.permission.role_service import (
    get_user_role_name,
    is_admin_user,
    is_hr_user,
    user_has_role,
)

__all__ = [
    "can_access_evaluations",
    "can_access_statistics",
    "can_manage_requests",
    "can_manage_work_info",
    "can_submit_evaluation_demo",
    "get_user_role_name",
    "has_admin_business_access",
    "has_custom_permission",
    "is_admin_user",
    "is_hr_user",
    "user_has_role",
]

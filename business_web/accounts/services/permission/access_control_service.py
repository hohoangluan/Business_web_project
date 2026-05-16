"""Access-control helper services."""

from accounts.models import Role
from accounts.services.permission.role_service import get_user_role_name, user_has_role


def has_admin_business_access(user):
    """Return whether the user has admin-level business access."""

    role_name = get_user_role_name(user)
    return role_name == Role.ADMIN or (
        user.is_authenticated and user.is_superuser and not role_name
    )


def can_manage_requests(user):
    """Return whether the user can approve requests."""

    return has_admin_business_access(user) or user_has_role(
        user, Role.HR, Role.MANAGER, Role.LEADER
    )


def can_manage_work_info(user):
    """Return whether the user can manage employee work info."""

    return has_admin_business_access(user) or user_has_role(user, Role.HR)


def can_access_statistics(user):
    """Return whether the user can access statistics pages."""

    return has_admin_business_access(user) or user_has_role(
        user, Role.HR, Role.MANAGER, Role.LEADER
    )


def can_access_evaluations(user):
    """Return whether the user can access evaluation actions."""

    return user_has_role(user, Role.MANAGER, Role.LEADER)


def can_submit_evaluation_demo(user):
    """Return whether the user can submit demo evaluations."""

    return can_access_evaluations(user)

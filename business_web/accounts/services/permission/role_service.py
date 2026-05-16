"""Role helper services."""

from accounts.models import Role, UserProfile


def get_user_role_name(user):
    """Return the normalized role name for a user."""

    if not user.is_authenticated:
        return ""
    try:
        role = user.profile.role
    except UserProfile.DoesNotExist:
        return ""
    return role.name.lower() if role and role.name else ""


def user_has_role(user, *role_names):
    """Return whether the user has any of the provided role names."""

    normalized_roles = {role.lower() for role in role_names}
    return get_user_role_name(user) in normalized_roles


def is_admin_user(user):
    """Predicate for admin-only views."""

    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return get_user_role_name(user) == Role.ADMIN


def is_hr_user(user):
    """Predicate for HR-only views."""

    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user_has_role(user, Role.HR)

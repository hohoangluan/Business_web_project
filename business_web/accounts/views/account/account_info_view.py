"""Account information and dashboard views."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import Role
from accounts.services import (
    can_access_evaluations,
    can_access_statistics,
    can_manage_work_info,
    ensure_profile,
    is_admin_user,
    user_has_role,
)


@login_required
def account_info_view(request):
    """Placeholder page for future account information UI."""

    ensure_profile(request.user)
    return render(
        request,
        "accounts/account/account_info.html",
        {"active_page": "account_info"},
    )


@login_required
def dashboard_view(request):
    """Show the role-aware dashboard."""

    ensure_profile(request.user)
    return render(
        request,
        "accounts/management/dashboard.html",
        {
            "active_page": "dashboard",
            "can_access_statistics": can_access_statistics(request.user),
            "can_access_evaluations": can_access_evaluations(request.user),
            "can_manage_work_info": can_manage_work_info(request.user),
            "is_system_admin": is_admin_user(request.user),
        },
    )


@login_required
def settings_view(request):
    """Show general account settings."""

    ensure_profile(request.user)
    return render(
        request,
        "accounts/account/settings.html",
        {
            "active_page": "settings",
            "is_admin": user_has_role(request.user, Role.ADMIN),
            "is_hr": user_has_role(request.user, Role.HR),
        },
    )

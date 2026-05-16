"""Account status actions for user management."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from accounts.services import DEFAULT_RESET_PASSWORD, is_admin_user


@login_required
@user_passes_test(is_admin_user)
def toggle_user_active_view(request, user_id):
    """Lock or unlock a user account."""

    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        messages.error(request, "Ban khong the khoa tai khoan cua chinh minh.")
        return redirect("user_list")

    if request.method == "POST":
        target_user.is_active = not target_user.is_active
        target_user.save()
        if target_user.is_active:
            messages.success(request, f"Da mo khoa tai khoan '{target_user.username}'.")
        else:
            messages.warning(request, f"Da khoa tai khoan '{target_user.username}'.")

    return redirect("user_list")


@login_required
@user_passes_test(is_admin_user)
def reset_user_password_view(request, user_id):
    """Reset a user's password to the project default."""

    target_user = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        target_user.set_password(DEFAULT_RESET_PASSWORD)
        target_user.save()
        messages.success(
            request,
            f"Mat khau cua '{target_user.username}' da duoc reset thanh: {DEFAULT_RESET_PASSWORD}",
        )

    return redirect("user_list")


@login_required
@user_passes_test(is_admin_user)
def account_status_view(request):
    """Placeholder page for future account status workflows."""

    return render(request, "accounts/management/account_status.html")

"""Account update and management views."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import AssignPermissionsForm
from accounts.models import Role
from accounts.services import (
    can_manage_work_info,
    create_notification,
    ensure_profile,
    is_admin_user,
)


@login_required
def account_update_view(request):
    """Placeholder page for future account update UI."""

    ensure_profile(request.user)
    return render(
        request,
        "accounts/account/account_update.html",
        {"active_page": "account_update"},
    )


@login_required
@require_POST
def switch_role_view(request):
    """Development-only helper for superusers to switch roles quickly."""

    if not request.user.is_superuser:
        messages.error(request, "Tinh nang nay chi danh cho Superuser.")
        return redirect("dashboard")

    role_name = request.POST.get("role_name")
    ensure_profile(request.user)

    if role_name:
        role, _ = Role.objects.get_or_create(name=role_name)
        request.user.profile.role = role
        request.user.profile.save()
        messages.success(request, f"[DEV] Da mo phong vai tro: {role.get_name_display()}")
    else:
        request.user.profile.role = None
        request.user.profile.save()
        messages.success(request, "[DEV] Da go Role.")

    return redirect(request.META.get("HTTP_REFERER", "dashboard"))


@login_required
@user_passes_test(is_admin_user)
def admin_create_account_view(request):
    """Admin tạo tài khoản nhanh — chỉ username + password.

    Khác giao diện HR "Tạo hồ sơ nhân sự" (form hồ sơ đầy đủ). Admin giữ phiên
    đăng nhập (không tự đăng nhập vào tài khoản mới). Vai trò gán sau ở Quản lý tài khoản.
    """

    template = "accounts/management/admin_create_account.html"

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        errors = []
        if not username:
            errors.append("Tên đăng nhập không được để trống.")
        elif User.objects.filter(username__iexact=username).exists():
            errors.append(f'Tên đăng nhập "{username}" đã tồn tại.')
        if not password:
            errors.append("Mật khẩu không được để trống.")
        elif password != password_confirm:
            errors.append("Mật khẩu xác nhận không khớp.")
        else:
            try:
                validate_password(password)
            except ValidationError as exc:
                errors.extend(exc.messages)

        if errors:
            for message in errors:
                messages.error(request, message)
            return render(request, template, {"active_page": "register", "username": username})

        user = User.objects.create_user(username=username, password=password)
        ensure_profile(user)
        messages.success(request, f'Đã tạo tài khoản "{username}" thành công.')
        return redirect("user_list")

    return render(request, template, {"active_page": "register"})


@login_required
@user_passes_test(can_manage_work_info)
def user_list_view(request):
    """Show all users for HR/Admin management."""

    users = (
        User.objects.all()
        .select_related("profile__role")
        .prefetch_related("profile__permissions")
        .order_by("-date_joined")
    )

    for user in users:
        ensure_profile(user)

    return render(
        request,
        "accounts/management/user_management.html",
        {
            "users": users,
            "active_page": "users",
            "can_manage_system_users": is_admin_user(request.user),
            "can_manage_work_info": can_manage_work_info(request.user),
        },
    )


@login_required
@user_passes_test(is_admin_user)
def assign_permissions_view(request, user_id):
    """Assign custom permissions for a user."""

    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)

    if request.method == "POST":
        form = AssignPermissionsForm(request.POST)
        if form.is_valid():
            profile.permissions.set(form.cleaned_data["permissions"])
            messages.success(request, f"Quyen cua '{target_user.username}' da duoc cap nhat.")
            return redirect("user_list")
    else:
        form = AssignPermissionsForm(initial={"permissions": profile.permissions.all()})

    return render(
        request,
        "accounts/permission/assign_permissions.html",
        {
            "form": form,
            "target_user": target_user,
            "active_page": "users",
        },
    )


@login_required
@user_passes_test(is_admin_user)
def delete_user_view(request, user_id):
    """Delete a user account."""

    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        messages.error(request, "Ban khong the xoa tai khoan cua chinh minh.")
        return redirect("user_list")

    if request.method == "POST":
        username = target_user.username
        target_user.delete()
        messages.success(request, f"Tai khoan '{username}' da duoc xoa.")
        return redirect("user_list")

    return render(
        request,
        "accounts/management/delete_user.html",
        {
            "target_user": target_user,
            "active_page": "users",
        },
    )

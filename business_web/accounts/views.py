"""
==============================================================================
ACCOUNTS VIEWS - accounts/views.py
==============================================================================
Sau khi tái cấu trúc, app accounts chỉ giữ:
  - Đăng ký, đăng nhập, đăng xuất, quên mật khẩu
  - Dashboard
  - Quản lý user (Admin): danh sách, gán role, gán quyền, xóa, khóa/mở, reset
  - Cài đặt chung
  - Switch Role (DEV tool)

Các chức năng khác đã chuyển sang app riêng:
  - Hồ sơ nhân viên → employee_profiles
  - Hợp đồng → contracts
  - Chấm công → attendance
  - Nghỉ phép → leaves
  - Tăng ca → overtime
  - Đánh giá → performance
  - Khen thưởng/Xử phạt → rewards_discipline
  - Báo cáo & Ticket → reports_interactions
  - Thống kê → statistics
==============================================================================
"""

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User

from .forms import RegisterForm, AssignRoleForm, AssignPermissionsForm
from .models import UserProfile, Role
from accounts.services import (
    ensure_profile,
    ensure_work_info,
    ensure_contract_info,
    is_admin_user,
    is_hr_user,
    can_manage_work_info,
    can_access_statistics,
    can_access_evaluations,
    get_user_role_name,
    user_has_role,
    mask_email,
)


# =============================================================================
# PUBLIC VIEWS: Registration, Login, Logout, Dashboard
# =============================================================================

def register_view(request):
    """
    Đăng ký tài khoản với 7 trường.
    - GET: hiển thị form đăng ký
    - POST: validate, tạo user + profile, tự động đăng nhập
    Template: accounts/register.html
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = ensure_profile(user)
            profile.full_name = form.cleaned_data['full_name']
            profile.phone_number = form.cleaned_data['phone_number']
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.employee_id = form.cleaned_data['employee_id']
            profile.save()

            # Tạo work_info và contract_info rỗng cho user mới
            ensure_work_info(user)
            ensure_contract_info(user)

            login(request, user)
            messages.success(request, 'Đăng ký tài khoản thành công! Chào mừng bạn.')
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def forgot_password_view(request):
    """
    UI quên mật khẩu 2 bước.
    Hiện chỉ dựng UI/flow, chưa gửi email thật.
    Template: accounts/forgot_password.html
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    context = {
        'step': 'username',
        'username': '',
        'masked_email': '',
    }

    if request.method == 'POST':
        step = request.POST.get('step', 'username')
        username = request.POST.get('username', '').strip()
        context['username'] = username

        if step == 'username':
            user = User.objects.filter(username=username).first() if username else None
            if not username:
                context['error_message'] = 'Vui lòng nhập username để nhận mã xác nhận.'
            elif not user:
                context['error_message'] = 'Không tìm thấy tài khoản với username này.'
            elif not user.email:
                context['error_message'] = 'Tài khoản này chưa có email trong hồ sơ.'
            else:
                context.update({
                    'step': 'code',
                    'masked_email': mask_email(user.email),
                    'success_message': 'Mã xác nhận sẽ được gửi đến Gmail trong hồ sơ tài khoản.',
                })

        elif step == 'code':
            verification_code = request.POST.get('verification_code', '').strip()
            user = User.objects.filter(username=username).first() if username else None
            context.update({
                'step': 'code',
                'masked_email': mask_email(user.email) if user and user.email else '',
                'verification_code': verification_code,
            })
            if not verification_code:
                context['error_message'] = 'Vui lòng nhập mã xác nhận.'
            elif len(verification_code) != 6:
                context['error_message'] = 'Mã xác nhận gồm 6 ký tự.'
            else:
                context['success_message'] = 'Giao diện xác nhận mã đã sẵn sàng.'

    return render(request, 'accounts/forgot_password.html', context)


@login_required
def dashboard_view(request):
    """
    Trang chủ sau đăng nhập. Hiển thị thông tin tổng quan theo vai trò.
    Template: accounts/dashboard.html
    """
    ensure_profile(request.user)
    return render(request, 'accounts/dashboard.html', {
        'active_page': 'dashboard',
        'can_access_statistics': can_access_statistics(request.user),
        'can_access_evaluations': can_access_evaluations(request.user),
        'can_manage_work_info': can_manage_work_info(request.user),
        'is_system_admin': is_admin_user(request.user),
    })


def logout_view(request):
    """Đăng xuất và redirect về trang đăng nhập."""
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('login')


# =============================================================================
# SETTINGS & DEV TOOLS
# =============================================================================

@login_required
def settings_view(request):
    """
    Trang Cài đặt chung.
    Template: accounts/settings.html
    """
    ensure_profile(request.user)
    return render(request, 'accounts/settings.html', {
        'active_page': 'settings',
        'is_admin': user_has_role(request.user, Role.ADMIN),
        'is_hr': user_has_role(request.user, Role.HR),
    })


@login_required
@require_POST
def switch_role_view(request):
    """DEV TOOL: Superuser chuyển đổi vai trò nhanh để test giao diện."""
    if not request.user.is_superuser:
        messages.error(request, 'Tính năng này chỉ dành cho Superuser.')
        return redirect('dashboard')

    role_name = request.POST.get('role_name')
    ensure_profile(request.user)

    if role_name:
        role, created = Role.objects.get_or_create(name=role_name)
        request.user.profile.role = role
        request.user.profile.save()
        messages.success(request, f'[DEV] Đã mô phỏng vai trò: {role.get_name_display()}')
    else:
        request.user.profile.role = None
        request.user.profile.save()
        messages.success(request, '[DEV] Đã gỡ Role.')

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# =============================================================================
# ADMIN VIEWS: User Management
# =============================================================================

@login_required
@user_passes_test(can_manage_work_info)
def user_list_view(request):
    """
    Danh sách tất cả hồ sơ nhân sự.
    HR/Admin xem. Thao tác nhạy cảm chỉ Admin.
    Template: accounts/user_management.html
    """
    users = User.objects.all().select_related('profile__role').prefetch_related(
        'profile__permissions'
    ).order_by('-date_joined')

    for user in users:
        ensure_profile(user)

    return render(request, 'accounts/user_management.html', {
        'users': users,
        'active_page': 'users',
        'can_manage_system_users': is_admin_user(request.user),
        'can_manage_work_info': can_manage_work_info(request.user),
    })


@login_required
@user_passes_test(is_admin_user)
def assign_role_view(request, user_id):
    """Gán vai trò cho user. Template: accounts/assign_role.html"""
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)

    if request.method == 'POST':
        form = AssignRoleForm(request.POST)
        if form.is_valid():
            profile.role = form.cleaned_data['role']
            profile.save()
            messages.success(
                request,
                f"Vai trò của '{target_user.username}' đã được cập nhật thành "
                f"'{profile.role}' thành công."
                if profile.role else
                f"Đã gỡ vai trò khỏi '{target_user.username}'."
            )
            return redirect('user_list')
    else:
        form = AssignRoleForm(initial={'role': profile.role})

    return render(request, 'accounts/assign_role.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
    })


@login_required
@user_passes_test(is_admin_user)
def assign_permissions_view(request, user_id):
    """Gán quyền cho user. Template: accounts/assign_permissions.html"""
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)

    if request.method == 'POST':
        form = AssignPermissionsForm(request.POST)
        if form.is_valid():
            profile.permissions.set(form.cleaned_data['permissions'])
            messages.success(request, f"Quyền của '{target_user.username}' đã được cập nhật.")
            return redirect('user_list')
    else:
        form = AssignPermissionsForm(initial={'permissions': profile.permissions.all()})

    return render(request, 'accounts/assign_permissions.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
    })


@login_required
@user_passes_test(is_admin_user)
def delete_user_view(request, user_id):
    """Xóa tài khoản. Template: accounts/delete_user.html"""
    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        messages.error(request, "Bạn không thể xóa tài khoản của chính mình.")
        return redirect('user_list')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f"Tài khoản '{username}' đã được xóa.")
        return redirect('user_list')

    return render(request, 'accounts/delete_user.html', {
        'target_user': target_user,
        'active_page': 'users',
    })


@login_required
@user_passes_test(is_admin_user)
def toggle_user_active_view(request, user_id):
    """Khóa/mở khóa tài khoản."""
    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        messages.error(request, "Bạn không thể khóa tài khoản của chính mình.")
        return redirect('user_list')

    if request.method == 'POST':
        target_user.is_active = not target_user.is_active
        target_user.save()
        if target_user.is_active:
            messages.success(request, f"Đã mở khóa tài khoản '{target_user.username}'.")
        else:
            messages.warning(request, f"Đã khóa tài khoản '{target_user.username}'.")

    return redirect('user_list')


@login_required
@user_passes_test(is_admin_user)
def reset_user_password_view(request, user_id):
    """Reset mật khẩu cho user."""
    target_user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        default_password = "Password@123"
        target_user.set_password(default_password)
        target_user.save()
        messages.success(
            request,
            f"Mật khẩu của '{target_user.username}' đã được reset thành: {default_password}"
        )

    return redirect('user_list')

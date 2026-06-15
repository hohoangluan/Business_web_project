"""Account information and dashboard views."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import Role
from accounts.services import (
    can_access_evaluations,
    can_access_statistics,
    can_manage_work_info,
    ensure_profile,
    is_admin_user,
    is_hr_user,
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
    """Show general account settings + HR work-schedule config (panel tab-hr)."""

    ensure_profile(request.user)

    from attendance.forms import WorkScheduleConfigForm
    from attendance.models import WorkScheduleConfig

    config = WorkScheduleConfig.get_solo()
    schedule_form = WorkScheduleConfigForm(instance=config)

    if (request.method == "POST"
            and request.POST.get("form_section") == "work_schedule"):
        # Chỉ HR được đổi giờ làm chuẩn của toàn công ty (Admin không xử lý nhân sự).
        if is_hr_user(request.user):
            schedule_form = WorkScheduleConfigForm(request.POST, instance=config)
            if schedule_form.is_valid():
                schedule_form.save()
                messages.success(request, "Đã cập nhật giờ làm việc chuẩn.")
            # invalid → schedule_form mang lỗi, render lại panel kèm thông báo.
        else:
            messages.error(request, "Bạn không có quyền thay đổi giờ làm việc.")

    return render(
        request,
        "accounts/account/settings.html",
        {
            "active_page": "settings",
            "is_admin": user_has_role(request.user, Role.ADMIN),
            "is_hr": user_has_role(request.user, Role.HR),
            "has_face": hasattr(request.user, 'employee_face'),
            "latest_face_request": request.user.face_change_requests.order_by('-created_at').first(),
            "schedule_form": schedule_form,
        },
    )

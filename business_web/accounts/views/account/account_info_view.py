"""Account information and dashboard views."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.forms import CompanyConfigurationForm
from accounts.models import CompanyConfiguration, Role
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
    """Show general settings with Admin company config and HR schedule config."""

    ensure_profile(request.user)

    from attendance.forms import WorkScheduleConfigForm
    from attendance.models import WorkScheduleConfig

    config = WorkScheduleConfig.get_solo()
    schedule_form = WorkScheduleConfigForm(instance=config)
    company_config = CompanyConfiguration.get_solo()
    company_form = CompanyConfigurationForm(instance=company_config)

    if request.method == "POST":
        form_section = request.POST.get("form_section")
        if form_section == "work_schedule":
            # Chỉ HR được đổi giờ làm chuẩn của toàn công ty (Admin không xử lý nhân sự).
            if is_hr_user(request.user):
                schedule_form = WorkScheduleConfigForm(request.POST, instance=config)
                if schedule_form.is_valid():
                    schedule_form.save()
                    messages.success(request, "Đã cập nhật giờ làm việc chuẩn.")
            else:
                messages.error(request, "Bạn không có quyền thay đổi giờ làm việc.")
        elif form_section == "company_configuration":
            if is_admin_user(request.user):
                company_form = CompanyConfigurationForm(request.POST, instance=company_config)
                if company_form.is_valid():
                    company_form.save()
                    messages.success(request, "Đã cập nhật cấu hình công ty.")
            else:
                messages.error(request, "Chỉ Admin mới được thay đổi cấu hình công ty.")

    return render(
        request,
        "accounts/account/settings.html",
        {
            "active_page": "settings",
            "is_admin": is_admin_user(request.user),
            "is_hr": user_has_role(request.user, Role.HR),
            "has_face": hasattr(request.user, 'employee_face'),
            "latest_face_request": request.user.face_change_requests.order_by('-created_at').first(),
            "schedule_form": schedule_form,
            "company_form": company_form,
        },
    )

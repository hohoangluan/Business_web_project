"""Reusable view decorators for access control."""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from accounts.services import is_admin_user


def deny_admin(view_func):
    """Chặn tài khoản Admin truy cập chức năng nghiệp vụ (chỉ quản lý hệ thống).

    Admin bị chuyển hướng về dashboard kèm thông báo. Áp cho các view nghiệp vụ
    (hồ sơ, hợp đồng, chấm công, nghỉ phép, tăng ca, báo cáo, khen thưởng...).
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if is_admin_user(request.user):
            messages.error(
                request,
                'Tài khoản Admin chỉ quản lý hệ thống, không sử dụng chức năng này.',
            )
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)

    return _wrapped

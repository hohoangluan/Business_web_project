"""Views cho tăng ca."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.services import ensure_profile, can_manage_requests


@login_required
def overtime_view(request):
    """Trang tăng ca cá nhân. MOCK DATA. Template: overtime/overtime.html"""
    ensure_profile(request.user)
    return render(request, 'overtime/overtime.html', {
        'active_page': 'overtime',
        'can_approve': can_manage_requests(request.user),
    })


@login_required
def overtime_approval_view(request):
    """Trang phê duyệt tăng ca. MOCK DATA. Template: overtime/overtime_approval.html"""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('overtime')
    return render(request, 'overtime/overtime_approval.html', {
        'active_page': 'overtime',
    })

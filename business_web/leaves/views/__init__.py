"""Views cho nghỉ phép."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.services import ensure_profile, can_manage_requests


@login_required
def leave_view(request):
    """Trang nghỉ phép cá nhân. MOCK DATA. Template: leaves/leave.html"""
    ensure_profile(request.user)
    return render(request, 'leaves/leave.html', {
        'active_page': 'leave',
        'can_approve': can_manage_requests(request.user),
    })


@login_required
def leave_approval_view(request):
    """Trang phê duyệt nghỉ phép. MOCK DATA. Template: leaves/leave_approval.html"""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('leave')
    return render(request, 'leaves/leave_approval.html', {
        'active_page': 'leave',
    })

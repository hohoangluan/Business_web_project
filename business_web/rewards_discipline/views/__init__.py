"""Views cho khen thưởng & xử phạt."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.services import ensure_profile, can_manage_requests


@login_required
def rewards_penalties_view(request):
    """Trang khen thưởng & xử phạt. MOCK DATA. Template: rewards_discipline/rewards_penalties.html"""
    ensure_profile(request.user)
    return render(request, 'rewards_discipline/rewards_penalties.html', {
        'active_page': 'rewards',
        'can_approve': can_manage_requests(request.user),
    })


@login_required
def rewards_penalties_approval_view(request):
    """Trang phê duyệt thưởng/phạt. MOCK DATA. Template: rewards_discipline/rewards_penalties_approval.html"""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('rewards_penalties')
    return render(request, 'rewards_discipline/rewards_penalties_approval.html', {
        'active_page': 'rewards',
    })

"""HR review trang điều chỉnh chấm công."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.services.permission.role_service import is_hr_user
from attendance.services.record.adjustment_review_service import (
    approve_adjustment, get_pending_adjustments, get_reviewed_adjustments,
    reject_adjustment,
)


@login_required
def adjustment_review_view(request):
    if not is_hr_user(request.user):
        messages.error(request, 'Bạn không có quyền duyệt điều chỉnh chấm công.')
        return redirect('attendance')
    return render(request, 'attendance/adjustment/adjustment_review.html', {
        'active_page': 'attendance',
        'pending': get_pending_adjustments(),
        'reviewed': get_reviewed_adjustments(),
    })


@login_required
@require_POST
def adjustment_approve_action(request, adj_id):
    if not is_hr_user(request.user):
        messages.error(request, 'Không có quyền.')
        return redirect('attendance')
    ok, msg = approve_adjustment(request.user, adj_id, request.POST.get('hr_note', ''))
    (messages.success if ok else messages.error)(request, msg)
    return redirect('attendance_adjustment_review')


@login_required
@require_POST
def adjustment_reject_action(request, adj_id):
    if not is_hr_user(request.user):
        messages.error(request, 'Không có quyền.')
        return redirect('attendance')
    ok, msg = reject_adjustment(request.user, adj_id, request.POST.get('hr_note', ''))
    (messages.success if ok else messages.error)(request, msg)
    return redirect('attendance_adjustment_review')

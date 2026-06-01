"""HR review trang duyệt cập nhật khuôn mặt."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.services.permission.role_service import is_hr_user
from attendance.services.face.face_change_service import (
    approve_face_change,
    get_pending_face_changes,
    get_reviewed_face_changes,
    reject_face_change,
)


@login_required
def face_change_review_view(request):
    if not is_hr_user(request.user):
        messages.error(request, 'Bạn không có quyền duyệt cập nhật khuôn mặt.')
        return redirect('attendance')
    return render(request, 'attendance/face/face_change_review.html', {
        'active_page': 'face_change_review',
        'pending': get_pending_face_changes(),
        'reviewed': get_reviewed_face_changes(),
    })


@login_required
@require_POST
def face_change_approve_action(request, req_id):
    if not is_hr_user(request.user):
        messages.error(request, 'Không có quyền.')
        return redirect('attendance')
    ok, msg = approve_face_change(request.user, req_id, request.POST.get('hr_note', ''))
    (messages.success if ok else messages.error)(request, msg)
    return redirect('face_change_review')


@login_required
@require_POST
def face_change_reject_action(request, req_id):
    if not is_hr_user(request.user):
        messages.error(request, 'Không có quyền.')
        return redirect('attendance')
    ok, msg = reject_face_change(request.user, req_id, request.POST.get('hr_note', ''))
    (messages.success if ok else messages.error)(request, msg)
    return redirect('face_change_review')

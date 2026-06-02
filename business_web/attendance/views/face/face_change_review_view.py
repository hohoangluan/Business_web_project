"""HR review trang duyệt cập nhật khuôn mặt."""
import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.services import is_admin_user, is_hr_user
from attendance.models import FaceChangeRequest
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


@login_required
def face_change_image_view(request, req_id):
    """Stream ảnh phiếu đổi mặt — chỉ chủ mặt hoặc HR/Admin. Không phơi URL Cloudinary."""
    try:
        req = FaceChangeRequest.objects.get(id=req_id)
    except FaceChangeRequest.DoesNotExist:
        raise Http404
    allowed = (
        request.user == req.user
        or is_hr_user(request.user)
        or is_admin_user(request.user)
    )
    if not allowed or not req.image:
        raise Http404
    ctype = mimetypes.guess_type(req.image.name)[0] or 'image/jpeg'
    return FileResponse(req.image.open('rb'), content_type=ctype)

"""Views cho nghỉ phép — đăng ký, hủy, phê duyệt 2 bước, từ chối."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from accounts.services import ensure_profile, can_manage_requests
from leaves.forms import LeaveRequestForm
from leaves.services import (
    approve_leave_request,
    bulk_approve_requests,
    cancel_leave_request,
    create_leave_request,
    get_pending_requests_for_approver,
    get_user_leave_requests,
    get_user_leave_stats,
    reject_leave_request,
)


# ---------------------------------------------------------------------------
#  NHÂN VIÊN: xem + tạo đơn nghỉ phép
# ---------------------------------------------------------------------------

@login_required
def leave_view(request):
    """
    GET  → Hiển thị trang nghỉ phép cá nhân (stats + bảng).
    POST → Tạo đơn nghỉ phép mới.
    """
    ensure_profile(request.user)

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES)
        if form.is_valid():
            create_leave_request(request.user, form)
            messages.success(request, 'Đã gửi đơn đăng ký nghỉ phép thành công!')
            return redirect('leave')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin đơn nghỉ phép.')
    else:
        form = LeaveRequestForm()

    stats = get_user_leave_stats(request.user)
    requests_list = get_user_leave_requests(request.user)

    return render(request, 'leaves/leave.html', {
        'active_page': 'leave',
        'can_approve': can_manage_requests(request.user),
        'form': form,
        'stats': stats,
        'requests': requests_list,
    })


# ---------------------------------------------------------------------------
#  NHÂN VIÊN: hủy đơn
# ---------------------------------------------------------------------------

@login_required
@require_POST
def leave_cancel_view(request, pk):
    """Hủy đơn nghỉ phép (chỉ đơn pending)."""
    ensure_profile(request.user)
    success, msg = cancel_leave_request(request.user, pk)
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect('leave')


# ---------------------------------------------------------------------------
#  QUẢN LÝ / HR: trang phê duyệt
# ---------------------------------------------------------------------------

@login_required
def leave_approval_view(request):
    """Trang phê duyệt nghỉ phép — 2 bước."""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('leave')

    approval_data = get_pending_requests_for_approver(request.user)

    role_name = ''
    try:
        role_name = request.user.profile.role.name if request.user.profile.role else ''
    except Exception:
        pass

    return render(request, 'leaves/leave_approval.html', {
        'active_page': 'leave',
        'step1_requests': approval_data['step1_requests'],
        'step2_requests': approval_data['step2_requests'],
        'role_name': role_name,
    })


# ---------------------------------------------------------------------------
#  QUẢN LÝ / HR: duyệt 1 đơn
# ---------------------------------------------------------------------------

@login_required
@require_POST
def leave_approve_action(request, pk):
    """Duyệt 1 đơn nghỉ phép."""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này!')
        return redirect('leave')

    success, msg = approve_leave_request(request.user, pk)
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect('leave_approval')


# ---------------------------------------------------------------------------
#  QUẢN LÝ / HR: từ chối 1 đơn
# ---------------------------------------------------------------------------

@login_required
@require_POST
def leave_reject_action(request, pk):
    """Từ chối 1 đơn nghỉ phép."""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này!')
        return redirect('leave')

    reason = request.POST.get('rejected_reason', '')
    success, msg = reject_leave_request(request.user, pk, reason)
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect('leave_approval')


# ---------------------------------------------------------------------------
#  QUẢN LÝ / HR: duyệt tất cả
# ---------------------------------------------------------------------------

@login_required
@require_POST
def leave_bulk_approve(request):
    """Duyệt tất cả đơn nghỉ phép mà user có quyền."""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này!')
        return redirect('leave')

    count = bulk_approve_requests(request.user)
    if count:
        messages.success(request, f'Đã duyệt {count} đơn nghỉ phép.')
    else:
        messages.info(request, 'Không có đơn nào cần duyệt.')
    return redirect('leave_approval')

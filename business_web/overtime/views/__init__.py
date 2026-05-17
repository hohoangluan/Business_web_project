"""Views cho tăng ca — đăng ký, hủy, phê duyệt 2 bước, từ chối."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from accounts.services import ensure_profile, can_manage_requests
from overtime.forms import OvertimeRequestForm
from overtime.services import (
    approve_overtime_request,
    bulk_approve_requests,
    cancel_overtime_request,
    create_overtime_request,
    get_monthly_chart_data,
    get_pending_requests_for_approver,
    get_user_overtime_requests,
    get_user_overtime_stats,
    reject_overtime_request,
)


# ---------------------------------------------------------------------------
#  NHÂN VIÊN: xem + tạo đơn tăng ca
# ---------------------------------------------------------------------------

@login_required
def overtime_view(request):
    """
    GET  → Hiển thị trang tăng ca cá nhân (stats + bảng + biểu đồ).
    POST → Tạo đơn tăng ca mới.
    """
    ensure_profile(request.user)

    if request.method == 'POST':
        form = OvertimeRequestForm(request.POST)
        if form.is_valid():
            create_overtime_request(request.user, form)
            messages.success(request, 'Đã gửi đơn đăng ký tăng ca thành công!')
            return redirect('overtime')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin đơn tăng ca.')
    else:
        form = OvertimeRequestForm()

    stats = get_user_overtime_stats(request.user)
    requests_list = get_user_overtime_requests(request.user)
    chart_data = get_monthly_chart_data(request.user)

    # Tính max cho biểu đồ (scale Y)
    chart_max = max((d['hours'] for d in chart_data), default=1) or 1

    return render(request, 'overtime/overtime.html', {
        'active_page': 'overtime',
        'can_approve': can_manage_requests(request.user),
        'form': form,
        'stats': stats,
        'requests': requests_list,
        'chart_data': chart_data,
        'chart_max': chart_max,
    })


# ---------------------------------------------------------------------------
#  NHÂN VIÊN: hủy đơn
# ---------------------------------------------------------------------------

@login_required
@require_POST
def overtime_cancel_view(request, pk):
    """Hủy đơn tăng ca (chỉ đơn pending của chính mình)."""
    ensure_profile(request.user)
    success, msg = cancel_overtime_request(request.user, pk)
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect('overtime')


# ---------------------------------------------------------------------------
#  QUẢN LÝ / HR: trang phê duyệt
# ---------------------------------------------------------------------------

@login_required
def overtime_approval_view(request):
    """
    Trang phê duyệt tăng ca — 2 bước.
    Leader/Manager thấy đơn pending (bước 1).
    HR thấy đơn leader_approved (bước 2).
    """
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('overtime')

    approval_data = get_pending_requests_for_approver(request.user)

    # Xác định role cho template
    role_name = ''
    try:
        role_name = request.user.profile.role.name if request.user.profile.role else ''
    except Exception:
        pass

    return render(request, 'overtime/overtime_approval.html', {
        'active_page': 'overtime',
        'step1_requests': approval_data['step1_requests'],
        'step2_requests': approval_data['step2_requests'],
        'role_name': role_name,
    })


# ---------------------------------------------------------------------------
#  QUẢN LÝ / HR: duyệt 1 đơn
# ---------------------------------------------------------------------------

@login_required
@require_POST
def overtime_approve_action(request, pk):
    """Duyệt 1 đơn tăng ca (bước 1 hoặc bước 2 tùy trạng thái)."""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này!')
        return redirect('overtime')

    success, msg = approve_overtime_request(request.user, pk)
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect('overtime_approval')


# ---------------------------------------------------------------------------
#  QUẢN LÝ / HR: từ chối 1 đơn
# ---------------------------------------------------------------------------

@login_required
@require_POST
def overtime_reject_action(request, pk):
    """Từ chối 1 đơn tăng ca (bước 1 hoặc bước 2)."""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này!')
        return redirect('overtime')

    reason = request.POST.get('rejected_reason', '')
    success, msg = reject_overtime_request(request.user, pk, reason)
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect('overtime_approval')


# ---------------------------------------------------------------------------
#  QUẢN LÝ / HR: duyệt tất cả
# ---------------------------------------------------------------------------

@login_required
@require_POST
def overtime_bulk_approve(request):
    """Duyệt tất cả đơn mà user có quyền duyệt."""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này!')
        return redirect('overtime')

    count = bulk_approve_requests(request.user)
    if count:
        messages.success(request, f'Đã duyệt {count} đơn tăng ca.')
    else:
        messages.info(request, 'Không có đơn nào cần duyệt.')
    return redirect('overtime_approval')

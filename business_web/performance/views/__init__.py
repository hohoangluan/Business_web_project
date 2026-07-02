"""Views cho đánh giá nhân viên (performance evaluations)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.services import (
    ensure_profile, can_access_evaluations, can_submit_evaluation_demo,
    get_user_role_name, get_user_display_name, can_acknowledge_evaluation, user_has_role,
)
from accounts.models import Role
from performance.services import (
    build_evaluations_page_context,
    get_pending_evaluations_for_hr,
    get_acknowledged_evaluations_for_hr,
    get_rejected_evaluations_for_hr,
    to_evaluation_dict,
    acknowledge_evaluation,
    reject_evaluation,
)
from performance.services.evaluation_data import build_evaluation_records


@login_required
def evaluations_view(request):
    """
    Trang đánh giá nhân viên (Manager/Leader).
    Submit lưu vào database thật và gửi HR xác nhận.
    Template: performance/evaluations.html
    """
    if user_has_role(request.user, Role.EMPLOYEE):
        records = build_evaluation_records([request.user])
        return render(request, 'performance/evaluations_employee.html', {
            'active_page': 'evaluations',
            'records': records,
        })

    if not can_access_evaluations(request.user):
        messages.error(request, 'Bạn không có quyền xem trang đánh giá nhân viên.')
        return redirect('dashboard')

    post_data = None
    uploaded_file = None
    if request.method == 'POST':
        if can_submit_evaluation_demo(request.user):
            post_data = request.POST
            uploaded_file = request.FILES.get('evidence_file')
        else:
            messages.error(request, 'Vai trò hiện tại chỉ được xem thông tin đánh giá.')

    context = build_evaluations_page_context(
        request.user, request.GET, post_data, uploaded_file,
    )
    if context['form_state']['success_message']:
        messages.success(request, context['form_state']['success_message'])

    context['active_page'] = 'evaluations'
    context['can_acknowledge'] = can_acknowledge_evaluation(request.user)
    return render(request, 'performance/evaluations.html', context)


@login_required
def evaluation_hr_approval_view(request):
    """
    Trang HR xác nhận các đánh giá từ Manager/Leader.
    Template: performance/evaluation_hr_approval.html
    """
    if not can_acknowledge_evaluation(request.user):
        messages.error(request, 'Bạn không có quyền truy cập trang xác nhận đánh giá.')
        return redirect('dashboard')

    pending_evals = get_pending_evaluations_for_hr(request.user)
    acknowledged_evals = get_acknowledged_evaluations_for_hr(request.user)
    rejected_evals = get_rejected_evaluations_for_hr(request.user)

    pending_list = [to_evaluation_dict(e) for e in pending_evals]
    acknowledged_list = [to_evaluation_dict(e) for e in acknowledged_evals]
    rejected_list = [to_evaluation_dict(e) for e in rejected_evals]

    context = {
        'pending_list': pending_list,
        'acknowledged_list': acknowledged_list,
        'rejected_list': rejected_list,
        'active_page': 'evaluation_hr_approval',
    }
    return render(request, 'performance/evaluation_hr_approval.html', context)


@login_required
def evaluation_hr_acknowledge_action(request, pk):
    """
    Hành động HR xác nhận đánh giá nhân viên.
    """
    if not can_acknowledge_evaluation(request.user):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này.')
        return redirect('dashboard')

    if request.method == 'POST':
        hr_note = request.POST.get('hr_note', '')
        success, message = acknowledge_evaluation(request.user, pk, hr_note)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
    return redirect('evaluation_hr_approval')

@login_required
def evaluation_hr_reject_action(request, pk):
    """Hành động HR từ chối đánh giá nhân viên."""
    if not can_acknowledge_evaluation(request.user):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này.')
        return redirect('dashboard')

    if request.method == 'POST':
        reason = request.POST.get('reject_reason', '')
        success, message = reject_evaluation(request.user, pk, reason)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

    return redirect('evaluation_hr_approval')
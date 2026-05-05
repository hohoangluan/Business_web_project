"""Views cho đánh giá nhân viên (performance evaluations)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.services import (
    ensure_profile, can_access_evaluations, can_submit_evaluation_demo,
    get_user_role_name, get_user_display_name,
)
from performance.services import build_evaluations_page_context


@login_required
def evaluations_view(request):
    """
    Trang đánh giá nhân viên (Manager/Leader).
    Submit chỉ tạo bản xem trước, chưa lưu database thật.
    Template: performance/evaluations.html
    """
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
    return render(request, 'performance/evaluations.html', context)

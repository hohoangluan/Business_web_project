"""Views điều chỉnh hợp đồng (tạo phiên bản mới) và xem lịch sử HĐ."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from accounts.services import (
    ensure_profile, ensure_contract_info,
    is_admin_user, is_hr_user, can_manage_work_info,
)
from contracts.forms import ContractAdjustForm
from contracts.services import adjust_contract, get_contract_history


@login_required
@user_passes_test(can_manage_work_info)
def hr_adjust_contract_view(request, user_id):
    """HR/Admin điều chỉnh HĐ — mỗi lần lưu tạo một phiên bản mới."""
    if is_admin_user(request.user):
        messages.error(request, 'Tài khoản Admin không có quyền điều chỉnh hợp đồng.')
        return redirect('user_list')

    target_user = get_object_or_404(User, pk=user_id)
    ensure_profile(target_user)
    contract = ensure_contract_info(target_user)

    if request.method == 'POST':
        form = ContractAdjustForm(request.POST)
        if form.is_valid():
            adjust_contract(target_user, form.cleaned_data)
            messages.success(request, f'Đã tạo phiên bản hợp đồng mới cho "{target_user.username}".')
            return redirect('contract_history', user_id=target_user.pk)
    else:
        form = ContractAdjustForm(initial={
            'contract_number': contract.contract_number,
            'contract_type': contract.contract_type,
            'contract_signed_date': contract.contract_signed_date,
            'contract_start_date': contract.contract_start_date,
            'contract_end_date': contract.contract_end_date,
            'contract_annual_leave_days': contract.contract_annual_leave_days,
            'contract_standard_shift': contract.contract_standard_shift,
            'shift_start_time': contract.shift_start_time,
            'shift_end_time': contract.shift_end_time,
            'contract_attachment_reference': contract.contract_attachment_reference,
        })

    return render(request, 'contracts/hr_adjust_contract.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
    })


@login_required
def contract_history_view(request, user_id):
    """Lịch sử HĐ. HR/superuser xem mọi người; nhân viên xem của chính mình. Admin bị chặn."""
    if is_admin_user(request.user):
        messages.error(request, 'Tài khoản Admin không sử dụng chức năng này.')
        return redirect('dashboard')

    target_user = get_object_or_404(User, pk=user_id)

    if not (is_hr_user(request.user) or request.user.id == target_user.id):
        messages.error(request, 'Bạn không có quyền xem lịch sử hợp đồng này.')
        return redirect('dashboard')

    history = get_contract_history(target_user)
    return render(request, 'contracts/contract_history.html', {
        'target_user': target_user,
        'history': history,
        'is_hr_viewer': is_hr_user(request.user),
        'active_page': 'contract',
    })

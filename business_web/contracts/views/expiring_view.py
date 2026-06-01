"""
View HR xem danh sách hợp đồng sắp hết hạn và trigger gửi email nhắc nhở.
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User

from accounts.services import can_manage_work_info, is_admin_user
from contracts.services.renewal_service import (
    THRESHOLD_FAR,
    THRESHOLD_NEAR,
    get_expiring_contracts,
    get_recipients_for_contract,
)
from contracts.services.email_service import send_renewal_reminder_email
from contracts.services import get_active_contract


@login_required
@user_passes_test(can_manage_work_info)
def hr_expiring_contracts_view(request):
    """
    Trang HR xem danh sách hợp đồng sắp hết hạn (30 ngày).
    Phân quyền: HR và Admin.
    Template: contracts/hr_expiring_contracts.html
    """
    expiring = get_expiring_contracts(days_threshold=THRESHOLD_FAR)

    context = {
        'active_page': 'contract',
        'expiring_list': expiring,
        'threshold_far': THRESHOLD_FAR,
        'threshold_near': THRESHOLD_NEAR,
        'total_count': len(expiring),
        'near_count': sum(1 for e in expiring if e['urgency'] == 'near'),
        'far_count': sum(1 for e in expiring if e['urgency'] == 'far'),
        'is_admin': is_admin_user(request.user),
    }
    return render(request, 'contracts/hr_expiring_contracts.html', context)


@login_required
@user_passes_test(can_manage_work_info)
def hr_send_reminder_view(request, user_id):
    """
    Gửi email nhắc gia hạn hợp đồng cho 1 nhân viên cụ thể.
    Chỉ nhận POST để tránh CSRF.
    """
    if request.method != 'POST':
        return redirect('hr_expiring_contracts')

    target_user = get_object_or_404(User, pk=user_id)

    contract = get_active_contract(target_user)
    if contract is None:
        messages.error(request, f"Nhân viên {target_user.username} chưa có thông tin hợp đồng.")
        return redirect('hr_expiring_contracts')

    from contracts.services.renewal_service import get_days_until_expiry
    days_left = get_days_until_expiry(contract)

    if days_left is None or days_left < 0:
        messages.warning(request, "Hợp đồng này không thời hạn hoặc đã hết hạn — không cần nhắc.")
        return redirect('hr_expiring_contracts')

    recipients = get_recipients_for_contract(contract)
    if not recipients:
        messages.warning(request, "Không có địa chỉ email nào để gửi nhắc nhở.")
        return redirect('hr_expiring_contracts')

    ok = send_renewal_reminder_email(contract, recipients, days_left)

    profile = getattr(target_user, 'profile', None)
    full_name = getattr(profile, 'full_name', '') or target_user.username

    if ok:
        messages.success(
            request,
            f"Đã gửi email nhắc gia hạn cho {full_name} đến {len(recipients)} người nhận."
        )
    else:
        messages.error(request, f"Gửi email thất bại cho {full_name}. Kiểm tra cấu hình SMTP.")

    return redirect('hr_expiring_contracts')


@login_required
@user_passes_test(can_manage_work_info)
def hr_send_all_reminders_view(request):
    """
    Gửi email nhắc nhở cho TẤT CẢ hợp đồng sắp hết hạn (≤ 30 ngày).
    Chỉ nhận POST.
    """
    if request.method != 'POST':
        return redirect('hr_expiring_contracts')

    expiring = get_expiring_contracts(days_threshold=THRESHOLD_FAR)
    success_count = 0
    fail_count = 0

    for item in expiring:
        contract  = item['contract']
        days_left = item['days_left']
        recipients = get_recipients_for_contract(contract)
        if not recipients:
            fail_count += 1
            continue
        ok = send_renewal_reminder_email(contract, recipients, days_left)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    if success_count:
        messages.success(
            request,
            f"Đã gửi email nhắc nhở cho {success_count} hợp đồng."
            + (f" ({fail_count} thất bại)" if fail_count else "")
        )
    elif fail_count:
        messages.error(request, f"Tất cả {fail_count} lần gửi đều thất bại. Kiểm tra cấu hình SMTP.")
    else:
        messages.info(request, "Không có hợp đồng nào sắp hết hạn để nhắc.")

    return redirect('hr_expiring_contracts')

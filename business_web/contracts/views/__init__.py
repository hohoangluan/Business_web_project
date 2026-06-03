"""Views cho hợp đồng lao động."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.decorators import deny_admin
from accounts.services import ensure_profile, ensure_contract_info
from contracts.services import build_contract_page_context

# Re-export HR views
from contracts.views.expiring_view import (
    hr_expiring_contracts_view,
    hr_send_reminder_view,
    hr_send_all_reminders_view,
)

from contracts.views.contract_versioning_view import (
    hr_adjust_contract_view,
    contract_history_view,
)


@login_required
@deny_admin
def contract_view(request):
    """
    Trang hợp đồng cá nhân.
    Chỉ hiển thị hợp đồng của chính người đang đăng nhập.
    Template: contracts/contract.html
    """
    ensure_profile(request.user)
    contract_info = ensure_contract_info(request.user)
    contract_context = build_contract_page_context(contract_info)

    return render(request, 'contracts/contract.html', {
        'active_page': 'contract',
        'contract_context': contract_context,
        'contract_info': contract_info,
    })

"""Services cho hợp đồng lao động."""
from datetime import datetime
from django.utils import timezone

# ----- Re-export từ renewal_service -----
from contracts.services.renewal_service import (
    THRESHOLD_FAR,
    THRESHOLD_NEAR,
    parse_ddmmyyyy,
    get_days_until_expiry,
    get_expiring_contracts,
    get_recipients_for_contract,
)

# ----- Re-export từ email_service -----
from contracts.services.email_service import send_renewal_reminder_email

# ----- Hàm cũ (giữ backward compatibility) -----

def parse_ddmmyyyy_date(raw_value):
    """Alias cũ — dùng parse_ddmmyyyy() thay thế."""
    return parse_ddmmyyyy(raw_value)


def has_complete_contract_info(contract_info):
    """Kiểm tra đã có đủ thông tin hợp đồng tối thiểu để hiển thị chưa."""
    return any([
        contract_info.contract_number,
        contract_info.contract_type,
        contract_info.contract_signed_date,
        contract_info.contract_start_date,
        contract_info.contract_standard_shift,
        contract_info.contract_annual_leave_days is not None,
    ])


def build_contract_page_context(contract_info):
    """Chuẩn bị dữ liệu cho trang hợp đồng cá nhân."""
    has_contract = has_complete_contract_info(contract_info)
    if not has_contract:
        return {
            'has_contract': False,
            'contract_status_label': '',
            'contract_status_class': 'badge-none',
            'contract_end_display': '',
            'show_expiry_warning': False,
            'days_until_expiry': None,
        }

    today = timezone.localdate()
    start_date = parse_ddmmyyyy(contract_info.contract_start_date)
    end_date = parse_ddmmyyyy(contract_info.contract_end_date)

    if not contract_info.contract_end_date:
        contract_status_label = 'Không thời hạn'
        contract_status_class = 'badge-active'
        contract_end_display = 'Không thời hạn'
    elif end_date and end_date < today:
        contract_status_label = 'Hết hạn'
        contract_status_class = 'badge-inactive'
        contract_end_display = contract_info.contract_end_date
    elif start_date and start_date > today:
        contract_status_label = 'Sắp hiệu lực'
        contract_status_class = 'badge-locked'
        contract_end_display = contract_info.contract_end_date
    else:
        contract_status_label = 'Có hiệu lực'
        contract_status_class = 'badge-active'
        contract_end_display = contract_info.contract_end_date

    show_expiry_warning = False
    days_until_expiry = None
    if end_date and today <= end_date:
        days_until_expiry = (end_date - today).days
        show_expiry_warning = days_until_expiry <= THRESHOLD_NEAR

    return {
        'has_contract': True,
        'contract_status_label': contract_status_label,
        'contract_status_class': contract_status_class,
        'contract_end_display': contract_end_display,
        'show_expiry_warning': show_expiry_warning,
        'days_until_expiry': days_until_expiry,
    }


def get_active_contract(user):
    """Trả hợp đồng đang hiệu lực (is_active=True) mới nhất, hoặc None."""
    return user.contracts.filter(is_active=True).order_by('-id').first()

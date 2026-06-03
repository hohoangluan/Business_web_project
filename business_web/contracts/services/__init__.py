"""Services cho hợp đồng lao động."""
from datetime import datetime
from django.utils import timezone

# ----- Re-export từ renewal_service -----
from contracts.services.renewal_service import (
    THRESHOLD_FAR,
    THRESHOLD_NEAR,
    parse_ddmmyyyy,
    expire_overdue_contracts,
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


def validate_contract_date_order(signed, start, end):
    """Kiểm tra thứ tự ngày hợp đồng (chuỗi DD/MM/YYYY).

    Quy tắc: ngày bắt đầu ≥ ngày ký; ngày hết hạn ≥ ngày bắt đầu (nếu có).
    Trả về list thông báo lỗi (rỗng = hợp lệ). Bỏ qua ngày trống/sai định dạng
    (validation định dạng do nơi gọi xử lý riêng).
    """
    errors = []
    d_signed = parse_ddmmyyyy(signed)
    d_start = parse_ddmmyyyy(start)
    d_end = parse_ddmmyyyy(end)
    if d_signed and d_start and d_start < d_signed:
        errors.append('Ngày bắt đầu hợp đồng phải từ ngày ký trở đi.')
    if d_start and d_end and d_end < d_start:
        errors.append('Ngày hết hạn hợp đồng phải từ ngày bắt đầu trở đi.')
    return errors


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


def get_shift_times(user):
    """Trả (shift_start, shift_end) từ HĐ active, fallback settings."""
    from django.conf import settings
    contract = get_active_contract(user)
    start = (contract.shift_start_time if contract and contract.shift_start_time
             else settings.WORK_START_TIME)
    end = (contract.shift_end_time if contract and contract.shift_end_time
           else settings.WORK_END_TIME)
    return start, end


# ----- Versioning hợp đồng -----

CONTRACT_VERSION_FIELDS = [
    'contract_number', 'contract_type', 'contract_signed_date',
    'contract_start_date', 'contract_end_date', 'contract_annual_leave_days',
    'contract_standard_shift', 'shift_start_time', 'shift_end_time',
    'contract_attachment_reference',
]


def adjust_contract(user, data):
    """Tạo phiên bản HĐ mới từ HĐ active hiện tại + field sửa.

    Archive HĐ active cũ (is_active=False) và tạo HĐ mới copy-forward toàn bộ
    field rồi ghi đè các field có trong `data`. Nguyên tử trong transaction.
    Trả về HĐ mới.
    """
    from django.db import transaction
    from contracts.models import ContractInfo
    from accounts.services import ensure_contract_info

    with transaction.atomic():
        old = ensure_contract_info(user)
        new_values = {f: getattr(old, f) for f in CONTRACT_VERSION_FIELDS}
        for f in CONTRACT_VERSION_FIELDS:
            if f in data:
                new_values[f] = data[f]
        old.is_active = False
        old.save(update_fields=['is_active'])
        return ContractInfo.objects.create(user=user, is_active=True, **new_values)


def get_contract_history(user):
    """Mọi phiên bản HĐ của user (active + archived), mới nhất trước."""
    return user.contracts.order_by('-created_at', '-id')

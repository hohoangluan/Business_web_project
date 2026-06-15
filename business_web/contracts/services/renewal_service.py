"""
==============================================================================
CONTRACT RENEWAL SERVICE
==============================================================================
Cung cấp logic phát hiện hợp đồng sắp hết hạn và tổng hợp danh sách
người nhận thông báo (nhân viên, manager, leader, HR).

Ngưỡng cảnh báo: 30 ngày, 15 ngày và 7 ngày.
==============================================================================
"""

from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User


# Các ngưỡng cảnh báo (ngày)
THRESHOLD_FAR = 30    # Nhắc lần đầu: còn 30 ngày
THRESHOLD_MID = 15    # Nhắc lần hai: còn 15 ngày
THRESHOLD_NEAR = 7    # Nhắc khẩn cấp: còn 7 ngày


def parse_ddmmyyyy(raw_value):
    """Chuyển chuỗi DD/MM/YYYY thành date. Trả None nếu sai format."""
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, '%d/%m/%Y').date()
    except ValueError:
        return None


def get_days_until_expiry(contract_info):
    """
    Tính số ngày còn lại đến ngày hết hạn hợp đồng.
    Trả về None nếu hợp đồng không thời hạn hoặc ngày không hợp lệ.
    """
    end_date = parse_ddmmyyyy(contract_info.contract_end_date)
    if not end_date:
        return None
    today = timezone.localdate()
    delta = (end_date - today).days
    return delta


def expire_overdue_contracts():
    """Đặt is_active=False cho HĐ đang hiệu lực đã quá hạn (days_left < 0).

    Trả về số hợp đồng vừa hết hiệu lực (QĐ_CanhBao §5.7).
    """
    from contracts.models import ContractInfo

    today = timezone.localdate()
    count = 0
    qs = ContractInfo.objects.filter(is_active=True).exclude(contract_end_date='')
    for contract in qs:
        end_date = parse_ddmmyyyy(contract.contract_end_date)
        if end_date and end_date < today:
            contract.is_active = False
            contract.save(update_fields=['is_active'])
            count += 1
    return count


def get_expiring_contracts(days_threshold=THRESHOLD_FAR):
    """
    Truy vấn danh sách ContractInfo sắp hết hạn trong `days_threshold` ngày.

    Trả về list dict:
    {
        'contract': ContractInfo,
        'days_left': int,
        'urgency': 'near' | 'far'   # 'near' nếu <= 7 ngày
    }
    """
    from contracts.models import ContractInfo

    today = timezone.localdate()
    deadline = today + timedelta(days=days_threshold)

    # Lọc theo vòng lặp vì ngày lưu dạng chuỗi DD/MM/YYYY
    all_contracts = ContractInfo.objects.select_related('user').filter(
        is_active=True,
    ).exclude(contract_end_date='')

    results = []
    for contract in all_contracts:
        end_date = parse_ddmmyyyy(contract.contract_end_date)
        if end_date is None:
            continue
        days_left = (end_date - today).days
        # Chỉ lấy hợp đồng sắp hết hạn vào đúng các mốc: 30, 15, 7 ngày để tránh spam
        if days_left in (THRESHOLD_FAR, THRESHOLD_MID, THRESHOLD_NEAR) and days_left <= days_threshold:
            urgency = 'near' if days_left <= THRESHOLD_NEAR else 'far'
            results.append({
                'contract': contract,
                'days_left': days_left,
                'urgency': urgency,
            })

    # Sắp xếp theo số ngày tăng dần (sắp hết trước)
    results.sort(key=lambda x: x['days_left'])
    return results


def get_recipients_for_contract(contract_info):
    """
    Tổng hợp danh sách email người cần nhận thông báo cho một hợp đồng:
    - Nhân viên (nếu có email)
    - Manager phụ trách
    - Leader phụ trách
    - Tất cả HR trong hệ thống

    Trả về list các email unique (bỏ trùng, bỏ rỗng).
    """
    from accounts.models import UserProfile

    recipients = set()
    employee = contract_info.user

    # 1. Bản thân nhân viên
    if employee.email:
        recipients.add(employee.email)

    # 2. Manager và Leader từ EmployeeWorkInfo
    try:
        work_info = employee.work_info
        if work_info.manager_user and work_info.manager_user.email:
            recipients.add(work_info.manager_user.email)
        if work_info.leader_user and work_info.leader_user.email:
            recipients.add(work_info.leader_user.email)
    except Exception:
        pass  # Không có work_info thì bỏ qua

    # 3. Tất cả HR trong hệ thống
    hr_profiles = UserProfile.objects.filter(
        role__name='hr'
    ).select_related('user')
    for profile in hr_profiles:
        if profile.user.email:
            recipients.add(profile.user.email)

    return list(recipients)

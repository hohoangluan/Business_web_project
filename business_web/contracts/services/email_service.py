"""
==============================================================================
CONTRACT EMAIL SERVICE
==============================================================================
Gửi email nhắc nhở gia hạn hợp đồng đến danh sách người nhận.
Sử dụng Gmail SMTP đã cấu hình trong settings.py / .env.
==============================================================================
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_renewal_reminder_email(contract_info, recipients, days_left):
    """
    Gửi email nhắc gia hạn hợp đồng cho danh sách người nhận.

    Args:
        contract_info: instance ContractInfo
        recipients: list[str] — danh sách địa chỉ email
        days_left: int — số ngày còn lại đến hết hạn

    Returns:
        bool — True nếu gửi thành công (có ít nhất 1 email), False nếu thất bại
    """
    if not recipients:
        return False

    employee = contract_info.user
    profile = getattr(employee, 'profile', None)
    full_name = getattr(profile, 'full_name', '') or employee.username
    employee_id = getattr(profile, 'employee_id', '') or '—'

    # Xác định mức độ khẩn
    is_urgent = days_left <= 7

    subject = (
        f"[KHẨN] Hợp đồng sắp hết hạn trong {days_left} ngày - {full_name}"
        if is_urgent else
        f"[Nhắc nhở] Hợp đồng sắp hết hạn trong {days_left} ngày - {full_name}"
    )

    context = {
        'full_name': full_name,
        'employee_id': employee_id,
        'username': employee.username,
        'contract_number': contract_info.contract_number or '—',
        'contract_type': contract_info.contract_type or '—',
        'contract_end_date': contract_info.contract_end_date or '—',
        'days_left': days_left,
        'is_urgent': is_urgent,
    }

    # Render HTML từ template
    html_message = render_to_string(
        'contracts/emails/renewal_reminder.html',
        context
    )
    # Plain text fallback
    plain_message = (
        f"Nhắc nhở gia hạn hợp đồng\n\n"
        f"Nhân viên: {full_name} ({employee_id})\n"
        f"Số HĐ: {context['contract_number']}\n"
        f"Loại HĐ: {context['contract_type']}\n"
        f"Ngày hết hạn: {context['contract_end_date']}\n"
        f"Số ngày còn lại: {days_left} ngày\n\n"
        f"Vui lòng liên hệ HR để gia hạn hợp đồng kịp thời."
    )

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"  [ERROR] Gửi email thất bại cho {recipients}: {e}")
        return False

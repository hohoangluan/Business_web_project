"""Forgot password helper services."""

import random
import string

from django.core.mail import send_mail
from django.conf import settings


def mask_email(email):
    """Mask the local part of an email address for recovery UI."""

    if not email or "@" not in email:
        return email or ""

    local_part, domain = email.split("@", 1)
    if len(local_part) <= 2:
        masked_local = local_part[:1] + "*"
    else:
        masked_local = local_part[0] + ("*" * (len(local_part) - 2)) + local_part[-1]
    return f"{masked_local}@{domain}"


def generate_otp():
    """Generate a random 6-digit numeric OTP string."""
    return "".join(random.choices(string.digits, k=6))


def send_otp_email(email, otp):
    """Send the OTP code to the given email address via Gmail SMTP.

    Returns True on success, False on failure.
    """
    subject = "Mã xác nhận khôi phục mật khẩu - HRMS Portal"
    message = (
        f"Xin chào,\n\n"
        f"Mã xác nhận của bạn là: {otp}\n\n"
        f"Mã có hiệu lực trong 1 phút kể từ lúc gửi thành công.\n"
        f"Vui lòng không chia sẻ mã này với bất kỳ ai.\n\n"
        f"Trân trọng,\nHRMS Portal"
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False


def create_otp_for_user(user):
    """Delete any existing OTPs for this user, create and return a new one.

    The new OtpCode record is saved to the database.
    """
    from accounts.models.otp_code_model import OtpCode

    # Remove all previous OTP records for this user
    OtpCode.objects.filter(user=user).delete()

    code = generate_otp()
    otp_record = OtpCode.objects.create(user=user, code=code)
    return otp_record


def verify_otp(user, input_code):
    """Verify the OTP for a given user.

    Returns a tuple (is_valid: bool, error_message: str | None).

    On success the OTP record is deleted from the database.
    On failure (wrong code or expired) the record is kept so the user
    can attempt again until the natural expiry window passes, but the
    record is deleted when expired so a fresh OTP must be requested.
    """
    from accounts.models.otp_code_model import OtpCode

    try:
        otp_record = OtpCode.objects.get(user=user)
    except OtpCode.DoesNotExist:
        return False, "Mã xác nhận không tồn tại. Vui lòng yêu cầu mã mới."

    if otp_record.is_expired():
        # Clean up expired record
        otp_record.delete()
        return False, "Mã xác nhận đã hết hạn. Vui lòng yêu cầu mã mới."

    if otp_record.code != input_code.strip():
        return False, "Mã xác nhận không đúng. Vui lòng kiểm tra lại."

    # Correct and still valid — consume it
    otp_record.delete()
    return True, None

"""Password recovery UI flow — OTP via Gmail."""

from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from accounts.services import (
    create_otp_for_user,
    mask_email,
    send_otp_email,
    verify_otp,
)


def forgot_password_view(request):
    """Three-step password recovery: username → OTP → reset password.

    Step 1 (username): Locate the account and send an OTP to the stored email.
    Step 2 (code):     Validate the OTP against the DB record (2-min expiry).
                       On success, store the verified username in session and
                       redirect to the reset-password page.
    Resend:            Regenerate and resend OTP when user clicks "Gửi lại mã".
    """

    if request.user.is_authenticated:
        return redirect("dashboard")

    context = {
        "step": "username",
        "username": "",
        "masked_email": "",
    }

    if request.method == "POST":
        step = request.POST.get("step", "username")
        username = request.POST.get("username", "").strip()
        context["username"] = username

        # ------------------------------------------------------------------
        # STEP 1 — Collect username, find user, send OTP
        # ------------------------------------------------------------------
        if step == "username":
            user = User.objects.filter(username=username).first() if username else None

            if not username:
                context["error_message"] = "Vui lòng nhập username để nhận mã xác nhận."

            elif not user:
                context["error_message"] = "Không tìm thấy tài khoản với username này."

            elif not user.email:
                context["error_message"] = "Tài khoản này chưa có email trong hồ sơ."

            else:
                # Create OTP in DB (deletes any previous one) then email it
                otp_record = create_otp_for_user(user)
                email_sent = send_otp_email(user.email, otp_record.code)

                if email_sent:
                    context.update(
                        {
                            "step": "code",
                            "masked_email": mask_email(user.email),
                            "success_message": (
                                "Mã xác nhận đã được gửi đến Gmail của bạn. "
                                "Mã có hiệu lực trong 1 phút kể từ lúc gửi thành công."
                            ),
                        }
                    )
                else:
                    context["error_message"] = (
                        "Không thể gửi email. Vui lòng thử lại sau hoặc liên hệ quản trị viên."
                    )

        # ------------------------------------------------------------------
        # STEP 2 — Validate OTP submitted by user
        # ------------------------------------------------------------------
        elif step == "code":
            verification_code = request.POST.get("verification_code", "").strip()
            user = User.objects.filter(username=username).first() if username else None

            context.update(
                {
                    "step": "code",
                    "masked_email": mask_email(user.email) if user and user.email else "",
                    "verification_code": verification_code,
                }
            )

            if not verification_code:
                context["error_message"] = "Vui lòng nhập mã xác nhận."

            elif not user:
                context["error_message"] = "Phiên làm việc hết hạn. Vui lòng thử lại từ đầu."
                context["step"] = "username"

            else:
                is_valid, error_msg = verify_otp(user, verification_code)

                if is_valid:
                    # Store verified identity in session then redirect
                    request.session["otp_verified_username"] = username
                    return redirect("reset_password_after_otp")
                else:
                    context["error_message"] = error_msg

        # ------------------------------------------------------------------
        # RESEND — User clicked "Gửi lại mã" (step hidden value = "username"
        #          but resend flag is present)
        # ------------------------------------------------------------------
        elif step == "resend":
            user = User.objects.filter(username=username).first() if username else None

            if not user or not user.email:
                context["error_message"] = "Không tìm thấy tài khoản. Vui lòng thử lại."
            else:
                otp_record = create_otp_for_user(user)
                email_sent = send_otp_email(user.email, otp_record.code)

                if email_sent:
                    context.update(
                        {
                            "step": "code",
                            "masked_email": mask_email(user.email),
                            "success_message": (
                                "Mã mới đã được gửi lại đến Gmail của bạn. "
                                "Mã có hiệu lực trong 1 phút kể từ lúc gửi thành công."
                            ),
                        }
                    )
                else:
                    context.update(
                        {
                            "step": "code",
                            "masked_email": mask_email(user.email),
                            "error_message": "Không thể gửi email. Vui lòng thử lại sau.",
                        }
                    )

    return render(request, "accounts/auth/forgot_password.html", context)

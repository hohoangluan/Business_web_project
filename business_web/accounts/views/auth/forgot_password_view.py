"""Password recovery UI flow for accounts."""

from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from accounts.services import mask_email


def forgot_password_view(request):
    """Two-step password recovery UI placeholder."""

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

        if step == "username":
            user = User.objects.filter(username=username).first() if username else None
            if not username:
                context["error_message"] = "Vui lòng nhập username để nhận mã xác nhận."
            elif not user:
                context["error_message"] = "Không tìm thấy tài khoản với username này."
            elif not user.email:
                context["error_message"] = "Tài khoản này chưa có email trong hồ sơ."
            else:
                context.update(
                    {
                        "step": "code",
                        "masked_email": mask_email(user.email),
                        "success_message": (
                            "Mã xác nhận sẽ được gửi đến Gmail trong hồ sơ tài khoản."
                        ),
                    }
                )

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
            elif len(verification_code) != 6:
                context["error_message"] = "Mã xác nhận gồm 6 ký tự."
            else:
                context["success_message"] = "Giao diện xác nhận mã đã sẵn sàng."

    return render(request, "accounts/auth/forgot_password.html", context)

"""Reset password view — post OTP verification, in auth package."""

from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from accounts.forms.auth.reset_password_form import ResetPasswordForm
from accounts.services.auth.reset_password_service import reset_user_password


def reset_password_after_otp_view(request):
    """Allow a user to set a new password after successful OTP verification.

    Guards against direct access: if ``session['otp_verified_username']``
    is absent the request is redirected back to the forgot-password page.
    """

    verified_username = request.session.get("otp_verified_username")
    if not verified_username:
        return redirect("forgot_password")

    user = User.objects.filter(username=verified_username).first()
    if not user:
        # Username stored in session is no longer valid
        del request.session["otp_verified_username"]
        return redirect("forgot_password")

    context = {"form": ResetPasswordForm()}

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        context["form"] = form

        if form.is_valid():
            new_password = form.cleaned_data["new_password1"]
            reset_user_password(user, new_password)

            # Clean up session key so this URL cannot be re-used
            try:
                del request.session["otp_verified_username"]
            except KeyError:
                pass

            return redirect("login")

    return render(request, "accounts/auth/reset_password.html", context)

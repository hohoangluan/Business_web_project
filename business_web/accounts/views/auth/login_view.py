"""Login view for accounts."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView

from accounts.forms import LoginForm
from accounts.services.auth.login_lockout_service import (
    clear_failures,
    reached_limit,
    register_failure,
)


class AccountsLoginView(LoginView):
    """Django login view with the accounts template and local form alias.

    Thực thi QĐ_TK1: sai mật khẩu liên tiếp tới ngưỡng → khóa tài khoản
    (``is_active=False``), chờ HR/Admin mở khóa (QĐ_TK2).
    """

    authentication_form = LoginForm
    template_name = "accounts/auth/login.html"

    def form_valid(self, form):
        clear_failures(form.get_user().get_username())
        return super().form_valid(form)

    def form_invalid(self, form):
        username = (self.request.POST.get('username') or '').strip()
        if username:
            count = register_failure(username)
            if reached_limit(count):
                self._lock_account(username)
        return super().form_invalid(form)

    def _lock_account(self, username):
        user = User.objects.filter(
            username__iexact=username, is_active=True
        ).first()
        if user:
            user.is_active = False
            user.save(update_fields=['is_active'])
            clear_failures(username)
        messages.error(
            self.request,
            'Tài khoản đã bị khóa do nhập sai mật khẩu '
            f'{settings.LOGIN_LOCKOUT_MAX_FAILS} lần. '
            'Vui lòng liên hệ HR/Admin để mở khóa.',
        )

"""Authentication views for accounts."""

from accounts.views.auth.forgot_password_view import forgot_password_view
from accounts.views.auth.login_view import AccountsLoginView
from accounts.views.auth.logout_view import logout_view
from accounts.views.auth.register_view import register_view
from accounts.views.auth.reset_password_view import reset_password_after_otp_view

__all__ = [
    "AccountsLoginView",
    "forgot_password_view",
    "logout_view",
    "register_view",
    "reset_password_after_otp_view",
]

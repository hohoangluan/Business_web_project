"""Public view exports for the accounts app."""

from accounts.views.account.account_info_view import (
    account_info_view,
    dashboard_view,
    settings_view,
)
from accounts.views.account.account_status_view import (
    account_status_view,
    reset_user_password_view,
    toggle_user_active_view,
)
from accounts.views.account.account_update_view import (
    account_update_view,
    admin_create_account_view,
    assign_permissions_view,
    assign_role_view,
    delete_user_view,
    switch_role_view,
    user_list_view,
)
from accounts.views.account.notification_view import (
    mark_notifications_read_view,
    notifications_view,
)
from accounts.views.auth.forgot_password_view import forgot_password_view
from accounts.views.auth.login_view import AccountsLoginView
from accounts.views.auth.logout_view import logout_view
from accounts.views.auth.register_view import register_view
from accounts.views.auth.reset_password_view import reset_password_after_otp_view

__all__ = [
    "AccountsLoginView",
    "account_info_view",
    "account_status_view",
    "account_update_view",
    "admin_create_account_view",
    "assign_permissions_view",
    "assign_role_view",
    "dashboard_view",
    "delete_user_view",
    "forgot_password_view",
    "logout_view",
    "mark_notifications_read_view",
    "notifications_view",
    "register_view",
    "reset_password_after_otp_view",
    "reset_user_password_view",
    "settings_view",
    "switch_role_view",
    "toggle_user_active_view",
    "user_list_view",
]

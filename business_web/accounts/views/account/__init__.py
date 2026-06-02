"""Account management views."""

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

__all__ = [
    "account_info_view",
    "account_status_view",
    "account_update_view",
    "admin_create_account_view",
    "assign_permissions_view",
    "assign_role_view",
    "dashboard_view",
    "delete_user_view",
    "mark_notifications_read_view",
    "notifications_view",
    "reset_user_password_view",
    "settings_view",
    "switch_role_view",
    "toggle_user_active_view",
    "user_list_view",
]

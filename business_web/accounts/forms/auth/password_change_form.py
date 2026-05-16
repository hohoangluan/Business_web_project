"""Password change form wrapper for accounts."""

from django.contrib.auth.forms import PasswordChangeForm


class AccountPasswordChangeForm(PasswordChangeForm):
    """Project-local alias for Django's password change form."""

    pass

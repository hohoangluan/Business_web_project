"""Login form wrapper for accounts."""

from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """Project-local alias for Django's authentication form."""

    pass

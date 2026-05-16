"""Login view for accounts."""

from django.contrib.auth.views import LoginView

from accounts.forms import LoginForm


class AccountsLoginView(LoginView):
    """Django login view with the accounts template and local form alias."""

    authentication_form = LoginForm
    template_name = "accounts/auth/login.html"

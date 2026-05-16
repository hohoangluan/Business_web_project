"""Password change placeholder view."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def password_change_view(request):
    """Placeholder page for future password change support."""

    return render(request, "accounts/auth/password_change.html")

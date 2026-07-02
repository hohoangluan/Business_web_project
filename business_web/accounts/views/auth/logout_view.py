"""Logout view for accounts."""

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache


@never_cache
def logout_view(request):
    """Log the current user out and return to the login page."""

    logout(request)
    messages.info(request, "Ban da dang xuat thanh cong.")
    response = redirect("login")
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response

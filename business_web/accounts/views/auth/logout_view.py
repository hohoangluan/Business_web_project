"""Logout view for accounts."""

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect


def logout_view(request):
    """Log the current user out and return to the login page."""

    logout(request)
    messages.info(request, "Ban da dang xuat thanh cong.")
    return redirect("login")

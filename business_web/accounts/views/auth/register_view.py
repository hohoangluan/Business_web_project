"""Registration view for accounts."""

from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from accounts.forms import RegisterForm
from accounts.services import create_manual_account


def register_view(request):
    """Register a user and initialize the related profile records."""

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = create_manual_account(
                    employee_id=form.cleaned_data["employee_id"],
                    password=form.cleaned_data["password"],
                    full_name=form.cleaned_data["full_name"],
                    email=form.cleaned_data["email"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                login(request, user)
                messages.success(request, "Dang ky tai khoan thanh cong! Chao mung ban.")
                return redirect("dashboard")
    else:
        form = RegisterForm()

    return render(request, "accounts/auth/register.html", {"form": form})

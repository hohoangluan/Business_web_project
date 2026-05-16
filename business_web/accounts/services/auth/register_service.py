"""Registration services for accounts."""

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction

from accounts.models import UserProfile
from accounts.services.account import ensure_account_profiles


def normalize_employee_username(employee_id):
    """Build the login username from an employee ID."""

    return (employee_id or "").strip().lower().replace(" ", "")


@transaction.atomic
def create_manual_account(employee_id, password, full_name="", email=""):
    """Create a new account manually from employee ID and password."""

    employee_id = (employee_id or "").strip()
    full_name = (full_name or "").strip()
    email = (email or "").strip()
    username = normalize_employee_username(employee_id)

    if not employee_id:
        raise ValidationError("Mã nhân viên không được để trống.")
    if not password:
        raise ValidationError("Mật khẩu không được để trống.")
    if email:
        validate_email(email)
    validate_password(password)
    if User.objects.filter(username=username).exists():
        raise ValidationError("Mã nhân viên này đã có tài khoản.")
    if email:
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email này đã được sử dụng.")

    user = User.objects.create_user(username=username, email=email, password=password)
    ensure_account_profiles(
        user,
        employee_id=employee_id,
        full_name=full_name,
        email=email,
    )
    return user


def create_automatic_account(*args, **kwargs):
    """Placeholder for the automatic account creation flow."""

    raise NotImplementedError("Automatic account creation will be implemented later.")

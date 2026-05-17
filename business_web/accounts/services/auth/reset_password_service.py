"""Reset password service for post-OTP verification flow."""

from django.contrib.auth.models import User


def reset_user_password(user: User, new_password: str) -> None:
    """Set a new password for the given user and save to DB.

    Should only be called after OTP has been verified successfully.
    """
    user.set_password(new_password)
    user.save()

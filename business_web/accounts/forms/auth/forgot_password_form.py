"""Forgot password forms for accounts."""

from django import forms


class ForgotPasswordUsernameForm(forms.Form):
    """Collect the username for password recovery."""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Nhap username / ma nhan vien",
                "id": "id_username",
            }
        ),
    )


class ForgotPasswordCodeForm(forms.Form):
    """Collect the verification code for password recovery."""

    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "placeholder": "------",
                "id": "id_verification_code",
                "maxlength": "6",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
            }
        ),
    )

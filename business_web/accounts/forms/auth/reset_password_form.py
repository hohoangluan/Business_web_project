"""Reset password form for post-OTP verification flow."""

from django import forms


class ResetPasswordForm(forms.Form):
    """Collect and validate a new password after OTP verification."""

    new_password1 = forms.CharField(
        label="Mật khẩu mới",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Nhập mật khẩu mới (tối thiểu 8 ký tự)",
                "id": "id_new_password1",
                "autocomplete": "new-password",
            }
        ),
    )
    new_password2 = forms.CharField(
        label="Xác nhận mật khẩu",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Nhập lại mật khẩu mới",
                "id": "id_new_password2",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean(self):
        """Validate that the two password fields match."""
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("new_password1")
        pw2 = cleaned_data.get("new_password2")

        if pw1 and pw2 and pw1 != pw2:
            self.add_error("new_password2", "Hai mật khẩu không khớp nhau.")

        return cleaned_data

"""Registration form for the accounts app."""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from accounts.models import UserProfile


class RegisterForm(forms.Form):
    """Manual registration form using employee account details."""

    employee_id = forms.CharField(
        max_length=50,
        required=True,
        help_text="Mã nhân viên duy nhất.",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "VD: NV001",
                "id": "employee_id",
            }
        ),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Nhập mật khẩu",
                "id": "password",
            }
        ),
    )
    full_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "VD: Nguyễn Văn A",
                "id": "full_name",
            }
        ),
    )
    email = forms.EmailField(
        required=False,
        error_messages={"invalid": "Email không đúng định dạng."},
        widget=forms.EmailInput(
            attrs={
                "class": "form-input",
                "placeholder": "VD: a@gmail.com",
                "id": "email",
            }
        ),
    )

    def clean_employee_id(self):
        value = self.cleaned_data.get("employee_id", "").strip()
        if not value:
            raise forms.ValidationError("Mã nhân viên không được để trống.")

        username = value.lower().replace(" ", "")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Mã nhân viên này đã có tài khoản.")
        if UserProfile.objects.filter(employee_id__iexact=value).exists():
            raise forms.ValidationError("Mã nhân viên này đã được sử dụng.")
        return value

    def clean_full_name(self):
        value = self.cleaned_data.get("full_name", "").strip()
        return value

    def clean_email(self):
        value = self.cleaned_data.get("email", "").strip()
        if not value:
            return ""
        if User.objects.filter(email__iexact=value).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return value

    def clean_password(self):
        password = self.cleaned_data.get("password", "")
        validate_password(password)
        return password

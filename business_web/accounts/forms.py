"""
==============================================================================
ACCOUNTS FORMS
==============================================================================
Chỉ giữ forms liên quan đến xác thực và quản trị user:
  - RegisterForm: đăng ký tài khoản
  - AssignRoleForm: gán vai trò (Admin)
  - AssignPermissionsForm: gán quyền (Admin)

EmployeeProfileForm đã chuyển sang employee_profiles.forms
==============================================================================
"""

import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Role, CustomPermission, UserProfile


class RegisterForm(UserCreationForm):
    """
    Form đăng ký 7 trường: username, password x2, full_name, email, phone, dob, employee_id.
    """

    full_name = forms.CharField(
        max_length=255, required=True,
        help_text="Họ tên đầy đủ. Chỉ chữ cái và dấu cách.",
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'VD: Nguyen Van A', 'id': 'full_name',
        }),
    )
    email = forms.EmailField(
        required=True, help_text="Phải chứa @.",
        widget=forms.EmailInput(attrs={
            'class': 'form-input', 'placeholder': 'VD: you@example.com', 'id': 'email',
        }),
    )
    phone_number = forms.CharField(
        max_length=20, required=True, help_text="Chỉ chứa số.",
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'VD: 0901234567', 'id': 'phone_number',
        }),
    )
    date_of_birth = forms.CharField(
        max_length=10, required=True, help_text="Định dạng: DD/MM/YYYY.",
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'VD: 15/06/1990', 'id': 'date_of_birth',
        }),
    )
    employee_id = forms.CharField(
        max_length=50, required=True, help_text="Mã nhân viên duy nhất.",
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'VD: EMP001', 'id': 'employee_id',
        }),
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2',
                  'full_name', 'email', 'phone_number',
                  'date_of_birth', 'employee_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-input', 'placeholder': 'Chọn username', 'id': 'username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input', 'placeholder': 'Chọn mật khẩu', 'id': 'password1',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input', 'placeholder': 'Xác nhận mật khẩu', 'id': 'password2',
        })

    def clean_full_name(self):
        value = self.cleaned_data.get('full_name', '').strip()
        if not value:
            raise forms.ValidationError("Họ tên không được để trống.")
        if not re.match(r"^[a-zA-ZÀ-ỹ\s\-']+$", value):
            raise forms.ValidationError("Họ tên không được chứa số hoặc ký tự đặc biệt.")
        return value

    def clean_email(self):
        value = self.cleaned_data.get('email', '').strip()
        if '@' not in value:
            raise forms.ValidationError("Email phải chứa '@'.")
        return value

    def clean_phone_number(self):
        value = self.cleaned_data.get('phone_number', '').strip()
        if not value.isdigit():
            raise forms.ValidationError("Số điện thoại chỉ chứa chữ số.")
        return value

    def clean_date_of_birth(self):
        value = self.cleaned_data.get('date_of_birth', '').strip()
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', value):
            raise forms.ValidationError("Ngày sinh phải có định dạng DD/MM/YYYY.")
        return value

    def clean_employee_id(self):
        value = self.cleaned_data.get('employee_id', '').strip()
        if not value:
            raise forms.ValidationError("Mã nhân viên không được để trống.")
        if UserProfile.objects.filter(employee_id=value).exists():
            raise forms.ValidationError("Mã nhân viên này đã được sử dụng.")
        return value


class AssignRoleForm(forms.Form):
    """Form gán vai trò cho user (Admin dùng)."""
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        empty_label="-- Chưa gán vai trò --",
        help_text="Vai trò quyết định giao diện và quyền truy cập.",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'role-select'}),
    )


class AssignPermissionsForm(forms.Form):
    """Form gán quyền tùy chỉnh cho user (Admin dùng)."""
    permissions = forms.ModelMultipleChoiceField(
        queryset=CustomPermission.objects.all(),
        required=False,
        help_text="Quyền tùy chỉnh, tách riêng khỏi vai trò.",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'permission-checkbox'}),
    )

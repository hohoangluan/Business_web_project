import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Role, CustomPermission, UserProfile


class RegisterForm(UserCreationForm):
    """
    Registration form collecting 7 fields:
    - Username (free input)
    - Password + confirmation (free input)
    - Full Name (no numbers or special characters)
    - Email (must contain @)
    - Phone Number (digits only)
    - Date of Birth (DD/MM/YYYY format)
    - Employee ID (must be unique)
    """

    # ----- Extra fields beyond username/password -----
    full_name = forms.CharField(
        max_length=255,
        required=True,
        help_text="Your full name. Letters and spaces only.",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., Nguyen Van A',
            'id': 'full_name',
        }),
    )
    email = forms.EmailField(
        required=True,
        help_text="Must contain @.",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., you@example.com',
            'id': 'email',
        }),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        help_text="Digits only.",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., 0901234567',
            'id': 'phone_number',
        }),
    )
    date_of_birth = forms.CharField(
        max_length=10,
        required=True,
        help_text="Format: DD/MM/YYYY.",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., 15/06/1990',
            'id': 'date_of_birth',
        }),
    )
    employee_id = forms.CharField(
        max_length=50,
        required=True,
        help_text="Must be unique. Each Employee ID can only be used once.",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., EMP001',
            'id': 'employee_id',
        }),
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2',
                  'full_name', 'email', 'phone_number',
                  'date_of_birth', 'employee_id']

    def __init__(self, *args, **kwargs):
        """Add CSS classes and placeholders to the default username/password fields."""
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Choose a username',
            'id': 'username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Choose a password',
            'id': 'password1',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirm your password',
            'id': 'password2',
        })

    # =========================================================================
    # VALIDATION METHODS
    # Each clean_<fieldname>() method validates one specific field.
    # If validation fails, it raises a ValidationError with a message.
    # =========================================================================

    def clean_full_name(self):
        """
        Full Name validation:
        - Must not contain numbers or special characters
        - Only letters, spaces, and common name characters (hyphens, apostrophes) allowed
        """
        value = self.cleaned_data.get('full_name', '').strip()
        if not value:
            raise forms.ValidationError("Full name is required.")
        # Allow letters (including Unicode/Vietnamese), spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-ZÀ-ỹ\s\-']+$", value):
            raise forms.ValidationError(
                "Full name must not contain numbers or special characters."
            )
        return value

    def clean_email(self):
        """
        Email validation:
        - Must contain "@"
        """
        value = self.cleaned_data.get('email', '').strip()
        if '@' not in value:
            raise forms.ValidationError("Email must contain '@'.")
        return value

    def clean_phone_number(self):
        """
        Phone Number validation:
        - Must contain digits only
        """
        value = self.cleaned_data.get('phone_number', '').strip()
        if not value.isdigit():
            raise forms.ValidationError("Phone number must contain digits only.")
        return value

    def clean_date_of_birth(self):
        """
        Date of Birth validation:
        - Must be in DD/MM/YYYY format
        - Basic syntax check only (not checking if the date actually exists)
        """
        value = self.cleaned_data.get('date_of_birth', '').strip()
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', value):
            raise forms.ValidationError("Date of birth must be in DD/MM/YYYY format.")
        return value

    def clean_employee_id(self):
        """
        Employee ID validation:
        - Must be unique (no other account can have the same Employee ID)
        """
        value = self.cleaned_data.get('employee_id', '').strip()
        if not value:
            raise forms.ValidationError("Employee ID is required.")
        if UserProfile.objects.filter(employee_id=value).exists():
            raise forms.ValidationError(
                "This Employee ID is already in use. Each ID can only be used once."
            )
        return value


class AssignRoleForm(forms.Form):
    """
    Form for admins to assign a ROLE to a user.
    Shows a dropdown with the 5 roles (Admin, HR, Manager, Leader, Employee).
    This is SEPARATE from permissions.
    """
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        empty_label="-- No Role --",
        help_text="Select a role for this user. Roles control what the user sees in the UI.",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'role-select'}),
    )


class AssignPermissionsForm(forms.Form):
    """
    Form for admins to assign PERMISSIONS to a user.
    Shows checkboxes for all available permissions.
    This is SEPARATE from roles.
    """
    permissions = forms.ModelMultipleChoiceField(
        queryset=CustomPermission.objects.all(),
        required=False,
        help_text="Select permissions to grant. These are independent of the user's role.",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'permission-checkbox'}),
    )


class UserChoiceField(forms.ModelChoiceField):
    """Show a friendly label instead of the raw username in dropdowns."""

    def label_from_instance(self, obj):
        profile = getattr(obj, 'profile', None)
        full_name = getattr(profile, 'full_name', '') if profile else ''
        employee_id = getattr(profile, 'employee_id', '') if profile else ''
        name = full_name or obj.username
        if employee_id:
            return f"{name} ({employee_id})"
        return name


class EmployeeProfileForm(forms.Form):
    """
    Form chỉnh toàn bộ phần dữ liệu đang lưu trong hồ sơ nhân viên.
    Phần role hệ thống vẫn để riêng để tránh nhầm giữa:
    - role của hệ thống
    - thông tin hồ sơ nhân sự, công việc và hợp đồng
    """

    full_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: Nguyen Van A',
        }),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: nguyenvana@company.vn',
        }),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: 0901234567',
        }),
    )
    date_of_birth = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: 15/06/1995',
        }),
    )
    employee_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: NV001',
        }),
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: Phòng Kinh doanh',
        }),
    )
    employee_type = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: Toan thoi gian',
        }),
    )
    position = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: Chuyên viên kinh doanh',
        }),
    )
    workplace = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: Van phong Ha Noi',
        }),
    )
    probation_start = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: 01/06/2026',
        }),
    )
    official_start_date = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: 01/08/2026',
        }),
    )
    contract_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: HD-2026-001',
        }),
    )
    contract_type = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: Thu viec 2 thang',
        }),
    )
    contract_signed_date = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: 01/05/2026',
        }),
    )
    contract_start_date = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: 05/05/2026',
        }),
    )
    contract_end_date = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: 05/05/2027',
        }),
    )
    contract_annual_leave_days = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: 12',
        }),
    )
    contract_standard_shift = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: 08:30 - 17:30 (Thu 2 den Thu 6)',
        }),
    )
    contract_attachment_reference = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: HD_NV001.pdf hoac duong link',
        }),
    )
    work_status = forms.ChoiceField(
        required=False,
        choices=[('', '-- Chưa chọn trạng thái --')] + list(UserProfile.WORK_STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    manager_user = UserChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label='-- Chưa gán quản lý --',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    leader_user = UserChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label='-- Chưa gán leader --',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(
        self,
        *args,
        manager_queryset=None,
        leader_queryset=None,
        current_user=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.current_user = current_user
        self.fields['manager_user'].queryset = manager_queryset or User.objects.none()
        self.fields['leader_user'].queryset = leader_queryset or User.objects.none()

    def clean_employee_id(self):
        """Không cho trùng mã nhân viên với user khác."""
        value = self.cleaned_data.get('employee_id', '').strip()
        if not value:
            return value

        queryset = UserProfile.objects.filter(employee_id=value)
        if self.current_user:
            queryset = queryset.exclude(user=self.current_user)

        if queryset.exists():
            raise forms.ValidationError('Mã nhân viên này đã tồn tại.')
        return value

    def clean(self):
        """Giữ rule đơn giản: công việc và hợp đồng phải đủ, cá nhân có thể để trống."""
        cleaned_data = super().clean()

        required_messages = {
            'employee_id': 'Mã nhân viên không được để trống.',
            'department': 'Phòng ban không được để trống.',
            'employee_type': 'Loại nhân viên không được để trống.',
            'position': 'Chức vụ không được để trống.',
            'workplace': 'Nơi làm việc không được để trống.',
            'probation_start': 'Ngày bắt đầu thử việc không được để trống.',
            'official_start_date': 'Ngày làm việc chính thức không được để trống.',
            'work_status': 'Trạng thái làm việc không được để trống.',
            'manager_user': 'Cần gán quản lý trực tiếp.',
            'leader_user': 'Cần gán leader phụ trách.',
            'contract_number': 'Số hợp đồng không được để trống.',
            'contract_type': 'Loại hợp đồng không được để trống.',
            'contract_signed_date': 'Ngày ký hợp đồng không được để trống.',
            'contract_start_date': 'Ngày bắt đầu hiệu lực không được để trống.',
            'contract_annual_leave_days': 'Số ngày nghỉ phép/năm không được để trống.',
            'contract_standard_shift': 'Ca làm tiêu chuẩn không được để trống.',
        }

        for field_name, error_message in required_messages.items():
            value = cleaned_data.get(field_name)
            if value in [None, '']:
                self.add_error(field_name, error_message)

        return cleaned_data

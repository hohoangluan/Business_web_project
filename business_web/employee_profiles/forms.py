"""
==============================================================================
EMPLOYEE_PROFILES FORMS
==============================================================================
Form chỉnh sửa hồ sơ nhân viên. Dùng bởi HR/Admin tại edit_work_info.
==============================================================================
"""

from django import forms
from django.contrib.auth.models import User
from accounts.models import UserProfile, Role
from employee_profiles.models import EmployeeWorkInfo
from contracts.models import ContractInfo


class UserChoiceField(forms.ModelChoiceField):
    """Hiển thị tên thân thiện trong dropdown chọn manager/leader."""

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
    Form chỉnh toàn bộ hồ sơ nhân viên:
    - Thông tin cá nhân (từ UserProfile)
    - Thông tin công việc (từ EmployeeWorkInfo)
    - Thông tin hợp đồng (từ ContractInfo)
    """

    # ----- Thông tin cá nhân (UserProfile) -----
    full_name = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Nguyen Van A'}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'VD: nguyenvana@company.vn'}),
    )
    phone_number = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 0901234567'}),
    )
    date_of_birth = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 15/06/1995'}),
    )
    # ----- Thông tin cá nhân mở rộng (PersonalInfo) -----
    gender = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Nam/Nữ'}))
    marital_status = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Độc thân'}))
    nationality = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Việt Nam'}))
    id_card_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 079123456789'}))
    id_card_issue_place = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Cục CSQLHC về TTXH'}))
    id_card_issue_date = forms.CharField(max_length=10, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 01/01/2020'}))
    permanent_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Địa chỉ thường trú'}))
    temporary_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Địa chỉ tạm trú'}))

    # ----- Người liên hệ khẩn cấp (EmergencyContact) -----
    contact_name = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ tên người liên hệ'}))
    contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'}))
    relation = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Quan hệ (VD: Vợ, Chồng, Cha, Mẹ)'}))
    contact_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Địa chỉ người liên hệ'}))

    # ----- Học vấn và Năng lực (EducationAndSkills) -----
    education_level = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Đại học, Cao đẳng'}))
    degree = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Cử nhân, Kỹ sư'}))
    major = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chuyên ngành'}))
    certificates = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Các chứng chỉ'}))
    foreign_languages = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ngoại ngữ'}))
    professional_skills = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Kỹ năng chuyên môn'}))

    employee_id = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: NV001'}),
    )

    # ----- Vai trò hệ thống (Role) -----
    role = forms.ModelChoiceField(
        queryset=Role.objects.none(), required=False,
        empty_label='-- Chưa gán vai trò --',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    # ----- Thông tin công việc (EmployeeWorkInfo) -----
    department = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Phòng Kinh doanh'}),
    )
    employee_type = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Toàn thời gian'}),
    )
    position = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Chuyên viên kinh doanh'}),
    )
    workplace = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Văn phòng Hà Nội'}),
    )
    probation_start = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 01/06/2026'}),
    )
    official_start_date = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 01/08/2026'}),
    )
    work_status = forms.ChoiceField(
        required=False,
        choices=[('', '-- Chưa chọn --')] + list(EmployeeWorkInfo.WORK_STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    manager_user = UserChoiceField(
        queryset=User.objects.none(), required=False,
        empty_label='-- Chưa gán quản lý --',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    leader_user = UserChoiceField(
        queryset=User.objects.none(), required=False,
        empty_label='-- Chưa gán leader --',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    # ----- Thông tin hợp đồng (ContractInfo) -----
    contract_number = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: HD-2026-001'}),
    )
    contract_type = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Thử việc 2 tháng'}),
    )
    contract_signed_date = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 01/05/2026'}),
    )
    contract_start_date = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 05/05/2026'}),
    )
    contract_end_date = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 05/05/2027'}),
    )
    contract_annual_leave_days = forms.IntegerField(
        required=False, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'VD: 12'}),
    )
    contract_standard_shift = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 08:30 - 17:30'}),
    )
    contract_attachment_reference = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: HD_NV001.pdf'}),
    )

    def __init__(self, *args, manager_queryset=None, leader_queryset=None,
                 current_user=None, is_admin_editor=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = current_user
        self.fields['manager_user'].queryset = manager_queryset or User.objects.none()
        self.fields['leader_user'].queryset = leader_queryset or User.objects.none()
        # Admin can assign any role; HR can assign all except Admin
        if is_admin_editor:
            self.fields['role'].queryset = Role.objects.all()
        else:
            self.fields['role'].queryset = Role.objects.exclude(name=Role.ADMIN)

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

    def clean_email(self):
        """Email có thể bỏ trống, nhưng không được trùng nếu đã nhập."""
        value = self.cleaned_data.get('email', '').strip()
        if not value:
            return ''

        user_queryset = User.objects.filter(email__iexact=value)
        if self.current_user:
            user_queryset = user_queryset.exclude(pk=self.current_user.pk)
        if user_queryset.exists():
            raise forms.ValidationError('Email này đã được sử dụng.')
        return value

    def clean(self):
        """Công việc và hợp đồng phải đủ, cá nhân có thể để trống."""
        cleaned_data = super().clean()
        # Các trường trước đây bị bắt buộc (required) trong clean()
        # Đã được gỡ bỏ để HR có thể lưu dữ liệu từng phần (như chỉ lưu số HĐ).
        required_messages = {}
        for field_name, error_message in required_messages.items():
            value = cleaned_data.get(field_name)
            if value in [None, '']:
                self.add_error(field_name, error_message)
                
        # Validate date format DD/MM/YYYY for contract dates
        import re
        date_pattern = re.compile(r'^\d{2}/\d{2}/\d{4}$')
        date_fields = ['contract_signed_date', 'contract_start_date', 'contract_end_date']
        for field_name in date_fields:
            value = cleaned_data.get(field_name)
            if value and not date_pattern.match(value.strip()):
                self.add_error(field_name, 'Định dạng ngày phải là DD/MM/YYYY.')
                
        return cleaned_data

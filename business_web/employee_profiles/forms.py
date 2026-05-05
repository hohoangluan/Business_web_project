"""
==============================================================================
EMPLOYEE_PROFILES FORMS
==============================================================================
Form chỉnh sửa hồ sơ nhân viên. Dùng bởi HR/Admin tại edit_work_info.
==============================================================================
"""

from django import forms
from django.contrib.auth.models import User
from accounts.models import UserProfile
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
    employee_id = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: NV001'}),
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
                 current_user=None, **kwargs):
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
        """Công việc và hợp đồng phải đủ, cá nhân có thể để trống."""
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

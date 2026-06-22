"""
==============================================================================
EMPLOYEE_PROFILES FORMS
==============================================================================
Form chỉnh sửa hồ sơ nhân viên. Dùng bởi HR/Admin tại edit_work_info.
==============================================================================
"""

from datetime import date

from django import forms
from django.contrib.auth.models import User
from accounts.models import UserProfile, Role
from common.validators import validate_phone_number
from contracts.services import parse_ddmmyyyy
from employee_profiles.models import EmployeeWorkInfo

EDUCATION_LEVEL_CHOICES = [
    ('', '-- Chọn trình độ --'),
    ('THPT', 'THPT'),
    ('Trung cấp', 'Trung cấp'),
    ('Cao đẳng', 'Cao đẳng'),
    ('Đại học', 'Đại học'),
    ('Thạc sĩ', 'Thạc sĩ'),
    ('Tiến sĩ', 'Tiến sĩ'),
]

MAJOR_SUGGESTIONS = [
    'Công nghệ thông tin', 'Kế toán', 'Quản trị kinh doanh', 'Marketing',
    'Tài chính - Ngân hàng', 'Kỹ thuật phần mềm', 'Khoa học máy tính',
    'Ngôn ngữ Anh', 'Luật', 'Nhân sự', 'Cơ khí', 'Điện - Điện tử',
]


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
    education_level = forms.ChoiceField(
        required=False, choices=EDUCATION_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    degree = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Cử nhân, Kỹ sư'}))
    major = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'list': 'major-suggestions',
            'placeholder': 'Gõ để tìm chuyên ngành...',
        }),
    )
    certificates = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Các chứng chỉ'}))
    foreign_languages = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ngoại ngữ'}))
    professional_skills = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Kỹ năng chuyên môn'}))

    employee_id = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: NV001'}),
    )

    # Vai trò hệ thống KHÔNG sửa ở đây — chỉ đổi qua trang phân role (hr_assign_role).

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

    def __init__(self, *args, manager_queryset=None, leader_queryset=None,
                 current_user=None, is_admin_editor=False, **kwargs):
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
        """Thông tin cá nhân có thể để trống; ràng buộc đặc thù xử lý ở từng field."""
        cleaned_data = super().clean()

        from contracts.services import validate_work_date_order
        for err in validate_work_date_order(
            cleaned_data.get('probation_start'),
            cleaned_data.get('official_start_date'),
        ):
            self.add_error('official_start_date', err)

        return cleaned_data


class PersonalEditForm(forms.Form):
    """
    Form tự chỉnh hồ sơ cá nhân của nhân viên (trang profile_view).
    Validate các field cơ bản để hiển thị lỗi từng field thay vì
    redirect âm thầm khi dữ liệu không hợp lệ (Bug #20/#21/#22).
    """

    full_name = forms.CharField(max_length=255, required=False)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.CharField(max_length=10, required=False)

    def __init__(self, *args, instance_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance_user = instance_user

    def clean_email(self):
        value = (self.cleaned_data.get('email') or '').strip()
        if not value:
            return ''
        qs = User.objects.filter(email__iexact=value)
        if self.instance_user:
            qs = qs.exclude(pk=self.instance_user.pk)
        if qs.exists():
            # Giữ thông điệp không dấu để khớp với test cũ (test_ep_prof_06_duplicate_email)
            # so sánh chuỗi thường (lowercase ASCII).
            raise forms.ValidationError('Email nay da duoc su dung.')
        return value

    def clean_phone_number(self):
        # validate_phone_number raises django.core.exceptions.ValidationError,
        # which Django forms treat the same as forms.ValidationError.
        return validate_phone_number(self.cleaned_data.get('phone_number'))

    def clean_date_of_birth(self):
        value = (self.cleaned_data.get('date_of_birth') or '').strip()
        if not value:
            return ''
        parsed = parse_ddmmyyyy(value)
        if not parsed:
            raise forms.ValidationError('Vui lòng nhập ngày sinh đúng định dạng DD/MM/YYYY.')
        if parsed > date.today():
            raise forms.ValidationError('Vui lòng nhập ngày sinh không ở tương lai.')
        return value

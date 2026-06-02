from django import forms
from django.contrib.auth.models import User
from accounts.services import is_hr_user
from common.file_validation import EVIDENCE_MIME, validate_upload
from rewards_discipline.models import RewardPenalty


class RewardPenaltyForm(forms.ModelForm):
    class Meta:
        model = RewardPenalty
        fields = ['employee', 'record_type', 'amount', 'reason_title', 'reason_detail', 'application_date', 'evidence_file']
        widgets = {
            'record_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nhập số tiền (VND)...', 'min': '0'}),
            'reason_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Đạt chỉ tiêu doanh số xuất sắc...'}),
            'reason_detail': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Nhập mô tả lý do chi tiết...', 'rows': 4, 'style': 'resize:none;'}),
            'application_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'employee': 'Nhân viên áp dụng',
            'record_type': 'Phân loại',
            'amount': 'Số tiền thưởng/phạt (VND)',
            'reason_title': 'Tiêu đề lý do',
            'reason_detail': 'Mô tả chi tiết',
            'application_date': 'Ngày áp dụng',
            'evidence_file': 'Tài liệu / Minh chứng đính kèm',
        }

    def clean_evidence_file(self):
        # Minh chứng tùy chọn → ảnh (JPG/PNG/GIF/WEBP) hoặc PDF, ≤5 MB.
        return validate_upload(
            self.cleaned_data.get('evidence_file'),
            allowed_mime=EVIDENCE_MIME,
            mime_message='Sai định dạng. Chấp nhận: ảnh hoặc PDF.',
        )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Dùng service an toàn thay vì truy cập trực tiếp user.profile
            if is_hr_user(user):
                employee_qs = User.objects.filter(is_active=True).order_by('username')
            else:
                employee_qs = User.objects.filter(
                    is_active=True,
                    work_info__leader_user=user
                ) | User.objects.filter(
                    is_active=True,
                    work_info__manager_user=user
                )
                employee_qs = employee_qs.distinct().order_by('username')

            choices = []
            for u in employee_qs:
                try:
                    fullname = u.profile.full_name if u.profile.full_name else ''
                except Exception:
                    fullname = ''
                display_label = f"{fullname} ({u.username})" if fullname else u.username
                choices.append((u.id, display_label))

            self.fields['employee'].choices = [('', '--- Chọn nhân viên ---')] + choices
            self.fields['employee'].widget.attrs.update({'class': 'form-control', 'required': 'required'})

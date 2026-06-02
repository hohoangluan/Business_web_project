"""Forms cho overtime."""
from django import forms
from django.utils import timezone

from common.file_validation import validate_upload
from overtime.models import OvertimeRequest


class OvertimeRequestForm(forms.ModelForm):
    """Form đăng ký tăng ca."""

    class Meta:
        model = OvertimeRequest
        fields = ['overtime_date', 'start_time', 'end_time', 'hours', 'reason', 'attachment']
        widgets = {
            'overtime_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                },
            ),
            'start_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control',
                },
            ),
            'end_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control',
                },
            ),
            'hours': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.5',
                    'min': '0.5',
                    'max': '8',
                    'placeholder': 'VD: 2.5',
                },
            ),
            'reason': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Nhập lý do tăng ca...',
                    'style': 'resize: none;',
                },
            ),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'overtime_date': 'Ngày tăng ca',
            'start_time': 'Giờ bắt đầu',
            'end_time': 'Giờ kết thúc',
            'hours': 'Số giờ',
            'reason': 'Lý do',
            'attachment': 'Tệp minh chứng (nếu có)',
        }

    def clean_attachment(self):
        # Minh chứng tùy chọn → validator dùng chung (5 MB + PDF/JPG/PNG).
        return validate_upload(self.cleaned_data.get('attachment'))

    def clean_overtime_date(self):
        """Ngày tăng ca không được ở quá khứ quá xa (> 30 ngày trước)."""
        date = self.cleaned_data.get('overtime_date')
        if date:
            today = timezone.localdate()
            diff = (today - date).days
            if diff > 30:
                raise forms.ValidationError(
                    'Ngày tăng ca không được quá 30 ngày trước.'
                )
        return date

    def clean_hours(self):
        """Số giờ phải > 0 và ≤ 8."""
        hours = self.cleaned_data.get('hours')
        if hours is not None:
            if hours <= 0:
                raise forms.ValidationError('Số giờ phải lớn hơn 0.')
            if hours > 8:
                raise forms.ValidationError('Số giờ tăng ca tối đa là 8 giờ.')
        return hours

    def clean(self):
        """Giờ kết thúc phải sau giờ bắt đầu."""
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        if start and end and end <= start:
            self.add_error(
                'end_time', 'Giờ kết thúc phải sau giờ bắt đầu.'
            )
        return cleaned

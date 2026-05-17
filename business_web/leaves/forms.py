"""Forms cho leaves — đăng ký nghỉ phép."""

from datetime import timedelta

from django import forms
from django.utils import timezone

from leaves.models import LeaveRequest


class LeaveRequestForm(forms.ModelForm):
    """
    Form đăng ký nghỉ phép.
    Validation: ngày bắt đầu >= hôm nay, ngày kết thúc >= ngày bắt đầu,
    số ngày tự tính.
    """

    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_leave_type',
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_start_date',
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_end_date',
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Nhập lý do nghỉ phép...',
                'id': 'id_reason',
                'style': 'resize: none;',
            }),
        }
        labels = {
            'leave_type': 'Loại nghỉ phép',
            'start_date': 'Từ ngày',
            'end_date': 'Đến ngày',
            'reason': 'Lý do',
        }

    def clean_start_date(self):
        """Ngày bắt đầu không được quá 7 ngày trong quá khứ."""
        start = self.cleaned_data['start_date']
        today = timezone.localdate()
        if start < today - timedelta(days=7):
            raise forms.ValidationError('Ngày bắt đầu không thể quá xa trong quá khứ.')
        return start

    def clean(self):
        """Ngày kết thúc phải >= ngày bắt đầu."""
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end:
            if end < start:
                self.add_error('end_date', 'Ngày kết thúc phải từ ngày bắt đầu trở đi.')
        return cleaned

"""Form HR cấu hình giờ làm chuẩn toàn công ty."""
from django import forms

from attendance.models import WorkScheduleConfig


class WorkScheduleConfigForm(forms.ModelForm):
    class Meta:
        model = WorkScheduleConfig
        fields = ['shift_start', 'shift_end', 'late_grace_minutes']
        widgets = {
            'shift_start': forms.TimeInput(
                attrs={'type': 'time', 'class': 'st-input',
                       'style': 'width: 120px; display: inline-block;'},
                format='%H:%M',
            ),
            'shift_end': forms.TimeInput(
                attrs={'type': 'time', 'class': 'st-input',
                       'style': 'width: 120px; display: inline-block;'},
                format='%H:%M',
            ),
            'late_grace_minutes': forms.NumberInput(
                attrs={'min': 0, 'class': 'st-input',
                       'style': 'width: 100px; display: inline-block;'},
            ),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('shift_start')
        end = cleaned.get('shift_end')
        if start and end and end <= start:
            self.add_error('shift_end', 'Giờ kết thúc phải sau giờ bắt đầu.')
        return cleaned

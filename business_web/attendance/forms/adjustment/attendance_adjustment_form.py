"""ModelForm for AttendanceAdjustmentRequest with evidence + time validation."""
from django import forms

from attendance.models import AttendanceAdjustmentRequest

MAX_EVIDENCE_BYTES = 5 * 1024 * 1024
ALLOWED_EVIDENCE_MIME = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf',
}


class AttendanceAdjustmentForm(forms.ModelForm):
    class Meta:
        model = AttendanceAdjustmentRequest
        fields = [
            'reason', 'reason_detail',
            'claimed_check_in_time', 'claimed_check_out_time', 'evidence',
        ]
        widgets = {
            'reason_detail': forms.Textarea(attrs={'rows': 3}),
            'claimed_check_in_time': forms.TimeInput(attrs={'type': 'time'}),
            'claimed_check_out_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_evidence(self):
        f = self.cleaned_data.get('evidence')
        if not f:
            raise forms.ValidationError(
                'Phải đính kèm minh chứng (ảnh hoặc PDF).'
            )
        if f.size > MAX_EVIDENCE_BYTES:
            raise forms.ValidationError('Chứng từ tối đa 5 MB.')
        content_type = getattr(f, 'content_type', '') or ''
        if content_type not in ALLOWED_EVIDENCE_MIME:
            raise forms.ValidationError(
                'Sai định dạng. Chấp nhận: ảnh (JPG/PNG/GIF/WEBP) hoặc PDF.'
            )
        return f

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('claimed_check_in_time') and not cleaned.get('claimed_check_out_time'):
            raise forms.ValidationError(
                'Phải khai báo ít nhất giờ vào hoặc giờ ra.'
            )
        return cleaned

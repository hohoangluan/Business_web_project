"""ModelForm for AttendanceAdjustmentRequest with evidence + time validation."""
from django import forms

from attendance.models import AttendanceAdjustmentRequest
from common.file_validation import EVIDENCE_MIME, validate_upload


class AttendanceAdjustmentForm(forms.ModelForm):
    class Meta:
        model = AttendanceAdjustmentRequest
        fields = [
            'reason', 'reason_detail',
            'claimed_check_in_time', 'claimed_check_out_time', 'evidence',
        ]
        widgets = {
            'reason': forms.Select(attrs={'class': 'adj-input'}),
            'reason_detail': forms.Textarea(attrs={'rows': 3, 'class': 'adj-input', 'placeholder': 'Mô tả thêm cho HR (tùy chọn)...'}),
            'claimed_check_in_time': forms.TimeInput(attrs={'type': 'time', 'class': 'adj-input adj-time'}),
            'claimed_check_out_time': forms.TimeInput(attrs={'type': 'time', 'class': 'adj-input adj-time'}),
            'evidence': forms.ClearableFileInput(attrs={'class': 'adj-file', 'accept': 'image/*,application/pdf'}),
        }

    def clean_evidence(self):
        # Minh chứng BẮT BUỘC; chấp nhận ảnh (JPG/PNG/GIF/WEBP) hoặc PDF, ≤5 MB.
        return validate_upload(
            self.cleaned_data.get('evidence'),
            required=True,
            allowed_mime=EVIDENCE_MIME,
            required_message='Phải đính kèm minh chứng (ảnh hoặc PDF).',
            mime_message='Sai định dạng. Chấp nhận: ảnh (JPG/PNG/GIF/WEBP) hoặc PDF.',
        )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('claimed_check_in_time') and not cleaned.get('claimed_check_out_time'):
            raise forms.ValidationError(
                'Phải khai báo ít nhất giờ vào hoặc giờ ra.'
            )
        return cleaned

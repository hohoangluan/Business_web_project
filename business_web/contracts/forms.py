"""Forms cho contracts."""
import re

from django import forms

from accounts.models import CompanyConfiguration

from contracts.services import normalize_date_string, validate_contract_date_order

WEEKDAY_CHOICES = [
    ('', '-- Chọn thứ --'),
    ('Thứ 2', 'Thứ 2'),
    ('Thứ 3', 'Thứ 3'),
    ('Thứ 4', 'Thứ 4'),
    ('Thứ 5', 'Thứ 5'),
    ('Thứ 6', 'Thứ 6'),
    ('Thứ 7', 'Thứ 7'),
    ('Chủ nhật', 'Chủ nhật'),
]

CONTRACT_TYPE_FALLBACK = [
    ('', '-- Chọn loại hợp đồng --'),
    ('Thử việc', 'Thử việc'),
    ('Xác định thời hạn', 'Xác định thời hạn'),
    ('Không xác định thời hạn', 'Không xác định thời hạn'),
    ('Thời vụ', 'Thời vụ'),
]


def configured_contract_type_choices(selected_value=None):
    """Build contract type choices from Admin company config."""

    try:
        choices = CompanyConfiguration.get_solo().choices_for('contract_types', '-- Chọn loại hợp đồng --')
    except Exception:
        choices = list(CONTRACT_TYPE_FALLBACK)

    selected_value = (selected_value or '').strip()
    values = {value for value, _ in choices}
    if selected_value and selected_value not in values:
        choices.append((selected_value, selected_value))
    return choices
class ContractAdjustForm(forms.Form):
    """Form điều chỉnh hợp đồng — chỉ field HĐ. Mỗi lần lưu = 1 phiên bản mới."""

    contract_number = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: HD-2026-001'}),
    )
    contract_type = forms.ChoiceField(
        required=False,
        choices=CONTRACT_TYPE_FALLBACK,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    contract_signed_date = forms.CharField(
        max_length=10, required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    contract_start_date = forms.CharField(
        max_length=10, required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    contract_end_date = forms.CharField(
        max_length=10, required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    contract_annual_leave_days = forms.IntegerField(
        required=False, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'VD: 12'}),
    )
    contract_standard_shift = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: 08:30 - 17:30'}),
    )
    shift_start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    shift_end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    shift_start_day = forms.ChoiceField(
        required=False, choices=WEEKDAY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    shift_end_day = forms.ChoiceField(
        required=False, choices=WEEKDAY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    contract_attachment_reference = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên file/link nếu lưu ngoài hệ thống'}),
    )
    contract_attachment_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,image/*'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected_value = self.data.get('contract_type') if self.is_bound else self.initial.get('contract_type')
        self.fields['contract_type'].choices = configured_contract_type_choices(selected_value)
    def clean(self):
        cleaned_data = super().clean()

        date_fields = ['contract_signed_date', 'contract_start_date', 'contract_end_date']
        bad_format = False
        for field_name in date_fields:
            value = cleaned_data.get(field_name)
            if value:
                normalized = normalize_date_string(value)
                if normalized == value and not re.match(r'^\d{2}/\d{2}/\d{4}$', value.strip()):
                    self.add_error(field_name, 'Định dạng ngày không hợp lệ.')
                    bad_format = True
                else:
                    cleaned_data[field_name] = normalized

        if not bad_format:
            order_errors = validate_contract_date_order(
                cleaned_data.get('contract_signed_date'),
                cleaned_data.get('contract_start_date'),
                cleaned_data.get('contract_end_date'),
            )
            for err in order_errors:
                if 'phải từ ngày ký' in err:
                    self.add_error('contract_start_date', err)
                elif 'sau ngày bắt đầu' in err:
                    self.add_error('contract_end_date', err)

        # Giờ ca: nếu điền cả 2 thì giờ kết thúc phải sau giờ bắt đầu (đồng bộ chấm công).
        shift_start = cleaned_data.get('shift_start_time')
        shift_end = cleaned_data.get('shift_end_time')
        if shift_start and shift_end and shift_end <= shift_start:
            self.add_error('shift_end_time', 'Giờ kết thúc ca phải sau giờ bắt đầu ca.')

        return cleaned_data

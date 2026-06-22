"""Forms cho contracts."""
import re

from django import forms

from contracts.services import validate_contract_date_order


class ContractAdjustForm(forms.Form):
    """Form điều chỉnh hợp đồng — chỉ field HĐ. Mỗi lần lưu = 1 phiên bản mới."""

    contract_number = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: HD-2026-001'}),
    )
    contract_type = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Chính thức 1 năm'}),
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
    shift_start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    shift_end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    contract_attachment_reference = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: HD_NV001.pdf'}),
    )

    def clean(self):
        cleaned_data = super().clean()

        date_pattern = re.compile(r'^\d{2}/\d{2}/\d{4}$')
        date_fields = ['contract_signed_date', 'contract_start_date', 'contract_end_date']
        bad_format = False
        for field_name in date_fields:
            value = cleaned_data.get(field_name)
            if value and not date_pattern.match(value.strip()):
                self.add_error(field_name, 'Định dạng ngày phải là DD/MM/YYYY.')
                bad_format = True

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

"""Forms for Admin-managed company settings."""

from django import forms

from accounts.models import CompanyConfiguration


class CompanyConfigurationForm(forms.ModelForm):
    """Edit company catalogs and reward/penalty policies from Settings."""

    class Meta:
        model = CompanyConfiguration
        fields = [
            "workplaces",
            "contract_types",
            "reward_policy",
            "penalty_policy",
            "departments",
            "positions",
        ]
        labels = {
            "workplaces": "Nơi làm việc",
            "contract_types": "Loại hợp đồng lao động",
            "reward_policy": "Cơ chế khen thưởng",
            "penalty_policy": "Cơ chế xử phạt",
            "departments": "Phòng ban",
            "positions": "Chức vụ",
        }
        help_texts = {
            "workplaces": "Mỗi dòng là một nơi làm việc.",
            "contract_types": "Mỗi dòng là một loại hợp đồng.",
            "departments": "Mỗi dòng là một phòng ban.",
            "positions": "Mỗi dòng là một chức vụ.",
        }
        widgets = {
            "workplaces": forms.Textarea(attrs={"class": "company-config-source", "rows": 5}),
            "contract_types": forms.Textarea(attrs={"class": "company-config-source", "rows": 5}),
            "reward_policy": forms.Textarea(attrs={"class": "company-config-source", "rows": 6}),
            "penalty_policy": forms.Textarea(attrs={"class": "company-config-source", "rows": 6}),
            "departments": forms.Textarea(attrs={"class": "company-config-source", "rows": 5}),
            "positions": forms.Textarea(attrs={"class": "company-config-source", "rows": 5}),
        }

    def clean(self):
        cleaned_data = super().clean()
        required_list_fields = {
            "workplaces": "Vui lòng nhập ít nhất một nơi làm việc.",
            "contract_types": "Vui lòng nhập ít nhất một loại hợp đồng.",
            "departments": "Vui lòng nhập ít nhất một phòng ban.",
            "positions": "Vui lòng nhập ít nhất một chức vụ.",
        }

        for field_name, message in required_list_fields.items():
            normalized = self._normalize_lines(cleaned_data.get(field_name, ""))
            if not normalized:
                self.add_error(field_name, message)
            else:
                cleaned_data[field_name] = normalized

        for field_name in ("reward_policy", "penalty_policy"):
            cleaned_data[field_name] = (cleaned_data.get(field_name) or "").strip()

        return cleaned_data

    @staticmethod
    def _normalize_lines(value):
        seen = set()
        lines = []
        for raw in (value or "").splitlines():
            item = raw.strip()
            key = item.casefold()
            if item and key not in seen:
                seen.add(key)
                lines.append(item)
        return "\n".join(lines)

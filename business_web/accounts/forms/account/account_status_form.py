"""Forms for account status actions."""

from django import forms


class AccountStatusForm(forms.Form):
    """Small placeholder form for future account status workflows."""

    is_active = forms.BooleanField(required=False)

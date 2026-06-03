"""Account update and permission assignment forms."""

from django import forms

from accounts.models import CustomPermission, Role


class AccountUpdateForm(forms.Form):
    """Placeholder form for future account update workflows."""

    full_name = forms.CharField(max_length=255, required=False)
    phone_number = forms.CharField(max_length=20, required=False)


class AssignPermissionsForm(forms.Form):
    """Form used by admins to assign custom permissions to a user."""

    permissions = forms.ModelMultipleChoiceField(
        queryset=CustomPermission.objects.all(),
        required=False,
        help_text="Quyen tuy chinh, tach rieng khoi vai tro.",
        widget=forms.CheckboxSelectMultiple(attrs={"class": "permission-checkbox"}),
    )

import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Role, CustomPermission, UserProfile


class RegisterForm(UserCreationForm):
    """
    Registration form collecting 7 fields:
    - Username (free input)
    - Password + confirmation (free input)
    - Full Name (no numbers or special characters)
    - Email (must contain @)
    - Phone Number (digits only)
    - Date of Birth (DD/MM/YYYY format)
    - Employee ID (must be unique)
    """

    # ----- Extra fields beyond username/password -----
    full_name = forms.CharField(
        max_length=255,
        required=True,
        help_text="Your full name. Letters and spaces only.",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., Nguyen Van A',
            'id': 'full_name',
        }),
    )
    email = forms.EmailField(
        required=True,
        help_text="Must contain @.",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., you@example.com',
            'id': 'email',
        }),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        help_text="Digits only.",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., 0901234567',
            'id': 'phone_number',
        }),
    )
    date_of_birth = forms.CharField(
        max_length=10,
        required=True,
        help_text="Format: DD/MM/YYYY.",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., 15/06/1990',
            'id': 'date_of_birth',
        }),
    )
    employee_id = forms.CharField(
        max_length=50,
        required=True,
        help_text="Must be unique. Each Employee ID can only be used once.",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., EMP001',
            'id': 'employee_id',
        }),
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2',
                  'full_name', 'email', 'phone_number',
                  'date_of_birth', 'employee_id']

    def __init__(self, *args, **kwargs):
        """Add CSS classes and placeholders to the default username/password fields."""
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Choose a username',
            'id': 'username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Choose a password',
            'id': 'password1',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirm your password',
            'id': 'password2',
        })

    # =========================================================================
    # VALIDATION METHODS
    # Each clean_<fieldname>() method validates one specific field.
    # If validation fails, it raises a ValidationError with a message.
    # =========================================================================

    def clean_full_name(self):
        """
        Full Name validation:
        - Must not contain numbers or special characters
        - Only letters, spaces, and common name characters (hyphens, apostrophes) allowed
        """
        value = self.cleaned_data.get('full_name', '').strip()
        if not value:
            raise forms.ValidationError("Full name is required.")
        # Allow letters (including Unicode/Vietnamese), spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-ZÀ-ỹ\s\-']+$", value):
            raise forms.ValidationError(
                "Full name must not contain numbers or special characters."
            )
        return value

    def clean_email(self):
        """
        Email validation:
        - Must contain "@"
        """
        value = self.cleaned_data.get('email', '').strip()
        if '@' not in value:
            raise forms.ValidationError("Email must contain '@'.")
        return value

    def clean_phone_number(self):
        """
        Phone Number validation:
        - Must contain digits only
        """
        value = self.cleaned_data.get('phone_number', '').strip()
        if not value.isdigit():
            raise forms.ValidationError("Phone number must contain digits only.")
        return value

    def clean_date_of_birth(self):
        """
        Date of Birth validation:
        - Must be in DD/MM/YYYY format
        - Basic syntax check only (not checking if the date actually exists)
        """
        value = self.cleaned_data.get('date_of_birth', '').strip()
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', value):
            raise forms.ValidationError("Date of birth must be in DD/MM/YYYY format.")
        return value

    def clean_employee_id(self):
        """
        Employee ID validation:
        - Must be unique (no other account can have the same Employee ID)
        """
        value = self.cleaned_data.get('employee_id', '').strip()
        if not value:
            raise forms.ValidationError("Employee ID is required.")
        if UserProfile.objects.filter(employee_id=value).exists():
            raise forms.ValidationError(
                "This Employee ID is already in use. Each ID can only be used once."
            )
        return value


class AssignRoleForm(forms.Form):
    """
    Form for admins to assign a ROLE to a user.
    Shows a dropdown with the 5 roles (Admin, HR, Manager, Leader, Employee).
    This is SEPARATE from permissions.
    """
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        empty_label="-- No Role --",
        help_text="Select a role for this user. Roles control what the user sees in the UI.",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'role-select'}),
    )


class AssignPermissionsForm(forms.Form):
    """
    Form for admins to assign PERMISSIONS to a user.
    Shows checkboxes for all available permissions.
    This is SEPARATE from roles.
    """
    permissions = forms.ModelMultipleChoiceField(
        queryset=CustomPermission.objects.all(),
        required=False,
        help_text="Select permissions to grant. These are independent of the user's role.",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'permission-checkbox'}),
    )
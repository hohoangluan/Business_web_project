from django.db import models
from django.contrib.auth.models import User


class Role(models.Model):
    """
    Represents a user's job role in the system.
    There are 4 predefined roles: Master, Manager, Leader, Employee.
    Each role determines what the user sees in the UI (menus, pages, etc.).
    """
    MASTER = 'master'
    MANAGER = 'manager'
    LEADER = 'leader'
    EMPLOYEE = 'employee'

    ROLE_CHOICES = [
        (MASTER, 'Master'),
        (MANAGER, 'Manager'),
        (LEADER, 'Leader'),
        (EMPLOYEE, 'Employee'),
    ]

    name = models.CharField(
        max_length=50,
        unique=True,
        choices=ROLE_CHOICES,
        help_text="The role name (e.g., 'master', 'manager')."
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="A human-readable description of what this role does."
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        ordering = ['name']


class CustomPermission(models.Model):
    """
    A specific ability that can be granted to any user, independent of their role.
    Examples: 'can_export_reports', 'can_approve_leave', 'can_view_analytics'.

    This is SEPARATE from the Role system — assigning a permission does NOT
    change a user's role, and changing a role does NOT affect permissions.
    """
    codename = models.CharField(
        max_length=100,
        unique=True,
        help_text="A short code for this permission (e.g., 'can_export_reports')."
    )
    name = models.CharField(
        max_length=255,
        help_text="A human-readable name (e.g., 'Can Export Reports')."
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="Explains what this permission allows the user to do."
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class UserProfile(models.Model):
    """
    Extends Django's built-in User model with:
    - A role (one role per user, e.g., 'Employee')
    - Custom permissions (zero or more, independent of the role)
    - Registration info: full name, phone, date of birth, employee ID

    The OneToOneField means each User has exactly ONE UserProfile,
    and each UserProfile belongs to exactly ONE User.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text="The Django user this profile belongs to."
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="The user's role. Determines UI behavior."
    )
    permissions = models.ManyToManyField(
        CustomPermission,
        blank=True,
        related_name='users',
        help_text="Custom permissions assigned to this user, independent of role."
    )

    # ----- Registration fields -----
    full_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="User's full name (no numbers or special characters)."
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Phone number (digits only)."
    )
    date_of_birth = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Date of birth in DD/MM/YYYY format."
    )
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique employee ID. Each ID can only be used for one account."
    )

    def __str__(self):
        role_name = self.role.get_name_display() if self.role else 'No Role'
        return f"{self.user.username} ({role_name})"

    def has_custom_permission(self, codename):
        """
        Check if this user has a specific custom permission.
        Usage: request.user.profile.has_custom_permission('can_export_reports')
        """
        return self.permissions.filter(codename=codename).exists()

    def is_master(self):
        """Returns True if the user has the Master role."""
        return self.role and self.role.name == Role.MASTER

    class Meta:
        ordering = ['user__username']

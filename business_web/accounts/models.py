from django.db import models
from django.contrib.auth.models import User


class Role(models.Model):
    """
    Represents a user's job role in the system.
    There are 5 predefined roles: Admin, HR, Manager, Leader, Employee.
    Each role determines what the user sees in the UI (menus, pages, etc.).
    """
    ADMIN = 'admin'
    HR = 'hr'
    MANAGER = 'manager'
    LEADER = 'leader'
    EMPLOYEE = 'employee'

    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (HR, 'HR'),
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
    employee_type = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Employee type such as Full-time, Part-time or Intern."
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Department or business unit managed by HR/Admin."
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Job title managed by HR/Admin."
    )
    workplace = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Main workplace or office location."
    )
    probation_start = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Probation start date in DD/MM/YYYY format."
    )
    official_start_date = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Official working date in DD/MM/YYYY format."
    )
    WORKING = 'working'
    PROBATION = 'probation'
    PAUSED = 'paused'
    RESIGNED = 'resigned'
    WORK_STATUS_CHOICES = [
        (WORKING, 'Đang làm việc'),
        (PROBATION, 'Đang thử việc'),
        (PAUSED, 'Tạm nghỉ'),
        (RESIGNED, 'Đã nghỉ việc'),
    ]
    work_status = models.CharField(
        max_length=30,
        blank=True,
        default='',
        choices=WORK_STATUS_CHOICES,
        help_text="Current working status managed by HR/Admin."
    )
    contract_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Current contract number managed by HR/Admin."
    )
    contract_type = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Current contract type such as probation or official contract."
    )
    contract_signed_date = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Contract signed date in DD/MM/YYYY format."
    )
    contract_start_date = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Contract effective start date in DD/MM/YYYY format."
    )
    contract_end_date = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Contract end date in DD/MM/YYYY format. Leave blank for open-ended contracts."
    )
    contract_annual_leave_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Annual leave days defined in the current contract."
    )
    contract_standard_shift = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Standard shift described in the current contract."
    )
    contract_attachment_reference = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="File name or link reference for the current contract attachment."
    )
    manager_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_team_members',
        help_text="Direct manager of this employee."
    )
    leader_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_team_members',
        help_text="Direct leader of this employee."
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

    def is_admin(self):
        """Returns True if the user has the Admin role."""
        return self.role and self.role.name == Role.ADMIN

    class Meta:
        ordering = ['user__username']

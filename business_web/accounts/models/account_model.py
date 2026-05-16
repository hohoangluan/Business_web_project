"""Account profile model for accounts."""

from django.contrib.auth.models import User
from django.db import models

from accounts.models.permission_model import CustomPermission
from accounts.models.role_model import Role


class UserProfile(models.Model):
    """Account profile that links a Django user to an employee ID."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        help_text="Django user that owns this profile.",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        help_text="System role used for interface and access control.",
    )
    permissions = models.ManyToManyField(
        CustomPermission,
        blank=True,
        related_name="users",
        help_text="Custom permissions assigned independently from role.",
    )
    full_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default="",
        help_text="Full name from registration.",
    )
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique employee ID.",
    )

    def __str__(self):
        role_name = self.role.get_name_display() if self.role else "No Role"
        return f"{self.user.username} ({role_name})"

    def has_custom_permission(self, codename):
        """Return whether this profile has the given custom permission."""

        return self.permissions.filter(codename=codename).exists()

    def get_role_name(self):
        """Return the assigned role name."""

        return self.role.name if self.role else "No Role"

    class Meta:
        ordering = ["user__username"]

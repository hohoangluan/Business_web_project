"""Role model for accounts."""

from django.db import models


class Role(models.Model):
    """System role assigned to a user profile."""

    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    LEADER = "leader"
    EMPLOYEE = "employee"

    ROLE_CHOICES = [
        (ADMIN, "Admin"),
        (HR, "HR"),
        (MANAGER, "Manager"),
        (LEADER, "Leader"),
        (EMPLOYEE, "Employee"),
    ]

    name = models.CharField(
        max_length=50,
        unique=True,
        choices=ROLE_CHOICES,
        help_text="Tên vai trò (VD: 'admin', 'manager').",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Mô tả vai trò này làm gì.",
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        ordering = ["name"]

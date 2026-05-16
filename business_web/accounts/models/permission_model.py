"""Custom permission model for accounts."""

from django.db import models


class CustomPermission(models.Model):
    """Custom permission that can be assigned independently of roles."""

    codename = models.CharField(
        max_length=100,
        unique=True,
        help_text="Mã quyền (VD: 'can_export_reports').",
    )
    name = models.CharField(
        max_length=255,
        help_text="Tên hiển thị (VD: 'Xuất báo cáo').",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Giải thích quyền này cho phép làm gì.",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

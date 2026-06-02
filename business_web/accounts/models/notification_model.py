"""Notification model for system notifications."""

from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    """Stores system notifications for users."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Người dùng"
    )
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    message = models.TextField(verbose_name="Nội dung")
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name="Liên kết")
    is_read = models.BooleanField(default=False, verbose_name="Đã đọc")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Thông báo"
        verbose_name_plural = "Thông báo"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

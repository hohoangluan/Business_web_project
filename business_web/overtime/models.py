"""
==============================================================================
OVERTIME MODELS
==============================================================================
Model tăng ca — hiện là placeholder cho tương lai.
==============================================================================
"""

from django.db import models
from django.contrib.auth.models import User


class OvertimeRequest(models.Model):
    """
    Đơn đăng ký tăng ca.
    Placeholder — sẽ được bổ sung khi xây dựng backend tăng ca thật.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='overtime_requests',
        help_text="Nhân viên đăng ký tăng ca.",
    )
    overtime_date = models.DateField(
        help_text="Ngày tăng ca.",
    )
    hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text="Số giờ tăng ca.",
    )
    reason = models.TextField(
        blank=True,
        default='',
        help_text="Lý do tăng ca.",
    )
    status = models.CharField(
        max_length=20,
        default='pending',
        help_text="Trạng thái: pending, approved, rejected.",
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_overtimes',
        help_text="Người phê duyệt.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.overtime_date} ({self.hours}h)"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Đơn tăng ca'
        verbose_name_plural = 'Đơn tăng ca'

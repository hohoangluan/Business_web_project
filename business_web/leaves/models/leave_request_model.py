from django.db import models
from django.contrib.auth.models import User

class LeaveRequest(models.Model):
    """
    Đơn xin nghỉ phép của nhân viên.
    Placeholder — sẽ được bổ sung khi xây dựng backend nghỉ phép thật.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        help_text="Nhân viên gửi đơn nghỉ phép.",
    )
    leave_type = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Loại nghỉ: phép năm, ốm, việc riêng...",
    )
    start_date = models.DateField(
        help_text="Ngày bắt đầu nghỉ.",
    )
    end_date = models.DateField(
        help_text="Ngày kết thúc nghỉ.",
    )
    reason = models.TextField(
        blank=True,
        default='',
        help_text="Lý do nghỉ phép.",
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
        related_name='approved_leaves',
        help_text="Người phê duyệt.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.start_date} đến {self.end_date}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Đơn nghỉ phép'
        verbose_name_plural = 'Đơn nghỉ phép'

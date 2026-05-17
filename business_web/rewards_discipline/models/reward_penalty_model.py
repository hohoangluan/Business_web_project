from django.db import models
from django.contrib.auth.models import User

class RewardPenalty(models.Model):
    """
    Phiếu khen thưởng hoặc xử phạt.
    Placeholder — sẽ được bổ sung khi xây dựng backend thật.
    """

    REWARD = 'reward'
    PENALTY = 'penalty'
    TYPE_CHOICES = [
        (REWARD, 'Khen thưởng'),
        (PENALTY, 'Xử phạt'),
    ]

    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rewards_penalties',
        help_text="Nhân viên được thưởng/phạt.",
    )
    record_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        help_text="Loại: khen thưởng hay xử phạt.",
    )
    amount = models.PositiveIntegerField(
        default=0,
        help_text="Số tiền thưởng/phạt (VND).",
    )
    reason_title = models.CharField(
        max_length=255,
        help_text="Tiêu đề lý do.",
    )
    reason_detail = models.TextField(
        blank=True,
        default='',
        help_text="Chi tiết lý do.",
    )
    proposer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposed_rewards_penalties',
        help_text="Người đề xuất.",
    )
    status = models.CharField(
        max_length=20,
        default='pending',
        help_text="Trạng thái: pending, approved, rejected.",
    )
    application_date = models.DateField(
        help_text="Ngày áp dụng.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_record_type_display()}: {self.employee.username} - {self.reason_title}"

    class Meta:
        ordering = ['-application_date']
        verbose_name = 'Khen thưởng / Xử phạt'
        verbose_name_plural = 'Khen thưởng / Xử phạt'

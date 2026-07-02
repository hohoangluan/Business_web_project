import os
from django.db import models
from django.contrib.auth.models import User

class RewardPenalty(models.Model):
    """
    Phiếu khen thưởng hoặc xử phạt.
    """

    REWARD = 'reward'
    PENALTY = 'penalty'
    TYPE_CHOICES = [
        (REWARD, 'Khen thưởng'),
        (PENALTY, 'Xử phạt'),
    ]

    # ----- Trạng thái duyệt HR -----
    PENDING = 'pending'                  # chờ HR duyệt
    LEADER_APPROVED = 'leader_approved'  # legacy: không dùng cho phiếu mới
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Chờ HR duyệt'),
        (LEADER_APPROVED, 'Chờ HR duyệt'),
        (APPROVED, 'Đã duyệt'),
        (REJECTED, 'Từ chối'),
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
        default=PENDING,
        help_text="Trạng thái duyệt: pending → approved / rejected.",
    )
    leader_approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reward_l1_approved',
        help_text="Manager duyệt cấp 1 (nếu Leader lập phiếu).",
    )
    leader_approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reward_l2_approved',
        help_text="HR duyệt cấp 2 (cuối).",
    )
    application_date = models.DateField(
        help_text="Ngày áp dụng.",
    )
    evidence_file = models.FileField(
        upload_to='reward_evidence/',
        null=True,
        blank=True,
        help_text="Tài liệu/File minh chứng đính kèm.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def evidence_filename(self):
        if self.evidence_file:
            return os.path.basename(self.evidence_file.name)
        return ""

    def __str__(self):
        return f"{self.get_record_type_display()}: {self.employee.username} - {self.reason_title}"

    class Meta:
        ordering = ['-application_date']
        verbose_name = 'Khen thưởng / Xử phạt'
        verbose_name_plural = 'Khen thưởng / Xử phạt'

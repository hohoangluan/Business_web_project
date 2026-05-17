from django.db import models
from django.contrib.auth.models import User

class Evaluation(models.Model):
    """
    Bản đánh giá nhân viên do Manager/Leader tạo.
    Placeholder — sẽ được bổ sung khi xây dựng backend đánh giá thật.
    """

    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evaluations_received',
        help_text="Nhân viên được đánh giá.",
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evaluations_given',
        help_text="Người thực hiện đánh giá (Manager/Leader).",
    )
    evaluation_date = models.DateField(
        help_text="Ngày đánh giá.",
    )
    content = models.TextField(
        help_text="Nội dung đánh giá.",
    )
    evidence_reference = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="File minh chứng hoặc link tham chiếu.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.username} đánh giá bởi {self.reviewer.username} ({self.evaluation_date})"

    class Meta:
        ordering = ['-evaluation_date']
        verbose_name = 'Đánh giá nhân viên'
        verbose_name_plural = 'Đánh giá nhân viên'

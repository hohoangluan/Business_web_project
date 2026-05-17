from django.db import models
from django.contrib.auth.models import User

class Report(models.Model):
    """
    Báo cáo cá nhân của nhân viên gửi lên quản lý.
    Placeholder — sẽ được bổ sung khi xây dựng backend thật.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_sent',
        help_text="Người gửi báo cáo.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Tiêu đề báo cáo.",
    )
    content = models.TextField(
        help_text="Nội dung báo cáo.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Báo cáo: {self.title} ({self.author.username})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Báo cáo'
        verbose_name_plural = 'Báo cáo'

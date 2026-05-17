from django.db import models
from django.contrib.auth.models import User

class Ticket(models.Model):
    """
    Ticket hỗ trợ & khiếu nại.
    Placeholder — sẽ được bổ sung khi xây dựng backend thật.
    """

    SUPPORT = 'support'
    COMPLAINT = 'complaint'
    TYPE_CHOICES = [
        (SUPPORT, 'Hỗ trợ'),
        (COMPLAINT, 'Khiếu nại'),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets',
        help_text="Người tạo ticket.",
    )
    ticket_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=SUPPORT,
        help_text="Loại: hỗ trợ hay khiếu nại.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Tiêu đề ticket.",
    )
    content = models.TextField(
        help_text="Nội dung chi tiết.",
    )
    status = models.CharField(
        max_length=20,
        default='open',
        help_text="Trạng thái: open, processing, closed.",
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        help_text="Người xử lý ticket.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket: {self.title} ({self.author.username})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'

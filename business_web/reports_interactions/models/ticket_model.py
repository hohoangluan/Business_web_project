from django.db import models
from django.contrib.auth.models import User

class Ticket(models.Model):
    """
    Ticket hỗ trợ & khiếu nại.
    """

    SUPPORT = 'support'
    COMPLAINT = 'complaint'
    TYPE_CHOICES = [
        (SUPPORT, 'Hỗ trợ'),
        (COMPLAINT, 'Khiếu nại'),
    ]

    STATUS_NEW = 'new'
    STATUS_PROCESSING = 'processing'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_NEW, 'Mới'),
        (STATUS_PROCESSING, 'Đang xử lý'),
        (STATUS_RESOLVED, 'Đã giải quyết'),
        (STATUS_CLOSED, 'Đã đóng'),
        (STATUS_REJECTED, 'Bị từ chối'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Thấp'),
        (PRIORITY_MEDIUM, 'Trung bình'),
        (PRIORITY_HIGH, 'Cao'),
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
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        help_text="Mức độ ưu tiên.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Tiêu đề ticket.",
    )
    content = models.TextField(
        help_text="Nội dung chi tiết.",
    )
    evidence_file = models.FileField(
        upload_to='tickets/%Y/%m/',
        null=True,
        blank=True,
        help_text="File minh chứng đính kèm."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        help_text="Trạng thái của ticket.",
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        help_text="Người xử lý ticket.",
    )
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Lý do từ chối (nếu có)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket: {self.title} ({self.author.username})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'

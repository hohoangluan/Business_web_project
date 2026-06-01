import os
from django.db import models
from django.contrib.auth.models import User

class Report(models.Model):
    """
    Báo cáo cá nhân của nhân viên gửi lên cấp quản lý theo sơ đồ phân cấp.
    Hỗ trợ tải lên file tài liệu đính kèm.
    Một khi báo cáo đã được quản lý tiếp nhận (status = ACKNOWLEDGED), người gửi không thể sửa hay xóa.
    """

    SUBMITTED = 'submitted'
    NEEDS_UPDATE = 'needs_update'
    ACKNOWLEDGED = 'acknowledged'
    STATUS_CHOICES = [
        (SUBMITTED, 'Đã gửi'),
        (NEEDS_UPDATE, 'Yêu cầu cập nhật'),
        (ACKNOWLEDGED, 'Đã tiếp nhận'),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_sent',
        help_text="Người gửi báo cáo.",
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_received',
        help_text="Quản lý nhận báo cáo.",
        null=True,
        blank=True,
    )
    title = models.CharField(
        max_length=255,
        help_text="Tiêu đề báo cáo.",
    )
    content = models.TextField(
        help_text="Nội dung báo cáo.",
    )
    file_attachment = models.FileField(
        upload_to='report_attachments/',
        null=True,
        blank=True,
        help_text="Tài liệu/file đính kèm.",
    )
    is_viewed = models.BooleanField(
        default=False,
        help_text="Trạng thái đã xem của cấp quản lý.",
    )
    viewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Thời điểm quản lý xem báo cáo.",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=SUBMITTED,
        help_text='Trạng thái nghiệp vụ của báo cáo.',
    )
    manager_note = models.TextField(
        blank=True, default='',
        help_text='Phản hồi/chỉ đạo của quản lý.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def can_edit_or_delete(self):
        """Khóa chỉnh sửa khi đã được quản lý tiếp nhận (acknowledged)."""
        return self.status != self.ACKNOWLEDGED

    @property
    def filename(self):
        """Trả về tên file nguyên bản để hiển thị trên giao diện."""
        if self.file_attachment:
            return os.path.basename(self.file_attachment.name)
        return ""

    def __str__(self):
        recipient_name = self.recipient.username if self.recipient else "Chưa gán"
        return f"Báo cáo: {self.title} (Từ: {self.author.username} -> Đến: {recipient_name})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Báo cáo'
        verbose_name_plural = 'Báo cáo'

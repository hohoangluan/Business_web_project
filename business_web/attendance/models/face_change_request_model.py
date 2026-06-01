"""Pending face-enrollment change + audit log.

Anti-fraud: a self-service face update does NOT take effect immediately.
It is parked here as `pending` and only becomes the active enrollment
(EmployeeFace + remote /register) after HR approves. Approved/rejected rows
are kept as an audit trail (who changed whose face, when, from where).
"""
from django.contrib.auth.models import User
from django.db import models


class FaceChangeRequest(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Chờ HR duyệt'),
        (APPROVED, 'Đã duyệt'),
        (REJECTED, 'Từ chối'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='face_change_requests',
        help_text='Nhân viên chủ khuôn mặt sẽ được cập nhật.',
    )
    submitted_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='+',
        help_text='Người thực hiện cập nhật (để phát hiện đổi mặt hộ người khác).',
    )
    image_base64 = models.TextField(
        help_text='Ảnh khuôn mặt chờ duyệt (base64).',
    )
    content_type = models.CharField(max_length=50, default='image/jpeg')
    image_sha256 = models.CharField(
        max_length=64, blank=True, default='',
        help_text='SHA-256 của ảnh — phục vụ audit / phát hiện đảo ảnh.',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=PENDING,
    )
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    hr_note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'FaceChange({self.user_id}, {self.status})'

    @property
    def is_cross_user(self):
        """True nếu người upload khác chủ khuôn mặt (cờ nghi vấn)."""
        return self.submitted_by_id != self.user_id

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Yêu cầu cập nhật khuôn mặt'
        verbose_name_plural = 'Yêu cầu cập nhật khuôn mặt'

from django.db import models
from django.contrib.auth.models import User


class OvertimeRequest(models.Model):
    """
    Đơn đăng ký tăng ca.

    Quy trình phê duyệt 2 bước:
      - Bước 1: Leader/Manager trực tiếp duyệt → status = leader_approved
      - Bước 2: HR duyệt cuối cùng         → status = approved

    Ngoại lệ: Nếu người tạo đơn có role HR → chỉ cần bước 1 (leader/manager
    duyệt) là đủ, status chuyển thẳng sang approved.
    """

    # ----- Status constants -----
    PENDING = 'pending'
    LEADER_APPROVED = 'leader_approved'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Chờ duyệt'),
        (LEADER_APPROVED, 'Quản lý đã duyệt'),
        (APPROVED, 'Đã duyệt'),
        (REJECTED, 'Từ chối'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='overtime_requests',
        help_text="Nhân viên đăng ký tăng ca.",
    )
    overtime_date = models.DateField(
        help_text="Ngày tăng ca.",
    )
    start_time = models.TimeField(
        help_text="Giờ bắt đầu tăng ca.",
    )
    end_time = models.TimeField(
        help_text="Giờ kết thúc tăng ca.",
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
        choices=STATUS_CHOICES,
        default=PENDING,
        help_text="Trạng thái đơn.",
    )

    # ----- Phê duyệt bước 1: Leader / Manager trực tiếp -----
    leader_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leader_approved_overtimes',
        help_text="Leader/Manager đã duyệt bước 1.",
    )
    leader_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Thời điểm duyệt bước 1.",
    )

    # ----- Phê duyệt bước 2 (cuối cùng): HR hoặc bước duy nhất cho HR staff -----
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_overtimes',
        help_text="Người phê duyệt cuối cùng.",
    )

    # ----- Từ chối -----
    rejected_reason = models.TextField(
        blank=True,
        default='',
        help_text="Lý do từ chối (nếu bị từ chối).",
    )

    attachment = models.FileField(
        upload_to='overtime/attachments/%Y/%m/',
        null=True,
        blank=True,
        help_text='Tệp minh chứng (PDF/JPG/PNG, ≤5MB).',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.overtime_date} ({self.hours}h)"

    @property
    def time_range_display(self):
        """Trả về chuỗi 'HH:MM - HH:MM' để hiển thị trên template."""
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

    @property
    def is_waiting(self):
        """Đơn đang chờ xử lý (pending hoặc leader_approved)."""
        return self.status in (self.PENDING, self.LEADER_APPROVED)

    @property
    def status_display_vi(self):
        """Trả về tên trạng thái tiếng Việt."""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Đơn tăng ca'
        verbose_name_plural = 'Đơn tăng ca'

from django.db import models
from django.contrib.auth.models import User


class LeaveRequest(models.Model):
    """
    Đơn xin nghỉ phép của nhân viên.

    Quy trình phê duyệt 2 bước (giống overtime):
      - Bước 1: Leader/Manager trực tiếp duyệt → status = leader_approved
      - Bước 2: HR duyệt cuối cùng             → status = approved
      - Ngoại lệ: HR chỉ cần bước 1.
    """

    # ----- Loại nghỉ phép -----
    ANNUAL = 'annual'
    SICK = 'sick'
    PERSONAL = 'personal'
    MATERNITY = 'maternity'
    BUSINESS = 'business'
    OTHER = 'other'
    LEAVE_TYPE_CHOICES = [
        (ANNUAL, 'Nghỉ phép năm'),
        (SICK, 'Nghỉ ốm'),
        (PERSONAL, 'Nghỉ việc riêng'),
        (MATERNITY, 'Nghỉ thai sản'),
        (BUSINESS, 'Công tác'),
        (OTHER, 'Khác'),
    ]

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
        related_name='leave_requests',
        help_text="Nhân viên gửi đơn nghỉ phép.",
    )
    leave_type = models.CharField(
        max_length=50,
        choices=LEAVE_TYPE_CHOICES,
        default=ANNUAL,
        help_text="Loại nghỉ: phép năm, ốm, việc riêng...",
    )
    start_date = models.DateField(
        help_text="Ngày bắt đầu nghỉ.",
    )
    end_date = models.DateField(
        help_text="Ngày kết thúc nghỉ.",
    )
    days = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text="Số ngày nghỉ.",
    )
    reason = models.TextField(
        blank=True,
        default='',
        help_text="Lý do nghỉ phép.",
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
        related_name='leader_approved_leaves',
        help_text="Leader/Manager đã duyệt bước 1.",
    )
    leader_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Thời điểm duyệt bước 1.",
    )

    # ----- Phê duyệt bước 2 (cuối): HR -----
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves',
        help_text="Người phê duyệt cuối cùng.",
    )

    # ----- Từ chối -----
    rejected_reason = models.TextField(
        blank=True,
        default='',
        help_text="Lý do từ chối (nếu bị từ chối).",
    )

    attachment = models.FileField(
        upload_to='leaves/attachments/%Y/%m/',
        null=True,
        blank=True,
        help_text='Tệp minh chứng (PDF/JPG/PNG, ≤5MB).',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.start_date} đến {self.end_date}"

    @property
    def date_range_display(self):
        """Trả về chuỗi 'dd/mm/yyyy - dd/mm/yyyy'."""
        return f"{self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')}"

    @property
    def leave_type_display(self):
        """Trả về tên loại nghỉ phép tiếng Việt."""
        return dict(self.LEAVE_TYPE_CHOICES).get(self.leave_type, self.leave_type)

    @property
    def is_waiting(self):
        """Đơn đang chờ xử lý."""
        return self.status in (self.PENDING, self.LEADER_APPROVED)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Đơn nghỉ phép'
        verbose_name_plural = 'Đơn nghỉ phép'

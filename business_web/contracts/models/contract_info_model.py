from django.db import models
from django.contrib.auth.models import User

class ContractInfo(models.Model):
    """
    Thông tin hợp đồng lao động của nhân viên (có lưu lịch sử).
    1 User → N ContractInfo, 1 HĐ active tại 1 thời điểm.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contracts',
        help_text="Nhân viên sở hữu hợp đồng này.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Hợp đồng đang hiệu lực?",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Thời điểm tạo bản HĐ này (dùng cho lịch sử).",
    )

    # ----- Thông tin hợp đồng -----
    contract_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Số hợp đồng hiện tại. VD: HD-2026-001.",
    )
    contract_type = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Loại hợp đồng. VD: Thử việc 2 tháng, Chính thức 1 năm.",
    )
    contract_signed_date = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Ngày ký hợp đồng (DD/MM/YYYY).",
    )
    contract_start_date = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Ngày bắt đầu hiệu lực (DD/MM/YYYY).",
    )
    contract_end_date = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Ngày hết hạn (DD/MM/YYYY). Để trống nếu không thời hạn.",
    )
    contract_annual_leave_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Số ngày nghỉ phép/năm theo hợp đồng.",
    )
    contract_standard_shift = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Ca làm tiêu chuẩn. VD: 08:30 - 17:30 (Thứ 2 đến Thứ 6).",
    )
    shift_start_time = models.TimeField(
        null=True, blank=True,
        help_text="Giờ bắt đầu ca (đi trễ tính từ đây).",
    )
    shift_end_time = models.TimeField(
        null=True, blank=True,
        help_text="Giờ kết thúc ca (về sớm tính từ đây).",
    )
    contract_attachment_reference = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Tên file hoặc link tham chiếu hợp đồng.",
    )

    def __str__(self):
        return f"Contract: {self.user.username} - {self.contract_number or 'Chưa có HĐ'}"

    class Meta:
        ordering = ['user__username']
        verbose_name = 'Hợp đồng lao động'
        verbose_name_plural = 'Hợp đồng lao động'

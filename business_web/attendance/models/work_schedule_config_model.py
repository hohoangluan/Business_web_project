from datetime import time

from django.db import models


class WorkScheduleConfig(models.Model):
    """Lịch giờ làm cố định toàn công ty (singleton, 1 dòng).

    HR cấu hình giờ vào/ra chuẩn + thời gian ân hạn đi trễ. Backend chấm công
    dùng làm mặc định khi hợp đồng nhân viên không quy định giờ ca riêng.
    """

    shift_start = models.TimeField(
        default=time(8, 30),
        help_text="Giờ bắt đầu làm việc chuẩn.",
    )
    shift_end = models.TimeField(
        default=time(17, 30),
        help_text="Giờ kết thúc ca làm chuẩn.",
    )
    late_grace_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Số phút ân hạn đi trễ trước khi tính 'late'.",
    )

    class Meta:
        verbose_name = "Cấu hình giờ làm"
        verbose_name_plural = "Cấu hình giờ làm"

    def __str__(self):
        return f"{self.shift_start:%H:%M}–{self.shift_end:%H:%M} (ân hạn {self.late_grace_minutes}')"

    @classmethod
    def get_solo(cls):
        """Trả dòng cấu hình duy nhất (pk=1), tạo với mặc định nếu chưa có."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

from django.db import models
from django.contrib.auth.models import User

class AttendanceRecord(models.Model):
    """
    Bản ghi chấm công của một nhân viên trong một ngày.
    Placeholder — sẽ được bổ sung khi xây dựng backend chấm công thật.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Nhân viên sở hữu bản ghi chấm công.",
    )
    record_date = models.DateField(
        help_text="Ngày chấm công.",
    )
    check_in_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Giờ vào làm.",
    )
    check_out_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Giờ tan làm.",
    )
    status = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Trạng thái: on_time, late, absent...",
    )

    def __str__(self):
        return f"{self.user.username} - {self.record_date}"

    class Meta:
        ordering = ['-record_date']
        unique_together = ['user', 'record_date']
        verbose_name = 'Bản ghi chấm công'
        verbose_name_plural = 'Bản ghi chấm công'

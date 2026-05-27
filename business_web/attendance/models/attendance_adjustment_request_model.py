"""Employee-submitted request to fix a forgotten/erroneous attendance record.

HR-side review (approve/reject) is out of scope this phase.
"""
from django.contrib.auth.models import User
from django.db import models

from attendance.models.attendance_record_model import AttendanceRecord


class AttendanceAdjustmentRequest(models.Model):
    REASON_CHOICES = [
        ('forgot',         'Quên chấm ra'),
        ('technical',      'Lỗi kỹ thuật / hệ thống'),
        ('business_trip',  'Đi công tác / ra ngoài làm việc'),
        ('other',          'Khác'),
    ]
    STATUS_CHOICES = [
        ('pending',  'Chờ HR duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    ]

    record = models.OneToOneField(
        AttendanceRecord,
        on_delete=models.CASCADE,
        related_name='adjustment_request',
    )
    submitted_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='+',
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    reason_detail = models.TextField(blank=True, default='')
    claimed_check_out_time = models.TimeField(
        help_text='Giờ ra thực tế nhân viên khai báo.',
    )
    evidence = models.FileField(
        upload_to='attendance/adjustments/%Y/%m/',
        null=True, blank=True,
        help_text='Ảnh / PDF chứng từ tùy chọn.',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+',
    )
    hr_note = models.TextField(blank=True, default='')

    def __str__(self):
        return f'AdjustRequest({self.record_id}, {self.status})'

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Yêu cầu điều chỉnh chấm công'
        verbose_name_plural = 'Yêu cầu điều chỉnh chấm công'

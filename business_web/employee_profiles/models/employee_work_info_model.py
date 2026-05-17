from django.db import models
from django.contrib.auth.models import User

class EmployeeWorkInfo(models.Model):
    """
    Thông tin công việc của nhân viên.
    Mỗi User có đúng 1 EmployeeWorkInfo (OneToOne).
    Truy cập: request.user.work_info
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='work_info',
        help_text="User sở hữu thông tin công việc này.",
    )

    # ----- Thông tin vị trí công việc -----
    employee_type = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Loại nhân viên: Toàn thời gian, Bán thời gian, Thực tập...",
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Phòng ban hoặc bộ phận. VD: Phòng Kinh doanh.",
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Chức danh. VD: Chuyên viên kinh doanh.",
    )
    workplace = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Nơi làm việc chính. VD: Văn phòng Hà Nội.",
    )

    # ----- Thời gian làm việc -----
    probation_start = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Ngày bắt đầu thử việc (DD/MM/YYYY).",
    )
    official_start_date = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Ngày làm việc chính thức (DD/MM/YYYY).",
    )

    # ----- Trạng thái làm việc -----
    WORKING = 'working'
    PROBATION = 'probation'
    PAUSED = 'paused'
    RESIGNED = 'resigned'
    WORK_STATUS_CHOICES = [
        (WORKING, 'Đang làm việc'),
        (PROBATION, 'Đang thử việc'),
        (PAUSED, 'Tạm nghỉ'),
        (RESIGNED, 'Đã nghỉ việc'),
    ]
    work_status = models.CharField(
        max_length=30,
        blank=True,
        default='',
        choices=WORK_STATUS_CHOICES,
        help_text="Trạng thái làm việc hiện tại.",
    )

    # ----- Quan hệ quản lý -----
    manager_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_employees',
        help_text="Quản lý trực tiếp của nhân viên này.",
    )
    leader_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_employees',
        help_text="Leader phụ trách nhân viên này.",
    )

    def __str__(self):
        return f"WorkInfo: {self.user.username} - {self.department or 'Chưa phân phòng ban'}"

    class Meta:
        ordering = ['user__username']
        verbose_name = 'Thông tin công việc'
        verbose_name_plural = 'Thông tin công việc'

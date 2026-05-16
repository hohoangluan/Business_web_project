"""
==============================================================================
EMPLOYEE_PROFILES MODELS
==============================================================================
Chứa thông tin công việc của nhân viên: phòng ban, chức vụ, nơi làm việc,
trạng thái làm việc, quản lý trực tiếp...

Tách riêng khỏi UserProfile (accounts) để:
  - Mỗi app chỉ quản lý dữ liệu thuộc nghiệp vụ của mình
  - Dễ tìm chỗ sửa khi cần nâng cấp thông tin nhân sự
  - Các app khác import từ đây khi cần thông tin công việc

Quan hệ: User ←(1:1)→ EmployeeWorkInfo
Truy cập: user.work_info
==============================================================================
"""

from django.db import models
from django.contrib.auth.models import User


class PersonalInfo(models.Model):
    """Supplemental personal details that are not collected during registration."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="personal_info",
        help_text="User that owns this personal information.",
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Phone number.",
    )
    date_of_birth = models.CharField(
        max_length=10,
        blank=True,
        default="",
        help_text="Date of birth (DD/MM/YYYY).",
    )
    gender = models.CharField(max_length=20, blank=True, default="", help_text="Giới tính")
    marital_status = models.CharField(max_length=50, blank=True, default="", help_text="Tình trạng hôn nhân")
    nationality = models.CharField(max_length=100, blank=True, default="", help_text="Quốc tịch")
    id_card_number = models.CharField(max_length=50, blank=True, default="", help_text="Số CCCD/CMND")
    id_card_issue_place = models.CharField(max_length=255, blank=True, default="", help_text="Nơi cấp")
    id_card_issue_date = models.CharField(max_length=10, blank=True, default="", help_text="Ngày cấp (DD/MM/YYYY)")
    permanent_address = models.TextField(blank=True, default="", help_text="Địa chỉ thường trú")
    temporary_address = models.TextField(blank=True, default="", help_text="Địa chỉ tạm trú")

    @property
    def employee_id(self):
        """Return the employee ID linked through UserProfile when available."""

        profile = getattr(self.user, "profile", None)
        return getattr(profile, "employee_id", "") if profile else ""

    def __str__(self):
        profile = getattr(self.user, "profile", None)
        display_name = (
            getattr(profile, "full_name", "")
            or getattr(profile, "employee_id", "")
            or self.user.username
        )
        return f"PersonalInfo: {display_name}"

    class Meta:
        ordering = ["user__username"]


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

class EmergencyContact(models.Model):
    """Thông tin người liên hệ khẩn cấp."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="emergency_contact",
        help_text="Nhân viên sở hữu thông tin liên hệ này.",
    )
    contact_name = models.CharField(max_length=255, blank=True, default="", help_text="Họ tên người liên hệ")
    contact_phone = models.CharField(max_length=20, blank=True, default="", help_text="Số điện thoại")
    relation = models.CharField(max_length=100, blank=True, default="", help_text="Quan hệ với nhân viên")
    contact_address = models.TextField(blank=True, default="", help_text="Địa chỉ")

    def __str__(self):
        return f"EmergencyContact: {self.user.username}"

class EducationAndSkills(models.Model):
    """Thông tin học vấn và năng lực chuyên môn."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="education_and_skills",
        help_text="Nhân viên sở hữu hồ sơ năng lực này.",
    )
    education_level = models.CharField(max_length=100, blank=True, default="", help_text="Trình độ học vấn")
    degree = models.CharField(max_length=255, blank=True, default="", help_text="Bằng cấp")
    major = models.CharField(max_length=255, blank=True, default="", help_text="Chuyên ngành")
    certificates = models.TextField(blank=True, default="", help_text="Chứng chỉ")
    foreign_languages = models.TextField(blank=True, default="", help_text="Ngoại ngữ")
    professional_skills = models.TextField(blank=True, default="", help_text="Kỹ năng chuyên môn")

    def __str__(self):
        return f"EducationAndSkills: {self.user.username}"

class EmployeeDocument(models.Model):
    """Tệp minh chứng đính kèm (bằng cấp, CCCD, ...)."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Nhân viên sở hữu tệp này.",
    )
    title = models.CharField(max_length=255, help_text="Tên hoặc tiêu đề minh chứng")
    document_type = models.CharField(max_length=100, blank=True, default="", help_text="Loại minh chứng (VD: Bằng cấp, CCCD)")
    file = models.FileField(upload_to="employee_documents/", help_text="Tệp đính kèm")
    uploaded_at = models.DateTimeField(auto_now_add=True, help_text="Thời gian tải lên")

    def __str__(self):
        return f"Document: {self.title} ({self.user.username})"

    class Meta:
        ordering = ['-uploaded_at']

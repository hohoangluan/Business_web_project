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

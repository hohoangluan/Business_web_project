from django.db import models
from django.contrib.auth.models import User

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

from django.db import models
from django.contrib.auth.models import User

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

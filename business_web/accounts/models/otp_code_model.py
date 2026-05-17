"""OTP code model for password recovery."""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class OtpCode(models.Model):
    """One-time password record linked to a user for password recovery.

    OTP is valid for 2 minutes from creation.
    Should be deleted immediately after successful verification or expiry.
    """

    OTP_EXPIRY_SECONDS = 120  # 2 minutes

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="otp_codes",
        help_text="User requesting password recovery.",
    )
    code = models.CharField(
        max_length=6,
        help_text="6-digit OTP code.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when OTP was generated.",
    )

    def is_expired(self):
        """Return True if this OTP has passed its 2-minute validity window."""
        elapsed = (timezone.now() - self.created_at).total_seconds()
        return elapsed > self.OTP_EXPIRY_SECONDS

    def __str__(self):
        return f"OTP for {self.user.username} (created {self.created_at:%H:%M:%S})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "OTP Code"
        verbose_name_plural = "OTP Codes"

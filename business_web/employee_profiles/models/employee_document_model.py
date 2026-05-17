from django.db import models
from django.contrib.auth.models import User

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

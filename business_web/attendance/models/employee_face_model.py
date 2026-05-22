from django.db import models
from django.contrib.auth.models import User


class EmployeeFace(models.Model):
    """
    Lưu trữ ảnh khuôn mặt (base64) của nhân viên phục vụ chấm công.
    Mỗi nhân viên (User) có đúng 1 bản ghi EmployeeFace.
    Truy cập: request.user.employee_face
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_face',
        help_text="Nhân viên sở hữu ảnh khuôn mặt này.",
    )
    face_base64 = models.TextField(
        help_text="Chuỗi base64 của ảnh khuôn mặt nhân viên.",
    )
    content_type = models.CharField(
        max_length=50,
        default='image/png',
        help_text="MIME type của ảnh gốc. VD: image/jpeg, image/png.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Thời gian cập nhật ảnh lần cuối.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Thời gian tạo bản ghi.",
    )

    def __str__(self):
        return f"Face: {self.user.username}"

    class Meta:
        verbose_name = 'Ảnh khuôn mặt nhân viên'
        verbose_name_plural = 'Ảnh khuôn mặt nhân viên'

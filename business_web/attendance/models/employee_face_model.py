from django.db import models
from django.contrib.auth.models import User


class EmployeeFace(models.Model):
    """
    Enrollment marker của nhân viên trên service nhận diện từ xa.
    Vector khuôn mặt và việc so khớp do service nhận diện từ xa xử lý
    (xem attendance/services/face/face_api_client.py).
    Mỗi nhân viên (User) có đúng 1 bản ghi EmployeeFace.
    Truy cập: request.user.employee_face
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_face',
        help_text="Nhân viên sở hữu bản ghi khuôn mặt này.",
    )
    slot_id = models.PositiveSmallIntegerField(
        default=1,
        help_text="Slot trên service từ xa (1-5). Hiện pin về 1.",
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

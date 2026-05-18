from django.db import models
from django.contrib.auth.models import User

class EvaluationCategory(models.Model):
    """
    Loại đánh giá (ví dụ: Chuyên cần, Hiệu suất công việc, Kỹ năng làm việc nhóm, thái độ...)
    Được HR/Admin cấu hình, Manager/Leader chọn khi tạo đánh giá.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Tên loại đánh giá."
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="Mô tả chi tiết loại đánh giá."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Loại đánh giá'
        verbose_name_plural = 'Loại đánh giá'


class Evaluation(models.Model):
    """
    Bản đánh giá nhân viên do Manager/Leader tạo.
    """
    STATUS_CHOICES = [
        ('draft', 'Nháp'),
        ('submitted', 'Đã gửi'),
        ('acknowledged', 'HR đã xác nhận'),
    ]

    RATING_CHOICES = [
        ('A', 'A - Xuất sắc'),
        ('B', 'B - Tốt'),
        ('C', 'C - Trung bình'),
        ('D', 'D - Cần cải thiện'),
    ]

    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evaluations_received',
        help_text="Nhân viên được đánh giá.",
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evaluations_given',
        help_text="Người thực hiện đánh giá (Manager/Leader).",
    )
    category = models.ForeignKey(
        EvaluationCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluations',
        help_text="Loại đánh giá."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Trạng thái đánh giá."
    )
    rating = models.CharField(
        max_length=5,
        choices=RATING_CHOICES,
        blank=True,
        default='',
        help_text="Xếp loại nhân viên."
    )
    evaluation_date = models.DateField(
        help_text="Ngày đánh giá.",
    )
    content = models.TextField(
        help_text="Nội dung đánh giá.",
    )
    evidence_reference = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="File minh chứng hoặc link tham chiếu.",
    )
    
    # HR Acknowledgement fields
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluations_acknowledged',
        help_text="HR xác nhận đánh giá."
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Thời điểm HR xác nhận."
    )
    hr_note = models.TextField(
        blank=True,
        default='',
        help_text="Ghi chú phản hồi từ HR."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        category_name = self.category.name if self.category else "Chưa phân loại"
        return f"{self.employee.username} - {category_name} bởi {self.reviewer.username} ({self.evaluation_date})"

    class Meta:
        ordering = ['-evaluation_date']
        verbose_name = 'Đánh giá nhân viên'
        verbose_name_plural = 'Đánh giá nhân viên'


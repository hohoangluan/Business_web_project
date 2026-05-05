"""
==============================================================================
ACCOUNTS MODELS - accounts/models.py
==============================================================================
Chứa các model liên quan đến xác thực và danh tính người dùng:
  - Role: vai trò hệ thống (Admin, HR, Manager, Leader, Employee)
  - CustomPermission: quyền tùy chỉnh tách riêng khỏi role
  - UserProfile: thông tin danh tính cơ bản gắn với Django User

Thông tin công việc → employee_profiles.EmployeeWorkInfo
Thông tin hợp đồng → contracts.ContractInfo
==============================================================================
"""

from django.db import models
from django.contrib.auth.models import User


class Role(models.Model):
    """
    Vai trò hệ thống của user.
    Có 5 vai trò: Admin, HR, Manager, Leader, Employee.
    Role quyết định user thấy menu gì, vào được route nào.
    """
    ADMIN = 'admin'
    HR = 'hr'
    MANAGER = 'manager'
    LEADER = 'leader'
    EMPLOYEE = 'employee'

    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (HR, 'HR'),
        (MANAGER, 'Manager'),
        (LEADER, 'Leader'),
        (EMPLOYEE, 'Employee'),
    ]

    name = models.CharField(
        max_length=50,
        unique=True,
        choices=ROLE_CHOICES,
        help_text="Tên vai trò (VD: 'admin', 'manager').",
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="Mô tả vai trò này làm gì.",
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        ordering = ['name']


class CustomPermission(models.Model):
    """
    Quyền tùy chỉnh, tách riêng với role.
    VD: 'can_export_reports', 'can_approve_leave'.
    Gán permission KHÔNG ảnh hưởng role và ngược lại.
    """
    codename = models.CharField(
        max_length=100,
        unique=True,
        help_text="Mã quyền (VD: 'can_export_reports').",
    )
    name = models.CharField(
        max_length=255,
        help_text="Tên hiển thị (VD: 'Xuất báo cáo').",
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="Giải thích quyền này cho phép làm gì.",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class UserProfile(models.Model):
    """
    Thông tin danh tính cơ bản gắn với Django User.
    Mỗi User có đúng 1 UserProfile (OneToOne).

    Lưu ý kiến trúc:
      - Thông tin công việc nằm ở: employee_profiles.EmployeeWorkInfo
      - Thông tin hợp đồng nằm ở: contracts.ContractInfo
      - UserProfile chỉ chứa: role, permissions, thông tin cá nhân cơ bản
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text="Django user mà profile này thuộc về.",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Vai trò hệ thống. Quyết định giao diện và quyền truy cập.",
    )
    permissions = models.ManyToManyField(
        CustomPermission,
        blank=True,
        related_name='users',
        help_text="Quyền tùy chỉnh, tách riêng khỏi role.",
    )

    # ----- Thông tin cá nhân cơ bản -----
    full_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Họ tên đầy đủ.",
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Số điện thoại.",
    )
    date_of_birth = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Ngày sinh (DD/MM/YYYY).",
    )
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Mã nhân viên duy nhất.",
    )

    def __str__(self):
        role_name = self.role.get_name_display() if self.role else 'No Role'
        return f"{self.user.username} ({role_name})"

    def has_custom_permission(self, codename):
        """Kiểm tra user có quyền tùy chỉnh cụ thể không."""
        return self.permissions.filter(codename=codename).exists()

    def is_admin(self):
        """Trả True nếu user có vai trò Admin."""
        return self.role and self.role.name == Role.ADMIN

    class Meta:
        ordering = ['user__username']

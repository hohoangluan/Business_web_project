from django.apps import AppConfig


class PerformanceConfig(AppConfig):
    """
    App đánh giá nhân viên.
    Quản lý đánh giá hiệu suất từ Manager/Leader.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'performance'
    verbose_name = 'Đánh giá nhân viên'

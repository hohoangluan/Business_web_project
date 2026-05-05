from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    """
    App chấm công.
    Quản lý lịch sử điểm danh, check-in/check-out của nhân viên.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'
    verbose_name = 'Chấm công'

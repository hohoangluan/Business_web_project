from django.apps import AppConfig


class OvertimeConfig(AppConfig):
    """
    App tăng ca.
    Quản lý đăng ký tăng ca và phê duyệt tăng ca.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'overtime'
    verbose_name = 'Tăng ca'

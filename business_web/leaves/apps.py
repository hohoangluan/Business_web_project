from django.apps import AppConfig


class LeavesConfig(AppConfig):
    """
    App nghỉ phép.
    Quản lý đơn nghỉ phép cá nhân và quy trình phê duyệt.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leaves'
    verbose_name = 'Nghỉ phép'

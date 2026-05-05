from django.apps import AppConfig


class ContractsConfig(AppConfig):
    """
    App quản lý hợp đồng lao động.
    Mỗi nhân viên có thông tin hợp đồng riêng (số HĐ, loại, thời hạn...).
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contracts'
    verbose_name = 'Hợp đồng lao động'

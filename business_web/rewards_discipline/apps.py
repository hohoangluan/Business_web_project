from django.apps import AppConfig


class RewardsDisciplineConfig(AppConfig):
    """
    App khen thưởng và xử phạt.
    Quản lý phiếu thưởng/phạt và quy trình phê duyệt.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rewards_discipline'
    verbose_name = 'Khen thưởng & Xử phạt'

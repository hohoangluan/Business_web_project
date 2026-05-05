from django.apps import AppConfig


class ReportsInteractionsConfig(AppConfig):
    """
    App báo cáo và tương tác.
    Quản lý báo cáo cá nhân, hộp thư báo cáo, ticket hỗ trợ & khiếu nại.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports_interactions'
    verbose_name = 'Báo cáo & Tương tác'

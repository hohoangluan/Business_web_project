from django.apps import AppConfig


class StatsReportsConfig(AppConfig):
    """
    App thống kê tổng hợp.
    Thu thập và trình bày dữ liệu từ các module khác.
    Tên app: stats_reports (tránh trùng stdlib 'statistics').
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stats_reports'
    verbose_name = 'Thống kê tổng hợp'

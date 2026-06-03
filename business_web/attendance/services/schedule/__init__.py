"""Resolver cấu hình giờ làm toàn công ty (WorkScheduleConfig)."""
from attendance.models import WorkScheduleConfig


def get_work_schedule():
    """Trả singleton cấu hình giờ làm (tạo mặc định nếu chưa có)."""
    return WorkScheduleConfig.get_solo()


def get_late_grace_minutes():
    """Số phút ân hạn đi trễ theo cấu hình HR."""
    return get_work_schedule().late_grace_minutes

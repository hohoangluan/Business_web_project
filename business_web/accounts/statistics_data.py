from datetime import timedelta

from django.utils import timezone


def build_statistics_records(users):
    """
    Tạo dữ liệu thống kê mock theo ngày cho danh sách user truyền vào.

    Vì project hiện chưa có model thật cho chấm công/nghỉ phép/tăng ca,
    file này gom toàn bộ dữ liệu demo vào một chỗ để người mới dễ sửa.
    """
    today = timezone.localdate()
    start_date = today - timedelta(days=179)
    records = []

    for user in users:
        profile = getattr(user, 'profile', None)
        if not profile:
            continue

        current_date = start_date
        while current_date <= today:
            record = build_daily_record(user, profile, current_date)
            if record is not None:
                records.append(record)
            current_date += timedelta(days=1)

    return records


def build_daily_record(user, profile, work_date):
    """
    Mỗi record là một dòng thống kê theo ngày.
    Cuối tuần được bỏ qua để dữ liệu nhìn tự nhiên hơn.
    """
    if work_date.weekday() >= 5:
        return None

    seed = make_seed(user.username, work_date)
    leave_days = 1 if seed % 29 == 0 else 0
    absence_days = 1 if leave_days == 0 and seed % 43 == 0 else 0

    if leave_days or absence_days:
        overtime_hours = 0
        late_count = 0
        attendance_rate = 0
    else:
        overtime_hours = seed % 4
        late_count = 1 if seed % 5 == 0 else 0
        attendance_rate = 92 if late_count else 100

    manager_user = getattr(profile, 'manager_user', None)
    leader_user = getattr(profile, 'leader_user', None)

    return {
        'record_date': work_date,
        'employee_username': user.username,
        'employee_name': profile.full_name or user.username,
        'department': profile.department or 'Chưa phân phòng ban',
        'manager_username': manager_user.username if manager_user else '',
        'leader_username': leader_user.username if leader_user else '',
        'leave_days': leave_days,
        'leave_requests': 1 if leave_days else 0,
        'overtime_hours': overtime_hours,
        'late_count': late_count,
        'absence_days': absence_days,
        'attendance_rate': attendance_rate,
    }


def make_seed(username, work_date):
    """
    Tạo seed cố định từ username + ngày để dữ liệu ổn định qua nhiều lần render.
    """
    text = f'{username}-{work_date:%Y%m%d}'
    return sum(ord(char) for char in text)

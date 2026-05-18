"""
Lấy dữ liệu thật từ database cho thống kê chấm công/nghỉ phép/tăng ca.
"""

from datetime import timedelta
from django.utils import timezone
from accounts.services import ensure_work_info
from leaves.models import LeaveRequest
from overtime.models import OvertimeRequest
from attendance.models import AttendanceRecord


def build_statistics_records(users, time_range=None):
    """
    Truy xuất dữ liệu thống kê từ CSDL thực.
    """
    today = timezone.localdate()
    if time_range:
        start_date = time_range['start_date']
        end_date = time_range['end_date']
    else:
        start_date = today - timedelta(days=179)
        end_date = today

    user_ids = [u.id for u in users]
    
    # 1. Lấy dữ liệu Leave
    approved_leaves = LeaveRequest.objects.filter(
        user_id__in=user_ids,
        status=LeaveRequest.APPROVED,
        start_date__lte=end_date,
        end_date__gte=start_date
    )
    
    # 2. Lấy dữ liệu Overtime
    approved_overtimes = OvertimeRequest.objects.filter(
        user_id__in=user_ids,
        status=OvertimeRequest.APPROVED,
        overtime_date__range=(start_date, end_date)
    )
    
    # 3. Lấy dữ liệu Attendance
    attendances = AttendanceRecord.objects.filter(
        user_id__in=user_ids,
        record_date__range=(start_date, end_date)
    )
    
    aggregated = {}
    
    # Cache user info
    user_map = {}
    for u in users:
        profile = getattr(u, 'profile', None)
        if not profile:
            continue
        work_info = ensure_work_info(u)
        manager_user = work_info.manager_user
        leader_user = work_info.leader_user
        user_map[u.username] = {
            'employee_username': u.username,
            'employee_name': profile.full_name or u.username,
            'department': work_info.department or 'Chưa phân phòng ban',
            'manager_username': manager_user.username if manager_user else '',
            'leader_username': leader_user.username if leader_user else '',
        }
        
    def get_or_create_daily_record(username, d):
        key = (username, d)
        if key not in aggregated:
            u_info = user_map.get(username)
            if not u_info:
                return None
            aggregated[key] = {
                'record_date': d,
                'employee_username': u_info['employee_username'],
                'employee_name': u_info['employee_name'],
                'department': u_info['department'],
                'manager_username': u_info['manager_username'],
                'leader_username': u_info['leader_username'],
                'leave_days': 0,
                'leave_requests': 0,
                'overtime_hours': 0,
                'late_count': 0,
                'absence_days': 0,
                'attendance_rate': 0,
            }
        return aggregated[key]

    # Process Leave
    for leave in approved_leaves:
        d = max(leave.start_date, start_date)
        e = min(leave.end_date, end_date)
        request_counted = False
        while d <= e:
            if d.weekday() < 5: # Chỉ tính ngày trong tuần
                rec = get_or_create_daily_record(leave.user.username, d)
                if rec:
                    rec['leave_days'] += 1
                    if not request_counted:
                        rec['leave_requests'] += 1
                        request_counted = True
            d += timedelta(days=1)
            
    # Process Overtime
    for ot in approved_overtimes:
        rec = get_or_create_daily_record(ot.user.username, ot.overtime_date)
        if rec:
            rec['overtime_hours'] += float(ot.hours)
            
    # Process Attendance
    for att in attendances:
        rec = get_or_create_daily_record(att.user.username, att.record_date)
        if rec:
            if att.status == 'late':
                rec['late_count'] += 1
                rec['attendance_rate'] = 90
            elif att.status == 'absent':
                rec['absence_days'] += 1
                rec['attendance_rate'] = 0
            else: # on_time
                rec['attendance_rate'] = 100
                
    return list(aggregated.values())

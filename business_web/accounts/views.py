"""
==============================================================================
ACCOUNTS VIEWS - accounts/views.py
==============================================================================
File này xử lý tất cả logic backend cho module tài khoản.
Mỗi view function nhận request từ URL → xử lý logic → trả về template.

VIEWS HIỆN CÓ (giữ nguyên logic, chỉ cập nhật template context):
  - register_view: Đăng ký tài khoản
  - dashboard_view: Trang chủ sau đăng nhập
  - logout_view: Đăng xuất
  - user_list_view: Danh sách tài khoản (NÂNG CẤP)
  - assign_role_view: Gán vai trò
  - assign_permissions_view: Gán quyền
  - delete_user_view: Xóa tài khoản

VIEWS MỚI:
  - profile_view: Xem/chỉnh sửa hồ sơ cá nhân
  - toggle_user_active_view: Khóa/mở khóa tài khoản
  - reset_user_password_view: Reset mật khẩu tài khoản
==============================================================================
"""

import csv
import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone

from .forms import (
    RegisterForm,
    AssignRoleForm,
    AssignPermissionsForm,
    EmployeeProfileForm,
)
from .models import UserProfile, Role
from .statistics_data import build_statistics_records


# =============================================================================
# HELPER: Access Control Check
# =============================================================================

def is_admin_user(user):
    """
    Kiểm tra user có quyền quản trị không.
    Dùng cho @user_passes_test (backend gate) — superuser luôn pass.
    Lưu ý: UI template dùng request.user.profile.is_admin riêng biệt.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return get_user_role_name(user) == Role.ADMIN


def ensure_profile(user):
    """
    Đảm bảo user có UserProfile.
    Nếu chưa có (VD: user tạo trước khi có profile system), tự động tạo.
    """
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


def mask_email(email):
    """Mask an email address before showing it in password recovery UI."""
    if not email or '@' not in email:
        return email or ''

    local_part, domain = email.split('@', 1)
    if len(local_part) <= 2:
        masked_local = local_part[:1] + '*'
    else:
        masked_local = local_part[0] + ('*' * (len(local_part) - 2)) + local_part[-1]
    return f'{masked_local}@{domain}'


def get_user_role_name(user):
    """Return the normalized profile role name used by the UI and guards."""
    if not user.is_authenticated:
        return ''
    try:
        role = user.profile.role
    except UserProfile.DoesNotExist:
        return ''
    return role.name.lower() if role and role.name else ''


def user_has_role(user, *role_names):
    normalized_roles = {role.lower() for role in role_names}
    return get_user_role_name(user) in normalized_roles


def has_admin_business_access(user):
    """
    Admin business actions should follow the active profile role.
    A superuser without a simulated role keeps full access, but switching to
    employee in the dev role switcher should behave like a real employee.
    """
    role_name = get_user_role_name(user)
    return role_name == Role.ADMIN or (user.is_authenticated and user.is_superuser and not role_name)


def is_hr_user(user):
    """
    Kiểm tra user có phải HR không.
    Dùng cho @user_passes_test — superuser cũng pass.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user_has_role(user, Role.HR)


def can_manage_requests(user):
    """HR/Manager/Leader/Admin can access approval and processing pages."""
    return has_admin_business_access(user) or user_has_role(
        user, Role.HR, Role.MANAGER, Role.LEADER
    )


def can_manage_work_info(user):
    """HR/Admin có thể cập nhật hồ sơ nhân sự đang lưu cho nhân viên."""
    return has_admin_business_access(user) or user_has_role(user, Role.HR)


def can_access_statistics(user):
    """HR/Admin/Manager/Leader có thể xem statistics theo phạm vi phù hợp."""
    return has_admin_business_access(user) or user_has_role(
        user, Role.HR, Role.MANAGER, Role.LEADER
    )


def get_user_display_name(user):
    """Ưu tiên full name để giao diện thân thiện hơn cho người mới đọc."""
    profile = ensure_profile(user)
    return profile.full_name or user.username


def get_department_label(profile):
    """Giữ nhãn phòng ban nhất quán giữa view, template và export."""
    return profile.department or 'Chưa phân phòng ban'


def get_manager_display_name(profile):
    manager_user = getattr(profile, 'manager_user', None)
    if not manager_user:
        return 'Chưa gán quản lý'
    return get_user_display_name(manager_user)


def get_leader_display_name(profile):
    leader_user = getattr(profile, 'leader_user', None)
    if not leader_user:
        return 'Chưa gán leader'
    return get_user_display_name(leader_user)


def parse_ddmmyyyy_date(raw_value):
    """Đọc chuỗi ngày DD/MM/YYYY. Sai format thì trả None."""
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, '%d/%m/%Y').date()
    except ValueError:
        return None


def has_complete_contract_info(profile):
    """Kiểm tra hồ sơ đã có đủ thông tin hợp đồng tối thiểu để hiển thị hay chưa."""
    return all([
        profile.contract_number,
        profile.contract_type,
        profile.contract_signed_date,
        profile.contract_start_date,
        profile.contract_standard_shift,
        profile.contract_annual_leave_days is not None,
    ])


def build_contract_page_context(profile):
    """
    Chuẩn bị dữ liệu hiển thị cho trang hợp đồng cá nhân.
    Giữ logic ở đây để template chỉ hiển thị, không phải tự xử lý ngày tháng.
    """
    has_contract = has_complete_contract_info(profile)
    if not has_contract:
        return {
            'has_contract': False,
            'contract_status_label': '',
            'contract_status_class': 'badge-none',
            'contract_end_display': '',
            'show_expiry_warning': False,
            'days_until_expiry': None,
        }

    today = timezone.localdate()
    start_date = parse_ddmmyyyy_date(profile.contract_start_date)
    end_date = parse_ddmmyyyy_date(profile.contract_end_date)

    if not profile.contract_end_date:
        contract_status_label = 'Không thời hạn'
        contract_status_class = 'badge-active'
        contract_end_display = 'Không thời hạn'
    elif end_date and end_date < today:
        contract_status_label = 'Hết hạn'
        contract_status_class = 'badge-inactive'
        contract_end_display = profile.contract_end_date
    elif start_date and start_date > today:
        contract_status_label = 'Sắp hiệu lực'
        contract_status_class = 'badge-locked'
        contract_end_display = profile.contract_end_date
    else:
        contract_status_label = 'Có hiệu lực'
        contract_status_class = 'badge-active'
        contract_end_display = profile.contract_end_date

    show_expiry_warning = False
    days_until_expiry = None
    if end_date and today <= end_date:
        days_until_expiry = (end_date - today).days
        show_expiry_warning = days_until_expiry <= 15

    return {
        'has_contract': True,
        'contract_status_label': contract_status_label,
        'contract_status_class': contract_status_class,
        'contract_end_display': contract_end_display,
        'show_expiry_warning': show_expiry_warning,
        'days_until_expiry': days_until_expiry,
    }


def get_manager_user_queryset():
    """Danh sách user có thể được chọn làm quản lý trực tiếp."""
    return User.objects.select_related('profile__role').filter(
        Q(is_superuser=True) | Q(profile__role__name__in=[Role.ADMIN, Role.MANAGER])
    ).order_by('profile__full_name', 'username')


def get_leader_user_queryset():
    """Danh sách user có thể được chọn làm leader trực tiếp."""
    return User.objects.select_related('profile__role').filter(
        Q(profile__role__name__in=[Role.LEADER, Role.MANAGER])
    ).order_by('profile__full_name', 'username')


def build_hr_create_profile_context(form_data=None):
    """Context chung cho trang tạo hồ sơ để chỗ GET/POST không bị lặp nhiều."""
    return {
        'active_page': 'hr_profiles',
        'form_data': form_data or {},
        'manager_choices': get_manager_user_queryset(),
        'leader_choices': get_leader_user_queryset(),
    }


def get_statistics_scope(user):
    """
    Xác định phạm vi dữ liệu mà user được quyền xem.
    Hàm này cố tình trả về dict dễ đọc để người mới debug thuận tiện.
    """
    profile = ensure_profile(user)

    if has_admin_business_access(user) or user_has_role(user, Role.HR):
        return {
            'scope_name': 'company',
            'scope_label': 'Toàn công ty',
            'locked_department': '',
            'locked_leader': '',
            'error_message': '',
        }

    if user_has_role(user, Role.MANAGER):
        if not profile.department:
            return {
                'scope_name': 'manager',
                'scope_label': '',
                'locked_department': '',
                'locked_leader': '',
                'error_message': 'Tài khoản Manager này chưa được gán phòng ban nên chưa thể xem thống kê.',
            }
        return {
            'scope_name': 'manager',
            'scope_label': f'Phòng ban: {profile.department}',
            'locked_department': profile.department,
            'locked_leader': '',
            'error_message': '',
        }

    if user_has_role(user, Role.LEADER):
        return {
            'scope_name': 'leader',
            'scope_label': f'Nhóm do {get_user_display_name(user)} phụ trách',
            'locked_department': '',
            'locked_leader': user.username,
            'error_message': '',
        }

    return {
        'scope_name': 'none',
        'scope_label': '',
        'locked_department': '',
        'locked_leader': '',
        'error_message': 'Bạn không có quyền truy cập statistics.',
    }


def get_scope_users(user, scope):
    """
    Lấy danh sách user nằm trong phạm vi statistics mà người hiện tại được xem.
    """
    users = User.objects.select_related(
        'profile__role',
        'profile__manager_user__profile',
        'profile__leader_user__profile',
    ).order_by('profile__full_name', 'username')

    for item in users:
        ensure_profile(item)

    if scope['scope_name'] == 'company':
        return [
            item for item in users
            if get_user_role_name(item) != Role.ADMIN
        ]

    if scope['scope_name'] == 'manager':
        return [
            item for item in users
            if item.pk != user.pk and item.profile.department == scope['locked_department']
        ]

    if scope['scope_name'] == 'leader':
        return [
            item for item in users
            if item.pk != user.pk and item.profile.leader_user_id == user.id
        ]

    return []


def parse_date_input(raw_value):
    """Đọc giá trị YYYY-MM-DD từ query string. Sai format thì trả None."""
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, '%Y-%m-%d').date()
    except ValueError:
        return None


def get_time_range_from_params(params):
    """
    Xử lý bộ lọc thời gian.
    Nếu preset là 'custom' thì dùng from_date / to_date.
    """
    today = timezone.localdate()
    period = params.get('period', 'this_month')
    from_date_raw = params.get('from_date', '')
    to_date_raw = params.get('to_date', '')

    if period == 'last_7_days':
        start_date = today - timedelta(days=6)
        end_date = today
        label = '7 ngày gần nhất'
    elif period == 'last_30_days':
        start_date = today - timedelta(days=29)
        end_date = today
        label = '30 ngày gần nhất'
    elif period == 'this_quarter':
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_start_month, day=1)
        end_date = today
        label = 'Quý này'
    elif period == 'this_year':
        start_date = today.replace(month=1, day=1)
        end_date = today
        label = 'Năm nay'
    elif period == 'custom':
        start_date = parse_date_input(from_date_raw)
        end_date = parse_date_input(to_date_raw)
        if not start_date or not end_date or start_date > end_date:
            start_date = today.replace(day=1)
            end_date = today
            period = 'this_month'
            label = 'Tháng này'
        else:
            label = 'Khoảng thời gian tùy chọn'
    else:
        start_date = today.replace(day=1)
        end_date = today
        period = 'this_month'
        label = 'Tháng này'

    return {
        'period': period,
        'from_date': from_date_raw,
        'to_date': to_date_raw,
        'start_date': start_date,
        'end_date': end_date,
        'label': label,
        'date_range_text': f'{start_date:%d/%m/%Y} - {end_date:%d/%m/%Y}',
    }


def build_statistics_filters(scope_users, scope, params):
    """
    Tạo option cho dropdown và lọc user theo từng cấp:
    phòng ban -> manager -> leader -> nhân viên.
    """
    filtered_users = list(scope_users)
    department_options = sorted({get_department_label(user.profile) for user in scope_users})

    if scope['locked_department']:
        selected_department = scope['locked_department']
    else:
        selected_department = params.get('department', '')
        if selected_department not in department_options:
            selected_department = ''

    if selected_department:
        filtered_users = [
            user for user in filtered_users
            if get_department_label(user.profile) == selected_department
        ]

    manager_map = {}
    for user in filtered_users:
        manager_user = user.profile.manager_user
        if manager_user:
            manager_map[manager_user.username] = get_user_display_name(manager_user)
    manager_options = [
        {'value': username, 'label': manager_map[username]}
        for username in sorted(manager_map.keys())
    ]

    selected_manager = params.get('manager', '')
    if selected_manager not in manager_map:
        selected_manager = ''

    if selected_manager:
        filtered_users = [
            user for user in filtered_users
            if user.profile.manager_user and user.profile.manager_user.username == selected_manager
        ]

    leader_map = {}
    for user in filtered_users:
        leader_user = user.profile.leader_user
        if leader_user:
            leader_map[leader_user.username] = get_user_display_name(leader_user)
    leader_options = [
        {'value': username, 'label': leader_map[username]}
        for username in sorted(leader_map.keys())
    ]

    if scope['locked_leader']:
        selected_leader = scope['locked_leader']
    else:
        selected_leader = params.get('leader', '')
        if selected_leader not in leader_map:
            selected_leader = ''

    if selected_leader:
        filtered_users = [
            user for user in filtered_users
            if user.profile.leader_user and user.profile.leader_user.username == selected_leader
        ]

    employee_map = {
        user.username: get_user_display_name(user)
        for user in filtered_users
    }
    employee_options = [
        {'value': username, 'label': employee_map[username]}
        for username in sorted(employee_map.keys())
    ]

    selected_employee = params.get('employee', '')
    if selected_employee not in employee_map:
        selected_employee = ''

    if selected_employee:
        filtered_users = [
            user for user in filtered_users
            if user.username == selected_employee
        ]

    return {
        'department_options': department_options,
        'manager_options': manager_options,
        'leader_options': leader_options,
        'employee_options': employee_options,
        'selected_department': selected_department,
        'selected_manager': selected_manager,
        'selected_leader': selected_leader,
        'selected_employee': selected_employee,
        'selected_manager_label': manager_map.get(selected_manager, ''),
        'selected_leader_label': leader_map.get(selected_leader, ''),
        'selected_employee_label': employee_map.get(selected_employee, ''),
        'filtered_users': filtered_users,
        'department_locked': bool(scope['locked_department']),
        'leader_locked': bool(scope['locked_leader']),
    }


def filter_statistics_records(records, filters, time_range):
    """Lọc record theo nhân viên đã chọn và khoảng thời gian đang xem."""
    allowed_usernames = {user.username for user in filters['filtered_users']}

    return [
        record for record in records
        if record['employee_username'] in allowed_usernames
        and time_range['start_date'] <= record['record_date'] <= time_range['end_date']
    ]


def build_statistics_summary_rows(filtered_users, filtered_records):
    """
    Gom record theo nhân viên để UI, CSV và print cùng dùng chung một bảng.
    """
    summary_map = {}

    for user in filtered_users:
        profile = ensure_profile(user)
        summary_map[user.username] = {
            'employee_name': get_user_display_name(user),
            'employee_username': user.username,
            'department': get_department_label(profile),
            'manager_name': get_manager_display_name(profile),
            'leader_name': get_leader_display_name(profile),
            'leave_days': 0,
            'leave_requests': 0,
            'overtime_hours': 0,
            'late_count': 0,
            'absence_days': 0,
            'attendance_total': 0,
            'attendance_entries': 0,
            'attendance_rate': 0,
        }

    for record in filtered_records:
        row = summary_map.get(record['employee_username'])
        if not row:
            continue
        row['leave_days'] += record['leave_days']
        row['leave_requests'] += record['leave_requests']
        row['overtime_hours'] += record['overtime_hours']
        row['late_count'] += record['late_count']
        row['absence_days'] += record['absence_days']
        row['attendance_total'] += record['attendance_rate']
        row['attendance_entries'] += 1

    rows = []
    for row in summary_map.values():
        if row['attendance_entries']:
            row['attendance_rate'] = round(
                row['attendance_total'] / row['attendance_entries'],
                1,
            )
        rows.append(row)

    rows.sort(key=lambda item: item['employee_name'].lower())
    return rows


def aggregate_rows(rows, label_key, value_key, empty_label):
    """Helper nhỏ để gom dữ liệu chart theo từng nhãn."""
    totals = {}
    for row in rows:
        label = row[label_key] or empty_label
        totals[label] = totals.get(label, 0) + row[value_key]

    sorted_items = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return {
        'labels': [item[0] for item in sorted_items],
        'values': [item[1] for item in sorted_items],
    }


def build_statistics_sections(summary_rows, time_range, filters, scope):
    """
    Chuẩn bị toàn bộ card, chart và bảng cho statistics.
    Tách hàm riêng để export CSV / print / màn hình web dùng chung dữ liệu.
    """
    employee_count = len(summary_rows)
    total_leave_days = sum(row['leave_days'] for row in summary_rows)
    total_leave_requests = sum(row['leave_requests'] for row in summary_rows)
    total_overtime_hours = sum(row['overtime_hours'] for row in summary_rows)
    total_late_count = sum(row['late_count'] for row in summary_rows)
    total_absence_days = sum(row['absence_days'] for row in summary_rows)
    average_attendance_rate = 0

    if employee_count:
        average_attendance_rate = round(
            sum(row['attendance_rate'] for row in summary_rows) / employee_count,
            1,
        )

    leave_by_department = aggregate_rows(
        summary_rows, 'department', 'leave_days', 'Chưa phân phòng ban'
    )
    leave_by_leader = aggregate_rows(
        summary_rows, 'leader_name', 'leave_days', 'Chưa gán leader'
    )
    leave_by_employee = {
        'labels': [row['employee_name'] for row in summary_rows[:8]],
        'values': [row['leave_days'] for row in summary_rows[:8]],
    }
    overtime_by_employee = {
        'labels': [row['employee_name'] for row in summary_rows[:8]],
        'values': [row['overtime_hours'] for row in summary_rows[:8]],
    }
    discipline_by_employee = {
        'labels': [row['employee_name'] for row in summary_rows[:8]],
        'late_values': [row['late_count'] for row in summary_rows[:8]],
        'absence_values': [row['absence_days'] for row in summary_rows[:8]],
    }

    filter_summary = [
        f"Phạm vi: {scope['scope_label'] or 'Không xác định'}",
        f"Thời gian: {time_range['label']} ({time_range['date_range_text']})",
    ]
    if filters['selected_department']:
        filter_summary.append(f"Phòng ban: {filters['selected_department']}")
    if filters['selected_manager']:
        filter_summary.append(
            f"Manager: {filters['selected_manager_label'] or filters['selected_manager']}"
        )
    if filters['selected_leader']:
        filter_summary.append(
            f"Leader: {filters['selected_leader_label'] or filters['selected_leader']}"
        )
    if filters['selected_employee']:
        filter_summary.append(
            f"Nhân viên: {filters['selected_employee_label'] or filters['selected_employee']}"
        )

    return {
        'summary_rows': summary_rows,
        'summary_cards': [
            {'label': 'Số nhân viên trong phạm vi', 'value': employee_count},
            {'label': 'Tổng giờ tăng ca', 'value': total_overtime_hours},
            {'label': 'Số lần đi trễ', 'value': total_late_count},
            {'label': 'Tỷ lệ chấm công trung bình', 'value': f'{average_attendance_rate}%'},
        ],
        'leave_cards': [
            {'label': 'Tổng ngày nghỉ', 'value': total_leave_days},
            {'label': 'Số đơn nghỉ', 'value': total_leave_requests},
            {'label': 'Leader đang có dữ liệu', 'value': len(leave_by_leader['labels'])},
            {'label': 'Phòng ban đang có dữ liệu', 'value': len(leave_by_department['labels'])},
        ],
        'attendance_cards': [
            {'label': 'Tổng giờ tăng ca', 'value': total_overtime_hours},
            {'label': 'Số lần đi trễ', 'value': total_late_count},
            {'label': 'Số ngày nghỉ làm', 'value': total_absence_days},
            {'label': 'Tỷ lệ đúng giờ trung bình', 'value': f'{average_attendance_rate}%'},
        ],
        'leave_by_department_json': json.dumps(leave_by_department),
        'leave_by_leader_json': json.dumps(leave_by_leader),
        'leave_by_employee_json': json.dumps(leave_by_employee),
        'overtime_by_employee_json': json.dumps(overtime_by_employee),
        'discipline_by_employee_json': json.dumps(discipline_by_employee),
        'filter_summary': filter_summary,
    }


def build_statistics_page_context(user, params):
    """
    Hàm trung tâm cho statistics.
    Màn hình web, CSV export và print view đều gọi lại hàm này để tránh lệch dữ liệu.
    """
    scope = get_statistics_scope(user)
    if scope['error_message']:
        return {
            'scope': scope,
            'time_range': get_time_range_from_params(params),
            'filters': {
                'department_options': [],
                'manager_options': [],
                'leader_options': [],
                'employee_options': [],
                'selected_department': '',
                'selected_manager': '',
                'selected_leader': scope['locked_leader'],
                'selected_employee': '',
                'selected_manager_label': '',
                'selected_leader_label': '',
                'selected_employee_label': '',
                'filtered_users': [],
                'department_locked': bool(scope['locked_department']),
                'leader_locked': bool(scope['locked_leader']),
            },
            'statistics_error_message': scope['error_message'],
            'statistics_sections': {
                'summary_rows': [],
                'summary_cards': [],
                'leave_cards': [],
                'attendance_cards': [],
                'leave_by_department_json': json.dumps({'labels': [], 'values': []}),
                'leave_by_leader_json': json.dumps({'labels': [], 'values': []}),
                'leave_by_employee_json': json.dumps({'labels': [], 'values': []}),
                'overtime_by_employee_json': json.dumps({'labels': [], 'values': []}),
                'discipline_by_employee_json': json.dumps({
                    'labels': [],
                    'late_values': [],
                    'absence_values': [],
                }),
                'filter_summary': [],
            },
        }

    scope_users = get_scope_users(user, scope)
    filters = build_statistics_filters(scope_users, scope, params)
    time_range = get_time_range_from_params(params)
    records = build_statistics_records(filters['filtered_users'])
    filtered_records = filter_statistics_records(records, filters, time_range)
    statistics_sections = build_statistics_sections(
        build_statistics_summary_rows(filters['filtered_users'], filtered_records),
        time_range,
        filters,
        scope,
    )

    statistics_error_message = ''
    if not scope_users:
        statistics_error_message = 'Chưa có nhân viên nào thuộc phạm vi quản lý của bạn để thống kê.'
    elif not filters['filtered_users']:
        statistics_error_message = 'Không tìm thấy nhân viên phù hợp với bộ lọc hiện tại.'

    return {
        'scope': scope,
        'time_range': time_range,
        'filters': filters,
        'statistics_sections': statistics_sections,
        'statistics_error_message': statistics_error_message,
    }

# =============================================================================
# PUBLIC VIEWS: Registration, Login, Logout, Dashboard
# =============================================================================

def register_view(request):
    """
    Xử lý đăng ký tài khoản với 7 trường.
    - GET: hiển thị form đăng ký
    - POST: validate, tạo user + profile, tự động đăng nhập

    Template: accounts/register.html
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()           # Lưu user (username, email, password)

            # Tạo UserProfile với các trường đăng ký bổ sung
            profile = ensure_profile(user)
            profile.full_name = form.cleaned_data['full_name']
            profile.phone_number = form.cleaned_data['phone_number']
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.employee_id = form.cleaned_data['employee_id']
            profile.save()

            login(request, user)         # Tự động đăng nhập sau đăng ký
            messages.success(request, 'Đăng ký tài khoản thành công! Chào mừng bạn.')
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def forgot_password_view(request):
    """
    UI quên mật khẩu 2 bước:
    - Bước 1: nhập username.
    - Bước 2: hiển thị form nhập mã xác nhận gửi về email trong tài khoản.

    Hiện tại chỉ dựng UI/flow xác nhận, chưa gửi email thật vì project chưa cấu
    hình EMAIL_BACKEND/SMTP.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    context = {
        'step': 'username',
        'username': '',
        'masked_email': '',
    }

    if request.method == 'POST':
        step = request.POST.get('step', 'username')
        username = request.POST.get('username', '').strip()
        context['username'] = username

        if step == 'username':
            user = User.objects.filter(username=username).first() if username else None

            if not username:
                context['error_message'] = 'Vui lòng nhập username để nhận mã xác nhận.'
            elif not user:
                context['error_message'] = 'Không tìm thấy tài khoản với username này.'
            elif not user.email:
                context['error_message'] = 'Tài khoản này chưa có email trong hồ sơ.'
            else:
                context.update({
                    'step': 'code',
                    'masked_email': mask_email(user.email),
                    'success_message': 'Mã xác nhận sẽ được gửi đến Gmail trong hồ sơ tài khoản.',
                })

        elif step == 'code':
            verification_code = request.POST.get('verification_code', '').strip()
            user = User.objects.filter(username=username).first() if username else None

            context.update({
                'step': 'code',
                'masked_email': mask_email(user.email) if user and user.email else '',
                'verification_code': verification_code,
            })

            if not verification_code:
                context['error_message'] = 'Vui lòng nhập mã xác nhận.'
            elif len(verification_code) != 6:
                context['error_message'] = 'Mã xác nhận gồm 6 ký tự.'
            else:
                context['success_message'] = 'Giao diện xác nhận mã đã sẵn sàng. Bước đặt lại mật khẩu sẽ được kết nối sau.'

    return render(request, 'accounts/forgot_password.html', context)


@login_required
def dashboard_view(request):
    """
    Trang chủ sau khi đăng nhập.
    Hiển thị thông tin tổng quan, link điều hướng theo vai trò.

    Template: accounts/dashboard.html
    Context: active_page - để sidebar highlight đúng menu item
    """
    ensure_profile(request.user)
    return render(request, 'accounts/dashboard.html', {
        'active_page': 'dashboard',  # Sidebar highlight
        'can_access_statistics': can_access_statistics(request.user),
        'can_manage_work_info': can_manage_work_info(request.user),
        'is_system_admin': is_admin_user(request.user),
    })


def logout_view(request):
    """Đăng xuất và redirect về trang đăng nhập."""
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('login')


# =============================================================================
# PROFILE VIEW (MỚI)
# =============================================================================

@login_required
def profile_view(request):
    """
    Trang hồ sơ cá nhân.
    - GET: Hiển thị thông tin user hiện tại
    - POST: Cập nhật các trường cho phép chỉnh sửa

    Các trường CÓ THỂ chỉnh sửa (đã có trong model):
      - full_name, email, phone_number, date_of_birth

    Các trường tổ chức như department / position / manager / leader
    đã có trong model nhưng được quản trị bởi HR/Admin ở màn hình riêng.
    Các nhóm dữ liệu cá nhân khác (giới tính, CCCD, ngân hàng...)
    vẫn đang là mock data trên template.
    → Khi thêm field vào model, chỉ cần thêm vào form xử lý bên dưới.

    Template: accounts/profile.html
    """
    profile = ensure_profile(request.user)

    if request.method == 'POST':
        # Cập nhật các field có trong model
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()

        # Validate đơn giản
        if full_name:
            profile.full_name = full_name
        if email:
            request.user.email = email
            request.user.save()
        if phone_number:
            profile.phone_number = phone_number
        if date_of_birth:
            profile.date_of_birth = date_of_birth

        profile.save()
        messages.success(request, 'Cập nhật hồ sơ thành công!')
        return redirect('profile')

    ensure_profile(request.user)
    return render(request, 'accounts/profile.html', {
        'active_page': 'profile'
    })


@login_required
def contract_view(request):
    """
    Trang hợp đồng cá nhân.
    Chỉ hiển thị hợp đồng hiện tại của chính người đang đăng nhập.
    """
    profile = ensure_profile(request.user)
    contract_context = build_contract_page_context(profile)

    return render(request, 'accounts/contract.html', {
        'active_page': 'contract',
        'contract_context': contract_context,
    })


@login_required
def attendance_view(request):
    """
    Trang giao diện Chấm công. MOCK DATA.
    - Hiển thị đồng hồ thời gian thực và lịch sử điểm danh.
    """
    ensure_profile(request.user)
    return render(request, 'accounts/attendance.html', {
        'active_page': 'attendance',
    })


@login_required
def leave_view(request):
    """
    Trang giao diện Nghỉ phép cá nhân. MOCK DATA.
    - Hiển thị danh sách nghỉ phép của chính mình.
    - Hiển thị nút Phê duyệt nếu user có quyền.
    """
    ensure_profile(request.user)
    
    can_approve = can_manage_requests(request.user)
            
    return render(request, 'accounts/leave.html', {
        'active_page': 'leave',
        'can_approve': can_approve,
    })


@login_required
def leave_approval_view(request):
    """
    Trang giao diện Phê duyệt Nghỉ phép. MOCK DATA.
    - Chỉ dành cho HR, Manager, Leader, Admin.
    """
    ensure_profile(request.user)
    
    can_approve = can_manage_requests(request.user)
            
    if not can_approve:
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('leave')
        
    return render(request, 'accounts/leave_approval.html', {
        'active_page': 'leave',  # giữ sidebar highlight ở phần mục Nghỉ phép
    })


@login_required
def overtime_view(request):
    """
    Trang giao diện Tăng ca cá nhân. MOCK DATA.
    - Hiển thị danh sách overtime của chính mình và biểu đồ tĩnh.
    - Hiển thị nút Phê duyệt nếu user có quyền.
    """
    ensure_profile(request.user)
    
    can_approve = can_manage_requests(request.user)
            
    return render(request, 'accounts/overtime.html', {
        'active_page': 'overtime',
        'can_approve': can_approve,
    })


@login_required
def overtime_approval_view(request):
    """
    Trang giao diện Phê duyệt Tăng ca. MOCK DATA.
    """
    ensure_profile(request.user)
    
    can_approve = can_manage_requests(request.user)
            
    if not can_approve:
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('overtime')
        
    return render(request, 'accounts/overtime_approval.html', {
        'active_page': 'overtime', 
    })


@login_required
def statistics_view(request):
    """
    Trang statistics mới:
    - hỗ trợ filter theo tổ chức
    - hỗ trợ filter theo thời gian
    - giới hạn dữ liệu theo role đang đăng nhập
    """
    ensure_profile(request.user)
    
    if not can_access_statistics(request.user):
        messages.error(request, 'Bạn không có quyền xem trang statistics.')
        return redirect('dashboard')

    context = build_statistics_page_context(request.user, request.GET)
    context['active_page'] = 'statistics'
    return render(request, 'accounts/statistics.html', context)


@login_required
def statistics_export_csv_view(request):
    """Xuất bảng tổng hợp statistics ra CSV để Excel mở trực tiếp."""
    ensure_profile(request.user)

    if not can_access_statistics(request.user):
        messages.error(request, 'Bạn không có quyền xuất statistics.')
        return redirect('dashboard')

    context = build_statistics_page_context(request.user, request.GET)
    time_range = context['time_range']
    file_name = (
        f"statistics_{time_range['start_date']:%Y%m%d}_{time_range['end_date']:%Y%m%d}.csv"
    )

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Bao cao statistics'])
    for item in context['statistics_sections']['filter_summary']:
        writer.writerow([item])
    writer.writerow([])
    writer.writerow([
        'Nhan vien',
        'Username',
        'Phong ban',
        'Quan ly',
        'Leader',
        'Ngay nghi',
        'So don nghi',
        'Gio tang ca',
        'Di tre',
        'Nghi lam',
        'Ty le cham cong',
    ])

    for row in context['statistics_sections']['summary_rows']:
        writer.writerow([
            row['employee_name'],
            row['employee_username'],
            row['department'],
            row['manager_name'],
            row['leader_name'],
            row['leave_days'],
            row['leave_requests'],
            row['overtime_hours'],
            row['late_count'],
            row['absence_days'],
            row['attendance_rate'],
        ])

    return response


@login_required
def statistics_print_view(request):
    """Trang in tối giản để người dùng lưu PDF từ trình duyệt."""
    ensure_profile(request.user)

    if not can_access_statistics(request.user):
        messages.error(request, 'Bạn không có quyền in statistics.')
        return redirect('dashboard')

    context = build_statistics_page_context(request.user, request.GET)
    return render(request, 'accounts/statistics_print.html', context)

@login_required
def report_view(request):
    """
    Trang Báo cáo cá nhân.
    - Hiển thị báo cáo tự tạo.
    - Nút truy cập Hộp thư dành cho quản lý.
    """
    ensure_profile(request.user)
    
    is_manager = can_manage_requests(request.user)
            
    return render(request, 'accounts/report.html', {
        'active_page': 'reports',
        'is_manager': is_manager,
    })

@login_required
def report_inbox_view(request):
    """
    Hộp thư nhận báo cáo từ nhân viên.
    Chỉ cho phép Manager, HR, Leader, Admin.
    """
    ensure_profile(request.user)
    
    is_manager = can_manage_requests(request.user)
            
    if not is_manager:
        messages.error(request, 'Bạn không có quyền xem hộp thư báo cáo!')
        return redirect('reports')
        
    return render(request, 'accounts/report_inbox.html', {
        'active_page': 'reports', 
    })


@login_required
def ticket_list_view(request):
    """
    Trang Quản lý Hỗ trợ & Khiếu nại cá nhân.
    - Hiển thị danh sách ticket của chính mình.
    - Nút xử lý nếu user có quyền Manager/HR.
    """
    ensure_profile(request.user)
    
    can_process = can_manage_requests(request.user)
            
    return render(request, 'accounts/tickets.html', {
        'active_page': 'tickets',
        'can_process': can_process,
    })

@login_required
def ticket_process_view(request):
    """
    Trang Xử lý Hỗ trợ & Khiếu nại (Quản lý).
    """
    ensure_profile(request.user)
    
    can_process = can_manage_requests(request.user)
            
    if not can_process:
        messages.error(request, 'Bạn không có quyền truy cập trang xử lý ticket!')
        return redirect('tickets')
        
    return render(request, 'accounts/ticket_process.html', {
        'active_page': 'tickets', 
    })


@login_required
def rewards_penalties_view(request):
    """
    Trang Quản lý Khen thưởng & Xử phạt cá nhân.
    - Nút đến trang phê duyệt nếu user có quyền Manager/HR/Admin.
    """
    ensure_profile(request.user)
    
    can_approve = can_manage_requests(request.user)
            
    return render(request, 'accounts/rewards_penalties.html', {
        'active_page': 'rewards',
        'can_approve': can_approve,
    })

@login_required
def rewards_penalties_approval_view(request):
    """
    Trang Phê duyệt Khen thưởng & Xử phạt.
    """
    ensure_profile(request.user)
    
    can_approve = can_manage_requests(request.user)
            
    if not can_approve:
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('rewards_penalties')
        
    return render(request, 'accounts/rewards_penalties_approval.html', {
        'active_page': 'rewards', 
    })



@login_required
def settings_view(request):
    """
    Trang Cài đặt chung (HRMS Settings).
    Hiển thị giao diện tab dọc. Admin thấy cấu hình Cty, HR thấy cấu hình Luật.
    """
    ensure_profile(request.user)
    
    is_admin = user_has_role(request.user, Role.ADMIN)
    is_hr = user_has_role(request.user, Role.HR)
        
    return render(request, 'accounts/settings.html', {
        'active_page': 'settings',
        'is_admin': is_admin,
        'is_hr': is_hr,
    })


@login_required
@require_POST
def switch_role_view(request):
    """
    DEV TOOL: Giúp superuser chuyển đổi vai trò nhanh chóng để test giao diện.
    Chỉ hiển thị và hoạt động đổi với Superuser.
    """
    if not request.user.is_superuser:
        messages.error(request, 'Tính năng Switch Role này chỉ dành cho tài khoản Admin/Dev khởi tạo (Superuser).')
        return redirect('dashboard')
        
    role_name = request.POST.get('role_name')
    ensure_profile(request.user)
    
    if role_name:
        role, created = Role.objects.get_or_create(name=role_name)
        request.user.profile.role = role
        request.user.profile.save()
        messages.success(request, f'[DEV] Đã mô phỏng trải nghiệm với vai trò: {role.get_name_display()}')
    else:
        request.user.profile.role = None
        request.user.profile.save()
        messages.success(request, f'[DEV] Đã gỡ Role. Tài khoản trở về trạng thái chưa cấp quyền.')
        
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

# =============================================================================
# HR VIEWS: Tạo hồ sơ nhân viên (chỉ cho HR)
# =============================================================================

@login_required
@user_passes_test(is_hr_user)
def hr_create_profile_view(request):
    """
    Trang tạo hồ sơ nhan su moi (danh cho HR).
    - GET: hiển thị form tạo hồ sơ
    - POST: tạo UserProfile + tài khoản Django tự động
    - Thông tin công việc và hợp đồng là bắt buộc
    - Thông tin cá nhân có thể để trống để nhân viên tự bổ sung sau
    """
    ensure_profile(request.user)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        dob = request.POST.get('date_of_birth', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        employee_type = request.POST.get('employee_type', '').strip()
        department = request.POST.get('department', '').strip()
        position = request.POST.get('position', '').strip()
        workplace = request.POST.get('workplace', '').strip()
        probation_start = request.POST.get('probation_start', '').strip()
        official_start_date = request.POST.get('official_start_date', '').strip()
        contract_number = request.POST.get('contract_number', '').strip()
        contract_type = request.POST.get('contract_type', '').strip()
        contract_signed_date = request.POST.get('contract_signed_date', '').strip()
        contract_start_date = request.POST.get('contract_start_date', '').strip()
        contract_end_date = request.POST.get('contract_end_date', '').strip()
        contract_annual_leave_days_raw = request.POST.get('contract_annual_leave_days', '').strip()
        contract_standard_shift = request.POST.get('contract_standard_shift', '').strip()
        contract_attachment_reference = request.POST.get('contract_attachment_reference', '').strip()
        work_status = request.POST.get('work_status', '').strip()
        manager_user_id = request.POST.get('manager_user', '').strip()
        leader_user_id = request.POST.get('leader_user', '').strip()
        role_name = request.POST.get('role', '').strip()
        auto_create = request.POST.get('auto_create_account') == 'on'
        manager_user = User.objects.filter(pk=manager_user_id).first() if manager_user_id else None
        leader_user = User.objects.filter(pk=leader_user_id).first() if leader_user_id else None
        contract_annual_leave_days = None
        
        # Validation
        errors = []
        if not employee_id:
            errors.append('Mã nhân viên không được để trống.')
        elif UserProfile.objects.filter(employee_id=employee_id).exists():
            errors.append(f'Mã nhân viên "{employee_id}" đã tồn tại.')
        if not department:
            errors.append('Phòng ban không được để trống.')
        if not position:
            errors.append('Chức vụ không được để trống.')
        if not employee_type:
            errors.append('Loại nhân viên không được để trống.')
        if not workplace:
            errors.append('Nơi làm việc không được để trống.')
        if not probation_start:
            errors.append('Ngày bắt đầu thử việc không được để trống.')
        if not official_start_date:
            errors.append('Ngày làm việc chính thức không được để trống.')
        if not work_status:
            errors.append('Trạng thái làm việc không được để trống.')
        if not manager_user:
            errors.append('Cần gán quản lý trực tiếp.')
        if not leader_user:
            errors.append('Cần gán leader phụ trách.')
        if not contract_number:
            errors.append('Số hợp đồng không được để trống.')
        if not contract_type:
            errors.append('Loại hợp đồng không được để trống.')
        if not contract_signed_date:
            errors.append('Ngày ký hợp đồng không được để trống.')
        if not contract_start_date:
            errors.append('Ngày bắt đầu hiệu lực không được để trống.')
        if not contract_annual_leave_days_raw:
            errors.append('Số ngày nghỉ phép/năm không được để trống.')
        else:
            try:
                contract_annual_leave_days = int(contract_annual_leave_days_raw)
                if contract_annual_leave_days < 0:
                    errors.append('Số ngày nghỉ phép/năm phải từ 0 trở lên.')
            except ValueError:
                errors.append('Số ngày nghỉ phép/năm phải là số nguyên.')
        if not contract_standard_shift:
            errors.append('Ca làm tiêu chuẩn không được để trống.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(
                request,
                'accounts/hr_create_profile.html',
                build_hr_create_profile_context(request.POST),
            )
        
        if auto_create:
            # Tự động tạo tài khoản Django
            username = employee_id.lower().replace(' ', '')
            password = f'{employee_id}@2026'
            
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" đã tồn tại. Vui lòng đổi Mã NV.')
                return render(
                    request,
                    'accounts/hr_create_profile.html',
                    build_hr_create_profile_context(request.POST),
                )
            
            user = User.objects.create_user(username=username, email=email, password=password)
            profile = ensure_profile(user)
            profile.full_name = full_name
            profile.phone_number = phone
            profile.date_of_birth = dob
            profile.employee_id = employee_id
            profile.employee_type = employee_type
            profile.department = department
            profile.position = position
            profile.workplace = workplace
            profile.probation_start = probation_start
            profile.official_start_date = official_start_date
            profile.contract_number = contract_number
            profile.contract_type = contract_type
            profile.contract_signed_date = contract_signed_date
            profile.contract_start_date = contract_start_date
            profile.contract_end_date = contract_end_date
            profile.contract_annual_leave_days = contract_annual_leave_days
            profile.contract_standard_shift = contract_standard_shift
            profile.contract_attachment_reference = contract_attachment_reference
            profile.work_status = work_status
            profile.manager_user = manager_user
            profile.leader_user = leader_user
            
            if role_name:
                role, _ = Role.objects.get_or_create(name=role_name)
                profile.role = role
            
            profile.save()
            
            display_name = full_name or employee_id
            messages.success(
                request,
                f'✅ Đã tạo hồ sơ và tài khoản cho "{display_name}" thành công! '
                f'Username: {username} | Mật khẩu: {password}'
            )
        else:
            display_name = full_name or employee_id or 'nhân viên mới'
            messages.success(
                request,
                f'✅ Đã mô phỏng lưu hồ sơ "{display_name}". '
                'Chế độ chưa tạo tài khoản hiện vẫn là demo UI nên chưa ghi dữ liệu thật.'
            )
        
        return redirect('hr_create_profile')
    
    return render(
        request,
        'accounts/hr_create_profile.html',
        build_hr_create_profile_context(),
    )


# =============================================================================
# ADMIN VIEWS: User Management (chỉ cho Admin / superuser)
# =============================================================================

@login_required
@user_passes_test(can_manage_work_info)
def user_list_view(request):
    """
    Danh sách tất cả hồ sơ nhân sự trong hệ thống.
    HR/Admin có thể xem. Riêng thao tác nhạy cảm vẫn chỉ dành cho Admin.

    Template MỚI: accounts/user_management.html (thay vì user_list.html cũ)
    Context:
      - users: QuerySet tất cả user + profile + role + permissions
      - active_page: để sidebar highlight đúng menu
    """
    users = User.objects.all().select_related('profile__role').prefetch_related(
        'profile__permissions'
    ).order_by('-date_joined')

    # Đảm bảo mọi user đều có profile
    for user in users:
        ensure_profile(user)

    return render(request, 'accounts/user_management.html', {
        'users': users,
        'active_page': 'users',  # Sidebar highlight
        'can_manage_system_users': is_admin_user(request.user),
        'can_manage_work_info': can_manage_work_info(request.user),
    })


@login_required
@user_passes_test(can_manage_work_info)
def edit_work_info_view(request, user_id):
    """
    Cập nhật toàn bộ dữ liệu đang lưu trong hồ sơ nhân viên.
    HR/Admin có thể sửa cả thông tin cá nhân, công việc và hợp đồng hiện tại.
    Vai trò hệ thống vẫn được giữ ở màn hình riêng để tránh nhầm với cơ cấu tổ chức.
    """
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)

    manager_queryset = get_manager_user_queryset()
    leader_queryset = get_leader_user_queryset()

    if request.method == 'POST':
        form = EmployeeProfileForm(
            request.POST,
            manager_queryset=manager_queryset,
            leader_queryset=leader_queryset,
            current_user=target_user,
        )
        if form.is_valid():
            target_user.email = form.cleaned_data['email']
            target_user.save()
            profile.full_name = form.cleaned_data['full_name']
            profile.phone_number = form.cleaned_data['phone_number']
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.employee_id = form.cleaned_data['employee_id']
            profile.department = form.cleaned_data['department']
            profile.employee_type = form.cleaned_data['employee_type']
            profile.position = form.cleaned_data['position']
            profile.workplace = form.cleaned_data['workplace']
            profile.probation_start = form.cleaned_data['probation_start']
            profile.official_start_date = form.cleaned_data['official_start_date']
            profile.contract_number = form.cleaned_data['contract_number']
            profile.contract_type = form.cleaned_data['contract_type']
            profile.contract_signed_date = form.cleaned_data['contract_signed_date']
            profile.contract_start_date = form.cleaned_data['contract_start_date']
            profile.contract_end_date = form.cleaned_data['contract_end_date']
            profile.contract_annual_leave_days = form.cleaned_data['contract_annual_leave_days']
            profile.contract_standard_shift = form.cleaned_data['contract_standard_shift']
            profile.contract_attachment_reference = form.cleaned_data['contract_attachment_reference']
            profile.work_status = form.cleaned_data['work_status']
            profile.manager_user = form.cleaned_data['manager_user']
            profile.leader_user = form.cleaned_data['leader_user']
            profile.save()
            messages.success(request, f'Đã cập nhật hồ sơ nhân sự cho "{target_user.username}".')
            return redirect('user_list')
    else:
        form = EmployeeProfileForm(
            initial={
                'full_name': profile.full_name,
                'email': target_user.email,
                'phone_number': profile.phone_number,
                'date_of_birth': profile.date_of_birth,
                'employee_id': profile.employee_id,
                'department': profile.department,
                'employee_type': profile.employee_type,
                'position': profile.position,
                'workplace': profile.workplace,
                'probation_start': profile.probation_start,
                'official_start_date': profile.official_start_date,
                'contract_number': profile.contract_number,
                'contract_type': profile.contract_type,
                'contract_signed_date': profile.contract_signed_date,
                'contract_start_date': profile.contract_start_date,
                'contract_end_date': profile.contract_end_date,
                'contract_annual_leave_days': profile.contract_annual_leave_days,
                'contract_standard_shift': profile.contract_standard_shift,
                'contract_attachment_reference': profile.contract_attachment_reference,
                'work_status': profile.work_status,
                'manager_user': profile.manager_user,
                'leader_user': profile.leader_user,
            },
            manager_queryset=manager_queryset,
            leader_queryset=leader_queryset,
            current_user=target_user,
        )

    return render(request, 'accounts/edit_work_info.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
        'can_manage_system_users': is_admin_user(request.user),
    })


@login_required
@user_passes_test(is_admin_user)
def assign_role_view(request, user_id):
    """
    Form thay đổi vai trò của user.
    1. Admin vào /users/5/role/ → thấy dropdown 4 vai trò
    2. Chọn vai trò mới → click "Lưu"
    3. Profile được cập nhật, hiện thông báo thành công

    Template: accounts/assign_role.html
    """
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)

    if request.method == 'POST':
        form = AssignRoleForm(request.POST)
        if form.is_valid():
            profile.role = form.cleaned_data['role']
            profile.save()
            messages.success(
                request,
                f"Vai trò của '{target_user.username}' đã được cập nhật thành "
                f"'{profile.role}' thành công."
                if profile.role else
                f"Đã gỡ vai trò khỏi '{target_user.username}'."
            )
            return redirect('user_list')
    else:
        form = AssignRoleForm(initial={'role': profile.role})

    return render(request, 'accounts/assign_role.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
    })


@login_required
@user_passes_test(is_admin_user)
def assign_permissions_view(request, user_id):
    """
    Form gán/gỡ quyền cho user.
    1. Admin vào /users/5/permissions/ → thấy checkboxes
    2. Tick = có quyền, bỏ tick = không có
    3. Click "Lưu" → quyền được cập nhật

    Template: accounts/assign_permissions.html
    """
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)

    if request.method == 'POST':
        form = AssignPermissionsForm(request.POST)
        if form.is_valid():
            profile.permissions.set(form.cleaned_data['permissions'])
            messages.success(
                request,
                f"Quyền của '{target_user.username}' đã được cập nhật."
            )
            return redirect('user_list')
    else:
        form = AssignPermissionsForm(
            initial={'permissions': profile.permissions.all()}
        )

    return render(request, 'accounts/assign_permissions.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
    })


@login_required
@user_passes_test(is_admin_user)
def delete_user_view(request, user_id):
    """
    Xóa tài khoản. Chỉ superuser/Master mới làm được.
    - GET: hiện trang xác nhận
    - POST: xóa user thật
    - Không thể tự xóa mình

    Template: accounts/delete_user.html
    """
    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        messages.error(request, "Bạn không thể xóa tài khoản của chính mình.")
        return redirect('user_list')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f"Tài khoản '{username}' đã được xóa.")
        return redirect('user_list')

    return render(request, 'accounts/delete_user.html', {
        'target_user': target_user,
        'active_page': 'users',
    })


# =============================================================================
# VIEWS MỚI: Khóa/Mở khóa + Reset Password
# =============================================================================

@login_required
@user_passes_test(is_admin_user)
def toggle_user_active_view(request, user_id):
    """
    Khóa hoặc mở khóa tài khoản user.
    - Chỉ xử lý POST request (an toàn, tránh khóa nhầm qua GET)
    - Đổi trạng thái is_active: True ↔ False
    - Không cho phép khóa chính mình

    Khi is_active=False, Django sẽ KHÔNG cho user đó đăng nhập.
    URL: /users/<id>/toggle-active/
    """
    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        messages.error(request, "Bạn không thể khóa tài khoản của chính mình.")
        return redirect('user_list')

    if request.method == 'POST':
        # Đảo trạng thái: active → inactive, inactive → active
        target_user.is_active = not target_user.is_active
        target_user.save()

        if target_user.is_active:
            messages.success(request, f"Đã mở khóa tài khoản '{target_user.username}'.")
        else:
            messages.warning(request, f"Đã khóa tài khoản '{target_user.username}'.")

    return redirect('user_list')


@login_required
@user_passes_test(is_admin_user)
def reset_user_password_view(request, user_id):
    """
    Reset mật khẩu cho user.
    - Chỉ xử lý POST request
    - Đặt mật khẩu mới mặc định: "Password@123"
    - Admin cần thông báo cho user biết mật khẩu mới

    TODO: Sau này có thể nâng cấp thành:
      - Gửi email reset password
      - Tạo mật khẩu ngẫu nhiên
      - Bắt user đổi mật khẩu khi đăng nhập lần đầu sau reset

    URL: /users/<id>/reset-password/
    """
    target_user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        # Đặt mật khẩu mặc định
        default_password = "Password@123"
        target_user.set_password(default_password)
        target_user.save()

        messages.success(
            request,
            f"Mật khẩu của '{target_user.username}' đã được reset thành: {default_password}"
        )

    return redirect('user_list')

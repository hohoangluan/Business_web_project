"""
==============================================================================
STATISTICS SERVICES
==============================================================================
Logic thống kê tổng hợp — thu thập dữ liệu từ các module khác.
Tách từ accounts/views.py — giữ nguyên logic, cập nhật imports.
==============================================================================
"""

import json
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import Role
from accounts.services import (
    ensure_profile, ensure_work_info,
    get_user_role_name, user_has_role,
    has_admin_business_access,
    get_user_display_name, get_department_label,
    get_manager_display_name, get_leader_display_name,
)
from stats_reports.services.statistics_data import build_statistics_records
from performance.services.evaluation_data import build_evaluation_records
from rewards_discipline.services.rewards_data import build_rewards_penalties_records


STATISTICS_TYPE_OPTIONS = [
    {'value': 'all', 'label': 'Tất cả'},
    {'value': 'leave', 'label': 'Nghỉ phép'},
    {'value': 'attendance', 'label': 'Chấm công'},
    {'value': 'summary', 'label': 'Tổng hợp'},
    {'value': 'evaluation', 'label': 'Đánh giá'},
    {'value': 'rewards', 'label': 'Khen thưởng & Xử phạt'},
]

STATISTICS_TYPE_LABEL_MAP = {
    item['value']: item['label'] for item in STATISTICS_TYPE_OPTIONS
}


def get_statistics_scope(user):
    """Xác định phạm vi dữ liệu mà user được xem."""
    ensure_profile(user)
    work_info = ensure_work_info(user)

    if has_admin_business_access(user) or user_has_role(user, Role.HR):
        return {
            'scope_name': 'company', 'scope_label': 'Toàn công ty',
            'locked_department': '', 'locked_leader': '', 'error_message': '',
        }

    if user_has_role(user, Role.MANAGER):
        if not work_info.department:
            return {
                'scope_name': 'manager', 'scope_label': '',
                'locked_department': '', 'locked_leader': '',
                'error_message': 'Manager chưa được gán phòng ban.',
            }
        return {
            'scope_name': 'manager',
            'scope_label': f'Phòng ban: {work_info.department}',
            'locked_department': work_info.department,
            'locked_leader': '', 'error_message': '',
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
        'scope_name': 'none', 'scope_label': '',
        'locked_department': '', 'locked_leader': '',
        'error_message': 'Bạn không có quyền truy cập statistics.',
    }


def get_scope_users(user, scope):
    """Lấy danh sách user trong phạm vi statistics."""
    users = User.objects.select_related('profile__role').order_by(
        'profile__full_name', 'username'
    )
    for item in users:
        ensure_profile(item)
        ensure_work_info(item)

    if scope['scope_name'] == 'company':
        return [
            item for item in users
            if get_user_role_name(item) != Role.ADMIN
        ]

    if scope['scope_name'] == 'manager':
        return [
            item for item in users
            if item.pk != user.pk and item.work_info.department == scope['locked_department']
        ]

    if scope['scope_name'] == 'leader':
        return [
            item for item in users
            if item.pk != user.pk and item.work_info.leader_user_id == user.id
        ]

    return []


def parse_date_input(raw_value):
    """Đọc giá trị YYYY-MM-DD từ query string."""
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, '%Y-%m-%d').date()
    except ValueError:
        return None


def get_time_range_from_params(params):
    """Xử lý bộ lọc thời gian."""
    today = timezone.localdate()
    period = params.get('period', 'this_month')
    from_date_raw = params.get('from_date', '')
    to_date_raw = params.get('to_date', '')

    if period == 'last_7_days':
        start_date, end_date, label = today - timedelta(days=6), today, '7 ngày gần nhất'
    elif period == 'last_30_days':
        start_date, end_date, label = today - timedelta(days=29), today, '30 ngày gần nhất'
    elif period == 'this_quarter':
        q_start = ((today.month - 1) // 3) * 3 + 1
        start_date, end_date, label = today.replace(month=q_start, day=1), today, 'Quý này'
    elif period == 'this_year':
        start_date, end_date, label = today.replace(month=1, day=1), today, 'Năm nay'
    elif period == 'custom':
        start_date = parse_date_input(from_date_raw)
        end_date = parse_date_input(to_date_raw)
        if not start_date or not end_date or start_date > end_date:
            start_date, end_date = today.replace(day=1), today
            period, label = 'this_month', 'Tháng này'
        else:
            label = 'Khoảng thời gian tùy chọn'
    else:
        start_date, end_date = today.replace(day=1), today
        period, label = 'this_month', 'Tháng này'

    return {
        'period': period, 'from_date': from_date_raw, 'to_date': to_date_raw,
        'start_date': start_date, 'end_date': end_date, 'label': label,
        'date_range_text': f'{start_date:%d/%m/%Y} - {end_date:%d/%m/%Y}',
    }


def get_statistics_type_from_params(params):
    """Loại thống kê nào đang được chọn."""
    selected_type = params.get('stats_type', 'all')
    if selected_type not in STATISTICS_TYPE_LABEL_MAP:
        selected_type = 'all'
    return selected_type


def build_statistics_filters(scope_users, scope, params):
    """Tạo options dropdown và lọc user theo tổ chức."""
    filtered_users = list(scope_users)
    department_options = sorted({get_department_label(user) for user in scope_users})

    if scope['locked_department']:
        selected_department = scope['locked_department']
    else:
        selected_department = params.get('department', '')
        if selected_department not in department_options:
            selected_department = ''

    if selected_department:
        filtered_users = [u for u in filtered_users if get_department_label(u) == selected_department]

    # Manager filter
    manager_map = {}
    for user in filtered_users:
        wi = ensure_work_info(user)
        if wi.manager_user:
            manager_map[wi.manager_user.username] = get_user_display_name(wi.manager_user)
    manager_options = [{'value': k, 'label': manager_map[k]} for k in sorted(manager_map.keys())]

    selected_manager = params.get('manager', '')
    if selected_manager not in manager_map:
        selected_manager = ''
    if selected_manager:
        filtered_users = [u for u in filtered_users if ensure_work_info(u).manager_user and ensure_work_info(u).manager_user.username == selected_manager]

    # Leader filter
    leader_map = {}
    for user in filtered_users:
        wi = ensure_work_info(user)
        if wi.leader_user:
            leader_map[wi.leader_user.username] = get_user_display_name(wi.leader_user)
    leader_options = [{'value': k, 'label': leader_map[k]} for k in sorted(leader_map.keys())]

    if scope['locked_leader']:
        selected_leader = scope['locked_leader']
    else:
        selected_leader = params.get('leader', '')
        if selected_leader not in leader_map:
            selected_leader = ''
    if selected_leader:
        filtered_users = [u for u in filtered_users if ensure_work_info(u).leader_user and ensure_work_info(u).leader_user.username == selected_leader]

    # Employee filter
    employee_map = {u.username: get_user_display_name(u) for u in filtered_users}
    employee_options = [{'value': k, 'label': employee_map[k]} for k in sorted(employee_map.keys())]

    selected_employee = params.get('employee', '')
    if selected_employee not in employee_map:
        selected_employee = ''
    if selected_employee:
        filtered_users = [u for u in filtered_users if u.username == selected_employee]

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
    """Lọc record theo nhân viên và thời gian."""
    allowed = {u.username for u in filters['filtered_users']}
    return [
        r for r in records
        if r['employee_username'] in allowed
        and time_range['start_date'] <= r['record_date'] <= time_range['end_date']
    ]


def build_statistics_summary_rows(filtered_users, filtered_records):
    """Gom record theo nhân viên."""
    summary = {}
    for user in filtered_users:
        summary[user.username] = {
            'employee_name': get_user_display_name(user),
            'employee_username': user.username,
            'department': get_department_label(user),
            'manager_name': get_manager_display_name(user),
            'leader_name': get_leader_display_name(user),
            'leave_days': 0, 'leave_requests': 0, 'overtime_hours': 0,
            'late_count': 0, 'absence_days': 0,
            'attendance_total': 0, 'attendance_entries': 0, 'attendance_rate': 0,
        }

    for r in filtered_records:
        row = summary.get(r['employee_username'])
        if not row:
            continue
        row['leave_days'] += r['leave_days']
        row['leave_requests'] += r['leave_requests']
        row['overtime_hours'] += r['overtime_hours']
        row['late_count'] += r['late_count']
        row['absence_days'] += r['absence_days']
        row['attendance_total'] += r['attendance_rate']
        row['attendance_entries'] += 1

    rows = []
    for row in summary.values():
        if row['attendance_entries']:
            row['attendance_rate'] = round(row['attendance_total'] / row['attendance_entries'], 1)
        rows.append(row)
    rows.sort(key=lambda x: x['employee_name'].lower())
    return rows


def aggregate_rows(rows, label_key, value_key, empty_label):
    """Helper gom dữ liệu chart theo nhãn."""
    totals = {}
    for row in rows:
        label = row[label_key] or empty_label
        totals[label] = totals.get(label, 0) + row[value_key]
    sorted_items = sorted(totals.items(), key=lambda x: (-x[1], x[0]))
    return {'labels': [x[0] for x in sorted_items], 'values': [x[1] for x in sorted_items]}


def aggregate_record_counts(records, label_key, empty_label):
    """Gom số bản ghi theo nhãn."""
    totals = {}
    for r in records:
        label = r.get(label_key) or empty_label
        totals[label] = totals.get(label, 0) + 1
    sorted_items = sorted(totals.items(), key=lambda x: (-x[1], x[0]))
    return {'labels': [x[0] for x in sorted_items], 'values': [x[1] for x in sorted_items]}


def build_timeline_chart(records, date_key):
    """Tạo chart xu hướng theo ngày."""
    totals = {}
    for r in records:
        raw_date = r.get(date_key)
        if not raw_date:
            continue
        label = raw_date.strftime('%d/%m')
        totals[label] = totals.get(label, 0) + 1
    sorted_items = sorted(totals.items(), key=lambda x: datetime.strptime(x[0], '%d/%m'))
    return {'labels': [x[0] for x in sorted_items], 'values': [x[1] for x in sorted_items]}


def build_evaluation_statistics_rows(records, filtered_employees):
    """Bảng chi tiết đánh giá cho statistics."""
    dept_map = {u.username: get_department_label(u) for u in filtered_employees}
    rows = []
    for r in records:
        rows.append({
            'employee_name': r['employee_name'],
            'employee_username': r['employee_username'],
            'department': dept_map.get(r['employee_username'], 'Chưa phân'),
            'reviewer_name': r['reviewer_name'],
            'reviewer_role': r['reviewer_role'],
            'evaluation_date_display': r['evaluation_date'].strftime('%d/%m/%Y'),
            'evaluation_content': r['evaluation_content'],
            'evidence_reference': r['evidence_reference'],
        })
    return rows


def build_evaluation_statistics_sections(filtered_employees, filtered_records):
    """Card/chart/table cho loại thống kê đánh giá."""
    reviewed = len({r['employee_username'] for r in filtered_records})
    evidence = sum(1 for r in filtered_records if r['evidence_reference'])
    reviewers = len({r['reviewer_username'] for r in filtered_records})
    rows = build_evaluation_statistics_rows(filtered_records, filtered_employees)
    for row in rows:
        row['reviewer_label'] = f"{row['reviewer_name']} ({row['reviewer_role']})"
    reviewer_src = [{'reviewer_label': r['reviewer_label']} for r in rows]

    return {
        'cards': [
            {'label': 'Tổng số đánh giá', 'value': len(filtered_records)},
            {'label': 'Nhân viên đã có đánh giá', 'value': reviewed},
            {'label': 'Đánh giá có minh chứng', 'value': evidence},
            {'label': 'Người đánh giá có dữ liệu', 'value': reviewers},
        ],
        'rows': rows,
        'by_department_json': json.dumps(aggregate_record_counts(rows, 'department', 'Chưa phân')),
        'by_reviewer_json': json.dumps(aggregate_record_counts(reviewer_src, 'reviewer_label', 'Chưa rõ')),
        'by_employee_json': json.dumps(aggregate_record_counts(rows, 'employee_name', 'Chưa rõ')),
        'trend_json': json.dumps(build_timeline_chart(filtered_records, 'evaluation_date')),
    }


def build_rewards_statistics_rows(records):
    """Bảng chi tiết thưởng/phạt cho statistics."""
    rows = []
    for r in records:
        signed = f"+{r['amount']:,}đ" if r['record_type'] == 'reward' else f"-{r['amount']:,}đ"
        rows.append({
            'employee_name': r['employee_name'], 'employee_username': r['employee_username'],
            'department': r['department'], 'proposer_name': r['proposer_name'],
            'proposer_role': r['proposer_role'], 'type_label': r['type_label'],
            'amount_display': signed, 'status': r['status'],
            'application_date_display': r['application_date'].strftime('%d/%m/%Y'),
            'reason_title': r['reason_title'], 'reason_detail': r['reason_detail'],
        })
    return rows


def build_rewards_statistics_sections(filtered_records):
    """Card/chart/table cho thống kê khen thưởng và xử phạt."""
    reward_total = sum(r['amount'] for r in filtered_records if r['record_type'] == 'reward')
    penalty_total = sum(r['amount'] for r in filtered_records if r['record_type'] == 'penalty')
    rows = build_rewards_statistics_rows(filtered_records)
    proposer_src = [{'proposer_label': f"{r['proposer_name']} ({r['proposer_role']})"} for r in rows]
    employee_src = [{'employee_name': r['employee_name']} for r in rows]
    type_src = [{'type_label': r['type_label']} for r in rows]

    return {
        'cards': [
            {'label': 'Tổng số phiếu', 'value': len(filtered_records)},
            {'label': 'Tổng tiền thưởng', 'value': f"+{reward_total:,}đ"},
            {'label': 'Tổng tiền phạt', 'value': f"-{penalty_total:,}đ"},
            {'label': 'Chênh lệch', 'value': f"{reward_total - penalty_total:+,}đ"},
        ],
        'rows': rows,
        'by_department_json': json.dumps(aggregate_record_counts(rows, 'department', 'Chưa phân')),
        'by_proposer_json': json.dumps(aggregate_record_counts(proposer_src, 'proposer_label', 'Chưa rõ')),
        'by_employee_json': json.dumps(aggregate_record_counts(employee_src, 'employee_name', 'Chưa rõ')),
        'by_type_json': json.dumps(aggregate_record_counts(type_src, 'type_label', 'Chưa rõ')),
    }


def filter_evaluation_records_by_time(records, time_range):
    return [r for r in records if time_range['start_date'] <= r['evaluation_date'] <= time_range['end_date']]


def filter_rewards_records_by_time(records, time_range):
    return [r for r in records if time_range['start_date'] <= r['application_date'] <= time_range['end_date']]


def build_empty_statistics_sections():
    """Context rỗng."""
    ec = json.dumps({'labels': [], 'values': []})
    return {
        'summary_rows': [], 'summary_cards': [], 'leave_cards': [], 'attendance_cards': [],
        'evaluation_cards': [], 'evaluation_rows': [],
        'rewards_cards': [], 'rewards_rows': [],
        'leave_by_department_json': ec, 'leave_by_leader_json': ec,
        'leave_by_employee_json': ec, 'overtime_by_employee_json': ec,
        'discipline_by_employee_json': json.dumps({'labels': [], 'late_values': [], 'absence_values': []}),
        'evaluation_by_department_json': ec, 'evaluation_by_reviewer_json': ec,
        'evaluation_by_employee_json': ec, 'evaluation_trend_json': ec,
        'rewards_by_department_json': ec, 'rewards_by_proposer_json': ec,
        'rewards_by_employee_json': ec, 'rewards_by_type_json': ec,
        'filter_summary': [],
    }


def build_statistics_sections(summary_rows, eval_sections, rewards_sections, time_range, filters, scope):
    """Chuẩn bị toàn bộ card, chart và bảng."""
    count = len(summary_rows)
    t_leave = sum(r['leave_days'] for r in summary_rows)
    t_requests = sum(r['leave_requests'] for r in summary_rows)
    t_ot = sum(r['overtime_hours'] for r in summary_rows)
    t_late = sum(r['late_count'] for r in summary_rows)
    t_absence = sum(r['absence_days'] for r in summary_rows)
    avg_att = round(sum(r['attendance_rate'] for r in summary_rows) / count, 1) if count else 0

    leave_by_dept = aggregate_rows(summary_rows, 'department', 'leave_days', 'Chưa phân')
    leave_by_leader = aggregate_rows(summary_rows, 'leader_name', 'leave_days', 'Chưa gán')
    leave_by_emp = {'labels': [r['employee_name'] for r in summary_rows[:8]], 'values': [r['leave_days'] for r in summary_rows[:8]]}
    ot_by_emp = {'labels': [r['employee_name'] for r in summary_rows[:8]], 'values': [r['overtime_hours'] for r in summary_rows[:8]]}
    disc_by_emp = {'labels': [r['employee_name'] for r in summary_rows[:8]], 'late_values': [r['late_count'] for r in summary_rows[:8]], 'absence_values': [r['absence_days'] for r in summary_rows[:8]]}

    fsummary = [
        f"Phạm vi: {scope['scope_label'] or 'Không xác định'}",
        f"Thời gian: {time_range['label']} ({time_range['date_range_text']})",
    ]
    if filters['selected_department']:
        fsummary.append(f"Phòng ban: {filters['selected_department']}")
    if filters['selected_manager']:
        fsummary.append(f"Manager: {filters['selected_manager_label'] or filters['selected_manager']}")
    if filters['selected_leader']:
        fsummary.append(f"Leader: {filters['selected_leader_label'] or filters['selected_leader']}")
    if filters['selected_employee']:
        fsummary.append(f"Nhân viên: {filters['selected_employee_label'] or filters['selected_employee']}")

    return {
        'summary_rows': summary_rows,
        'summary_cards': [
            {'label': 'Số nhân viên', 'value': count},
            {'label': 'Tổng giờ tăng ca', 'value': t_ot},
            {'label': 'Số lần đi trễ', 'value': t_late},
            {'label': 'Tỷ lệ chấm công TB', 'value': f'{avg_att}%'},
        ],
        'leave_cards': [
            {'label': 'Tổng ngày nghỉ', 'value': t_leave},
            {'label': 'Số đơn nghỉ', 'value': t_requests},
            {'label': 'Leader có dữ liệu', 'value': len(leave_by_leader['labels'])},
            {'label': 'Phòng ban có dữ liệu', 'value': len(leave_by_dept['labels'])},
        ],
        'attendance_cards': [
            {'label': 'Tổng giờ tăng ca', 'value': t_ot},
            {'label': 'Số lần đi trễ', 'value': t_late},
            {'label': 'Số ngày nghỉ làm', 'value': t_absence},
            {'label': 'Tỷ lệ đúng giờ TB', 'value': f'{avg_att}%'},
        ],
        'leave_by_department_json': json.dumps(leave_by_dept),
        'leave_by_leader_json': json.dumps(leave_by_leader),
        'leave_by_employee_json': json.dumps(leave_by_emp),
        'overtime_by_employee_json': json.dumps(ot_by_emp),
        'discipline_by_employee_json': json.dumps(disc_by_emp),
        'evaluation_cards': eval_sections['cards'],
        'evaluation_rows': eval_sections['rows'],
        'evaluation_by_department_json': eval_sections['by_department_json'],
        'evaluation_by_reviewer_json': eval_sections['by_reviewer_json'],
        'evaluation_by_employee_json': eval_sections['by_employee_json'],
        'evaluation_trend_json': eval_sections['trend_json'],
        'rewards_cards': rewards_sections['cards'],
        'rewards_rows': rewards_sections['rows'],
        'rewards_by_department_json': rewards_sections['by_department_json'],
        'rewards_by_proposer_json': rewards_sections['by_proposer_json'],
        'rewards_by_employee_json': rewards_sections['by_employee_json'],
        'rewards_by_type_json': rewards_sections['by_type_json'],
        'filter_summary': fsummary,
    }


def build_statistics_page_context(user, params):
    """Hàm trung tâm cho statistics — web, CSV, print đều dùng."""
    scope = get_statistics_scope(user)
    selected_type = get_statistics_type_from_params(params)
    if scope['error_message']:
        return {
            'scope': scope,
            'time_range': get_time_range_from_params(params),
            'selected_stats_type': selected_type,
            'selected_stats_type_label': STATISTICS_TYPE_LABEL_MAP[selected_type],
            'stats_type_options': STATISTICS_TYPE_OPTIONS,
            'filters': {
                'department_options': [], 'manager_options': [],
                'leader_options': [], 'employee_options': [],
                'selected_department': '', 'selected_manager': '',
                'selected_leader': scope['locked_leader'], 'selected_employee': '',
                'selected_manager_label': '', 'selected_leader_label': '',
                'selected_employee_label': '', 'filtered_users': [],
                'department_locked': bool(scope['locked_department']),
                'leader_locked': bool(scope['locked_leader']),
            },
            'statistics_error_message': scope['error_message'],
            'statistics_sections': build_empty_statistics_sections(),
        }

    scope_users = get_scope_users(user, scope)
    filters = build_statistics_filters(scope_users, scope, params)
    time_range = get_time_range_from_params(params)
    records = build_statistics_records(filters['filtered_users'], time_range)
    filtered_records = filter_statistics_records(records, filters, time_range)
    summary_rows = build_statistics_summary_rows(filters['filtered_users'], filtered_records)

    emp_users = [u for u in filters['filtered_users'] if get_user_role_name(u) == Role.EMPLOYEE]
    eval_records = build_evaluation_records(emp_users)
    filtered_eval = filter_evaluation_records_by_time(eval_records, time_range)
    rewards_records = build_rewards_penalties_records(emp_users)
    filtered_rewards = filter_rewards_records_by_time(rewards_records, time_range)

    sections = build_statistics_sections(
        summary_rows,
        build_evaluation_statistics_sections(emp_users, filtered_eval),
        build_rewards_statistics_sections(filtered_rewards),
        time_range, filters, scope,
    )

    error_msg = ''
    if not scope_users:
        error_msg = 'Chưa có nhân viên nào thuộc phạm vi quản lý để thống kê.'
    elif not filters['filtered_users']:
        error_msg = 'Không tìm thấy nhân viên phù hợp với bộ lọc.'

    return {
        'scope': scope,
        'time_range': time_range,
        'selected_stats_type': selected_type,
        'selected_stats_type_label': STATISTICS_TYPE_LABEL_MAP[selected_type],
        'stats_type_options': STATISTICS_TYPE_OPTIONS,
        'filters': filters,
        'statistics_sections': sections,
        'statistics_error_message': error_msg,
    }

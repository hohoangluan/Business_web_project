"""
==============================================================================
PERFORMANCE SERVICES
==============================================================================
Business logic cho đánh giá nhân viên (lưu DB thật).
==============================================================================
"""

import os
from datetime import datetime
from urllib.parse import urlencode
from django.utils import timezone
from django.core.files.storage import default_storage

from accounts.models import Role
from accounts.services import (
    ensure_profile, ensure_work_info,
    get_user_role_name, user_has_role,
    get_user_display_name, get_department_label,
    can_access_evaluations, can_submit_evaluation_demo,
)
from performance.services.evaluation_data import (
    build_evaluation_records,
    build_reviewer_evaluation_records,
)
from performance.models import Evaluation, EvaluationCategory


def create_evaluation(reviewer, employee_user, form_data, uploaded_file=None):
    """
    Tạo đánh giá mới lưu vào database thật.
    Trạng thái mặc định là 'submitted' (đã gửi lên HR).
    """
    category_id = form_data.get('category')
    category = None
    if category_id:
        try:
            category = EvaluationCategory.objects.get(id=category_id)
        except (ValueError, EvaluationCategory.DoesNotExist):
            pass

    evidence_reference = ''
    if uploaded_file:
        path = default_storage.save(f'evaluations/{uploaded_file.name}', uploaded_file)
        evidence_reference = uploaded_file.name

    raw_score = form_data.get('score')
    try:
        score_value = int(raw_score) if raw_score not in (None, '') else None
    except (TypeError, ValueError):
        score_value = None

    evaluation = Evaluation.objects.create(
        employee=employee_user,
        reviewer=reviewer,
        category=category,
        status='submitted',
        score=score_value,
        evaluation_date=form_data.get('evaluation_date'),
        content=form_data.get('evaluation_content', ''),
        evidence_reference=evidence_reference,
    )
    return evaluation


def to_evaluation_dict(evaluation):
    """Chuyển đổi Evaluation model instance thành dict để tương thích với UI."""
    return {
        'id': evaluation.id,
        'employee_username': evaluation.employee.username,
        'employee_name': get_user_display_name(evaluation.employee),
        'reviewer_username': evaluation.reviewer.username,
        'reviewer_name': get_user_display_name(evaluation.reviewer),
        'reviewer_role': get_user_role_name(evaluation.reviewer).title(),
        'category_name': evaluation.category.name if evaluation.category else 'Chưa phân loại',
        'category_id': evaluation.category.id if evaluation.category else None,
        'evaluation_date': evaluation.evaluation_date,
        'evaluation_content': evaluation.content,
        'evidence_reference': evaluation.evidence_reference,
        'status': evaluation.status,
        'status_display': evaluation.get_status_display(),
        'score': evaluation.score,
        'rating': evaluation.rating,
        'rating_display': evaluation.get_rating_display() if evaluation.rating else 'Chưa xếp loại',
        'hr_note': evaluation.hr_note,
        'acknowledged_by_name': get_user_display_name(evaluation.acknowledged_by) if evaluation.acknowledged_by else '',
        'acknowledged_at_display': evaluation.acknowledged_at.strftime('%d/%m/%Y %H:%M') if evaluation.acknowledged_at else '',
    }


def get_pending_evaluations_for_hr(hr_user=None):
    """HR lấy danh sách đánh giá đang chờ xác nhận (status = 'submitted')."""
    return Evaluation.objects.filter(status='submitted').select_related('employee', 'reviewer', 'category')


def get_acknowledged_evaluations_for_hr(hr_user=None):
    """HR lấy danh sách đánh giá đã xác nhận (status = 'acknowledged')."""
    return Evaluation.objects.filter(status='acknowledged').select_related('employee', 'reviewer', 'category')


def acknowledge_evaluation(hr_user, eval_id, note):
    """HR xác nhận đánh giá."""
    try:
        evaluation = Evaluation.objects.get(id=eval_id)
        evaluation.status = 'acknowledged'
        evaluation.acknowledged_by = hr_user
        evaluation.acknowledged_at = timezone.now()
        evaluation.hr_note = note.strip()
        evaluation.save()
        return True, "Xác nhận đánh giá thành công."
    except Evaluation.DoesNotExist:
        return False, "Không tìm thấy đánh giá."


def get_evaluations_for_employee(employee):
    """Nhân viên xem các đánh giá của mình (chỉ xem các đánh giá đã được HR xác nhận)."""
    return Evaluation.objects.filter(employee=employee, status='acknowledged').select_related('reviewer', 'category')


def get_evaluation_scope(user):
    """Đánh giá nhân viên dùng cùng phạm vi với statistics."""
    from stats_reports.services import get_statistics_scope
    return get_statistics_scope(user)


def get_scope_employees_for_evaluations(user, scope):
    """Trang đánh giá chỉ tập trung vào nhân viên (không phải quản lý)."""
    from stats_reports.services import get_scope_users
    scope_users = get_scope_users(user, scope)
    return [
        item for item in scope_users
        if get_user_role_name(item) == Role.EMPLOYEE
    ]


def build_evaluation_filters(scope_employees, scope, params):
    """Tái dùng bộ lọc tổ chức từ statistics."""
    from stats_reports.services import build_statistics_filters
    return build_statistics_filters(scope_employees, scope, params)


def parse_date_input(raw_value):
    """Đọc giá trị YYYY-MM-DD từ query string."""
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, '%Y-%m-%d').date()
    except ValueError:
        return None


def get_evaluation_date_range(params):
    """Bộ lọc ngày cho trang đánh giá."""
    from_date_raw = params.get('from_date', '')
    to_date_raw = params.get('to_date', '')
    from_date = parse_date_input(from_date_raw)
    to_date = parse_date_input(to_date_raw)
    error_message = ''

    if from_date and to_date and from_date > to_date:
        error_message = 'Từ ngày không được lớn hơn đến ngày.'
        from_date = None
        to_date = None

    if from_date and to_date:
        date_range_text = f'{from_date:%d/%m/%Y} - {to_date:%d/%m/%Y}'
    elif from_date:
        date_range_text = f'Từ {from_date:%d/%m/%Y} đến hiện tại'
    elif to_date:
        date_range_text = f'Từ trước đến {to_date:%d/%m/%Y}'
    else:
        date_range_text = 'Tất cả thời gian'

    return {
        'from_date': from_date_raw,
        'to_date': to_date_raw,
        'from_date_value': from_date,
        'to_date_value': to_date,
        'date_range_text': date_range_text,
        'error_message': error_message,
    }


def build_evaluation_statistics_query(params):
    """Từ trang đánh giá đi sang statistics với loại đánh giá."""
    query = {'stats_type': 'evaluation'}
    for key in ['department', 'manager', 'leader', 'employee']:
        value = params.get(key, '').strip()
        if value:
            query[key] = value
    from_date = params.get('from_date', '').strip()
    to_date = params.get('to_date', '').strip()
    if from_date and to_date:
        query['period'] = 'custom'
        query['from_date'] = from_date
        query['to_date'] = to_date
    return urlencode(query)


def build_evaluation_page_query(params, employee_username=''):
    """Giữ bộ lọc khi chuyển giữa danh sách và form đánh giá."""
    query = {}
    for key in ['department', 'manager', 'leader', 'from_date', 'to_date']:
        value = params.get(key, '').strip()
        if value:
            query[key] = value
    if employee_username:
        query['employee'] = employee_username
    return urlencode(query)


def filter_evaluation_records(records, filters, date_range):
    """Lọc đánh giá theo nhân viên và khoảng ngày."""
    allowed_usernames = {user.username for user in filters['filtered_users']}
    filtered = []
    for record in records:
        if record['employee_username'] not in allowed_usernames:
            continue
        if date_range['from_date_value'] and record['evaluation_date'] < date_range['from_date_value']:
            continue
        if date_range['to_date_value'] and record['evaluation_date'] > date_range['to_date_value']:
            continue
        filtered.append(record)
    return filtered


def build_evaluation_sections(filtered_employees, filtered_records, filters, scope, date_range):
    """Chuẩn bị card, chip filter và danh sách hiển thị."""
    reviewed_count = len({r['employee_username'] for r in filtered_records})
    evidence_count = sum(1 for r in filtered_records if r['evidence_reference'])

    filter_summary = [
        f"Phạm vi: {scope['scope_label'] or 'Không xác định'}",
        f"Thời gian: {date_range['date_range_text']}",
    ]
    if filters['selected_department']:
        filter_summary.append(f"Phòng ban: {filters['selected_department']}")
    if filters['selected_manager']:
        filter_summary.append(f"Manager: {filters['selected_manager_label'] or filters['selected_manager']}")
    if filters['selected_leader']:
        filter_summary.append(f"Leader: {filters['selected_leader_label'] or filters['selected_leader']}")
    if filters['selected_employee']:
        filter_summary.append(f"Nhân viên: {filters['selected_employee_label'] or filters['selected_employee']}")

    display_records = []
    for record in filtered_records:
        display_records.append({
            **record,
            'evaluation_date_display': record['evaluation_date'].strftime('%d/%m/%Y'),
        })

    return {
        'summary_cards': [
            {'label': 'Nhân viên trong phạm vi', 'value': len(filtered_employees)},
            {'label': 'Số đánh giá đang hiển thị', 'value': len(filtered_records)},
            {'label': 'Nhân viên đã có đánh giá', 'value': reviewed_count},
            {'label': 'Đánh giá có minh chứng', 'value': evidence_count},
        ],
        'filter_summary': filter_summary,
        'records': display_records,
    }


def build_evaluation_employee_cards(available_users, reviewer_records, params):
    """Danh sách nhân viên để chọn trước khi mở form."""
    review_count_map = {}
    for record in reviewer_records:
        username = record['employee_username']
        review_count_map[username] = review_count_map.get(username, 0) + 1

    cards = []
    for user in available_users:
        ensure_profile(user)
        work_info = ensure_work_info(user)
        cards.append({
            'username': user.username,
            'display_name': get_user_display_name(user),
            'department': get_department_label(user),
            'position': work_info.position or 'Chưa cập nhật chức danh',
            'review_count': review_count_map.get(user.username, 0),
            'select_query': build_evaluation_page_query(params, user.username),
        })
    return cards


def get_selected_employee_user(filtered_users, selected_employee_username):
    """Lấy nhân viên đang được chọn."""
    if not selected_employee_username:
        return None
    for user in filtered_users:
        if user.username == selected_employee_username:
            return user
    return None


def build_evaluation_form_state(current_user, selected_employee_user, post_data=None, uploaded_file=None):
    """Form đánh giá UI — validate và lưu vào database thật."""
    form_state = {
        'can_submit': can_submit_evaluation_demo(current_user),
        'form_data': {'evaluation_content': '', 'evaluation_date': '', 'category': '', 'score': ''},
        'errors': {},
        'preview': None,
        'success_message': '',
        'selected_file_name': '',
        'selected_employee_username': selected_employee_user.username if selected_employee_user else '',
        'selected_employee_name': get_user_display_name(selected_employee_user) if selected_employee_user else '',
        'categories': EvaluationCategory.objects.all(),
    }

    if not selected_employee_user:
        if post_data:
            form_state['errors']['employee_username'] = 'Vui lòng chọn nhân viên trước.'
        return form_state

    if not form_state['can_submit']:
        return form_state

    if post_data is None:
        form_state['form_data']['evaluation_date'] = timezone.localdate().isoformat()
        return form_state

    form_state['form_data'] = {
        'evaluation_content': post_data.get('evaluation_content', '').strip(),
        'evaluation_date': post_data.get('evaluation_date', '').strip(),
        'category': post_data.get('category', '').strip(),
        'score': post_data.get('score', '').strip(),
    }
    if uploaded_file:
        form_state['selected_file_name'] = uploaded_file.name

    content = form_state['form_data']['evaluation_content']
    date_raw = form_state['form_data']['evaluation_date']
    eval_date = parse_date_input(date_raw)
    posted_username = post_data.get('employee_username', '').strip()
    category_id = form_state['form_data']['category']
    score = form_state['form_data']['score']

    if posted_username != selected_employee_user.username:
        form_state['errors']['employee_username'] = 'Nhân viên không khớp.'
    if not content:
        form_state['errors']['evaluation_content'] = 'Nội dung không được để trống.'
    if not eval_date:
        form_state['errors']['evaluation_date'] = 'Ngày đánh giá không hợp lệ.'
    if not category_id:
        form_state['errors']['category'] = 'Vui lòng chọn loại đánh giá.'
    if not score:
        form_state['errors']['score'] = 'Vui lòng nhập điểm đánh giá.'
    else:
        try:
            score_int = int(score)
            if not (0 <= score_int <= 100):
                form_state['errors']['score'] = 'Điểm phải từ 0 đến 100.'
        except ValueError:
            form_state['errors']['score'] = 'Điểm phải là số.'

    if form_state['errors']:
        return form_state

    # Lưu DB thật
    eval_obj = create_evaluation(current_user, selected_employee_user, form_state['form_data'], uploaded_file)

    form_state['preview'] = {
        'employee_name': get_user_display_name(selected_employee_user),
        'reviewer_name': get_user_display_name(current_user),
        'reviewer_role': get_user_role_name(current_user).title(),
        'evaluation_date_display': eval_date.strftime('%d/%m/%Y'),
        'evaluation_content': content,
        'evidence_reference': form_state['selected_file_name'],
        'category_name': eval_obj.category.name if eval_obj.category else '',
        'rating_display': eval_obj.get_rating_display(),
    }
    form_state['success_message'] = f'Đã lưu đánh giá cho {get_user_display_name(selected_employee_user)} thành công và gửi lên HR.'
    return form_state


def build_evaluations_page_context(user, params, post_data=None, uploaded_file=None):
    """Hàm trung tâm cho trang đánh giá nhân viên."""
    scope = get_evaluation_scope(user)
    if scope['error_message']:
        return _build_empty_evaluation_context(user, scope, params, post_data, uploaded_file)

    scope_employees = get_scope_employees_for_evaluations(user, scope)
    filters = build_evaluation_filters(scope_employees, scope, params)
    date_range = get_evaluation_date_range(params)
    selected_employee = get_selected_employee_user(
        filters['filtered_users'], filters['selected_employee'],
    )
    records = build_reviewer_evaluation_records(filters['filtered_users'], user)
    filtered_records = filter_evaluation_records(records, filters, date_range)
    sections = build_evaluation_sections(
        filters['filtered_users'], filtered_records, filters, scope, date_range,
    )
    form_state = build_evaluation_form_state(user, selected_employee, post_data, uploaded_file)
    employee_cards = build_evaluation_employee_cards(
        filters['filtered_users'], records, params,
    )

    error_msg = ''
    empty_msg = ''
    if not scope_employees:
        error_msg = 'Chưa có nhân viên nào thuộc phạm vi quản lý để đánh giá.'
    elif not filters['filtered_users']:
        error_msg = 'Không tìm thấy nhân viên phù hợp với bộ lọc.'
    elif filters['selected_employee'] and not selected_employee:
        error_msg = 'Nhân viên đang chọn không còn nằm trong phạm vi hiện tại.'
    elif selected_employee and not filtered_records:
        empty_msg = 'Nhân viên này chưa có đánh giá nào.'
    elif not selected_employee:
        empty_msg = 'Hãy chọn một nhân viên để bắt đầu đánh giá.'

    return {
        'scope': scope,
        'filters': filters,
        'evaluation_date_range': date_range,
        'evaluation_sections': sections,
        'employee_cards': employee_cards,
        'selected_employee_user': selected_employee,
        'show_employee_selection': not bool(selected_employee),
        'back_to_employee_list_query': build_evaluation_page_query(params),
        'evaluation_error_message': error_msg,
        'evaluation_warning_message': date_range['error_message'],
        'evaluation_empty_message': empty_msg,
        'form_state': form_state,
        'evaluation_statistics_query': build_evaluation_statistics_query(params),
    }


def _build_empty_evaluation_context(user, scope, params, post_data, uploaded_file):
    """Context rỗng khi không có quyền hoặc chưa đủ dữ liệu."""
    return {
        'scope': scope,
        'filters': {
            'department_options': [], 'manager_options': [],
            'leader_options': [], 'employee_options': [],
            'selected_department': '', 'selected_manager': '',
            'selected_leader': scope['locked_leader'],
            'selected_employee': '',
            'selected_manager_label': '', 'selected_leader_label': '',
            'selected_employee_label': '',
            'filtered_users': [],
            'department_locked': bool(scope['locked_department']),
            'leader_locked': bool(scope['locked_leader']),
        },
        'evaluation_date_range': {
            'from_date': params.get('from_date', ''),
            'to_date': params.get('to_date', ''),
            'from_date_value': None, 'to_date_value': None,
            'date_range_text': 'Tất cả thời gian', 'error_message': '',
        },
        'evaluation_sections': {
            'summary_cards': [], 'filter_summary': [], 'records': [],
        },
        'employee_cards': [],
        'selected_employee_user': None,
        'show_employee_selection': True,
        'back_to_employee_list_query': build_evaluation_page_query(params),
        'evaluation_error_message': scope['error_message'],
        'evaluation_warning_message': '',
        'evaluation_empty_message': '',
        'form_state': build_evaluation_form_state(user, None, post_data, uploaded_file),
        'evaluation_statistics_query': build_evaluation_statistics_query(params),
    }

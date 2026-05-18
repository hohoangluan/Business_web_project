"""
Dịch vụ truy vấn dữ liệu đánh giá từ Database thật.
Giúp tương thích hoàn hảo với module stats_reports mà không cần sửa code bên đó.
"""

from performance.models import Evaluation
from accounts.services import get_user_display_name, get_user_role_name

def get_demo_display_name(user):
    """Mô phỏng tên hiển thị để tương thích với các module khác."""
    if not user:
        return ""
    profile = getattr(user, 'profile', None)
    if profile and profile.full_name:
        return profile.full_name
    return user.username


def build_evaluation_records(users):
    """
    Lấy danh sách đánh giá từ database thật cho các nhân viên được truyền vào.
    Chỉ hiển thị các đánh giá đã được HR xác nhận (status='acknowledged').
    """
    usernames = [u.username for u in users]
    evals = Evaluation.objects.filter(
        employee__username__in=usernames, 
        status='acknowledged'
    ).select_related('employee', 'reviewer', 'category')
    
    records = []
    for ev in evals:
        records.append({
            'employee_username': ev.employee.username,
            'employee_name': get_user_display_name(ev.employee),
            'reviewer_username': ev.reviewer.username,
            'reviewer_name': get_user_display_name(ev.reviewer),
            'reviewer_role': get_user_role_name(ev.reviewer).title(),
            'evaluation_date': ev.evaluation_date,
            'evaluation_content': ev.content,
            'evidence_reference': ev.evidence_reference,
            'status': ev.status,
            'rating': ev.rating,
            'category_name': ev.category.name if ev.category else 'Chưa phân loại',
        })
    return records


def build_reviewer_evaluation_records(users, reviewer):
    """
    Lấy đánh giá do reviewer (Manager/Leader) tạo trong DB.
    """
    usernames = [u.username for u in users]
    evals = Evaluation.objects.filter(
        employee__username__in=usernames, 
        reviewer=reviewer
    ).select_related('employee', 'reviewer', 'category')
    
    records = []
    for ev in evals:
        records.append({
            'id': ev.id,
            'employee_username': ev.employee.username,
            'employee_name': get_user_display_name(ev.employee),
            'reviewer_username': ev.reviewer.username,
            'reviewer_name': get_user_display_name(ev.reviewer),
            'reviewer_role': get_user_role_name(ev.reviewer).title(),
            'evaluation_date': ev.evaluation_date,
            'evaluation_content': ev.content,
            'evidence_reference': ev.evidence_reference,
            'status': ev.status,
            'status_display': ev.get_status_display(),
            'rating': ev.rating,
            'rating_display': ev.get_rating_display() if ev.rating else 'Chưa xếp loại',
            'category_name': ev.category.name if ev.category else 'Chưa phân loại',
            'hr_note': ev.hr_note,
        })
    return records

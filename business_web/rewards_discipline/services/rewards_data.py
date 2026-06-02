"""
Dịch vụ truy xuất dữ liệu khen thưởng/xử phạt từ Database thật.
Giúp tương thích hoàn hảo với module stats_reports.
"""

from rewards_discipline.models import RewardPenalty
from accounts.services import get_user_display_name, ensure_work_info, get_user_role_name

def build_rewards_penalties_records(users):
    """
    Tạo danh sách phiếu thưởng/phạt từ database thật theo nhân viên trong phạm vi xem.
    """
    user_ids = [u.id for u in users]
    
    # Lấy toàn bộ bản ghi của những nhân viên này
    db_records = RewardPenalty.objects.filter(
        employee_id__in=user_ids
    ).select_related('employee', 'proposer')
    
    STATUS_MAP = {
        'pending': 'Chờ duyệt cấp 1',
        'leader_approved': 'Chờ HR duyệt',
        'approved': 'Đã duyệt',
        'rejected': 'Từ chối',
    }
    
    records = []
    for r in db_records:
        work_info = ensure_work_info(r.employee)
        
        proposer_name = get_user_display_name(r.proposer) if r.proposer else 'Hệ thống'
        proposer_role = get_user_role_name(r.proposer).title() if r.proposer else 'N/A'
        
        records.append({
            'employee_username': r.employee.username,
            'employee_name': get_user_display_name(r.employee),
            'department': work_info.department or 'Chưa phân phòng ban',
            'proposer_name': proposer_name,
            'proposer_role': proposer_role,
            'record_type': r.record_type,
            'type_label': r.get_record_type_display(),
            'amount': r.amount,
            'status': STATUS_MAP.get(r.status, r.status),
            'application_date': r.application_date,
            'reason_title': r.reason_title,
            'reason_detail': r.reason_detail,
        })

    # Sắp xếp theo ngày mới nhất
    records.sort(key=lambda item: item['application_date'], reverse=True)
    return records

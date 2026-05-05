"""
Mock data cho phần khen thưởng và xử phạt.

File này chỉ phục vụ giao diện và statistics mock.
Chưa có model thật nên toàn bộ dữ liệu được tạo ổn định từ danh sách nhân viên.
"""

from datetime import timedelta

from django.utils import timezone

from .evaluation_data import get_demo_display_name


REWARD_TEMPLATES = [
    {
        'title': 'Thưởng KPI quý',
        'detail': 'Đạt vượt mục tiêu công việc trong kỳ đánh giá.',
        'amount': 3000000,
        'status': 'Đã duyệt',
    },
    {
        'title': 'Thưởng sáng kiến',
        'detail': 'Đề xuất cải tiến quy trình mang lại hiệu quả rõ rệt.',
        'amount': 1500000,
        'status': 'Chờ duyệt',
    },
    {
        'title': 'Thưởng nhân viên tiêu biểu',
        'detail': 'Giữ chất lượng công việc ổn định và hỗ trợ đồng đội tốt.',
        'amount': 2000000,
        'status': 'Đã duyệt',
    },
]

PENALTY_TEMPLATES = [
    {
        'title': 'Đi trễ nhiều lần',
        'detail': 'Đi làm muộn vượt ngưỡng theo dõi trong kỳ.',
        'amount': 200000,
        'status': 'Đã duyệt',
    },
    {
        'title': 'Vi phạm quy trình nội bộ',
        'detail': 'Chưa tuân thủ đầy đủ checklist công việc đã ban hành.',
        'amount': 300000,
        'status': 'Chờ duyệt',
    },
    {
        'title': 'Thiếu cập nhật tiến độ',
        'detail': 'Không cập nhật trạng thái công việc đúng nhịp báo cáo.',
        'amount': 150000,
        'status': 'Đã duyệt',
    },
]


def build_rewards_penalties_records(users):
    """
    Tạo danh sách phiếu thưởng/phạt mock theo nhân viên trong phạm vi xem.
    """
    today = timezone.localdate()
    records = []

    for index, user in enumerate(users):
        profile = getattr(user, 'profile', None)
        if not profile:
            continue

        proposer = profile.leader_user or profile.manager_user
        proposer_name = get_demo_display_name(proposer) if proposer else 'HR'
        proposer_role = 'Leader' if profile.leader_user else 'Manager' if profile.manager_user else 'HR'

        reward_template = REWARD_TEMPLATES[index % len(REWARD_TEMPLATES)]
        records.append({
            'employee_username': user.username,
            'employee_name': get_demo_display_name(user),
            'department': profile.department or 'Chưa phân phòng ban',
            'proposer_name': proposer_name,
            'proposer_role': proposer_role,
            'record_type': 'reward',
            'type_label': 'Khen thưởng',
            'amount': reward_template['amount'],
            'status': reward_template['status'],
            'application_date': today - timedelta(days=2 + index),
            'reason_title': reward_template['title'],
            'reason_detail': reward_template['detail'],
        })

        penalty_template = PENALTY_TEMPLATES[index % len(PENALTY_TEMPLATES)]
        records.append({
            'employee_username': user.username,
            'employee_name': get_demo_display_name(user),
            'department': profile.department or 'Chưa phân phòng ban',
            'proposer_name': proposer_name,
            'proposer_role': proposer_role,
            'record_type': 'penalty',
            'type_label': 'Xử phạt',
            'amount': penalty_template['amount'],
            'status': penalty_template['status'],
            'application_date': today - timedelta(days=4 + (index * 2)),
            'reason_title': penalty_template['title'],
            'reason_detail': penalty_template['detail'],
        })

    records.sort(key=lambda item: item['application_date'], reverse=True)
    return records

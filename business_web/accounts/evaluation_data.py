"""
Mock data cho chức năng đánh giá nhân viên.

Mục tiêu của file này:
- Giữ toàn bộ dữ liệu demo ở một chỗ duy nhất.
- Dễ sửa cho người mới: mỗi record chỉ là một dict đơn giản.
- Không random để giao diện và test luôn ổn định.
"""

from datetime import timedelta

from django.utils import timezone


LEADER_EVALUATION_TEMPLATES = [
    {
        'content': 'Hoàn thành công việc đúng hạn và phối hợp nhóm ổn định.',
        'evidence': 'Biên bản họp nhóm tuần',
    },
    {
        'content': 'Chủ động hỗ trợ đồng đội và phản hồi công việc nhanh.',
        'evidence': '',
    },
    {
        'content': 'Cần cải thiện thêm phần cập nhật tiến độ hằng ngày.',
        'evidence': 'Link bảng theo dõi task nội bộ',
    },
]

MANAGER_EVALUATION_TEMPLATES = [
    {
        'content': 'Đảm bảo chất lượng đầu ra tốt và giữ nhịp công việc ổn định.',
        'evidence': 'Báo cáo kết quả công việc tháng',
    },
    {
        'content': 'Có tinh thần trách nhiệm tốt, phù hợp để giao thêm đầu việc.',
        'evidence': '',
    },
    {
        'content': 'Cần theo dõi sát hơn về tính chủ động trong giai đoạn cao điểm.',
        'evidence': 'Ghi chú buổi review 1-1',
    },
]


def get_demo_display_name(user):
    """Ưu tiên full name để giao diện nhìn tự nhiên hơn."""
    profile = getattr(user, 'profile', None)
    if profile and profile.full_name:
        return profile.full_name
    return user.username


def build_evaluation_records(users):
    """
    Tạo danh sách đánh giá demo dựa trên nhân viên đang có trong phạm vi xem.

    Mỗi nhân viên có thể có:
    - 1 đánh giá từ leader nếu đã được gán leader
    - 1 đánh giá từ manager nếu đã được gán manager
    """
    today = timezone.localdate()
    records = []

    for index, user in enumerate(users):
        profile = getattr(user, 'profile', None)
        if not profile:
            continue

        if profile.leader_user:
            leader_template = LEADER_EVALUATION_TEMPLATES[index % len(LEADER_EVALUATION_TEMPLATES)]
            records.append({
                'employee_username': user.username,
                'employee_name': get_demo_display_name(user),
                'reviewer_username': profile.leader_user.username,
                'reviewer_name': get_demo_display_name(profile.leader_user),
                'reviewer_role': 'Leader',
                'evaluation_date': today - timedelta(days=1 + index),
                'evaluation_content': leader_template['content'],
                'evidence_reference': leader_template['evidence'],
            })

        if profile.manager_user:
            manager_template = MANAGER_EVALUATION_TEMPLATES[index % len(MANAGER_EVALUATION_TEMPLATES)]
            records.append({
                'employee_username': user.username,
                'employee_name': get_demo_display_name(user),
                'reviewer_username': profile.manager_user.username,
                'reviewer_name': get_demo_display_name(profile.manager_user),
                'reviewer_role': 'Manager',
                'evaluation_date': today - timedelta(days=3 + (index * 2)),
                'evaluation_content': manager_template['content'],
                'evidence_reference': manager_template['evidence'],
            })

    records.sort(key=lambda item: item['evaluation_date'], reverse=True)
    return records


def build_reviewer_evaluation_records(users, reviewer):
    """
    Trang đánh giá của manager/leader chỉ nên thấy các đánh giá do chính họ tạo.
    """
    return [
        record for record in build_evaluation_records(users)
        if record['reviewer_username'] == reviewer.username
    ]

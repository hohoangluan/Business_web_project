"""Service duyệt 2 cấp cho khen thưởng / xử phạt (QĐ §5.9).

Luồng:
  - Leader lập phiếu  → PENDING (chờ Manager duyệt L1) → LEADER_APPROVED
                        → HR duyệt L2 → APPROVED.
  - Manager/HR/Admin lập → LEADER_APPROVED ngay (bỏ L1) → HR duyệt L2 → APPROVED.
  - Từ chối ở bất kỳ cấp → REJECTED.
"""
from django.utils import timezone

from accounts.models import Role
from accounts.services import (
    create_notification,
    is_admin_user,
    is_hr_user,
    user_has_role,
)
from rewards_discipline.models import RewardPenalty


def _record_label(obj):
    return 'Khen thưởng' if obj.record_type == RewardPenalty.REWARD else 'Xử phạt'


def initial_status_for(proposer):
    """Trạng thái khởi tạo theo vai trò người lập phiếu."""
    if user_has_role(proposer, Role.LEADER):
        return RewardPenalty.PENDING          # cần Manager duyệt L1
    return RewardPenalty.LEADER_APPROVED      # Manager/HR/Admin lập → thẳng L2


def _is_l1_approver(user):
    return user_has_role(user, Role.MANAGER) or is_admin_user(user)


def _is_l2_approver(user):
    return is_hr_user(user) or is_admin_user(user)


def approve_reward_penalty(approver, record_id):
    """Duyệt 1 phiếu theo cấp hiện tại. Trả (success, message)."""
    try:
        obj = RewardPenalty.objects.get(id=record_id)
    except RewardPenalty.DoesNotExist:
        return False, 'Không tìm thấy phiếu.'

    if obj.proposer_id == approver.id:
        return False, 'Không thể tự duyệt phiếu của chính mình.'

    if obj.status == RewardPenalty.PENDING:
        if not _is_l1_approver(approver):
            return False, 'Chỉ Manager mới được duyệt cấp 1.'
        obj.status = RewardPenalty.LEADER_APPROVED
        obj.leader_approved_by = approver
        obj.leader_approved_at = timezone.now()
        obj.save(update_fields=['status', 'leader_approved_by', 'leader_approved_at'])
        return True, 'Đã duyệt cấp 1 (Manager). Chuyển HR duyệt cuối.'

    if obj.status == RewardPenalty.LEADER_APPROVED:
        if not _is_l2_approver(approver):
            return False, 'Chỉ HR mới được duyệt cấp cuối.'
        obj.status = RewardPenalty.APPROVED
        obj.approved_by = approver
        obj.save(update_fields=['status', 'approved_by'])
        create_notification(
            obj.employee,
            f'{_record_label(obj)} đã được duyệt',
            f'Phiếu "{obj.reason_title}" đã được phê duyệt.',
        )
        return True, 'Đã phê duyệt cuối cùng (HR).'

    return False, 'Phiếu đã được xử lý.'


def reject_reward_penalty(approver, record_id):
    """Từ chối phiếu (ở cấp đang chờ). Trả (success, message)."""
    try:
        obj = RewardPenalty.objects.get(id=record_id)
    except RewardPenalty.DoesNotExist:
        return False, 'Không tìm thấy phiếu.'

    if obj.status == RewardPenalty.PENDING and not _is_l1_approver(approver):
        return False, 'Không có quyền từ chối phiếu này.'
    if obj.status == RewardPenalty.LEADER_APPROVED and not _is_l2_approver(approver):
        return False, 'Không có quyền từ chối phiếu này.'
    if obj.status not in (RewardPenalty.PENDING, RewardPenalty.LEADER_APPROVED):
        return False, 'Phiếu đã được xử lý.'

    obj.status = RewardPenalty.REJECTED
    obj.save(update_fields=['status'])
    create_notification(
        obj.employee,
        f'{_record_label(obj)} bị từ chối',
        f'Phiếu "{obj.reason_title}" đã bị từ chối.',
    )
    return True, 'Đã từ chối phiếu.'


def get_pending_for_approver(user):
    """Hàng đợi duyệt theo vai trò: Manager→L1 (pending); HR/Admin→L2 (leader_approved)."""
    qs = RewardPenalty.objects.select_related('employee', 'proposer')
    if _is_l2_approver(user):
        return qs.filter(status=RewardPenalty.LEADER_APPROVED).order_by('-created_at')
    if _is_l1_approver(user):
        return qs.filter(status=RewardPenalty.PENDING).order_by('-created_at')
    return qs.none()

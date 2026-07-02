"""Service duyệt khen thưởng / xử phạt: Leader/Manager đề xuất, HR duyệt hoặc từ chối."""

from accounts.models import Role
from accounts.services import create_notification, is_hr_user, user_has_role
from rewards_discipline.models import RewardPenalty


def _record_label(obj):
    return 'Khen thưởng' if obj.record_type == RewardPenalty.REWARD else 'Xử phạt'



def _is_l1_approver(user, obj=None):
    """Legacy shim: L1 approval was removed; no user is an L1 approver now."""
    return False


def _is_l2_approver(user, obj=None):
    """Legacy shim: HR is the only final approver in the simplified flow."""
    return is_hr_user(user)

def initial_status_for(proposer):
    """Mọi đề xuất hợp lệ đi thẳng vào hàng chờ HR."""
    return RewardPenalty.PENDING


def can_propose_reward_penalty(user):
    return is_hr_user(user) or user_has_role(user, Role.MANAGER) or user_has_role(user, Role.LEADER)


def approve_reward_penalty(approver, record_id):
    """HR duyệt 1 phiếu. Trả (success, message)."""
    try:
        obj = RewardPenalty.objects.get(id=record_id)
    except RewardPenalty.DoesNotExist:
        return False, 'Không tìm thấy phiếu.'

    if not is_hr_user(approver):
        return False, 'Chỉ HR mới được duyệt phiếu.'
    if obj.proposer_id == approver.id:
        return False, 'Không thể tự duyệt phiếu của chính mình.'
    if obj.status != RewardPenalty.PENDING:
        return False, 'Phiếu đã được xử lý.'

    obj.status = RewardPenalty.APPROVED
    obj.approved_by = approver
    obj.save(update_fields=['status', 'approved_by'])
    create_notification(
        obj.employee,
        f'{_record_label(obj)} đã được duyệt',
        f'Phiếu "{obj.reason_title}" đã được HR phê duyệt.',
    )
    return True, 'HR đã phê duyệt phiếu.'


def reject_reward_penalty(approver, record_id):
    """HR từ chối 1 phiếu. Trả (success, message)."""
    try:
        obj = RewardPenalty.objects.get(id=record_id)
    except RewardPenalty.DoesNotExist:
        return False, 'Không tìm thấy phiếu.'

    if not is_hr_user(approver):
        return False, 'Chỉ HR mới được từ chối phiếu.'
    if obj.proposer_id == approver.id:
        return False, 'Không thể tự xử lý phiếu của chính mình.'
    if obj.status != RewardPenalty.PENDING:
        return False, 'Phiếu đã được xử lý.'

    obj.status = RewardPenalty.REJECTED
    obj.approved_by = approver
    obj.save(update_fields=['status', 'approved_by'])
    create_notification(
        obj.employee,
        f'{_record_label(obj)} bị từ chối',
        f'Phiếu "{obj.reason_title}" đã bị HR từ chối.',
    )
    return True, 'HR đã từ chối phiếu.'


def get_pending_for_approver(user):
    """Chỉ HR có hàng đợi duyệt."""
    qs = RewardPenalty.objects.select_related('employee', 'proposer')
    if is_hr_user(user):
        return qs.filter(status=RewardPenalty.PENDING).order_by('-created_at')
    return qs.none()
"""Business logic cho nghỉ phép — tạo, hủy, phê duyệt 2 bước, thống kê."""

from decimal import Decimal

from django.db.models import Sum, Q
from django.utils import timezone

from accounts.models import Role
from leaves.models import LeaveRequest


# ===========================================================================
#  HELPER: Kiểm tra vai trò & quan hệ quản lý
#  (Tái sử dụng logic từ overtime — nhưng giữ tách biệt để tránh coupling)
# ===========================================================================

def _is_hr_role(user):
    """Kiểm tra user có role HR không."""
    try:
        return user.profile.role and user.profile.role.name == Role.HR
    except Exception:
        return False


def _is_direct_supervisor(approver, employee):
    """Kiểm tra approver có phải quản lý trực tiếp không."""
    try:
        wi = employee.work_info
    except Exception:
        return False
    return approver in (wi.leader_user, wi.manager_user)


def _get_direct_report_user_ids(supervisor):
    """Trả về danh sách user ID mà supervisor quản lý trực tiếp."""
    from employee_profiles.models import EmployeeWorkInfo
    return list(
        EmployeeWorkInfo.objects.filter(
            Q(leader_user=supervisor) | Q(manager_user=supervisor)
        ).values_list('user_id', flat=True)
    )


# ===========================================================================
#  EMPLOYEE: tạo / hủy / xem đơn
# ===========================================================================

def create_leave_request(user, form):
    """Tạo đơn nghỉ phép mới. Tự tính số ngày từ start_date/end_date."""
    obj = form.save(commit=False)
    obj.user = user
    obj.status = LeaveRequest.PENDING
    # Tính số ngày (bao gồm cả ngày đầu và ngày cuối)
    obj.days = Decimal(str((obj.end_date - obj.start_date).days + 1))
    obj.save()
    return obj


def cancel_leave_request(user, request_id):
    """Hủy đơn nghỉ phép (chỉ đơn pending chưa ai duyệt)."""
    try:
        obj = LeaveRequest.objects.get(pk=request_id, user=user)
    except LeaveRequest.DoesNotExist:
        return False, 'Không tìm thấy đơn nghỉ phép.'

    if obj.status != LeaveRequest.PENDING:
        return False, 'Chỉ có thể hủy đơn đang chờ duyệt (chưa được quản lý duyệt).'

    obj.delete()
    return True, 'Đã hủy đơn nghỉ phép thành công.'


def get_user_leave_requests(user):
    """Trả về toàn bộ đơn nghỉ phép của user, mới nhất lên đầu."""
    return LeaveRequest.objects.filter(user=user).select_related(
        'approved_by', 'leader_approved_by',
    )


def get_user_leave_stats(user):
    """
    Thống kê nghỉ phép của user trong năm hiện tại.

    Returns dict:
        total_allowed  – tổng ngày phép năm (mặc định 12)
        used_days      – số ngày đã nghỉ (đơn approved)
        remaining_days – số ngày còn lại
        pending_count  – số đơn đang chờ (pending + leader_approved)
    """
    today = timezone.localdate()
    year_qs = LeaveRequest.objects.filter(
        user=user,
        start_date__year=today.year,
    )

    approved_qs = year_qs.filter(status=LeaveRequest.APPROVED)
    agg = approved_qs.aggregate(total=Sum('days'))
    used_days = agg['total'] or Decimal('0')

    total_allowed = None
    try:
        from contracts.services import get_active_contract
        active_contract = get_active_contract(user)
        if active_contract and active_contract.contract_annual_leave_days is not None:
            total_allowed = Decimal(str(active_contract.contract_annual_leave_days))
    except Exception:
        pass

    waiting_count = year_qs.filter(
        status__in=[LeaveRequest.PENDING, LeaveRequest.LEADER_APPROVED],
    ).count()

    remaining_days = None
    if total_allowed is not None:
        remaining_days = max(total_allowed - used_days, Decimal('0'))

    return {
        'total_allowed': total_allowed,
        'used_days': used_days,
        'remaining_days': remaining_days,
        'pending_count': waiting_count,
    }


# ===========================================================================
#  MANAGER / HR: lấy danh sách đơn cần duyệt
# ===========================================================================

def get_pending_requests_for_approver(approver):
    """
    Lấy danh sách đơn nghỉ phép mà approver có quyền duyệt.

    - Leader/Manager: đơn pending từ nhân viên trực tiếp
    - HR: đơn leader_approved chờ duyệt cuối
    """
    step1 = LeaveRequest.objects.none()
    step2 = LeaveRequest.objects.none()

    # Bước 1: Leader/Manager duyệt nhân viên trực tiếp
    report_ids = _get_direct_report_user_ids(approver)
    if report_ids:
        step1 = (
            LeaveRequest.objects
            .filter(status=LeaveRequest.PENDING, user_id__in=report_ids)
            .exclude(user=approver)
            .select_related('user', 'user__profile')
            .order_by('-created_at')
        )

    # Bước 2: HR duyệt cuối
    if _is_hr_role(approver):
        step2 = (
            LeaveRequest.objects
            .filter(status=LeaveRequest.LEADER_APPROVED)
            .exclude(user=approver)
            .select_related('user', 'user__profile', 'leader_approved_by')
            .order_by('-created_at')
        )

    return {
        'step1_requests': step1,
        'step2_requests': step2,
    }


# ===========================================================================
#  PHÊ DUYỆT 2 BƯỚC
# ===========================================================================

def approve_leave_request(approver, request_id):
    """
    Duyệt đơn nghỉ phép — logic 2 bước giống overtime.
    """
    try:
        obj = LeaveRequest.objects.select_related(
            'user', 'user__profile', 'user__profile__role',
        ).get(pk=request_id)
    except LeaveRequest.DoesNotExist:
        return False, 'Không tìm thấy đơn nghỉ phép.'

    if obj.user == approver:
        return False, 'Không thể tự duyệt đơn của chính mình.'

    now = timezone.now()

    # Bước 1: pending → leader_approved / approved
    if obj.status == LeaveRequest.PENDING:
        if not _is_direct_supervisor(approver, obj.user):
            return False, 'Bạn không phải quản lý trực tiếp của nhân viên này.'

        obj.leader_approved_by = approver
        obj.leader_approved_at = now

        if _is_hr_role(obj.user):
            obj.status = LeaveRequest.APPROVED
            obj.approved_by = approver
            obj.save(update_fields=[
                'status', 'leader_approved_by', 'leader_approved_at', 'approved_by',
            ])
            return True, 'Đã duyệt đơn nghỉ phép thành công (nhân viên HR — hoàn tất).'

        obj.status = LeaveRequest.LEADER_APPROVED
        obj.save(update_fields=[
            'status', 'leader_approved_by', 'leader_approved_at',
        ])
        return True, 'Đã duyệt bước 1. Đơn chuyển sang chờ HR phê duyệt cuối.'

    # Bước 2: leader_approved → approved
    if obj.status == LeaveRequest.LEADER_APPROVED:
        if not _is_hr_role(approver):
            return False, 'Chỉ HR mới được duyệt bước cuối.'

        obj.status = LeaveRequest.APPROVED
        obj.approved_by = approver
        obj.save(update_fields=['status', 'approved_by'])
        return True, 'Đã phê duyệt cuối cùng. Đơn nghỉ phép đã được duyệt hoàn tất!'

    return False, 'Đơn đã được xử lý hoặc không ở trạng thái chờ duyệt.'


def reject_leave_request(approver, request_id, reason=''):
    """Từ chối đơn nghỉ phép — ở cả bước 1 lẫn bước 2."""
    try:
        obj = LeaveRequest.objects.select_related('user').get(pk=request_id)
    except LeaveRequest.DoesNotExist:
        return False, 'Không tìm thấy đơn nghỉ phép.'

    if obj.user == approver:
        return False, 'Không thể tự xử lý đơn của chính mình.'

    if obj.status == LeaveRequest.PENDING:
        if not _is_direct_supervisor(approver, obj.user):
            return False, 'Bạn không phải quản lý trực tiếp của nhân viên này.'
    elif obj.status == LeaveRequest.LEADER_APPROVED:
        if not _is_hr_role(approver):
            return False, 'Chỉ HR mới được từ chối ở bước cuối.'
    else:
        return False, 'Đơn đã được xử lý hoặc không ở trạng thái chờ duyệt.'

    obj.status = LeaveRequest.REJECTED
    obj.approved_by = approver
    obj.rejected_reason = reason
    obj.save(update_fields=['status', 'approved_by', 'rejected_reason'])
    return True, 'Đã từ chối đơn nghỉ phép.'


def bulk_approve_requests(approver):
    """Duyệt hàng loạt đơn nghỉ phép mà approver có quyền."""
    count = 0
    now = timezone.now()

    report_ids = _get_direct_report_user_ids(approver)
    if report_ids:
        step1_qs = LeaveRequest.objects.filter(
            status=LeaveRequest.PENDING, user_id__in=report_ids,
        ).exclude(user=approver).select_related(
            'user', 'user__profile', 'user__profile__role',
        )

        for obj in step1_qs:
            obj.leader_approved_by = approver
            obj.leader_approved_at = now
            if _is_hr_role(obj.user):
                obj.status = LeaveRequest.APPROVED
                obj.approved_by = approver
            else:
                obj.status = LeaveRequest.LEADER_APPROVED
            obj.save(update_fields=[
                'status', 'leader_approved_by', 'leader_approved_at', 'approved_by',
            ])
            count += 1

    if _is_hr_role(approver):
        step2_count = LeaveRequest.objects.filter(
            status=LeaveRequest.LEADER_APPROVED,
        ).exclude(user=approver).update(
            status=LeaveRequest.APPROVED,
            approved_by=approver,
        )
        count += step2_count

    return count

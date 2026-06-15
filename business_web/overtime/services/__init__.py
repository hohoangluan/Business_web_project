"""Business logic cho tăng ca — tạo, hủy, phê duyệt 2 bước, thống kê."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Q
from django.utils import timezone

from accounts.models import Role
from accounts.services import create_notification
from overtime.models import OvertimeRequest


# ===========================================================================
#  HELPER: Kiểm tra vai trò & quan hệ quản lý
# ===========================================================================

def _is_hr_role(user):
    """Kiểm tra user có role HR không."""
    try:
        return user.profile.role and user.profile.role.name == Role.HR
    except Exception:
        return False


def _get_direct_supervisor(user):
    """
    Trả về leader_user hoặc manager_user của nhân viên.
    Ưu tiên leader_user trước, fallback sang manager_user.
    """
    try:
        wi = user.work_info
    except Exception:
        return None
    return wi.leader_user or wi.manager_user


def _is_direct_supervisor(approver, employee):
    """
    Kiểm tra ``approver`` có phải quản lý trực tiếp (leader hoặc manager)
    của ``employee`` không.
    """
    try:
        wi = employee.work_info
    except Exception:
        return False
    return approver in (wi.leader_user, wi.manager_user)


def _get_direct_report_user_ids(supervisor):
    """
    Trả về danh sách user ID của nhân viên mà ``supervisor`` quản lý trực tiếp
    (qua leader_user hoặc manager_user trong EmployeeWorkInfo).
    """
    from employee_profiles.models import EmployeeWorkInfo
    return list(
        EmployeeWorkInfo.objects.filter(
            Q(leader_user=supervisor) | Q(manager_user=supervisor)
        ).values_list('user_id', flat=True)
    )


def _has_supervisor(user):
    """Nhân viên có ít nhất 1 leader hoặc manager phụ trách không."""
    try:
        wi = user.work_info
    except Exception:
        return False
    return bool(wi.leader_user_id or wi.manager_user_id)


def _resolve_initial_status(user):
    """Trạng thái khởi tạo đơn theo cấu hình quản lý của nhân viên.

    - Có ≥1 leader/manager        → PENDING (duyệt L1 bình thường, rồi HR L2).
    - Trống cả 2, nhân viên thường → LEADER_APPROVED (bỏ L1, chuyển thẳng HR L2).
    - Trống cả 2, nhân viên HR      → APPROVED (tự duyệt: không có L1, HR không cần L2).
    """
    if _has_supervisor(user):
        return OvertimeRequest.PENDING
    if _is_hr_role(user):
        return OvertimeRequest.APPROVED
    return OvertimeRequest.LEADER_APPROVED


# ===========================================================================
#  EMPLOYEE: tạo / hủy / xem đơn
# ===========================================================================

def create_overtime_request(user, form):
    """Tạo đơn tăng ca mới từ một form đã validated."""
    obj = form.save(commit=False)
    obj.user = user
    obj.status = _resolve_initial_status(user)
    obj.save()
    if obj.status == OvertimeRequest.APPROVED:
        # Trống cả leader/manager và bản thân là HR → không có cấp duyệt nào.
        create_notification(
            user,
            'Đơn tăng ca đã được duyệt',
            'Đơn tăng ca của bạn đã được tự động phê duyệt '
            '(không có quản lý phụ trách).',
        )
    return obj


def cancel_overtime_request(user, request_id):
    """
    Hủy đơn tăng ca.  Chỉ cho phép hủy đơn của chính mình và đang ở trạng
    thái *pending* (chưa ai duyệt).  Trả về ``(success, message)``.
    """
    try:
        obj = OvertimeRequest.objects.get(pk=request_id, user=user)
    except OvertimeRequest.DoesNotExist:
        return False, 'Không tìm thấy đơn tăng ca.'

    if obj.status != OvertimeRequest.PENDING:
        return False, 'Chỉ có thể hủy đơn đang chờ duyệt (chưa được quản lý duyệt).'

    obj.delete()
    return True, 'Đã hủy đơn tăng ca thành công.'


def get_approved_overtime_end(user, on_date):
    """Trả giờ kết thúc OT đã duyệt muộn nhất của user trong ngày, hoặc None.

    Dùng để tính giờ tan làm kỳ vọng khi nhân viên có tăng ca: nếu có OT
    approved trong ngày, giờ ra "đúng giờ" được dời tới end_time của OT.
    """
    obj = (OvertimeRequest.objects
           .filter(user=user,
                   overtime_date=on_date,
                   status=OvertimeRequest.APPROVED)
           .order_by('-end_time')
           .first())
    return obj.end_time if obj else None


def get_user_overtime_requests(user):
    """Trả về toàn bộ đơn tăng ca của user, mới nhất lên đầu."""
    return OvertimeRequest.objects.filter(user=user).select_related(
        'approved_by', 'leader_approved_by',
    )


def get_user_overtime_stats(user):
    """
    Thống kê tăng ca của user trong tháng hiện tại.
    ``pending_count`` bao gồm cả ``pending`` + ``leader_approved``.
    """
    today = timezone.localdate()
    month_qs = OvertimeRequest.objects.filter(
        user=user,
        overtime_date__year=today.year,
        overtime_date__month=today.month,
    )

    approved_qs = month_qs.filter(status=OvertimeRequest.APPROVED)
    agg = approved_qs.aggregate(total=Sum('hours'))
    total_hours = agg['total'] or Decimal('0')

    waiting_count = month_qs.filter(
        status__in=[OvertimeRequest.PENDING, OvertimeRequest.LEADER_APPROVED],
    ).count()

    return {
        'total_hours': total_hours,
        'approved_count': approved_qs.count(),
        'pending_count': waiting_count,
        'total_pay': int(total_hours * 150_000),
    }


def get_monthly_chart_data(user):
    """
    Trả về dữ liệu biểu đồ tăng ca 4 tuần gần nhất (chỉ tính đơn approved).
    """
    today = timezone.localdate()
    weeks = []
    for i in range(4, 0, -1):
        week_end = today - timedelta(weeks=i - 1)
        week_start = week_end - timedelta(days=6)
        agg = OvertimeRequest.objects.filter(
            user=user,
            status=OvertimeRequest.APPROVED,
            overtime_date__gte=week_start,
            overtime_date__lte=week_end,
        ).aggregate(total=Sum('hours'))
        weeks.append({
            'label': f'T{5 - i}',
            'hours': float(agg['total'] or 0),
        })
    return weeks


# ===========================================================================
#  MANAGER / HR: lấy danh sách đơn cần duyệt
# ===========================================================================

def get_pending_requests_for_approver(approver):
    """
    Lấy danh sách đơn tăng ca mà ``approver`` có quyền duyệt.

    - **Leader / Manager**: thấy đơn ``pending`` của nhân viên trực tiếp.
    - **HR**: thấy đơn ``leader_approved`` (đã qua bước 1, chờ HR duyệt cuối).
      Không bao gồm đơn của người tạo có role HR (vì HR chỉ cần 1 bước).

    Trả về dict với 2 key:
      - ``step1_requests``: đơn chờ duyệt bước 1 (cho leader/manager)
      - ``step2_requests``: đơn chờ HR duyệt cuối (cho HR)
    """
    step1 = OvertimeRequest.objects.none()
    step2 = OvertimeRequest.objects.none()

    # ----- Bước 1: Leader/Manager duyệt nhân viên trực tiếp -----
    report_ids = _get_direct_report_user_ids(approver)
    if report_ids:
        step1 = (
            OvertimeRequest.objects
            .filter(
                status=OvertimeRequest.PENDING,
                user_id__in=report_ids,
            )
            .exclude(user=approver)
            .select_related('user', 'user__profile')
            .order_by('-created_at')
        )

    # ----- Bước 2: HR duyệt cuối -----
    if _is_hr_role(approver):
        step2 = (
            OvertimeRequest.objects
            .filter(status=OvertimeRequest.LEADER_APPROVED)
            .exclude(user=approver)
            .select_related('user', 'user__profile', 'leader_approved_by')
            .order_by('-created_at')
        )

    return {
        'step1_requests': step1,
        'step2_requests': step2,
    }


# ===========================================================================
#  PHÊT DUYỆT: Bước 1 — Leader / Manager trực tiếp
# ===========================================================================

def approve_overtime_request(approver, request_id):
    """
    Duyệt 1 đơn tăng ca.  Logic:

    - Nếu đơn ở ``pending`` và approver là quản lý trực tiếp:
        → Nếu người tạo là HR → chuyển thẳng ``approved``
        → Nếu không → chuyển ``leader_approved`` (chờ HR)
    - Nếu đơn ở ``leader_approved`` và approver là HR:
        → Chuyển ``approved``

    Trả về ``(success, message)``.
    """
    try:
        obj = OvertimeRequest.objects.select_related(
            'user', 'user__profile', 'user__profile__role',
        ).get(pk=request_id)
    except OvertimeRequest.DoesNotExist:
        return False, 'Không tìm thấy đơn tăng ca.'

    if obj.user == approver:
        return False, 'Không thể tự duyệt đơn của chính mình.'

    now = timezone.now()

    # ----- BƯỚC 1: pending → leader_approved / approved -----
    if obj.status == OvertimeRequest.PENDING:
        if not _is_direct_supervisor(approver, obj.user):
            return False, 'Bạn không phải quản lý trực tiếp của nhân viên này.'

        obj.leader_approved_by = approver
        obj.leader_approved_at = now

        # HR staff chỉ cần 1 bước → approved luôn
        if _is_hr_role(obj.user):
            obj.status = OvertimeRequest.APPROVED
            obj.approved_by = approver
            obj.save(update_fields=[
                'status', 'leader_approved_by', 'leader_approved_at',
                'approved_by',
            ])
            create_notification(
                obj.user,
                'Đơn tăng ca đã được duyệt',
                'Đơn đăng ký tăng ca của bạn đã được phê duyệt.',
            )
            return True, 'Đã duyệt đơn tăng ca thành công (nhân viên HR — hoàn tất).'

        # Các role khác → chờ HR duyệt cuối
        obj.status = OvertimeRequest.LEADER_APPROVED
        obj.save(update_fields=[
            'status', 'leader_approved_by', 'leader_approved_at',
        ])
        return True, 'Đã duyệt bước 1. Đơn chuyển sang chờ HR phê duyệt cuối.'

    # ----- BƯỚC 2: leader_approved → approved (HR duyệt cuối) -----
    if obj.status == OvertimeRequest.LEADER_APPROVED:
        if not _is_hr_role(approver):
            return False, 'Chỉ HR mới được duyệt bước cuối.'

        obj.status = OvertimeRequest.APPROVED
        obj.approved_by = approver
        obj.save(update_fields=['status', 'approved_by'])
        create_notification(
            obj.user,
            'Đơn tăng ca đã được duyệt',
            'Đơn đăng ký tăng ca của bạn đã được phê duyệt.',
        )
        return True, 'Đã phê duyệt cuối cùng. Đơn tăng ca đã được duyệt hoàn tất!'

    return False, 'Đơn đã được xử lý hoặc không ở trạng thái chờ duyệt.'


# ===========================================================================
#  TỪ CHỐI: Có thể từ chối ở cả 2 bước
# ===========================================================================

def reject_overtime_request(approver, request_id, reason=''):
    """
    Từ chối 1 đơn tăng ca.  Cho phép reject ở cả ``pending`` (bước 1)
    lẫn ``leader_approved`` (bước 2).  Trả về ``(success, message)``.
    """
    try:
        obj = OvertimeRequest.objects.select_related(
            'user',
        ).get(pk=request_id)
    except OvertimeRequest.DoesNotExist:
        return False, 'Không tìm thấy đơn tăng ca.'

    if obj.user == approver:
        return False, 'Không thể tự xử lý đơn của chính mình.'

    # Bước 1: chỉ quản lý trực tiếp mới được từ chối
    if obj.status == OvertimeRequest.PENDING:
        if not _is_direct_supervisor(approver, obj.user):
            return False, 'Bạn không phải quản lý trực tiếp của nhân viên này.'

    # Bước 2: chỉ HR mới được từ chối
    elif obj.status == OvertimeRequest.LEADER_APPROVED:
        if not _is_hr_role(approver):
            return False, 'Chỉ HR mới được từ chối ở bước cuối.'

    else:
        return False, 'Đơn đã được xử lý hoặc không ở trạng thái chờ duyệt.'

    obj.status = OvertimeRequest.REJECTED
    obj.approved_by = approver
    obj.rejected_reason = reason
    obj.save(update_fields=['status', 'approved_by', 'rejected_reason'])
    create_notification(
        obj.user,
        'Đơn tăng ca bị từ chối',
        f'Đơn đăng ký tăng ca của bạn đã bị từ chối.{" Lý do: " + reason if reason else ""}',
    )
    return True, 'Đã từ chối đơn tăng ca.'


# ===========================================================================
#  DUYỆT HÀNG LOẠT
# ===========================================================================

def bulk_approve_requests(approver):
    """
    Duyệt hàng loạt đơn mà approver có quyền:
    - Leader/Manager: duyệt tất cả pending của nhân viên trực tiếp → leader_approved
    - HR: duyệt tất cả leader_approved → approved

    Trả về tổng số đơn đã duyệt.
    """
    count = 0
    now = timezone.now()

    # Bước 1: Leader/Manager duyệt nhân viên trực tiếp
    report_ids = _get_direct_report_user_ids(approver)
    if report_ids:
        step1_qs = OvertimeRequest.objects.filter(
            status=OvertimeRequest.PENDING,
            user_id__in=report_ids,
        ).exclude(user=approver).select_related(
            'user', 'user__profile', 'user__profile__role',
        )

        for obj in step1_qs:
            obj.leader_approved_by = approver
            obj.leader_approved_at = now
            if _is_hr_role(obj.user):
                # HR staff → approved luôn
                obj.status = OvertimeRequest.APPROVED
                obj.approved_by = approver
            else:
                obj.status = OvertimeRequest.LEADER_APPROVED
            obj.save(update_fields=[
                'status', 'leader_approved_by', 'leader_approved_at',
                'approved_by',
            ])
            count += 1

    # Bước 2: HR duyệt cuối
    if _is_hr_role(approver):
        step2_count = OvertimeRequest.objects.filter(
            status=OvertimeRequest.LEADER_APPROVED,
        ).exclude(user=approver).update(
            status=OvertimeRequest.APPROVED,
            approved_by=approver,
        )
        count += step2_count

    return count

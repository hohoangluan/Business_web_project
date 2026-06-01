"""HR-side review (approve/reject) cho yêu cầu điều chỉnh chấm công."""
from django.db import transaction
from django.utils import timezone

from attendance.models import AttendanceAdjustmentRequest
from attendance.services.record.attendance_logging_service import recompute_record_status


def get_pending_adjustments():
    """Tất cả yêu cầu đang chờ HR duyệt."""
    return (AttendanceAdjustmentRequest.objects
            .filter(status='pending')
            .select_related('record', 'submitted_by')
            .order_by('-submitted_at'))


def get_reviewed_adjustments():
    """Lịch sử đã duyệt/từ chối."""
    return (AttendanceAdjustmentRequest.objects
            .exclude(status='pending')
            .select_related('record', 'submitted_by', 'reviewed_by')
            .order_by('-reviewed_at'))


def approve_adjustment(hr_user, adj_id, hr_note=''):
    try:
        adj = AttendanceAdjustmentRequest.objects.select_related('record').get(id=adj_id)
    except AttendanceAdjustmentRequest.DoesNotExist:
        return False, 'Không tìm thấy yêu cầu.'
    if adj.status != 'pending':
        return False, 'Yêu cầu đã được xử lý.'
    with transaction.atomic():
        record = adj.record
        if adj.claimed_check_in_time:
            record.check_in_time = adj.claimed_check_in_time
        if adj.claimed_check_out_time:
            record.check_out_time = adj.claimed_check_out_time
        record.status = recompute_record_status(record)
        record.save(update_fields=['check_in_time', 'check_out_time', 'status'])
        adj.status = 'approved'
        adj.reviewed_by = hr_user
        adj.reviewed_at = timezone.now()
        adj.hr_note = (hr_note or '').strip()
        adj.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_note'])
    return True, 'Đã duyệt yêu cầu điều chỉnh.'


def reject_adjustment(hr_user, adj_id, hr_note=''):
    try:
        adj = AttendanceAdjustmentRequest.objects.select_related('record').get(id=adj_id)
    except AttendanceAdjustmentRequest.DoesNotExist:
        return False, 'Không tìm thấy yêu cầu.'
    if adj.status != 'pending':
        return False, 'Yêu cầu đã được xử lý.'
    with transaction.atomic():
        record = adj.record
        record.status = recompute_record_status(record)
        record.save(update_fields=['status'])
        adj.status = 'rejected'
        adj.reviewed_by = hr_user
        adj.reviewed_at = timezone.now()
        adj.hr_note = (hr_note or '').strip()
        adj.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_note'])
    return True, 'Đã từ chối yêu cầu điều chỉnh.'

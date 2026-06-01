"""Single-responsibility helpers for the attendance log.

Each function does one DB-shaped thing. The view orchestrates them
inside a transaction.atomic block.
"""
import logging
from datetime import date, datetime, timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from attendance.models import AttendanceRecord

logger = logging.getLogger('face.attendance')


def get_or_create_today_record(user) -> AttendanceRecord:
    rec, _ = AttendanceRecord.objects.get_or_create(
        user=user, record_date=timezone.localdate(),
    )
    return rec


def decide_next_action(record: AttendanceRecord) -> str:
    """Return one of: 'check_in', 'check_out', 'done'."""
    if record.check_in_time is None:
        return 'check_in'
    if record.check_out_time is None:
        return 'check_out'
    return 'done'


def classify_status(check_in_time, check_out_time, shift_start, shift_end):
    """Phân loại bản ghi: late nếu vào trễ, early_leave nếu ra sớm, else on_time."""
    grace = timedelta(minutes=settings.WORK_LATE_GRACE_MIN)
    today = date.today()
    in_limit = (datetime.combine(today, shift_start) + grace).time()
    status = 'late' if check_in_time and check_in_time > in_limit else 'on_time'
    if check_out_time and check_out_time < shift_end:
        status = 'early_leave'
    return status


def record_check_in(user, now=None) -> AttendanceRecord:
    from contracts.services import get_shift_times
    today = timezone.localdate()
    now_time = (now or timezone.localtime()).time()
    rec, _ = AttendanceRecord.objects.get_or_create(user=user, record_date=today)
    if rec.check_in_time is None:
        shift_start, shift_end = get_shift_times(user)
        rec.check_in_time = now_time
        rec.status = classify_status(now_time, rec.check_out_time, shift_start, shift_end)
        rec.save(update_fields=['check_in_time', 'status'])
        logger.info('check_in user=%s time=%s status=%s', user.id, now_time, rec.status)
    return rec


def record_check_out(user, now=None) -> AttendanceRecord:
    from contracts.services import get_shift_times
    today = timezone.localdate()
    now_time = (now or timezone.localtime()).time()
    rec, _ = AttendanceRecord.objects.get_or_create(user=user, record_date=today)
    if rec.check_out_time is None:
        shift_start, shift_end = get_shift_times(user)
        rec.check_out_time = now_time
        rec.status = classify_status(rec.check_in_time, now_time, shift_start, shift_end)
        rec.save(update_fields=['check_out_time', 'status'])
        logger.info('check_out user=%s time=%s status=%s', user.id, now_time, rec.status)
    return rec


def get_open_previous_record(user) -> AttendanceRecord | None:
    today = timezone.localdate()
    return (AttendanceRecord.objects
            .filter(user=user,
                    record_date__lt=today,
                    check_in_time__isnull=False,
                    check_out_time__isnull=True)
            .order_by('-record_date')
            .first())


def close_open_records_before(cutoff_date: date) -> int:
    """Stamp `status='no_checkout'` on past open-checkin records.

    Pure UPDATE, no per-row Python. Idempotent because rows already at
    'no_checkout' are filtered out.
    """
    qs = (AttendanceRecord.objects
          .filter(record_date__lt=cutoff_date,
                  check_in_time__isnull=False,
                  check_out_time__isnull=True)
          .exclude(status='no_checkout'))
    return qs.update(status='no_checkout')

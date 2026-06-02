"""Views cho chấm công."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import deny_admin
from accounts.services import ensure_profile
from attendance.models import AttendanceRecord, AttendanceAdjustmentRequest
from attendance.services.record.attendance_logging_service import get_open_previous_record


def _history_rows(user, limit=10):
    today = timezone.localdate()
    first_of_month = today.replace(day=1)
    rows = list(
        AttendanceRecord.objects
        .filter(user=user, record_date__gte=first_of_month)
        .order_by('-record_date')[:limit]
    )
    adj_map = {
        a.record_id: a
        for a in AttendanceAdjustmentRequest.objects.filter(record__in=rows)
    }
    for r in rows:
        r.adjustment = adj_map.get(r.id)
    return rows


@login_required
@deny_admin
def attendance_view(request):
    """Trang chấm công. Real data."""
    ensure_profile(request.user)

    open_prev = get_open_previous_record(request.user)
    # banner_eligible_for_adjustment = status is exactly 'no_checkout' (no submission yet)
    eligible = (
        open_prev is not None
        and open_prev.status == 'no_checkout'
        and not AttendanceAdjustmentRequest.objects.filter(record=open_prev).exists()
    )

    return render(request, 'attendance/record/attendance.html', {
        'active_page': 'attendance',
        'open_previous_record': open_prev,
        'banner_eligible_for_adjustment': eligible,
        'history_rows': _history_rows(request.user),
        'today_first_of_month': timezone.localdate().replace(day=1),
        'today_short': timezone.localdate().strftime('%d/%m'),
    })

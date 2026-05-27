"""Views cho chấm công."""
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from accounts.services import ensure_profile
from attendance.models import AttendanceRecord, AttendanceAdjustmentRequest
from attendance.services.attendance_logging_service import get_open_previous_record


def _history_rows(user, limit=10):
    today = timezone.localdate()
    first_of_month = today.replace(day=1)
    return list(
        AttendanceRecord.objects
        .filter(user=user, record_date__gte=first_of_month)
        .order_by('-record_date')[:limit]
    )


@login_required
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

    return render(request, 'attendance/attendance.html', {
        'active_page': 'attendance',
        'open_previous_record': open_prev,
        'banner_eligible_for_adjustment': eligible,
        'history_rows': _history_rows(request.user),
        'today_short': timezone.localdate().strftime('%d/%m'),
    })

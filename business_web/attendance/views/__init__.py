"""Views cho chấm công."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.services import ensure_profile


@login_required
def attendance_view(request):
    """Trang chấm công. MOCK DATA. Template: attendance/attendance.html"""
    ensure_profile(request.user)
    return render(request, 'attendance/attendance.html', {
        'active_page': 'attendance',
    })

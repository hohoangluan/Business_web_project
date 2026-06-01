"""GET/POST /attendance/adjustment/<record_id>/ — nhân viên gửi yêu cầu điều chỉnh.

Mọi role có chấm công (employee/leader/manager) gửi cho record CỦA CHÍNH MÌNH
trong tháng hiện tại. HR duyệt ở trang review.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from attendance.forms.adjustment.attendance_adjustment_form import AttendanceAdjustmentForm
from attendance.models import AttendanceAdjustmentRequest, AttendanceRecord


@login_required
def submit_adjustment_view(request, record_id):
    record = get_object_or_404(
        AttendanceRecord, id=record_id, user=request.user,
    )

    # Đã có yêu cầu cho record này (OneToOne).
    if AttendanceAdjustmentRequest.objects.filter(record=record).exists():
        messages.error(request, 'Ngày này đã có yêu cầu điều chỉnh.')
        return redirect(reverse('attendance'))

    # Chỉ cho điều chỉnh record trong ĐÚNG THÁNG DƯƠNG LỊCH HIỆN TẠI
    # (ngày 1 → cuối tháng theo lịch; không phụ thuộc lúc bật hệ thống).
    today = timezone.localdate()
    if (record.record_date.year, record.record_date.month) != (today.year, today.month):
        messages.error(
            request, 'Chỉ được yêu cầu điều chỉnh cho ngày trong tháng hiện tại.'
        )
        return redirect(reverse('attendance'))

    if request.method == 'POST':
        form = AttendanceAdjustmentForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                adj = form.save(commit=False)
                adj.record = record
                adj.submitted_by = request.user
                adj.status = 'pending'
                adj.save()
                record.status = 'pending_adjustment'
                record.save(update_fields=['status'])
            messages.success(request, 'Đã gửi yêu cầu điều chỉnh tới HR.')
            return redirect(reverse('attendance'))
    else:
        form = AttendanceAdjustmentForm()

    return render(
        request,
        'attendance/adjustment/adjustment_request_form.html',
        {'form': form, 'record': record, 'active_page': 'attendance'},
    )

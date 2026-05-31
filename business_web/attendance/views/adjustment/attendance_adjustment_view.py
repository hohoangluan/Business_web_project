"""GET/POST /attendance/adjustment/<record_id>/ — employee-side submission only."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from attendance.forms.adjustment.attendance_adjustment_form import AttendanceAdjustmentForm
from attendance.models import AttendanceAdjustmentRequest, AttendanceRecord


@login_required
def submit_adjustment_view(request, record_id):
    record = get_object_or_404(
        AttendanceRecord, id=record_id, user=request.user,
    )

    if AttendanceAdjustmentRequest.objects.filter(record=record).exists():
        if request.method == 'POST':
            return JsonResponse(
                {'error': 'already_submitted'}, status=409,
            )
        return JsonResponse(
            {'error': 'already_submitted'}, status=409,
        )

    if record.status != 'no_checkout':
        return JsonResponse(
            {'error': 'not_eligible'}, status=400,
        )

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
            messages.success(
                request,
                'Đã gửi yêu cầu điều chỉnh tới HR.',
            )
            return redirect(reverse('attendance'))
    else:
        form = AttendanceAdjustmentForm()

    return render(
        request,
        'attendance/adjustment/adjustment_request_form.html',
        {'form': form, 'record': record, 'active_page': 'attendance'},
    )

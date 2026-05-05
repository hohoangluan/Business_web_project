"""
Views cho stats_reports — thống kê tổng hợp, export CSV, print PDF.
"""

import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse

from accounts.services import ensure_profile, can_access_statistics
from stats_reports.services import (
    build_statistics_page_context,
    STATISTICS_TYPE_LABEL_MAP,
)


@login_required
def statistics_view(request):
    """Trang statistics. Template: stats_reports/statistics.html"""
    ensure_profile(request.user)
    if not can_access_statistics(request.user):
        messages.error(request, 'Bạn không có quyền xem statistics.')
        return redirect('dashboard')

    context = build_statistics_page_context(request.user, request.GET)
    context['active_page'] = 'statistics'
    return render(request, 'stats_reports/statistics.html', context)


@login_required
def statistics_export_csv_view(request):
    """Xuất bảng tổng hợp statistics ra CSV."""
    ensure_profile(request.user)
    if not can_access_statistics(request.user):
        messages.error(request, 'Bạn không có quyền xuất statistics.')
        return redirect('dashboard')

    ctx = build_statistics_page_context(request.user, request.GET)
    tr = ctx['time_range']
    st = ctx['selected_stats_type']
    fname = f"statistics_{st}_{tr['start_date']:%Y%m%d}_{tr['end_date']:%Y%m%d}.csv"

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Bao cao statistics'])
    writer.writerow(['Loai thong ke', ctx['selected_stats_type_label']])
    for item in ctx['statistics_sections']['filter_summary']:
        writer.writerow([item])
    writer.writerow([])

    sections = ctx['statistics_sections']

    if st == 'evaluation':
        writer.writerow(['Nhan vien', 'Username', 'Phong ban', 'Nguoi danh gia', 'Ngay', 'Noi dung', 'Minh chung'])
        for r in sections['evaluation_rows']:
            writer.writerow([r['employee_name'], r['employee_username'], r['department'], f"{r['reviewer_name']} ({r['reviewer_role']})", r['evaluation_date_display'], r['evaluation_content'], r['evidence_reference']])
        return response

    if st == 'rewards':
        writer.writerow(['Nhan vien', 'Username', 'Phong ban', 'Nguoi de xuat', 'Phan loai', 'So tien', 'Ngay', 'Trang thai', 'Ly do'])
        for r in sections['rewards_rows']:
            writer.writerow([r['employee_name'], r['employee_username'], r['department'], f"{r['proposer_name']} ({r['proposer_role']})", r['type_label'], r['amount_display'], r['application_date_display'], r['status'], r['reason_title']])
        return response

    if st == 'leave':
        writer.writerow(['Nhan vien', 'Username', 'Phong ban', 'Quan ly', 'Leader', 'Ngay nghi', 'So don'])
        for r in sections['summary_rows']:
            writer.writerow([r['employee_name'], r['employee_username'], r['department'], r['manager_name'], r['leader_name'], r['leave_days'], r['leave_requests']])
        return response

    if st == 'attendance':
        writer.writerow(['Nhan vien', 'Username', 'Phong ban', 'Gio tang ca', 'Di tre', 'Nghi lam', 'Ty le'])
        for r in sections['summary_rows']:
            writer.writerow([r['employee_name'], r['employee_username'], r['department'], r['overtime_hours'], r['late_count'], r['absence_days'], r['attendance_rate']])
        return response

    writer.writerow(['Nhan vien', 'Username', 'Phong ban', 'Quan ly', 'Leader', 'Ngay nghi', 'So don', 'Gio tang ca', 'Di tre', 'Nghi lam', 'Ty le'])
    for r in sections['summary_rows']:
        writer.writerow([r['employee_name'], r['employee_username'], r['department'], r['manager_name'], r['leader_name'], r['leave_days'], r['leave_requests'], r['overtime_hours'], r['late_count'], r['absence_days'], r['attendance_rate']])

    if st == 'all':
        writer.writerow([])
        writer.writerow(['Thong ke danh gia'])
        writer.writerow(['Nhan vien', 'Username', 'Phong ban', 'Nguoi danh gia', 'Ngay', 'Noi dung', 'Minh chung'])
        for r in sections['evaluation_rows']:
            writer.writerow([r['employee_name'], r['employee_username'], r['department'], f"{r['reviewer_name']} ({r['reviewer_role']})", r['evaluation_date_display'], r['evaluation_content'], r['evidence_reference']])
        writer.writerow([])
        writer.writerow(['Thong ke khen thuong va xu phat'])
        writer.writerow(['Nhan vien', 'Username', 'Phong ban', 'Nguoi de xuat', 'Phan loai', 'So tien', 'Ngay', 'Trang thai', 'Ly do'])
        for r in sections['rewards_rows']:
            writer.writerow([r['employee_name'], r['employee_username'], r['department'], f"{r['proposer_name']} ({r['proposer_role']})", r['type_label'], r['amount_display'], r['application_date_display'], r['status'], r['reason_title']])

    return response


@login_required
def statistics_print_view(request):
    """Trang in tối giản. Template: stats_reports/statistics_print.html"""
    ensure_profile(request.user)
    if not can_access_statistics(request.user):
        messages.error(request, 'Bạn không có quyền in statistics.')
        return redirect('dashboard')

    context = build_statistics_page_context(request.user, request.GET)
    return render(request, 'stats_reports/statistics_print.html', context)

"""Views cho báo cáo & tương tác (reports, tickets)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.services import ensure_profile, can_manage_requests


@login_required
def report_view(request):
    """Trang báo cáo cá nhân. MOCK DATA. Template: reports_interactions/report.html"""
    ensure_profile(request.user)
    return render(request, 'reports_interactions/report.html', {
        'active_page': 'reports',
        'is_manager': can_manage_requests(request.user),
    })


@login_required
def report_inbox_view(request):
    """Hộp thư nhận báo cáo. Template: reports_interactions/report_inbox.html"""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền xem hộp thư báo cáo!')
        return redirect('reports')
    return render(request, 'reports_interactions/report_inbox.html', {
        'active_page': 'reports',
    })


@login_required
def ticket_list_view(request):
    """Trang ticket cá nhân. MOCK DATA. Template: reports_interactions/tickets.html"""
    ensure_profile(request.user)
    return render(request, 'reports_interactions/tickets.html', {
        'active_page': 'tickets',
        'can_process': can_manage_requests(request.user),
    })


@login_required
def ticket_process_view(request):
    """Trang xử lý ticket. Template: reports_interactions/ticket_process.html"""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền truy cập trang xử lý ticket!')
        return redirect('tickets')
    return render(request, 'reports_interactions/ticket_process.html', {
        'active_page': 'tickets',
    })

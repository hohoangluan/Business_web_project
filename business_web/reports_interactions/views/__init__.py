"""Views cho báo cáo & tương tác (reports, tickets)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from accounts.services import ensure_profile, can_manage_requests
from reports_interactions.models import Report
from reports_interactions.models.ticket_model import Ticket
from reports_interactions.forms import ReportForm, TicketForm


@login_required
def report_view(request):
    """
    Trang quản lý báo cáo cá nhân của người dùng.
    Hỗ trợ xem danh sách, tạo mới tự do, sửa và xóa báo cáo chưa được quản lý tiếp nhận (acknowledged).
    """
    ensure_profile(request.user)
    
    # 1. Danh sách báo cáo do người dùng này tạo ra
    reports = Report.objects.filter(author=request.user).select_related('recipient').order_by('-created_at')

    # 2. Xử lý các thao tác POST (tạo, sửa, xóa)
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'create':
            form = ReportForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                report = form.save(commit=False)
                report.author = request.user
                report.save()
                messages.success(request, 'Đã gửi báo cáo tự do thành công!')
                return redirect('reports')
            else:
                messages.error(request, 'Có lỗi xảy ra khi gửi báo cáo, vui lòng kiểm tra lại.')
        
        elif action == 'edit':
            report_id = request.POST.get('report_id')
            report = get_object_or_404(Report, pk=report_id, author=request.user)
            if not report.can_edit_or_delete:
                messages.error(request, 'Báo cáo đã được quản lý xem, không thể chỉnh sửa!')
                return redirect('reports')
            
            form = ReportForm(request.POST, request.FILES, instance=report, user=request.user)
            if form.is_valid():
                form.save()
                if report.status == Report.NEEDS_UPDATE:
                    report.status = Report.SUBMITTED
                    report.save(update_fields=['status'])
                messages.success(request, 'Đã cập nhật báo cáo thành công!')
                return redirect('reports')
            else:
                messages.error(request, 'Có lỗi xảy ra khi cập nhật báo cáo.')
                
        elif action == 'delete':
            report_id = request.POST.get('report_id')
            report = get_object_or_404(Report, pk=report_id, author=request.user)
            if not report.can_edit_or_delete:
                messages.error(request, 'Báo cáo đã được quản lý xem, không thể xóa!')
                return redirect('reports')
                
            report.delete()
            messages.success(request, 'Đã xóa báo cáo thành công!')
            return redirect('reports')

    # 3. Form rỗng cho Modal tạo mới
    form = ReportForm(user=request.user)

    return render(request, 'reports_interactions/report.html', {
        'active_page': 'reports',
        'is_manager': can_manage_requests(request.user),
        'reports': reports,
        'form': form,
    })


@login_required
def report_detail_view(request, pk):
    """
    Trang chi tiết báo cáo.
    Tự động đánh dấu đã xem (is_viewed = True) nếu người nhận (quản lý) truy cập.
    Quản lý có thể yêu cầu cập nhật (needs_update) hoặc tiếp nhận (acknowledged);
    báo cáo chỉ bị khóa sửa/xóa khi đã ở trạng thái acknowledged.
    """
    ensure_profile(request.user)
    report = get_object_or_404(Report, pk=pk)

    # Kiểm tra quyền xem báo cáo
    is_author = (report.author == request.user)
    is_recipient = (report.recipient == request.user)
    is_superuser = request.user.is_superuser

    if not (is_author or is_recipient or is_superuser):
        messages.error(request, 'Bạn không có quyền xem báo cáo này!')
        return redirect('reports')

    # Nếu người xem là người nhận (Quản lý) và chưa đọc, đánh dấu đã xem
    if is_recipient and not report.is_viewed:
        report.is_viewed = True
        report.viewed_at = timezone.now()
        report.save()

    if request.method == 'POST' and (is_recipient or is_superuser):
        action = request.POST.get('action')
        if action == 'request_update':
            report.status = report.NEEDS_UPDATE
            report.manager_note = request.POST.get('manager_note', '').strip()
            report.save(update_fields=['status', 'manager_note'])
            messages.success(request, 'Đã yêu cầu nhân viên cập nhật báo cáo.')
            return redirect('report_detail', pk=report.pk)
        elif action == 'acknowledge':
            report.status = report.ACKNOWLEDGED
            report.save(update_fields=['status'])
            messages.success(request, 'Đã tiếp nhận báo cáo.')
            return redirect('report_detail', pk=report.pk)

    return render(request, 'reports_interactions/report_detail.html', {
        'active_page': 'reports',
        'report': report,
        'is_author': is_author,
        'is_recipient': is_recipient,
    })


@login_required
def report_inbox_view(request):
    """
    Hộp thư nhận báo cáo của quản lý/leader/admin/hr.
    """
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền xem hộp thư báo cáo!')
        return redirect('reports')

    # Lấy các báo cáo gửi tới quản lý hiện tại
    reports = Report.objects.filter(recipient=request.user).select_related('author').order_by('-created_at')
    unread_count = reports.filter(is_viewed=False).count()

    return render(request, 'reports_interactions/report_inbox.html', {
        'active_page': 'reports',
        'reports': reports,
        'unread_count': unread_count,
    })


@login_required
def ticket_list_view(request):
    """Trang ticket cá nhân. Template: reports_interactions/tickets.html"""
    ensure_profile(request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            form = TicketForm(request.POST, request.FILES)
            if form.is_valid():
                ticket = form.save(commit=False)
                ticket.author = request.user
                ticket.status = Ticket.STATUS_NEW
                ticket.save()
                messages.success(request, 'Đã tạo yêu cầu/khiếu nại thành công!')
                return redirect('tickets')
            else:
                messages.error(request, 'Có lỗi xảy ra khi tạo ticket. Vui lòng kiểm tra lại.')
    else:
        form = TicketForm()

    status_filter = request.GET.get('status', '')
    tickets = Ticket.objects.filter(author=request.user)
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
        
    tickets = tickets.order_by('-created_at')

    # Thống kê
    stats = {
        'waiting': Ticket.objects.filter(author=request.user, status=Ticket.STATUS_NEW).count(),
        'processing': Ticket.objects.filter(author=request.user, status=Ticket.STATUS_PROCESSING).count(),
        'resolved': Ticket.objects.filter(author=request.user, status=Ticket.STATUS_RESOLVED).count(),
        'closed': Ticket.objects.filter(author=request.user, status=Ticket.STATUS_CLOSED).count(),
    }

    return render(request, 'reports_interactions/tickets.html', {
        'active_page': 'tickets',
        'can_process': can_manage_requests(request.user),
        'tickets': tickets,
        'form': form,
        'stats': stats,
        'status_filter': status_filter,
    })


@login_required
def ticket_process_view(request):
    """Trang xử lý ticket. Template: reports_interactions/ticket_process.html"""
    ensure_profile(request.user)
    if not can_manage_requests(request.user):
        messages.error(request, 'Bạn không có quyền truy cập trang xử lý ticket!')
        return redirect('tickets')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        ticket_id = request.POST.get('ticket_id')
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        
        if action == 'receive':
            ticket.status = Ticket.STATUS_PROCESSING
            ticket.assigned_to = request.user
            ticket.save()
            messages.success(request, f'Đã tiếp nhận ticket: {ticket.title}')
        elif action == 'resolve':
            ticket.status = Ticket.STATUS_RESOLVED
            ticket.save()
            messages.success(request, f'Đã giải quyết ticket: {ticket.title}')
        elif action == 'close':
            ticket.status = Ticket.STATUS_CLOSED
            ticket.save()
            messages.success(request, f'Đã đóng ticket: {ticket.title}')
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '').strip()
            if reason:
                ticket.status = Ticket.STATUS_REJECTED
                ticket.rejection_reason = reason
                ticket.save()
                messages.success(request, f'Đã từ chối ticket: {ticket.title}')
            else:
                messages.error(request, 'Vui lòng nhập lý do từ chối.')
                
        return redirect('ticket_process')

    # Lấy các ticket chưa đóng và chưa từ chối
    tickets = Ticket.objects.exclude(status__in=[Ticket.STATUS_CLOSED, Ticket.STATUS_REJECTED, Ticket.STATUS_RESOLVED]).select_related('author', 'author__profile').order_by('-created_at')
    
    return render(request, 'reports_interactions/ticket_process.html', {
        'active_page': 'tickets',
        'tickets': tickets,
    })

"""Views cho báo cáo & tương tác (reports, tickets)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from accounts.services import ensure_profile, can_manage_requests
from reports_interactions.models import Report
from reports_interactions.forms import ReportForm


@login_required
def report_view(request):
    """
    Trang quản lý báo cáo cá nhân của người dùng.
    Hỗ trợ xem danh sách, tạo mới tự do, sửa và xóa báo cáo chưa được xem.
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

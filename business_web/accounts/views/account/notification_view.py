"""Views for viewing and managing system notifications."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from accounts.models import Notification


@login_required
def notifications_view(request):
    """Trang xem toàn bộ thông báo của người dùng; đánh dấu đã đọc khi mở."""

    notifications = Notification.objects.filter(user=request.user)

    # Mở trang danh sách = đã xem hết → đánh dấu đã đọc.
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    return render(
        request,
        "accounts/account/notifications.html",
        {
            "active_page": "notifications",
            "notifications": notifications,
        },
    )


@login_required
@require_POST
def mark_notifications_read_view(request):
    """Đánh dấu tất cả thông báo chưa đọc là đã đọc (gọi khi mở chuông)."""

    updated = Notification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True)
    return JsonResponse({"success": True, "updated": updated})

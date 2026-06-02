"""Context processors for accounts app."""

from accounts.models.notification_model import Notification

def notifications(request):
    """Bổ sung danh sách thông báo chưa đọc vào context cho mọi template."""
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            user=request.user, is_read=False
        ).order_by('-created_at')[:5]
        unread_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
    else:
        unread_notifications = []
        unread_count = 0

    return {
        'unread_notifications': unread_notifications,
        'unread_count': unread_count,
    }

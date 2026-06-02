"""Service helpers for creating system notifications."""

from accounts.models import Notification


def create_notification(user, title, message, link=""):
    """Tạo một thông báo hệ thống cho ``user``.

    Trả về đối tượng Notification vừa tạo. Bỏ qua nếu thiếu user.
    """

    if user is None:
        return None

    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        link=link or "",
    )

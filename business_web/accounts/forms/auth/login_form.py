"""Login form wrapper for accounts."""

from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """Authentication form với thông báo lỗi tiếng Việt.

    Django mặc định in lỗi tiếng Anh ("Please enter a correct username...").
    Override ``error_messages`` để user thấy thông báo tiếng Việt.
    """

    error_messages = {
        "invalid_login": "Tên đăng nhập hoặc mật khẩu không đúng.",
        "inactive": "Tài khoản đã bị khóa. Vui lòng liên hệ HR/Admin để mở khóa.",
    }

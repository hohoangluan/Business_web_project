"""Đếm số lần đăng nhập sai (QĐ_TK1) bằng cache, không thêm model.

Sai mật khẩu liên tiếp ``LOGIN_LOCKOUT_MAX_FAILS`` lần → caller khóa tài khoản
(is_active=False). Key dưới namespace ``login_lockout:``, gắn theo username.
"""
import hashlib

from django.conf import settings
from django.core.cache import cache


def _fails_key(username: str) -> str:
    # Hash để cache key luôn hợp lệ (username có thể chứa khoảng trắng/ký tự
    # đặc biệt → vỡ chuẩn memcached).
    norm = (username or '').strip().lower()
    digest = hashlib.sha256(norm.encode('utf-8')).hexdigest()
    return f'login_lockout:fails:{digest}'


def register_failure(username: str) -> int:
    """Tăng bộ đếm sai cho username. Trả về số lần sai hiện tại."""
    key = _fails_key(username)
    ttl = settings.LOGIN_LOCKOUT_WINDOW_SEC
    # cache.add chỉ set khi key chưa tồn tại → khởi tạo = 1.
    if cache.add(key, 1, timeout=ttl):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=ttl)
        return 1


def clear_failures(username: str) -> None:
    """Xóa bộ đếm (đăng nhập thành công hoặc đã khóa tài khoản)."""
    cache.delete(_fails_key(username))


def reached_limit(count: int) -> bool:
    """Đã chạm ngưỡng khóa chưa?"""
    return count >= settings.LOGIN_LOCKOUT_MAX_FAILS

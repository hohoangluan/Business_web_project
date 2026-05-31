"""Cache-backed lockout counter for face verification.

No new model. Keys live under `face_lockout:` namespace.
"""
import time
from typing import Tuple

from django.conf import settings
from django.core.cache import cache


def _fails_key(user) -> str:
    return f'face_lockout:fails:{user.id}'


def _until_key(user) -> str:
    return f'face_lockout:until:{user.id}'


def is_locked(user) -> Tuple[bool, int]:
    """Return (locked, seconds_remaining)."""
    until = cache.get(_until_key(user))
    if until is None:
        return False, 0
    remaining = int(until - time.time())
    if remaining <= 0:
        cache.delete(_until_key(user))
        cache.delete(_fails_key(user))
        return False, 0
    return True, remaining


def register_failure(user) -> int:
    """Increment fail counter; lock if it reaches MAX_FAILS. Returns new count."""
    key = _fails_key(user)
    ttl = settings.FACE_LOCKOUT_DURATION_SEC
    # cache.add does nothing when the key exists; use it to initialize at 1.
    if cache.add(key, 1, timeout=ttl):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=ttl)
            count = 1
    if count >= settings.FACE_LOCKOUT_MAX_FAILS:
        cache.set(_until_key(user), time.time() + ttl, timeout=ttl)
    return count


def clear_failures(user) -> None:
    cache.delete(_fails_key(user))
    cache.delete(_until_key(user))

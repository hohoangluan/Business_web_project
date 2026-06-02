"""FUNC-ATT-012 / SEC-013: lockout chấm công 3 lần sai → khóa 300s."""
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from attendance.services.face import face_lockout_service as lock


class TestFaceLockout(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='u', password='123')

    def test_locks_after_3_failures(self):
        # 2 lần sai → chưa khóa.
        lock.register_failure(self.user)
        lock.register_failure(self.user)
        locked, _ = lock.is_locked(self.user)
        self.assertFalse(locked)
        # Lần 3 → khóa.
        lock.register_failure(self.user)
        locked, remaining = lock.is_locked(self.user)
        self.assertTrue(locked)
        self.assertGreater(remaining, 0)

    def test_clear_unlocks(self):
        for _ in range(3):
            lock.register_failure(self.user)
        lock.clear_failures(self.user)
        locked, _ = lock.is_locked(self.user)
        self.assertFalse(locked)

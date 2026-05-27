"""Tests for face_lockout_service. Uses locmem cache."""
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings

from attendance.services import face_lockout_service as svc


@override_settings(
    FACE_LOCKOUT_MAX_FAILS=3,
    FACE_LOCKOUT_DURATION_SEC=60,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                        'LOCATION': 'lockout-tests'}},
)
class FaceLockoutServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('alice', password='x')

    def test_initial_state_not_locked(self):
        locked, remaining = svc.is_locked(self.user)
        self.assertFalse(locked)
        self.assertEqual(remaining, 0)

    def test_first_failure_counts_but_not_locked(self):
        count = svc.register_failure(self.user)
        self.assertEqual(count, 1)
        locked, _ = svc.is_locked(self.user)
        self.assertFalse(locked)

    def test_locks_at_max_fails(self):
        for _ in range(3):
            svc.register_failure(self.user)
        locked, remaining = svc.is_locked(self.user)
        self.assertTrue(locked)
        self.assertGreater(remaining, 0)
        self.assertLessEqual(remaining, 60)

    def test_clear_failures_resets(self):
        for _ in range(3):
            svc.register_failure(self.user)
        svc.clear_failures(self.user)
        locked, remaining = svc.is_locked(self.user)
        self.assertFalse(locked)
        self.assertEqual(remaining, 0)

    def test_failures_namespaced_per_user(self):
        other = User.objects.create_user('bob', password='x')
        for _ in range(3):
            svc.register_failure(self.user)
        locked_self, _ = svc.is_locked(self.user)
        locked_other, _ = svc.is_locked(other)
        self.assertTrue(locked_self)
        self.assertFalse(locked_other)

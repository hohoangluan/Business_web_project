"""Bổ sung kiểm thử nhóm 1 (accounts) + nhóm 5 (security).

ACC-006, ACC-009/SEC-012 (OTP), SEC-003 (RBAC matrix), SEC-008 (CSRF),
SEC-010 (session config).
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import OtpCode, Role, UserProfile


class TestForgotPasswordEdge(TestCase):
    def test_func_acc_006_unknown_username_no_otp(self):
        """FUNC-ACC-006: username không tồn tại → báo lỗi, không tạo OTP."""
        resp = self.client.post(reverse('forgot_password'), data={
            'step': 'username', 'username': 'khongton',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Không tìm thấy tài khoản')
        self.assertEqual(OtpCode.objects.count(), 0)


class TestOtpExpiryBoundary(TestCase):
    """FUNC-ACC-009 / SEC-012: biên hết hạn OTP 120 giây."""

    def setUp(self):
        self.user = User.objects.create_user(username='u1', password='123', email='u1@x.com')
        from accounts.services import verify_otp
        self.verify_otp = verify_otp

    def _make_otp(self, age_seconds, code='123456'):
        otp = OtpCode.objects.create(user=self.user, code=code)
        # created_at là auto_now_add → ghi đè bằng update().
        OtpCode.objects.filter(pk=otp.pk).update(
            created_at=timezone.now() - timedelta(seconds=age_seconds)
        )
        return otp

    def test_otp_valid_just_before_expiry(self):
        self._make_otp(age_seconds=119)
        ok, _ = self.verify_otp(self.user, '123456')
        self.assertTrue(ok)

    def test_otp_expired_after_120s(self):
        self._make_otp(age_seconds=121)
        ok, msg = self.verify_otp(self.user, '123456')
        self.assertFalse(ok)
        self.assertIn('hết hạn', msg)

    def test_otp_wrong_code(self):
        self._make_otp(age_seconds=10, code='111111')
        ok, msg = self.verify_otp(self.user, '999999')
        self.assertFalse(ok)


class TestRbacMatrix(TestCase):
    """SEC-003: employee thường bị chặn khỏi chức năng HR/Admin."""

    def setUp(self):
        self.client = Client()
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        self.emp = User.objects.create_user(username='emp', password='123')
        UserProfile.objects.create(user=self.emp, role=self.emp_role, employee_id='E001')
        self.target = User.objects.create_user(username='target', password='123')
        UserProfile.objects.create(user=self.target, employee_id='T001')

    def test_employee_blocked_from_hr_admin_endpoints(self):
        self.client.force_login(self.emp)
        cases = [
            ('hr_create_profile', None),
            ('user_list', None),
            ('hr_assign_role', [self.target.pk]),
            ('hr_view_profile', [self.target.pk]),
            ('reset_user_password', [self.target.pk]),
        ]
        for name, args in cases:
            url = reverse(name, args=args) if args else reverse(name)
            resp = self.client.get(url) if args is None or name in ('hr_view_profile',) else self.client.post(url)
            self.assertIn(
                resp.status_code, (302, 403),
                f'{name} phải chặn employee (302/403), nhận {resp.status_code}',
            )

    def test_employee_cannot_delete_user(self):
        self.client.force_login(self.emp)
        resp = self.client.post(reverse('delete_user', args=[self.target.pk]))
        self.assertIn(resp.status_code, (302, 403))
        self.assertTrue(User.objects.filter(pk=self.target.pk).exists())


class TestCsrf(TestCase):
    """SEC-008: POST thiếu CSRF token → 403."""

    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(username='u', password='123')
        UserProfile.objects.create(user=self.user, employee_id='U001')

    def test_post_without_csrf_is_forbidden(self):
        self.csrf_client.force_login(self.user)
        resp = self.csrf_client.post(reverse('leave'), data={
            'leave_type': 'annual',
            'start_date': '2026-07-01', 'end_date': '2026-07-02', 'reason': 'x',
        })
        self.assertEqual(resp.status_code, 403)


class TestSessionConfig(TestCase):
    """SEC-010: cấu hình timeout 30 phút (idle)."""

    def test_session_settings(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 1800)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)

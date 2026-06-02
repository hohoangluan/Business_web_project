"""Kiểm thử bảo mật tầng ứng dụng (test_plan §5).

Phủ: hash mật khẩu (SEC-005), SQL Injection (SEC-006), XSS (SEC-007),
chặn ẩn danh (SEC-001), IDOR (SEC-004).
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, UserProfile
from leaves.models import LeaveRequest
from reports_interactions.models import Report


class TestPasswordHashing(TestCase):
    """SEC-005: mật khẩu không bao giờ lưu plain text."""

    def test_sec_005_password_is_hashed(self):
        resp = self.client.post(reverse('register'), data={
            'employee_id': 'NV001',
            'password': 'StrongPassword123!',
            'full_name': 'Nguyen Van A',
            'email': 'nva@example.com',
        })
        self.assertRedirects(resp, reverse('dashboard'))
        user = User.objects.get(username='nv001')
        # Không lưu plain text; dùng hasher Django (PBKDF2 mặc định).
        self.assertNotEqual(user.password, 'StrongPassword123!')
        self.assertTrue(user.password.startswith('pbkdf2_'))
        self.assertTrue(user.check_password('StrongPassword123!'))


class TestSqlInjection(TestCase):
    """SEC-006: payload SQLi ở ô đăng nhập vô hại (ORM tham số hóa)."""

    def setUp(self):
        User.objects.create_user(username='nv001', password='StrongPassword123!')

    def test_sec_006_sqli_login_payload_is_harmless(self):
        resp = self.client.post(reverse('login'), data={
            'username': "' OR '1'='1",
            'password': "' OR '1'='1",
        })
        # Không crash (không 500), không đăng nhập được.
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        # User thật vẫn còn nguyên (không bị xóa/đổi do injection).
        self.assertTrue(User.objects.filter(username='nv001').exists())


class TestAnonymousAccess(TestCase):
    """SEC-001: trang nội bộ chặn người chưa đăng nhập → redirect login."""

    def test_sec_001_protected_pages_redirect_anonymous(self):
        for name in ['leave', 'overtime', 'profile', 'reports']:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302, f'{name} phải redirect khi ẩn danh')
            self.assertIn(reverse('login'), resp.url)


class TestIdorAndXss(TestCase):
    """SEC-004 (IDOR) + SEC-007 (XSS)."""

    def setUp(self):
        self.client = Client()
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        self.alice = User.objects.create_user(username='alice', password='123')
        UserProfile.objects.create(user=self.alice, role=self.emp_role, employee_id='A001')
        self.bob = User.objects.create_user(username='bob', password='123')
        UserProfile.objects.create(user=self.bob, role=self.emp_role, employee_id='B001')
        self.mallory = User.objects.create_user(username='mallory', password='123')
        UserProfile.objects.create(user=self.mallory, role=self.emp_role, employee_id='M001')

    def test_sec_004_idor_cannot_cancel_others_leave(self):
        """Mallory không hủy được đơn nghỉ của Alice qua URL."""
        leave = LeaveRequest.objects.create(
            user=self.alice, leave_type=LeaveRequest.ANNUAL,
            start_date='2026-07-01', end_date='2026-07-02',
            days=Decimal('2.0'), status=LeaveRequest.PENDING,
        )
        self.client.force_login(self.mallory)
        self.client.post(reverse('leave_cancel', args=[leave.id]))
        # Đơn của Alice còn nguyên.
        self.assertTrue(LeaveRequest.objects.filter(id=leave.id).exists())

    def test_sec_004_idor_cannot_view_others_report(self):
        """Mallory không xem được báo cáo giữa Alice (gửi) và Bob (nhận)."""
        report = Report.objects.create(
            author=self.alice, recipient=self.bob,
            title='Bí mật', content='nội dung riêng',
        )
        self.client.force_login(self.mallory)
        resp = self.client.get(reverse('report_detail', args=[report.id]))
        # Bị chặn → redirect về danh sách.
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('reports'), resp.url)

    def test_sec_007_xss_report_content_is_escaped(self):
        """Nội dung báo cáo chứa <script> phải bị escape khi render."""
        payload = '<script>alert(1)</script>'
        report = Report.objects.create(
            author=self.alice, recipient=self.bob,
            title='XSS', content=payload,
        )
        self.client.force_login(self.alice)
        resp = self.client.get(reverse('report_detail', args=[report.id]))
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        # Template autoescape → không có thẻ script thô.
        self.assertNotIn(payload, body)
        self.assertIn('&lt;script&gt;', body)

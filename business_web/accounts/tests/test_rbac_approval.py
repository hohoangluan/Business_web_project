"""SEC-002: nhân viên thường bị chặn khỏi các trang phê duyệt."""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, UserProfile


class TestApprovalRbac(TestCase):
    def setUp(self):
        self.client = Client()
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        self.emp = User.objects.create_user(username='emp', password='123')
        UserProfile.objects.create(user=self.emp, role=self.emp_role, employee_id='E001')

    def test_employee_blocked_from_approval_pages(self):
        self.client.force_login(self.emp)
        for name in ['leave_approval', 'overtime_approval',
                     'rewards_penalties_approval', 'evaluation_hr_approval']:
            resp = self.client.get(reverse(name))
            self.assertIn(
                resp.status_code, (302, 403),
                f'{name} phải chặn employee, nhận {resp.status_code}',
            )

"""Admin chỉ quản lý hệ thống — bị chặn khỏi mọi chức năng nghiệp vụ."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from accounts.models import Role, UserProfile


BUSINESS_VIEWS = [
    'profile', 'contract', 'attendance', 'leave',
    'overtime', 'reports', 'rewards_penalties',
]


class AdminAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)

        self.admin = User.objects.create_user('admin_u', password='x')
        UserProfile.objects.create(user=self.admin, role=self.admin_role, employee_id='ADM')
        self.hr = User.objects.create_user('hr_u', password='x')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR')

    def test_is_admin_property(self):
        self.assertTrue(self.admin.profile.is_admin)
        self.assertFalse(self.hr.profile.is_admin)

    def test_admin_blocked_from_business_views(self):
        self.client.force_login(self.admin)
        for name in BUSINESS_VIEWS:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302, f'{name} phải chặn admin')
            self.assertEqual(resp.headers['Location'], reverse('dashboard'))

    def test_hr_can_view_rewards(self):
        """HR phải xem được Khen thưởng & Xử phạt."""
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(reverse('rewards_penalties')).status_code, 200)

    def test_hr_can_view_profile(self):
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(reverse('profile')).status_code, 200)

    def test_superuser_role_simulation(self):
        """DEV: superuser mô phỏng role nào thì xem giao diện + quyền của role đó.

        - Chưa gán role → dev/admin (chặn nghiệp vụ, vào được quản lý hệ thống).
        - Mô phỏng employee → xem hồ sơ, bị chặn khen thưởng.
        - Mô phỏng HR → xem được khen thưởng.
        """
        su = User.objects.create_superuser('dev_u', 'd@x.com', 'x')
        UserProfile.objects.create(user=su, employee_id='DEV')
        self.client.force_login(su)

        # Mặc định (chưa role) = admin/dev.
        self.assertTrue(User.objects.get(pk=su.pk).profile.is_admin)
        self.assertEqual(self.client.get(reverse('rewards_penalties')).status_code, 302)

        # Mô phỏng employee.
        self.client.post(reverse('switch_role'), {'role_name': Role.EMPLOYEE})
        self.assertFalse(User.objects.get(pk=su.pk).profile.is_admin)
        self.assertEqual(self.client.get(reverse('profile')).status_code, 200)
        self.assertEqual(self.client.get(reverse('rewards_penalties')).status_code, 302)

        # Mô phỏng HR.
        self.client.post(reverse('switch_role'), {'role_name': Role.HR})
        self.assertEqual(self.client.get(reverse('rewards_penalties')).status_code, 200)

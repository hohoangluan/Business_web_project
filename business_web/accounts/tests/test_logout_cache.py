from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class LogoutCacheTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.user = User.objects.create_user('emp', password='x')
        UserProfile.objects.create(user=self.user, role=self.emp_role, employee_id='E1')

    def test_authenticated_page_is_no_store(self):
        self.client.login(username='emp', password='x')
        resp = self.client.get(reverse('dashboard'))
        self.assertIn('no-store', resp.headers.get('Cache-Control', ''))

    def test_dashboard_requires_login_after_logout(self):
        self.client.login(username='emp', password='x')
        self.client.get(reverse('logout'))
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)  # redirected to login

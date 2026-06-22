from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class SettingsNoTaxTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        self.admin = User.objects.create_user('admin_u', password='x')
        UserProfile.objects.create(user=self.admin, role=self.admin_role, employee_id='ADM')

    def test_no_tax_code_field(self):
        self.client.login(username='admin_u', password='x')
        resp = self.client.get(reverse('settings'))
        self.assertNotContains(resp, 'Mã số thuế')

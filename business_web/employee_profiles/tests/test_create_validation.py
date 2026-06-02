"""FUNC-EP-003 / EP-004: validation bắt buộc khi HR tạo hồ sơ."""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, UserProfile


class TestHrCreateValidation(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr_role = Role.objects.create(name=Role.HR)
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR001')
        self.client.force_login(self.hr)
        self.url = reverse('hr_create_profile')

    def _messages(self, resp):
        return [m.message for m in resp.context['messages']]

    def test_func_ep_003_employee_id_required(self):
        resp = self.client.post(self.url, data={'employee_id': '', 'department': 'Kinh doanh'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Mã nhân viên không được để trống.', self._messages(resp))
        self.assertEqual(User.objects.count(), 1)  # chỉ còn HR

    def test_func_ep_004_department_required(self):
        resp = self.client.post(self.url, data={'employee_id': 'NV999', 'department': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Phòng ban không được để trống.', self._messages(resp))
        self.assertFalse(UserProfile.objects.filter(employee_id='NV999').exists())

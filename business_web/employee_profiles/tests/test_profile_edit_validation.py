from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class ProfileEditValidationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.user = User.objects.create_user('emp', password='x', email='e@x.vn')
        UserProfile.objects.create(user=self.user, role=self.emp_role, employee_id='E1')
        self.client.login(username='emp', password='x')

    def test_invalid_phone_shows_error_not_silent(self):
        resp = self.client.post(reverse('profile'), {
            'full_name': 'A', 'email': 'e@x.vn',
            'phone_number': 'abc', 'date_of_birth': '',
        })
        self.assertContains(resp, 'Số điện thoại')  # error rendered on page
        self.assertEqual(resp.status_code, 200)

    def test_future_dob_rejected(self):
        resp = self.client.post(reverse('profile'), {
            'full_name': 'A', 'email': 'e@x.vn',
            'phone_number': '', 'date_of_birth': '01/01/2999',
        })
        self.assertContains(resp, 'ngày sinh')

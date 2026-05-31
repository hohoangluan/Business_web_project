from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

class TestLoginView(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(username='nv001', password='StrongPassword123!')

    def test_acc_login_01_valid_credentials(self):
        """ACC-LOGIN-01: Đăng nhập đúng username/password"""
        response = self.client.post(self.login_url, data={
            'username': 'nv001',
            'password': 'StrongPassword123!'
        })
        
        # Check redirect to dashboard
        self.assertRedirects(response, reverse('dashboard'))
        # Check session is created
        self.assertEqual(str(self.client.session.get('_auth_user_id')), str(self.user.pk))

    def test_acc_login_02_invalid_credentials(self):
        """ACC-LOGIN-02: Đăng nhập sai password"""
        response = self.client.post(self.login_url, data={
            'username': 'nv001',
            'password': 'WrongPassword123!'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 'Please enter a correct username and password. Note that both fields may be case-sensitive.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_acc_login_03_inactive_account(self):
        """ACC-LOGIN-03: Đăng nhập tài khoản bị khóa (is_active=False)"""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(self.login_url, data={
            'username': 'nv001',
            'password': 'StrongPassword123!'
        })
        
        self.assertEqual(response.status_code, 200)
        # Form error message for inactive user might be different but it will have an error
        self.assertTrue(response.context['form'].errors)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_acc_login_04_session_verification(self):
        """ACC-LOGIN-04: Đăng nhập -> kiểm tra session chứa user_id đúng"""
        self.client.post(self.login_url, data={
            'username': 'nv001',
            'password': 'StrongPassword123!'
        })
        
        # Ensure session stores correct user ID
        self.assertEqual(str(self.client.session['_auth_user_id']), str(self.user.pk))
